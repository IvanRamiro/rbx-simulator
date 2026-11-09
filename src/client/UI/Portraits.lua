-- Portraits for the windows' cards: a pet or a weapon as it really is, in a ViewportFrame. Each
-- kind is built once and copied after.
--   Portraits.pet(petId, size)              the pet from the front, a little above and to the side
--   Portraits.silhouette(petId, size)       the same pet as a solid black shape, for a beast not yet discovered
--   Portraits.spin(frame)                   turns a pet portrait slowly round; returns a function that stops it
--   Portraits.weapon(weaponId, tint, size)  the weapon on the diagonal, tip up and to the right;
--                                            tint (a forged element's colour) lights its glow pieces
-- Both return the ViewportFrame (position and parent it), or a plain frame if the model is missing.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

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
    UiKit.corner(frame)
    UiKit.stroke(frame, C.EdgeDim, 0.4)
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

-- pets whose reach would be cut off by the usual tight framing (the Warden's crook stands well above its body; the Moth's wings reach far out to either side)
local FILL_FOR = { LanternWarden = 0.98, DreamMoth = 1.02, TheNamelessOne = 1.0, CelestialSnowLeopard = 0.95, SolarButterfly = 1.0, ObsidianGuardian = 1.0 } -- the camera farther back: the Nameless One's halo and scarves reach past its head
-- where the camera looks from, for a pet the usual three-quarter view hides: the Hydra's four heads line up behind each other
-- from the side, so it is seen more from the front and above, its necks fanned out
local DIRECTION = Vector3.new(0.45, 0.35, -1)
-- and the Snow Leopard's long, low body hides behind its head from the front: seen more from the side, its length and tail show;
-- so do the Comet Stag's antlers, which sweep straight back and from the front read as upright
local DIRECTION_FOR = { VoidscaleHydra = Vector3.new(0.3, 0.75, -1), CelestialSnowLeopard = Vector3.new(0.85, 0.4, -0.9), CometStag = Vector3.new(1, 0.3, -0.55),
    SolarButterfly = Vector3.new(0.25, 1.4, -0.6) } -- its wings are flat: seen from the usual angle they read as a line, so it is seen from above

-- a pet that floats is framed on what can be seen of it: its importer's holder part sits at the origin, well below it, and pulls the box down
local VISIBLE_BOX_FOR = { GlacierPuff = true }

local function visibleBox(model)
    local lo, hi = Vector3.one * math.huge, -Vector3.one * math.huge
    for _, part in model:GetDescendants() do
        if part:IsA("BasePart") and part.Transparency < 1 then
            local half = part.Size / 2
            for _, corner in { Vector3.new(-1, -1, -1), Vector3.new(1, 1, 1), Vector3.new(-1, 1, 1), Vector3.new(1, -1, -1), Vector3.new(1, -1, 1), Vector3.new(-1, 1, -1), Vector3.new(1, 1, -1), Vector3.new(-1, -1, 1) } do
                local p = part.CFrame:PointToWorldSpace(half * corner)
                lo, hi = lo:Min(p), hi:Max(p)
            end
        end
    end
    return CFrame.new((lo + hi) / 2), hi - lo
end

-- frames `model` in `frame`, seen from `direction` (from the model's centre toward the camera)
local function shoot(frame, model, direction, fill, visibleOnly)
    model.Parent = frame
    local box, size
    if visibleOnly then
        box, size = visibleBox(model)
    else
        box, size = model:GetBoundingBox()
    end
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
        shoot(frame, pets[petId]:Clone(), DIRECTION_FOR[petId] or DIRECTION, FILL_FOR[petId] or 0.82, VISIBLE_BOX_FOR[petId]) -- pets face -Z
    end
    return frame
end

-- Unlit and unpainted: the shape, and nothing a player could read the beast from.
local NO_SHOW = { "Decal", "Texture", "Light", "ParticleEmitter", "Beam", "Trail", "Highlight", "Fire", "Smoke", "Sparkles" }
function Portraits.silhouette(petId, size)
    local frame = view(size)
    frame.Ambient = Color3.new(0, 0, 0)
    frame.LightColor = Color3.new(0, 0, 0)
    frame.BackgroundColor3 = Color3.fromRGB(86, 104, 190) -- a lit page, so the black shape reads against it
    frame.BackgroundTransparency = 0.35
    if pets[petId] == nil then
        local model = PetModels.build(petId)
        pets[petId] = if model then flatten(model, PetMaps[petId]) else false
    end
    if pets[petId] then
        local copy = pets[petId]:Clone()
        for _, piece in copy:GetDescendants() do
            if piece:IsA("BasePart") then
                piece.Color = Color3.new(0, 0, 0)
                piece.Material = Enum.Material.SmoothPlastic
                if piece.Transparency < 1 then
                    piece.Transparency = 0 -- a see-through part is solid in a silhouette
                end
                if piece:IsA("MeshPart") then
                    piece.TextureID = ""
                end
            elseif piece:IsA("SpecialMesh") then
                piece.TextureId = ""
            else
                for _, kind in NO_SHOW do
                    if piece:IsA(kind) then
                        piece:Destroy()
                        break
                    end
                end
            end
        end
        shoot(frame, copy, DIRECTION_FOR[petId] or DIRECTION, FILL_FOR[petId] or 0.82, VISIBLE_BOX_FOR[petId])
    end
    return frame
end

local SPIN_SPEED = 0.5 -- radians a second
function Portraits.spin(frame)
    local camera = frame.CurrentCamera
    local model = frame:FindFirstChildOfClass("Model")
    if not (camera and model) then
        return function() end
    end
    local centre = model:GetBoundingBox().Position
    local from = camera.CFrame.Position - centre
    local connection = RunService.RenderStepped:Connect(function()
        local turned = CFrame.Angles(0, os.clock() * SPIN_SPEED, 0) * from
        camera.CFrame = CFrame.lookAt(centre + turned, centre)
    end)
    return function()
        connection:Disconnect()
    end
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
