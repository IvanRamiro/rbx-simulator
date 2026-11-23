-- Realm 7's (Divine Realm) unique feature, 2026-11-23, second version: LIGHTNING THAT FLICKERS RANDOMLY WITHIN THE BODY (the owner: "try to find an asset for lightning, and the spread
-- are random within the body, and it should not be wide, just an ordinary aura"). It replaces the LightningCorona (a wide corona of bolts), which did not suit the realm. The old
-- RealmUnique.Tier07 model stays in ReplicatedStorage (the breakthrough still reads its textures).
--
-- The sprites are the ones of two free Creator Store lightning auras (their emitters' textures, used as they are; no model, no script is brought in):
--   * "red lightning aura" (asset 12276491211): a 4x4 flipbook of one bolt forking and snapping (texture 9135310747), played once over each particle's short life, squashed so it
--     stretches and shrinks, at a random rotation: a defined red arc;
--   * "Thunder Aura" (asset 9986036815): four thin electric sprites (6959235625, 6967938745, 6964374407, 6967940662), each on screen for a twentieth of a second: the wispy crackle
--     between the arcs.
-- They are laid out the way the base aura's body smoke is: emitters on the body parts (a Box volume emits through the whole part), so the arcs appear at random places over the head,
-- chest, arms and legs, reach about a stud past the skin and are gone, and the aura is never wider than the body. A black copy of the arc (normal blend) goes under the red so the
-- lightning is black and red, not pink. The emitters sit on the body parts, outside the aura's folder, and go with it (RealmAura's cull switches them off; the cleanup removes them).
-- Cost: 4 emitters a body part (11 parts on a phone, with fewer emitters), about 40 emitters for an R15 body. A phone and another player's aura thin the rates.
--
--   local undress = BodyLightning.build(root, fx, { low = Quality.Low, isLocal = true }, record)
-- Tried on the body in Studio (a test-range dummy, Realm 7): the arcs alone read as thin red threads; the wisps alone, at the Thunder Aura's own rate (15 a second on the torso),
-- as a wild tangle three studs wide; the mix below (wisps 2.4 studs at a third of that rate, arcs 1.1 studs) as deep-red lightning crackling over the body and no wider than it.
local BodyLightning = {}

local TEX = {
    Arc = "rbxassetid://9135310747", -- the red lightning aura's flipbook (Grid4x4)
    Thunder = { "rbxassetid://6959235625", "rbxassetid://6967938745" }, -- two of the Thunder Aura's sprites
}
local RED = Color3.fromRGB(235, 14, 34)
local DEEP = Color3.fromRGB(150, 0, 18)
local BLACK = Color3.new(0, 0, 0)

-- the parts that carry lightning (R15 and R6; the hands and feet are left bare, too small)
local PARTS = {
    Head = true, UpperTorso = true, LowerTorso = true,
    LeftUpperArm = true, LeftLowerArm = true, RightUpperArm = true, RightLowerArm = true,
    LeftUpperLeg = true, LeftLowerLeg = true, RightUpperLeg = true, RightLowerLeg = true,
    Torso = true, ["Left Arm"] = true, ["Right Arm"] = true, ["Left Leg"] = true, ["Right Leg"] = true,
}
-- on a phone: the fewest parts that still cover the whole body
local LOW_PARTS = { Head = true, UpperTorso = true, LeftUpperArm = true, RightUpperArm = true, LeftUpperLeg = true, RightUpperLeg = true,
    Torso = true, ["Left Arm"] = true, ["Right Arm"] = true, ["Left Leg"] = true, ["Right Leg"] = true }

local function seq(points)
    local keys = {}
    for _, p in points do
        table.insert(keys, NumberSequenceKeypoint.new(p[1], p[2]))
    end
    return NumberSequence.new(keys)
end

-- the layers, each: name, the rate per cubic stud of the part, the least and the most a part gets (a second), and its properties
local ARC, WISP = 1.1, 2.4 -- the sizes (studs) tried on the body: an arc, a wisp
local function layers()
    local arcSquash = seq({ { 0, -1.18 }, { 0.67, -0.18 }, { 1, -1.11 } })
    local arc = {
        FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4, FlipbookMode = Enum.ParticleFlipbookMode.OneShot,
        FlipbookFramerate = NumberRange.new(6.4), Squash = arcSquash, Rotation = NumberRange.new(-180, 180),
        Orientation = Enum.ParticleOrientation.FacingCamera, LightInfluence = 0, LockedToPart = true,
        Speed = NumberRange.new(0), Transparency = NumberSequence.new(0), Lifetime = NumberRange.new(0.14, 0.18),
        Size = NumberSequence.new(ARC), ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume,
    }
    local function copy(props, extra)
        local c = table.clone(props)
        for k, v in extra do
            c[k] = v
        end
        return c
    end
    local list = {
        -- the black arc, under the red one
        { "LightningBlack", 0.8, 1, 8, copy(arc, { Texture = TEX.Arc, Color = ColorSequence.new(BLACK), LightEmission = 0, Brightness = 1, ZOffset = -0.5,
            Size = NumberSequence.new(ARC * 1.1) }) },
        -- the red arc: a deep red, not pink (a lower LightEmission and Brightness than the asset's, which blooms to pink)
        { "LightningRed", 1.2, 1, 12, copy(arc, { Texture = TEX.Arc, Color = ColorSequence.new(RED, DEEP), LightEmission = 0.5, Brightness = 1.5, ZOffset = 0.5 }) },
        -- the wispy sprites: thin electric lines across the body for a twentieth of a second
        { "LightningWisp1", 1.6, 2.5, 6, {
            Texture = TEX.Thunder[1], Color = ColorSequence.new(RED), LightEmission = 0.4, Brightness = 1.2, LightInfluence = 0, LockedToPart = true,
            Orientation = Enum.ParticleOrientation.VelocityParallel, Rotation = NumberRange.new(-180, 180), Speed = NumberRange.new(0.1),
            Lifetime = NumberRange.new(0.05, 0.09), Size = NumberSequence.new(WISP), Transparency = seq({ { 0, 0 }, { 0.62, 0 }, { 1, 1 } }),
            SpreadAngle = Vector2.new(180, 180), ZOffset = 1,
        } },
        { "LightningWisp2", 1.6, 2.5, 6, {
            Texture = TEX.Thunder[2], Color = ColorSequence.new(RED, DEEP), LightEmission = 0.4, Brightness = 1.2, LightInfluence = 0, LockedToPart = true,
            Orientation = Enum.ParticleOrientation.VelocityParallel, Rotation = NumberRange.new(-180, 180), Speed = NumberRange.new(0.1),
            Lifetime = NumberRange.new(0.05, 0.09), Size = NumberSequence.new(WISP), Transparency = seq({ { 0, 0 }, { 0.62, 0 }, { 1, 1 } }),
            SpreadAngle = Vector2.new(180, 180), ZOffset = 1,
        } },
    }
    return list
end

-- Dresses the body of `root`'s character with the lightning. tuning: { low = Quality.Low, isLocal = the local player's own aura }.
-- `record` is RealmAura's record of the aura being built (its items are switched off when the aura is culled). Returns the undress function.
function BodyLightning.build(root, fx, tuning, record)
    tuning = tuning or {}
    local low = tuning.low == true
    local thin = (if low then 0.45 else 1) * (if tuning.isLocal then 1 else 0.6) -- a phone and another player's aura: fewer arcs
    local list = layers()
    local made = {}

    local function dress(part)
        if not PARTS[part.Name] or not part:IsA("BasePart") or part:FindFirstChild("LightningRed") or (low and not LOW_PARTS[part.Name]) then
            return
        end
        local size = part.Size
        local volume = size.X * size.Y * size.Z
        for _, layer in list do
            if low and layer[1] ~= "LightningRed" and layer[1] ~= "LightningBlack" then
                continue -- a phone: the arcs only
            end
            local e = Instance.new("ParticleEmitter")
            for k, v in layer[5] do
                e[k] = v
            end
            e.Name = layer[1]
            e.Rate = math.clamp(volume * layer[2], layer[3], layer[4]) * thin
            e.Parent = part
            table.insert(made, e)
            if record then
                table.insert(record.items, e)
                e.Enabled = not record.culled
            end
        end
    end

    local model = root.Parent
    for _, part in model:GetChildren() do
        dress(part)
    end
    -- with streaming on, a far body part can reach the client after the build, or stream out and come back as a new part: dress it when it arrives
    local arrived = model.ChildAdded:Connect(dress)
    local function undress()
        arrived:Disconnect()
        for _, e in made do
            e:Destroy()
        end
        table.clear(made)
    end
    if record then
        table.insert(record.cleanups, undress)
    end
    fx.Destroying:Connect(undress)
    return undress
end

return BodyLightning
