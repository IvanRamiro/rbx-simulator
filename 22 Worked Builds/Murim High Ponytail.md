---
type: build
tags: [roblox, ugc, hair, marketplace]
created: 2026-11-02
status: files deleted 2026-11-11 at the owner's word (paused since 2026-11-02, never published); kept as a record
---

# Murim High Ponytail

> **Deleted (2026-11-11):** the owner chose to delete this hair's files (`assets/ugc/Hair/MurimHighPonytail/`, `tools/blender/ugc/hair/`). They remain in git history (last present in commit 0b179a4). This note stays as the record of how it was built.

A Roblox marketplace hair (a rigid accessory on HairAttachment), made for the owner to sell; not
part of Qi Aura Simulator. It is the first item of the hair category: scripts in
`tools/blender/ugc/hair/`, assets in `assets/ugc/Hair/`.

## The brief

The owner's "Murim Hair" concept sheet, its main design (front, side and back views): "You only
need one just do the first thing which is the high ponytail". Then: "no volume, do exactly what's
on the reference but enhance it", and the [[Universal 3D Modeling Directive]].

## How it got here (three rejected passes, one lesson each)

1. **Sleek, drawn back:** my own idea, not the sheet's. Rejected: "no volume".
2. **Spiky clumps:** about 70 generated clumps. Rejected: "is that the best you can do?", with
   marketplace hairs for comparison. In clay it was a spiky helmet, a pile of cones and a
   detached tail.
3. **Thin blade strands:** written but never built. The owner's directive arrived first, and it
   rules out dozens of duplicated strands.
4. **Masses** (`masses.py`): lobed sheets. Shown in clay, then "start from the scratch again".
5. **Third design** (`v3.py`, `v3_locks.py`, `run_v3.py`), built in stages, each checked in clay
   from six views:
   - **Stage 1, primary forms:** the mane, the bangs and curtains as major lobes, the chest locks,
     the tie and a comet-shaped tail.
   - **Stage 2:** every lock designed in a table.
   - **Stage 3:** the bake, the clasp and the ribbon.

## The design (third, final)

From the sheet, analysed for why it works, not copied:
- **Silhouette:** a tall, wild mane, flaring at the temples and narrowing to the jaw, with long
  locks onto the chest; a high tie, and a long comet of a tail.
- **Locks, each one in a table:**
  - centre-parted bangs: 12 (the left and right sides differ);
  - side curtains: 12;
  - chest locks: 4;
  - crown locks drawn up into the tie: 9;
  - nape: 5;
  - a burst out of the tie: 4;
  - tail clumps in two layers along an S: 8;
  - flyaways: 2.

  A coarse mane base sits underneath.
- **Tie:**
  - a silver clasp (a band, a pointed crown at the front with a red gem, a diamond at the back);
  - a crimson bow, with two tails with forked ends down the tail and one streamer.
- **Shading:**
  - an anime gradient: dark roots, a soft highlight band, fine strands;
  - the tail's ends turn burgundy;
  - roughness about 0.6, a soft sheen.

## Files

- **Scripts:** `tools/blender/ugc/hair/murim_high_ponytail/run_v3.py`. `run(ref_dir)` rebuilds it in
  about 40 s.
- **Output:** `assets/ugc/Hair/MurimHighPonytail/`:
  - `MurimHighPonytail.fbx`;
  - the four maps, uploaded (IDs in `maps.json`, read back from Roblox and matching);
  - `MurimHighPonytail_export.json`: the fit report and the HairAttachment position in the Handle;
  - `MurimHighPonytail.blend`: this design only.

## Close-up pass (2026-11-02)

The owner asked to see it; at full size the review sheets had hidden its faults. The owner's word:
"Fix it now, the rounder locks, tones, clasp and ribbons".
- **Rounder locks:** six-sided sections where the camera looks most (crown, bangs, curtains), five
  on the tail and the burst, four on the thin chest locks. The nape (hidden under the tail) and the
  two flyaways (they read as twigs) went to pay for it.
- **Tones:** a weaker highlight band; on the tail it sits lower (0.38 to 0.56), off the arch.
- **Clasp:** a thicker band; the crown a third larger and raised clear of the hair; the gem 40%
  larger; brighter silver at metalness 0.5.
- **Ribbons:** a clean satin shader; the occlusion pass now at 256 samples and smoothed. At 32
  samples its grain blotched the bright crimson (pixel noise 0.058, now 0.033, the designed
  sheen).

## Checked (2026-11-02, after the close-up pass)

- **Mesh:** one mesh, 3,904 triangles (budget 4,000), mostly quads, no n-gons, 59 closed pieces.
  None inside-out; no open edges, degenerate faces or loose vertices.
- **UVs and material:** every UV inside the texture, one material, no vertex colours.
- **Fit:** inside Roblox's Classic hair box round HairAttachment: 0.93 studs at the widest side,
  0.82 in front, 1.50 behind, 2.63 down and 0.66 up.
- **Maps:** 1,024 (colour and normal) and 512 (roughness and metalness); no black texels in the
  normal or roughness maps.
- **Reviewed:** six-view renders in clay, and of the baked game mesh in EEVEE and Cycles.
- **Not yet:**
  - the import, Accessory set-up and fit test on the owner's avatar and a blocky dummy in Studio;
  - Roblox's marketplace validation, which runs only at upload;
  - fit on non-blocky bodies (it is built for the Classic body scale).

## Lessons (measured)

- **Bake each part from its own source** (`hair_kit.split_pairs`). Lens-shaped sources bulge past
  the diamond game locks, so a neighbour bled in as stair-stepped patches.
- **Don't weld separate locks:** they share root points. A welded tail fused clumps into one part
  that was baked from one clump.
- **A smooth underlayer bakes from itself.** A finer source baked black rings into the mane's
  normal map.
- **Map the underlayer's UVs into the shader's range.** Past v = 1 the shader deepened it to root
  black, which read as holes.
- **Occlusion over the whole game mesh:** keep it short (0.05) and shallow (floor 0.6). A deep
  floor ringed the mane in black where locks hover over it.
- **Glossy black hair mirrors a dark sky as black.** Roughness about 0.6. Metallic silver reads as
  a dark lump the same way: metalness 0.5.
- **Judge an asset at the size it is sold at.** Four-sided locks looked fine on a small review sheet
  and like folded paper close up.
- **Occlusion grain hides on black and shows on bright colours.** Bake it with many samples and
  smooth it. Measure noise as pixel-to-neighbour difference.
- **When a render shows a defect, isolate it.** Solid view, then colour only, then normal only;
  then compare EEVEE with Cycles.

Related: [[Roblox Layered Clothing Pipeline]], [[Eclipse Exorcist Outfit]], [[Work in Progress]].
