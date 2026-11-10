"""Realm 6 (Immortal) elements built from Studio instances only (the owner's rules from the ornamental sigils on, 2026-11-10:
ParticleEmitter, Beam, Trail, Attachment and custom textures; no MeshParts; nothing generated at runtime: authored in
Studio). Textures come from what already exists (the owner, 2026-11-10: "WHY DO YOU NEED TO CREATE A NEW ONE? WHEN THERE
IS AN EXISTING PARTICLES IN ROBLOX STUDIO?"): Creator Store images, used by id, nothing uploaded. This file is the ONE place
every number lives:

    tools/vfx/realm6_build_luau.py  writes the Studio build scripts (tools/roblox/realm6/*.lua) and the motion config
                                    (src/client/Auras/Realm6MotionConfig.lua) from it
    tools/vfx/realm6_preview.py     renders offline previews from it

Frame: studs, the character's own axes: x its right, y up, z behind it; y = 0 is the ground under its root part (the
build script finds it from the root's size and the Humanoid's HipHeight). Every Attachment hangs on the HumanoidRootPart.
An Attachment is (position, X axis, Y axis): a Beam's curve handles run along X and, with FaceCamera off, its width along
Y. A ParticleEmitter on an Attachment fires along the attachment's +Y, and SpreadAngle.X turns about its X (measured in
Play: a source facing out level with X up fans all the way round the ground).

Straight Beams: handles a third of the beam's length, along it (X from Attachment0 to Attachment1); with CurveSize 0 a
Bezier crowds the texture toward both ends.

Property values: plain numbers/bools/strings, or tagged tuples:
    ("CS", [(t, (r, g, b)), ...])   ColorSequence        ("NS", [(t, v) or (t, v, envelope), ...])   NumberSequence
    ("NR", a, b)  NumberRange        ("V2", x, y)  Vector2        ("V3", x, y, z)  Vector3
    ("E", "TextureMode", "Stretch")  an Enum item       ("A", "MagicCircle")  a texture, by name (see TEXTURES)
"""
import math

# every texture: name -> (where it comes from, image asset id; None = not chosen yet: the build stops)
TEXTURES = {
    # the owner's magic circle: Creator Store decal 107338734690539 (Aogame12381) with its white outside cut to black and
    # clear (the owner's choice B, 2026-11-11; tools/vfx/realm6_circle_cutout.py -> assets/aura/realm6_circle/MagicCircle.png)
    # uploaded by the owner through Studio (1024 px). Not delivered yet: every upload from 2026-11-10 on fails with "No asset
    # content representation found" (see Work in Progress); earlier copies 99442536956304, 75927473983632 (512) are unused
    "MagicCircle": ("Creator Store decal 107338734690539, outside cut away (owner's upload)", 135356618504238),
    # the owner's picks for the vortex (2026-11-10; also offered: 18453651571 smoky wisps, 14364460918, 12191903502,
    # 113083314207224, 115544666170781): soft golden energy streams for the arms, a soft wisp for the comet trails
    "VortexEnergy": ("the owner's pick, Creator Store image 'Images/0008' (kmfssfkm)", 12251459424),
    "VortexTrail": ("the owner's pick, Creator Store image 'Images/Trails15' (BloxenRBLX)", 124753331461910),
    "PDSCrossSpark": ("PDS' Particles & Models Kit, Sparkles&Debris: a crisp crossed-star spark", 7216848832),
    # the owner's sea of clouds (2026-11-11): a 4x4 smoke-puff flipbook and a smoke wisp, existing Creator Store images
    "SmokePuff": ("the owner's pick, Creator Store image 'Images/225415aabzrzk1k1zz (2)' (PersonThatExlsts), 4x4", 13455668887),
    "SmokeWisp": ("the owner's pick, Creator Store image 'Images/413569800' (k3rxse)", 113821949376919),
    # still to choose from existing textures (the earlier drawn ones were rejected)
    "DustMote": ("to choose: an existing dust/sparkle texture", None),
    "ColumnCore": ("to choose: an existing beam texture", None),
    "ColumnHaze": ("to choose: an existing beam texture", None),
    "ColumnStreak": ("to choose: an existing streak texture", None),
}

UP = (0.0, 1.0, 0.0)
X_AXIS = (1.0, 0.0, 0.0)


def norm(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / n for c in v)


def att(name, pos, x=X_AXIS, y=UP):
    return {"name": name, "pos": tuple(pos), "x": norm(x), "y": norm(y)}


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


# ---- 1. the magic circle (ornamental sigils) ----------------------------------------------------------------------
def sigils():
    r = 5.0  # 10 studs across
    return {
        "name": "Sigils", "prefix": "Sigil_",
        "attachments": [att("Sigil_Circle_W", (-r, 0.04, 0.0), (1, 0, 0), (0, 0, 1)), att("Sigil_Circle_E", (r, 0.04, 0.0), (1, 0, 0), (0, 0, 1))],
        "beams": [{
            "name": "Sigil_Circle", "a0": "Sigil_Circle_W", "a1": "Sigil_Circle_E",
            "Texture": ("A", "MagicCircle"), "TextureMode": ("E", "TextureMode", "Stretch"), "TextureLength": 1, "TextureSpeed": 0,
            "FaceCamera": False, "Segments": 1, "CurveSize0": 2 * r / 3, "CurveSize1": 2 * r / 3, "Width0": 2 * r, "Width1": 2 * r,
            "Color": ("CS", [(0, (255, 196, 100)), (1, (255, 196, 100))]), "Transparency": ("NS", [(0, 0.1), (1, 0.1)]),
            "LightEmission": 1, "LightInfluence": 0, "Brightness": 1.2, "ZOffset": 0,
        }],
        "emitters": [], "trails": [],
    }


# ---- 2. golden vortex ---------------------------------------------------------------------------------------------
VORTEX = {"arms": 3, "turns": 1.25, "segments": 5, "y0": 0.3, "y1": 8.5, "r0": 2.6, "r1": 1.5, "period": 2.8}


def helix(arm, s):
    """A vortex arm at s (0 bottom .. 1 top): (position, tangent d/ds)."""
    V = VORTEX
    th = arm * 2 * math.pi / V["arms"] + s * V["turns"] * 2 * math.pi
    r = lerp(V["r0"], V["r1"], s)
    y = lerp(V["y0"], V["y1"], s)
    dth, dr, dy = V["turns"] * 2 * math.pi, V["r1"] - V["r0"], V["y1"] - V["y0"]
    pos = (r * math.cos(th), y, r * math.sin(th))
    tan = (dr * math.cos(th) - r * dth * math.sin(th), dy, dr * math.sin(th) + r * dth * math.cos(th))
    return pos, tan


def vortex():
    V = VORTEX
    attachments, beams, emitters, trails = [], [], [], []
    n = V["segments"]

    def alpha(s):  # the arm fades in at its root and out at its top (tuned in Play, 2026-11-10)
        return 0.22 + 0.78 * (1 - smoothstep(0.0, 0.16, s) * (1 - smoothstep(0.78, 1.0, s)))

    for arm in range(V["arms"]):
        for j in range(n + 1):
            p, t = helix(arm, j / n)
            attachments.append(att("Vortex_Arm%d_J%d" % (arm + 1, j), p, t, (p[0], 0.0, p[2])))
        for j in range(n):
            s0, s1 = j / n, (j + 1) / n
            _, t0 = helix(arm, s0)
            _, t1 = helix(arm, s1)
            keys = [(k / 4, round(alpha(lerp(s0, s1, k / 4)), 3)) for k in range(5)]
            beams.append({
                "name": "Vortex_Arm%d_Seg%d" % (arm + 1, j + 1), "a0": "Vortex_Arm%d_J%d" % (arm + 1, j), "a1": "Vortex_Arm%d_J%d" % (arm + 1, j + 1),
                "Texture": ("A", "VortexEnergy"), "TextureMode": ("E", "TextureMode", "Stretch"), "TextureLength": 1, "TextureSpeed": 0.6,
                "FaceCamera": True, "Segments": 10,
                "CurveSize0": math.sqrt(sum(c * c for c in t0)) / n / 3, "CurveSize1": math.sqrt(sum(c * c for c in t1)) / n / 3,
                "Width0": round(lerp(1.3, 0.6, s0), 3), "Width1": round(lerp(1.3, 0.6, s1), 3),
                "Color": ("CS", [(0, (255, 196, 92)), (1, (255, 226, 160))]) if j < n - 1 else ("CS", [(0, (255, 214, 130)), (1, (255, 236, 190))]),
                "Transparency": ("NS", keys), "LightEmission": 0.8, "LightInfluence": 0, "Brightness": 1.6, "ZOffset": 0,
            })
        a, b = "Vortex_Comet%d_A" % (arm + 1), "Vortex_Comet%d_B" % (arm + 1)
        p, _ = helix(arm, 0.0)
        attachments.append(att(a, p))
        attachments.append(att(b, (p[0], p[1] + 0.35, p[2])))
        trails.append({
            "name": "Vortex_Comet%d_Trail" % (arm + 1), "a0": a, "a1": b,
            "Texture": ("A", "VortexTrail"), "TextureMode": ("E", "TextureMode", "Stretch"), "TextureLength": 1,
            "Lifetime": 0.55, "MinLength": 0.05, "MaxLength": 0, "FaceCamera": True,
            "Color": ("CS", [(0, (255, 214, 120)), (1, (240, 150, 50))]), "Transparency": ("NS", [(0, 0.2), (1, 1)]),
            "WidthScale": ("NS", [(0, 1), (1, 0.2)]), "LightEmission": 0.7, "LightInfluence": 0, "Brightness": 1.0,
        })
        emitters.append({
            "name": "Vortex_Comet%d_Sparks" % (arm + 1), "parent": a,
            "Texture": ("A", "PDSCrossSpark"), "Rate": 14, "Lifetime": ("NR", 0.4, 0.7), "Speed": ("NR", 0.4, 1.0),
            "SpreadAngle": ("V2", 180, 180), "Acceleration": ("V3", 0, 0.5, 0), "Drag": 2.5,
            "Size": ("NS", [(0, 0.32), (1, 0)]), "Transparency": ("NS", [(0, 0.1), (1, 1)]),
            "Color": ("CS", [(0, (255, 226, 150)), (1, (255, 170, 60))]),
            "Rotation": ("NR", 0, 360), "RotSpeed": ("NR", -120, 120), "Orientation": ("E", "ParticleOrientation", "FacingCamera"),
            "LightEmission": 1, "LightInfluence": 0, "Brightness": 1.5, "ZOffset": 0.1, "LockedToPart": False,
        })
    motion = [{"kind": "helix", "arm": arm, "a": "Vortex_Comet%d_A" % (arm + 1), "b": "Vortex_Comet%d_B" % (arm + 1),
               "trail": "Vortex_Comet%d_Trail" % (arm + 1), "phase": arm / V["arms"], "width": 0.35} for arm in range(V["arms"])]
    return {"name": "Vortex", "prefix": "Vortex_", "attachments": attachments, "beams": beams, "emitters": emitters,
            "trails": trails, "motion": motion}


# ---- 3. sea of clouds: the owner's three emitters, as the owner specified them (2026-11-11). Orientation
# VelocityPerpendicular (the owner): each puff faces along its velocity, straight up from the source, so it lies flat as a
# cloud layer. Fields the owner left out are taken from the emitter before it (marked "as 1" / "as 2"); anything else is
# Roblox's default. Glow and wisp add light (LightEmission 1); the shadow is black, unlit, drawn behind.
CLOUD_GOLD = ("CS", [(0, (255, 168, 92)), (1, (255, 168, 92))])
CLOUD_GROW = ("NS", [(0, 0), (1, 20)])
CLOUD_FADE = ("NS", [(0, 0), (1, 1)])
CLOUD_FLAT = ("E", "ParticleOrientation", "VelocityPerpendicular")
CLOUD_Y = 2.7  # the root part's centre on the workbench dummy
# the owner's 10 blew the glow to a white orb that hid the character; lowered at the owner's word, tuned in Play
# (2026-11-11): at 3 the centre was still white, at 1.2 / 1.5 the gold reads and the wisp's texture shows
GLOW_BRIGHTNESS = 1.2
WISP_BRIGHTNESS = 1.5


def clouds():
    return {"name": "Clouds", "prefix": "Cloud_", "attachments": [att("Cloud_Source", (0, CLOUD_Y, 0))], "beams": [], "trails": [],
            "emitters": [
                {"name": "Cloud_Glow", "parent": "Cloud_Source", "Texture": ("A", "SmokePuff"),
                 "FlipbookLayout": ("E", "ParticleFlipbookLayout", "Grid4x4"), "FlipbookMode": ("E", "ParticleFlipbookMode", "OneShot"),
                 "Rate": 7, "Lifetime": ("NR", 0.8, 1.8), "Speed": ("NR", 0.001, 0.001), "SpreadAngle": ("V2", 3, 3),
                 "Size": CLOUD_GROW, "Transparency": CLOUD_FADE, "Color": CLOUD_GOLD, "Rotation": ("NR", -360, 360),
                 "Orientation": CLOUD_FLAT, "LightEmission": 1, "LightInfluence": 0, "Brightness": GLOW_BRIGHTNESS},
                {"name": "Cloud_Wisp", "parent": "Cloud_Source", "Texture": ("A", "SmokeWisp"),
                 "FlipbookLayout": ("E", "ParticleFlipbookLayout", "None"),
                 "Rate": 15, "Lifetime": ("NR", 0.5, 1), "Speed": ("NR", 0.001, 0.001), "SpreadAngle": ("V2", 2, 2),
                 "Size": CLOUD_GROW, "Transparency": CLOUD_FADE,  # size and transparency: as 1
                 "Color": CLOUD_GOLD, "Rotation": ("NR", -360, 360),
                 "Orientation": CLOUD_FLAT, "LightEmission": 1, "LightInfluence": 0, "Brightness": WISP_BRIGHTNESS},
                {"name": "Cloud_Shadow", "parent": "Cloud_Source", "Texture": ("A", "SmokeWisp"),
                 "FlipbookLayout": ("E", "ParticleFlipbookLayout", "None"),
                 "Rate": 10, "Lifetime": ("NR", 0.5, 1), "Speed": ("NR", 0.001, 0.001), "SpreadAngle": ("V2", 0, 0),
                 "Size": CLOUD_GROW, "Rotation": ("NR", -360, 360),  # lifetime, speed, size, rotation: as 2
                 "Transparency": CLOUD_FADE, "Color": ("CS", [(0, (0, 0, 0)), (1, (0, 0, 0))]),
                 "Orientation": CLOUD_FLAT, "LightEmission": 0, "LightInfluence": 0, "Brightness": 10, "ZOffset": -0.001},
            ]}


# ---- 4-5: ascension dust, column of light: their emitters and beams are laid out; each waits for an existing texture to
# be chosen (the drawn ones were rejected, 2026-11-10)
def dust():
    return {"name": "Dust", "prefix": "Dust_", "attachments": [att("Dust_Source", (0, 0.2, 0))], "beams": [], "trails": [],
            "emitters": [{
                "name": "Dust_Rise", "parent": "Dust_Source", "Texture": ("A", "DustMote"),
                "Rate": 22, "Lifetime": ("NR", 3.2, 4.8), "Speed": ("NR", 4.0, 6.5),
                "SpreadAngle": ("V2", 85, 85), "Acceleration": ("V3", 0, 1.1, 0), "Drag": 1.6,
                "Size": ("NS", [(0, 0), (0.1, 0.24, 0.06), (0.85, 0.2, 0.05), (1, 0)]),
                "Transparency": ("NS", [(0, 1), (0.1, 0.1), (0.3, 0.35), (0.45, 0.05), (0.6, 0.4), (0.75, 0.1), (1, 1)]),
                "Color": ("CS", [(0, (255, 236, 170)), (1, (255, 190, 90))]),
                "Rotation": ("NR", 0, 360), "RotSpeed": ("NR", -140, 140), "Orientation": ("E", "ParticleOrientation", "FacingCamera"),
                "LightEmission": 0.9, "LightInfluence": 0, "Brightness": 1.6, "ZOffset": 0.3, "LockedToPart": False,
            }]}


COLUMN_HANDLE = (60 - 0.05) / 3


def column():
    return {"name": "Column", "prefix": "Column_",
            "attachments": [att("Column_Base", (0, 0.05, 0), UP, X_AXIS), att("Column_Top", (0, 60, 0), UP, X_AXIS),
                            att("Column_StreakSource", (0, 0.1, 0))], "trails": [],
            "beams": [
                {"name": "Column_Core", "a0": "Column_Base", "a1": "Column_Top",
                 "Texture": ("A", "ColumnCore"), "TextureMode": ("E", "TextureMode", "Stretch"), "TextureLength": 6, "TextureSpeed": 0.35,
                 "FaceCamera": True, "Segments": 2, "CurveSize0": COLUMN_HANDLE, "CurveSize1": COLUMN_HANDLE, "Width0": 1.1, "Width1": 1.6,
                 "Color": ("CS", [(0, (255, 214, 140)), (1, (255, 190, 100))]),
                 "Transparency": ("NS", [(0, 0.85), (0.06, 0.88), (0.11, 0.5), (0.5, 0.62), (1, 1)]),
                 "LightEmission": 0.8, "LightInfluence": 0, "Brightness": 1.2, "ZOffset": 0},
                {"name": "Column_Haze", "a0": "Column_Base", "a1": "Column_Top",
                 "Texture": ("A", "ColumnHaze"), "TextureMode": ("E", "TextureMode", "Stretch"), "TextureLength": 2, "TextureSpeed": 0.12,
                 "FaceCamera": True, "Segments": 2, "CurveSize0": COLUMN_HANDLE, "CurveSize1": COLUMN_HANDLE, "Width0": 3.2, "Width1": 5.0,
                 "Color": ("CS", [(0, (255, 214, 140)), (1, (255, 214, 140))]),
                 "Transparency": ("NS", [(0, 0.85), (0.1, 0.72), (0.6, 0.82), (1, 1)]),
                 "LightEmission": 0.6, "LightInfluence": 0, "Brightness": 1.0, "ZOffset": -0.2},
            ],
            "emitters": [{
                "name": "Column_Streaks", "parent": "Column_StreakSource", "Texture": ("A", "ColumnStreak"),
                "Rate": 7, "Lifetime": ("NR", 1.8, 3.0), "Speed": ("NR", 12, 18),
                "SpreadAngle": ("V2", 2.5, 2.5), "Acceleration": ("V3", 0, 0, 0), "Drag": 0,
                "Size": ("NS", [(0, 0.5), (1, 0.4)]), "Squash": ("NS", [(0, 2.5), (1, 2.5)]),
                "Transparency": ("NS", [(0, 1), (0.08, 0.25), (0.7, 0.5), (1, 1)]),
                "Color": ("CS", [(0, (255, 240, 200)), (1, (255, 214, 140))]),
                "Rotation": ("NR", 0, 0), "RotSpeed": ("NR", 0, 0), "Orientation": ("E", "ParticleOrientation", "VelocityParallel"),
                "LightEmission": 1, "LightInfluence": 0, "Brightness": 1.3, "ZOffset": 0.2, "LockedToPart": False,
            }]}


ELEMENTS = {"Sigils": sigils, "Vortex": vortex, "Clouds": clouds, "Dust": dust, "Column": column}
ORDER = ["Sigils", "Vortex", "Clouds", "Dust", "Column"]
