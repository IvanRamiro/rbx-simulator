-- What makes a big pet feel heavy, shared by the pets beside their owners (PetCompanionController) and the pens (PenController):
-- a soft shadow on the ground under a Large, Giant or Colossal one, dust and a low thud at a Giant or Colossal walker's footfalls
-- and landings (a Colossal's deeper and wider: its dust scales with its footprint, its thud is pitched down), and a
-- fade when the camera comes inside a pet (a Giant beside its owner is wider than the camera's distance, so turning the camera
-- would put it inside the beast). No camera shake, for anyone. Cheap: one shadow part per big pet, two emitters per Giant walker,
-- and nothing for Small and Normal pets.
--
--   PetHeft.measure(model)            its footprint as built, in its root's frame: { half = Vector3 (half the box), offset = Vector3
--                                     (the box's middle from the root), parts = { BasePart } }
--   PetHeft.shadow(model, half)       a shadow under it (its PetSize Large or bigger), parented to the model; nil otherwise
--   PetHeft.placeShadow(shadow, ground, lift, heading)  where it lies (a CFrame for BulkMoveTo) on the ground at `ground` (a
--                                     Vector3), turned by `heading` (a rotation), fainter the higher (`lift`, studs) its feet are off the
--                                     ground; a nil ground hides it (and returns nil)
--   PetHeft.dust(model, rootPart, half)  the footfall dust of a Giant or Colossal walker (an Attachment with its emitters), or nil
--   PetHeft.step(dust, ground, heavy) one footfall at `ground`: a ring of dust and a thud; heavy (a landing): a wider ring, more dust
--   PetHeft.fade(pet, eye, dt)        fades a pet (a record with model, cframe, foot = measure's result) while the camera at `eye` is
--                                     inside it, and back when it leaves
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local PetRules = require(ReplicatedStorage:WaitForChild("PetRules"))

local Quality = require(script.Parent.Parent:WaitForChild("Performance"):WaitForChild("Quality"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local PetHeft = {}

local TEXTURES = { Glow = "rbxassetid://135169457468310", Ring = "rbxassetid://81927825399672" } -- (HatchCeremony's)
local SHADOW_TONE = 0.45 -- the shadow's transparency right under its feet
local SHADOW_FADE = 40   -- studs off the ground at which it has faded out
local FADED = 0.82       -- a pet's transparency while the camera is inside it
local FADE_MARGIN = 1.5  -- studs round its box that count as inside
local DUST = Color3.fromRGB(214, 202, 182)

local function reduced()
    return Players.LocalPlayer:GetAttribute("SettingReducedEffects") == true
end

function PetHeft.measure(model)
    local root = model.PrimaryPart
    local box, size = model:GetBoundingBox()
    local parts = {}
    for _, part in model:GetDescendants() do
        if part:IsA("BasePart") and part ~= root then
            table.insert(parts, part)
        end
    end
    return {
        half = size / 2,
        offset = if root then root.CFrame:PointToObjectSpace(box.Position) else Vector3.zero,
        parts = parts,
        fade = 0,
    }
end

function PetHeft.shadow(model, half)
    if PetRules.sizeInfo(model:GetAttribute("PetSize")).Order < PetRules.Sizes.Large.Order then
        return nil
    end
    local part = Instance.new("Part")
    part.Name = "HeftShadow"
    part.Anchored = true
    part.CanCollide = false
    part.CanQuery = false
    part.CanTouch = false
    part.CastShadow = false
    part.Transparency = 1
    -- a soft oval a little wider than its footprint (it reads as the body's shade, not a mat)
    part.Size = Vector3.new(math.max(half.X, 1) * 2.1, 0.05, math.max(half.Z, 1) * 1.9)
    local decal = Instance.new("Decal")
    decal.Face = Enum.NormalId.Top
    decal.Texture = TEXTURES.Glow
    decal.Color3 = Color3.new(0, 0, 0)
    decal.Transparency = SHADOW_TONE
    decal.Parent = part
    part.Parent = model
    return part
end

function PetHeft.placeShadow(shadow, ground, lift, heading)
    local decal = shadow:FindFirstChildOfClass("Decal")
    if not ground then
        if decal then
            decal.Transparency = 1
        end
        return
    end
    if decal then
        local fade = math.clamp(math.max(lift, 0) / SHADOW_FADE, 0, 1)
        local tone = SHADOW_TONE + (1 - SHADOW_TONE) * fade
        if math.abs(decal.Transparency - tone) > 0.02 then
            decal.Transparency = tone
        end
    end
    return CFrame.new(ground + Vector3.new(0, 0.06, 0)) * heading
end

function PetHeft.dust(model, rootPart, half)
    if PetRules.sizeInfo(model:GetAttribute("PetSize")).Order < PetRules.Sizes.Giant.Order or not rootPart then
        return nil
    end
    local reach = math.max(half.X, half.Z)
    local holder = Instance.new("Attachment")
    holder.Name = "HeftDust"
    holder:SetAttribute("Pitch", if model:GetAttribute("PetSize") == "Colossal" then 0.8 else 1) -- (a Colossal's thud, deeper)
    holder.Parent = rootPart
    local ring = Instance.new("ParticleEmitter")
    ring.Name = "Ring"
    ring.Texture = TEXTURES.Ring
    ring.Rate = 0
    ring.LightEmission = 0
    ring.LightInfluence = 1
    ring.Color = ColorSequence.new(DUST)
    ring.EmissionDirection = Enum.NormalId.Top
    ring.Orientation = Enum.ParticleOrientation.VelocityPerpendicular
    ring.Speed = NumberRange.new(0.01)
    ring.Lifetime = NumberRange.new(0.7, 0.9)
    ring.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, reach * 0.25), NumberSequenceKeypoint.new(1, reach * 0.9) })
    ring.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.55), NumberSequenceKeypoint.new(0.5, 0.75),
        NumberSequenceKeypoint.new(1, 1) })
    ring.Parent = holder
    local puff = Instance.new("ParticleEmitter")
    puff.Name = "Puff"
    puff.Texture = TEXTURES.Glow
    puff.Rate = 0
    puff.LightEmission = 0
    puff.LightInfluence = 1
    puff.Color = ColorSequence.new(DUST)
    puff.SpreadAngle = Vector2.new(80, 80)
    puff.EmissionDirection = Enum.NormalId.Top
    puff.Speed = NumberRange.new(reach * 0.15, reach * 0.35)
    puff.Drag = 3
    puff.Acceleration = Vector3.new(0, 0.6, 0)
    puff.Lifetime = NumberRange.new(0.9, 1.4)
    puff.Rotation = NumberRange.new(0, 360)
    puff.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, reach * 0.12), NumberSequenceKeypoint.new(1, reach * 0.35) })
    puff.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.6), NumberSequenceKeypoint.new(1, 1) })
    puff.Parent = holder
    return holder
end

function PetHeft.step(dust, ground, heavy)
    if not (dust and dust.Parent and ground) then
        return
    end
    dust.WorldCFrame = CFrame.new(ground + Vector3.new(0, 0.15, 0))
    local ring, puff = dust:FindFirstChild("Ring"), dust:FindFirstChild("Puff")
    if ring then
        ring:Emit(1)
    end
    if puff and not reduced() then
        puff:Emit(if heavy then 8 elseif Quality.Low then 2 else 4)
    end
    Sfx.play(if heavy then "GiantLand" else "GiantStep", ground, dust:GetAttribute("Pitch"))
end

function PetHeft.fade(pet, eye, dt)
    local foot = pet.foot
    if not (foot and eye) then
        return
    end
    local here = (pet.cframe * CFrame.new(foot.offset)):PointToObjectSpace(eye)
    local half = foot.half
    local inside = math.abs(here.X) < half.X + FADE_MARGIN and math.abs(here.Y) < half.Y + FADE_MARGIN
        and math.abs(here.Z) < half.Z + FADE_MARGIN
    local goal = if inside then FADED else 0
    if foot.fade == goal then
        return
    end
    foot.fade = if math.abs(goal - foot.fade) < 0.03 then goal else foot.fade + (goal - foot.fade) * math.min(1, dt * 8)
    for _, part in foot.parts do
        part.LocalTransparencyModifier = foot.fade
    end
end

return PetHeft
