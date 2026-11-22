"""jade_lib_looks: the Roblox look of every material suffix in Jade Grove's library (2026-11-22). No texture anywhere: a mesh is split by material
(<piece>__<Suffix>) and each part takes a Roblox material and a colour. The same table drives the Blender previews and the Lua placements
(`Looks`), so what the renders show is what the builder sets. Palette: deep jade, teal, moss, soft mist-pale new growth, weathered timber and
grey-green stone; the only glow is a small Neon accent (never a light).

LOOKS[suffix] = (Roblox Material enum name, (r, g, b), extras dict).  Extras: Transparency, Reflectance, CastShadow.
The suffix must be letters only (WorldBuilder.splitName reads `__(%a+)$`).
"""

LOOKS = {
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
