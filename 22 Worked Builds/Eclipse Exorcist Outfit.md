---
type: build
tags: [roblox, ugc, outfit, marketplace]
created: 2026-11-02
status: built and tested in Studio; not yet published
---

# Eclipse Exorcist Outfit

A Roblox marketplace outfit made for the owner to sell. It isn't part of Qi Aura Simulator.

## The brief

From the owner's concept sheet (a blocky avatar in a black and crimson exorcist robe): "My
favorite detail is the asymmetric robe with the red braided waist cord and silver talismans";
"you can invent other design". Later: "no error, smooth".

The owner chose:
- layered clothing for the robe and pants, plus a waist set;
- three items;
- tuned on the blocky body;
- the high collar mask only (no hair).

## The design

An exorcist who seals a blood-moon demon into silver talismans; the robe shows what the seal
costs him.

**EE_Robe** (layered jacket, 3,908 triangles):
- black silk with crimson brush slashes on his left side and grey storm clouds (kumo) printed on
  his right;
- a high collar masking the face to the nose, crimson inside;
- a crimson crossed collar band (left over right);
- a white funeral stole with ink clouds and a seal stamp over the left shoulder, and a black
  half-mantle with three lappets over the right: the shoulders never match;
- five skirt panels, long on the left with a pointed tail, short on the right, over a ragged,
  scorched crimson underskirt;
- an eclipse crest on the back; a silver clasp on the collar.

**EE_Hakama** (layered pants, 2,064 triangles): charcoal pinstriped hakama, shins in black kyahan
wraps cross-tied with crimson cord, split-toed lacquer tabi boots.

**EE_SealCord** (layered, worn over the robe, 3,468 triangles):
- a braided crimson rope tied in an off-centre knot with tasselled ends;
- an eight-pointed silver seal round a black eclipse disc, with a red ofuda tag (abstract
  sigils, no real writing);
- white shide papers on the left hip;
- a silver chain to the right hip carrying a seal-kunai.

## Files

- **Scripts:** `tools/blender/ugc/eclipse_exorcist/`. `run_all.run(ref_dir)` rebuilds everything
  in about 80 s; it was checked from a clean Blender and reproduced the delivered meshes and
  counts.
- **Output:** `assets/ugc/EclipseExorcist/`: three FBX files, their maps, and `maps.json` (the
  uploaded map IDs).
- **Studio:** `ServerStorage.UGC_EclipseExorcist` holds the three Accessories (WrapLayer Order:
  hakama 3, robe 8, seal cord 10) and the raw imports.

## Tested in Studio (2026-11-02)

- On the owner's avatar (blocky R15, height 0.9, width 0.81) and on a default blocky dummy:
  standing, front and back, walking, mid-jump. Everything shows and follows the body. No errors.
- **The rigid seal cord failed on the owner's narrow body:** the robe swallowed it. Rebuilt as
  layered over the robe's cage; it now shows on both bodies.
- **Not verified:** Roblox's marketplace validation (only at upload), and fit on Rthro and other
  non-blocky bodies.
- **Test side effect:** the owner's saved outfit choice is now "no robes" (the Murim robes came
  off through the game's own OutfitEvent). The Robes button puts them back.

## To sell it

Upload each Accessory from Studio with the owner's UGC creator account (validation runs at
upload). Open question: the seal cord is set as a Jacket because Roblox has no layered belt type.

Related: [[Roblox Layered Clothing Pipeline]], [[Work in Progress]].
