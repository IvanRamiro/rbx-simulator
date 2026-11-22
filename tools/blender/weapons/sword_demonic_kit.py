"""Mesh tools for the Demonic sword (run inside Blender, headless): parametric surfaces built from numpy grids, so the blade, the
guard and the fittings can be made at any density: dense for the high-detail source the maps are baked from (real bevels, real
engraving), coarse for the game mesh, from the same functions.

Points are authored in Roblox space (x right, y up, the point toward -z) and turned into Blender space (x, -z, y) when the mesh is
made, as the other weapon scripts do (worldlib.rb).

- Mesh: collects grids and polygons with per-vertex UVs, an "Aux" UV layer of per-face flags for the shaders, and material
  indices; object() welds, turns every face outward (closed pieces), marks sharp edges by angle and creates the mesh object.
- strokes_field(): engraving as a field: tapered strokes with a rounded groove profile, rasterised onto a grid.
- tendril(): a smoke line: a long drifting stroke ending in a small curl, for the engraving.
"""
import math

import bmesh
import bpy
import numpy as np

TAU = math.tau


def to_blender(p):
    """(..., 3) Roblox space -> Blender space."""
    p = np.asarray(p, dtype=np.float64)
    return np.stack([p[..., 0], -p[..., 2], p[..., 1]], axis=-1)


class Mesh:
    """Quads and polygons with per-corner UVs. `uv` is the primary UV layer (what a hi-detail shader reads), `aux` an extra layer
    ("Aux") holding a per-face (flag, zone) pair that shaders read as a mask."""

    def __init__(self):
        self.P = []          # arrays (k, 3)
        self.UV = []         # arrays (k, 2)
        self.faces = []      # (nf, 4) vertex index arrays, triangles repeat their last index
        self.fmat = []       # (nf,)
        self.faux = []       # (nf, 2)
        self.vaux = []       # per-vertex Aux values (k, 2), NaN where a vertex has none (then its face's value is used)
        self.n = 0

    # -- building --
    def verts(self, P, uv=None):
        P = np.asarray(P, dtype=np.float64).reshape(-1, 3)
        k = len(P)
        self.P.append(P)
        self.vaux.append(np.full((k, 2), np.nan))
        self.UV.append(np.zeros((k, 2)) if uv is None else np.asarray(uv, dtype=np.float64).reshape(-1, 2))
        i0 = self.n
        self.n += k
        return i0

    def grid(self, P, uv=None, mat=0, aux=None, flip=False, wrap=False, vaux=None):
        """A grid surface: P (rows, cols, 3); quads between neighbours. uv: (rows, cols, 2) or None (the grid's fractions);
        aux: (rows-1, cols-1, 2) per-quad values or a pair for all. wrap: the last column joins the first (a tube; do not repeat
        the first column)."""
        P = np.asarray(P, dtype=np.float64)
        r, c = P.shape[:2]
        if uv is None:
            uu, vv = np.meshgrid(np.linspace(0, 1, c), np.linspace(0, 1, r))
            uv = np.stack([uu, vv], axis=-1)
        i0 = self.verts(P.reshape(-1, 3), np.asarray(uv).reshape(-1, 2))
        if vaux is not None:
            self.vaux[-1] = np.asarray(vaux, dtype=np.float64).reshape(-1, 2)
        idx = (np.arange(r * c).reshape(r, c) + i0)
        cols = c if wrap else c - 1
        a = idx[:-1, :cols]
        b = idx[:-1, 1:] if not wrap else np.roll(idx, -1, axis=1)[:-1]
        d = idx[1:, :cols]
        e = idx[1:, 1:] if not wrap else np.roll(idx, -1, axis=1)[1:]
        quads = np.stack([a, b, e, d], axis=-1).reshape(-1, 4)
        if flip:
            quads = quads[:, ::-1]
        self.faces.append(quads)
        nf = len(quads)
        self.fmat.append(np.full(nf, mat, dtype=np.int32))
        if aux is None:
            aux_arr = np.zeros((nf, 2))
        else:
            aux = np.asarray(aux, dtype=np.float64)
            if aux.shape == (2,):
                aux_arr = np.tile(aux, (nf, 1))
            else:
                aux_arr = aux[:, :cols].reshape(-1, 2) if aux.ndim == 3 else aux.reshape(-1, 2)
        self.faux.append(aux_arr)
        return idx

    def fan(self, ring_idx, centre, mat=0, uv_centre=None, flip=False, aux=(0, 0)):
        """A cap: triangles from `centre` (a point) to the closed ring of vertex indices (a list)."""
        ring_idx = list(ring_idx)
        c = self.verts(np.asarray(centre).reshape(1, 3), np.asarray(uv_centre if uv_centre is not None else (0.5, 0.5)).reshape(1, 2))
        m = len(ring_idx)
        if flip:      # (the repeated index stays last: a triangle is a quad whose last two indices are equal)
            tri = np.array([[ring_idx[(i + 1) % m], ring_idx[i], c, c] for i in range(m)])
        else:
            tri = np.array([[ring_idx[i], ring_idx[(i + 1) % m], c, c] for i in range(m)])
        self.faces.append(tri)
        self.fmat.append(np.full(m, mat, dtype=np.int32))
        self.faux.append(np.tile(np.asarray(aux, dtype=np.float64), (m, 1)))

    def tris(self, idx, mat=0, aux=(0, 0)):
        idx = np.asarray(idx, dtype=np.int64).reshape(-1, 3)
        self.faces.append(np.concatenate([idx, idx[:, -1:]], axis=1))
        self.fmat.append(np.full(len(idx), mat, dtype=np.int32))
        self.faux.append(np.tile(np.asarray(aux, dtype=np.float64), (len(idx), 1)))

    # -- making the object --
    def object(self, name, coll, materials, sharp_deg=28.0, weld=2e-5, outward=True, smooth=True, uv_name="Param"):
        P = to_blender(np.concatenate(self.P))
        UV = np.concatenate(self.UV)
        F = np.concatenate(self.faces)
        M = np.concatenate(self.fmat)
        AUX = np.concatenate(self.faux)
        VAUX = np.concatenate(self.vaux)
        nf = len(F)
        tri = F[:, 2] == F[:, 3]
        me = bpy.data.meshes.new(name)
        me.vertices.add(len(P))
        me.vertices.foreach_set("co", P.astype(np.float32).ravel())
        sizes = np.where(tri, 3, 4).astype(np.int32)
        starts = np.concatenate([[0], np.cumsum(sizes)[:-1]]).astype(np.int32)
        # vectorised loop arrays
        n_loops = int(sizes.sum())
        lv = np.empty(n_loops, dtype=np.int32)
        luv = np.empty((n_loops, 2), dtype=np.float32)
        lax = np.empty((n_loops, 2), dtype=np.float32)
        q = np.where(~tri)[0]
        t = np.where(tri)[0]
        for rows, cnt in ((q, 4), (t, 3)):
            if len(rows) == 0:
                continue
            base = starts[rows]
            for j in range(cnt):
                lv[base + j] = F[rows, j]
                luv[base + j] = UV[F[rows, j]]
                va = VAUX[F[rows, j]]
                lax[base + j] = np.where(np.isnan(va), AUX[rows], va)
        me.loops.add(n_loops)
        me.polygons.add(nf)
        me.polygons.foreach_set("loop_start", starts)
        me.polygons.foreach_set("loop_total", sizes)
        me.loops.foreach_set("vertex_index", lv)
        me.polygons.foreach_set("material_index", M)
        uvl = me.uv_layers.new(name=uv_name)
        uvl.data.foreach_set("uv", luv.ravel())
        aux = me.uv_layers.new(name="Aux")
        aux.data.foreach_set("uv", lax.ravel())
        me.uv_layers.active_index = 0
        uvl.active_render = True
        me.update(calc_edges=True)
        for m in materials:
            me.materials.append(m)
        bm = bmesh.new()
        bm.from_mesh(me)
        if weld:
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=weld)
        bmesh.ops.dissolve_degenerate(bm, dist=1e-7, edges=bm.edges)
        if outward:
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for f in bm.faces:
            f.smooth = smooth
        if sharp_deg and smooth:
            lim = math.radians(sharp_deg)
            for e in bm.edges:
                if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > lim:
                    e.smooth = False
        bm.to_mesh(me)
        bm.free()
        o = bpy.data.objects.new(name, me)
        coll.objects.link(o)
        return o


# ---------- engraving as a field ----------
def seg_dist(A, B, p0, p1):
    """Distance from grid points (A, B) to segment p0-p1, and the parameter along it (0..1)."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L2 = dx * dx + dy * dy
    if L2 < 1e-12:
        return np.hypot(A - p0[0], B - p0[1]), np.zeros_like(A)
    t = np.clip(((A - p0[0]) * dx + (B - p0[1]) * dy) / L2, 0.0, 1.0)
    return np.hypot(A - (p0[0] + t * dx), B - (p0[1] + t * dy)), t


def strokes_field(A, B, strokes, soft=1.0):
    """Engraving depth 0..1 at grid points (A, B) (same shape) from strokes [(points (k, 2), widths (k,))]: each stroke a groove
    of the given width at each point (full width across, a rounded bottom), deepest on its line, 0 outside it. Returns the max
    over the strokes."""
    out = np.zeros_like(A, dtype=np.float64)
    for pts, widths in strokes:
        pts = np.asarray(pts, dtype=np.float64)
        widths = np.asarray(widths, dtype=np.float64)
        lo = np.array([pts[:, 0].min() - widths.max(), pts[:, 1].min() - widths.max()])
        hi = np.array([pts[:, 0].max() + widths.max(), pts[:, 1].max() + widths.max()])
        sel = (A >= lo[0]) & (A <= hi[0]) & (B >= lo[1]) & (B <= hi[1])
        if not sel.any():
            continue
        a, b = A[sel], B[sel]
        best = np.zeros_like(a)
        for i in range(len(pts) - 1):
            d, t = seg_dist(a, b, pts[i], pts[i + 1])
            w = (widths[i] * (1 - t) + widths[i + 1] * t) * 0.5
            prof = np.sqrt(np.clip(1.0 - (d / np.maximum(w, 1e-6)) ** 2, 0.0, 1.0))
            best = np.maximum(best, prof)
        out[sel] = np.maximum(out[sel], best)
    return out


def tendril(x0, y0, length, drift, amp, wavelength, phase=0.0, width=(0.02, 0.004), curl=0.9, curl_dir=1, n=90, heading=0.0, curl_turn=None):
    """A smoke line: from (x0, y0) it runs `length` along `heading` (radians, 0 = +x), swaying by `amp` with `wavelength` (the sway
    fading in over the first tenth), drifting sideways by `drift` overall, and ending in a gentle flick to the side `curl_dir` (its size
    set by `curl`). Its width swells from two thirds of width[0] at both ends to width[0] in the middle: an engraver's line with a point
    at each end, never a thick head with a thin tail (that reads as something else). Returns (points, widths)."""
    pts = []
    hx, hy = math.cos(heading), math.sin(heading)
    nx, ny = -hy, hx
    for i in range(n + 1):
        t = i / n
        s = t * length
        env = min(1.0, t * 8.0) * (1 - 0.35 * t)
        off = amp * math.sin(TAU * s / wavelength + phase) * env + drift * t * t
        tail = max(0.0, (t - 0.86) / 0.14)
        off += curl_dir * curl * 0.045 * length * tail * tail
        pts.append((x0 + hx * s + nx * off, y0 + hy * s + ny * off))
    w0, w1 = width
    widths = [w0 * (0.66 + 0.34 * math.sin(math.pi * min(1.0, i / n * 1.02)) ** 0.7) + 0.2 * w1 for i in range(n + 1)]
    return np.array(pts), np.array(widths)


def smoothstep(e0, e1, x):
    t = np.clip((np.asarray(x, dtype=np.float64) - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)
