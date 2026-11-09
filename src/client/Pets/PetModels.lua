local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local PetRig = require(script.Parent:WaitForChild("PetRig"))

local meshFolder = ReplicatedStorage:WaitForChild("PetMeshes", 10)

local PetModels = {}

-- [model] = its rig. A rig holds its model, so a weak key would never free it: each entry goes
-- when its model is destroyed (keep).
local rigs = {}
local function keep(model, rig)
    rigs[model] = rig
    model.Destroying:Once(function()
        rigs[model] = nil
    end)
end

function PetModels.getRig(model)
    return rigs[model]
end

PetModels.SIZE = 2

local function at(x, y, z, rx, ry, rz)
    return CFrame.new(x, y, z) * CFrame.Angles(math.rad(rx or 0), math.rad(ry or 0), math.rad(rz or 0))
end

local BLACK = Color3.fromRGB(25, 25, 35)

local function mirrored(parts, make)
    table.insert(parts, make(-1))
    table.insert(parts, make(1))
end

local function wing(side, x, y, z, span, chord, lift, color, neon)
    return {
        Shape = "Wedge",
        Size = Vector3.new(0.08, span, chord),
        At = at(side * x, y, z) * CFrame.Angles(0, 0, math.rad(side * (lift - 90))) * CFrame.new(0, span / 2, 0),
        Color = color,
        Neon = neon,
    }
end

local function eyes(parts, apart, y, z, size, iris)
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(size, size * 1.2, 0.06), At = at(side * apart / 2, y, z), Color = iris or Color3.fromRGB(25, 35, 90) }
    end)
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(size * 0.38, size * 0.38, 0.04), At = at(side * apart / 2 - size * 0.18, y + size * 0.25, z - 0.04), Color = Color3.new(1, 1, 1), Neon = true }
    end)
end

local function diamond(x, y, z, size, color)
    return { Shape = "Block", Size = Vector3.new(size, size, size), At = at(x, y, z, 45, 0, 45), Color = color, Neon = true }
end

local function lunarHopper()
    local fur = Color3.fromRGB(160, 145, 235)
    local pale = Color3.fromRGB(210, 200, 255)
    local glow = Color3.fromRGB(110, 140, 255)
    local parts = {
        { Shape = "Prism", Axis = "Y", Size = Vector3.new(0.95, 0.9, 1.1), At = at(0, 0, 0.1), Color = fur },
        { Shape = "Prism", Axis = "Y", Size = Vector3.new(0.55, 0.55, 0.3), At = at(0, 0, -0.42), Color = pale },
        { Shape = "Prism", Axis = "X", Size = Vector3.new(0.85, 0.75, 0.75), At = at(0, 0.72, -0.3), Color = pale },
        { Shape = "Block", Size = Vector3.new(0.1, 0.07, 0.05), At = at(0, 0.6, -0.69), Color = Color3.fromRGB(255, 160, 200) },
        { Shape = "Prism", Axis = "Y", Size = Vector3.new(0.3, 0.3, 0.3), At = at(0, -0.05, 0.7), Color = pale },
        diamond(0.3, 0.2, 0.55, 0.08, pale),
        diamond(-0.25, -0.1, 0.5, 0.07, pale),
        diamond(0.75, 1.25, 0.1, 0.12, glow),
        diamond(-0.7, 0.95, 0.35, 0.09, glow),
    }
    eyes(parts, 0.42, 0.78, -0.69, 0.24)
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.2, 0.95, 0.12), At = at(side * 0.2, 1.45, -0.22, -10, 0, side * -12), Color = fur }
    end)
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.09, 0.7, 0.04), At = at(side * 0.2, 1.42, -0.29, -10, 0, side * -12), Color = glow, Neon = true }
    end)
    mirrored(parts, function(side)
        return { Shape = "Prism", Size = Vector3.new(0.3, 0.35, 0.65), At = at(side * 0.4, -0.38, 0.15), Color = fur }
    end)
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.18, 0.3, 0.2), At = at(side * 0.2, -0.38, -0.45), Color = pale }
    end)
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.04, 0.12, 0.38), At = at(side * 0.49, 0.05, 0.15, 30, 0, 0), Color = glow, Neon = true }
    end)
    return { Scale = 1, Parts = parts }
end

local function voltFox()
    local fur = Color3.fromRGB(255, 205, 45)
    local dark = Color3.fromRGB(45, 40, 40)
    local white = Color3.fromRGB(255, 248, 225)
    local spark = Color3.fromRGB(255, 240, 120)
    local parts = {
        { Shape = "Prism", Size = Vector3.new(0.75, 0.7, 1.2), At = at(0, 0, 0.1), Color = fur },
        { Shape = "Wedge", Size = Vector3.new(0.5, 0.45, 0.32), At = at(0, 0.12, -0.6, 0, 180, 180), Color = white },
        { Shape = "Prism", Size = Vector3.new(0.8, 0.7, 0.7), At = at(0, 0.5, -0.7), Color = fur },
        { Shape = "Wedge", Size = Vector3.new(0.42, 0.3, 0.45), At = at(0, 0.36, -1.22), Color = white },
        { Shape = "Block", Size = Vector3.new(0.13, 0.1, 0.08), At = at(0, 0.5, -1.45), Color = dark },
        { Shape = "Block", Size = Vector3.new(0.3, 0.3, 0.6), At = at(0.15, 0.3, 0.9, 40, -20, 0), Color = fur },
        { Shape = "Block", Size = Vector3.new(0.4, 0.4, 0.65), At = at(0.4, 0.75, 1.1, -30, -30, 0), Color = fur },
        { Shape = "Block", Size = Vector3.new(0.45, 0.45, 0.6), At = at(0.65, 1.2, 1.25, 35, -40, 0), Color = fur },
        { Shape = "Wedge", Size = Vector3.new(0.4, 0.45, 0.4), At = at(0.8, 1.62, 1.32, 0, 140, 0), Color = white },
        { Shape = "Block", Size = Vector3.new(0.42, 0.08, 0.3), At = at(0.4, 1, 1.15, -30, -30, 0), Color = dark },
    }
    eyes(parts, 0.42, 0.58, -1.06, 0.2, Color3.fromRGB(60, 40, 20))
    mirrored(parts, function(side)
        return { Shape = "Wedge", Size = Vector3.new(0.12, 0.7, 0.42), At = at(side * 0.27, 1.1, -0.66, 0, 90 * side), Color = fur }
    end)
    mirrored(parts, function(side)
        return { Shape = "Wedge", Size = Vector3.new(0.13, 0.25, 0.16), At = at(side * 0.27, 1.38, -0.66, 0, 90 * side), Color = dark }
    end)
    for _, z in { -0.3, 0.45 } do
        mirrored(parts, function(side)
            return { Shape = "Block", Size = Vector3.new(0.2, 0.25, 0.2), At = at(side * 0.25, -0.38, z), Color = fur }
        end)
        mirrored(parts, function(side)
            return { Shape = "Wedge", Size = Vector3.new(0.21, 0.22, 0.21), At = at(side * 0.25, -0.6, z, 0, 180, 0), Color = dark }
        end)
    end
    table.insert(parts, diamond(0.7, 0.9, 0.3, 0.12, spark))
    table.insert(parts, diamond(-0.65, 0.6, 0.9, 0.1, spark))
    return { Scale = 1.05, Parts = parts }
end

local function astralWhale()
    local deep = Color3.fromRGB(55, 75, 195)
    local belly = Color3.fromRGB(200, 222, 255)
    local crystal = Color3.fromRGB(95, 110, 250)
    local star = Color3.fromRGB(235, 240, 255)
    local parts = {
        { Shape = "Prism", Size = Vector3.new(1, 0.9, 1.7), At = at(0, 0, 0), Color = deep },
        { Shape = "Prism", Size = Vector3.new(0.85, 0.75, 0.45), At = at(0, -0.05, -1.02), Color = deep },
        { Shape = "Prism", Size = Vector3.new(0.7, 0.32, 1.6), At = at(0, -0.33, -0.15), Color = belly },
        { Shape = "Prism", Size = Vector3.new(0.5, 0.45, 0.7), At = at(0, 0.12, 1.15, -12), Color = deep },
        { Shape = "Wedge", Size = Vector3.new(0.1, 0.35, 0.35), At = at(0, 0.6, -0.35, 0, 180, 0), Color = crystal, Neon = true },
        { Shape = "Wedge", Size = Vector3.new(0.1, 0.5, 0.45), At = at(0, 0.68, 0.1, 0, 180, 0), Color = crystal, Neon = true },
        { Shape = "Wedge", Size = Vector3.new(0.1, 0.32, 0.32), At = at(0, 0.55, 0.55, 0, 180, 0), Color = crystal, Neon = true },
        diamond(0.32, 0.25, -0.4, 0.07, star),
        diamond(-0.3, 0.1, 0.2, 0.06, star),
        diamond(0.2, 0.38, 0.5, 0.06, star),
        diamond(-0.15, 0.42, -0.75, 0.05, star),
    }
    eyes(parts, 0.8, 0.02, -0.98, 0.14, Color3.fromRGB(20, 25, 70))
    mirrored(parts, function(side)
        return wing(side, 0.42, -0.25, -0.3, 0.75, 0.55, -25, crystal, true)
    end)
    mirrored(parts, function(side)
        return wing(side, 0.05, 0.2, 1.35, 0.55, 0.55, 20, crystal, true)
    end)
    return { Scale = 1.25, Parts = parts }
end

local function nineTailMoonfox()
    local fur = Color3.fromRGB(245, 245, 255)
    local lilac = Color3.fromRGB(190, 160, 255)
    local violet = Color3.fromRGB(150, 110, 255)
    local parts = {
        { Shape = "Prism", Size = Vector3.new(0.75, 0.7, 1.2), At = at(0, 0, 0.1), Color = fur },
        { Shape = "Prism", Size = Vector3.new(0.8, 0.7, 0.7), At = at(0, 0.45, -0.65), Color = fur },
        { Shape = "Wedge", Size = Vector3.new(0.4, 0.3, 0.45), At = at(0, 0.32, -1.18), Color = fur },
        { Shape = "Block", Size = Vector3.new(0.12, 0.12, 0.05), At = at(0, 0.72, -1.01, 0, 0, 45), Color = lilac, Neon = true },
    }
    mirrored(parts, function(side)
        return { Shape = "Wedge", Size = Vector3.new(0.12, 0.5, 0.35), At = at(0.25 * side, 0.92, -0.6, 0, 90 * side), Color = fur }
    end)
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.15, 0.1, 0.06), At = at(0.2 * side, 0.52, -1.01), Color = violet, Neon = true }
    end)
    for tail = 1, 9 do
        local base = at(0, 0.15, 0.75, 25, 0, -60 + (tail - 1) * 15)
        table.insert(parts, { Shape = "Wedge", Size = Vector3.new(0.12, 0.85, 0.25), At = base * CFrame.new(0, 0.5, 0), Color = fur })
        table.insert(parts, { Shape = "Block", Size = Vector3.new(0.15, 0.15, 0.15), At = base * CFrame.new(0, 0.98, 0) * CFrame.Angles(0, 0, math.rad(45)), Color = lilac, Neon = true })
    end
    return { Scale = 1.2, Parts = parts }
end

local function originSerpent()
    local silver = Color3.fromRGB(225, 232, 236)
    local teal = Color3.fromRGB(60, 215, 185)
    local parts = {}
    for segment = 0, 9 do
        local t = segment / 9
        local angle = t * 2.6 * math.pi
        local radius = 0.65 - 0.2 * t
        local size = 0.55 - 0.2 * t
        local position = Vector3.new(math.cos(angle) * radius, -0.4 + t, math.sin(angle) * radius)
        local tangent = Vector3.new(-math.sin(angle), 0.35, math.cos(angle))
        local placement = CFrame.lookAt(position, position + tangent)
        table.insert(parts, {
            Shape = "Block",
            Size = Vector3.new(size, size, size * 1.4),
            At = placement,
            Color = if segment % 3 == 1 then teal else silver,
            Neon = segment % 3 == 1,
        })
        if segment % 2 == 0 then
            table.insert(parts, {
                Shape = "Wedge",
                Size = Vector3.new(0.06, size * 0.5, size * 0.6),
                At = placement * CFrame.new(0, size * 0.6, 0) * CFrame.Angles(0, math.pi, 0),
                Color = teal,
            })
        end
    end
    table.insert(parts, { Shape = "Prism", Size = Vector3.new(0.6, 0.45, 0.8), At = at(0, 0.85, -0.45), Color = silver })
    table.insert(parts, { Shape = "Wedge", Size = Vector3.new(0.42, 0.25, 0.38), At = at(0, 0.8, -0.98), Color = silver })
    mirrored(parts, function(side)
        return { Shape = "Wedge", Size = Vector3.new(0.08, 0.5, 0.55), At = at(side * 0.2, 1.22, -0.25, -25, 180, side * -15), Color = teal }
    end)
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.4, 0.04, 0.04), At = at(side * 0.38, 0.72, -1, 0, side * 30, side * -15), Color = teal, Neon = true }
    end)
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.13, 0.1, 0.06), At = at(side * 0.18, 0.95, -0.86), Color = teal, Neon = true }
    end)
    local orbCenter = at(0.75, 1.65, 0.25)
    table.insert(parts, { Shape = "Prism", Axis = "Y", Size = Vector3.new(0.38, 0.38, 0.38), At = orbCenter, Color = teal, Neon = true })
    for index = 0, 9 do
        local angle = index / 10 * 2 * math.pi
        table.insert(parts, {
            Shape = "Block",
            Size = Vector3.new(0.05, 0.04, 0.22),
            At = orbCenter * CFrame.Angles(math.rad(20), 0, math.rad(-15))
                * CFrame.new(math.cos(angle) * 0.42, 0, math.sin(angle) * 0.42)
                * CFrame.Angles(0, -angle, 0),
            Color = teal,
            Neon = true,
        })
    end
    return { Scale = 1.25, Parts = parts }
end

local function mossGolem()
    local stone = Color3.fromRGB(120, 120, 115)
    local moss = Color3.fromRGB(95, 160, 75)
    local glow = Color3.fromRGB(170, 255, 140)
    local parts = {
        { Shape = "Prism", Axis = "Y", Size = Vector3.new(1.25, 1.1, 0.95), At = at(0, 0, 0), Color = stone },
        { Shape = "Prism", Axis = "Y", Size = Vector3.new(0.8, 0.65, 0.7), At = at(0, 0.85, -0.1), Color = stone },
        { Shape = "Prism", Axis = "Y", Size = Vector3.new(1.35, 0.25, 1.05), At = at(0, 0.55, 0), Color = moss },
        { Shape = "Prism", Axis = "Y", Size = Vector3.new(0.85, 0.2, 0.75), At = at(0, 1.2, -0.1), Color = moss },
        { Shape = "Block", Size = Vector3.new(0.1, 0.4, 0.1), At = at(0, 1.45, -0.1), Color = moss },
        { Shape = "Wedge", Size = Vector3.new(0.08, 0.15, 0.35), At = at(0.12, 1.65, -0.1, 0, 90, -30), Color = glow, Neon = true },
    }
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.17, 0.14, 0.06), At = at(0.2 * side, 0.9, -0.46), Color = glow, Neon = true }
    end)
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.4, 0.95, 0.45), At = at(0.82 * side, -0.1, 0, 0, 0, 8 * side), Color = stone }
    end)
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.45, 0.45, 0.5), At = at(0.32 * side, -0.75, 0), Color = stone }
    end)
    return { Scale = 0.9, Parts = parts }
end

local function myceliumSprite()
    local cap = Color3.fromRGB(70, 215, 195)
    local stem = Color3.fromRGB(235, 230, 215)
    local spot = Color3.fromRGB(200, 255, 245)
    local parts = {
        { Shape = "Prism", Axis = "Y", Size = Vector3.new(1.5, 0.4, 1.5), At = at(0, 0.35, 0), Color = cap, Neon = true, Transparency = 0.1 },
        { Shape = "Prism", Axis = "Y", Size = Vector3.new(1, 0.3, 1), At = at(0, 0.7, 0, 0, 22.5, 0), Color = cap, Neon = true, Transparency = 0.1 },
        { Shape = "Prism", Axis = "Y", Size = Vector3.new(0.6, 0.9, 0.6), At = at(0, -0.3, 0), Color = stem },
        { Shape = "Block", Size = Vector3.new(0.2, 0.08, 0.2), At = at(0, 0.88, 0, 0, 45, 0), Color = spot, Neon = true },
        { Shape = "Block", Size = Vector3.new(0.18, 0.08, 0.18), At = at(0.48, 0.57, 0.25, 0, 45, 0), Color = spot, Neon = true },
        { Shape = "Block", Size = Vector3.new(0.18, 0.08, 0.18), At = at(-0.42, 0.57, -0.32, 0, 45, 0), Color = spot, Neon = true },
    }
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.12, 0.14, 0.06), At = at(0.13 * side, -0.15, -0.31), Color = BLACK }
    end)
    mirrored(parts, function(side)
        return { Shape = "Wedge", Size = Vector3.new(0.1, 0.35, 0.15), At = at(0.36 * side, -0.35, 0, 0, 90 * side, 30 * side), Color = stem }
    end)
    return { Scale = 0.9, Parts = parts }
end

local function jadeSpiritPanda()
    local white = Color3.fromRGB(245, 245, 240)
    local black = Color3.fromRGB(30, 35, 35)
    local jade = Color3.fromRGB(80, 210, 140)
    local parts = {
        { Shape = "Prism", Axis = "Y", Size = Vector3.new(1.2, 1.1, 1.1), At = at(0, 0, 0), Color = white },
        { Shape = "Prism", Axis = "X", Size = Vector3.new(0.95, 0.9, 0.9), At = at(0, 0.8, -0.2), Color = white },
        { Shape = "Prism", Size = Vector3.new(0.35, 0.25, 0.25), At = at(0, 0.68, -0.72), Color = white },
        { Shape = "Block", Size = Vector3.new(0.14, 0.1, 0.06), At = at(0, 0.76, -0.86), Color = black },
        { Shape = "Block", Size = Vector3.new(0.3, 0.3, 0.08), At = at(0, 0.05, -0.57, 0, 0, 45), Color = jade, Neon = true },
    }
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.32, 0.32, 0.25), At = at(0.36 * side, 1.25, -0.15, 0, 0, 20 * side), Color = black }
    end)
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.24, 0.3, 0.08), At = at(0.2 * side, 0.85, -0.66, 0, 0, -20 * side), Color = black }
    end)
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.09, 0.09, 0.06), At = at(0.2 * side, 0.87, -0.71), Color = jade, Neon = true }
    end)
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.32, 0.6, 0.32), At = at(0.58 * side, 0, -0.25, 20, 0, 15 * side), Color = black }
    end)
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.4, 0.32, 0.5), At = at(0.35 * side, -0.58, -0.15), Color = black }
    end)
    return { Scale = 1, Parts = parts }
end

local function jadeAntlerDeer()
    local fur = Color3.fromRGB(165, 120, 75)
    local light = Color3.fromRGB(240, 225, 200)
    local jade = Color3.fromRGB(120, 230, 140)
    local parts = {
        { Shape = "Prism", Size = Vector3.new(0.75, 0.75, 1.4), At = at(0, 0, 0), Color = fur },
        { Shape = "Block", Size = Vector3.new(0.35, 0.7, 0.35), At = at(0, 0.5, -0.55, -25), Color = fur },
        { Shape = "Prism", Size = Vector3.new(0.5, 0.45, 0.65), At = at(0, 0.95, -0.85), Color = fur },
        { Shape = "Wedge", Size = Vector3.new(0.28, 0.22, 0.3), At = at(0, 0.86, -1.3), Color = light },
        { Shape = "Wedge", Size = Vector3.new(0.22, 0.3, 0.2), At = at(0, 0.3, 0.75, 30, 180, 0), Color = light },
        { Shape = "Block", Size = Vector3.new(0.13, 0.05, 0.13), At = at(0.18, 0.38, 0.1, 0, 45, 0), Color = light },
        { Shape = "Block", Size = Vector3.new(0.13, 0.05, 0.13), At = at(-0.16, 0.38, -0.2, 0, 45, 0), Color = light },
        { Shape = "Block", Size = Vector3.new(0.11, 0.05, 0.11), At = at(-0.08, 0.38, 0.4, 0, 45, 0), Color = light },
    }
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.08, 0.75, 0.08), At = at(0.15 * side, 1.5, -0.8, 0, 0, -18 * side), Color = jade, Neon = true }
    end)
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.07, 0.4, 0.07), At = at(0.32 * side, 1.55, -0.8, 0, 0, -60 * side), Color = jade, Neon = true }
    end)
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.07, 0.35, 0.07), At = at(0.3 * side, 1.82, -0.8, 0, 0, -10 * side), Color = jade, Neon = true }
    end)
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.1, 0.1, 0.06), At = at(0.18 * side, 1, -1.18), Color = BLACK }
    end)
    for _, z in { -0.45, 0.45 } do
        mirrored(parts, function(side)
            return { Shape = "Block", Size = Vector3.new(0.13, 0.65, 0.13), At = at(0.22 * side, -0.6, z), Color = fur }
        end)
    end
    return { Scale = 1.05, Parts = parts }
end

local function magmaCub()
    local rock = Color3.fromRGB(55, 45, 45)
    local lava = Color3.fromRGB(255, 110, 30)
    local parts = {
        { Shape = "Prism", Size = Vector3.new(1.1, 0.95, 1.2), At = at(0, 0, 0.1), Color = rock },
        { Shape = "Prism", Axis = "X", Size = Vector3.new(0.9, 0.85, 0.85), At = at(0, 0.6, -0.5), Color = rock },
        { Shape = "Prism", Size = Vector3.new(0.42, 0.3, 0.3), At = at(0, 0.48, -1), Color = rock },
        { Shape = "Block", Size = Vector3.new(0.14, 0.1, 0.06), At = at(0, 0.56, -1.16), Color = lava, Neon = true },
        { Shape = "Block", Size = Vector3.new(0.7, 0.07, 0.08), At = at(0, 0.48, 0.1, 0, 0, 15), Color = lava, Neon = true },
        { Shape = "Block", Size = Vector3.new(0.5, 0.07, 0.08), At = at(0.05, 0.47, 0.45, 0, 0, -20), Color = lava, Neon = true },
        { Shape = "Block", Size = Vector3.new(0.08, 0.07, 0.5), At = at(-0.15, 0.48, 0.25), Color = lava, Neon = true },
    }
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.28, 0.28, 0.18), At = at(0.32 * side, 1.02, -0.45, 0, 0, 45), Color = rock }
    end)
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.15, 0.12, 0.06), At = at(0.2 * side, 0.7, -0.94), Color = lava, Neon = true }
    end)
    for _, z in { -0.25, 0.45 } do
        mirrored(parts, function(side)
            return { Shape = "Block", Size = Vector3.new(0.3, 0.4, 0.3), At = at(0.32 * side, -0.48, z), Color = rock }
        end)
    end
    return { Scale = 0.95, Parts = parts }
end

local function sunscaleDragon()
    local gold = Color3.fromRGB(255, 200, 60)
    local amber = Color3.fromRGB(230, 120, 30)
    local sun = Color3.fromRGB(255, 240, 150)
    local parts = {
        { Shape = "Prism", Size = Vector3.new(0.85, 0.75, 0.95), At = at(0, 0.45, -0.7), Color = gold },
        { Shape = "Wedge", Size = Vector3.new(0.5, 0.35, 0.5), At = at(0, 0.35, -1.35), Color = gold },
        { Shape = "Prism", Size = Vector3.new(0.85, 0.85, 0.8), At = at(0, 0, 0), Color = gold },
        { Shape = "Prism", Size = Vector3.new(0.7, 0.7, 0.6), At = at(0, -0.05, 0.62, -10), Color = amber },
        { Shape = "Prism", Size = Vector3.new(0.5, 0.5, 0.5), At = at(0, 0.15, 1.12, -25), Color = amber },
        { Shape = "Prism", Size = Vector3.new(1.35, 1.35, 0.08), At = at(0, 0.75, -0.15), Color = sun, Neon = true, Transparency = 0.35 },
    }
    mirrored(parts, function(side)
        return { Shape = "Wedge", Size = Vector3.new(0.15, 0.5, 0.35), At = at(0.25 * side, 1, -0.55, -20, 180, 0), Color = amber }
    end)
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.16, 0.14, 0.08), At = at(0.3 * side, 0.6, -1.15), Color = sun, Neon = true }
    end)
    mirrored(parts, function(side)
        return wing(side, 0.35, 0.35, 0.1, 1, 0.9, 30, amber)
    end)
    return { Scale = 1, Parts = parts }
end

local function dawnPhoenix()
    local flame = Color3.fromRGB(255, 120, 55)
    local gold = Color3.fromRGB(255, 205, 90)
    local crimson = Color3.fromRGB(215, 35, 85)
    local parts = {
        { Shape = "Prism", Size = Vector3.new(0.8, 0.8, 1.2), At = at(0, 0, 0, -10), Color = flame },
        { Shape = "Prism", Axis = "Y", Size = Vector3.new(0.6, 0.6, 0.6), At = at(0, 0.6, -0.55), Color = flame },
        { Shape = "Wedge", Size = Vector3.new(0.2, 0.2, 0.35), At = at(0, 0.55, -1.02), Color = gold },
        { Shape = "Wedge", Size = Vector3.new(0.1, 0.5, 0.3), At = at(0, 1.05, -0.5, -10, 180, 0), Color = gold, Neon = true },
        { Shape = "Wedge", Size = Vector3.new(0.1, 0.4, 0.3), At = at(0, 0.98, -0.3, -35, 180, 0), Color = gold, Neon = true },
    }
    mirrored(parts, function(side)
        return { Shape = "Block", Size = Vector3.new(0.12, 0.12, 0.06), At = at(0.2 * side, 0.68, -0.86), Color = BLACK }
    end)
    mirrored(parts, function(side)
        return wing(side, 0.3, 0.3, 0.05, 1.3, 1, 40, flame)
    end)
    mirrored(parts, function(side)
        return wing(side, 0.3, 0.45, 0.05, 0.8, 0.6, 40, gold, true)
    end)
    for index, angle in { -15, 0, 15 } do
        local length = if index == 2 then 1.4 else 1.1
        table.insert(parts, {
            Shape = "Wedge",
            Size = Vector3.new(0.18, 0.12, length),
            At = at(0, -0.05, 0.6, 15, angle, 0) * CFrame.new(0, 0, length / 2),
            Color = crimson,
            Neon = true,
        })
    end
    return { Scale = 1.15, Parts = parts }
end

PetModels.Pets = {
    AquaWisp = { Scale = 0.95, Parts = {} }, -- recreated (2026-11-09): only its imported model; its old droplet design removed (MESH_LOOKS was tuned with this scale)
    EmberWyrm = { Scale = 1.05, Parts = {} }, -- recreated (2026-11-09): only its imported model; its old lava-bead design removed (MESH_LOOKS was tuned with this scale)
    LunarHopper = lunarHopper(),
    VoltFox = voltFox(),
    GoldenKirin = { Scale = 1.15, Parts = {} }, -- recreated (2026-11-09): only its imported model; its old design removed (MESH_LOOKS was tuned with this scale)
    NineTailMoonfox = nineTailMoonfox(),
    OriginSerpent = originSerpent(),
    AstralWhale = astralWhale(),
    MossGolem = mossGolem(),
    MyceliumSprite = myceliumSprite(),
    JadeSpiritPanda = jadeSpiritPanda(),
    JadeAntlerDeer = jadeAntlerDeer(),
    MagmaCub = magmaCub(),
    SunscaleDragon = sunscaleDragon(),
    DawnPhoenix = dawnPhoenix(),
}

do
    local PetArchetypes = require(script.Parent:WaitForChild("PetArchetypes"))
    for petId, spec in PetArchetypes.Specs do
        if not PetModels.Pets[petId] then
            local pet = GameConfig.Pets[petId]
            PetModels.Pets[petId] = PetArchetypes.build(spec, pet and pet.Rarity)
        end
    end
end

local PART_SHAPES = {
    Block = Enum.PartType.Block,
    Wedge = Enum.PartType.Wedge,
}

local PRISM_TURNS = {
    X = CFrame.identity,
    Y = CFrame.Angles(0, 0, math.rad(90)),
    Z = CFrame.Angles(0, math.rad(90), 0),
}

local function prismPieces(size, axis)
    local length, height, depth
    if axis == "X" then
        length, height, depth = size.X, size.Y, size.Z
    elseif axis == "Y" then
        length, height, depth = size.Y, size.X, size.Z
    else
        length, height, depth = size.Z, size.Y, size.X
    end

    local turn = PRISM_TURNS[axis]
    local corner = math.min(height, depth) * 0.293
    local pieces = {
        { Shape = "Block", Size = Vector3.new(length, height - 2 * corner, depth), Offset = turn, Tone = 0 },
        { Shape = "Block", Size = Vector3.new(length, height, depth - 2 * corner), Offset = turn, Tone = 0 },
    }
    for index, signs in { { 1, 1 }, { -1, 1 }, { -1, -1 }, { 1, -1 } } do
        table.insert(pieces, {
            Shape = "Wedge",
            Tone = signs[1],
            Size = Vector3.new(length, corner, corner),
            Offset = turn
                * CFrame.new(0, signs[1] * (height / 2 - corner / 2), signs[2] * (depth / 2 - corner / 2))
                * CFrame.Angles(math.rad(90 * (index - 1)), 0, 0)
                * CFrame.Angles(0, math.pi, 0),
        })
    end
    return pieces
end

local function toneColor(color, tone)
    if tone > 0 then
        return color:Lerp(Color3.new(1, 1, 1), 0.22)
    elseif tone < 0 then
        return color:Lerp(Color3.new(0, 0, 0), 0.22)
    end
    return color
end

local function createPart(model, rootPart, shape, size, cframe, spec, tone)
    local part = Instance.new("Part")
    part.Shape = PART_SHAPES[shape]
    part.Size = size
    part.CFrame = cframe
    part.Color = if spec.Neon then spec.Color else toneColor(spec.Color, tone or 0)
    part.Material = if spec.Neon then Enum.Material.Neon elseif spec.Glass then Enum.Material.Glass else Enum.Material.SmoothPlastic
    part.Transparency = spec.Transparency or 0
    part.TopSurface = Enum.SurfaceType.Smooth
    part.BottomSurface = Enum.SurfaceType.Smooth
    part.CanCollide = false
    part.CanTouch = false
    part.CanQuery = false
    part.CastShadow = false
    part.Massless = true
    part.Anchored = false

    local weld = Instance.new("WeldConstraint")
    weld.Part0 = rootPart
    weld.Part1 = part
    weld.Parent = part

    part.Parent = model
end

local MESH_LOOKS = {
    MyceliumSprite = { Glow = Color3.fromRGB(90, 245, 215), Length = 2.6 },
    MossGolem = { Glow = Color3.fromRGB(110, 255, 140), Length = 3.4 },
    JadeSpiritPanda = { Glow = Color3.fromRGB(60, 225, 130), Length = 3.3 },
    JadeAntlerDeer = { Glow = Color3.fromRGB(60, 225, 140), Length = 4.2 },
    MagmaCub = { Glow = Color3.fromRGB(255, 120, 30), Length = 2.6 },
    AzureSkyDragon = { Glow = Color3.fromRGB(70, 170, 255), Length = 4.4 },
    SpiritCrane = { Glow = Color3.fromRGB(40, 210, 200), Length = 4.2 },
    CloudSheep = { Glow = Color3.fromRGB(120, 215, 245), Length = 3.0 },
    WindSprite = { Glow = Color3.fromRGB(30, 235, 180), Length = 3.5 },
    GalaxyManta = { Glow = Color3.fromRGB(140, 100, 255), Length = 4.0 },
    AbyssAnomalocaris = { Glow = Color3.fromRGB(190, 36, 146), Length = 3.8 },
    VoidscaleHydra = { Glow = Color3.fromRGB(70, 150, 255), Length = 4.0 },
    TheNamelessOne = { Glow = Color3.fromRGB(200, 170, 255), Length = 3.6 },
    EclipseCat = { Glow = Color3.fromRGB(176, 124, 255), Length = 3.0 },
    Shadowcoil = { Glow = Color3.fromRGB(168, 255, 224), Length = 3.0 },
    CelestialPearlDragon = { Glow = Color3.fromRGB(224, 210, 255), Length = 4.6 },
    CelestialSnowLeopard = { Glow = Color3.fromRGB(196, 232, 255), Length = 4.2 },
    CometStag = { Glow = Color3.fromRGB(150, 210, 255), Length = 4.6 },
    SandPhantom = { Glow = Color3.fromRGB(240, 196, 120), Length = 4.0 }, -- its long tail is most of its length
    SolarButterfly = { Glow = Color3.fromRGB(255, 170, 70), Length = 3.8 }, -- its wingspan
    ObsidianGuardian = { Glow = Color3.fromRGB(176, 110, 255), Length = 3.8 }, -- its folded wings' peaks: its tallest part
    GlacierPuff = { Glow = Color3.fromRGB(170, 225, 255), Length = 2.6 }, -- its box runs from the origin below it (it floats) to its top: about 4 studs nose to tail
    GravityImp = { Glow = Color3.fromRGB(210, 140, 255), Length = 2.6 }, -- its box runs from the origin, just under its moonlet, to its cowlick (it is "a small creature": at 3.2 it stood taller than its owner)
    CrystalBeetle = { Glow = Color3.fromRGB(160, 245, 255), Length = 3.2 }, -- nose to tail (its longest): long and low, so at 2.6 it was knee-high and lost in tall grass
    ThunderclawDrake = { Glow = Color3.fromRGB(255, 235, 100), Length = 5.8 }, -- its box's longest side is its raised wingspan; nose to tail it is three quarters of that (at 5.2 its head came only to its owner's, lost in tall grass)
    FrostfangSerpent = { Glow = Color3.fromRGB(130, 210, 255), Length = 3.4 }, -- its box's longest side is its height, reared: about the Pearl Dragon's
    StormBumblebee = { Glow = Color3.fromRGB(255, 220, 80), Length = 3.2 }, -- feeler tips to tail (its longest), hovering: about the Crystal Beetle's
    TimekeeperTortoise = { Glow = Color3.fromRGB(255, 214, 130), Length = 4.4 }, -- head to tail
    StormhornKirin = { Glow = Color3.fromRGB(90, 170, 255), Length = 4.4 },
    JadeWyrmTurtle = { Glow = Color3.fromRGB(60, 220, 170), Length = 4.8 },
    NebulaOwl = { Glow = Color3.fromRGB(176, 122, 255), Length = 4.0 },
    CosmicJellyfish = { Glow = Color3.fromRGB(245, 120, 180), Length = 3.3 },
    StarfallFox = { Glow = Color3.fromRGB(150, 160, 255), Length = 3.6 },
    LanternWarden = { Glow = Color3.fromRGB(255, 176, 70), Length = 3.2 },
    DreamMoth = { Glow = Color3.fromRGB(230, 170, 255), Length = 3.2 },
    PrismArmadillo = { Glow = Color3.fromRGB(190, 150, 255), Length = 4.0 },
    CrystalSnail = { Glow = Color3.fromRGB(110, 230, 200), Length = 3.2 },
    GoldenManeLion = { Glow = Color3.fromRGB(255, 180, 60), Length = 4.4 },
    DawnPhoenix = { Glow = Color3.fromRGB(255, 170, 70), Length = 4.6 },
    AquaWisp = { Glow = Color3.fromRGB(60, 196, 232), Length = 1.8 }, -- crown to tail (its longest, upright): about 3.4 studs, a small starter beside its owner
    EmberWyrm = { Glow = Color3.fromRGB(255, 122, 30), Length = 2.4 }, -- nose to campfire (its longest): about 5 studs long and 1.5 tall, a small salamander at its owner's feet
    LunarHopper = { Effect = "Stars", Glow = Color3.fromRGB(150, 160, 255), Length = 2.58 },
    VoltFox = { Effect = "Sparks", Glow = Color3.fromRGB(255, 235, 110), Length = 2.91 },
    GoldenKirin = { Glow = Color3.fromRGB(255, 214, 120), Length = 2.4 }, -- nose to tail-silk (its longest), 5.5 studs; its halo's top about 4.8 studs up, under its owner's head (k is about 2.3 for it: 4.4 stood it 9 studs tall)
    AstralWhale = { Effect = "Stars", Glow = Color3.fromRGB(130, 125, 255), Length = 4.0 },
    OriginSerpent = { Effect = "Stars", Glow = Color3.fromRGB(80, 190, 255), Length = 2.9 },
    SunscaleDragon = { Glow = Color3.fromRGB(255, 194, 74), Length = 4.6 },
    BonefireDragon = { Glow = Color3.fromRGB(100, 170, 255), Length = 3.4 },
    PrismaticPhoenix = { Effect = "Glitter", Glow = Color3.fromRGB(255, 175, 130), Length = 4.2 },
    RuneSphinx = { Glow = Color3.fromRGB(255, 190, 90), Length = 4.0 },
    WorldrootColossus = { Effect = "Glitter", Glow = Color3.fromRGB(90, 235, 120), Length = 3.6 },
    ThousandYearDreamEater = { Effect = "Stars", Glow = Color3.fromRGB(170, 120, 255), Length = 3.7 },
    EternalClockworkDragon = { Effect = "Sparks", Glow = Color3.fromRGB(255, 200, 90), Length = 4.3 },
    HeavenbreakerApe = { Effect = "Sparks", Glow = Color3.fromRGB(255, 215, 110), Length = 3.4 },
    DreadfangCerberus = { Glow = Color3.fromRGB(40, 200, 255), Length = 3.4 },
}

local TEXTURES = {
    Glow = "rbxasset://textures/particles/explosion01_implosion_main.dds",
    Sparkle = "rbxasset://textures/particles/sparkles_main.dds",
    Fire = "rbxasset://textures/particles/fire_main.dds",
    Sparks = "rbxasset://textures/particles/fire_sparks_main.dds",
}

local function emitter(parent, properties)
    local particles = Instance.new("ParticleEmitter")
    particles.LightInfluence = 0
    for property, value in properties do
        particles[property] = value
    end
    particles.Parent = parent
    return particles
end

local function sizeCurve(peak, k)
    return NumberSequence.new({
        NumberSequenceKeypoint.new(0, 0),
        NumberSequenceKeypoint.new(0.3, peak * k),
        NumberSequenceKeypoint.new(1, 0),
    })
end

local MESH_EFFECTS = {
    Bubbles = function(body, tail, glow, k)
        emitter(body, {
            Texture = TEXTURES.Glow, Color = ColorSequence.new(glow), LightEmission = 0.4, Brightness = 2,
            Size = sizeCurve(0.22, k), Transparency = NumberSequence.new(0.2), Rate = 5,
            Lifetime = NumberRange.new(1.2, 1.8), Speed = NumberRange.new(0.3, 0.8), SpreadAngle = Vector2.new(180, 180),
            Acceleration = Vector3.new(0, 1, 0),
        })
    end,
    TailFlame = function(body, tail, glow, k)
        emitter(tail, {
            Texture = TEXTURES.Fire, Brightness = 5, LightEmission = 0.4,
            Color = ColorSequence.new({
                ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 220, 120)),
                ColorSequenceKeypoint.new(0.5, Color3.fromRGB(255, 120, 40)),
                ColorSequenceKeypoint.new(1, Color3.fromRGB(200, 40, 20)),
            }),
            Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.7 * k), NumberSequenceKeypoint.new(1, 0.15 * k) }),
            Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.15), NumberSequenceKeypoint.new(1, 1) }),
            Rate = 18, Lifetime = NumberRange.new(0.35, 0.55), Speed = NumberRange.new(1, 2),
            SpreadAngle = Vector2.new(15, 15), Acceleration = Vector3.new(0, 6, 0),
            Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-90, 90),
        })
        emitter(body, {
            Texture = TEXTURES.Glow, Color = ColorSequence.new(glow), LightEmission = 0.5, Brightness = 2,
            Size = sizeCurve(0.12, k), Rate = 6, Lifetime = NumberRange.new(0.8, 1.3),
            Speed = NumberRange.new(0.5, 1.2), SpreadAngle = Vector2.new(40, 40), Acceleration = Vector3.new(0, 2.5, 0),
        })
    end,
    Stars = function(body, tail, glow, k)
        emitter(body, {
            Texture = TEXTURES.Sparkle, Color = ColorSequence.new(glow), LightEmission = 0.6, Brightness = 2,
            Size = sizeCurve(0.35, k), Rate = 6, Lifetime = NumberRange.new(0.5, 0.9),
            Speed = NumberRange.new(0.1, 0.4), SpreadAngle = Vector2.new(180, 180), Rotation = NumberRange.new(0, 90),
        })
    end,
    Sparks = function(body, tail, glow, k)
        for _, source in { body, tail } do
            emitter(source, {
                Texture = TEXTURES.Sparks, Color = ColorSequence.new(glow), LightEmission = 0.6, Brightness = 2.5,
                Orientation = Enum.ParticleOrientation.VelocityParallel,
                Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.3 * k), NumberSequenceKeypoint.new(1, 0.05 * k) }),
                Rate = 6, Lifetime = NumberRange.new(0.12, 0.25), Speed = NumberRange.new(4, 7),
                SpreadAngle = Vector2.new(180, 180), Drag = 6,
            })
        end
    end,
    Glitter = function(body, tail, glow, k)
        emitter(body, {
            Texture = TEXTURES.Sparkle, Color = ColorSequence.new(Color3.fromRGB(255, 225, 120), glow), LightEmission = 0.6,
            Brightness = 2, Size = sizeCurve(0.25, k), Rate = 7, Lifetime = NumberRange.new(0.6, 1),
            Speed = NumberRange.new(0.2, 0.5), SpreadAngle = Vector2.new(180, 180), Acceleration = Vector3.new(0, 0.6, 0),
        })
    end,
}

local function weldTo(rootPart, part)
    part.Anchored = false
    part.CanCollide = false
    part.CanTouch = false
    part.CanQuery = false
    part.CastShadow = false
    part.Massless = true
    local weld = Instance.new("WeldConstraint")
    weld.Part0 = rootPart
    weld.Part1 = part
    weld.Parent = part
end

local dressUp

local function addImported(model, rootPart, template, design, petId)
    local look = MESH_LOOKS[petId] or {}
    local turn = template:GetAttribute("Turn") or CFrame.identity
    local boxCFrame, boxSize = template:GetBoundingBox()
    local longest = math.max(boxSize.X, boxSize.Y, boxSize.Z)
    local k = design.Scale * PetModels.SIZE
    local scale = (look.Length or longest) * k / longest

    if PetRig.isRigged(petId, template) then
        if PetRig.Profiles[petId].Skinned then
            keep(model, PetRig.buildSkinned(model, rootPart, template, petId, turn, scale, (look.Length or longest) * k))
            return
        end
        local function place(piece)
            local offset = CFrame.new(-boxCFrame.Position) * piece.CFrame
            return turn * (offset.Rotation + offset.Position * scale), piece.Size * scale
        end
        keep(model, PetRig.build(model, rootPart, template, petId, place, scale))
        return
    end

    local body
    for _, piece in template:GetDescendants() do
        if not piece:IsA("BasePart") then
            continue
        end
        local part = piece:Clone()
        local hex = string.match(piece.Name, "_Glow_(%x%x%x%x%x%x)$")
        for _, child in part:GetChildren() do
            if hex or not child:IsA("SurfaceAppearance") then
                child:Destroy()
            end
        end
        local offset = CFrame.new(-boxCFrame.Position) * piece.CFrame
        part.Size = piece.Size * scale
        part.CFrame = turn * (offset.Rotation + offset.Position * scale)
        if hex then
            part.Color = Color3.fromHex(hex)
            part.Material = Enum.Material.Neon
            if part:IsA("MeshPart") then
                part.TextureID = ""
            end
        else
            part.Material = Enum.Material.SmoothPlastic
            body = body or part
        end
        weldTo(rootPart, part)
        part.Parent = model
    end
    if body then
        dressUp(model, rootPart, body, boxSize * scale, look, k, turn)
    end
end

dressUp = function(model, rootPart, body, size, look, k, turn)
    local glow = look.Glow or Color3.new(1, 1, 1)
    local shell = body:Clone()
    shell.Name = "EnergyShell"
    shell:ClearAllChildren()
    shell.Material = Enum.Material.ForceField
    shell.Color = glow
    if shell:IsA("MeshPart") then
        shell.TextureID = ""
    end
    shell.Size = body.Size * 1.06
    weldTo(rootPart, shell)
    shell.Parent = model

    local light = Instance.new("PointLight")
    light.Color = glow
    light.Brightness = 1.2
    light.Range = 3 * k
    light.Parent = body

    local effect = MESH_EFFECTS[look.Effect]
    if effect then
        local tail = Instance.new("Attachment")
        tail.Name = "TailTip"
        tail.Position = (turn or CFrame.identity) * Vector3.new(0, size.Y * 0.25, size.Z * 0.45)
        tail.Parent = rootPart
        effect(body, tail, glow, k)
    end
end

function PetModels.build(petId)
    local design = PetModels.Pets[petId]
    if not design then
        return nil
    end

    local model = Instance.new("Model")
    model.Name = petId

    local rootPart = Instance.new("Part")
    rootPart.Name = "Root"
    rootPart.Size = Vector3.new(0.2, 0.2, 0.2)
    rootPart.Transparency = 1
    rootPart.Anchored = true
    rootPart.CanCollide = false
    rootPart.CanTouch = false
    rootPart.CanQuery = false
    rootPart.CFrame = CFrame.identity
    rootPart.Parent = model
    model.PrimaryPart = rootPart

    local imported = meshFolder and meshFolder:FindFirstChild(petId, true)
    if imported and imported:IsA("Model") then
        addImported(model, rootPart, imported, design, petId)
        return model, rootPart
    end

    local scale = design.Scale * PetModels.SIZE
    for _, spec in design.Parts do
        local offset = spec.At - spec.At.Position + spec.At.Position * scale
        local size = spec.Size * scale

        if spec.Shape == "Prism" then
            for _, piece in prismPieces(size, spec.Axis or "Z") do
                createPart(model, rootPart, piece.Shape, piece.Size, offset * piece.Offset, spec, piece.Tone)
            end
        else
            createPart(model, rootPart, spec.Shape, size, offset, spec)
        end
    end

    return model, rootPart
end

for petId in GameConfig.Pets do
    assert(PetModels.Pets[petId], "PetModels has no model for pet " .. petId)
end

for petId, design in PetModels.Pets do
    for _, spec in design.Parts do
        assert(spec.Shape == "Prism" or PART_SHAPES[spec.Shape], "PetModels: " .. petId .. " uses an unknown Shape: " .. tostring(spec.Shape))
        assert(spec.Shape ~= "Prism" or PRISM_TURNS[spec.Axis or "Z"], "PetModels: " .. petId .. " has a prism with an unknown Axis")
    end
end

return PetModels
