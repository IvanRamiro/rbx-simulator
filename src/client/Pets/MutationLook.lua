-- How a mutated pet looks (the owner, 2026-11-17: "SO LET'S ALSO ADD PET MUTATION, SO THERE PET WILL LOOK COOLER", then "No need
-- to add effects for mutation, just a mutation change of pet color, no need for any particles / just a color glow depends on the
-- mutation"; the ladder and its odds are PetRules.Mutations; vault: Pet Mutations Design 2026-11-17). A look is colour and glow only,
-- on what the pet already has, so it works on jointed and skinned pets and at every size, Colossal included:
--   1. its body recoloured: a SurfaceAppearance's Color multiplied by the mutation's tint (its maps' shading and detail stay), a
--      plain piece's Color lerped toward it;
--   2. its own glow pieces (Neon) and its own light in the mutation's glow colour;
--   3. one Highlight (a soft fill and outline in the mutation's colour), from a budget: the player's own pets first, then the nearest
--      within HIGHLIGHT_REACH, at most MAX_HIGHLIGHTS (eggs and auras use Highlights too).
-- No particles, sparkles, trails or other effects. The colour may move: Rainbow's hue slowly shifts, the others' glow pulses gently;
-- one step at TICK animates every mutated pet near the camera. On a phone another player's mutated pet keeps its colours and glow
-- pieces but no Highlight; Reduced Effects holds the pulses still and slows Rainbow.
--
--   MutationLook.dress(model, mutation, rig, options)  dresses a built pet (PetModels.build calls it); options: { own = true for the
--                                      local player's, priority = a number (higher keeps its Highlight first), quiet = true for no
--                                      Highlight }. Nothing for no mutation.
--   MutationLook.setPriority(model, priority, own)
--   MutationLook.portrait(frame, mutation)   tints a pet portrait (a ViewportFrame: it draws no Highlight); returns a stop
--   MutationLook.badge(mutation)       a tag in its colour (Rainbow's cycles)
--   MutationLook.color(mutation)       its colour now (Rainbow's cycles), for words
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local PetRules = require(ReplicatedStorage:WaitForChild("PetRules"))
local Quality = require(script.Parent.Parent:WaitForChild("Performance"):WaitForChild("Quality"))
local UiKit = require(script.Parent.Parent:WaitForChild("UI"):WaitForChild("UiKit"))

local MutationLook = {}

local LOW = Quality.Low
local TICK = 1 / 20             -- seconds between colour steps
local BUDGET_EVERY = 0.5        -- seconds between Highlight and distance passes
local MAX_HIGHLIGHTS = if LOW then 6 else 16 -- (six players with up to six pets each: own first, then the nearest)
local HIGHLIGHT_REACH = if LOW then 70 else 140 -- studs from the camera
local ANIMATE_REACH = if LOW then 70 else 140   -- colours stop moving farther away

local function rgb(r, g, b)
    return Color3.fromRGB(r, g, b)
end

local function colors(points)
    local keys = {}
    for _, p in points do
        table.insert(keys, ColorSequenceKeypoint.new(p[1], p[2]))
    end
    return ColorSequence.new(keys)
end

local RAINBOW = colors({ { 0, rgb(255, 90, 90) }, { 0.2, rgb(255, 200, 70) }, { 0.4, rgb(110, 255, 120) },
    { 0.6, rgb(80, 200, 255) }, { 0.8, rgb(170, 110, 255) }, { 1, rgb(255, 100, 210) } })

-- Each look. Tint: a SurfaceAppearance's colour multiplier (nil: kept); Plain, Mix, Shine: a plain piece's colour, how far toward it,
-- its reflectance; Glow: its glow pieces' colour (Brighten: toward white instead); Fill/FillT, Edge/EdgeT: the Highlight (a map can
-- only be multiplied, so on a pet of the opposite colour the fill carries the hue: gold on a blue pet alone reads green); Anim: how
-- the colour moves; Portrait: a portrait's ImageColor3.
local LOOKS = {
    Shiny = { -- its own colours, made bright and pearly, a white-gold edge that shimmers
        Brighten = 0.45, Fill = rgb(255, 252, 236), FillT = 0.8, Edge = rgb(255, 240, 190), EdgeT = 0.05, Anim = "Twinkle",
        Portrait = rgb(255, 252, 240),
    },
    Golden = {
        Tint = rgb(255, 210, 100), Plain = rgb(255, 196, 64), Mix = 0.85, Shine = 0.25, Glow = rgb(255, 214, 90),
        Fill = rgb(255, 190, 40), FillT = 0.5, Edge = rgb(255, 222, 120), EdgeT = 0.1, Anim = "Gleam", Portrait = rgb(255, 214, 120),
    },
    Jade = {
        Tint = rgb(140, 240, 176), Plain = rgb(60, 200, 130), Mix = 0.75, Shine = 0.12, Glow = rgb(110, 255, 170),
        Fill = rgb(60, 220, 140), FillT = 0.6, Edge = rgb(170, 255, 205), EdgeT = 0.15, Anim = "Breathe", Portrait = rgb(150, 240, 186),
    },
    Frozen = {
        Tint = rgb(150, 210, 255), Plain = rgb(170, 220, 255), Mix = 0.75, Shine = 0.25, Glow = rgb(226, 248, 255),
        Fill = rgb(170, 225, 255), FillT = 0.45, Edge = rgb(226, 250, 255), EdgeT = 0.05, Anim = "Breathe", Portrait = rgb(185, 226, 255),
    },
    Molten = { -- a dark crust, its glows beating hot like a heart
        Tint = rgb(112, 80, 66), Plain = rgb(60, 40, 36), Mix = 0.8, Glow = rgb(255, 120, 30), GlowHot = rgb(255, 214, 90),
        Fill = rgb(255, 100, 20), FillT = 0.72, Edge = rgb(255, 122, 30), EdgeT = 0.05, Anim = "Heartbeat", Portrait = rgb(214, 140, 110),
    },
    Shocked = { -- electric blue, its edge and glows crackling brighter in quick, uneven pulses
        Tint = rgb(80, 150, 255), Plain = rgb(40, 130, 255), Mix = 0.75, Glow = rgb(90, 240, 255), GlowHot = rgb(235, 255, 255),
        Fill = rgb(20, 140, 255), FillT = 0.45, Edge = rgb(90, 255, 255), EdgeT = 0, Anim = "Crackle", Portrait = rgb(120, 180, 255),
    },
    Rainbow = { -- the spectrum running nose to tail, slowly shifting
        Tint = rgb(255, 255, 255), Plain = rgb(255, 255, 255), Mix = 0.6, Glow = rgb(255, 255, 255), Fill = rgb(255, 255, 255), FillT = 0.62,
        Edge = rgb(255, 255, 255), EdgeT = 0.05, Anim = "Cycle", Portrait = rgb(255, 255, 255),
    },
    Celestial = { -- deep starlit indigo, white-gold glows, a gold edge
        Tint = rgb(84, 84, 196), Plain = rgb(40, 40, 120), Mix = 0.8, Shine = 0.1, Glow = rgb(255, 236, 170),
        Fill = rgb(60, 50, 190), FillT = 0.45, Edge = rgb(255, 225, 140), EdgeT = 0.05, Anim = "Breathe", Portrait = rgb(150, 146, 255),
    },
    Void = { -- near-black, a violet rim breathing round it
        Tint = rgb(40, 28, 60), Plain = rgb(18, 12, 28), Mix = 0.9, Glow = rgb(200, 110, 255),
        Fill = rgb(30, 6, 56), FillT = 0.32, Edge = rgb(200, 110, 255), EdgeT = 0, Anim = "Rim", Portrait = rgb(104, 78, 150),
    },
}
MutationLook.Looks = LOOKS
for id in PetRules.Mutations do
    assert(LOOKS[id], "MutationLook has no look for mutation " .. id)
end

local function reduced()
    return Players.LocalPlayer:GetAttribute("SettingReducedEffects") == true
end

local function multiply(a, b)
    return Color3.new(a.R * b.R, a.G * b.G, a.B * b.B)
end

local function hue(h, s, v)
    return Color3.fromHSV(h % 1, s, v)
end

-- ---------- the pets dressed ----------
local dressed = {} -- [model] = entry

-- the pieces that make its body, and its glows
local function survey(model)
    local body, glows = {}, {}
    for _, part in model:GetDescendants() do
        if part:IsA("BasePart") and part ~= model.PrimaryPart and part.Name ~= "RootPart" and part.Name ~= "HeftShadow"
            and part.Transparency < 0.99 then
            if part.Material == Enum.Material.Neon then
                table.insert(glows, part)
            else
                table.insert(body, part)
            end
        end
    end
    return body, glows
end

function MutationLook.dress(model, mutation, rig, options)
    local id = PetRules.mutation(mutation)
    if not (model and id) then
        return
    end
    options = options or {}
    local look = LOOKS[id]
    model:SetAttribute("PetMutation", id)
    local body, glowParts = survey(model)
    local _, box = model:GetBoundingBox()
    local reach = math.max(box.X, box.Y, box.Z) / 2
    local length = math.max(box.X, box.Y, box.Z)
    local pulse = {}
    if rig then
        for _, glow in rig.pulseGlow or {} do
            pulse[glow.part] = glow
        end
    end
    local entry = { model = model, id = id, look = look, own = options.own == true, priority = options.priority or 0,
        quiet = options.quiet == true or (LOW and options.own ~= true), rig = rig, pulse = pulse, body = {}, glows = {},
        phase = math.random() * 10, reach = reach }

    -- 1. the body
    local pivot = model:GetPivot()
    for _, part in body do
        local appearance = part:FindFirstChildOfClass("SurfaceAppearance")
        local record = { part = part, appearance = appearance }
        -- (a piece's place along the body, for Rainbow's spectrum running nose to tail)
        local here = pivot:PointToObjectSpace(part.Position)
        record.along = (here.Z + here.X * 0.5 + here.Y * 0.3) / math.max(length, 1)
        if appearance then
            record.base = appearance.Color
            if look.Tint then
                appearance.Color = multiply(record.base, look.Tint)
            end
        else
            record.base = part.Color
            if look.Plain then
                part.Color = record.base:Lerp(look.Plain, look.Mix or 0.6)
            end
            if look.Shine then
                part.Reflectance = math.max(part.Reflectance, look.Shine)
            end
        end
        table.insert(entry.body, record)
    end
    -- 2. its glows and its light (its flight trails stay its own)
    local function setGlow(part, color)
        local p = pulse[part]
        if p then
            p.color = color -- (PetRig.update lerps its pulsing glow from this each frame)
        else
            part.Color = color
        end
    end
    entry.setGlow = setGlow
    for _, part in glowParts do
        local p = pulse[part]
        local base = if p then p.color else part.Color
        local color = if look.Brighten then base:Lerp(Color3.new(1, 1, 1), look.Brighten) else look.Glow
        setGlow(part, color)
        table.insert(entry.glows, { part = part, base = base, along = 0 })
    end
    if rig then
        if rig.light and look.Glow then
            rig.light.Color = look.Glow
        end
    end
    dressed[model] = entry
    model.Destroying:Once(function()
        dressed[model] = nil
    end)
end

function MutationLook.setPriority(model, priority, own)
    local entry = dressed[model]
    if entry then
        entry.priority = priority or entry.priority
        if own ~= nil then
            entry.own = own
        end
    end
end

-- ---------- the Highlights, by budget ----------
local function highlightOf(entry)
    local h = entry.highlight
    if h and h.Parent then
        return h
    end
    local look = entry.look
    h = Instance.new("Highlight")
    h.Name = "MutationGlow"
    h.DepthMode = Enum.HighlightDepthMode.Occluded
    h.FillColor = look.Fill or look.Edge
    h.FillTransparency = look.FillT or 1
    h.OutlineColor = look.Edge
    h.OutlineTransparency = look.EdgeT or 0.2
    h.Parent = entry.model
    entry.highlight = h
    return h
end

local function budget()
    local camera = workspace.CurrentCamera
    local eye = camera and camera.CFrame.Position
    local list = {}
    for model, entry in dressed do
        local shown = model:IsDescendantOf(workspace)
        local near = false
        if shown and eye then
            entry.distance = (model:GetPivot().Position - eye).Magnitude
            near = entry.distance <= math.max(ANIMATE_REACH, entry.reach * 2)
        end
        entry.near = near
        if shown and not entry.quiet and eye and entry.distance <= math.max(HIGHLIGHT_REACH, entry.reach * 2) then
            table.insert(list, entry)
        elseif entry.highlight then
            entry.highlight:Destroy()
            entry.highlight = nil
        end
    end
    table.sort(list, function(a, b)
        if a.priority ~= b.priority then
            return a.priority > b.priority
        end
        return a.distance < b.distance
    end)
    for index, entry in list do
        if index <= MAX_HIGHLIGHTS then
            highlightOf(entry)
        elseif entry.highlight then
            entry.highlight:Destroy()
            entry.highlight = nil
        end
    end
end

-- ---------- the animation ----------
local function animate(entry, t, calm)
    local look, anim = entry.look, entry.look.Anim
    local h = entry.highlight
    local p = t + entry.phase
    if anim == "Cycle" then -- the spectrum runs along its body, nose to tail, and round the outline
        local speed = if calm then 0.04 else 0.12
        for _, record in entry.body do
            local c = hue(p * speed + record.along * 0.6, 0.5, 1)
            if record.appearance then
                record.appearance.Color = multiply(record.base, c)
            else
                record.part.Color = record.base:Lerp(c, look.Mix)
            end
        end
        for _, glow in entry.glows do
            entry.setGlow(glow.part, hue(p * speed + 0.33, 0.6, 1))
        end
        if h then
            h.OutlineColor = hue(p * speed + 0.5, 0.75, 1)
            h.FillColor = hue(p * speed + 0.1, 0.6, 1)
        end
    elseif anim == "Heartbeat" then -- a double beat, then a rest: its glows run hot
        local beat = math.max(0, math.sin(p * 4.2)) ^ 6 + 0.6 * math.max(0, math.sin(p * 4.2 - 0.9)) ^ 6
        local k = if calm then 0.3 else math.clamp(beat, 0, 1)
        for _, glow in entry.glows do
            entry.setGlow(glow.part, look.Glow:Lerp(look.GlowHot, k))
        end
        if h then
            h.FillTransparency = look.FillT - 0.18 * k
        end
    elseif anim == "Crackle" then -- quick, uneven brightening of its glows and edge (smooth: never a strobe or a flash)
        local k = if calm then 0.3
            else math.clamp((math.sin(p * 7.3) + math.sin(p * 11.9 + 1.3) + math.sin(p * 4.1)) / 3 * 1.4 + 0.2, 0, 1)
        for _, glow in entry.glows do
            entry.setGlow(glow.part, look.Glow:Lerp(look.GlowHot, k))
        end
        if h then
            h.OutlineTransparency = look.EdgeT + 0.4 * (1 - k)
            h.FillTransparency = look.FillT - 0.12 * k
        end
    elseif h then
        local wave = 0.5 + 0.5 * math.sin(p * (if anim == "Twinkle" then 3 elseif anim == "Rim" then 2.2 else 1.8))
        if calm then
            wave = 0.5
        end
        if anim == "Gleam" or anim == "Breathe" then
            h.FillTransparency = look.FillT - 0.16 * wave
        elseif anim == "Twinkle" then
            h.OutlineTransparency = 0.35 * wave
        elseif anim == "Rim" then
            h.OutlineTransparency = 0.3 * wave
        end
    end
end

-- ---------- portraits and badges ----------
local portraits = {} -- [frame] = its mutation id (Rainbow's colour shifts)
local badges = {}    -- [gradient] = true (Rainbow's)

function MutationLook.color(mutation)
    local id = PetRules.mutation(mutation)
    if id == "Rainbow" then
        return hue(os.clock() * 0.12, 0.55, 1)
    end
    return if id then PetRules.Mutations[id].Color else Color3.new(1, 1, 1)
end

-- A ViewportFrame draws no Highlight: a portrait is tinted instead (Rainbow's tint shifts).
function MutationLook.portrait(frame, mutation)
    local id = PetRules.mutation(mutation)
    portraits[frame] = id
    frame.ImageColor3 = if id then LOOKS[id].Portrait else Color3.new(1, 1, 1)
    if id then
        frame.Destroying:Once(function()
            portraits[frame] = nil
        end)
    end
    return function()
        if portraits[frame] == id then
            MutationLook.portrait(frame, nil)
        end
    end
end

-- its badge: the mutation's name in its colour, a little bolder than a tag (Rainbow's colours run through it)
function MutationLook.badge(mutation)
    local id = PetRules.mutation(mutation)
    if not id then
        return nil
    end
    local color = PetRules.Mutations[id].Color
    local tag = UiKit.tag(id, color)
    tag.Name = "MutationTag"
    tag.BackgroundTransparency = 0.62
    local edge = tag:FindFirstChildOfClass("UIStroke")
    if edge then
        edge.Transparency = 0.1
    end
    if id == "Rainbow" and edge then -- (its edge runs through the spectrum; the word keeps its colour, so it always reads)
        edge.Color = Color3.new(1, 1, 1)
        edge.Thickness = 1.5
        local gradient = Instance.new("UIGradient")
        gradient.Color = RAINBOW
        gradient.Parent = edge
        badges[gradient] = true
        gradient.Destroying:Once(function()
            badges[gradient] = nil
        end)
    end
    return tag
end

-- ---------- the one step ----------
local sinceTick, sinceBudget = 0, 0
RunService.Heartbeat:Connect(function(dt)
    sinceTick += dt
    sinceBudget += dt
    if sinceBudget >= BUDGET_EVERY then
        sinceBudget = 0
        budget()
    end
    if sinceTick < TICK then
        return
    end
    sinceTick = 0
    local t = os.clock()
    local calm = reduced()
    for _, entry in dressed do
        if entry.near and entry.look.Anim then
            animate(entry, t, calm)
        end
    end
    for frame, id in portraits do
        if id == "Rainbow" and frame.Visible and frame.Parent then
            frame.ImageColor3 = hue(t * (if calm then 0.04 else 0.12), 0.35, 1)
        end
    end
    for gradient in badges do
        gradient.Offset = Vector2.new(math.sin(t * 0.8) * 0.5, 0)
    end
end)

return MutationLook
