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
    local color = spec.Accent
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

local KINDS = { Beast = beast, Bird = bird, Serpent = serpent, Blob = blob, Golem = golem }
local SCALE_BY_RARITY = { Common = 0.9, Uncommon = 0.95, Rare = 1, Epic = 1.05, Legendary = 1.15, Mythical = 1.2, Secret = 1.25 }

function PetArchetypes.scaleFor(rarity)
    return SCALE_BY_RARITY[rarity] or 1
end

function PetArchetypes.build(spec, rarity)
    local build = KINDS[spec.Kind]
    assert(build, "PetArchetypes: unknown Kind " .. tostring(spec.Kind))
    return { Scale = PetArchetypes.scaleFor(rarity), Parts = build(spec) }
end

local function rgb(r, g, b)
    return Color3.fromRGB(r, g, b)
end

PetArchetypes.Specs = {
    NinefoldSpiritSerpent = { Kind = "Serpent", Body = rgb(230, 240, 250), Accent = rgb(130, 255, 210), Belly = rgb(250, 255, 255), Glow = rgb(140, 255, 220), Core = rgb(230, 255, 248), Horns = "Antlers", Whiskers = true, Gems = true },
}

return PetArchetypes
