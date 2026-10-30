local PetArchetypes = {}

local function at(x, y, z, rx, ry, rz)
    return CFrame.new(x, y, z) * CFrame.Angles(math.rad(rx or 0), math.rad(ry or 0), math.rad(rz or 0))
end

local function mirrored(parts, make)
    table.insert(parts, make(-1))
    table.insert(parts, make(1))
end

local function prism(axis, size, cframe, color, extra)
    local spec = { Shape = "Prism", Axis = axis, Size = size, At = cframe, Color = color }
    for key, value in extra or {} do
        spec[key] = value
    end
    return spec
end

local function block(size, cframe, color, neon, transparency)
    return { Shape = "Block", Size = size, At = cframe, Color = color, Neon = neon, Transparency = transparency }
end

local function wedge(size, cframe, color, neon, transparency)
    return { Shape = "Wedge", Size = size, At = cframe, Color = color, Neon = neon, Transparency = transparency }
end

local function diamond(x, y, z, size, color)
    return { Shape = "Block", Size = Vector3.one * size, At = at(x, y, z, 45, 0, 45), Color = color, Neon = true }
end

local function addEyes(parts, spec, apart, y, z, size)
    local iris = spec.GlowEyes and spec.Glow or Color3.fromRGB(25, 30, 60)
    mirrored(parts, function(side)
        local shape = if spec.GlowEyes then Vector3.new(size * 1.1, size * 0.55, 0.06) else Vector3.new(size, size * 1.2, 0.06)
        return block(shape, at(side * apart / 2, y, z, 0, 0, if spec.GlowEyes then side * -12 else 0), iris, spec.GlowEyes)
    end)
    if not spec.GlowEyes then
        mirrored(parts, function(side)
            return block(Vector3.new(size * 0.38, size * 0.38, 0.04), at(side * apart / 2 - size * 0.18, y + size * 0.25, z - 0.04), Color3.new(1, 1, 1), true)
        end)
    end
end

local function addWings(parts, spec, x, y, z, span, chord)
    if not spec.Wings then
        return
    end
    local insect = spec.Wings == "Insect"
    local color = if spec.Wings == "Bat" then spec.Accent else spec.Accent
    mirrored(parts, function(side)
        local lift = if insect then 55 else 35
        return {
            Shape = "Wedge",
            Size = Vector3.new(0.08, span, chord),
            At = at(side * x, y, z) * CFrame.Angles(0, 0, math.rad(side * (lift - 90))) * CFrame.new(0, span / 2, 0),
            Color = if insect then spec.Glow else color,
            Neon = insect,
            Transparency = if insect then 0.25 else nil,
        }
    end)
    if insect then
        mirrored(parts, function(side)
            return {
                Shape = "Wedge",
                Size = Vector3.new(0.07, span * 0.6, chord * 0.7),
                At = at(side * x, y - 0.15, z + 0.15) * CFrame.Angles(0, 0, math.rad(side * (20 - 90))) * CFrame.new(0, span * 0.3, 0),
                Color = spec.Accent,
                Transparency = 0.2,
            }
        end)
    end
end

local function addHorns(parts, spec, x, y, z)
    local horns = spec.Horns
    if horns == "Single" then
        table.insert(parts, wedge(Vector3.new(0.1, 0.55, 0.28), at(0, y + 0.1, z - 0.15, -20, 180, 0), spec.Glow, true))
    elseif horns == "Horns" then
        mirrored(parts, function(side)
            return wedge(Vector3.new(0.1, 0.5, 0.26), at(side * x, y, z, -25, 180, side * -15), spec.Accent)
        end)
    elseif horns == "Curled" then
        mirrored(parts, function(side)
            return prism("X", Vector3.new(0.18, 0.22, 0.22), at(side * (x + 0.12), y - 0.15, z + 0.05), spec.Accent)
        end)
    elseif horns == "Antlers" then
        mirrored(parts, function(side)
            return block(Vector3.new(0.07, 0.55, 0.07), at(side * x, y + 0.12, z, -10, 0, side * -25), spec.Accent)
        end)
        mirrored(parts, function(side)
            return block(Vector3.new(0.05, 0.3, 0.05), at(side * (x + 0.18), y + 0.3, z - 0.05, -30, 0, side * -60), spec.Accent)
        end)
        mirrored(parts, function(side)
            return diamond(side * (x + 0.24), y + 0.42, z - 0.1, 0.09, spec.Glow)
        end)
    end
end

local function addTail(parts, spec, y, z)
    local tail = spec.Tail
    if tail == "Fluffy" then
        table.insert(parts, prism("Y", Vector3.new(0.6, 0.4, 0.42), at(0, y + 0.2, z + 0.2, -35), spec.Body))
        table.insert(parts, prism("Y", Vector3.new(0.25, 0.3, 0.32), at(0, y + 0.5, z + 0.42, -45), spec.Belly))
    elseif tail == "Long" then
        table.insert(parts, prism("Z", Vector3.new(0.85, 0.16, 0.16), at(0, y + 0.1, z + 0.4, 20), spec.Body))
        table.insert(parts, diamond(0, y + 0.3, z + 0.85, 0.16, spec.Glow))
    elseif tail == "Flame" then
        table.insert(parts, wedge(Vector3.new(0.3, 0.55, 0.3), at(0, y + 0.3, z + 0.25, 0, 180, 0), spec.Glow, true))
        table.insert(parts, wedge(Vector3.new(0.18, 0.35, 0.2), at(0, y + 0.42, z + 0.27, 0, 180, 0), spec.Core or spec.Belly, true))
    elseif tail == "Fan" then
        for index, angle in { -28, 0, 28 } do
            table.insert(parts, wedge(Vector3.new(0.08, 0.6, 0.35), at(angle / 100, y + 0.15, z + 0.3, 30, 0, angle), if index == 2 then spec.Glow else spec.Accent, index == 2))
        end
    elseif tail == "Stinger" then
        table.insert(parts, prism("Z", Vector3.new(0.6, 0.14, 0.14), at(0, y + 0.25, z + 0.3, 40), spec.Body))
        table.insert(parts, wedge(Vector3.new(0.12, 0.3, 0.2), at(0, y + 0.55, z + 0.5, 0, 180, 0), spec.Glow, true))
    end
end

local function addExtras(parts, spec, topY)
    if spec.Gems then
        table.insert(parts, diamond(0.85, topY - 0.2, 0.1, 0.15, spec.Glow))
        table.insert(parts, diamond(-0.8, topY - 0.45, 0.4, 0.12, spec.Glow))
        table.insert(parts, diamond(0.6, topY - 0.95, 0.6, 0.1, spec.Glow))
    end
    if spec.Halo then
        for index = 0, 7 do
            local angle = index / 8 * math.pi * 2
            table.insert(parts, block(Vector3.new(0.22, 0.05, 0.08), at(math.cos(angle) * 0.42, topY + 0.25, math.sin(angle) * 0.42 - 0.3, 0, -math.deg(angle) + 90, 0), spec.Glow, true))
        end
    end
end

local function beast(spec)
    local body, accent, belly = spec.Body, spec.Accent, spec.Belly
    local transparency = if spec.Translucent then 0.25 else nil
    local parts = {
        prism("Z", Vector3.new(1.3, 0.8, 0.85), at(0, 0, 0.1), body, { Transparency = transparency }),
        prism("Z", Vector3.new(1.0, 0.3, 0.6), at(0, -0.3, 0.05), belly),
        prism("Z", Vector3.new(0.7, 0.72, 0.78), at(0, 0.5, -0.7), body),
        prism("Z", Vector3.new(0.35, 0.35, 0.45), at(0, 0.36, -1.1), belly),
        block(Vector3.new(0.12, 0.08, 0.06), at(0, 0.46, -1.29), Color3.fromRGB(35, 30, 40)),
    }
    addEyes(parts, spec, 0.42, 0.6, -1.06, 0.2)
    for _, legZ in { -0.3, 0.55 } do
        mirrored(parts, function(side)
            return block(Vector3.new(0.24, 0.55, 0.26), at(side * 0.3, -0.55, legZ), body)
        end)
        mirrored(parts, function(side)
            return block(Vector3.new(0.26, 0.14, 0.3), at(side * 0.3, -0.8, legZ - 0.02), belly)
        end)
    end
    if spec.Ears == "Pointed" then
        mirrored(parts, function(side)
            return wedge(Vector3.new(0.1, 0.42, 0.3), at(side * 0.25, 0.95, -0.6, 0, 0, side * -10), accent)
        end)
    elseif spec.Ears == "Round" then
        mirrored(parts, function(side)
            return prism("X", Vector3.new(0.1, 0.3, 0.3), at(side * 0.32, 0.92, -0.6), accent)
        end)
    elseif spec.Ears == "Long" then
        mirrored(parts, function(side)
            return wedge(Vector3.new(0.1, 0.75, 0.25), at(side * 0.22, 1.1, -0.55, -10, 0, side * -8), accent)
        end)
    end
    addHorns(parts, spec, 0.2, 1.05, -0.62)
    if spec.Mane then
        table.insert(parts, prism("Z", Vector3.new(0.45, 1.0, 1.05), at(0, 0.45, -0.42), accent))
    end
    if spec.Shell then
        table.insert(parts, prism("Z", Vector3.new(1.25, 0.6, 1.05), at(0, 0.35, 0.15), accent))
        mirrored(parts, function(side)
            return diamond(side * 0.28, 0.68, 0.15, 0.14, spec.Glow)
        end)
        table.insert(parts, diamond(0, 0.72, -0.2, 0.15, spec.Glow))
        table.insert(parts, diamond(0, 0.7, 0.5, 0.15, spec.Glow))
    end
    if spec.Stripes then
        for _, z in { -0.2, 0.15, 0.5 } do
            table.insert(parts, block(Vector3.new(0.88, 0.1, 0.1), at(0, 0.3, z), accent))
        end
    end
    if spec.Spikes then
        for index, z in { -0.25, 0.1, 0.45 } do
            table.insert(parts, wedge(Vector3.new(0.08, 0.28 - index * 0.04, 0.25), at(0, 0.5, z, 0, 180, 0), accent))
        end
    end
    if spec.Puffs then
        for _, offset in { Vector3.new(0.35, 0.35, -0.1), Vector3.new(-0.35, 0.3, 0.3), Vector3.new(0, 0.42, 0.45), Vector3.new(0.3, 0.2, 0.6) } do
            table.insert(parts, prism("Y", Vector3.new(0.45, 0.5, 0.5), CFrame.new(offset), belly))
        end
    end
    if spec.Heads and spec.Heads > 1 then
        mirrored(parts, function(side)
            return prism("Z", Vector3.new(0.55, 0.55, 0.6), at(side * 0.55, 0.4, -0.55, 0, side * 15, 0), body)
        end)
        mirrored(parts, function(side)
            return block(Vector3.new(0.14, 0.07, 0.04), at(side * 0.62, 0.48, -0.86, 0, side * 15, side * -12), spec.Glow, true)
        end)
    end
    addWings(parts, spec, 0.35, 0.35, 0.05, 1.0, 0.7)
    addTail(parts, spec, 0.15, 0.7)
    addExtras(parts, spec, 1.2)
    return parts
end

local function bird(spec)
    local body, accent, belly = spec.Body, spec.Accent, spec.Belly
    local parts = {
        prism("Z", Vector3.new(0.95, 0.82, 0.8), at(0, 0, 0), body),
        prism("Z", Vector3.new(0.6, 0.5, 0.62), at(0, -0.12, -0.25), belly),
        prism("Z", Vector3.new(0.56, 0.56, 0.56), at(0, 0.55, -0.38), body),
        prism("Z", Vector3.new(0.32, 0.13, 0.14), at(0, 0.5, -0.78), accent),
    }
    addEyes(parts, spec, 0.3, 0.62, -0.67, 0.15)
    if spec.Crest then
        table.insert(parts, wedge(Vector3.new(0.08, 0.4, 0.32), at(0, 0.98, -0.3), spec.Glow, true))
    end
    if spec.Ears == "Pointed" then
        mirrored(parts, function(side)
            return wedge(Vector3.new(0.08, 0.3, 0.2), at(side * 0.2, 0.95, -0.38), accent)
        end)
    end
    if spec.Legs then
        mirrored(parts, function(side)
            return block(Vector3.new(0.06, 0.55, 0.06), at(side * 0.15, -0.6, 0), accent)
        end)
    end
    addWings(parts, spec, 0.4, 0.15, 0.05, 0.95, 0.7)
    addTail(parts, spec, -0.05, 0.4)
    addExtras(parts, spec, 1.1)
    return parts
end

local function serpent(spec)
    local body, accent, belly = spec.Body, spec.Accent, spec.Belly
    local parts = {}
    local path = {
        { Vector3.new(0, 0, -0.35), 0.5 }, { Vector3.new(0, -0.12, 0.2), 0.48 }, { Vector3.new(0.25, -0.1, 0.65), 0.42 },
        { Vector3.new(0.05, 0.05, 1.05), 0.36 }, { Vector3.new(-0.2, 0.25, 1.35), 0.28 }, { Vector3.new(0, 0.5, 1.6), 0.2 },
    }
    for index, point in path do
        local position, size = point[1], point[2]
        local nextPoint = path[index + 1]
        local look = if nextPoint then CFrame.lookAt(position, nextPoint[1]) else CFrame.lookAt(position, position + Vector3.new(0, 0.5, 1))
        table.insert(parts, prism("Z", Vector3.new(size * 1.3, size, size), look - look.Position + position, body))
        table.insert(parts, prism("Z", Vector3.new(size * 1.1, size * 0.35, size * 0.6), (look - look.Position + position) * CFrame.new(0, -size * 0.38, 0), belly))
        if spec.Spikes and index < #path then
            table.insert(parts, wedge(Vector3.new(0.07, size * 0.55, size * 0.5), (look - look.Position + position) * CFrame.new(0, size * 0.55, 0) * CFrame.Angles(0, math.rad(180), 0), accent))
        end
    end
    table.insert(parts, prism("Z", Vector3.new(0.72, 0.5, 0.56), at(0, 0.28, -0.85), body))
    table.insert(parts, prism("Z", Vector3.new(0.42, 0.3, 0.42), at(0, 0.2, -1.25), belly))
    addEyes(parts, spec, 0.36, 0.42, -1.1, 0.15)
    addHorns(parts, spec, 0.18, 0.62, -0.75)
    if spec.Whiskers then
        mirrored(parts, function(side)
            return block(Vector3.new(0.5, 0.03, 0.03), at(side * 0.38, 0.15, -1.3, 0, side * 25, side * -12), spec.Glow, true)
        end)
    end
    if spec.Legs then
        for _, legZ in { -0.15, 0.6 } do
            mirrored(parts, function(side)
                return block(Vector3.new(0.18, 0.42, 0.2), at(side * 0.3, -0.42, legZ), body)
            end)
        end
    end
    if spec.Heads and spec.Heads > 1 then
        mirrored(parts, function(side)
            return prism("Z", Vector3.new(0.55, 0.38, 0.42), at(side * 0.55, 0.15, -0.55, 0, side * 25, 0), body)
        end)
        mirrored(parts, function(side)
            return block(Vector3.new(0.13, 0.06, 0.04), at(side * 0.65, 0.22, -0.78, 0, side * 25, side * -12), spec.Glow, true)
        end)
    end
    addWings(parts, spec, 0.3, 0.25, 0.1, 1.05, 0.75)
    table.insert(parts, diamond(0, 0.62, 1.75, 0.18, spec.Glow))
    addExtras(parts, spec, 1.1)
    return parts
end

local function blob(spec)
    local body, accent, belly = spec.Body, spec.Accent, spec.Belly
    local transparency = if spec.Translucent then 0.3 else nil
    local parts = {
        prism("X", Vector3.new(1.15, 1.05, 1.05), at(0, 0, 0), body, { Transparency = transparency, Glass = spec.Translucent }),
        block(Vector3.new(0.6, 0.45, 0.06), at(0, -0.2, -0.53), belly),
    }
    addEyes(parts, spec, 0.48, 0.12, -0.58, 0.23)
    mirrored(parts, function(side)
        return block(Vector3.new(0.12, 0.06, 0.04), at(side * 0.38, -0.08, -0.56), Color3.fromRGB(255, 170, 210))
    end)
    if spec.Ears == "Long" then
        mirrored(parts, function(side)
            return wedge(Vector3.new(0.1, 0.55, 0.3), at(side * 0.32, 0.72, -0.05, 0, 0, side * -18), accent)
        end)
    end
    if spec.Antennae then
        mirrored(parts, function(side)
            return block(Vector3.new(0.05, 0.45, 0.05), at(side * 0.2, 0.7, -0.15, -15, 0, side * -20), accent)
        end)
        mirrored(parts, function(side)
            return diamond(side * 0.29, 0.93, -0.22, 0.12, spec.Glow)
        end)
    end
    if spec.Tentacles then
        for index = 0, 4 do
            local angle = index / 5 * math.pi * 2
            table.insert(parts, block(Vector3.new(0.08, 0.7, 0.08), at(math.cos(angle) * 0.32, -0.75, math.sin(angle) * 0.32, 0, 0, math.sin(angle * 3) * 10), spec.Glow, true, 0.15))
        end
    end
    if spec.Puffs then
        for _, offset in { Vector3.new(0.45, 0.35, 0.1), Vector3.new(-0.45, 0.3, 0.15), Vector3.new(0.1, 0.55, 0.25) } do
            table.insert(parts, prism("Y", Vector3.new(0.45, 0.5, 0.5), CFrame.new(offset), belly))
        end
    end
    if spec.Spikes then
        for index, x in { -0.3, 0, 0.3 } do
            table.insert(parts, wedge(Vector3.new(0.08, 0.35, 0.3), at(x, 0.62, 0.05, 0, 180, x * -40), spec.Glow, true))
        end
    end
    if spec.Shell then
        table.insert(parts, prism("Z", Vector3.new(1.15, 0.55, 1.1), at(0, 0.32, 0.12), accent))
        table.insert(parts, block(Vector3.new(0.05, 0.4, 1.0), at(0, 0.5, 0.12), spec.Glow, true))
    end
    if spec.ShellSpiral then
        table.insert(parts, prism("X", Vector3.new(0.5, 0.95, 0.95), at(0, 0.45, 0.42), accent))
        table.insert(parts, prism("X", Vector3.new(0.52, 0.45, 0.45), at(0, 0.5, 0.45), spec.Glow, { Neon = true }))
    end
    addHorns(parts, spec, 0.22, 0.6, -0.15)
    addWings(parts, spec, 0.45, 0.15, 0.1, 0.8, 0.6)
    addTail(parts, spec, -0.1, 0.45)
    addExtras(parts, spec, 1)
    return parts
end

local function ray(spec)
    local body, accent, belly = spec.Body, spec.Accent, spec.Belly
    local parts = {
        prism("Z", Vector3.new(1.3, 0.38, 0.9), at(0, 0, 0), body),
        prism("Z", Vector3.new(1.0, 0.15, 0.7), at(0, -0.2, 0), belly),
        prism("Z", Vector3.new(1.5, 0.08, 0.08), at(0, 0.02, 1.2, 8), accent),
        diamond(0, 0.1, 1.95, 0.16, spec.Glow),
    }
    mirrored(parts, function(side)
        return {
            Shape = "Wedge",
            Size = Vector3.new(0.1, 1.2, 1.1),
            At = at(side * 0.4, 0, 0.1) * CFrame.Angles(0, 0, math.rad(side * (-80))) * CFrame.new(0, 0.6, 0),
            Color = accent,
        }
    end)
    addEyes(parts, spec, 0.42, 0.12, -0.66, 0.16)
    for index = 0, 5 do
        table.insert(parts, diamond((index % 3 - 1) * 0.5, 0.22, (index // 3) * 0.5 - 0.2, 0.08, spec.Glow))
    end
    addExtras(parts, spec, 0.9)
    return parts
end

local function golem(spec)
    local body, accent, belly = spec.Body, spec.Accent, spec.Belly
    local parts = {
        prism("Y", Vector3.new(1.15, 1.05, 0.8), at(0, 0, 0), body),
        prism("Y", Vector3.new(0.62, 0.62, 0.56), at(0, 0.92, -0.05), body),
        prism("Y", Vector3.new(0.6, 0.3, 0.6), at(0, 0.3, -0.05), accent),
        diamond(0, 0.1, -0.44, 0.24, spec.Glow),
    }
    addEyes(parts, spec, 0.28, 1.0, -0.34, 0.15)
    mirrored(parts, function(side)
        return block(Vector3.new(0.38, 0.95, 0.42), at(side * 0.82, -0.05, 0, 0, 0, side * 8), body)
    end)
    mirrored(parts, function(side)
        return block(Vector3.new(0.44, 0.24, 0.48), at(side * 0.84, -0.6, 0), accent)
    end)
    mirrored(parts, function(side)
        return block(Vector3.new(0.42, 0.5, 0.46), at(side * 0.3, -0.78, 0), belly)
    end)
    if spec.Spikes then
        mirrored(parts, function(side)
            return wedge(Vector3.new(0.1, 0.45, 0.3), at(side * 0.7, 0.6, 0, 0, 0, side * -25), spec.Glow, true)
        end)
    end
    addHorns(parts, spec, 0.18, 1.3, -0.05)
    addExtras(parts, spec, 1.4)
    return parts
end

local KINDS = { Beast = beast, Bird = bird, Serpent = serpent, Blob = blob, Ray = ray, Golem = golem }
local SCALE_BY_RARITY = { Common = 0.9, Uncommon = 0.95, Rare = 1, Epic = 1.05, Legendary = 1.15, Mythical = 1.2, Secret = 1.25 }

function PetArchetypes.build(spec, rarity)
    local build = KINDS[spec.Kind]
    assert(build, "PetArchetypes: unknown Kind " .. tostring(spec.Kind))
    return { Scale = SCALE_BY_RARITY[rarity] or 1, Parts = build(spec) }
end

local function rgb(r, g, b)
    return Color3.fromRGB(r, g, b)
end

PetArchetypes.Specs = {
    WindSprite = { Kind = "Blob", Body = rgb(175, 235, 220), Accent = rgb(110, 210, 190), Belly = rgb(230, 250, 245), Glow = rgb(150, 255, 220), Core = rgb(220, 255, 245), Wings = "Insect", Antennae = true },
    CloudSheep = { Kind = "Beast", Body = rgb(245, 245, 250), Accent = rgb(190, 200, 225), Belly = rgb(255, 255, 255), Glow = rgb(200, 220, 255), Core = rgb(255, 255, 255), Ears = "Round", Horns = "Curled", Puffs = true, Tail = "Fluffy" },
    SpiritCrane = { Kind = "Bird", Body = rgb(240, 240, 245), Accent = rgb(40, 45, 60), Belly = rgb(255, 255, 255), Glow = rgb(255, 90, 90), Core = rgb(255, 240, 240), Wings = "Feather", Crest = true, Tail = "Long", Legs = true },
    AzureSkyDragon = { Kind = "Serpent", Body = rgb(70, 150, 240), Accent = rgb(220, 240, 255), Belly = rgb(190, 225, 255), Glow = rgb(150, 220, 255), Core = rgb(220, 245, 255), Horns = "Antlers", Wings = "Feather", Whiskers = true },
    StormhornKirin = { Kind = "Beast", Body = rgb(90, 95, 140), Accent = rgb(255, 230, 90), Belly = rgb(190, 195, 230), Glow = rgb(255, 240, 120), Core = rgb(255, 250, 200), Horns = "Single", Mane = true, Tail = "Long", Gems = true },
    GlacierPuff = { Kind = "Blob", Body = rgb(200, 235, 255), Accent = rgb(150, 210, 255), Belly = rgb(240, 250, 255), Glow = rgb(170, 235, 255), Core = rgb(240, 252, 255), Puffs = true, Spikes = true },
    ThunderJelly = { Kind = "Blob", Body = rgb(255, 230, 110), Accent = rgb(190, 140, 255), Belly = rgb(255, 245, 190), Glow = rgb(255, 240, 120), Core = rgb(255, 250, 200), Tentacles = true, Translucent = true },
    CrystalBeetle = { Kind = "Blob", Body = rgb(90, 70, 150), Accent = rgb(150, 240, 255), Belly = rgb(60, 50, 100), Glow = rgb(160, 245, 255), Core = rgb(220, 250, 255), Shell = true, Horns = "Single", Antennae = true },
    GravityImp = { Kind = "Blob", Body = rgb(80, 60, 120), Accent = rgb(200, 120, 255), Belly = rgb(140, 110, 190), Glow = rgb(210, 140, 255), Core = rgb(240, 210, 255), Horns = "Horns", Wings = "Bat", Gems = true, Tail = "Stinger" },
    ThunderclawDrake = { Kind = "Serpent", Body = rgb(60, 60, 80), Accent = rgb(255, 220, 70), Belly = rgb(110, 110, 140), Glow = rgb(255, 235, 100), Core = rgb(255, 250, 190), Horns = "Horns", Wings = "Bat", Legs = true, Spikes = true },
    FrostfangSerpent = { Kind = "Serpent", Body = rgb(215, 240, 255), Accent = rgb(120, 200, 255), Belly = rgb(250, 255, 255), Glow = rgb(160, 230, 255), Core = rgb(240, 252, 255), Horns = "Antlers", Spikes = true, Gems = true },
    DreamMoth = { Kind = "Blob", Body = rgb(230, 200, 255), Accent = rgb(255, 180, 230), Belly = rgb(250, 235, 255), Glow = rgb(255, 190, 240), Core = rgb(255, 235, 250), Wings = "Insect", Antennae = true },
    CrystalSnail = { Kind = "Blob", Body = rgb(170, 230, 190), Accent = rgb(120, 240, 220), Belly = rgb(210, 250, 225), Glow = rgb(140, 255, 230), Core = rgb(210, 255, 240), ShellSpiral = true, Antennae = true },
    PrismArmadillo = { Kind = "Beast", Body = rgb(150, 130, 120), Accent = rgb(200, 160, 255), Belly = rgb(210, 190, 175), Glow = rgb(190, 170, 255), Core = rgb(240, 230, 255), Ears = "Round", Shell = true, Tail = "Long" },
    LanternWarden = { Kind = "Golem", Body = rgb(90, 110, 90), Accent = rgb(255, 210, 110), Belly = rgb(130, 150, 120), Glow = rgb(255, 220, 120), Core = rgb(255, 245, 200), Halo = true, GlowEyes = true },
    JadeWyrmTurtle = { Kind = "Beast", Body = rgb(90, 160, 110), Accent = rgb(60, 200, 150), Belly = rgb(200, 220, 170), Glow = rgb(110, 255, 190), Core = rgb(210, 255, 230), Shell = true, Horns = "Horns", Tail = "Long", Spikes = true },
    EchoBat = { Kind = "Blob", Body = rgb(90, 80, 120), Accent = rgb(170, 150, 220), Belly = rgb(150, 140, 180), Glow = rgb(200, 170, 255), Core = rgb(230, 220, 255), Ears = "Long", Wings = "Bat" },
    QiClockworkFinch = { Kind = "Bird", Body = rgb(200, 160, 90), Accent = rgb(130, 230, 210), Belly = rgb(230, 200, 140), Glow = rgb(140, 255, 230), Core = rgb(230, 255, 245), Wings = "Feather", Tail = "Fan", Gems = true },
    MoonfangTiger = { Kind = "Beast", Body = rgb(225, 225, 240), Accent = rgb(120, 130, 200), Belly = rgb(250, 250, 255), Glow = rgb(170, 180, 255), Core = rgb(240, 240, 255), Ears = "Pointed", Tail = "Long", Stripes = true },
    ThousandEyedGuardian = { Kind = "Golem", Body = rgb(70, 60, 90), Accent = rgb(255, 200, 90), Belly = rgb(110, 100, 130), Glow = rgb(255, 210, 110), Core = rgb(255, 240, 200), GlowEyes = true, Gems = true, Halo = true },
    NinefoldSpiritSerpent = { Kind = "Serpent", Body = rgb(230, 240, 250), Accent = rgb(130, 255, 210), Belly = rgb(250, 255, 255), Glow = rgb(140, 255, 220), Core = rgb(230, 255, 248), Horns = "Antlers", Whiskers = true, Gems = true },
    WorldrootColossus = { Kind = "Golem", Body = rgb(110, 85, 60), Accent = rgb(120, 220, 110), Belly = rgb(150, 120, 90), Glow = rgb(140, 255, 140), Core = rgb(220, 255, 210), Horns = "Antlers", GlowEyes = true },
    SandPhantom = { Kind = "Blob", Body = rgb(230, 200, 140), Accent = rgb(200, 150, 80), Belly = rgb(245, 225, 180), Glow = rgb(255, 210, 130), Core = rgb(255, 240, 200), Tentacles = true, Translucent = true },
    SolarButterfly = { Kind = "Blob", Body = rgb(255, 200, 80), Accent = rgb(255, 130, 60), Belly = rgb(255, 230, 150), Glow = rgb(255, 210, 90), Core = rgb(255, 245, 190), Wings = "Insect", Antennae = true },
    ObsidianGuardian = { Kind = "Golem", Body = rgb(40, 35, 50), Accent = rgb(180, 90, 255), Belly = rgb(70, 60, 80), Glow = rgb(200, 120, 255), Core = rgb(230, 200, 255), Spikes = true, GlowEyes = true },
    GoldenManeLion = { Kind = "Beast", Body = rgb(240, 190, 90), Accent = rgb(255, 140, 40), Belly = rgb(255, 225, 160), Glow = rgb(255, 200, 90), Core = rgb(255, 245, 200), Ears = "Round", Mane = true, Tail = "Long" },
    DreadfangCerberus = { Kind = "Beast", Body = rgb(45, 40, 50), Accent = rgb(255, 90, 50), Belly = rgb(80, 70, 80), Glow = rgb(255, 110, 60), Core = rgb(255, 200, 170), Heads = 3, Ears = "Pointed", Spikes = true, GlowEyes = true, Tail = "Flame" },
    BonefireDragon = { Kind = "Serpent", Body = rgb(225, 220, 210), Accent = rgb(90, 255, 180), Belly = rgb(180, 175, 165), Glow = rgb(100, 255, 190), Core = rgb(220, 255, 240), Horns = "Horns", Wings = "Bat", Spikes = true, GlowEyes = true },
    PrismaticPhoenix = { Kind = "Bird", Body = rgb(255, 140, 200), Accent = rgb(120, 220, 255), Belly = rgb(255, 230, 160), Glow = rgb(255, 200, 120), Core = rgb(255, 250, 240), Wings = "Feather", Crest = true, Tail = "Fan", Gems = true, Halo = true },
    StarfallFox = { Kind = "Beast", Body = rgb(70, 80, 150), Accent = rgb(255, 230, 140), Belly = rgb(160, 170, 230), Glow = rgb(255, 235, 150), Core = rgb(255, 250, 220), Ears = "Pointed", Tail = "Fluffy", Gems = true },
    CosmicJellyfish = { Kind = "Blob", Body = rgb(150, 110, 230), Accent = rgb(255, 150, 230), Belly = rgb(200, 170, 255), Glow = rgb(255, 170, 240), Core = rgb(255, 230, 250), Tentacles = true, Translucent = true, Gems = true },
    NebulaOwl = { Kind = "Bird", Body = rgb(80, 60, 140), Accent = rgb(220, 160, 255), Belly = rgb(150, 130, 200), Glow = rgb(230, 180, 255), Core = rgb(245, 230, 255), Wings = "Feather", Ears = "Pointed", Gems = true },
    CelestialSnowLeopard = { Kind = "Beast", Body = rgb(235, 240, 250), Accent = rgb(140, 190, 255), Belly = rgb(255, 255, 255), Glow = rgb(170, 215, 255), Core = rgb(245, 250, 255), Ears = "Round", Tail = "Fluffy", Stripes = true, Gems = true },
    CometStag = { Kind = "Beast", Body = rgb(60, 70, 140), Accent = rgb(150, 230, 255), Belly = rgb(130, 140, 210), Glow = rgb(170, 240, 255), Core = rgb(235, 250, 255), Horns = "Antlers", Tail = "Flame", Gems = true },
    CelestialPearlDragon = { Kind = "Serpent", Body = rgb(245, 240, 235), Accent = rgb(255, 210, 140), Belly = rgb(255, 250, 240), Glow = rgb(255, 225, 170), Core = rgb(255, 250, 235), Horns = "Antlers", Whiskers = true, Gems = true, Halo = true },
    EclipseCat = { Kind = "Beast", Body = rgb(30, 30, 45), Accent = rgb(255, 190, 90), Belly = rgb(60, 60, 80), Glow = rgb(255, 200, 110), Core = rgb(255, 235, 190), Ears = "Pointed", Tail = "Long", Halo = true, GlowEyes = true },
    TimekeeperTortoise = { Kind = "Beast", Body = rgb(120, 150, 140), Accent = rgb(255, 215, 120), Belly = rgb(190, 200, 170), Glow = rgb(255, 225, 140), Core = rgb(255, 245, 210), Shell = true, Halo = true, Tail = "Long" },
    GalaxyManta = { Kind = "Ray", Body = rgb(40, 40, 110), Accent = rgb(180, 120, 255), Belly = rgb(90, 90, 170), Glow = rgb(200, 150, 255), Core = rgb(240, 225, 255), Gems = true },
    Shadowcoil = { Kind = "Serpent", Body = rgb(35, 30, 50), Accent = rgb(160, 90, 255), Belly = rgb(70, 60, 90), Glow = rgb(170, 100, 255), Core = rgb(220, 190, 255), Spikes = true, GlowEyes = true },
    RuneSphinx = { Kind = "Beast", Body = rgb(215, 180, 110), Accent = rgb(90, 200, 255), Belly = rgb(240, 215, 160), Glow = rgb(110, 210, 255), Core = rgb(220, 245, 255), Ears = "Pointed", Wings = "Feather", Halo = true, Gems = true },
    ThousandYearDreamEater = { Kind = "Beast", Body = rgb(120, 90, 170), Accent = rgb(255, 170, 230), Belly = rgb(180, 160, 220), Glow = rgb(255, 180, 240), Core = rgb(255, 230, 250), Ears = "Long", Tail = "Fluffy", Gems = true, Halo = true },
    HeavenbreakerApe = { Kind = "Golem", Body = rgb(60, 45, 40), Accent = rgb(255, 200, 80), Belly = rgb(140, 110, 90), Glow = rgb(255, 210, 100), Core = rgb(255, 245, 200), Halo = true, GlowEyes = true, Spikes = true },
    VoidscaleHydra = { Kind = "Serpent", Body = rgb(30, 25, 55), Accent = rgb(140, 70, 255), Belly = rgb(60, 50, 90), Glow = rgb(170, 100, 255), Core = rgb(220, 190, 255), Heads = 3, Spikes = true, GlowEyes = true },
    TheNamelessOne = { Kind = "Golem", Body = rgb(15, 15, 25), Accent = rgb(255, 255, 255), Belly = rgb(40, 40, 60), Glow = rgb(230, 220, 255), Core = rgb(255, 255, 255), GlowEyes = true, Halo = true, Gems = true },
    EternalClockworkDragon = { Kind = "Serpent", Body = rgb(210, 170, 90), Accent = rgb(120, 240, 255), Belly = rgb(240, 210, 150), Glow = rgb(140, 245, 255), Core = rgb(235, 255, 255), Horns = "Horns", Wings = "Feather", Legs = true, Gems = true, Halo = true },
}

return PetArchetypes
