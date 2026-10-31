"""Egg aura textures (the auras are built in src/worldbuild/EggAuraVFX.lua), drawn procedurally (run inside Blender: its Python has numpy). White with the
shape in alpha, tinted per egg in the game. Single frames only (the auras use no flipbooks).

Ground formations, one per egg:
- SigilWindRose (Spirit Breeze): six wind arms sweeping round a still centre, inside a ring of
  cloud-curl dashes.
- SigilWuxing (Elemental Core): the five-element cycle: five element rings joined by the
  generating pentagon and the overcoming star, round a diamond core.

Rings:
- AuraQiRing (Beginner Qi): a bold band of Qi with a fine inner thread strung with Qi beads, and six comet streaks
  riding just outside it, so the ring visibly flows as it turns (bold enough to read in daylight,
  which VFX Studio's hairline rings do not).

- AuraElementBand (Elemental Core): a gyroscope band: twin rails with a bright band between,
  broken by five element nodes (a ring round a bead), one per element of the cycle beneath.

Beams:
- AuraStream (Elemental Core): an element stream that tiles along its length: a bright core
  with two filaments braiding round it and packets of energy riding along it (scrolled by the
  beam's TextureSpeed).

Particles and floating objects:
- AuraFeather: a soft feather with its vane lines.
- AuraCloud: one auspicious cloud.
- AuraCrystal: a faceted crystal shard, modelled and rendered in Blender (near-white facets with
  bright edges, so it tints to any colour), floated round the eggs as a billboard.

Writes PNGs to assets/vfx/eggs/.
"""
import math
import os

import numpy as np

import qinggong_textures as Q

OUT = os.path.join(Q.REPO, "assets", "vfx", "eggs")
grid, smoothstep, line, glow, spiral_distance = Q.grid, Q.smoothstep, Q.line, Q.glow, Q.spiral_distance


def save(name, alpha):
    Q.OUT = OUT
    return Q.save(name, alpha)


def segment(x, y, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    t = np.clip(((x - ax) * vx + (y - ay) * vy) / (vx * vx + vy * vy), 0, 1)
    return np.hypot(x - (ax + vx * t), y - (ay + vy * t))


def sigil_wind_rose(size=768):
    x, y = grid(size)
    r, th = np.hypot(x, y), np.arctan2(y, x)
    px = 2.0 / size
    a = line(r - 0.92, 0.01, 2 * px)
    # a ring of cloud-curl dashes: short arcs each ending in a small curl
    for k in range(10):
        ang = k * math.tau / 10
        rel = (th - ang) % math.tau
        a = np.maximum(a, line(r - 0.82, 0.014, 2 * px) * (rel < 0.38))
        cx, cy = 0.82 * math.cos(ang + 0.38), 0.82 * math.sin(ang + 0.38)
        d, t = spiral_distance(x, y, cx, cy, 0.004, 0.045, 1.2, ang)
        a = np.maximum(a, line(d, 0.012, 2 * px))
    # six wind arms sweeping from the still centre out to the ring, thinning as they go
    for k in range(6):
        d, t = spiral_distance(x, y, 0, 0, 0.12, 0.74, 0.55, k * math.tau / 6, handed=-1)
        a = np.maximum(a, line(d, 0.05 * (1 - t) ** 1.2 + 0.006, 3 * px) * (r > 0.1) * (r < 0.76))
    a = np.maximum(a, line(r - 0.1, 0.012, 2 * px))
    a *= 1 - smoothstep(0.94, 0.97, r)
    return save("SigilWindRose", np.clip(a + glow(a, 5) * 0.5, 0, 1))


def sigil_wuxing(size=768):
    x, y = grid(size)
    r = np.hypot(x, y)
    px = 2.0 / size
    a = np.maximum(line(r - 0.94, 0.014, 2 * px), line(r - 0.88, 0.006, 2 * px))
    nodes = [(0.66 * math.cos(math.pi / 2 + k * math.tau / 5), 0.66 * math.sin(math.pi / 2 + k * math.tau / 5)) for k in range(5)]
    for k, (nx, ny) in enumerate(nodes):
        d = np.hypot(x - nx, y - ny)
        a = np.maximum(a, line(d - 0.14, 0.016, 2 * px))          # each element's ring
        a = np.maximum(a, line(d - 0.09, 0.006, 2 * px) * 0.8)
        bx, by = nodes[(k + 1) % 5]                               # the generating cycle (pentagon)
        a = np.maximum(a, line(segment(x, y, nx, ny, bx, by), 0.01, 2 * px) * (d > 0.14) * (np.hypot(x - bx, y - by) > 0.14))
        cx, cy = nodes[(k + 2) % 5]                               # the overcoming cycle (star)
        a = np.maximum(a, line(segment(x, y, nx, ny, cx, cy), 0.006, 2 * px) * 0.75 * (d > 0.14) * (np.hypot(x - cx, y - cy) > 0.14))
    ax_, ay_ = np.abs(x), np.abs(y)                               # the diamond core
    a = np.maximum(a, line(ax_ / 0.13 + ay_ / 0.18 - 1, 0.12, 0.05))
    a *= 1 - smoothstep(0.96, 0.99, r)
    return save("SigilWuxing", np.clip(a + glow(a, 5) * 0.5, 0, 1))


def qi_ring(size=768):
    x, y = grid(size)
    r, th = np.hypot(x, y), np.arctan2(y, x)
    px = 2.0 / size
    a = line(r - 0.86, 0.024, 3 * px)                                        # the band
    a = np.maximum(a, line(r - 0.785, 0.006, 2 * px) * 0.6)                  # a fine inner thread...
    for k in range(12):                                                      # ...strung with Qi beads
        ang = (k + 0.5) * math.tau / 12
        d = np.abs(x - 0.785 * math.cos(ang)) + np.abs(y - 0.785 * math.sin(ang))
        a = np.maximum(a, line(d, 0.04, 3 * px))
    for k in range(6):                                                       # comets: a soft head, a long tapering tail
        rel = (th - k * math.tau / 6) % math.tau
        t = np.clip(rel / 0.95, 0, 1)
        width = 0.032 * smoothstep(0, 0.05, t) * (1 - t) ** 0.8 + 0.002
        a = np.maximum(a, line(r - 0.93, width, 2 * px) * (rel < 0.95) * (1 - t) ** 0.6)
    a *= 1 - smoothstep(0.97, 0.99, r)
    return save("AuraQiRing", np.clip(a + glow(a, 6) * 0.7, 0, 1))


def element_band(size=768):
    x, y = grid(size)
    r, th = np.hypot(x, y), np.arctan2(y, x)
    px = 2.0 / size
    nodes = [(0.87 * math.cos(math.pi / 2 + k * math.tau / 5), 0.87 * math.sin(math.pi / 2 + k * math.tau / 5)) for k in range(5)]
    near = np.min([np.hypot(x - nx, y - ny) for nx, ny in nodes], axis=0)
    gap = smoothstep(0.075, 0.095, near)                                     # the band breaks round each node
    a = np.maximum(line(r - 0.81, 0.008, 2 * px), line(r - 0.93, 0.008, 2 * px)) * gap
    a = np.maximum(a, line(r - 0.87, 0.03, 3 * px) * gap)
    a = np.maximum(a, line(near - 0.06, 0.014, 2 * px))                      # each node: a ring...
    a = np.maximum(a, 1 - smoothstep(0.02, 0.03, near))                      # ...round a bead
    a *= 1 - smoothstep(0.97, 0.99, r)
    return save("AuraElementBand", np.clip(a + glow(a, 6) * 0.7, 0, 1))


def stream(w=512, h=128):
    x, y = grid(w, h)
    u = (x + 1) / 2                                   # every term has whole periods in u, so it tiles
    px = 2.0 / h
    core = line(y, 0.14, 0.14) * 0.75
    braids = np.maximum(line(y - 0.5 * np.sin(2 * math.pi * 2 * u), 0.06, 3 * px),
                        line(y + 0.5 * np.sin(2 * math.pi * 2 * u), 0.06, 3 * px)) * 0.8
    packets = smoothstep(0.55, 0.95, np.cos(2 * math.pi * 3 * u)) * (1 - smoothstep(0.05, 0.4, np.abs(y)))
    a = np.maximum(np.maximum(core, braids), packets)
    halo = glow(np.concatenate([a, a, a], axis=1), 3)[:, w:2 * w]   # blurred across the seam, so it tiles
    return save("AuraStream", np.clip(a + halo * 0.5, 0, 1) * (1 - smoothstep(0.85, 1, np.abs(y))))


def feather(size=256):
    x, y = grid(size)
    t = (y + 1) / 2
    width = 0.42 * np.sin(np.pi * np.clip(t, 0, 1)) ** 0.8 * (1 - 0.3 * t)
    bend = 0.12 * (t - 0.5) ** 2
    xs = x - bend
    vane = 1 - smoothstep(width * 0.85, width, np.abs(xs))
    barbs = 0.65 + 0.35 * np.abs(np.sin((y * 26 + np.abs(xs) * 10)))
    shaft = line(xs, 0.025, 0.01) * (t > 0.02)
    a = np.maximum(vane * barbs * (t > 0.08) * 0.85, shaft)
    return save("AuraFeather", np.clip(a + glow(a, 2) * 0.3, 0, 1))


def cloud(size=512):
    return save("AuraCloud", Q.cloud_cell(size, 3, Q.CLOUD_SHAPES[0]))


def crystal(size=512):
    """Renders a faceted crystal shard (a real Blender mesh) to a transparent PNG."""
    import bpy
    import sys
    sys.path.insert(0, os.path.join(Q.REPO, "tools", "blender", "eggs"))
    import egg_kit as K
    import egg_render as R
    mb = K.W.MeshBuilder()
    # a double-pointed crystal with two small splinters growing from its waist
    K.shard(mb, (0, -0.1, 0), (0.05, 1, 0.12), 1.35, 0.38, (0.5, 0.5), seed=7, sides=6)
    K.shard(mb, (0, 0.0, 0), (-0.05, -1, -0.12), 0.85, 0.36, (0.5, 0.5), seed=8, sides=6)
    K.shard(mb, (0.22, -0.1, 0.05), (0.7, 1, 0.2), 0.75, 0.15, (0.5, 0.5), seed=9, sides=5)
    K.shard(mb, (-0.2, 0.05, -0.05), (-0.8, 0.4, -0.15), 0.6, 0.13, (0.5, 0.5), seed=11, sides=5)
    coll = bpy.data.collections.get("VFXSprites") or bpy.data.collections.new("VFXSprites")
    old = bpy.data.objects.get("AuraCrystalMesh")
    if old:
        bpy.data.objects.remove(old)
    mat = bpy.data.materials.get("AuraCrystalMat") or bpy.data.materials.new("AuraCrystalMat")
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.85, 0.92, 1.0, 1)
    bsdf.inputs["Roughness"].default_value = 0.15
    bsdf.inputs["Emission Color"].default_value = (0.55, 0.7, 1.0, 1)
    bsdf.inputs["Emission Strength"].default_value = 0.35
    obj = mb.object("AuraCrystalMesh", coll, mat)
    for poly in obj.data.polygons:
        poly.use_smooth = False
    scene = R.lab()
    scene.render.film_transparent = True
    path = os.path.join(OUT, "AuraCrystal.png")
    os.makedirs(OUT, exist_ok=True)
    R.render([obj], path, view="three_quarter", size=(size, size), centre=(0, 0, 0.3), distance=5.2)
    scene.render.film_transparent = False
    return path


def build_all():
    return [sigil_wind_rose(), sigil_wuxing(), qi_ring(), element_band(), stream(), feather(), cloud(), crystal()]
