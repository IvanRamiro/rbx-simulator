"""The Demonic sword's grip, pommel and cord (run inside Blender, headless).

Authored in the weapon's frame (the hand at z = 0, the point toward -Z, flats +-Y, edges +-X). The R15 hand block is 0.91 long
along the grip; the grip runs from the guard's rear face (z -0.73) to the pommel (z +0.80), so the hand's fist closes on the middle
and the fittings stand clear of it.

    grip_core(m, lod, mat)    the ray-skin core, a slightly flattened oval with a gentle belly
    wrap(m, lod, mat)         blood-red silk cord bound in the diamond wrap: two sets of flat ribbons crossing over and under
    fuchi(m, lod, mat)        the collar at the guard end of the grip
    kashira(m, lod, mat)      the heavy cap at the other end, with the stem the ring hangs from
    ring(m, lod, mat)         the Korean-style ring pommel: a heavy flat-sided ring standing in the flat the player sees
    cord_parts(...)           the short ragged red cord tied through the ring (built with the egg_hi tube tools)
"""
import math

import numpy as np

import sword_demonic_kit as KT

smooth = KT.smoothstep
TAU = math.tau

Z_FRONT = -0.72     # the guard's rear face
Z_BACK = 0.82       # where the cap begins
RX, RY = 0.168, 0.140        # the grip's half width (across the flats' edges) and half thickness at the belly

# the ring's numbers
RING_R = 0.275      # its major radius
RING_RADIAL = 0.098     # half its radial width... the section's half width in the ring's plane
RING_THICK = 0.078      # half its thickness (along y)
RING_Z = 1.10 + RING_R + 0.04     # its centre along the weapon


def grip_r(z):
    z = np.asarray(z, dtype=np.float64)
    t = np.clip((z - Z_FRONT) / (Z_BACK - Z_FRONT), 0.0, 1.0)
    belly = 0.93 + 0.10 * np.sin(np.pi * t) ** 0.7
    return RX * belly, RY * belly


def lathe(m, z, rx, ry, p=2.4, n=32, mat=0, caps=(True, True), uv=None, belt=False):
    """A solid of revolution round the z axis, its rings squashed (rx across, ry along y) and squared (superellipse exponent p),
    ring k at z[k] with half sizes rx[k], ry[k]; ends capped by fans. belt=True (the game mesh): the UVs are a straight strip in studs
    (round the ring, along the profile) closing on a repeated first column, so the bake lays it out as a rectangle: a short barrel
    unwrapped by projection comes out as a ring-shaped island, and ring-shaped islands side by side read as eyes."""
    z = np.asarray(z, dtype=np.float64)
    rx = np.asarray(rx, dtype=np.float64)
    ry = np.asarray(ry, dtype=np.float64)
    ang = np.linspace(0.0, TAU, n, endpoint=False)
    cx = np.sign(np.cos(ang)) * np.abs(np.cos(ang)) ** (2.0 / p)
    cy = np.sign(np.sin(ang)) * np.abs(np.sin(ang)) ** (2.0 / p)
    ring = np.zeros((len(z), n, 3))
    ring[..., 0] = rx[:, None] * cx[None, :]
    ring[..., 1] = ry[:, None] * cy[None, :]
    ring[..., 2] = z[:, None]
    if belt:
        ring2 = np.concatenate([ring, ring[:, :1]], axis=1)
        per = TAU * float(np.mean(np.sqrt((rx ** 2 + ry ** 2) / 2)))
        run = np.concatenate([[0.0], np.cumsum(np.sqrt(np.diff(z) ** 2 + np.diff(np.sqrt((rx ** 2 + ry ** 2) / 2)) ** 2))])
        uu = np.broadcast_to(np.linspace(0, per, n + 1)[None, :], (len(z), n + 1))
        vv = np.broadcast_to(run[:, None], (len(z), n + 1))
        idx = m.grid(ring2, np.stack([uu, vv], axis=-1), mat=mat)
        idx = idx[:, :-1]
    else:
        if uv is None:
            uu = np.broadcast_to(np.linspace(0, 1, n, endpoint=False)[None, :], (len(z), n))
            vv = np.broadcast_to(((z - z[0]) / max(abs(z[-1] - z[0]), 1e-6))[:, None], (len(z), n))
            uv = np.stack([uu, vv], axis=-1)
        idx = m.grid(ring, uv, mat=mat, wrap=True)
    if caps[0]:
        m.fan(idx[0], np.array([0.0, 0.0, z[0]]), mat=mat, flip=True)
    if caps[1]:
        m.fan(idx[-1], np.array([0.0, 0.0, z[-1]]), mat=mat)
    return idx


def grip_core(m, lod="hi", mat=0):
    nz = 40 if lod == "hi" else 8
    z = np.linspace(Z_FRONT - 0.04, Z_BACK + 0.04, nz)
    rx, ry = grip_r(z)
    lathe(m, z, rx * 0.985, ry * 0.985, p=2.6, n=40 if lod == "hi" else 14, mat=mat, caps=(False, False))


def grip_core_low(m, mat=0):
    """The game mesh's grip: the core at the wrap's surface (the ribbons are baked, not geometry)."""
    z = np.linspace(Z_FRONT - 0.02, Z_BACK + 0.02, 9)
    rx, ry = grip_r(z)
    lathe(m, z, rx + 0.020, ry + 0.020, p=2.4, n=14, mat=mat, caps=(False, False), belt=True)


def wrap(m, lod="hi", mat=0, nrib=5, pitch=0.95, width=0.108, thick=0.026, lift=0.011):
    """Two sets of `nrib` flat ribbons wound in opposite hands round the grip between the collars, crossing over and under in a
    plain weave, so diamonds of the core show between them."""
    z0, z1 = Z_FRONT + 0.10, Z_BACK - 0.02
    nz = 120 if lod == "hi" else 1
    if lod != "hi":
        return
    z = np.linspace(z0, z1, nz)
    rx, ry = grip_r(z)
    prof = [(1, 0.55), (0.55, 1), (-0.55, 1), (-1, 0.55), (-1, -0.55), (-0.55, -1), (0.55, -1), (1, -0.55)]
    for hand in (1, -1):
        for i in range(nrib):
            th = TAU * i / nrib + (0.0 if hand > 0 else math.pi / nrib * 0.0) + (z - z0) * 0
            theta = TAU * i / nrib + hand * TAU * (z - z0) / pitch
            lf = hand * lift * np.cos(TAU * nrib * (z - z0) / pitch)
            ex = (rx + thick * 0.5 + lf)
            ey = (ry + thick * 0.5 + lf)
            pos = np.stack([ex * np.cos(theta), ey * np.sin(theta), z], axis=-1)
            tan = np.gradient(pos, axis=0)
            tan /= np.linalg.norm(tan, axis=-1, keepdims=True)
            nrm = np.stack([np.cos(theta) / rx, np.sin(theta) / ry, np.zeros(nz)], axis=-1)
            nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
            side = np.cross(tan, nrm)
            side /= np.linalg.norm(side, axis=-1, keepdims=True)
            rows = []
            for a, b in prof:
                rows.append(pos + side * (a * width / 2) + nrm * (b * thick / 2))
            ring = np.stack(rows, axis=1)       # (nz, 8, 3)
            uu = np.broadcast_to(np.linspace(0, 1, 8, endpoint=False)[None, :], (nz, 8))
            vv = np.broadcast_to(((z - z0) / (z1 - z0))[:, None] * 9.0, (nz, 8))
            idx = m.grid(ring, np.stack([uu, vv], axis=-1), mat=mat, wrap=True)
            m.fan(idx[0], pos[0], mat=mat, flip=True)
            m.fan(idx[-1], pos[-1], mat=mat)


def fuchi(m, lod="hi", mat=1):
    """The collar at the guard end: a short barrel, a hairline groove each side of a raised band."""
    n = 36 if lod == "hi" else 14
    zs = np.array([Z_FRONT, Z_FRONT + 0.012, Z_FRONT + 0.03, Z_FRONT + 0.05, Z_FRONT + 0.075, Z_FRONT + 0.10, Z_FRONT + 0.125, Z_FRONT + 0.15, Z_FRONT + 0.165])
    k = np.array([0.88, 1.12, 1.12, 1.04, 1.16, 1.16, 1.04, 1.10, 0.97])
    if lod != "hi":
        zs = np.array([Z_FRONT, Z_FRONT + 0.02, Z_FRONT + 0.075, Z_FRONT + 0.125, Z_FRONT + 0.165])
        k = np.array([0.9, 1.12, 1.15, 1.12, 0.97])
    rx, ry = grip_r(zs)
    lathe(m, zs, rx * k + 0.012, ry * k + 0.012, p=2.4, n=n, mat=mat, caps=(False, False), belt=(lod != "hi"))


def kashira(m, lod="hi", mat=1):
    """The cap: swells from the grip's end into a heavy rounded barrel, then draws in to the stem the ring hangs from."""
    n = 36 if lod == "hi" else 14
    z = np.linspace(Z_BACK - 0.02, 1.12, 26 if lod == "hi" else 9)
    t = (z - z[0]) / (z[-1] - z[0])
    prof = 0.88 + 0.30 * np.sin(np.pi * np.clip(t * 1.25, 0, 1)) ** 0.8 - 0.55 * smooth(0.72, 1.0, t)
    rx, ry = grip_r(np.array([Z_BACK]))
    lathe(m, z, rx[0] * prof + 0.005, ry[0] * prof * 1.12 + 0.005, p=2.5, n=n, mat=mat, caps=(False, lod == "hi"), belt=(lod != "hi"))


def ring_strokes():
    """Smoke lines round the ring's two flat faces: in (arc distance round the ring, distance across its width): one wave that circles
    it with a heavier second swell, and a curl where it ends."""
    n = 220
    R = RING_R
    out = []
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append((TAU * R * t * 0.94, 0.022 * math.sin(TAU * 3 * t) + 0.006 * math.sin(TAU * 7 * t + 1.0)))
    out.append((np.array(pts), np.array([0.015 * (1 - 0.6 * abs(2 * i / n - 1)) + 0.004 for i in range(n + 1)])))
    return out


def ring(m, lod="hi", mat=0):
    """The ring pommel: standing in the plane the player sees (the x-z plane), a heavy ring of rounded-rectangle section, engraved on its
    two flat faces with one flowing line."""
    nu = 260 if lod == "hi" else 28
    ns = 120 if lod == "hi" else 10
    u = np.linspace(0.0, TAU, nu + 1)
    sa = np.linspace(0.0, TAU, ns, endpoint=False)
    p = 3.0
    cs, sn = np.cos(sa), np.sin(sa)
    sx = np.sign(cs) * np.abs(cs) ** (2.0 / p) * RING_RADIAL
    sy = np.sign(sn) * np.abs(sn) ** (2.0 / p) * RING_THICK
    P = np.zeros((nu + 1, ns + 1, 3))
    depth = np.zeros((nu + 1, ns + 1))
    sx1 = np.concatenate([sx, sx[:1]])
    sy1 = np.concatenate([sy, sy[:1]])
    sn1 = np.concatenate([sn, sn[:1]])
    if lod == "hi":
        A, B = np.meshgrid(u * RING_R, sx1, indexing="ij")
        strokes = ring_strokes()
        f_top = KT.strokes_field(A, B, strokes)
        f_bot = KT.strokes_field(A, B, [(np.column_stack([q[:, 0], -q[:, 1]]), w) for q, w in strokes])
        face = np.clip((np.abs(sn1) - 0.9) / 0.1, 0, 1)[None, :] * (np.abs(sx1) < RING_RADIAL * 0.72)[None, :]
        depth = 0.014 * np.where(sn1[None, :] > 0, f_top, f_bot) * face
    for i in range(nu + 1):
        a = u[i]
        radial = np.array([math.sin(a), 0.0, math.cos(a)])       # in the x-z plane
        c = np.array([0.0, 0.0, RING_Z]) + radial * RING_R
        P[i, :, 0] = c[0] + radial[0] * sx1
        P[i, :, 2] = c[2] + radial[2] * sx1
        P[i, :, 1] = sy1 - np.sign(sn1) * depth[i]
    # the ring is a belt: u round its section, v round the ring, both closing on repeated first rows and columns (so no quad's UVs run
    # back across the island)
    uu = np.broadcast_to(np.linspace(0, 1, ns + 1)[None, :], (nu + 1, ns + 1))
    vv = np.broadcast_to(np.linspace(0, 1, nu + 1)[:, None], (nu + 1, ns + 1))
    va = np.stack([(depth > 0.004).astype(float), np.zeros_like(depth)], axis=-1) if lod == "hi" else None
    m.grid(P, np.stack([uu, vv], axis=-1), mat=mat, vaux=va)


def ring_stem(m, lod="hi", mat=0):
    """The stem from the cap into the ring's near side."""
    z = np.linspace(1.04, 1.10 + RING_RADIAL * 0.7, 6)
    r = 0.085 * (1 - 0.15 * np.linspace(0, 1, 6))
    lathe(m, z, r, r * 0.9, p=2.4, n=18 if lod == "hi" else 10, mat=mat, caps=(False, False), belt=(lod != "hi"))


# ---------- the cord ----------
def cord_parts(hi, seed=7):
    """The short ragged cord, in an egg_hi `Hi` object: a lark's-head loop round the ring's far side, two twisted tails that drop
    and trail back, and a brush of frayed strands at each end."""
    import random

    import secret_kit as SK
    import egg_hi as Hm
    from mathutils import Vector as V
    rnd = random.Random(seed)
    far = RING_Z + RING_R                 # the ring's far side, along the weapon
    # the loop: the cord goes round the ring's tube a turn and a half
    coil = []
    for i in range(0, 25):
        a = TAU * 1.5 * i / 24
        y = 0.115 * math.sin(a)
        zz = far + 0.115 * math.cos(a)
        coil.append((-0.075 + 0.15 * i / 24, y, zz))
    SK.strand(hi, coil, 0.046, turns=0.0, strands=1, sides=6, per=2, mat=0)
    tails = [
        [(0.075, 0.115 * math.sin(TAU * 1.5), far + 0.115 * math.cos(TAU * 1.5)), (0.10, -0.12, far + 0.24), (0.13, -0.28, far + 0.42), (0.12, -0.42, far + 0.58)],
        [(-0.07, 0.0, far + 0.12), (-0.09, -0.10, far + 0.30), (-0.14, -0.24, far + 0.48), (-0.10, -0.36, far + 0.64)],
    ]
    for t in tails:
        SK.strand(hi, t, 0.066, turns=3.0, strands=2, sides=5, per=6, mat=0, ratio=0.62)
        end = V(t[-1])
        for k in range(9):         # a brush of frayed ends
            d = V((rnd.uniform(-0.05, 0.05), rnd.uniform(-0.12, 0.0), rnd.uniform(0.05, 0.22)))
            a = end + V((rnd.uniform(-0.025, 0.025), rnd.uniform(-0.02, 0.02), 0.0))
            b = end + d * rnd.uniform(0.8, 1.4)
            mid = (a + b) / 2 + V((rnd.uniform(-0.02, 0.02), -0.02, 0.0))
            Hm.htube(hi, [a, mid, b], lambda u: 0.014 * (1 - 0.8 * u) + 0.002, sides=4, per=2, mat=0, uv_scale=6.0, tip=True, wobble=0.0)
