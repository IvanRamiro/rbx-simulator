-- Weapon auras: a realm weapon's blade or spearhead, wrapped in light that follows its real silhouette.
--
--   WeaponAura.attach(body, offset, weaponId, options) -> aura   (nil when the weapon has no profile)
--     body     the weapon's "Body" MeshPart, in a model the caller owns (everything built here is parented to it, so
--              destroying the model destroys the aura; nothing is left behind)
--     offset   the body's Offset from the weapon's origin (weapon space: the point runs along -Z)
--     options  { mine = bool, mode = "drawn" | "sheathed", element = GameConfig.Forge.Elements entry or nil }
--   aura:setDetail(level)   2 everything, 1 edge light and one thin emitter, 0 off (the caller picks it by distance)
--   aura:setMode(mode)      "drawn" at full strength, "sheathed" a quiet version
--   aura:charge(seconds)    the blade gathers light for a moment (a blow's wind-up)
--   aura:strike(seconds)    the blade flares for a moment (a blow)
--   aura:destroy()
--
-- Only the steel is wrapped: WeaponAuraProfiles holds the silhouette measured from each weapon's mesh between where its
-- steel begins and its point (never the grip, hilt, guard collar, sheaths or plumes). The layers, each for a reason:
--   rim     thin lines of light along both edges, chained segment by segment through the measured stations, so they bend with a
--           leaf blade, jump with a lightning blade and trace a crescent; a texture flows along them
--   halo    soft glow ribbons whose width follows the blade's width (the glow hugs the steel, not a floating sphere)
--   skin    sparse particles born from the blade's own volume, locked to it, so they move with every swing
--   shed    particles that leave it and drift off the way a moving thing sheds
--   wake    a trail behind the point
--   scripted extras (lightning, helix, orbit), driven by one shared 20 Hz loop only for auras near the camera
-- Per tier looks: WeaponAuraStyles. Budget: about 40 instances and under 60 particles a second per weapon, none off screen.
local RunService = game:GetService("RunService")

local Profiles = require(script.Parent:WaitForChild("WeaponAuraProfiles"))
local Styles = require(script.Parent:WaitForChild("WeaponAuraStyles"))
local Quality = require(script.Parent.Parent:WaitForChild("Quality"))

local WeaponAura = {}

local TEX = Styles.Textures

-- ---------- small helpers ----------
local function ns(list)
    if typeof(list) == "NumberSequence" then
        return list
    end
    local keys = {}
    for _, k in list do
        table.insert(keys, NumberSequenceKeypoint.new(k[1], k[2], k[3] or 0))
    end
    return NumberSequence.new(keys)
end

local function range(v)
    if typeof(v) == "NumberRange" then
        return v
    elseif type(v) == "number" then
        return NumberRange.new(v)
    end
    return NumberRange.new(v[1], v[2])
end

-- a palette colour by name or a literal
local function paint(palette, c)
    if type(c) == "string" then
        return palette[c]
    end
    return c
end

-- a colour sequence written with palette names: { { 0, "Core" }, { 1, "Main" } }
local function palSeq(palette, list)
    local keys = {}
    for _, k in list do
        table.insert(keys, ColorSequenceKeypoint.new(k[1], paint(palette, k[2])))
    end
    return ColorSequence.new(keys)
end

-- a value (a number, or a palette colour) along a list of { time, value } keypoints, `u` from 0 to 1
local function along(list, u, palette)
    local a, b = list[1], list[#list]
    for i = 1, #list - 1 do
        if u >= list[i][1] and u <= list[i + 1][1] then
            a, b = list[i], list[i + 1]
            break
        end
    end
    local va, vb = a[2], b[2]
    if type(va) == "string" then
        va, vb = palette[va], palette[vb]
    end
    local f = if b[1] > a[1] then math.clamp((u - a[1]) / (b[1] - a[1]), 0, 1) else 0
    if typeof(va) == "Color3" then
        return va:Lerp(vb, f)
    end
    return va + (vb - va) * f
end

local function weaponPoint(offset, x, y, z)
    return offset:PointToObjectSpace(Vector3.new(x, y, z))
end

-- ---------- the blade ----------
-- `want` stations picked evenly along the blade, always the first and the point, skipping the measured zero-width gaps
local function pickStations(blade, want)
    local usable = {}
    for i, s in ipairs(blade) do
        if i == #blade or s[4] > 0 then
            table.insert(usable, s)
        end
    end
    if #usable <= want then
        return usable
    end
    local picked = {}
    for i = 1, want do
        local target = (i - 1) / (want - 1) * blade.Length
        local best, bestGap = usable[1], math.huge
        for _, s in usable do
            local gap = math.abs(s[6] - target)
            if gap < bestGap then
                best, bestGap = s, gap
            end
        end
        if picked[#picked] ~= best then
            table.insert(picked, best)
        end
    end
    if picked[#picked] ~= usable[#usable] then
        table.insert(picked, usable[#usable])
    end
    return picked
end

-- ---------- builder ----------
local Aura = {}
Aura.__index = Aura

local function newAttachment(parent, position, name)
    local a = Instance.new("Attachment")
    a.Name = name or "AuraPoint"
    a.Position = position
    a.Parent = parent
    return a
end

local function newBeam(parent, a0, a1, props)
    local b = Instance.new("Beam")
    b.Attachment0, b.Attachment1 = a0, a1
    b.LightInfluence = 0
    b.LightEmission = props.LightEmission or 1
    b.FaceCamera = props.FaceCamera ~= false
    b.Segments = props.Segments or 4
    b.Width0, b.Width1 = props.W0, props.W1
    b.Color = props.Color
    b.Transparency = props.Transparency
    if props.Texture then
        b.Texture = props.Texture
        b.TextureMode = props.TextureMode or Enum.TextureMode.Wrap
        b.TextureLength = props.TextureLength or 1
        b.TextureSpeed = props.TextureSpeed or 0
        b.Brightness = props.Brightness or 1
    else
        b.Brightness = props.Brightness or 1
    end
    b.ZOffset = props.ZOffset or 0
    b.CurveSize0, b.CurveSize1 = props.Curve0 or 0, props.Curve1 or 0
    b.Parent = parent
    return b
end

-- emitter properties from a style entry (sequences written as lists; colours by palette name)
local function newEmitter(parent, desc, palette)
    local e = Instance.new("ParticleEmitter")
    e.Texture = desc.Texture or TEX.Glow
    e.LightEmission = desc.LightEmission or 1
    e.LightInfluence = 0
    e.Rate = 0
    e.Speed = range(desc.Speed or 0)
    e.Lifetime = range(desc.Lifetime or 0.6)
    e.Size = ns(desc.Size or { { 0, 0.2 }, { 1, 0 } })
    e.Transparency = ns(desc.Transparency or { { 0, 1 }, { 0.15, 0.2 }, { 1, 1 } })
    e.Color = palSeq(palette, desc.Color or { { 0, "Core" }, { 1, "Main" } })
    if desc.Squash then e.Squash = ns(desc.Squash) end
    if desc.Rotation then e.Rotation = range(desc.Rotation) end
    if desc.RotSpeed then e.RotSpeed = range(desc.RotSpeed) end
    if desc.Spread then
        e.SpreadAngle = if type(desc.Spread) == "number" then Vector2.new(desc.Spread, desc.Spread) else Vector2.new(desc.Spread[1], desc.Spread[2])
    end
    if desc.Accel then e.Acceleration = Vector3.new(desc.Accel[1], desc.Accel[2], desc.Accel[3]) end
    if desc.Drag then e.Drag = desc.Drag end
    if desc.Orientation then e.Orientation = Enum.ParticleOrientation[desc.Orientation] end
    if desc.Brightness then e.Brightness = desc.Brightness end
    if desc.ZOffset then e.ZOffset = desc.ZOffset end
    if desc.Inherit then e.VelocityInheritance = desc.Inherit end
    if desc.Flipbook then
        e.FlipbookLayout = Enum.ParticleFlipbookLayout[desc.Flipbook.Layout]
        e.FlipbookMode = Enum.ParticleFlipbookMode[desc.Flipbook.Mode or "Loop"]
        e.FlipbookFramerate = NumberRange.new(desc.Flipbook.Fps or 10)
        e.FlipbookStartRandom = desc.Flipbook.Random == true
    end
    e.LockedToPart = desc.Locked == true
    if desc.Shape then
        e.Shape = Enum.ParticleEmitterShape[desc.Shape]
        e.ShapeStyle = Enum.ParticleEmitterShapeStyle[desc.ShapeStyle or "Volume"]
        e.ShapeInOut = Enum.ParticleEmitterShapeInOut[desc.ShapeInOut or "Outward"]
    end
    e.Enabled = false
    e.Parent = parent
    return e
end

function WeaponAura.attach(body, offset, weaponId, options)
    local tierNumber = tonumber(string.match(weaponId, "%d+"))
    local kind = string.match(weaponId, "^%a+")
    local blade = tierNumber and Profiles.blade(weaponId)
    local style = tierNumber and Styles.Tiers[tierNumber]
    if not blade or not style then
        return nil
    end
    options = options or {}
    local self = setmetatable({
        body = body, weaponId = weaponId, kind = kind, mine = options.mine == true, mode = options.mode or "drawn", detail = 0,
        items = { rim = {}, flow = {}, halo = {}, emitters = {}, extra = {} }, boost = 1, strikeId = 0, ticks = {},
    }, Aura)

    -- palette: the tier's, with a forged element's colours over its Main and Core
    local palette = table.clone(style.Palette)
    if options.element then
        palette.Main, palette.Core = options.element.Color, options.element.Core
        palette.Accent = options.element.Color:Lerp(options.element.Core, 0.5)
    end
    self.palette = palette
    local recipe = style[kind] or {}
    local function pick(name)
        return recipe[name] or style[name]
    end

    local stations = pickStations(blade, recipe.Stations or style.Stations or 6)
    self.stations = stations
    local L = blade.Length
    local folder = Instance.new("Folder")
    folder.Name = "WeaponAura"
    folder.Parent = body
    self.folder = folder
    local at = function(s, dx, dy) -- a weapon-space point beside station s, in the body's space
        return weaponPoint(offset, s[2] + dx, s[3] + dy, s[1])
    end

    -- ---- edges: lines along both sides of the blade, chained segment by segment ----
    -- Rim is the solid hairline (shown at every detail); Flow is a texture running on along the same edges (a bead of light,
    -- a ribbon) and Echo a second, ghostly outline a little way out; both at full detail. Each segment's texture starts where
    -- the last one ended, so the flow runs through the joints.
    for _, layer in { { "Rim", 1, self.items.rim }, { "Flow", 2, self.items.flow }, { "Echo", 2, self.items.flow } } do
        local spec, level, list = pick(layer[1]), layer[2], layer[3]
        if spec then
            local pad = spec.Pad or 0.03
            local edgeAttach = { {}, {} }
            for i, s in stations do
                -- Hug widens the line out from the steel, by at most a quarter stud (a crescent's wide arms stay close)
                local hw = s[4] + math.min(s[4] * ((spec.Hug or 1) - 1), 0.25) + pad
                edgeAttach[1][i] = newAttachment(folder, at(s, -hw, spec.Lift or 0), "EdgeL")
                edgeAttach[2][i] = newAttachment(folder, at(s, hw, spec.Lift or 0), "EdgeR")
            end
            for side = 1, 2 do
                for i = 1, #stations - 1 do
                    local u0, u1 = stations[i][6] / L, stations[i + 1][6] / L
                    local w = (spec.Width or 0.09) * 1.25
                    local taper = spec.Taper or 0.65
                    local beam = newBeam(folder, edgeAttach[side][i], edgeAttach[side][i + 1], {
                        W0 = w * (1 - taper * u0), W1 = w * (1 - taper * u1),
                        -- the colour and the transparency run down the whole edge: each segment takes its own stretch of them
                        Color = ColorSequence.new(along(spec.Color or { { 0, "Core" }, { 1, "Main" } }, u0, palette), along(spec.Color or { { 0, "Core" }, { 1, "Main" } }, u1, palette)),
                        Transparency = NumberSequence.new(along(spec.Transparency or { { 0, 0.15 }, { 1, 0.15 } }, u0), along(spec.Transparency or { { 0, 0.15 }, { 1, 0.15 } }, u1)),
                        Texture = spec.Texture, TextureLength = spec.Length or 1.2, LightEmission = spec.LightEmission,
                        TextureSpeed = (spec.Speed or 1.5) * (if side == 2 and spec.Mirror then -1 else 1),
                        Brightness = spec.Brightness or 2, ZOffset = spec.ZOffset or 0.04, Segments = 3,
                    })
                    if spec.Texture then
                        beam:SetTextureOffset(stations[i][6] / (spec.Length or 1.2))
                    end
                    table.insert(list, { beam = beam, base = beam.Transparency, level = level })
                end
            end
        end
    end

    -- ---- halo: soft glow ribbons that follow the blade's width ----
    local halo = pick("Halo")
    if halo then
        local mids = {}
        for i, s in stations do
            mids[i] = newAttachment(folder, at(s, 0, 0), "HaloMid")
        end
        for i = 1, #stations - 1 do
            local a, b = stations[i], stations[i + 1]
            local k = halo.Scale or 2.4
            local beam = newBeam(folder, mids[i], mids[i + 1], {
                W0 = math.max(a[4] * k, 0.12) + (halo.Add or 0.1), W1 = math.max(b[4] * k, 0.1) + (halo.Add or 0.1) * 0.5,
                Color = palSeq(palette, halo.Color or { { 0, "Main" }, { 1, "Main" } }),
                Transparency = NumberSequence.new(along(halo.Transparency or { { 0, 0.72 }, { 1, 0.78 } }, a[6] / L) * 0.68, along(halo.Transparency or { { 0, 0.72 }, { 1, 0.78 } }, b[6] / L) * 0.68),
                Texture = halo.Texture or TEX.Glow, TextureMode = Enum.TextureMode.Stretch, Brightness = halo.Brightness or 1.6, LightEmission = halo.LightEmission,
                ZOffset = -0.02, Segments = 2,
            })
            table.insert(self.items.halo, { beam = beam, base = beam.Transparency, level = 1 })
        end
    end

    -- ---- emitters: born inside the blade's own volume ----
    local volume
    local function ensureVolume()
        if volume then
            return volume
        end
        local maxHW, maxHT, meanHW = 0.08, 0.04, 0
        for i, s in stations do
            maxHW, maxHT = math.max(maxHW, s[4]), math.max(maxHT, s[5])
            meanHW += s[4] / #stations
        end
        local first, last = stations[1], stations[#stations]
        local length = math.abs(first[1] - last[1])
        local middle = Vector3.new((first[2] + last[2]) / 2, (first[3] + last[3]) / 2, (first[1] + last[1]) / 2)
        volume = Instance.new("Part")
        volume.Name = "AuraVolume"
        volume.Transparency = 1
        volume.CanCollide, volume.CanQuery, volume.CanTouch, volume.CastShadow, volume.Massless = false, false, false, false, true
        volume.Size = Vector3.new(math.max(meanHW * 1.7, 0.12), math.max(maxHT * 1.6, 0.1), length * 0.92)
        local weld = Instance.new("Weld")
        weld.Part0, weld.Part1 = body, volume
        weld.C0 = offset:Inverse() * CFrame.new(middle)
        weld.Parent = volume
        volume.Parent = folder
        return volume
    end
    local anchors = {}
    local function anchorAt(t) -- a point on the blade centre line, t along it (0 foot, 1 point)
        local key = math.floor(t * 100)
        if anchors[key] then
            return anchors[key]
        end
        local target = t * L
        local s = stations[#stations]
        for i = 1, #stations - 1 do
            if stations[i + 1][6] >= target then
                local a, b = stations[i], stations[i + 1]
                local f = (target - a[6]) / math.max(b[6] - a[6], 1e-3)
                s = { a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f, a[3] + (b[3] - a[3]) * f }
                break
            end
        end
        local att = newAttachment(folder, at(s, 0, 0), "Anchor")
        anchors[key] = att
        return att
    end
    for index, desc in ipairs(pick("Emitters") or {}) do
        local parent
        if desc.At == nil or desc.At == "volume" then
            parent = ensureVolume()
        else
            parent = anchorAt(desc.At == "tip" and 1 or desc.At)
        end
        local e = newEmitter(parent, desc, palette)
        -- a spear leads with its point: the glint there is stronger
        local rate = (desc.Rate or 4) * (if desc.At == "tip" and kind == "Spear" then 1.8 else 1)
        table.insert(self.items.emitters, { emitter = e, rate = rate, level = desc.Level or (if index == 1 then 1 else 2), strike = desc.Strike or 1 })
    end

    -- ---- wake: a trail behind the point ----
    local wake = pick("Wake")
    if wake then
        local tip = stations[#stations]
        local from = stations[math.max(1, math.floor(#stations * (wake.From or 0.55)))]
        local a0 = newAttachment(folder, at(tip, 0, 0), "WakeTip")
        local a1 = newAttachment(folder, at(from, (wake.Sideways or 0), 0), "WakeFrom")
        local trail = Instance.new("Trail")
        trail.Name = "AuraWake"
        trail.Attachment0, trail.Attachment1 = a0, a1
        trail.Lifetime = wake.Lifetime or 0.3
        trail.FaceCamera = true
        trail.LightEmission, trail.LightInfluence = 1, 0
        trail.Brightness = wake.Brightness or 2
        trail.Texture = wake.Texture or TEX.Glow
        trail.TextureMode = Enum.TextureMode.Stretch
        trail.Color = palSeq(palette, wake.Color or { { 0, "Core" }, { 1, "Main" } })
        trail.Transparency = ns(wake.Transparency or { { 0, 0.4 }, { 1, 1 } })
        trail.WidthScale = ns(wake.WidthScale or { { 0, 1 }, { 1, 0 } })
        trail.Enabled = false
        trail.Parent = folder
        self.wake = trail
    end

    -- ---- a light at the blade's middle (the player's own weapon only) ----
    if self.mine and style.Light then
        local mid = anchorAt(0.5)
        local light = Instance.new("PointLight")
        light.Color = palette.Main
        light.Range = style.Light.Range or 9
        light.Brightness = 0
        light.Shadows = false
        light.Enabled = false
        light.Parent = mid
        self.light = light
        self.lightBrightness = style.Light.Brightness or 0.9
    end

    -- ---- scripted extras ----
    for _, extra in (pick("Extras") or {}) do
        local builder = WeaponAura.Extras[extra.Kind]
        if builder then
            builder(self, extra, folder, stations, offset, palette, at, anchorAt)
        end
    end

    self:setDetail(0)
    return self
end

local running = {} -- [aura] = true: the auras whose scripted extras tick
local rng = Random.new()

-- ---------- extras ----------
-- Each builds its own attachments, beams or emitters under `folder`, registers what a detail level switches in
-- self.items.extra ({ instance, level }) and an optional per-tick function in self.ticks.
WeaponAura.Extras = {}

-- jagged lightning: a few short beams that jump to new places along the blade several times a second
WeaponAura.Extras.Lightning = function(self, extra, folder, stations, offset, palette, at)
    local count = extra.Count or 2
    local L = stations[#stations][6]
    local items = {}
    for i = 1, count do
        local a0, a1 = newAttachment(folder, weaponPoint(offset, stations[#stations][2], stations[#stations][3], stations[#stations][1]), "Bolt0"), newAttachment(folder, weaponPoint(offset, stations[#stations][2], stations[#stations][3], stations[#stations][1]), "Bolt1")
        local beam = newBeam(folder, a0, a1, {
            W0 = extra.Width or 0.07, W1 = (extra.Width or 0.07) * 0.5,
            Color = palSeq(palette, extra.Color or { { 0, "Core" }, { 1, "Main" } }),
            Transparency = NumberSequence.new(0.1), Texture = extra.Texture, TextureMode = Enum.TextureMode.Stretch,
            Brightness = extra.Brightness or 3, Segments = 5, ZOffset = 0.06,
        })
        beam.Enabled = false
        table.insert(self.items.extra, { beam = beam, level = 2, managed = true })
        items[i] = { a0 = a0, a1 = a1, beam = beam, nextAt = 0 }
    end
    local reach = extra.Reach or 0.2
    self.ticks[#self.ticks + 1] = function(t, rng)
        for _, bolt in items do
            if t >= bolt.nextAt then
                bolt.nextAt = t + (extra.Every or 0.11) * (0.6 + rng:NextNumber() * 0.9)
                if rng:NextNumber() < (extra.Chance or 0.7) then
                    local span = (extra.Span or 1.1) * (0.6 + rng:NextNumber() * 0.8)
                    local from = rng:NextNumber() * math.max(L - span, 0.1)
                    -- two points along the centre line `from` and `from + span`, thrown out to the side
                    local function station(d)
                        local best = stations[#stations]
                        for i = 1, #stations - 1 do
                            if stations[i + 1][6] >= d then
                                local a, b = stations[i], stations[i + 1]
                                local f = (d - a[6]) / math.max(b[6] - a[6], 1e-3)
                                return { a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f, a[3] + (b[3] - a[3]) * f, a[4] + (b[4] - a[4]) * f }
                            end
                        end
                        return best
                    end
                    local s0, s1 = station(from), station(from + span)
                    local side0, side1 = (rng:NextNumber() * 2 - 1) * (s0[4] + reach), (rng:NextNumber() * 2 - 1) * (s1[4] + reach)
                    bolt.a0.Position = weaponPoint(offset, s0[2] + side0, s0[3] + (rng:NextNumber() - 0.5) * 0.1, s0[1])
                    bolt.a1.Position = weaponPoint(offset, s1[2] + side1, s1[3] + (rng:NextNumber() - 0.5) * 0.1, s1[1])
                    bolt.beam.CurveSize0 = (rng:NextNumber() * 2 - 1) * 0.35
                    bolt.beam.CurveSize1 = (rng:NextNumber() * 2 - 1) * 0.35
                    bolt.beam.Enabled = self.detail >= 2
                else
                    bolt.beam.Enabled = false
                end
            end
        end
    end
end

-- ribbons twisting round the blade's axis: `Count` of them, each a short chain of beams between points on a spiral
WeaponAura.Extras.Helix = function(self, extra, folder, stations, offset, palette, at)
    local last = stations[#stations]
    local L = last[6]
    local links = extra.Links or 5
    local ribbons = {}
    for r = 1, (extra.Count or 2) do
        local points = {}
        for k = 1, links + 1 do
            points[k] = newAttachment(folder, weaponPoint(offset, stations[#stations][2], stations[#stations][3], stations[#stations][1]), "Helix")
        end
        local color = extra.Colors and palSeq(palette, extra.Colors[r]) or palSeq(palette, { { 0, "Core" }, { 1, "Main" } })
        for k = 1, links do
            local u = (k - 1) / links
            local beam = newBeam(folder, points[k], points[k + 1], {
                W0 = (extra.Width or 0.07) * (1 - 0.5 * u), W1 = (extra.Width or 0.07) * (1 - 0.5 * (u + 1 / links)),
                Color = color, Transparency = ns(extra.Transparency or { { 0, 0.2 }, { 1, 0.2 } }),
                Texture = extra.Texture, TextureLength = 0.8, TextureSpeed = 1.5, Brightness = extra.Brightness or 2.2, Segments = 3, ZOffset = 0.05,
            })
            beam.Enabled = false
            table.insert(self.items.extra, { beam = beam, level = 2 })
        end
        ribbons[r] = points
    end
    local turns = extra.Turns or 1.6
    local speed = extra.Speed or 2.4
    local radius = extra.Radius or 0.12
    local function sample(d)
        for i = 1, #stations - 1 do
            if stations[i + 1][6] >= d then
                local a, b = stations[i], stations[i + 1]
                local f = (d - a[6]) / math.max(b[6] - a[6], 1e-3)
                return a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f, a[3] + (b[3] - a[3]) * f, a[4] + (b[4] - a[4]) * f, a[5] + (b[5] - a[5]) * f
            end
        end
        return last[1], last[2], last[3], last[4], last[5]
    end
    self.ticks[#self.ticks + 1] = function(t)
        for r, points in ribbons do
            local phase = t * speed * (if extra.Opposed and r % 2 == 0 then -1 else 1) + (r - 1) * math.pi * 2 / #ribbons
            for k, att in points do
                local d = (k - 1) / links * L * (extra.Span or 0.95) + L * (extra.From or 0.02)
                local z, cx, cy, hw, ht = sample(d)
                local a = phase + (k - 1) / links * turns * math.pi * 2
                att.Position = weaponPoint(offset, cx + math.cos(a) * (hw + radius), cy + math.sin(a) * (ht + radius * 0.8), z)
            end
        end
    end
end

-- bright points circling the blade, each leaving a little trail of particles behind it
WeaponAura.Extras.Orbit = function(self, extra, folder, stations, offset, palette)
    local last = stations[#stations]
    local L = last[6]
    local orbs = {}
    for i = 1, (extra.Count or 3) do
        local att = newAttachment(folder, weaponPoint(offset, stations[#stations][2], stations[#stations][3], stations[#stations][1]), "Orb")
        local e = newEmitter(att, extra.Emitter or { Texture = TEX.Star, Rate = 12, Lifetime = 0.5, Size = { { 0, 0.18 }, { 1, 0 } } }, palette)
        table.insert(self.items.emitters, { emitter = e, rate = (extra.Emitter or {}).Rate or 10, level = 2, strike = 1 })
        orbs[i] = { att = att, phase = (i - 1) / (extra.Count or 3) }
    end
    local function sample(d)
        for i = 1, #stations - 1 do
            if stations[i + 1][6] >= d then
                local a, b = stations[i], stations[i + 1]
                local f = (d - a[6]) / math.max(b[6] - a[6], 1e-3)
                return a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f, a[3] + (b[3] - a[3]) * f, a[4] + (b[4] - a[4]) * f, a[5] + (b[5] - a[5]) * f
            end
        end
        return last[1], last[2], last[3], last[4], last[5]
    end
    self.ticks[#self.ticks + 1] = function(t)
        for i, orb in orbs do
            local along = (t * (extra.Rise or 0.35) + orb.phase) % 1
            local z, cx, cy, hw, ht = sample(along * L * 0.96)
            local a = t * (extra.Speed or 3) * (if i % 2 == 0 then -1 else 1) + orb.phase * math.pi * 2
            local r = (extra.Radius or 0.2)
            orb.att.Position = weaponPoint(offset, cx + math.cos(a) * (hw + r), cy + math.sin(a) * (ht + r), z)
        end
    end
end

-- a glint that runs up the blade from the foot to the point every few seconds
WeaponAura.Extras.Sweep = function(self, extra, folder, stations, offset, palette)
    local last = stations[#stations]
    local L = last[6]
    local att = newAttachment(folder, weaponPoint(offset, stations[#stations][2], stations[#stations][3], stations[#stations][1]), "Sweep")
    local e = newEmitter(att, extra.Emitter or { Texture = TEX.Star, Lifetime = 0.45, Size = { { 0, 0.5 }, { 1, 0 } } }, palette)
    e.Rate = 0
    e.Enabled = true -- (Emit below; the rate stays 0)
    local startAt = 0
    local function sample(d)
        for i = 1, #stations - 1 do
            if stations[i + 1][6] >= d then
                local a, b = stations[i], stations[i + 1]
                local f = (d - a[6]) / math.max(b[6] - a[6], 1e-3)
                return a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f, a[3] + (b[3] - a[3]) * f
            end
        end
        return last[1], last[2], last[3]
    end
    local every, runTime = extra.Every or 3, extra.Run or 0.55
    self.ticks[#self.ticks + 1] = function(t, rng)
        if startAt == 0 then
            startAt = t + rng:NextNumber() * every
        end
        local u = (t - startAt) / runTime
        if u >= 0 and u <= 1 then
            local z, cx, cy = sample(u * L)
            att.Position = weaponPoint(offset, cx, cy, z)
            e:Emit(extra.Burst or 2)
        elseif u > 1 then
            startAt = t + every * (0.7 + rng:NextNumber() * 0.6)
        end
    end
end

-- ---------- state ----------
-- what each layer shows at a detail level and mode
local MODE_QUIET = 0.4 -- sheathed: a share of the drawn strength

local function applySequence(base, factor)
    -- raise a transparency list toward 1 by `factor` (0 keeps it, 1 hides it)
    local keys = {}
    for _, k in ns(base).Keypoints do
        table.insert(keys, NumberSequenceKeypoint.new(k.Time, k.Value + (1 - k.Value) * factor, k.Envelope))
    end
    return NumberSequence.new(keys)
end

function Aura:refresh()
    local detail, drawn = self.detail, self.mode == "drawn"
    local quiet = if drawn then 0 else 0.55
    local lowScale = Quality.Low and 0.5 or 1
    for _, item in self.items.rim do
        item.beam.Enabled = detail >= 1
        if self.quiet ~= quiet then
            item.beam.Transparency = applySequence(item.base, quiet)
        end
    end
    for _, item in self.items.flow do
        item.beam.Enabled = detail >= 2 and drawn
    end
    for _, item in self.items.halo do
        item.beam.Enabled = detail >= 1 and (drawn or detail >= 2)
        if self.quiet ~= quiet then
            item.beam.Transparency = applySequence(item.base, quiet)
        end
    end
    for _, item in self.items.emitters do
        local on = detail >= item.level and (drawn or item.level <= 1)
        item.emitter.Rate = if on then item.rate * lowScale * (if drawn then 1 else MODE_QUIET) * (if self.boost > 1 then self.boost else 1) else 0
        item.emitter.Enabled = on
    end
    for _, item in self.items.extra do
        if not (detail >= item.level and drawn) then
            item.beam.Enabled = false
        elseif not item.managed then -- (a bolt is switched on by its own tick)
            item.beam.Enabled = true
        end
    end
    if self.wake then
        self.wake.Enabled = detail >= 2 and drawn
    end
    if self.light then
        self.light.Enabled = detail >= 2 and drawn
        self.light.Brightness = self.lightBrightness * self.boost
    end
    self.quiet = quiet
    self.folder:SetAttribute("Boost", self.boost) -- the blade's flare (1 at rest), for tests
    local ticking = #self.ticks > 0 and detail >= 2 and drawn
    if ticking and not running[self] then
        for _, tick in self.ticks do
            tick(os.clock(), rng)
        end
    end
    WeaponAura.register(self, ticking)
end

function Aura:setDetail(level)
    if self.dead or level == self.detail then
        return
    end
    self.detail = level
    self:refresh()
end

function Aura:setMode(mode)
    if self.dead or mode == self.mode then
        return
    end
    self.mode = mode
    self:refresh()
end

-- a blow's wind-up: the blade gathers light for `seconds` (the flare of the blow itself, strike, follows and takes over)
function Aura:charge(seconds)
    if self.dead or self.detail < 1 then
        return
    end
    self.strikeId += 1
    local mine = self.strikeId
    self.boost = math.max(self.boost, 1.5)
    self:refresh()
    task.delay(seconds, function()
        if not self.dead and self.strikeId == mine then
            self.boost = 1
            self:refresh()
        end
    end)
end

-- a blow: the blade flares for `seconds`
function Aura:strike(seconds)
    if self.dead or self.detail < 1 then
        return
    end
    self.strikeId += 1
    local mine = self.strikeId
    self.boost = 2.2
    self:refresh()
    for _, item in self.items.emitters do
        if item.strike > 1 then
            item.emitter:Emit(math.floor(item.strike))
        end
    end
    task.delay(seconds or 0.35, function()
        if not self.dead and self.strikeId == mine then
            self.boost = 1
            self:refresh()
        end
    end)
end

function Aura:destroy()
    if self.dead then
        return
    end
    self.dead = true
    WeaponAura.register(self, false)
    for _, item in self.items.emitters do
        item.emitter.Enabled = false
    end
    if self.folder then
        self.folder:Destroy()
    end
end

-- ---------- the shared loop for scripted extras ----------
local connection
local acc = 0
local TICK = 1 / 20

function WeaponAura.register(aura, on)
    if on then
        running[aura] = true
    else
        running[aura] = nil
    end
    if on and not connection then
        connection = RunService.Heartbeat:Connect(function(dt)
            acc += dt
            if acc < TICK then
                return
            end
            acc = 0
            local t = os.clock()
            for a in running do
                for _, tick in a.ticks do
                    tick(t, rng)
                end
            end
        end)
    elseif connection and next(running) == nil then
        connection:Disconnect()
        connection = nil
    end
end

-- counts for tests: how many auras tick
function WeaponAura.running()
    local n = 0
    for _ in running do
        n += 1
    end
    return n
end

return WeaponAura
