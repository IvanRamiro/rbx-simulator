-- The six beast pen spots on Yggdrasil: the ONE table of where pens stand, read by the builder (PastureBuilder: the paving ring, the
-- gate, the board) and by the server (PenService: each spot's area name and order; it gives players spots in this order). The pen's
-- look and growth (shared/PenLayout, client/Pets/PenFence) are drawn in a spot's own frame, so moving a pen is editing its row here
-- and re-running PastureBuilder.build() (after PastureBuilder.clearGround() for the old spots).
--   Area       what players are told ("Your Beast Pasture: the south meadow")
--   Centre     the spot's centre, island-local studs (the hub's ground is Y 0 here: the builder sets it on the terrain under it)
--   Yaw        turns the spot's -Z (the pen's gate and the owner's board) toward the path players come by (now: the World Tree)
--   Footprint  the most ground the spot may use (X, Z studs): the largest pen level and its paving ring must fit (PastureBuilder checks)
--   Spawn      (a hook, unused now: the owner's planned re-layout puts each player's spawn before their own pen) a spot-local
--              position for its holder to spawn at; nil = the hub's usual spawn. PenService sets it on the holder as their PenSpawn
--              attribute (a world position); WorldService would read that when it places their character.
-- Found in Studio, 2026-11-15, by a search over the hub's meadow: each footprint on grass that is flat or gently sloped, clear of the
-- avenues, plazas, shops, the altar, the spring, the bridgeheads and every prop, with walkable ground before its front. Players are
-- given them in this order: the nearest to the spawn first.
return {
    { Area = "south meadow", Centre = Vector3.new(-37, 0, 206), Yaw = -0.178, Footprint = Vector2.new(54, 76), Spawn = nil },
    { Area = "south-east meadow", Centre = Vector3.new(158, 0, 128), Yaw = 1.010, Footprint = Vector2.new(54, 76), Spawn = nil },
    { Area = "south-west meadow", Centre = Vector3.new(-148, 0, 152), Yaw = -1.012, Footprint = Vector2.new(54, 76), Spawn = nil },
    { Area = "west meadow", Centre = Vector3.new(-151, 0, -31), Yaw = -1.773, Footprint = Vector2.new(54, 76), Spawn = nil },
    { Area = "north-east meadow", Centre = Vector3.new(125, 0, -91), Yaw = 2.200, Footprint = Vector2.new(54, 76), Spawn = nil },
    { Area = "north-west meadow", Centre = Vector3.new(-172, 0, -124), Yaw = -2.195, Footprint = Vector2.new(54, 76), Spawn = nil },
}
