-- The flying sword's pieces (tools/blender/weapons/flying_sword.py): centres as authored, in studs
-- from the sword's origin, where the rider's feet stand (lying flat, tip toward -Z, the spine's
-- centre plane at y = 0, its top Top above it). Edge and Core are glow pieces, found by colour (Hex).
-- Used by OutfitBuilder.storeSword; FlightService mounts the sword by its origin.
return {
    Top = 0.065,
    Pieces = {
        Body = { Centre = Vector3.new(0.0000, 0.0189, 0.2464) },
        Edge = { Centre = Vector3.new(0.0000, 0.0000, -1.2850), Hex = "4b8cff" },
        Core = { Centre = Vector3.new(0.0000, 0.0383, -0.6500), Hex = "9cc4ff" },
    },
    -- uploaded by us: the importer's own uploads are unreliable
    Maps = {
        Body = {
            Color = "rbxassetid://132234857829930", Normal = "rbxassetid://97876410493187",
            Roughness = "rbxassetid://108416515757332", Metalness = "rbxassetid://90728440821247",
        },
    },
}
