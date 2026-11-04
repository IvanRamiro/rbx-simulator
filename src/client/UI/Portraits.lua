-- Portraits for the windows' cards: a pet or a weapon as it really is, in a ViewportFrame. Each
-- kind is built once and copied after.
--   Portraits.pet(petId, size)              the pet from the front, a little above and to the side
--   Portraits.weapon(weaponId, tint, size)  the weapon on the diagonal, tip up and to the right;
--                                            tint (a forged element's colour) lights its glow pieces
-- Both return the ViewportFrame (position and parent it), or a plain frame if the model is missing.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local PetMaps = require(ReplicatedStorage:WaitForChild("PetMaps"))
local WeaponMaps = require(ReplicatedStorage:WaitForChild("WeaponMaps"))
local UiKit = require(script.Parent:WaitForChild("UiKit"))
local UiTheme = require(script.Parent:WaitForChild("UiTheme"))
local PetModels = require(script.Parent.Parent:WaitForChild("Pets"):WaitForChild("PetModels"))

local C = UiTheme.Colors
local Portraits = {}

local FIELD_OF_VIEW = 28
local WEAPON_TURN = CFrame.Angles(math.rad(45), 0, 0) -- the blade (along -Z) tilted up 45 degrees

local function view(size)
    local frame = Instance.new("ViewportFrame")
    frame.Name = "Portrait"
    frame.BackgroundColor3 = C.Well
    frame.BackgroundTransparency = 0.35
    frame.BorderSizePixel = 0
    frame.Ambient = Color3.fromRGB(190, 196, 210)
    frame.LightColor = Color3.new(1, 1, 1)
    frame.LightDirection = Vector3.new(-0.4, -1, -0.6)
    frame.Size = UDim2.fromOffset(size, size)
    UiKit.corner(frame, 8)
    UiKit.stroke(frame, C.Edge, 0.6)
    return frame
end

-- A SurfaceAppearance renders black in a ViewportFrame (it has no environment to light it), so a
-- portrait copy shows each such piece by its colour map alone: the same artwork, without the PBR
-- shading. A game script can't read a SurfaceAppearance's maps, so they come from shared/WeaponMaps
-- and shared/PetMaps.
local function flatten(model, colorMap)
    for _, appearance in model:GetDescendants() do
        if appearance:IsA("SurfaceAppearance") then
            local part = appearance.Parent
            appearance:Destroy()
            if colorMap and part:IsA("MeshPart") then
                part.TextureID = colorMap
            end
        end
    end
    return model
end

-- frames `model` in `frame`, seen from `direction` (from the model's centre toward the camera)
local function shoot(frame, model, direction, fill)
    model.Parent = frame
    local box, size = model:GetBoundingBox()
    local camera = Instance.new("Camera")
    camera.FieldOfView = FIELD_OF_VIEW
    local distance = (size.Magnitude / 2) / math.tan(math.rad(FIELD_OF_VIEW / 2)) * (fill or 1.02)
    camera.CFrame = CFrame.lookAt(box.Position + direction.Unit * distance, box.Position)
    camera.Parent = frame
    frame.CurrentCamera = camera
end

local pets = {}
function Portraits.pet(petId, size)
    local frame = view(size)
    if pets[petId] == nil then
        local model = PetModels.build(petId)
        pets[petId] = if model then flatten(model, PetMaps[petId]) else false
    end
    if pets[petId] then
        shoot(frame, pets[petId]:Clone(), Vector3.new(0.45, 0.35, -1), 0.82) -- pets face -Z
    end
    return frame
end

-- a stored weapon (ReplicatedStorage.Weapons/<id>: pieces placed by their Offset) as one model
local weapons = {}
local function weaponTemplate(weaponId)
    if weapons[weaponId] == nil then
        local folder = ReplicatedStorage:FindFirstChild("Weapons")
        local source = folder and folder:FindFirstChild(weaponId)
        local model = false
        if source then
            model = Instance.new("Model")
            for _, piece in source:GetChildren() do
                if piece:IsA("BasePart") then
                    local part = piece:Clone()
                    part.Anchored = true
                    local offset = piece:GetAttribute("Offset")
                    part.CFrame = WEAPON_TURN * (if typeof(offset) == "CFrame" then offset else CFrame.identity)
                    part.Parent = model
                end
            end
        end
        weapons[weaponId] = if model then flatten(model, WeaponMaps[weaponId] and WeaponMaps[weaponId].Color) else false
    end
    return weapons[weaponId]
end

function Portraits.weapon(weaponId, tint, size)
    local frame = view(size)
    local template = weaponTemplate(weaponId)
    if template then
        local model = template:Clone()
        if tint then
            for _, part in model:GetChildren() do
                if part:IsA("BasePart") and part:GetAttribute("Glow") then
                    part.Color = tint
                end
            end
        end
        -- from the side (+X): the blade's length lies across the frame, its flat toward us
        -- (a long blade on the frame's diagonal: framing its whole length, not its bounding sphere)
        shoot(frame, model, Vector3.new(1, 0, 0), 0.74)
    end
    return frame
end

return Portraits
