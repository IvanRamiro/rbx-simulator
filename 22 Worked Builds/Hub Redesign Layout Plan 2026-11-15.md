---
type: build
tags: [world, hub, plan]
created: 2026-11-15
status: kept from renders/hub_redesign before the renders were deleted (2026-11-22)
---

# Hub Redesign Layout Plan (2026-11-15)

The layout plan for the hub's rearrangement, saved here when the local review renders were deleted. The pictures are gone; the plan text is below. The design doc's Yggdrasil section is the current reference.

---
type: plan
tags: [hub, layout, yggdrasil]
date: 2026-11-15
status: phase 1, revision 2 (the owner's three answers applied), waiting for the owner's approval of the layout
---

# Main hub redesign: layout plan (phase 1)

The owner's brief: the World Tree at the centre; six pet pens round it, one per player (six players at most); each player's spawn
directly in front of their own pen; a Market, a Blacksmith and a Buy & Sell, grouped; the Leaderboard near the tree; the Hidden
Merchant beside the tree, opposite the Leaderboard. The reference image ([[Qi_Aura_Simulator_Design#Yggdrasil (built; the celestial
city since November 12, 2026)]], `assets/concepts/HubLayoutReference_2026-11-15.png`) is used for **placement only**. Nothing of its
look is copied: the hub stays the celestial crystal city (white marble, glowing crystal, light blue and gold), with no Chinese forms.

The greybox of this plan stands in the open place as `Workspace.HubBlockout` (built by `src/worldbuild/HubBlockout.lua`; its
`Layout` table holds the same numbers as this note). Screenshots are in this folder.

**Units and directions.** Hub-local studs: the World Tree at (0, 0), X east, Z south, ground Y 0 (world Y 200). A *bearing* is
`atan2(z, x)` in degrees: east 0, south 90, west 180, north -90. North is toward the outer islands, as today.

## The owner's decisions (2026-11-15)

1. **Shops: "Far side, like the reference".** The Market, Blacksmith and Buy & Sell stand together on the far side of the tree from the
   Arrival Plaza, to the north-east, with their own square; the bridges arrive on the Ring Road beside the district, not through it.
2. **Spawn facing:** toward the player's own pen.
3. **Buildings:** the Market, Blacksmith, Buy & Sell, Leaderboard and Merchant's dais are modelled new, as one celestial district.
   The Hatching Sanctum and the Qi Spring move as they are, with refreshed plinths.

---

## 1. The idea in one paragraph

Three rings and six spokes. The **Tree Ring** (today's paved ring round the tree's mound) is the hub's heart. The **six pens** stand
in a ring round it, each on its own lawn, each with its owner's **spawn pad** on the short spur between the Tree Ring and the pen's
gate. The **Ring Road** circles outside the pens and joins every bridge, the shops and the great root. **Six avenues** run out between
the pens: north to the Hatching Sanctum and the Ember Peak and Moonlit Isle bridges, south to the Arrival Plaza (the main entry),
north-east (the **Market Avenue**) straight into the Market Square, south-west to the Qi Spring, north-west toward the Jade Grove
bridge, south-east to the Ring Road. The **Leaderboard** stands at the head of the south avenue, against the tree, facing the Arrival
Plaza; the **Hidden Merchant** stands at the head of the north avenue, against the tree, facing the bridges. The reference's order
holds: entry at the bottom, the tree in the middle, the Merchant at the top, the shops at the top right.

## 2. Extent: keep the circle, add one lobe on the north-east

- **The core keeps its circle** (rim about 240 to 262 today). Every bridge keeps its exact line, length and gate (their first deck
  nodes stay at 245 from the centre, `Placements/Bridges.lua` unchanged), so the bridges, their Qi barriers, `WorldConfig.bridgeLanding`
  and the guardians' way home are untouched. The great root's head (0, 238) and the Root of the Island under the hub are untouched.
- **New ground: the Merchants' Terrace**, one lobe grown out of the north-east rim, from bearing -46 to 2, out to 385 from the tree.
  Its outline is each shop's footprint plus 18 studs, and the square's outer half, smoothed. The island's top grows from about
  196,000 to 226,000 square studs (+15%). In the blockout: the translucent blue slab with a darker rim line.
- **Kept clear of the Origin Abyss bridge.** No new ground lies within 7.4 degrees east of that bridge's line (32 studs at the rim),
  so its deck runs past the district over open air: the nearest new ground is 50 studs from the deck's centre line, 30 from its edge.
  The bridge lands on the Ring Road 97 studs from the square's edge, beside it.
- **No bridge moves.** Shifting the Origin landing north was considered (it is allowed) and isn't needed: between Moonlit Isle
  (bearing -76.5) and Origin Abyss (-55.2) there is no room for a district, and east of the Origin line there is plenty.
- Under the lobe: today's underside roots `YG_GripRoot6` (north-east; it climbs over the rim exactly where the square goes, seen in
  screenshot 03) and `YG_GripRoot0` (east) are re-routed over the new rim in phase 2. Nothing else hangs there (the old Qi Spring's
  waterfall at bearing -10 goes with the old spring).
- Where the core rim comes within 12 studs of the Ring Road (bearings 56 to 85, the great root's cove), a waist-high marble parapet
  runs along the road. Nowhere else needs one.

## 3. Every structure

Centre in hub-local studs; footprint is width along the front x depth (or diameter); *faces* is the bearing the front looks toward.
Heights are the range from the main mass to the highest point.

### The ring of pens and spawns

| | Bearing | Pen centre | `Yaw` (Pastures.lua) | Spawn pad (pen-local Z -48) | Board (Z -38) |
|---|---|---|---|---|---|
| Pen 1, south-east | 60 | (84.0, 145.5) | 0.5236 | (60.0, 103.9) | r 130 |
| Pen 2, south-west | 120 | (-84.0, 145.5) | -0.5236 | (-60.0, 103.9) | r 130 |
| Pen 3, west | 180 | (-168.0, 0) | -1.5708 | (-120.0, 0) | r 130 |
| Pen 4, north-west | -120 | (-84.0, -145.5) | -2.6180 | (-60.0, -103.9) | r 130 |
| Pen 5, north-east | -60 | (84.0, -145.5) | 2.6180 | (60.0, -103.9) | r 130 |
| Pen 6, east | 0 | (168.0, 0) | 1.5708 | (120.0, 0) | r 130 |

- **Sized for level 9 with a margin.** Each pen's ground is the level-9 pen with its paving ring (54 x 76, `PenLayout.Ring`) plus 4
  studs all round: a 62 x 84 plot, from 126 to 212 out. The fence (42 x 62 inside at level 9) keeps its front line 32 before the
  centre at every level and grows back and sideways, exactly as `shared/PenLayout` does now; nothing in PenLayout changes.
- Pens stand 72 studs apart (plot edge to plot edge) and 60 degrees apart, gate toward the tree.
- **Players are given pens in number order** (Pastures.lua row order): 1 and 2 first, flanking the Arrival Plaza.
- **Spawn pads**: a marble disc 12 across on the pen's spur, 120 from the centre, 10 studs before the owner's board and 16 before the
  gate, a crystal in its rim. **The player arrives facing their own pen** (the owner's choice). The owner's name plate on the board
  stands 8 to 10 studs up, so it reads over the player's own head from the default camera (at 5 studs the character hides it: seen in
  the blockout). Nothing taller than the pens' fences stands within 15 studs behind a pad, so the default camera has room.
- Each pen's spur (12 wide) runs from the Tree Ring through the spawn pad to the gate: spawn to pen 16 studs, spawn to the Tree Ring 10.

### The centre

| Structure | Centre | Footprint | Faces | Height | Notes |
|---|---|---|---|---|---|
| World Tree | (0, 0) | mound r 76 | | ~200 | unchanged (`ygg_tree.py`), with its arching roots and their colliders |
| Tree Ring | (0, 0) | ring r 80 to 104 | | flat | today's radii; repaved in the new paving set |
| **Leaderboard** (new model) | (0, 118) | 28 x 6 board on a dais 26 across | 90 (south) | 16 to 22 | at the head of the south avenue, its back to the tree, read from the Arrival Plaza 58 studs away |
| **Hidden Merchant** (new dais) | (0, -120) | dais 30 across, camp 14 x 10 | -90 (north) | 3 to 14 | beside the tree opposite the Leaderboard, at the head of the north avenue: everyone walking home from the northern bridges meets him. When he is away (50 minutes an hour) the dais stays: an empty, quiet place, not a hole |

### On the avenues

| Structure | Centre | Footprint | Faces | Height | Notes |
|---|---|---|---|---|---|
| **Hatching Sanctum** (moved as it is) | (0, -178) | dais 44 across, rotunda 36 | 90 (toward the tree); open north and south | 26 to 32 | on the north avenue between the Merchant and the Ring Road. Re-checked against the north-east district: no conflict (section 6) |
| **Qi Spring** (moved as it is) | (-147.2, 85) | court 48 across, basin 20 | -30 (toward the tree) | fountain 12 | on the south-west avenue, beside the Arrival Plaza: new players meditate here first. The bonus ring stays 10 studs (`TrainingStation.Radius`). Its overflow channel and waterfall are dropped (they would cross the Ring Road) |
| **Arrival Plaza** (main spawn, main entry) | (0, 176) | 48 across | | flat | the hub's own `IslandSpawn` (for anyone without a pen yet, and the fallback), facing north to the Leaderboard and the tree. The great root's way down leaves from its far side, across the Ring Road, at (0, 238) |
| **Seren, the Guide** | (10, 162) | | toward the main spawn | | on the plaza's north-east edge |

### The Merchants' Terrace (new ground, north-east)

The square sits where the Market Avenue (bearing -30) crosses the Ring Road; the shops stand in an arc beyond it, 84 studs from the
square's centre, each facing it.

| Structure | Centre | Footprint | Faces | Height | Notes |
|---|---|---|---|---|---|
| **Market Square** | (226.5, -110.5) | 56 across | | flat | bearing -26, 252 out; the Ring Road runs along its inner edge and the Market Avenue enters it |
| **Blacksmith** (Celestial Forge, new) | (235.3, -194.0) | 40 x 44, furnace tower 12 x 12 at the back | 96 (the square) | hall 18, tower 36 | the nearest shop to the northern bridges, so a player buys a weapon on the way out; its tower and smoke mark the district from across the hub and from the Origin and Moonlit bridges. Brann at its front. 34 studs from the Origin deck's edge |
| **Market** (Crystal Market, new) | (304.4, -141.9) | 48 x 40 | 158 (the square, toward the tree) | 18 to 30 | at the back of the arc, closing the view down the Market Avenue. Lyra at its front |
| **Buy & Sell** (Gilded Vault, new) | (288.9, -54.3) | 40 x 40 | -138 (the square) | 16 to 28 | the east end of the arc. Corvin at its forecourt counter |

- The three are 27 to 31 studs apart; each has a 14-wide forecourt from the square to its door (30 studs of it). Their backs keep 18
  to 27 studs to the new rim. Nearest other things: Pen 6 is 55 studs from Buy & Sell; Pen 5 is 82 from the Blacksmith.
- Designed as one district: the same base course, the same gold line and the same marble, three different silhouettes (the Market's
  arcade, the forge's tower, the vault's drum).

### The bridges

Unchanged lines and gates. Each gets an **apron** the deck's width (40) from the Ring Road out to its gate (226 to 247 from the centre).

| Bridge | Gate (first node) | Bearing | Reached by |
|---|---|---|---|
| Beginner Isle | (-244.7, 12.2) | 177.1 | Ring Road behind Pen 3 (from the south-west or north-west avenue, about 110 studs along the road) |
| Jade Grove | (-159.8, -185.7) | -130.7 | north-west avenue, then 75 studs along the road |
| Ember Peak | (-44.5, -240.9) | -100.5 | north avenue, past the Sanctum: 44 studs west of its end |
| Moonlit Isle | (57.3, -238.2) | -76.5 | north avenue, past the Sanctum: 57 studs east of its end |
| Origin Abyss | (139.9, -201.1) | -55.2 | the Ring Road, beside the Market Square (97 studs to its edge); the Market Avenue is 25 degrees along the road |

Three gates (Beginner, Jade, Origin) open onto the Ring Road just behind a pen (13 to 14 studs from its plot, with the road between).

## 4. Paths and circulation

| Path | Width | Where |
|---|---|---|
| Tree Ring | 24 | r 80 to 104 |
| Ring Road | 20 | r 216 to 236 |
| North, south and Market avenues | 20 | bearings -90, 90, -30 (the Market Avenue runs on into the square) |
| North-west, south-west, south-east avenues | 16 | bearings -150, 150, 30 |
| Pen spurs | 12 | Tree Ring to each gate, through the spawn pad |
| Bridge aprons | 40 | Ring Road to each gate |
| Shop forecourts | 14 | Market Square to each door |
| Root stair | 12 | Ring Road to the great root's head |

- Grass never grows under paving (the terrain under every path is a non-grass material that renders level: Pavement, as the pens'
  rings use today).
- **Walks** (path lengths at 16 studs/s): spawn to own gate 16 studs (1 s); spawn to the Tree Ring 10; neighbouring spawns 130 by
  the Tree Ring (8 s), opposite spawns 320 (20 s); Pen 5's spawn to the square's edge 190 by the paths (12 s, 140 over the
  lawn), Pen 1's 300 (19 s), the Arrival Plaza's 380 (24 s); Pen 4's spawn to the Sanctum about 90 (6 s); the Ember and Moonlit gates to the Sanctum's edge about 60
  (4 s); the Arrival Plaza to the Qi Spring 173 straight over the lawn (11 s). The lawns between paths are open, walkable grass.
- **The loops the game is built on:**
  - *New player:* pen spawn, Tree Ring, south avenue, Arrival Plaza (Seren), Qi Spring; then the Ring Road west to the Beginner bridge.
  - *Gearing up:* Tree Ring, Market Avenue, Market Square (Blacksmith first, nearest the bridges), then the Ring Road north-west to the
    Moonlit, Ember or Origin gate.
  - *Thief home:* bridge gate, Ring Road, north avenue (Ember, Moonlit), the north-west avenue (Jade) or the Ring Road west to the
    north avenue (Origin), the Sanctum, then past the Merchant to the Tree Ring and their pen. The egg is secured on setting foot on the
    hub, as now.
  - *Shopping:* pen, Tree Ring, Market Avenue, Market Square, any of the three.
- **Shops and bridges never cross.** Shop traffic uses the Market Avenue and the square; bridge traffic uses the aprons and the Ring
  Road. They only share the Ring Road's stretch between the square and the Origin apron, a 20-wide road with no building on it.
- **No dead ends:** every avenue ends on the Ring Road; every pen is reachable from the Tree Ring (front) and the Ring Road (round its
  side).

## 5. Sight lines

- **On spawning** (screenshot 05, Pen 5): the player's own pen straight ahead, its board and name plate, and beyond it the Ring Road and
  the bridge gates. From Pens 4 and 5 the northern gates frame the view, and from Pen 5 and Pen 6 the Market district stands to one
  side; from Pens 1 and 2 the Arrival Plaza and the spring are to one side. One turn shows the tree.
- **From the Arrival Plaza** (the main entry): the south avenue leads the eye to the Leaderboard, framed against the tree's trunk; the
  tree fills the sky. Seren is on the right. Across the hub, to the right of the trunk, the Blacksmith's tower and smoke mark the
  district (screenshot 02 shows the arrangement from above the entry).
- **The Leaderboard** faces the Arrival Plaza and the south avenue (read from 58 studs on the plaza, and from the south half of the
  Tree Ring). It is 16 to 22 tall, so its crest shows over the pens' fences (3.2 tall) from Pens 1 and 2's spawns.
- **The Merchant** faces the north avenue and the Sanctum: seen by everyone walking home from Ember Peak and Moonlit Isle.
- **The Market** closes the view down the Market Avenue; walking home over the Origin bridge, the district stands beside the deck on
  the left and the gate frames the tree ahead (screenshot 04).
- Nothing taller than the pens' fences stands between any spawn and the tree.

## 6. Systems that weren't on the owner's list

| System | Where it goes | Why |
|---|---|---|
| Hatching Sanctum (`HatchingAltar`) | north avenue (0, -178), unchanged by the district's move | four of five bridges land in the north; the thief from Ember Peak or Moonlit Isle walks straight in. The district is beyond the Ring Road, 160 studs east of it: no shared path, no crossing |
| Qi Spring | south-west avenue (-147.2, 85) | beside the Arrival Plaza, where new players start cultivating |
| Seren, the Guide | Arrival Plaza (10, 162) | meets players at the main entry |
| Brann, Lyra, Corvin | at each shop's front | as now, with the prompts beside them |
| The five bridge gates | unchanged | their aprons join the Ring Road |
| Great root and the Root of the Island | unchanged: from the Ring Road at the south, (0, 238), down the cliff | the root stair is a short paved way off the Ring Road |
| Hub spawn (`IslandSpawn`) | Arrival Plaza (0, 176) | for a player without a pen (a seventh player, or before a pen is given) |

**Guardians' way home, re-checked.** It depends only on the bridge landings and the hub's safe-zone radius, and neither changes:
the egg is secured inside 242 from the centre, and each thief's marker points 230 out along their bridge's line (`Guardian.lua`,
`SAFE_WAYPOINT_INSET`). For Origin Abyss that is (131, -189), on the Ring Road at its apron, outside the district. A thief can't
secure an egg on the Merchants' Terrace beyond 242, but no bridge leads there: every thief steps onto the hub at a gate first.

## 7. What must change in code (phase 3)

Bridges, guardians' homes, relics, the bridge barriers and every other island stay as they are.

**Data**
- `src/worldbuild/Placements/Pastures.lua`: the six rows above (Centre, Yaw, Area such as "south-east ring", `Spawn = Vector3.new(0, 0, -48)`).
  Footprint stays 54 x 76.
- `src/worldbuild/Placements/Yggdrasil.lua` (written by `hub_ground.py`): `Spawn` (0, ~2.2, 176); `Plots` (Blacksmith, BuySell,
  Marketplace: centres, sizes and yaws from section 3); `Shops` (signs, prompts and effects in each new building's frame); `Npcs`
  (Guide, Forgemaster, Curator, Appraiser); `Leaderboard` (0, 0.25, 118), facing south; `Merchant` (0, 0, -120), facing north;
  `QiSpring` (-147.2, 0.25, 85) and its `SpillEnd` (dropped); every `Kit` entry (paving, avenues, plazas, lamps). `Relics` unchanged.
- `src/worldbuild/Terrain/Yggdrasil.lua`: regenerated with the lobe.
- `src/shared/GameConfig.lua`: `HatchingAltar.Centre` (142.83, 0.25, 51.99) to (0, 0.25, -178), `Yaw` to 0 (its front, local +Z,
  toward the tree); quest `Way` points: "the Hatching Sanctum" (128, 47) to (0, -178), "the Blacksmith" (-118, 74), twice, to the
  Blacksmith's door (233, -172). "the great root" (1, 238) and every bridge and guardian point are unchanged.
- `src/server/World/WorldConfig.lua`: `Islands.Yggdrasil` keeps `Radius = 250` (the guardians' safe zone); add a `Reach` of 400
  that `WorldService.islandAt` uses instead of `Radius * 1.3` (325), or the Merchants' Terrace beyond 325 (it reaches 385) would count
  as no island.

**Server**
- `WorldService`: spawn and respawn each player at their pen's pad (the `PenSpawn` attribute `PenService` already sets), facing the
  pen; a fall on the hub returns them to their pad too; a player without a pen uses `IslandSpawn`. The clean way: six `SpawnLocation`
  pads built with the pens (`PenSpawn1` to `PenSpawn6`, `Enabled = false` so nobody else lands on them) and `player.RespawnLocation`
  set to the right one.
- `PenService`: assigns a pen before the player's first character loads (today it may run after); writes the new Area names.
- `MerchantService`: nothing in code; `ServerStorage.WanderingMerchant` is rebuilt at the new camp (`WorldBuilder.buildMerchantTemplate`).
- `ShopService`, `LeaderboardService`, `PetService` (the altar), `QiService` (the spring's `SpringWater`), `NpcService`: they find
  their parts by name, so they follow the rebuilt models; each is re-tested.

**Client**
- `GuideController`: Seren's pages say "East of the tree is the Qi Spring" and "the north lawn" for the Merchant; rewrite them for the
  new places ("Beside the Arrival Plaza..."; "beside the World Tree, on its north side"), and send players to the Market district
  "across the tree, to the north-east".
- `PenController`, `PenFence`, `PenPicker`, `WorldMarkers`, `QuestController`: no positions in code; re-tested.

**Build tools (phase 2)**
- `tools/blender/world/ygg_island.py`: the rim (the north-east lobe; the parapet line); its header and `PLOTS` describe the first hub
  and are rewritten.
- `tools/blender/world/hub_ground.py`: `SITES`, the avenues, plazas, rings, spurs, aprons, lamps and the terrain export.
- `tools/blender/world/hub_celestial.py`: the new pieces (section 9).
- `tools/blender/world/ygg_meshes.py`: the lobe's underside and the two grip roots re-routed over it.
- `src/worldbuild/WorldBuilder.lua`: `buildQiSpring` without the spill; `buildSpawn` from the new `Spawn`; nothing else structural.
- `src/worldbuild/PastureBuilder.lua`: the spawn pads; `clearGround()` first, to give the old spots back their grass.
- `layout.py`: nothing (the bridges stay).

**Saved in the place, to remove after the new hub is in:** the old `HB_*` kit instances, the old `Shops`, `HatchingAltar`, `QiSpring`,
`Leaderboard`, `IslandSpawn` and `BeastPastures` (rebuilt), the old pasture paving rings (back to grass), and `WorldKit.Yggdrasil`'s
old pieces. Count them first, strip, count again.

## 8. Performance budgets

Today's hub (without the tree's underside): 597 BaseParts (385 MeshParts, 376 casting shadows), 18 lights.

| Item | Triangles | Parts (MeshParts + colliders) | Notes |
|---|---|---|---|
| Market | 30k | 40 + 8 | split by material, as `hub_finish.py` does |
| Blacksmith | 30k | 40 + 8 | |
| Buy & Sell | 25k | 35 + 6 | |
| Hatching Sanctum | 25k | as today | moved, its plinth refreshed |
| Qi Spring | 15k | 25 | without the channel, its plinth refreshed |
| Leaderboard | 5k | 10 | the board is a SurfaceGui (as today) |
| Merchant's dais | 6k | 8 | the camp props are today's |
| Pen gate and board | 3k each | 12 each | one mesh, placed six times |
| Spawn pad | 1.5k each | 3 each | one mesh, six times |
| Paving (rings, avenues, aprons, plazas, the square) | 60k in all | 12 | in meshes of 10k triangles at most (Roblox caps a mesh at 20k; smaller pieces cull better) |
| Lamps (20) | 1.2k each | 3 each | |
| **The hub, new pieces in all** | **about 260k** | **under 700 BaseParts** | from any spawn at most about half is in front of the camera |

- **Textures:** none uploaded. Roblox materials only (Marble, Glass, Neon, Foil and Metal for gold, Slate), coloured per piece, as the
  celestial city is built today. Board faces are SurfaceGuis at 25 pixels per stud at most.
- **Collision:** gold trims, glow, crystal, inlays and small props: `CanCollide`, `CanTouch` and `CanQuery` off. Building shells:
  `Box` or `Hull` fidelity, with invisible box colliders for walls and floors players stand on; nothing `PreciseConvexDecomposition`
  except where a player really walks on a curved surface. Paving meshes lie on level terrain and don't collide (the terrain is the floor).
  Steps get a hidden ramp so walking never stutters.
- **CastShadow:** on for building shells, the tree, arches and the Sanctum's dome; off for paving, everything under 2 studs, trims,
  glow and crystal pieces, lamps, spawn pads, pens' fences (built on each client) and every collider.
- **Lights:** 16 PointLights at most in the hub, none with shadows: one per lamp pair (10), the forge, the Market, the Sanctum, the
  spring, the Merchant. Lamps: 20, one pair where each avenue reaches its place (the Sanctum, the Arrival Plaza, the Qi Spring, the
  Market Square) and at each of the five bridge aprons. The spawn pads' crystals mark the spawns; no lamps line the paths.
- **Streaming (StreamingEnabled on, target 1024, min 64):** the hub reaches 385 from its centre, so a player anywhere on it has all of
  it streamed. Each building is a Model with `ModelStreamingMode = Atomic` (never half drawn); what is `Persistent` today stays so
  (the altar's staged egg), and nothing new needs it. The lobe adds 15% of ground, a few thousand terrain voxels.
- **Camera:** no overhang under 14 studs over a path a player walks (the camera never gets trapped); arches over main paths 16 or
  more; nothing taller than a fence within 15 studs behind any spawn pad.

## 9. Phases 2 to 4

**Phase 2: modelling (Blender, after the owner approves this layout).** One asset at a time, each finished and exported before the
next, each through the quality gate (`qa_check --profile roblox` with no errors, six-view clay reviews, look-dev renders) and shown to
the owner before the next:
1. The ground: `ygg_island.py` rim and lobe, `ygg_meshes.py` underside (the two grip roots re-routed), `hub_ground.py` terrain and
   paving set (rings, avenues, spurs, aprons, the square, the plaza, the root stair, the parapet).
2. The three shops, designed together as one district.
3. The Leaderboard, the Merchant's dais, the spawn pad, the pen gate and board, the lamp; the Sanctum's and the spring's new plinths.
4. Export `Yggdrasil_Celestial.fbx` (anchor `HB_Anchor`), terrain and placements; scans for machine paths and banned words.

**Phase 3: Studio (the owner imports; then the build).** The owner imports the FBX files. Then, in Edit: store the kit, rebuild the
terrain, place the kit, the shops, altar, spring, leaderboard, spawn, root colliders, NPCs, the Merchant's template, the pastures
(after `clearGround`); move the code as in section 7. The owner saves the place.

**Phase 4: testing and removing the old hub.** Every risk below is tested in Play on a test save (`StudioTestSave`), then the old
hub's instances are counted and stripped, the design doc's Yggdrasil section is rewritten, and the work is committed when verified.

## 10. Risks, and how phase 3 tests them

| Risk | Test |
|---|---|
| A player spawns at the old hub spawn, at another player's pen, facing away, or before their pen is given | join with 1, then 6 players (Studio's local server); each lands on their own pad facing their pen; respawn (reset) lands there again; a seventh lands on the Arrival Plaza |
| A fall on the hub returns the player to the Arrival Plaza instead of their pad | jump off the rim at four bearings, and off the Merchants' Terrace's far edge |
| `islandAt` doesn't see the Merchants' Terrace (beyond 325) | stand behind the Market (380 out): the `Island` attribute stays Yggdrasil, the music stays the hub's |
| A player below the Origin rank reaches the Origin deck from the district's edge, past the barrier | jump and glide from the Terrace's edge toward the deck: the bridge's zone puts them back in front of the gate, as today |
| The safe zone: a thief secured too early or too late | carry an egg home over each of the five bridges: secured at the gate as today; the way-home marker points at the same place |
| The altar's window, the hatch cinematic or the staged egg broken by the move | hatch an egg (test save): the window opens, the egg rests in the cradle and breaks; the window closes when walking away |
| A shop's prompt, sign or effect left at the old place | open each window from its prompt; check the board, fire, smoke and coins sit on the new building |
| The Merchant appears at the old camp | force a visit (Studio): his camp copies in at the new dais, facing north; his prompt opens the window |
| The leaderboard stops filling | the board fills; reads the top ten |
| Quest markers point at old places | step through the Hatch, Weapon and Forge quests: the world marker points at the new Sanctum and Blacksmith |
| The spring's bonus at the wrong place | cultivate in the basin: +50%; at 13 studs out: none |
| Pens built on uneven ground, or grass through the paving rings | `PastureBuilder.check()` reports the new spots level and clear; look from the ground |
| Paths blocked, steps that stutter, a place the camera gets stuck | walk every path end to end in Play, with the camera zoomed in and out; walk under the arching roots on every spur |
| The lobe's underside clips the Origin bridge's abutment, or a grip root pokes through the square | look from the deck and from under the rim; walk the square |
| Old hub pieces left in the place | count the old instances before stripping and after (zero); grep the decoded place file for old names |
| Performance | in Play: the hub's part count, triangle estimate and draw calls from MicroProfiler at each spawn and on the Market Square; frame time against today's hub at the same spots |

## 11. Open questions

None for now: the owner's three answers are applied. The layout as drawn here waits for the owner's approval before any modelling.

Note: the owner's "Hidden Merchant" is the game's Wandering Merchant; his name in the game stays as it is unless the owner says.
