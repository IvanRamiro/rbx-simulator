---
type: build
tags: [world, hub, import]
created: 2026-11-15
status: kept from renders/hub_redesign before the renders were deleted (2026-11-22)
---

# Hub Redesign Phase 3 Import (2026-11-15)

The import steps for the hub redesign's third phase. See also [[Hub Redesign Layout Plan 2026-11-15]].

---
type: handoff
tags: [hub, yggdrasil, import]
date: 2026-11-15
status: phase 2 done (modelled, QA'd, exported); waiting for the owner's import
---

# Main hub redesign: phase 3 import and build

Phase 2 built every new piece of the approved layout ([[LAYOUT_PLAN]]) headless in Blender, QA'd it (asset QA, profile roblox:
0 errors on every asset; renders/hub_redesign/phase2_qa.txt) and exported it. Review sheet: renders/hub_redesign/phase2_review.png.

## What the owner imports (File > Import 3D, in this order, into Workspace)

1. `assets/world/Yggdrasil/Yggdrasil_District.fbx`: 93 MeshParts and the anchor `HB_Anchor` (the island's centre). The Market,
   Blacksmith, Buy & Sell, Leaderboard, the Merchant's dais, the spawn pad, the Sanctum's and the Qi Spring's plinths, the Market
   Square's centrepiece, the paving (Tree Ring, Ring Road in four quarters, avenues, plazas, aprons, runes) and the parapet over the
   great root's cove. No textures: every piece takes a Roblox material by its name (`WorldBuilder.MaterialLooks`), so nothing is uploaded.
2. `assets/world/Yggdrasil/Yggdrasil_Underside.fbx`: 12 MeshParts (`YG_Slab0`-`4`, `YG_GripRoot0`-`6`) and the anchor `YG_Anchor`.
   No texture: they take the Yggdrasil atlas the underside already has.

Nothing else is imported: the World Tree, the Hatching Sanctum, the Qi Spring, the bridge gates and the lamps keep their stored templates.

## The Studio steps (Edit mode), after the import

```lua
local WB = require(game.ServerStorage.WorldBuild.WorldBuilder:Clone())

-- 1. the templates the new kit replaces (split names like HB_Market__Steel would otherwise linger) and the spring's dropped channel
local replaced = {
    HB_Market = true, HB_MarketCanopy = true, HB_MarketGlow = true, HB_Blacksmith = true, HB_BlacksmithCore = true,
    HB_BlacksmithCrystal = true, HB_BuySell = true, HB_BuySellStones = true, HB_Leaderboard = true, HB_LeaderboardGlow = true,
    HB_RingPlaza = true, HB_Plazas = true, HB_Avenues = true, HB_PavingRunes = true, HB_SpringChannel = true, HB_SpringChannelWater = true,
}
for _, t in game.ServerStorage.WorldKit.Yggdrasil:GetChildren() do
    if replaced[WB.splitName(t.Name)] then t:Destroy() end
end
-- 2. store the district (expect 93)
WB.storeKit("Yggdrasil", workspace.Yggdrasil_District, "HB_Anchor")
```

3. Copy the staged data over the live data (Rojo syncs them): `assets/world/Yggdrasil/phase3/Placements_Yggdrasil.lua` to
   `src/worldbuild/Placements/Yggdrasil.lua`, `phase3/Pastures.lua` to `src/worldbuild/Placements/Pastures.lua`,
   `phase3/Terrain_Yggdrasil.lua` to `src/worldbuild/Terrain/Yggdrasil.lua`; and make the code changes below.

```lua
-- 4. the terrain: buildTerrain ONLY. Do NOT run clearTerrain: the new heightfield's square (+-396) reaches Jade Grove's and the
--    Beginner Isle's terrain, and clearTerrain fills its whole square with air. buildTerrain rewrites only the columns the hub owns,
--    top to bottom, and the new rim is never inside the old one, so every old hub column is rewritten.
WB.buildTerrain("Yggdrasil")
WB.applyMaterialColors()
-- 5. the hub
WB.placeKit("Yggdrasil"); WB.buildShops("Yggdrasil"); WB.buildAltar("Yggdrasil"); WB.buildQiSpring("Yggdrasil")
WB.buildLeaderboard("Yggdrasil"); WB.buildSpawn("Yggdrasil"); WB.buildHubNpcs("Yggdrasil"); WB.buildMerchantTemplate("Yggdrasil")
-- 6. the underside: swap the changed pieces into the Island folder (seatImport clears its target, so seat them apart first)
local island = workspace.FloatingIslands.Yggdrasil.Island
local atlas = island.YG_Slab0.TextureID
WB.seatImport("Yggdrasil", workspace.Yggdrasil_Underside, "YG_Anchor", "IslandNew")
local new = workspace.FloatingIslands.Yggdrasil.IslandNew
for _, p in new:GetChildren() do
    local old = island:FindFirstChild(p.Name)
    if old then old:Destroy() end
    p.TextureID = atlas
    p.Parent = island
end
new:Destroy()
-- 7. the pens on their ring
require(game.ServerStorage.WorldBuild.PastureBuilder:Clone()).build()
-- 8. in a later call (collision applies asynchronously): WB.checkCollision(workspace.FloatingIslands.Yggdrasil) -> {}
```

9. The owner saves the place. Phase 4 then tests everything (LAYOUT_PLAN.md section 10) and removes the blockout (`HubBlockout.clear()`).

## Code changes phase 3 makes (nothing else moves)

- `WorldBuilder.Board`: `Face = { Centre = Vector3.new(0, 8.6, 1.09), Size = Vector2.new(20, 10.4) }`,
  `Title = { Centre = Vector3.new(0, 15.35, 1.09), Size = Vector2.new(11, 1.35) }`, `Star = Vector3.new(0, 21.3, 0)`. The
  board's interface is unchanged: a part `Board` with a SurfaceGui of `Row1`-`Row10` (Place, Cultivator, Rank, Qi), which
  LeaderboardService fills.
- `WorldBuilder.Shops` and `WorldBuilder.Plots`: unchanged (the new buildings keep the piece names). The prompts, signs and effects
  come from the new `Placements.Shops`; the keepers stand at the new `Placements.Npcs` (Forgemaster beside the anvil, Curator behind
  the central counter, Appraiser inside the curved counter).
- `WorldBuilder.Appearance` (new names): `HB_RingRoadNE/SE/SW/NW` and `HB_Aprons` like `HB_Avenues` (no collision, no shadow; their
  `__Gold` SmoothPlastic gold); `HB_SpawnPadGlow`, `HB_SquareCompassGlow`, `HB_MerchantDaisGlow` Neon crystal (no collision, no
  shadow); `HB_SpawnPad`, `HB_SanctumPlinth`, `HB_SpringPlinth` CastShadow off.
- `WorldBuilder.Collision` (new names): `HB_RingParapet` and `HB_MerchantDais` PreciseConvexDecomposition (a hull would fill the arc in
  front of them); `HB_SquareCompass` Hull; `HB_SpawnPad`, `HB_SanctumPlinth`, `HB_SpringPlinth` and every new `...Glow` Box. The
  shops keep their rules (PreciseConvexDecomposition: players walk in), the canopies and glows Box.
- `WorldBuilder.buildQiSpring`: no `SpillEnd` any more (no channel, no waterfall): skip `buildWaterfall` when it is nil.
- `GameConfig.HatchingAltar`: `Centre = Vector3.new(0, 0.25, -178)`, `Yaw = 0`. Quests: "the Hatching Sanctum" to (0, -178);
  "the Blacksmith" (twice) to (233, -172).
- `WorldConfig.Islands.Yggdrasil`: add `Reach = 400`, used by `WorldService.islandAt` (the terrace reaches 385 from the centre).
- `WorldService`: spawn and respawn at the player's pen pad (`Placements.Yggdrasil.PenSpawns`, the `PenSpawn` attribute), facing
  the pen; a fall on the hub returns there; `IslandSpawn` (the Arrival Plaza) for a player without a pen.
- `PenService`: give the pen before the first character spawns.
- `GuideController`: Seren's lines about the spring ("beside the Arrival Plaza"), the Merchant ("beside the World Tree, on its north
  side") and the shops ("across the tree, to the north-east").

## Budgets as built (triangles; each MeshPart under 20,000)

| Piece | Triangles | Note |
|---|---|---|
| Market | 16,104 | colonnade, crystal dome with the egg of light, three counters, two porch stalls |
| Blacksmith | 8,652 | vaulted hall, hearth, anvil, trough, rack; the chimney tower with its furnace mouth |
| Buy & Sell | 12,796 | drum, gold dome, the balance, vault door, portico, curved counter |
| Leaderboard | 4,592 | |
| Merchant's dais | 4,446 | |
| Spawn pad | 1,756 | one mesh, placed six times |
| Sanctum plinth / Spring plinth | 3,848 / 3,912 | |
| Square centrepiece | 2,476 | |
| Paving and parapet | 73,824 | in 43 meshes; over the plan's 60k by a fifth, inside every per-mesh limit |
| Underside (changed pieces) | 23,210 | |

No textures: Roblox materials only. UVs tile the material every 8 studs (each face cut to its 8-stud cell, so no UV leaves 0-1).
CastShadow on for the shops' shells, the Leaderboard and the dais; off for paving, plinths, pads, glows and crystal.

## Phase 3: done (2026-11-15), one re-import left

Built in the open place as above. One change after seeing it in Studio: the Blacksmith tower's crown (a flared square cap with prongs
curling out) read from afar as an upturned eave, so it is now a round gold brazier whose prongs curl in round the crystal.

**Owner's re-import:** File > Import 3D `assets/world/Yggdrasil/Yggdrasil_Blacksmith.fbx` (9 pieces, anchor `HB_Anchor`). Then:

```lua
local WB = require(game.ServerStorage.WorldBuild.WorldBuilder:Clone())
for _, t in game.ServerStorage.WorldKit.Yggdrasil:GetChildren() do
    local base = WB.splitName(t.Name)
    if base == "HB_Blacksmith" or base == "HB_BlacksmithCore" or base == "HB_BlacksmithCrystal" then t:Destroy() end
end
WB.storeKit("Yggdrasil", workspace.Yggdrasil_Blacksmith, "HB_Anchor")
WB.buildShops("Yggdrasil")
```

Its sign, prompt, forge and smoke spots are unchanged (the smoke rises from the brazier at the same height).
