-- Realm6HalosConfig: every value behind the Realm 6 (Immortal) celestial halos. The runtime (Realm6Halos) holds no look of its
-- own.
--
-- The owner's brief (2026-11-10): "Celestial halos: Curved and segmented Beams + particle glints". The design doc's Realm 6
-- theme: layered halos and luminous energy wings, gold.
--
-- How it's built: each halo is a ring of curved Beam segments (each a circular arc: a Bezier whose handles run along the
-- ring's tangent, 4/3 tan(arc/4) of the radius long) with gaps between them, on one invisible anchored part that turns
-- (so turning a ring rewrites nothing). Textures painted from scratch (tools/vfx/realm6_halo_textures.py). Thin lines
-- with gaps, three rings each at its own speed and depth: never a flat glowing disc. Glints: one emitter on each joint of
-- the two rings behind the head, fired one at a time by script, riding the ring as it turns (LockedToPart).
--
-- Colour: a saturated gold with little light of its own, and lines bold enough to carry it (a hairline core greyed into
-- the sky). Paler or glowing, the rings vanished wherever they crossed the ivory wings (no contrast: seen in Play). A ZOffset (studs toward the camera) draws them over the wings' roots from in front and behind;
-- no ring reaches down past the shoulders (offset 1 stud, arcs drew over the torso).
--
-- Units: studs at character scale 1 (times Scale), degrees, seconds, radians a second. A ring's Centre is from the head's
-- centre: x the character's right, y up, z behind it.
return {
    Scale = 1,
    FallbackHead = 1.5, -- on a rig without a Head: the head's centre this far above the root part's (studs, scale 1)
    Bob = { Amount = 0.05, Speed = 0.9 }, -- all three float together, gently

    Rings = {
        {
            Name = "Crown", -- the halo proper, behind the head
            Texture = "CrownBand", Radius = 1.5, Width = 0.4, Segments = 12, Gap = 3, BeamSegments = 8,
            Centre = { 0, 1.1, 0.66 }, Plane = "Back", Spin = 0.15, -- behind the head's top, in front of the wings' roots
            Color = Color3.fromRGB(255, 178, 56), Transparency = 0, LightEmission = 0.3, Brightness = 1.0, ZOffset = 0.8,
            Grow = { Delay = 0.0, Time = 0.8 }, Glints = true,
        },
        {
            Name = "Graduated", -- a ring of fine graduations just outside it, a little farther back, turning the other way
            Texture = "GraduatedBand", Radius = 2.05, Width = 0.45, Segments = 8, Gap = 12, BeamSegments = 8,
            Centre = { 0, 1.25, 0.72 }, Plane = "Back", Spin = -0.07, -- its bottom (0.8 under the head's centre) stays above the shoulders
            Color = Color3.fromRGB(246, 158, 44), Transparency = 0, LightEmission = 0.2, Brightness = 1.0, ZOffset = 0.75,
            Grow = { Delay = 0.2, Time = 0.9 }, Glints = true,
        },
        {
            Name = "Orbit", -- a beaded orbit round and above the head, tilted, its tilt slowly turning (precessing)
            Texture = "OrbitBand", Radius = 1.8, Width = 0.32, Segments = 4, Gap = 20, BeamSegments = 12,
            Centre = { 0, 0.95, 0 }, Plane = "Tilted", Tilt = 72, Precess = 0.12, Spin = 0.35,
            Color = Color3.fromRGB(255, 188, 76), Transparency = 0, LightEmission = 0.3, Brightness = 1.0, ZOffset = 0.3,
            Grow = { Delay = 0.4, Time = 0.9 },
        },
    },
    GrowFrom = 0.55, -- each ring grows from this share of its radius as it appears (ease-out-back)
    Overshoot = 1.3,

    Textures = {
        CrownBand = "rbxassetid://109733879900942",
        GraduatedBand = "rbxassetid://76661890842510",
        OrbitBand = "rbxassetid://103966290878869",
        Glint = "rbxassetid://120100158319762",
    },

    Fade = { Out = 0.7, ShrinkTo = 0.7 }, -- destroy(): each ring shrinks to this share and fades

    -- the particle glints: one at a time, at a random joint of the rings marked Glints
    Glints = {
        Interval = { 0.25, 0.6 },
        Lifetime = { 0.45, 0.75 }, Rotation = { -15, 15 }, RotSpeed = { -30, 30 },
        Size = { { 0, 0 }, { 0.4, 0.42 }, { 1, 0 } }, Transparency = { { 0, 0 }, { 1, 0.3 } },
        Color = Color3.fromRGB(255, 220, 150), LightEmission = 1, LightInfluence = 0, Brightness = 1.0, ZOffset = 0.2,
    },

    Performance = {
        CullDistance = 140, -- studs from the camera past which other players' halos hide and stop
        LowQualityCullDistance = 70,
        LowQualityGlints = 0.5, -- share of the glints at low quality
    },
}
