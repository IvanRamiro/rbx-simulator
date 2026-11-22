"""The Unorthodox sword's fittings (run inside Blender): the one-sided guard, the collar, the grip with its lashings, the cap and the
interlocked link pommel. Every part is built twice from the same numbers: a high-detail version (real bevels, a pierced plate, twisted
cord) that the maps are baked from, and, where the game mesh cannot simply be the decimated high one, a low version.

Authored in Roblox studs from the grip (point toward -Z). Parts and their contacts (z along the weapon):
  blade foot        z -0.70 (inside the guard), the blade leaves the plate at z -1.0;
  seppa (spacers)   z -0.79 .. -0.815 behind the plate;
  guard plate       z -0.845 .. -0.995 (raised face -0.815 .. -1.025), the blade passes through it, the arm leaves its left edge;
  habaki            z -1.025 .. -1.31, round the blade, touching the plate's front;
  fuchi collar      z -0.79 .. -0.58, touching the seppa, round the grip core;
  grip core         z -0.62 .. +0.80, radius 0.115, three lashings of linen cord on it;
  kashira cap       z +0.60 .. +0.92 over the core's end;   eye lug on it z +0.93 .. +1.07;
  link A (flat)     passes through the eye; link B (upright) passes through link A.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

import secret_kit as SK  # noqa: E402

WK, Hm, W = SK.WK, SK.Hm, SK.W
V = Vector
TAU = math.tau

# ---- numbers ----
PLATE_Z = -0.92
PLATE_HALF = 0.072
GRIP_R = 0.135
GRIP0, GRIP1 = -0.66, 0.80
BANDS = [(-0.555, -0.255), (-0.135, 0.165), (0.285, 0.565)]


def rrect(k=8, p=0.55):
    """A rounded rectangle profile of 4k points (a unit squircle)."""
    return SK.lens_profile(k * 2, flat=1 - p) if False else [(math.copysign(abs(math.cos(TAU * i / (4 * k))) ** p, math.cos(TAU * i / (4 * k))),
                                                            math.copysign(abs(math.sin(TAU * i / (4 * k))) ** p, math.sin(TAU * i / (4 * k)))) for i in range(4 * k)]


def mokko(cx, cy, hx, hy, n=96, p=2.3, lobe=0.05):
    """A four-lobed rounded square (the mokko of a Japanese guard): a squircle whose sides dip a little between its corners."""
    out = []
    for i in range(n):
        a = TAU * i / n
        c, s_ = math.cos(a), math.sin(a)
        r = 1.0 - lobe * math.cos(4 * a)
        out.append((cx + hx * r * math.copysign(abs(c) ** (2 / p), c), cy + hy * r * math.copysign(abs(s_) ** (2 / p), s_)))
    return out


def squircle(cx, cy, hx, hy, n=64, p=2.6):
    return [(cx + hx * math.copysign(abs(math.cos(TAU * i / n)) ** (2 / p), math.cos(TAU * i / n)),
             cy + hy * math.copysign(abs(math.sin(TAU * i / n)) ** (2 / p), math.sin(TAU * i / n))) for i in range(n)]


def obj_from(hi, name, coll, mat):
    return hi.object(name, coll, mat if isinstance(mat, (list, tuple)) else [mat], smooth=True)


# ---------- extruded outlines (the guard plate and its cutters) ----------
def prism_z(hi, outline, z0, z1, mat=0):
    """A flat plate in the XY plane, from z0 to z1, outline [(x, y)] simple; faces turned outward."""
    n = len(outline)
    front = [hi.v(V((x, y, z1))) for x, y in outline]     # z1 is the toward-the-point face when z1 < z0
    back = [hi.v(V((x, y, z0))) for x, y in outline]
    tris = SK.ear_clip(outline)
    zmax = max(z0, z1)
    for a, b, c in tris:
        for ids, zz in (([front[a], front[b], front[c]], z1), ([back[a], back[b], back[c]], z0)):
            hi.facing(ids, [(outline[i][0], outline[i][1]) for i in (a, b, c)], (0, 0, 1 if zz == zmax else -1), mat)
    ccw = SK._area2(outline) > 0
    run = 0.0
    for i in range(n):
        j = (i + 1) % n
        dx, dy = outline[j][0] - outline[i][0], outline[j][1] - outline[i][1]
        ln = math.hypot(dx, dy)
        nx, ny = (dy, -dx) if ccw else (-dy, dx)
        hi.facing([front[i], front[j], back[j], back[i]], [(run, 1), (run + ln, 1), (run + ln, 0), (run, 0)], (nx, ny, 0), mat)
        run += ln


def boolean(obj, cutters, op="DIFFERENCE"):
    for c in cutters:
        Hm.apply_modifiers(obj, [("BOOLEAN", {"operation": op, "object": c, "solver": "EXACT"})])
        me = c.data
        bpy.data.objects.remove(c, do_unlink=True)
        bpy.data.meshes.remove(me)
    return obj


def cutter(coll, outline, z0, z1):
    h = Hm.Hi()
    prism_z(h, outline, z0, z1)
    return h.object("cutter", coll, [], smooth=False, weld=0)


def stroke_outline(pts, widths, n_cap=6):
    """A closed outline round a polyline [(x, y)] with a width at each point, ends rounded (a slit's cutter)."""
    p = np.array(pts, float)
    w = np.array(widths, float)
    t = np.gradient(p, axis=0)
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
    nrm = np.stack([-t[:, 1], t[:, 0]], 1)
    left = p + nrm * (w[:, None] / 2)
    right = p - nrm * (w[:, None] / 2)
    out = [tuple(q) for q in left]
    r = w[-1] / 2
    a0 = math.atan2(nrm[-1][1], nrm[-1][0])
    for k in range(1, n_cap):
        a = a0 - math.pi * k / n_cap
        out.append((p[-1][0] + r * math.cos(a), p[-1][1] + r * math.sin(a)))
    out += [tuple(q) for q in right[::-1]]
    r = w[0] / 2
    a0 = math.atan2(-nrm[0][1], -nrm[0][0])
    for k in range(1, n_cap):
        a = a0 - math.pi * k / n_cap
        out.append((p[0][0] + r * math.cos(a), p[0][1] + r * math.sin(a)))
    return out


# ---------- the loop tube (links) ----------
def loop_tube(hi, pts, normal, rin, rout, sides=10, mat=0, facets=False):
    """A tube round a closed planar loop: `rin` across the loop's plane, `rout` out of it (round when equal). pts: loop points (Roblox space)."""
    P = [V(p) for p in pts]
    n = len(P)
    nrm = V(normal).normalized()
    c = sum(P, V((0, 0, 0))) / n
    rings = []
    for i, p in enumerate(P):
        t = (P[(i + 1) % n] - P[i - 1]).normalized()
        radial = nrm.cross(t).normalized()
        ring = []
        for j in range(sides):
            a = TAU * j / sides + (math.pi / sides if facets else 0.0)
            ring.append(hi.v(p + radial * (rin * math.cos(a)) + nrm * (rout * math.sin(a))))
        rings.append(ring)
    for i in range(n):
        i2 = (i + 1) % n
        for j in range(sides):
            j2 = (j + 1) % sides
            quad = [rings[i][j], rings[i][j2], rings[i2][j2], rings[i2][j]]
            mid = sum((V(hi.verts[q]) for q in quad), V((0, 0, 0))) / 4
            pc = P[i]
            a = TAU * (j + 0.5) / sides
            radial = nrm.cross((P[(i + 1) % n] - P[i - 1]).normalized()).normalized()
            out = radial * math.cos(a) + nrm * math.sin(a)
            hi.facing(quad, [(i / n * 4, j / sides), (i / n * 4, (j + 1) / sides), ((i + 1) / n * 4, (j + 1) / sides), ((i + 1) / n * 4, j / sides)], tuple(out), mat)


def stadium(c, along, across, length, width, n=16):
    """A stadium (a rectangle with round ends) as a closed loop of points: centre c, `along` its long axis, `across` the other, overall
    `length` x `width`."""
    a, b = V(along).normalized(), V(across).normalized()
    r = width / 2
    straight = (length - width) / 2
    pts = []
    for i in range(n + 1):             # the far cap
        t = math.pi * i / n
        pts.append(V(c) + a * (straight + r * math.sin(t)) + b * (r * -math.cos(t)))
    for i in range(n + 1):             # the near cap
        t = math.pi * i / n
        pts.append(V(c) + a * (-straight - r * math.sin(t)) + b * (r * math.cos(t)))
    # remove the duplicated joins
    out = []
    for p in pts:
        if not out or (p - out[-1]).length > 1e-6:
            out.append(p)
    if (out[0] - out[-1]).length < 1e-6:
        out.pop()
    return out


# ---------- the parts, high detail ----------
def slit_outlines(pts_per=14, cap=6):
    """The three slots through the guard plate: parallel, long, slanted like drawn wind lines (a rising slant toward the arm's side), each a
    stadium of one width (tapered slits read as eyes). Laid out so no three of them can be taken for a face."""
    out = []
    th = math.radians(22)
    d = (-math.cos(th), math.sin(th))
    nrm = (-d[1], d[0])
    for k, ln in enumerate((0.28, 0.42, 0.26)):
        off = (k - 1) * 0.185
        cx, cy = -0.395 + nrm[0] * off - d[0] * (k - 1) * 0.07, 0.0 + nrm[1] * off - d[1] * (k - 1) * 0.07
        pts = []
        for s_ in np.linspace(-0.5, 0.5, pts_per):
            bulge = 0.03 * math.cos(math.pi * s_)
            pts.append((cx + d[0] * ln * s_ + nrm[0] * bulge, cy + d[1] * ln * s_ + nrm[1] * bulge))
        out.append(stroke_outline(pts, [0.05] * pts_per, cap))
    return out


def guard_plate(coll, mat):
    """The guard plate: a raised face inside a flat rim (the mimi of a tsuba), offset toward the edge side (-X), pierced by three
    long slits that follow the blade's own sweep; the raised face is cut round by a small chamfer."""
    hi = Hm.Hi()
    rim = mokko(-0.20, 0.0, 0.50, 0.465, 96, 2.15, 0.05)
    prism_z(hi, rim, PLATE_Z + PLATE_HALF, PLATE_Z - PLATE_HALF)
    o = obj_from(hi, "UG_Plate", coll, mat)
    face = mokko(-0.205, 0.0, 0.425, 0.390, 96, 2.15, 0.05)
    h2 = Hm.Hi()
    prism_z(h2, face, PLATE_Z + PLATE_HALF + 0.03, PLATE_Z - PLATE_HALF - 0.03)
    o2 = obj_from(h2, "UG_Face", coll, mat)
    cuts = [cutter(coll, ol, PLATE_Z + 0.2, PLATE_Z - 0.2) for ol in slit_outlines(14, 6)]
    boolean(o, [o2], "UNION")
    boolean(o, cuts)
    Hm.apply_modifiers(o, [("BEVEL", {"width": 0.012, "segments": 3, "limit_method": "ANGLE", "angle_limit": math.radians(40), "affect": "EDGES"})])
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def _join(objs, name, coll):
    bm = bmesh.new()
    mats = []
    for o in objs:
        me = o.data.copy()
        me.transform(o.matrix_world)
        off = len(mats)
        mats.extend(me.materials)
        for p in me.polygons:
            p.material_index += off
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats[:1]:
        me.materials.append(m)
    out = bpy.data.objects.new(name, me)
    coll.objects.link(out)
    for o in objs:
        m = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.meshes.remove(m)
    out.name = name
    return out


ARM_PATHS = {
    "prong": [(-0.48, 0, -0.92), (-0.92, 0, -0.94), (-1.13, 0, -1.18), (-1.17, 0, -1.62), (-1.09, 0, -2.08), (-0.93, 0, -2.40)],
    "hook": [(-0.48, 0, -0.92), (-0.88, 0, -0.93), (-1.10, 0, -1.15), (-1.15, 0, -1.50), (-1.02, 0, -1.84), (-0.82, 0, -1.98), (-0.68, 0, -1.96)],
    "sweep": [(-0.48, 0, -0.92), (-0.90, 0, -0.94), (-1.12, 0, -1.16), (-1.17, 0, -1.58), (-1.07, 0, -1.98), (-0.89, 0, -2.22)],
}
ARM = os.environ.get("UG_ARM", "sweep")
ARM_PATH = ARM_PATHS[ARM]


def arm_path(per=10):
    return [V(p) for p in W.catmull(ARM_PATH, per)]


def arm_scale(t):
    """Plan width and height of the arm along it (full sizes, halved by the sweep): a stout root, a long taper to a pointed end."""
    w, h = 0.31 - 0.17 * t ** 1.05, 0.40 - 0.22 * t ** 1.05
    if t > 0.93:
        k = max(0.10, 1.0 - ((t - 0.93) / 0.07) ** 1.5)
        w, h = w * k, h * k
    return (w / 2, h / 2)


def guard_arm(coll, mat):
    """The one-sided arm: leaves the plate's edge, sweeps out and forward and turns back toward the blade; a faceted hexagonal section,
    stout at the root and tapering to a point, with a linen lashing at its root and two thin brass bands (see arm_sleeves)."""
    hi = Hm.Hi()
    path = arm_path(10)
    SK.sweep(hi, path, SK.hex_profile(0.5), arm_scale, mat=0, up=(0, 1, 0), uv_scale=2.0)
    o = obj_from(hi, "UG_Arm", coll, mat)
    SK.bevel(o, 0.010, 2, 28)
    return o


def arm_sleeves(coll, mat):
    """Two thin brass bands on the arm (a forged bar fitted in stages, not one casting)."""
    full = arm_path(40)
    n = len(full)
    hi = Hm.Hi()
    for t0, t1, grow in ((0.43, 0.455, 0.13), (0.70, 0.72, 0.13)):
        sub = full[int(t0 * (n - 1)):int(t1 * (n - 1)) + 1]
        SK.sweep(hi, sub, SK.hex_profile(0.5), lambda f, t0=t0, t1=t1, grow=grow: tuple(v * (1 + grow) for v in arm_scale(t0 + (t1 - t0) * f)),
                 mat=0, up=(0, 1, 0), uv_scale=2.0)
    o = obj_from(hi, "UG_ArmBrass", coll, mat)
    SK.bevel(o, 0.005, 2, 35)
    return o


def arm_lashing(coll, mat):
    """Five turns of linen cord round the arm's root (the arm runs along -X there), a tuck at each end."""
    hi = Hm.Hi()
    x0, x1 = -0.68, -0.90
    turns = 4
    n = turns * 22
    pts = []
    for i in range(n + 1):
        f = i / n
        x = x0 + (x1 - x0) * f
        a = TAU * turns * f
        pts.append(V((x, 0.235 * math.cos(a), -0.93 + 0.185 * math.sin(a))))
    SK.strand(hi, pts, 0.040, turns=turns * 1.6, strands=2, sides=5, per=1, mat=0, uv_scale=6.0)
    WK.blob(hi, V((x1 - 0.02, 0.24, -0.93)), V((x1 + 0.05, 0.24, -0.93)), 0.036, sides=8, per=4)
    return obj_from(hi, "UG_ArmCord", coll, mat)


def plate_wire(coll, mat):
    """Copper wire let into the plate's flat rim, front and back (the rim between the raised face and the edge), following the mokko outline."""
    hi = Hm.Hi()
    for z in (PLATE_Z + PLATE_HALF + 0.003, PLATE_Z - PLATE_HALF - 0.003):
        ring_pts = [V((x, y, z)) for x, y in mokko(-0.202, 0.0, 0.463, 0.428, 120, 2.15, 0.05)]
        loop_tube(hi, ring_pts, (0, 0, 1), 0.0115, 0.0115, sides=6, mat=0)
    return obj_from(hi, "UG_PlateWire", coll, mat)


def arm_inlay(coll, mat):
    """A copper line let into the top ridge of the arm, from just outside the plate to near the point: it follows the arm's whole curve."""
    hi = Hm.Hi()
    full = arm_path(40)
    n = len(full)
    pts = []
    for i in range(int(0.07 * (n - 1)), int(0.90 * (n - 1))):
        t = i / (n - 1)
        pts.append(full[i] + V((0, arm_scale(t)[1] + 0.003, 0)))
    Hm.htube(hi, pts, lambda t: 0.0135 * (1 - 0.55 * t), sides=6, per=1, mat=0, uv_scale=3.0, tip=True, wobble=0.0)
    return obj_from(hi, "UG_ArmInlay", coll, mat)


def bands_low(coll):
    """The two brass bands of the arm, built directly (a sweep's UVs are a strip, not a ring-shaped island)."""
    full = arm_path(40)
    n = len(full)
    hi = Hm.Hi()
    for t0, t1, grow in ((0.43, 0.455, 0.13), (0.70, 0.72, 0.13)):
        sub = full[int(t0 * (n - 1)):int(t1 * (n - 1)) + 1]
        SK.sweep(hi, sub, SK.hex_profile(0.5), lambda f, t0=t0, t1=t1, grow=grow: tuple(v * (1 + grow) for v in arm_scale(t0 + (t1 - t0) * f)),
                 mat=0, up=(0, 1, 0), uv_scale=1.0)
    o = hi.object("UL_Bands", coll, [], smooth=False, weld=1e-6)
    o["uv_keep"] = True
    return o


def drop_end_faces(obj, zs, tol=0.012):
    """Deletes the flat faces at the given z (Roblox axes, the weapon's own frame): the ends of a collar or cap that lie inside the part beside it."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    dead = [f for f in bm.faces if any(all(abs(-v.co.y - z) < tol for v in f.verts) for z in zs)]
    bmesh.ops.delete(bm, geom=dead, context="FACES")
    bm.to_mesh(obj.data)
    bm.free()
    return obj


def lashing_low(coll, name):
    """The game mesh's version of a cord lashing round the arm's root: a short ridged sleeve (the cord's twist is in the normal map)."""
    hi = Hm.Hi()
    x0, x1 = -0.68, -0.90
    path = [V((x0 + (x1 - x0) * i / 11, 0.0, -0.93)) for i in range(12)]
    SK.sweep(hi, path, SK.lens_profile(5), lambda f: (0.185 * (1.0 + 0.07 * math.cos(TAU * 4 * f)), 0.235 * (1.0 + 0.07 * math.cos(TAU * 4 * f))),
             mat=0, up=(0, 1, 0), uv_scale=1.0)
    o = hi.object(name, coll, [], smooth=True, weld=1e-6)
    o["uv_keep"] = True
    return o


def seppa(coll, mat):
    hi = Hm.Hi()
    for z in (-0.802, ):
        prism_z(hi, squircle(0.0, 0.0, 0.215, 0.235, 48, 2.2), z + 0.012, z - 0.012)
    o = obj_from(hi, "UG_Seppa", coll, mat)
    SK.bevel(o, 0.006, 2, 40)
    return o


def habaki(b, coll, mat):
    """The blade collar: a stepped teardrop in copper round the blade's foot, in front of the plate."""
    import sword_unorthodox_blade as BL
    hi = Hm.Hi()
    zs = np.linspace(-1.0, -1.31, 20)
    rings = []
    for z in zs:
        t = max(0.0, (z - (-1.025)) / (-1.31 - (-1.025)))
        u = float(np.interp(z, b.z[::-1], b.u[::-1]))
        we, ws, h = b.at(b.we, u), b.at(b.ws, u), b.at(b.h, u)
        m = 0.058 * (1 - t ** 2.2) ** 0.8 + 0.012 + 0.014 * math.sin(t * 9) * (1 - t)
        cx = b.at(b.x, u)
        a_c = (we - ws) / 2
        ring = []
        for (px, py) in SK.lens_profile(12, flat=0.55):
            a = a_c + (px * ((we + ws) / 2 + m))
            y = py * (h * 1.15 + m)
            ring.append(V((cx + b.at(b.nx, u) * a, y, z)))
        rings.append((V((cx + b.at(b.nx, u) * a_c, 0, z)), ring))
    WK.loft(hi, rings, mat=0, cap_start=True, cap_end=True, uv_scale=2.0)
    o = obj_from(hi, "UG_Habaki", coll, mat)
    SK.bevel(o, 0.006, 2, 35)
    return o


def grip_core(coll, mat):
    hi = Hm.Hi()
    poly = [(0.0, GRIP0)]
    zs = np.linspace(GRIP0, GRIP1, 22)
    for z in zs:
        t = (z - GRIP0) / (GRIP1 - GRIP0)
        poly.append((GRIP_R * (1 + 0.10 * math.sin(math.pi * t) ** 1.2), float(z)))
    poly.append((0.0, GRIP1))
    SK.revolve(hi, poly, n=24, mat=0, uv_scale=1.5)
    return obj_from(hi, "UG_Core", coll, mat)


def grip_cord(coll, mat):
    """Three lashings of two-ply linen cord, each a tight single helix (turn touching turn), with a tuck at its rear end."""
    hi = Hm.Hi()
    for k, (z0, z1) in enumerate(BANDS):
        turns = round((z1 - z0) / 0.066)
        pts = []
        n = turns * 20
        for i in range(n + 1):
            f = i / n
            z = z0 + (z1 - z0) * f
            r = GRIP_R * (1 + 0.10 * math.sin(math.pi * (z - GRIP0) / (GRIP1 - GRIP0)) ** 1.2) + 0.026
            a = TAU * turns * f * (1 if k != 1 else -1)
            pts.append(V((r * math.cos(a), r * math.sin(a), z)))
        SK.strand(hi, pts, 0.050, turns=turns * 1.6, strands=2, sides=5, per=1, mat=0, uv_scale=6.0)
        zk = z1 + 0.02
        r = GRIP_R * (1 + 0.10 * math.sin(math.pi * (zk - GRIP0) / (GRIP1 - GRIP0)) ** 1.2) + 0.03
        WK.blob(hi, V((0.0, r, zk - 0.035)), V((0.0, r, zk + 0.035)), 0.05, sides=8, per=4)
    return obj_from(hi, "UG_Cord", coll, mat)


def grip_stitches(coll, mat):
    """A row of cord stitches along the leather where it shows between the lashings (the grip's underside)."""
    hi = Hm.Hi()
    gaps = [(BANDS[0][1] + 0.02, BANDS[1][0] - 0.02), (BANDS[1][1] + 0.02, BANDS[2][0] - 0.02)]
    for z0, z1 in gaps:
        n = 7
        for i in range(n):
            z = z0 + (z1 - z0) * (i + 0.5) / n
            r = GRIP_R * (1 + 0.10 * math.sin(math.pi * (z - GRIP0) / (GRIP1 - GRIP0)) ** 1.2)
            for ang in (-math.pi / 2 - 0.5, -math.pi / 2 + 0.5):
                c = V((r * math.cos(ang), r * math.sin(ang), z))
                d = V((math.cos(ang), math.sin(ang), 0.0))
                Hm.htube(hi, [c - V((0, 0, 0.016)) + d * 0.0, c + d * 0.012, c + V((0, 0, 0.016))], lambda t: 0.007, sides=4, per=1, mat=0, uv_scale=2.0, tip=True, wobble=0.0)
    return obj_from(hi, "UG_Stitch", coll, mat)


def fuchi(coll, mat):
    """The collar at the guard end of the grip: aged brass, two raised bands, chamfered; revolve of a profile."""
    hi = Hm.Hi()
    poly = [(0.128, -0.835), (0.152, -0.835), (0.158, -0.82), (0.158, -0.745), (0.146, -0.735), (0.146, -0.72), (0.158, -0.71), (0.158, -0.645), (0.150, -0.63), (0.128, -0.63)]
    SK.revolve(hi, poly, n=28, mat=0, uv_scale=2.0)
    o = obj_from(hi, "UG_Fuchi", coll, mat)
    SK.bevel(o, 0.004, 2, 40)
    return o


RING = dict(near=1.0, length=0.56, width=0.48, tube=0.096)


def kashira(coll, mat):
    """The cap on the grip's end: a domed brass cup with a lip."""
    hi = Hm.Hi()
    prof = [(0.128, 0.60), (0.178, 0.60), (0.182, 0.616), (0.172, 0.645), (0.158, 0.70), (0.150, 0.78), (0.136, 0.86), (0.108, 0.918), (0.07, 0.95), (0.0, 0.962)]
    SK.revolve(hi, [(0.0, 0.60)] + prof, n=28, mat=0, uv_scale=2.0)
    o = obj_from(hi, "UG_Kashira", coll, mat)
    SK.bevel(o, 0.004, 2, 40)
    return o


def eye_lug(coll, mat):
    """The eye the pommel ring passes through: a small ring in the YZ plane at the cap's end."""
    hi = Hm.Hi()
    SK.torus(hi, V((0, 0, 1.0)), (1, 0, 0), 0.165, 0.046, n=26, sides=8)
    o = obj_from(hi, "UG_Eye", coll, mat)
    SK.bevel(o, 0.004, 2, 40)
    return o


def ring_pommel(coll, mat):
    """The heavy ring: a cast bronze ring, an oval in the XZ plane with a rounded-hexagon section, its near side through the cap's eye."""
    hi = Hm.Hi()
    near, ln, wd, tube = RING["near"], RING["length"], RING["width"], RING["tube"]
    pts = []
    n = 40
    for i in range(n):
        a = TAU * i / n
        c, sn = math.cos(a), math.sin(a)
        pts.append(V((wd / 2 * math.copysign(abs(c) ** 0.85, c), 0.0, near + ln / 2 + ln / 2 * math.copysign(abs(sn) ** 0.85, sn))))
    loop_tube(hi, pts, (0, 1, 0), tube, tube * 0.9, sides=6, mat=0, facets=True)
    o = obj_from(hi, "UG_Ring", coll, mat)
    SK.bevel(o, 0.008, 2, 35)
    return o


def pendant(coll, mat_cord, mat_bone):
    """A doubled linen cord looped through the ring's far side with a knot, ending in a bone toggle."""
    hi = Hm.Hi()
    far = RING["near"] + RING["length"]
    top = V((0.0, -0.02, far + 0.0))
    for dx in (-0.018, 0.018):
        path = [V((dx, 0.02, far - 0.02)), V((dx * 1.4, -0.10, far + 0.06)), V((dx * 1.3, -0.30, far + 0.075)), V((dx * 0.8, -0.60, far + 0.08))]
        SK.strand(hi, path, 0.034, turns=3, strands=2, sides=5, per=6, mat=0, uv_scale=6.0)
    WK.blob(hi, V((0.0, -0.22, far + 0.07)), V((0.0, -0.31, far + 0.07)), 0.052, sides=10, per=5)
    cord = obj_from(hi, "UG_PendantCord", coll, mat_cord)
    hb = Hm.Hi()
    path = [V((0.0, -0.46, far + 0.08)), V((0.0, -0.58, far + 0.08)), V((0.0, -0.74, far + 0.08))]
    Hm.htube(hb, path, lambda t: 0.062 * math.sin(math.pi * (0.1 + 0.8 * t)) ** 0.5 + 0.012, sides=14, per=6, mat=0, uv_scale=3.0, tip=False, wobble=0.0)
    bone = obj_from(hb, "UG_PendantBone", coll, mat_bone)
    return cord, bone


# ---------- the game mesh's own versions (built directly, with the UVs a flat strip needs) ----------
def low_plate(coll):
    """The game mesh's guard plate: the mokko outline as a flat slab (the raised face and the rim's step are in the normal map) with the
    three slits cut right through. Clean planar faces, so its UV islands are two big faces and a rim strip."""
    hi = Hm.Hi()
    t = PLATE_HALF + 0.015
    prism_z(hi, mokko(-0.2, 0.0, 0.50, 0.465, 56, 2.15, 0.05), PLATE_Z + t, PLATE_Z - t)
    o = hi.object("UL_Plate", coll, [], smooth=False, weld=1e-6)
    cuts = [cutter(coll, ol, PLATE_Z + 0.2, PLATE_Z - 0.2) for ol in slit_outlines(7, 3)]
    boolean(o, cuts)
    Hm.apply_modifiers(o, [("TRIANGULATE", {"min_vertices": 4})])
    bm = bmesh.new()
    bm.from_mesh(o.data)
    for e in bm.edges:
        if e.is_manifold and e.calc_face_angle(0.0) > math.radians(30):
            e.smooth = False
    bm.to_mesh(o.data)
    bm.free()
    for p_ in o.data.polygons:
        p_.use_smooth = True
    return o


def low_ring(coll, sides=6, segs=24):
    """The game mesh's pommel ring, a closed tube with its UV laid out as one strip (u along the ring, v round the tube): flattened it is a
    rectangle, not a ring-shaped island."""
    near, ln, wd, tube = RING["near"], RING["length"], RING["width"], RING["tube"]
    pts = []
    for i in range(segs):
        a = TAU * i / segs
        c, sn = math.cos(a), math.sin(a)
        pts.append(V((wd / 2 * math.copysign(abs(c) ** 0.85, c), 0.0, near + ln / 2 + ln / 2 * math.copysign(abs(sn) ** 0.85, sn))))
    nrm = V((0, 1, 0))
    rings = []
    verts, faces, uvs = [], [], []
    lens = [0.0]
    for i in range(1, segs + 1):
        lens.append(lens[-1] + (pts[i % segs] - pts[i - 1]).length)
    total = lens[-1]
    for i, p in enumerate(pts):
        t = (pts[(i + 1) % segs] - pts[i - 1]).normalized()
        radial = nrm.cross(t).normalized()
        ring = []
        for j in range(sides):
            a = TAU * j / sides + math.pi / sides
            q = p + radial * (tube * math.cos(a)) + nrm * (tube * 0.9 * math.sin(a))
            ring.append(len(verts))
            verts.append(tuple(W.rb(q.x, q.y, q.z)))
        rings.append(ring)
    su, sv = 1.0 / total * 0.5, 1.0 / (sides * tube * 1.4) * 0.12      # a strip in 0..1 (its scale is set by the packer)
    for i in range(segs):
        i2 = (i + 1) % segs
        for j in range(sides):
            j2 = (j + 1) % sides
            faces.append([rings[i][j], rings[i][j2], rings[i2][j2], rings[i2][j]])
            uvs.append([(lens[i] * su, j / sides * 0.3), (lens[i] * su, (j + 1) / sides * 0.3), (lens[i + 1] * su, (j + 1) / sides * 0.3), (lens[i + 1] * su, j / sides * 0.3)])
    me = bpy.data.meshes.new("UL_Ring")
    me.from_pydata(verts, [], faces)
    me.validate()
    layer = me.uv_layers.new(name="UVMap")
    for poly, uv in zip(me.polygons, uvs):
        for li, c in zip(poly.loop_indices, uv):
            layer.data[li].uv = c
    # wind every face outward (against the ring's centre line)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    for p_ in me.polygons:
        p_.use_smooth = True
    o = bpy.data.objects.new("UL_Ring", me)
    coll.objects.link(o)
    o["uv_keep"] = True
    return o


def low_eye(coll):
    """The game mesh's eye lug: a small closed tube, its UV a strip (a torus unwrapped by itself comes out as a ring-shaped island)."""
    hi = Hm.Hi()
    SK.torus(hi, V((0, 0, 1.0)), (1, 0, 0), 0.165, 0.046, n=14, sides=6, uv_scale=1.0)
    o = hi.object("UL_Eye", coll, [], smooth=True, weld=1e-6)
    o["uv_keep"] = True
    return o


def cylinder_uv(obj, axis_x=0.0, k=1.0):
    """Cylindrical UVs round the weapon's z axis for a collar, cap or grip (a closed tube unwrapped by itself comes out as a ring-shaped
    island): u = the angle round the axis times the mean radius, v = z + k * radius (so a flat ring face still has an extent). A face that
    crosses the cut is moved to one side, so it is never stretched across the sheet. The object is marked to keep these UVs."""
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    layer = me.uv_layers.active
    rs = [math.hypot(v.co.x - axis_x, v.co.z) for v in me.vertices]
    rmean = max(0.05, sum(rs) / max(1, len(rs)))
    for poly in me.polygons:
        angs = [math.atan2(me.vertices[vi].co.z, me.vertices[vi].co.x - axis_x) for vi in poly.vertices]
        ref = math.atan2(sum(math.sin(a) for a in angs), sum(math.cos(a) for a in angs))
        for li, vi, a in zip(poly.loop_indices, poly.vertices, angs):
            co = me.vertices[vi].co
            d = (a - ref + math.pi) % (2 * math.pi) - math.pi
            layer.data[li].uv = ((ref + d) * rmean, -co.y + k * math.hypot(co.x - axis_x, co.z))
    obj["uv_keep"] = True
    return obj
