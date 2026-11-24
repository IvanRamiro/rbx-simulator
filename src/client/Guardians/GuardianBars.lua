-- Each guardian's health bar and its cooldown sign, drawn in the world (BillboardGuis), never on the screen (the owner,
-- 2026-11-16: "The HP bar and cooldown indicator should be world-space UI elements, not player-screen UI. They should remain
-- associated with their respective Guardians and never track or follow individual players"):
--   - THE BAR stands over the guardian's head: an Attachment on its PrimaryPart, so it goes wherever the guardian goes (a
--     chase, a leap, the walk home), and a new model gets a new bar. Across, it follows the head (eased, so a strike doesn't
--     shake it); its height is fixed, ABOVE studs over the top of the guardian's solid silhouette (horns, a mane, the
--     Cinder Roc's crest, Tiangou's eclipse disc), measured as it arrives, so it never covers any of it. The world
--     hides it behind walls (not AlwaysOnTop), it is gone past BAR_DISTANCE from the camera, and its size eases from full
--     close by to a smaller floor far off, never below readable text. It shows the guardian's name, its state in a word, and
--     its health from the replicated Health attribute: the fill eases to it, what was just lost trails behind in white, a
--     gold mark shows where it weakens. Weakened, it flashes gold and its edge keeps pulsing.
--   - THE SIGN stands over the guardian's lair (the model's Home attribute), fixed in the world: while the guardian's
--     cooldown runs (the model's AvailableAt, a server time: Guardian.lua) it counts down "BACK IN 0:27" with a draining bar;
--     when the cooldown ends it says AVAILABLE! in green for a few seconds, then goes. Each guardian has its own.
--   The bar hides while its guardian's sign shows (the guardian rests at its lair, under the sign), so the two never overlap.
--
--   GuardianBars.add(model) / GuardianBars.remove(model)   GuardianController follows the Guardian tag
--   GuardianBars.update(dt)                                every frame
--   GuardianBars.screenBoxes(camera)                       where the shown bars and signs are on the screen, in the HUD's
--                                                          pixels (WorldToScreenPoint): the TAKE marks keep clear of them
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local UI = script.Parent.Parent:WaitForChild("UI")
local HudMetrics = require(UI:WaitForChild("HudMetrics"))
local UiFx = require(UI:WaitForChild("UiFx"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))

local C = UiTheme.Colors
local GuardianBars = {}

local BAR_DISTANCE = 150   -- studs from the camera past which a bar is gone
local SIGN_DISTANCE = 220  -- a sign reads from farther: it says when to come back
local ABOVE = 4.5          -- studs between the top of the guardian and the bar's foot
local FOLLOW = 6           -- how quickly the bar follows the head across (1/s)
local NEAR, FAR = 50, 110  -- studs over which a bar or sign eases from full size to its floor
local AVAILABLE_FOR = 5    -- seconds AVAILABLE! shows once a cooldown ends
local LATE = 1.5           -- seconds past its end before a cooldown reads BACK SOON (the guardian still walking home)

-- the bar's pieces, in its own pixels at scale 1: the shield centred down its left, the name over the state's word, the
-- health track along the bottom, each row clear of the next
local BAR_W, PAD, ICON = 290, UiTheme.Space.M, 34
local V_PAD, NAME_H, STATE_H, TRACK_H, ROW_GAP = 8, 22, 16, 20, 3
local TEXT_LEFT = PAD + ICON + UiTheme.Space.S
local NAME_TOP = V_PAD
local STATE_TOP = NAME_TOP + NAME_H + 1
local TRACK_TOP = STATE_TOP + STATE_H + ROW_GAP
local BAR_H = TRACK_TOP + TRACK_H + V_PAD
local SIGN_W, SIGN_H = 260, 82

local WEAK_GOLD = Color3.fromRGB(255, 200, 70)
local GUARD_BLUE = Color3.fromRGB(150, 200, 255)
local BOUNTY_W = 64 -- the row's room for BOUNTY at its end
local STATE_LOOK = {
    Dormant = { Text = "ASLEEP", Color = C.Muted },
    Guardian = { Text = "AWAKE", Color = Color3.fromRGB(120, 214, 255) },
    Weakened = { Text = "WEAK · TAKE AN EGG", Color = Color3.fromRGB(255, 196, 70) },
    Enraged = { Text = "ANGRY", Color = Color3.fromRGB(255, 96, 50) },
    Returning = { Text = "GOING HOME", Color = C.Muted },
    Resting = { Text = "RESTING", Color = C.Muted },
}
local FILL = { -- the HUD's blue while it guards; gold once weakened; red once enraged
    Calm = ColorSequence.new(Color3.fromRGB(120, 214, 255), Color3.fromRGB(26, 104, 196)),
    Weak = ColorSequence.new(Color3.fromRGB(255, 232, 130), Color3.fromRGB(224, 140, 20)),
    Rage = ColorSequence.new(Color3.fromRGB(255, 110, 120), Color3.fromRGB(176, 22, 44)),
}

local entries = {} -- [model] = its bar and sign

-- How big a bar or sign is drawn at `distance` studs: full close by, easing to a floor far off. A phone draws it a little
-- smaller but keeps its floor high, so its smallest words (15 px authored) stay at a phone's 11 px or more, and a desktop's 10.
local function scaleAt(distance)
    local phone = HudMetrics.class() == "Phone"
    local device = if phone then 0.9 else math.clamp(HudMetrics.scale(), 0.85, 1.15)
    local floor = if phone then 0.9 else 0.78
    local far = math.clamp((distance - NEAR) / (FAR - NEAR), 0, 1)
    return device * (1 - (1 - floor) * far)
end

local function billboard(name, anchor, maxDistance)
    local gui = Instance.new("BillboardGui")
    gui.Name = name
    gui.Adornee = anchor
    gui.AlwaysOnTop = false -- the world in front of it hides it
    gui.LightInfluence = 0  -- the same at night as at noon
    gui.MaxDistance = maxDistance
    gui.SizeOffset = Vector2.new(0, 0.5) -- its foot on the anchor, so it grows upward, away from the guardian
    gui.ClipsDescendants = false
    gui.Enabled = false
    gui.Parent = anchor
    return gui
end

local function formatNumber(n)
    local s = tostring(math.floor(n))
    return (s:reverse():gsub("(%d%d%d)", "%1,"):reverse():gsub("^,", ""))
end

local function formatTime(seconds)
    seconds = math.max(0, math.ceil(seconds))
    return string.format("%d:%02d", seconds // 60, seconds % 60)
end

-- ---------- the bar ----------
local function buildBar(anchor)
    local gui = billboard("GuardianHealthBar", anchor, BAR_DISTANCE)
    local panel = UiKit.panel({ Name = "Panel", Size = UDim2.fromOffset(BAR_W, BAR_H), Brackets = false, Parent = gui })
    local scale = Instance.new("UIScale")
    scale.Parent = panel
    local icon = UiKit.icon(UiTheme.Icons.Guardian, ICON, "Danger")
    icon.AnchorPoint = Vector2.new(0, 0.5)
    icon.Position = UDim2.new(0, PAD, 0.5, 0)
    icon.Parent = panel
    local name = UiKit.label({
        Name = "GuardianName", Font = "Title", TextSize = 18, Position = UDim2.fromOffset(TEXT_LEFT, NAME_TOP),
        Size = UDim2.new(1, -(TEXT_LEFT + PAD), 0, NAME_H), TextTruncate = Enum.TextTruncate.AtEnd, Parent = panel,
    })
    UiKit.outline(name, 1.5)
    local state = UiKit.label({
        Name = "GuardianState", Font = "Heavy", TextSize = 15, Position = UDim2.fromOffset(TEXT_LEFT, STATE_TOP),
        Size = UDim2.new(1, -(TEXT_LEFT + PAD + BOUNTY_W), 0, STATE_H), TextTruncate = Enum.TextTruncate.AtEnd, Parent = panel,
    })
    UiKit.outline(state, 1)
    -- the day's bounty (GameConfig.Bounty): the marked guardian says so, at the end of the state row
    local bountyTag = UiKit.label({
        Name = "BountyTag", Font = "Heavy", TextSize = 15, Text = "BOUNTY", TextColor3 = WEAK_GOLD, AnchorPoint = Vector2.new(1, 0),
        Position = UDim2.new(1, -PAD, 0, STATE_TOP), Size = UDim2.fromOffset(BOUNTY_W, STATE_H), TextXAlignment = Enum.TextXAlignment.Right,
        Visible = false, Parent = panel,
    })
    UiKit.outline(bountyTag, 1)

    local track = Instance.new("Frame")
    track.Name = "Track"
    track.Position = UDim2.fromOffset(TEXT_LEFT, TRACK_TOP)
    track.Size = UDim2.new(1, -(TEXT_LEFT + PAD), 0, TRACK_H)
    track.BackgroundColor3 = C.Well
    track.ClipsDescendants = true
    track.Parent = panel
    UiKit.corner(track, 2)
    UiKit.stroke(track, C.EdgeDim, 0.3)
    local trail = Instance.new("Frame") -- the health just lost, catching up behind the fill
    trail.Name = "Trail"
    trail.BorderSizePixel = 0
    trail.BackgroundColor3 = Color3.fromRGB(236, 246, 255)
    trail.Size = UDim2.fromScale(1, 1)
    trail.Parent = track
    local fill = Instance.new("Frame")
    fill.Name = "Fill"
    fill.BorderSizePixel = 0
    fill.BackgroundColor3 = Color3.new(1, 1, 1)
    fill.Size = UDim2.fromScale(1, 1)
    fill.Parent = track
    local gradient = Instance.new("UIGradient")
    gradient.Rotation = 90
    gradient.Color = FILL.Calm
    gradient.Parent = fill
    local weakMark = Instance.new("Frame") -- where it weakens
    weakMark.Name = "WeakMark"
    weakMark.BorderSizePixel = 0
    weakMark.BackgroundColor3 = C.Highlight
    weakMark.AnchorPoint = Vector2.new(0.5, 0)
    weakMark.Size = UDim2.new(0, 3, 1, 0)
    weakMark.ZIndex = 3
    weakMark.Parent = track
    local health = UiKit.label({
        Name = "Health", Font = "Strong", TextSize = 15, TextXAlignment = Enum.TextXAlignment.Center,
        Size = UDim2.fromScale(1, 1), ZIndex = 4, Parent = track,
    })
    UiKit.outline(health, 1)
    local edge = panel:FindFirstChildOfClass("UIStroke")
    return {
        gui = gui, panel = panel, scale = scale, name = name, state = state, fill = fill, trail = trail, gradient = gradient, bountyTag = bountyTag,
        weakMark = weakMark, health = health, edge = edge, edgeColor = edge.Color, edgeThickness = edge.Thickness,
    }
end

-- ---------- the sign ----------
local function buildSign(anchor)
    local gui = billboard("GuardianCooldownSign", anchor, SIGN_DISTANCE)
    local panel = UiKit.panel({ Name = "Panel", Size = UDim2.fromOffset(SIGN_W, SIGN_H), Brackets = false, Parent = gui })
    local scale = Instance.new("UIScale")
    scale.Parent = panel
    local name = UiKit.label({
        Name = "GuardianName", Font = "Strong", TextSize = 15, TextColor3 = C.Muted, TextXAlignment = Enum.TextXAlignment.Center,
        Position = UDim2.fromOffset(PAD, 8), Size = UDim2.new(1, -2 * PAD, 0, 18), TextTruncate = Enum.TextTruncate.AtEnd,
        Parent = panel,
    })
    UiKit.outline(name, 1)
    local word = UiKit.label({
        Name = "Countdown", Font = "Heavy", TextSize = 26, TextColor3 = C.Highlight, TextXAlignment = Enum.TextXAlignment.Center,
        Position = UDim2.fromOffset(PAD, 27), Size = UDim2.new(1, -2 * PAD, 0, 30), Parent = panel,
    })
    UiKit.outline(word, 2)
    local bar = UiKit.bar({ Name = "Time", Fill = C.Highlight, Position = UDim2.new(0, PAD + 6, 1, -16), Size = UDim2.new(1, -2 * (PAD + 6), 0, 8), Parent = panel })
    return { gui = gui, panel = panel, scale = scale, name = name, word = word, bar = bar, edge = panel:FindFirstChildOfClass("UIStroke") }
end

-- The guardian's head: the Head bone of a skinned guardian (every guardian is skinned now; a Head part is still taken, should a
-- jointed one come back); nil if it has none.
local function findHead(model)
    local head = model:FindFirstChild("Head", true)
    return if head and (head:IsA("Bone") or head:IsA("BasePart")) then head else nil
end

local function headPosition(head)
    return if head:IsA("Bone") then head.TransformedWorldCFrame.Position else head.Position
end

-- The top of the guardian's solid silhouette: its pieces that aren't see-through glow (Tiangou's corona, Pangu's void haze).
local function silhouetteTop(model)
    local top = -math.huge
    for _, part in model:GetDescendants() do
        if part:IsA("BasePart") and part.Transparency < 0.4 then
            local cf, size = part.CFrame, part.Size
            local up = (math.abs(cf.RightVector.Y) * size.X + math.abs(cf.UpVector.Y) * size.Y + math.abs(cf.LookVector.Y) * size.Z) / 2
            top = math.max(top, cf.Position.Y + up)
        end
    end
    return top
end

-- Where the bar's anchor rests, in the PrimaryPart's space, from the guardian as it arrives: over its head, ABOVE studs over
-- the top of its silhouette. Without a head, over the middle of its body.
local function restAnchor(model, head)
    local root = model.PrimaryPart
    local box, size = model:GetBoundingBox()
    local at = if head then headPosition(head) else box.Position
    local top = silhouetteTop(model)
    if top == -math.huge then
        top = box.Position.Y + size.Y / 2
    end
    return root.CFrame:PointToObjectSpace(Vector3.new(at.X, top + ABOVE, at.Z))
end

function GuardianBars.add(model)
    if entries[model] then
        return
    end
    local root = model.PrimaryPart or model:WaitForChild("Root", 10)
    if not (root and root:IsA("BasePart") and model.Parent) then
        return
    end
    local head = findHead(model)
    local rest = restAnchor(model, head)
    local anchor = Instance.new("Attachment")
    anchor.Name = "HealthBarAnchor"
    anchor.Position = rest
    anchor.Parent = root
    -- the sign's anchor: the same point over the guardian standing at its lair, fixed in the world (on the Terrain, which
    -- never moves). Placed once the Home attribute is known.
    local fromPivot = model:GetPivot():PointToObjectSpace(anchor.WorldPosition)
    local signAnchor = Instance.new("Attachment")
    signAnchor.Name = "GuardianSign_" .. model.Name
    signAnchor.Parent = Workspace.Terrain
    local config = GameConfig.Guardians[model:GetAttribute("GuardianId")]
    local entry = {
        model = model, anchor = anchor, signAnchor = signAnchor, fromPivot = fromPivot, head = head, rest = rest,
        bar = buildBar(anchor), sign = buildSign(signAnchor),
        displayName = config and config.DisplayName or model.Name,
        weakenedAt = config and config.WeakenedAt or 0.1,
        shownFill = 1, shownTrail = 1, state = nil, home = nil, total = 0, availableUntil = 0, cooling = false,
    }
    entry.bar.name.Text = entry.displayName
    entry.sign.name.Text = entry.displayName
    entry.bar.weakMark.Position = UDim2.fromScale(entry.weakenedAt, 0)
    entries[model] = entry
end

function GuardianBars.remove(model)
    local entry = entries[model]
    if entry then
        entries[model] = nil
        entry.anchor:Destroy()
        entry.signAnchor:Destroy()
    end
end

-- The cooldown: the sign's words and bar, and whether it shows (counting down, or AVAILABLE! for a moment after).
local function updateSign(entry, now, clock)
    local model, sign = entry.model, entry.sign
    local availableAt = model:GetAttribute("AvailableAt")
    local home = model:GetAttribute("Home")
    if home ~= entry.home and typeof(home) == "CFrame" then
        entry.home = home
        entry.signAnchor.WorldPosition = home:PointToWorldSpace(entry.fromPivot)
    end
    if typeof(availableAt) == "number" then
        local left = availableAt - now
        if not entry.cooling or left > entry.total then
            entry.total = math.max(left, 1) -- the bar drains from where it was first seen (later if its stands empty)
        end
        if not entry.cooling then
            entry.cooling = true
            sign.word.TextColor3 = C.Highlight
            UiKit.setBarColor(sign.bar, C.Highlight)
        end
        -- (past its time it is still walking home; the moment itself is left to the server's word, a frame or two late)
        sign.word.Text = if left > -LATE then "BACK IN " .. formatTime(left) else "BACK SOON"
        UiKit.setBar(sign.bar, math.clamp(left / entry.total, 0, 1), true)
        return true
    end
    if entry.cooling then -- it has just ended: say so, brightly
        entry.cooling = false
        entry.availableUntil = clock + AVAILABLE_FOR
        sign.word.Text = "AVAILABLE!"
        sign.word.TextColor3 = C.BuyBright
        UiKit.setBarColor(sign.bar, C.Buy)
        UiKit.setBar(sign.bar, 1)
        UiFx.flash(sign.panel, C.BuyBright)
        UiFx.sweep(sign.panel, C.BuyBright, 0.8)
        UiFx.pop(sign.word, 1.25)
    end
    return clock < entry.availableUntil
end

-- Across, the anchor eases after the head as it moves (sitting, rearing, turning to strike); its height stays.
local function followHead(entry, dt)
    local head, root = entry.head, entry.model.PrimaryPart
    if not (head and head.Parent and root) then
        return
    end
    local now = root.CFrame:PointToObjectSpace(headPosition(head))
    local at = entry.anchor.Position
    local ease = 1 - math.exp(-dt * FOLLOW)
    entry.anchor.Position = Vector3.new(at.X + (now.X - at.X) * ease, entry.rest.Y, at.Z + (now.Z - at.Z) * ease)
end

local function updateBar(entry, dt)
    local model, bar = entry.model, entry.bar
    local state = model:GetAttribute("State")
    local look = STATE_LOOK[state] or STATE_LOOK.Guardian
    local fresh = entry.state == nil -- just shown: it starts where the guardian is, with no flash for a state reached unseen
    if state ~= entry.state then
        if state == "Weakened" and not fresh then
            UiFx.flash(bar.panel, WEAK_GOLD)
            UiFx.sweep(bar.panel, WEAK_GOLD, 0.8)
        elseif state == "Enraged" and not fresh then
            UiFx.flash(bar.panel, STATE_LOOK.Enraged.Color)
        end
        entry.state = state
        bar.state.Text = look.Text
        bar.state.TextColor3 = look.Color
        bar.gradient.Color = if state == "Enraged" then FILL.Rage elseif state == "Weakened" then FILL.Weak else FILL.Calm
    end
    bar.bountyTag.Visible = model:GetAttribute("Bounty") == true
    -- it has braced for a combo (GameConfig.GuardianReact): the bar says so until the guard is down
    local guarding = model:GetAttribute("Guard") == true
    if guarding then
        bar.state.Text = "GUARDING"
        bar.state.TextColor3 = GUARD_BLUE
        entry.guarding = true
    elseif entry.guarding then
        entry.guarding = nil
        entry.state = nil -- (the word of its state comes back at once)
    end
    local health, maxHealth = model:GetAttribute("Health") or 0, model:GetAttribute("MaxHealth") or 1
    local share = math.clamp(health / maxHealth, 0, 1)
    if fresh then
        entry.shownFill, entry.shownTrail = share, share
    end
    -- eased: a hit slides the fill down, a heal fills it up; the white trail of what was lost follows more slowly
    entry.shownFill += (share - entry.shownFill) * (1 - math.exp(-dt * 12))
    entry.shownTrail = if share > entry.shownTrail then entry.shownFill else entry.shownTrail + (share - entry.shownTrail) * (1 - math.exp(-dt * 2.5))
    bar.fill.Size = UDim2.fromScale(entry.shownFill, 1)
    bar.trail.Size = UDim2.fromScale(math.max(entry.shownTrail, entry.shownFill), 1)
    bar.health.Text = formatNumber(health) .. " / " .. formatNumber(maxHealth)
    -- weakened, its edge keeps pulsing gold
    if state == "Weakened" then
        local pulse = 0.5 + 0.5 * math.sin(os.clock() * 5)
        bar.edge.Color = WEAK_GOLD
        bar.edge.Thickness = 2 + 2 * pulse
    elseif bar.edge.Color == WEAK_GOLD then
        bar.edge.Color = bar.edgeColor
        bar.edge.Thickness = bar.edgeThickness
    end
end

local function fit(piece, width, height, distance)
    local scale = scaleAt(distance)
    piece.scale.Scale = scale
    piece.gui.Size = UDim2.fromOffset(math.round(width * scale), math.round(height * scale))
end

function GuardianBars.update(dt)
    local camera = Workspace.CurrentCamera
    if not camera then
        return
    end
    local eye = camera.CFrame.Position
    local now, clock = Workspace:GetServerTimeNow(), os.clock()
    for model, entry in entries do
        if not model.Parent then
            GuardianBars.remove(model)
            continue
        end
        local signShown = updateSign(entry, now, clock)
        entry.sign.gui.Enabled = signShown
        if signShown then
            fit(entry.sign, SIGN_W, SIGN_H, (entry.signAnchor.WorldPosition - eye).Magnitude)
        end
        local barDistance = (entry.anchor.WorldPosition - eye).Magnitude
        local barShown = not signShown and barDistance <= BAR_DISTANCE + 10
        entry.bar.gui.Enabled = barShown
        if barShown then
            followHead(entry, dt)
            updateBar(entry, dt)
            fit(entry.bar, BAR_W, BAR_H, barDistance)
        else
            entry.state = nil
        end
    end
end

-- The bars and signs on the screen now: { x, y, width, height } in the HUD's pixels (the world may still hide one).
function GuardianBars.screenBoxes(camera)
    local boxes = {}
    local eye = camera.CFrame.Position
    for _, entry in entries do
        for _, piece in { entry.bar, entry.sign } do
            local gui = piece.gui
            local at = gui.Adornee and gui.Adornee.WorldPosition
            if gui.Enabled and at and (at - eye).Magnitude <= gui.MaxDistance then
                local point = camera:WorldToScreenPoint(at)
                if point.Z > 0 then
                    local width, height = gui.Size.X.Offset, gui.Size.Y.Offset
                    table.insert(boxes, { point.X - width / 2, point.Y - height, width, height })
                end
            end
        end
    end
    return boxes
end

return GuardianBars
