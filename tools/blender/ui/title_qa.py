"""QA for the title banner art (title_banner.py + title_compose.py). Needs Pillow and numpy. Exit code 0 only when every check passes.

    python title_qa.py <folder with <name>_steel.png and <name>_light.png> [<name> ...] [--plate-half 2.1]     (default: every title_tier*_full set found)

Checks, per set:
  size        800 high, a whole number of units (200 px) wide (2400 for the default canvas)
  clipping    nothing touches the canvas edge (a clipped blade or shard would show as a hard cut in the game): alpha under 3/255 within 2 px of every edge
  symmetry    the silhouette is the same upside down in the wing columns (the game turns one end half a turn for the other) and left to right overall
  highlights  under 2% of the metal's pixels are blown out to pure white (it would read as flat plastic)
  glow layer  pure white wherever it has alpha (so ImageColor3 tints it exactly), and it is not empty
  plate       the plate's middle, where the letters sit, is dark enough for light lettering (mean luminance under 0.22)
  weight      each file under 4 MB
"""
import glob
import os
import sys

import numpy as np
from PIL import Image

H, PX = 800, 200


def load(path):
    return np.asarray(Image.open(path).convert("RGBA"), dtype=np.float32) / 255.0


def iou(a, b):
    both = np.logical_and(a, b).sum()
    either = np.logical_or(a, b).sum()
    return both / either if either else 1.0


def check(folder, name, plate_half=2.1):
    results = []
    steel_path, light_path = os.path.join(folder, name + "_steel.png"), os.path.join(folder, name + "_light.png")
    steel, light = load(steel_path), load(light_path)

    def record(label, ok, detail):
        results.append((label, ok, detail))

    W = steel.shape[1]
    record("size", steel.shape[0] == H and W % PX == 0 and light.shape[:2] == steel.shape[:2], "steel %s light %s" % (steel.shape[:2], light.shape[:2]))
    edge = max(steel[:2, :, 3].max(), steel[-2:, :, 3].max(), steel[:, :2, 3].max(), steel[:, -2:, 3].max(),
               light[:2, :, 3].max(), light[-2:, :, 3].max(), light[:, :2, 3].max(), light[:, -2:, 3].max())
    record("clipping", edge < 3 / 255, "strongest alpha on an edge: %.1f/255" % (edge * 255))
    both = np.maximum(steel[..., 3], light[..., 3]) > 0.1
    flipped = both[::-1, :]
    columns = np.zeros(W, dtype=bool)
    columns[: int(W * 0.33)] = True
    columns[int(W * 0.67):] = True
    record("symmetry up/down (wings)", iou(both[:, columns], flipped[:, columns]) > 0.88, "overlap %.3f" % iou(both[:, columns], flipped[:, columns]))
    record("symmetry left/right", iou(both, both[:, ::-1]) > 0.9, "overlap %.3f" % iou(both, both[:, ::-1]))
    solid = steel[..., 3] > 0.5
    lum = steel[..., :3].mean(axis=2)
    blown = float(((lum > 0.97) & solid).sum()) / max(solid.sum(), 1)
    record("highlights", blown < 0.02, "%.2f%% of the metal blown out" % (blown * 100))
    on = light[..., 3] > 0.02
    pure = bool(np.all(light[..., :3][on] > 0.99)) if on.any() else False
    record("glow layer", on.any() and pure, "%d px lit; pure white: %s" % (int(on.sum()), pure))
    cx, cy = W // 2, H // 2
    rx, ry = int((plate_half - 0.35) * PX), int(0.2 * PX)
    zone = steel[cy - ry:cy + ry, cx - rx:cx + rx]
    mean = float((zone[..., :3].mean(axis=2) * zone[..., 3]).sum() / max(zone[..., 3].sum(), 1))
    record("plate dark for lettering", mean < 0.22, "mean luminance %.3f" % mean)
    sizes = [os.path.getsize(steel_path), os.path.getsize(light_path)]
    record("weight", max(sizes) < 4 * 1024 * 1024, "%.1f and %.1f MB" % (sizes[0] / 1048576, sizes[1] / 1048576))
    return results


def main():
    argv = sys.argv[1:]
    plate_half = 2.1  # half the plate's length, in units (title_banner.py --length / 2)
    if "--plate-half" in argv:
        i = argv.index("--plate-half")
        plate_half = float(argv[i + 1])
        del argv[i:i + 2]
    folder = argv[0]
    names = argv[1:] or sorted(os.path.basename(p)[:-10] for p in glob.glob(os.path.join(folder, "title_tier*_full_steel.png")))
    if not names:
        print("no sets found in", folder)
        sys.exit(1)
    failed = 0
    for name in names:
        print(name)
        for label, ok, detail in check(folder, name, plate_half):
            print("  %s  %-26s %s" % ("PASS" if ok else "FAIL", label, detail))
            failed += 0 if ok else 1
    print("%d check(s) failed" % failed)
    sys.exit(1 if failed else 0)


main()
