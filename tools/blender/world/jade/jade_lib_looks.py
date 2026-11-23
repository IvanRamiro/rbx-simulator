"""jade_lib_looks: the Roblox look of every material suffix in Jade Grove's library (2026-11-22). No texture anywhere: a mesh is split by material
(<piece>__<Suffix>) and each part takes a Roblox material and a colour. The same table drives the Blender previews and the Lua placements
(`Looks`), so what the renders show is what the builder sets. Palette: deep jade, teal, moss, soft mist-pale new growth, weathered timber and
grey-green stone; the only glow is a small Neon accent (never a light).

LOOKS[suffix] = (Roblox Material enum name, (r, g, b), extras dict).  Extras: Transparency, Reflectance, CastShadow.
The suffix must be letters only (WorldBuilder.splitName reads `__(%a+)$`).
"""

# Polish pass 2026-11-23 (the owner saw the island in Studio: "dim and murky"): the leaf, moss, ground-cover and plant values are lifted by 15 to 25 percent and the palette has more range
# (deep jade shadows that stay dark, a brighter jade mid, pale new growth and a warm pale-gold edge on it, lime ferns, gold flower centres). It stays Jade's own: green and teal, never
# Blossom's rose, Ember's basalt and fire, Moonlit's blue silver or Origin's violet black; Neon stays on the small glow-cap accents (GlowTeal, GlowAmber) only.
LOOKS = {
    # wood and bark
    "Trunk": ("Wood", (84, 68, 54), {}),                 # umber bark with a green cast, a little lighter than before (the dark trunks were part of the murk)
    "TrunkPale": ("Wood", (172, 170, 146), {}),          # the slender tree's silvery bark
    "Root": ("Wood", (68, 56, 46), {}),
    "Culm": ("SmoothPlastic", (118, 176, 84), {}),       # a bamboo culm
    "CulmNode": ("SmoothPlastic", (66, 104, 54), {}),
    "CulmPale": ("SmoothPlastic", (214, 232, 164), {}),  # young shoots: pale gold-green
    "Plank": ("WoodPlanks", (146, 118, 90), {}),
    "PlankDark": ("WoodPlanks", (96, 77, 60), {}),
    "Timber": ("Wood", (122, 96, 70), {}),
    "Shingle": ("Wood", (88, 75, 58), {}),
    "Cord": ("Fabric", (204, 180, 126), {"CastShadow": False}),
    # leaves and ground cover
    "LeafDeep": ("LeafyGrass", (24, 98, 72), {}),        # deep jade: the shadow tone, still dark but no longer black-green
    "LeafMid": ("LeafyGrass", (50, 150, 104), {}),       # the jade of the island
    "LeafPale": ("LeafyGrass", (188, 232, 162), {}),     # new growth: pale, with a warm gold-green edge
    "LeafTeal": ("LeafyGrass", (40, 150, 144), {}),
    "Fern": ("LeafyGrass", (58, 164, 90), {}),
    "FernBright": ("LeafyGrass", (130, 208, 104), {}),   # bright lime-jade
    "Moss": ("LeafyGrass", (104, 158, 66), {}),
    "MossDeep": ("LeafyGrass", (64, 114, 56), {}),
    "Grass": ("LeafyGrass", (134, 190, 92), {}),
    "GrassPale": ("LeafyGrass", (208, 226, 142), {}),    # pale gold-green: the sunlit tips
    # stone
    "Rock": ("Rock", (112, 118, 110), {}),
    "RockDark": ("Rock", (74, 82, 80), {}),
    "RockPale": ("Rock", (156, 160, 148), {}),
    "Stone": ("Cobblestone", (128, 132, 120), {}),       # worked stone: steps, plinths, lanterns, carved markers
    "StoneDark": ("Cobblestone", (88, 92, 86), {}),
    "Jade": ("SmoothPlastic", (62, 196, 150), {"Reflectance": 0.08}),   # polished jade seams and inlays
    "JadeGlass": ("Glass", (88, 222, 180), {"Transparency": 0.3, "CastShadow": False}),
    "Soil": ("Mud", (78, 62, 48), {}),
    # flowers
    "BloomWhite": ("SmoothPlastic", (250, 252, 244), {"CastShadow": False}),
    "BloomRose": ("SmoothPlastic", (244, 176, 198), {"CastShadow": False}),
    "BloomViolet": ("SmoothPlastic", (184, 156, 230), {"CastShadow": False}),
    "BloomGold": ("SmoothPlastic", (255, 224, 122), {"CastShadow": False}),
    "CapPale": ("SmoothPlastic", (216, 242, 230), {}),
    # glow: small Neon accents only (the island has at most eight PointLights; none of them are on these)
    "GlowTeal": ("Neon", (40, 236, 200), {"CastShadow": False}),
    "GlowAmber": ("Neon", (255, 184, 92), {"CastShadow": False}),
    # water
    "Water": ("Glass", (76, 180, 170), {"Transparency": 0.45, "CastShadow": False}),
}


# phase A's table (kept for the before and after sheets only; nothing reads it for the game)
LOOKS_PHASE_A = {
    # wood and bark
    "Trunk": ("Wood", (74, 60, 48), {}),                 # dark umber bark with a green cast
    "TrunkPale": ("Wood", (152, 152, 130), {}),          # the slender tree's silvery bark
    "Root": ("Wood", (60, 50, 42), {}),
    "Culm": ("SmoothPlastic", (98, 150, 70), {}),        # a bamboo culm
    "CulmNode": ("SmoothPlastic", (52, 84, 44), {}),
    "CulmPale": ("SmoothPlastic", (190, 214, 152), {}),  # young shoots
    "Plank": ("WoodPlanks", (136, 110, 84), {}),
    "PlankDark": ("WoodPlanks", (90, 72, 56), {}),
    "Timber": ("Wood", (112, 88, 64), {}),
    "Shingle": ("Wood", (82, 70, 54), {}),
    "Cord": ("Fabric", (196, 172, 120), {"CastShadow": False}),
    # leaves and ground cover
    "LeafDeep": ("LeafyGrass", (22, 84, 62), {}),
    "LeafMid": ("LeafyGrass", (40, 120, 88), {}),
    "LeafPale": ("LeafyGrass", (152, 206, 168), {}),
    "LeafTeal": ("LeafyGrass", (34, 126, 124), {}),
    "Fern": ("LeafyGrass", (46, 134, 76), {}),
    "FernBright": ("LeafyGrass", (104, 176, 92), {}),
    "Moss": ("LeafyGrass", (84, 128, 56), {}),
    "MossDeep": ("LeafyGrass", (52, 92, 48), {}),
    "Grass": ("LeafyGrass", (110, 160, 78), {}),
    "GrassPale": ("LeafyGrass", (172, 198, 122), {}),
    # stone
    "Rock": ("Rock", (108, 114, 106), {}),
    "RockDark": ("Rock", (70, 78, 76), {}),
    "RockPale": ("Rock", (150, 154, 142), {}),
    "Stone": ("Cobblestone", (122, 126, 114), {}),       # worked stone: steps, plinths, lanterns, carved markers
    "StoneDark": ("Cobblestone", (84, 88, 82), {}),
    "Jade": ("SmoothPlastic", (52, 172, 132), {"Reflectance": 0.08}),   # polished jade seams and inlays
    "JadeGlass": ("Glass", (74, 200, 160), {"Transparency": 0.3, "CastShadow": False}),
    "Soil": ("Mud", (72, 58, 44), {}),
    # flowers
    "BloomWhite": ("SmoothPlastic", (242, 246, 238), {"CastShadow": False}),
    "BloomRose": ("SmoothPlastic", (238, 162, 186), {"CastShadow": False}),
    "BloomViolet": ("SmoothPlastic", (172, 142, 222), {"CastShadow": False}),
    "BloomGold": ("SmoothPlastic", (246, 206, 100), {"CastShadow": False}),
    "CapPale": ("SmoothPlastic", (206, 236, 222), {}),
    # glow: small Neon accents only (the island has at most eight PointLights; none of them are on these)
    "GlowTeal": ("Neon", (40, 236, 200), {"CastShadow": False}),
    "GlowAmber": ("Neon", (255, 184, 92), {"CastShadow": False}),
    # water
    "Water": ("Glass", (70, 170, 160), {"Transparency": 0.45, "CastShadow": False}),
}


# which materials never collide whatever the piece (foliage, glow, glass, cloth)
NO_COLLIDE = {"LeafDeep", "LeafMid", "LeafPale", "LeafTeal", "Fern", "FernBright", "Moss", "MossDeep", "Grass", "GrassPale", "BloomWhite", "BloomRose",
              "BloomViolet", "BloomGold", "CapPale", "GlowTeal", "GlowAmber", "Water", "JadeGlass", "Cord", "CulmPale"}

# the angle (degrees) over which an edge is smoothed in the preview and the export: foliage stays crisp, bark and stone read rounded
SMOOTH = {"LeafDeep": 60, "LeafMid": 60, "LeafPale": 60, "LeafTeal": 60, "Fern": 50, "FernBright": 50, "Trunk": 58, "TrunkPale": 58, "Root": 55, "Culm": 70, "CulmNode": 60, "CulmPale": 70, "Rock": 38, "RockDark": 38, "RockPale": 38,
          "Stone": 30, "StoneDark": 30, "Moss": 40, "MossDeep": 40, "Jade": 40, "Plank": 25, "PlankDark": 25, "Timber": 30, "Shingle": 25}
DEFAULT_SMOOTH = 34

# Part-count cuts (polish pass 2026-11-23): in the game each material mesh of a piece is one MeshPart, and the part count (not the triangles) is what the draw calls follow.
# MERGE[piece] = {from suffix: to suffix}: that material's geometry joins the other's, so the piece exports with fewer meshes. Applied at the end of every family's build_all().
_STONE = {"StoneDark": "Stone", "Moss": "Stone"}
_SLAB = {"RockPale": "Rock", "RockDark": "Rock"}
_WALL = {"RockPale": "Rock", "Root": "Moss", "MossDeep": "Moss"}
MERGE = {
    # structures: small props placed many times keep one stone and their glow (the moss patches were a few triangles)
    "JG_Path_Slab_P1": _STONE, "JG_Path_Slab_P2": _STONE, "JG_Path_Slab_P3": _STONE,
    "JG_Lantern_Sprout_L1": _STONE, "JG_Lantern_Sprout_L2": _STONE,
    "JG_Ruin_Column_C1": _STONE, "JG_Ruin_Column_C2": _STONE,
    "JG_Waymarker_W1": _STONE, "JG_Waymarker_W2": _STONE, "JG_Waymarker_W3": _STONE,
    "JG_Offering_Table_O1": {"StoneDark": "Stone", "Moss": "Stone", "RockDark": "Stone", "RockPale": "Stone", "Cord": "Timber"},
    # rocks
    "JG_Rock_StandingSlab_L3": _SLAB, "JG_Rock_LeaningSlab_L1": _SLAB, "JG_Rock_LeaningSlab_L2": _SLAB,
    "JG_Rock_MossBoulders_B1": {"RockPale": "Rock", "MossDeep": "Moss"}, "JG_Rock_MossBoulders_B2": {"RockPale": "Rock", "MossDeep": "Moss"},
    "JG_Rock_JadeVein_J1": {"RockPale": "Rock", "RockDark": "Rock", "JadeGlass": "Jade"},
    "JG_Rock_SplitStone_S1": {"RockPale": "Rock", "Root": "Trunk", "LeafPale": "LeafMid", "LeafDeep": "LeafMid"},
    "JG_Rock_TerraceStep_T1": {"RockPale": "RockDark"}, "JG_Rock_RiverStones_R2": {"RockPale": "Rock"},
    # plants and fungi: the root knot takes the plant's own green, the soil the grass's, the dark moss the moss's
    "JG_Plant_Grass_G1": {"Soil": "Grass"}, "JG_Plant_Grass_G2": {"Soil": "Grass"},
    "JG_Plant_Fern_Fountain_F1": {"Root": "Fern"}, "JG_Plant_Fern_Crown_F2": {"Root": "Fern"}, "JG_Plant_BroadLeaf_L1": {"Root": "Fern", "LeafMid": "Fern"},
    "JG_Plant_Orchid_O1": {"Root": "Fern"}, "JG_Plant_FlowerBush_C1": {"Root": "LeafDeep"},
    "JG_Mush_Parasol_M1": {"MossDeep": "Moss"}, "JG_Mush_Cluster_M3": {"MossDeep": "Moss"}, "JG_Mush_Funnel_M4": {"MossDeep": "Moss"},
    "JG_Moss_Mat_M1": {"MossDeep": "Moss"}, "JG_Moss_Mat_M2": {"MossDeep": "Moss"},
    "JG_Log_Fallen_L1": {"Timber": "Trunk", "RockDark": "Trunk", "LeafPale": "FernBright"}, "JG_Log_Stump_S1": {"Timber": "Trunk", "LeafPale": "FernBright"},
    # trees and bamboo: roots join the bark (or the culm node's dark green), the pale and the dark trunk of the small tree are one
    "JG_Tree_Mistbough_D1": {"TrunkPale": "Trunk", "Root": "Trunk"}, "JG_Tree_Mistbough_D2": {"TrunkPale": "Trunk", "Root": "Trunk"},
    "JG_Tree_Spiral_C1": {"Root": "CulmNode"}, "JG_Tree_Spiral_C2": {"Root": "CulmNode"},
    "JG_Tree_Buttress_B1": {"Root": "Trunk"}, "JG_Tree_Buttress_B2": {"Root": "Trunk"}, "JG_Tree_Veil_F1": {"Root": "Trunk"},
    "JG_Bamboo_Grove_G1": {"Root": "CulmNode"}, "JG_Bamboo_Grove_G2": {"Root": "CulmNode"}, "JG_Bamboo_Clump_K1": {"Root": "CulmNode"}, "JG_Bamboo_Clump_K2": {"Root": "CulmNode"},
    "JG_Bamboo_Shoots_S1": {"Timber": "CulmNode", "MossDeep": "Moss"},
    # cliffs: the walls on the ridge and the plateau, the pool rims, the cascade and the rim lip: three rocks at most
    "JG_Cliff_Wall_W1": _WALL, "JG_Cliff_Wall_W2": _WALL, "JG_Cliff_PoolRim_P1": {"RockPale": "Rock"}, "JG_Cliff_PoolRim_P2": {"RockPale": "Rock"},
    "JG_Cliff_Cascade_C1": {"RockPale": "Rock"}, "JG_Cliff_RimLip_R1": {"RockPale": "Rock"},
}
