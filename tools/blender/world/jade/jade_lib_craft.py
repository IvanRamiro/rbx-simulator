"""jade_lib_craft: crafted-detail builders shared by Jade Grove's cliffs and structures (2026-11-22, the second pass after the coordinator's review: "stacked slabs" and
"plain props" are not the bar). Plain Python on jade_lib_core.

  rock_face      a real rock face: a displaced front surface (irregular strata that step in and out, soft recessed layers, brows and undercuts, vertical joint cracks, roughness)
                 closed into a solid by a back and four sides, with an optional carved cave mouth (an arched pocket, a weathered lip) and a notch in the top edge
  foot_blocks    broken blocks lying at a cliff's foot (lumpy stones of several sizes, some tilted, mossy on top)
  root_hooks     roots growing over a brow and hooking down a face
  fluted_column  a tapered, fluted shaft with entasis, a moulded base and an optional leaf capital
  shingle_rows   a gable slope as overlapping rows of boards (a gently concave profile)
  cord_wrap      a lashing of cord round a post or beam
  woven_panel    a wattle panel of upright rods and woven bands
  curl           a spiral curl (ridge ends, finials)
"""
import math
import random

import jade_lib_core as C

TAU = C.TAU


# ----------------------------------------------------------------------------------------------------------------------
# rock face
# ----------------------------------------------------------------------------------------------------------------------
def _layers(rnd, H, count, soft_every):
    ys = sorted(rnd.uniform(0.08, 0.92) * H for _ in range(count - 1))
    # keep the layers at least 1.1 apart
    out = [0.0]
    for y in ys:
        if y - out[-1] > 1.1 and H - y > 1.0:
            out.append(y)
    out.append(H)
    pr = []
    for k in range(len(out) - 1):
        soft = (k % soft_every) == soft_every - 1
        pr.append(rnd.uniform(-2.8, -1.0) if soft else rnd.uniform(-0.1, 1.5))
    return out, pr


def rock_face(W, H, D, seed, layers=5, soft_every=3, overhang=1.2, undercut=0.9, cracks=4, rough=0.22, step=1.0, fine=None, arch=None, notch=None, mouth_depth=8.0, end_curl=0.0, end_drop=0.0):
    """Returns a closed Geo. Frame: x across (centred), y up from 0, the face looking toward -z, the rock running back to z = D.
    arch = (cx, half_width, jamb_height, crown_height): a cave mouth (pocket of depth `mouth_depth`) in the face.  notch = (cx, half_width, drop): the top edge lowered there.
    fine = (x0, x1): between these x the columns are half-spaced (the mouth needs resolution).
    end_curl / end_drop: over the last 3.4 studs at each end the face turns back into the rock by end_curl and the top comes down by end_drop (a fraction of H): the mass ends rounded, not cut."""
    rnd = random.Random(seed)
    bounds, prot = _layers(rnd, H, layers, soft_every)
    cr = []
    for _ in range(cracks):
        x = rnd.uniform(-W / 2 + 1.5, W / 2 - 1.5)
        y0 = rnd.uniform(0.0, H * 0.5)
        cr.append((x, y0, y0 + rnd.uniform(H * 0.3, H * 0.7), rnd.uniform(0.28, 0.5), rnd.uniform(0.9, 1.8)))
    xs = []
    x = -W / 2
    while x < W / 2 - 1e-6:
        xs.append(x)
        x += (step * 0.5) if (fine and fine[0] <= x <= fine[1]) else step
    xs.append(W / 2)

    def end_k(x):
        return C.smoothstep(W / 2 - 3.4, W / 2, abs(x)) if (end_curl or end_drop) else 0.0

    def top_at(x):
        t = H * (1.0 - end_drop * end_k(x))
        if notch:
            cx, hw, drop = notch
            t -= drop * (1.0 - C.smoothstep(hw - 0.6, hw + 0.6, abs(x - cx)))
        return t

    def front(x, y):
        """Depth of the front surface (z, negative toward the viewer) at (x, y)."""
        # strata: each layer sits at its own offset (meandering along the face), joined over about half a stud (a near-horizontal shelf where it steps out)
        pz = prot[0] + 0.9 * C.fbm2(x * 0.14 + seed, 0.5, seed, 2)
        for k in range(1, len(bounds) - 1):
            lo = bounds[k] + 1.0 * C.fbm2(x * 0.16 + seed + k * 7, k * 1.3, seed + k, 2)
            if y >= lo - 0.9:
                here = prot[k] + 0.9 * C.fbm2(x * 0.14 + seed + k * 3, 0.5 + k, seed, 2)
                pz = pz + (here - pz) * C.smoothstep(lo - 0.8, lo + 0.8, y)
        z = -pz
        z -= overhang * C.smoothstep(0.5, 1.0, y / H)
        z += undercut * (1.0 - C.smoothstep(0.0, 2.4, y))
        z += 1.1 * C.fbm2(x * 0.09 + seed, y * 0.12, seed + 5, 2)
        for (xj, ya, yb, w, d) in cr:
            if ya <= y <= yb:
                z += d * math.exp(-((x - xj) / w) ** 2) * C.smoothstep(ya, ya + 1.2, y) * (1 - C.smoothstep(yb - 1.2, yb, y))
        z += rough * C.fbm2(x * 0.3 + seed, y * 0.4, seed, 2)
        z += end_curl * end_k(x) ** 1.5 * (0.6 + 0.4 * y / H)
        if arch:
            cx, hw, jh, ch = arch
            dx = abs(x - cx)
            crown = jh + math.sqrt(max(0.0, 1 - (dx / hw) ** 2)) * (ch - jh) if dx < hw else -1.0
            if dx < hw and y < crown:
                # inside the mouth: a pocket, its walls ramping back over 1.3 studs from the carved lip
                margin = min(hw - dx, crown - y)
                ramp = C.smoothstep(0.0, 1.3, margin)
                z = z * (1 - ramp) + mouth_depth * ramp
            else:
                # outside it: the carved lip stands proud of the face round the opening
                if dx >= hw:
                    d_out = (dx - hw) if y < jh else math.hypot(dx - hw, y - jh)
                else:
                    d_out = y - crown
                if d_out < 1.1:
                    z -= 0.6 * (1.0 - d_out / 1.1)
        return z
    # rows: the strata's boundaries get a pair of rows each so the steps stay crisp
    ys = [0.0]
    for b in bounds[1:-1]:
        ys += [max(ys[-1] + 0.2, b - 0.75), b + 0.75]
    ys += [H]
    extra = []
    for a, b in zip(ys, ys[1:]):
        if b - a > 1.9:
            extra.append((a + b) / 2)
    ys = sorted(set(round(v, 3) for v in ys + extra))
    g = C.Geo()
    grid = []
    for i, x in enumerate(xs):
        col = []
        t = top_at(x)
        for y in ys:
            yy = y * t / H
            col.append((x, yy, front(x, yy)))
        grid.append(col)
    nx, ny = len(xs), len(ys)
    for i in range(nx - 1):
        for j in range(ny - 1):
            g.face(grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j])
    # the ring round the face, pulled back to z = D: top and bottom strips, the two sides, and a back fan
    ring_front = [grid[i][0] for i in range(nx)] + [grid[nx - 1][j] for j in range(1, ny)] + [grid[i][ny - 1] for i in range(nx - 2, -1, -1)] + [grid[0][j] for j in range(ny - 2, 0, -1)]
    ring_back = [(p[0], p[1], D) for p in ring_front]
    n = len(ring_front)
    for k in range(n):
        a, b = ring_front[k], ring_front[(k + 1) % n]
        a2, b2 = ring_back[k], ring_back[(k + 1) % n]
        g.face(b, b2, a2, a)
    cx = sum(p[0] for p in ring_back) / n
    cy = sum(p[1] for p in ring_back) / n
    for k in range(n):
        g.face(ring_back[k], ring_back[(k + 1) % n], (cx, cy, D))
    return g


def face_mat(seed, mouth_z=2.0):
    """Rock by what a face looks at and where it sits: moss on up-facing shelves in soft patches, dark in the cracks, the undersides and the mouth, and weathered bands of
    pale and dark stone following the strata (a band every 2.6 studs, wavering), never a per-face checker."""
    def choose(n, ctr):
        if ctr[2] > mouth_z:
            return "RockDark"
        if n[1] > 0.5:
            if C.fbm3(ctr[0] * 0.12 + seed, ctr[1] * 0.12, ctr[2] * 0.12, seed, 2) > -0.2:
                return "Moss"
            return "RockPale"
        if n[1] < -0.3 or (abs(n[0]) > 0.6 and n[1] < 0.2):
            return "RockDark"
        band = int((ctr[1] + 1.6 * C.fbm2(ctr[0] * 0.07 + seed, 0.3, seed, 2)) / 2.6)
        if ctr[1] < 0.9:
            return "RockDark"
        return ("Rock", "RockPale", "Rock", "RockDark")[band % 4]
    return choose


def foot_blocks(P, rnd, W, z0, n, seed, ymax=2.2, avoid=None, seg=8, rings=5):
    """Broken blocks lying in front of a face: lumpy stones of several sizes, some tilted, moss on top, leaning against the foot."""
    for k in range(n):
        x = rnd.uniform(-W / 2 + 1.0, W / 2 - 3.6)
        if avoid and avoid[0] < x < avoid[1]:
            x = (avoid[1] + 1.0) if x > 0 else (avoid[0] - 1.0)
        z = z0 - rnd.uniform(0.4, 3.4)
        r = rnd.uniform(0.7, 1.6)
        ry = min(r * rnd.uniform(0.6, 1.0), ymax / 2)
        g = C.ellipsoid((0, 0, 0), (r, ry, r * rnd.uniform(0.8, 1.2)), seg, rings, 0.3, seed + k * 7, flat=-ry * 0.5)
        P.put(g, lambda n_, c: "Moss" if n_[1] > 0.6 and C.fbm3(c[0] * 0.6, c[1], c[2] * 0.6, seed, 2) > -0.05 else ("RockDark" if c[1] < 0.3 else "Rock"),
              t=(x, ry * 0.4, z), yaw=rnd.uniform(0, TAU), tilt=((rnd.uniform(-1, 1), 0, rnd.uniform(-1, 1)), rnd.uniform(0.0, 0.5)))


def root_hooks(P, rnd, W, H, z_face, n, seed, mat="Root", avoid=None):
    """Roots coming over the brow and hooking down the face: a thick root from the top, thinning, with a curl at its end."""
    for k in range(n):
        x = rnd.uniform(-W / 2 + 3.6, W / 2 - 3.6)
        if avoid and avoid[0] < x < avoid[1]:
            x = (avoid[1] + 1.0) if x > 0 else (avoid[0] - 1.0)
        L = rnd.uniform(H * 0.25, H * 0.6)
        z = z_face - rnd.uniform(0.2, 0.5)
        pts = [(x, H - 0.3, z + 3.6), (x + rnd.uniform(-0.5, 0.5), H - 0.6, z + 0.6), (x + rnd.uniform(-1.0, 1.0), H - L * 0.5, z - 0.5), (x + rnd.uniform(-1.2, 1.2), H - L, z - 0.3)]
        P.put(C.tube(pts, lambda t: 0.46 - 0.34 * t, None, 4, per=2, wob=0.1, seed=seed + k), mat)


# ----------------------------------------------------------------------------------------------------------------------
# structure details
# ----------------------------------------------------------------------------------------------------------------------
def fluted_column(h, r0, r1, flutes=8, seg=16, entasis=0.06, base=True, capital=None, seed=0, break_top=0.0, rings=3):
    """A tapered shaft with fluting and entasis. Returns a Geo from y = 0 (a moulded base when `base`). capital = None | 'leaf'. break_top > 0 breaks the top at an angle."""
    prof = []
    if base:
        prof += [(0.0, -0.3), (r0 * 1.5, -0.3), (r0 * 1.5, 0.14), (r0 * 1.25, 0.28), (r0 * 1.1, 0.44)]
    else:
        prof += [(0.0, -0.3), (r0 * 1.02, -0.3)]
    n = rings
    for k in range(n + 1):
        t = k / float(n)
        y = 0.5 + (h - 0.5) * t
        r = (r0 + (r1 - r0) * t) * (1 + entasis * math.sin(math.pi * t))
        prof.append((r, y))
    if capital:
        prof += [(r1 * 1.18, h + 0.05), (r1 * 1.5, h + 0.28), (r1 * 1.75, h + 0.62), (r1 * 1.6, h + 0.92), (0.0, h + 0.92)]
    else:
        prof.append((0.0, h))

    def mod(th, k):
        if base and k < 5:
            return 1.0
        if (not base) and k < 2:
            return 1.0
        if capital and k >= len(prof) - 5:
            return 1.0 + 0.08 * math.sin(flutes * th)
        return 1.0 - 0.07 * (0.5 + 0.5 * math.cos(flutes * th))
    g = C.lathe(prof, seg, mod=mod)
    return g


def shingle_rows(P, c, w, d, rise, rows, thick, yaw, seed, mat="Shingle", overhang=0.9, moss=False, curve=0.35):
    """Both slopes of a gable as overlapping rows of boards: a gently concave profile (the slope steepens toward the eave), each row a tilted board a little longer than the
    last; ridge along z, eave line at y = c[1], half width w/2 + overhang."""
    rnd = random.Random(seed)
    half = w / 2 + overhang
    for side in (-1, 1):
        for k in range(rows):
            t0, t1 = k / rows, (k + 1) / rows
            def yy(t):
                return rise * (1 - t) ** (1.0 + curve) * 1.0 + 0.0
            x0, x1 = half * t0, half * t1
            y0, y1 = yy(t0), yy(t1)
            ang = math.atan2(y0 - y1, x1 - x0)
            length = math.hypot(x1 - x0, y0 - y1) + 0.35
            xm, ym = side * (x0 + x1) / 2, (y0 + y1) / 2
            cs, sn = math.cos(yaw), math.sin(yaw)
            dd = d + overhang * 1.2 + rnd.uniform(-0.25, 0.25)
            ang_k = ang - (0.07 if k % 2 else 0.0)      # every other row lifts its outer edge a little: shingles overlap, and no two rows lie in one plane
            board = C.chunk((0, 0, 0), (length, thick, dd), seed + k * 5 + side, 0.02, tilt=((0, 0, 1), -side * ang_k))

            def m(n_, ctr, kk=k):
                if moss and n_[1] > 0.6 and C.fbm3(ctr[0] * 0.4 + seed, ctr[1], ctr[2] * 0.4, seed, 2) > 0.05 + 0.06 * kk:
                    return "Moss"
                return mat if (kk % 2) else "Timber"
            P.put(board, m, t=(c[0] + (xm * cs), c[1] + ym + thick * 0.4 * k * 0.0, c[2] - xm * sn), yaw=yaw)
    return P


def ring_band(r_in, r_out, y0, y1, seg=8):
    """A closed flat ring (a washer with a height): the shell of a lashing round a post. No axis caps, so nothing coplanar is doubled."""
    loop = [(r_out, y0), (r_out, y1), (r_in, y1), (r_in, y0)]
    rings = [[(math.cos(TAU * i / seg) * r, y, math.sin(TAU * i / seg) * r) for i in range(seg)] for (r, y) in loop]
    g = C.Geo()
    for k in range(4):
        a, b = rings[k], rings[(k + 1) % 4]
        for i in range(seg):
            j = (i + 1) % seg
            g.face(a[i], a[j], b[j], b[i])
    return g


def cord_wrap(P, centre, r, axis=(0.0, 1.0, 0.0), turns=2, width=0.22, mat="Cord"):
    """A lashing of cord: a few thin rings round a post or beam (axis = its direction)."""
    ax = C.vnorm(axis)
    up = (0.0, 1.0, 0.0)
    cr = C.vcross(up, ax)
    if C.vlen(cr) < 1e-6:
        tilt = None
    else:
        tilt = (C.vnorm(cr), math.acos(max(-1.0, min(1.0, C.vdot(up, ax)))))
    seg = 6 if r < 0.6 else 8
    for k in range(turns):
        y = (k - (turns - 1) / 2) * width * 0.9
        P.put(ring_band(r - 0.03, r + 0.1, y - width / 2, y + width / 2, seg), mat, t=centre, tilt=tilt)


def woven_panel(P, x0, x1, y0, y1, z, rods=7, bands=5, rod_r=0.07, mat_rod="Timber", mat_band="Cord", seed=0, axis="x"):
    """A wattle panel in the plane of constant z (axis 'x') or constant x (axis 'z'): upright rods, horizontal bands woven in front of and behind them alternately."""
    rnd = random.Random(seed)
    for i in range(rods):
        t = i / float(max(1, rods - 1))
        x = x0 + (x1 - x0) * t
        p0, p1 = ((x, y0, z), (x, y1 + rnd.uniform(-0.2, 0.2), z)) if axis == "x" else ((z, y0, x), (z, y1 + rnd.uniform(-0.2, 0.2), x))
        P.put(C.tube([p0, p1], rod_r, rod_r * 0.9, 4, per=1), mat_rod)
    for j in range(bands):
        y = y0 + (y1 - y0) * (j + 0.5) / bands
        pts = []
        for i in range(rods):
            t = i / float(max(1, rods - 1))
            x = x0 + (x1 - x0) * t
            off = (0.1 if (i + j) % 2 == 0 else -0.1)
            pts.append((x, y, z + off) if axis == "x" else (z + off, y, x))
        P.put(C.tube(pts, 0.06, 0.06, 3, per=1), mat_band)


def curl(P, base, direction, r0, turns=1.2, size=0.6, mat="Timber", up=(0.0, 1.0, 0.0)):
    """A spiral curl growing out of `base` along `direction` (a ridge end or a finial): a tube winding in."""
    d = C.vnorm(direction)
    side = C.vnorm(C.vcross(d, up)) if abs(C.vdot(d, up)) < 0.95 else (1.0, 0.0, 0.0)
    nrm = C.vcross(side, d)
    pts = []
    for k in range(7):
        a = turns * TAU * k / 6.0
        rr = size * (1.0 - 0.7 * k / 6.0)
        px = d[0] * (math.sin(a) * rr + k * size * 0.1) + nrm[0] * (1 - math.cos(a)) * rr
        py = d[1] * (math.sin(a) * rr + k * size * 0.1) + nrm[1] * (1 - math.cos(a)) * rr
        pz = d[2] * (math.sin(a) * rr + k * size * 0.1) + nrm[2] * (1 - math.cos(a)) * rr
        pts.append((base[0] + px, base[1] + py, base[2] + pz))
    P.put(C.tube(pts, lambda t: r0 * (1 - 0.7 * t), None, 4, per=1), mat)
