"""The Cinder Roc's feathers and armour: builders for the parts that are not the soft body (run inside Blender).

Everything is authored in Roblox studs (the bird faces -Z, its right wing is +X) through egg_hi.Hi. A feather is a closed lens of a blade
(`blade`): a ridge down its centre (the rachis), a narrow leading vane and a broad trailing vane, a sharp edge all round, thick enough
that Roblox, which culls back faces, shows it from both sides. UVs: u across (0 leading edge to 1 trailing edge), v along (0 root,
1 tip), so the shaders can burn the root and the edges ember-orange. Wing pieces are built for the right side and mirrored.
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import egg_hi as Hm
import egg_kit as K
from cinder_roc_bones import BONES, PRIM_ANGLES, PRIM_LENGTHS, PRIM_ROOTS, SEC_LENGTHS, SEC_ROOTS, _trail, _unit, wing_frame

W = K.W
V = Vector
TAU = 2 * math.pi


def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


# ---------------------------------------------------------------- the feather
def vane(root=0.14, tip=0.3, round_=1.0):
    """Half width along a feather, 0..1: it widens quickly, holds, and ends in a rounded point; `round_` 1 is blunt, 0.4 a blade's point."""
    def fn(s):
        up = smoothstep(0.0, root, s) ** 0.7
        if s <= 1 - tip:
            return up
        u = (s - (1 - tip)) / tip
        return up * max(0.0, 1 - u ** (1.5 + 1.2 * round_)) ** 0.55
    return fn


def curve_points(pts, count):
    """`count` points evenly spread by arc length along the smooth curve through pts."""
    dense = [V(p) for p in W.catmull([tuple(p) for p in pts], 12)]
    at = [0.0]
    for a, b in zip(dense, dense[1:]):
        at.append(at[-1] + (b - a).length)
    out, j = [], 0
    for i in range(count):
        s = at[-1] * i / (count - 1)
        while j < len(dense) - 2 and at[j + 1] < s:
            j += 1
        span = at[j + 1] - at[j]
        out.append(dense[j].lerp(dense[j + 1], 0 if span <= 0 else (s - at[j]) / span))
    return out


def blade(hi, pts, up, side, width, shape=None, lead=0.42, th=0.11, steps=8, across=5, mat=0, cup=0.0, ridge=1.0, twist=0.0, solid=True):
    """One feather along the smooth curve through pts. `up`: where its face looks; `side`: which way its broad (trailing) vane lies;
    `width`: the trailing vane's greatest half width; `lead`: the leading vane's share of it; `th`: half the thickness at the ridge.
    Returns the rachis (the list of centre points)."""
    shape = shape or vane()
    centre = curve_points(pts, steps + 1)
    n_across = across
    rows = []
    for i, c in enumerate(centre):
        s = i / steps
        tan = (centre[min(i + 1, steps)] - centre[max(i - 1, 0)]).normalized()
        turn = Matrix.Rotation(twist * s, 3, tan)
        sv, uv_ = turn @ V(side), turn @ V(up)
        sd = sv - tan * sv.dot(tan)
        sd = sd.normalized() if sd.length > 1e-4 else tan.cross(uv_).normalized()
        face = tan.cross(sd)
        if face.dot(uv_) < 0:
            face = -face
        w = width * shape(s)
        wl = w * lead
        offs = [(-wl, 0.0), (-wl * 0.5, 0.35), (0.0, ridge), (w * 0.5, 0.45), (w, 0.0)] if n_across == 5 else [(-wl, 0.0), (0.0, ridge), (w, 0.0)]
        top, bot = [], []
        for k, (o, h) in enumerate(offs):
            edge = k in (0, len(offs) - 1)
            lift = cup * w * (abs(o) / max(w, 1e-4)) ** 2
            top.append(hi.v(c + sd * o + face * (th * h + lift)))
            bot.append(None if not solid else top[-1] if edge else hi.v(c + sd * o - face * (th * h * 0.6) + face * lift))
        rows.append((top, bot, s, face))
    n = len(rows[0][0])
    for (t0, b0, s0, f0), (t1, b1, s1, f1) in zip(rows, rows[1:]):
        for k in range(n - 1):
            uv = [(k / (n - 1), s0), ((k + 1) / (n - 1), s0), ((k + 1) / (n - 1), s1), (k / (n - 1), s1)]
            hi.facing([t0[k], t0[k + 1], t1[k + 1], t1[k]], uv, tuple(f0), mat)
            if solid:
                hi.facing([b0[k], b1[k], b1[k + 1], b0[k + 1]], [uv[0], uv[3], uv[2], uv[1]], tuple(-f0), mat)
    return centre


def mirror(obj, name=None):
    """A copy of obj turned across the middle (x to -x), its faces wound back outward."""
    me = obj.data.copy()
    bm = bmesh.new()
    bm.from_mesh(me)
    for v in bm.verts:
        v.co.x = -v.co.x
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    out = bpy.data.objects.new(name or obj.name + "_L", me)
    for coll in obj.users_collection:
        coll.objects.link(out)
    for k in obj.keys():
        out[k] = obj[k]
    return out


# ---------------------------------------------------------------- the wing (right side)
def _radius(rad):
    def fn(t):
        x = min(t, 0.999) * (len(rad) - 1)
        i = int(x)
        return lerp(rad[i], rad[i + 1], x - i)
    return fn


def wing_points():
    return wing_frame(1)


def build_wing(M, coll, seed=1):
    """The right wing as high-detail objects: {name: object}. M: the materials."""
    rnd = random.Random(seed)
    cl, sh, el, wr, tip = wing_points()
    hd = _unit(tip - wr)
    fd = _unit(wr - el)
    ud = _unit(el - sh)
    t_h, t_f, t_u = _trail(hd), _trail(fd), _trail(ud)
    up = V((0, 1, 0))
    flight, covert, arm, plates, magma, claws = (Hm.Hi() for _ in range(6))

    # the arm: a real one under the feathers, thick at the shoulder and slim at the wrist
    pts = [sh + V((-0.4, 0, 0.2)), sh.lerp(el, 0.5) + V((0, 0.15, 0)), el, wr.lerp(el, 0.4), wr, wr.lerp(tip, 0.5), tip + hd * 0.4]
    rad = [1.7, 1.55, 1.3, 1.0, 0.85, 0.62, 0.3]
    Hm.htube(arm, pts, _radius(rad), sides=9, per=5, uv_scale=1.0, tip=True, wobble=0.0)

    # primaries: ten blades fanned from the hand toward the trailing edge, scimitars that curve up and back
    prim_roots = []
    for k in range(10):
        a = math.radians(8 + 8.0 * k)
        d = (hd * math.cos(a) + t_h * math.sin(a)).normalized()
        root = wr + hd * lerp(4.3, 0.1, k / 9)
        length = (7.4, 9.2, 9.8, 9.6, 9.4, 9.0, 8.6, 8.2, 7.8, 7.2)[k]
        mid = root + d * length * 0.5 + up * 0.10 * length * 0.25 + t_h * 0.04 * length * 0.25
        end = root + d * length + up * 0.07 * length + t_h * 0.07 * length - hd * 0.0
        blade(flight, [root, mid, end], up, t_h, 0.66 - 0.05 * (k / 9), vane(0.10, 0.34, 0.5), lead=0.38, th=0.13, steps=9, mat=0)
        prim_roots.append((root, d, length))
    # secondaries: twelve broad blades along the forearm, their blunt tips drawing the trailing edge
    for k in range(12):
        q = lerp(0.97, 0.06, k / 11)
        root = el.lerp(wr, q)
        d = (t_f * math.cos(math.radians(8 + 6 * (1 - q))) - fd * math.sin(math.radians(8 + 6 * (1 - q)))).normalized()
        length = 6.4 + 1.2 * math.sin(math.pi * (0.12 + 0.76 * (1 - q)))
        mid = root + d * length * 0.5 + up * 0.5
        end = root + d * length + up * 0.45 * (0.6 + (1 - q) * 0.6)
        blade(flight, [root + up * 0.05, mid, end], up, t_f, 0.92, vane(0.16, 0.26, 1.0), lead=0.5, th=0.13, steps=8, mat=0)
    # tertials: four short broad blades from the upper arm that close the trailing edge against the body
    for k in range(4):
        q = lerp(0.9, 0.18, k / 3)
        root = sh.lerp(el, q) + up * 0.1
        d = (t_u + ud * 0.05).normalized()
        length = 5.4 - 0.5 * k
        blade(flight, [root, root + d * length * 0.5 + up * 0.3, root + d * length + up * 0.5], up, t_u, 1.0, vane(0.16, 0.3, 1.0), lead=0.5, th=0.12, steps=7, mat=0)
    # coverts: rows of small blades on the face of the wing, hiding the roots of the flight feathers
    for k in range(10):
        root, d, length = prim_roots[k]
        base = root + d * length * 0.10 + up * 0.28
        blade(covert, [base, base + d * length * 0.20 + up * 0.06, base + d * length * 0.40 + up * 0.10], up, t_h, 0.60, vane(0.2, 0.4, 0.6), lead=0.4, th=0.10, steps=4, across=3, mat=0)
    for k in range(12):
        q = lerp(0.97, 0.06, k / 11)
        root = el.lerp(wr, q)
        d = (t_f * math.cos(math.radians(8 + 6 * (1 - q))) - fd * math.sin(math.radians(8 + 6 * (1 - q)))).normalized()
        base = root + d * 0.8 + up * 0.5
        blade(covert, [base, base + d * 1.6 + up * 0.1, base + d * 3.0 + up * 0.18], up, t_f, 0.82, vane(0.2, 0.35, 1.0), lead=0.5, th=0.10, steps=4, across=3, mat=0)
    for k in range(12):
        q = lerp(0.95, 0.05, k / 11)
        root = el.lerp(wr, q) + t_f * 0.3
        d = (t_f * 0.95 - fd * 0.2).normalized()
        base = root + d * 0.5 + up * 0.85
        blade(covert, [base, base + d * 1.0 + up * 0.08, base + d * 1.9 + up * 0.14], up, t_f, 0.7, vane(0.2, 0.4, 1.0), lead=0.5, th=0.09, steps=3, across=3, mat=0)
    for k in range(8):
        q = lerp(0.9, 0.12, k / 7)
        root = sh.lerp(el, q) + t_u * 0.3 + up * 1.2
        d = (t_u + ud * 0.1).normalized()
        blade(covert, [root, root + d * 1.1 + up * 0.1, root + d * 2.3 + up * 0.2], up, t_u, 0.8, vane(0.2, 0.4, 1.0), lead=0.5, th=0.09, steps=3, across=3, mat=0)

    # armour: a basalt pauldron over the shoulder, a bracer round the wrist, and the hooked claw that stands out from it
    shoulder_plate = _plate_lobes(sh + V((0.9, 0.9, 0.0)), (2.4, 1.4, 2.0), 1.0, seed)
    wrist_plate = _plate_lobes(wr + V((0, 0.35, -0.1)), (1.3, 1.05, 1.5), 1.0, seed + 1)
    # the claw: a curved black horn from the wrist's leading side, pointing forward and out
    cl0 = wr + V((0.2, 0.35, -0.8))
    Hm.htube(claws, [cl0, cl0 + V((0.8, 0.25, -1.4)), cl0 + V((1.9, -0.2, -2.0)), cl0 + V((3.2, -1.0, -2.0))], lambda t: 0.5 * (1 - t) ** 0.85 + 0.03, sides=7, per=5, uv_scale=1.0, tip=True, wobble=0.0)
    # magma along the trailing edge of each primary and along the leading edge of the arm
    for k in range(10):
        root, d, length = prim_roots[k]
        w = 0.66 - 0.05 * (k / 9)
        edge = []
        for i in range(8):
            s = 0.28 + 0.66 * i / 7
            p = root + d * length * s + t_h * w * vane(0.10, 0.34, 0.5)(s) + up * (0.10 * length * s * s + 0.13 * 0.4)
            edge.append(p)
        Hm.htube(magma, edge, lambda t: 0.065 * (1 - 0.75 * t), sides=4, per=2, uv_scale=1.0, tip=True, wobble=0.0)
    out = {"flight": flight, "covert": covert, "arm": arm, "claws": claws, "magma": magma}
    return out, shoulder_plate, wrist_plate


def _plate_lobes(centre, radii, size, seed):
    """Cracked basalt armour: a few hexagonal-ish slabs, as soft lobes to be remeshed and chiselled."""
    rnd = random.Random(seed)
    lobes = []
    for k in range(5):
        a = TAU * k / 5 + rnd.uniform(-0.3, 0.3)
        r = 0.55 + rnd.uniform(-0.1, 0.1)
        c = V(centre) + V((math.cos(a) * radii[0] * r, rnd.uniform(-0.1, 0.25) * radii[1], math.sin(a) * radii[2] * r))
        lobes.append((tuple(c), (radii[0] * 0.55, radii[1] * 0.7, radii[2] * 0.55), None))
    lobes.append((tuple(centre), (radii[0] * 0.85, radii[1], radii[2] * 0.85), None))
    return lobes


# ---------------------------------------------------------------- the tail and the crest
def build_tail(coll, M):
    """Five ribbons of tail along their bones, and a small fan of short upper coverts at the root: {name: Hi}."""
    tail, glow = Hm.Hi(), Hm.Hi()
    up = V((0, 1, 0))
    chains = {"Tail0": ("Tail0A", "Tail0B", "Tail0C"), "RightTail1": ("RightTail1A", "RightTail1B"), "LeftTail1": ("LeftTail1A", "LeftTail1B"),
              "RightTail2": ("RightTail2A", "RightTail2B"), "LeftTail2": ("LeftTail2A", "LeftTail2B")}
    widths = {"Tail0": 1.15, "RightTail1": 1.0, "LeftTail1": 1.0, "RightTail2": 0.85, "LeftTail2": 0.85}
    for key, names in chains.items():
        pts = [V(BONES[names[0]][1])] + [V(BONES[n][2]) for n in names]
        side = V((1 if "Right" in key else -1 if "Left" in key else 1, 0, 0))
        # a gentle ripple so the ribbon already moves in the bind: it is straightened by the pose, never by the model
        pts = [p + V((0.35 * math.sin(i * 1.7 + len(key)), 0.0, 0.0)) if i else p for i, p in enumerate(pts)]
        tilt = {"Tail0": 0.0, "RightTail1": -0.5, "LeftTail1": 0.5, "RightTail2": -0.9, "LeftTail2": 0.9}[key]
        centre = blade(tail, pts, up, side, widths[key], vane(0.10, 0.26, 0.7), lead=0.9, th=0.12, steps=16, mat=0, cup=0.05, twist=tilt * 1.6)
        edge = [c + side * widths[key] * vane(0.10, 0.26, 0.7)(i / 15) for i, c in enumerate(centre)][3:14]
        Hm.htube(glow, edge, lambda t: 0.07 * (1 - 0.7 * t), sides=4, per=2, uv_scale=1.0, tip=True, wobble=0.0)
    # the short upper coverts fanned over the root
    for k in range(9):
        a = math.radians(-60 + 15 * k)
        root = V((0, 12.9, 3.3))
        d = V((math.sin(a), -0.05, math.cos(a))).normalized()
        blade(tail, [root, root + d * 1.6 + V((0, 0.3, 0)), root + d * 3.2 + V((0, 0.1, 0))], up, V((math.cos(a), 0, -math.sin(a))), 0.8, vane(0.2, 0.45, 1.0), lead=0.9, th=0.1, steps=5, across=3, mat=0)
    return {"tail": tail, "glow": glow}


def build_crest(coll, M):
    """Seven plumes swept back from the crown like flames: {name: Hi}."""
    crest, glow = Hm.Hi(), Hm.Hi()
    up = V((0, 1, 0))
    base = V(BONES["CrestA"][1])
    plumes = [(0.0, 1.0, 1.0), (-0.9, 0.82, 1.0), (0.9, 0.82, 1.0), (-1.5, 0.62, 0.8), (1.5, 0.62, 0.8), (-0.45, 0.9, 1.0), (0.45, 0.9, 1.0)]
    for x, scale, w in plumes:
        p0 = V((x * 0.55, base.y - 0.1 - 0.05 * abs(x), base.z + 0.1))
        # swept up and back, then falling away: a flame's lean
        p1 = p0 + V((x * 0.35, 1.05 * scale, 2.3 * scale))
        p2 = p1 + V((x * 0.4, 0.5 * scale, 2.9 * scale))
        p3 = p2 + V((x * 0.25, -0.9 * scale, 2.2 * scale))
        p4 = p3 + V((x * 0.1, -1.6 * scale, 0.9 * scale))
        centre = blade(crest, [p0, p1, p2, p3, p4], V((1 if x >= 0 else -1, 0.2, 0)), V((0, 1, 0)), 0.42 * w, vane(0.08, 0.5, 0.2), lead=1.0, th=0.1, steps=14, mat=0)
        Hm.htube(glow, centre[3:13], lambda t: 0.06 * (1 - 0.6 * t), sides=4, per=2, uv_scale=1.0, tip=True, wobble=0.0)
    return {"crest": crest, "glow": glow}


# ---------------------------------------------------------------- feathers on the body
def surface_of(skin):
    """A function (origin, direction) -> (point, normal) in Roblox space: where a ray from inside the skin leaves it."""
    from mathutils.bvhtree import BVHTree
    tree = BVHTree.FromObject(skin, bpy.context.evaluated_depsgraph_get())

    def surf(origin, direction):
        hit, n, _, _ = tree.ray_cast(W.rb(*origin), W.rb(*direction).normalized())
        if hit is None:
            return None
        return V(K.rb_inv(*hit)), V(K.rb_inv(*n)).normalized()
    return surf


def contour(hi, surf, origin, direction, flow, length, width, tilt=22.0, steps=4, th=0.1, shape=None):
    """One contour feather lying on the body where the ray from `origin` along `direction` leaves it, pointing along `flow` (projected on
    the surface) and lifted by `tilt` degrees, so rows shingle over each other."""
    hit = surf(origin, direction)
    if hit is None:
        return False
    pt, n = hit
    f = V(flow) - n * V(flow).dot(n)
    if f.length < 0.2:
        return False
    f.normalize()
    t = math.radians(tilt)
    d = f * math.cos(t) + n * math.sin(t)
    root = pt - n * 0.12 - f * 0.2
    path = [root, root + d * length * 0.5 + n * 0.07 * length, root + d * length + n * 0.03 * length]
    blade(hi, path, n, n.cross(d), width, shape or vane(0.16, 0.5, 1.0), lead=0.9, th=th, steps=steps, across=3, solid=False)
    return True


def build_body_feathers(skin, seed=7):
    """The feathers that cover the body, in rows that shingle: the breast, the neck's ruff, the thighs' trousers, the back and the
    flanks. One Hi object (the colour of the plumage)."""
    rnd = random.Random(seed)
    surf = surface_of(skin)
    hi = Hm.Hi()
    count = 0
    # the breast: rows from the throat down to the belly, lifting toward the front
    chest = V((0, 13.9, -3.0))
    for e, n in ((60, 7), (46, 9), (32, 11), (18, 12), (4, 13), (-10, 13), (-24, 12), (-38, 10)):
        er = math.radians(e)
        for k in range(n):
            ph = math.radians(-72 + 144 * k / (n - 1) + rnd.uniform(-3, 3))
            d = V((math.sin(ph) * math.cos(er), math.sin(er), -math.cos(ph) * math.cos(er)))
            count += contour(hi, surf, chest, d, (0, -0.9, 0.35), 3.1 + rnd.uniform(-0.2, 0.3), 0.85, tilt=20, steps=4)
    # the neck's ruff: long feathers hanging from rings round the neck, down over the chest
    neck = [V((0, 14.6, -5.1)), V((0, 16.0, -7.0)), V((0, 17.4, -7.7)), V((0, 18.5, -7.8))]
    for i, (c, length, n) in enumerate(zip(neck, (3.2, 2.5, 1.8, 1.2), (14, 12, 9, 6))):
        axis = (neck[min(i + 1, 3)] - neck[max(i - 1, 0)]).normalized()
        a1 = axis.cross(V((1, 0, 0))).normalized()
        a2 = axis.cross(a1).normalized()
        for k in range(n):
            a = TAU * (k + 0.5 * (i % 2)) / n
            d = a1 * math.cos(a) + a2 * math.sin(a)
            count += contour(hi, surf, c, d, (0, -1.0, 0.25), length + rnd.uniform(-0.2, 0.2), 0.95 - 0.1 * i, tilt=26, steps=4)
    # the trousers: the thighs' long feathers falling behind the knee to the hock
    for sign in (-1, 1):
        for j in range(7):
            t = j / 6
            c = V((sign * (3.3 + 0.1 * t), lerp(10.8, 4.8, t), lerp(-0.3, 1.5, t)))
            for k in range(7):
                a = math.radians(-100 + 200 * k / 6)
                # round the leg: from the outside (x = sign) through the back (+z) to the inside
                d = V((sign * math.cos(a), 0.0, math.sin(a)))
                if d.x * sign < -0.5 and j > 1:
                    continue
                count += contour(hi, surf, c, d, (0, -1.0, 0.18), lerp(3.5, 2.4, t) + rnd.uniform(-0.2, 0.3), 1.0, tilt=18 + 8 * t, steps=4)
    # the back and shoulders: scapulars laid backward over the wing roots
    for z, n in ((-4.2, 8), (-2.4, 9), (-0.6, 9), (1.2, 8), (3.0, 6)):
        for k in range(n):
            ph = math.radians(-62 + 124 * k / (n - 1) + rnd.uniform(-3, 3))
            c = V((0, 12.5, z))
            d = V((math.sin(ph), math.cos(ph), 0.0))
            count += contour(hi, surf, c, d, (0, -0.15, 1.0), 3.1 + rnd.uniform(-0.2, 0.3), 1.05, tilt=16, steps=4)
    # the flanks, under the wings
    for sign in (-1, 1):
        for e, n in ((22, 6), (6, 7), (-10, 7), (-26, 6)):
            er = math.radians(e)
            for k in range(n):
                ph = math.radians(-50 + 100 * k / (n - 1))
                d = V((sign * math.cos(er) * math.cos(ph), math.sin(er), math.sin(ph) * math.cos(er)))
                count += contour(hi, surf, V((0, 12.9, -0.2)), d, (0, -0.55, 0.85), 2.8 + rnd.uniform(-0.2, 0.3), 1.0, tilt=18, steps=4)
    return hi, count
