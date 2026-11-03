---
type: reference
tags: [vfx, particles, smoke, textures, library]
created: 2026-11-03
---

# Smoke and Cloud Texture Library

The owner's collection of smoke textures (sent 2026-11-03, "save any of this smoke that might be
useful in future reference"). Every one was laid out on a contact sheet in Studio and judged by eye.
All are images (asset type 1), so the id goes straight into `ParticleEmitter.Texture` as
`rbxassetid://<id>`.

**Grids** are what the sheet showed: set `FlipbookLayout` to match, usually with `FlipbookMode =
OneShot` so each puff plays its life once. Every texture is white on black or transparent: tint it
with `Color`. Black backgrounds vanish with `LightEmission = 1`; for dark smoke, use a texture with
real transparency.

Related: [[Work in Progress]] (Realm 5 workbench), [[VFX AAA Technical Director]],
[[Egg Aura Studio Lessons]].

## Best picks

| Id | Grid | Looks like | Good for |
|---|---|---|---|
| 16867371255 | 4x4 | billowy cloud that swells, then thins out | clouds, cultivation steam, ground cloud |
| 13367803563 | 4x4 | ink-like smoke curling and dissolving | dark smoke, void and soul effects |
| 73138837979221 | 4x4 | detailed swirling smoke that breaks up | magical smoke round the body |
| 82029518693714 | 4x4 | white puff billowing out and dissolving | puffs, landings, dashes |
| 4510290214 | single | a soft, round cloud puff | soft clouds, glows, fog banks |
| 291880914 | single | a big fluffy billowing cloud | heavy clouds, explosions' smoke |
| 16172858603 | 4x4 | soft drifting wisp that flattens | ground mist |
| 13655845087 | 4x4 | thin smoke rings fading out | smoke ripples, shockwave rings |

## Everything else

**Single images**
- 883906867 (FireParticle3): spiky, wispy burst cloud; energy smoke.
- 12302665387 (Fog): a speckled, dusty ring of fog; dust haze.
- 92598900300299: swirling smoke with rainbow (chromatic) edges; magical, void.
- 83879596549256: chromatic wisps, sparse.
- 464840466 (Dust) and 90406562081887: nearly invisible at normal settings; only with high
  Brightness.

**4x4 flipbooks**
- 71355345702692: dark cloud puff. **In use:** the Realm 4 vortex cloud and the Realm 5 workbench
  ground cloud.
- 95274053372063: its sibling wisp, from the same set.
- 82126503991261: faint smoke wisps.
- 14641036736 (FLAME PARTICLE): small flame-like puff fading.
- 12360899465 (Flame burst): a puff that turns into a breaking ring; impacts.
- 16843373901: wispy puff fading.
- 124640421906932: smoke with orange and blue fringes; fire-lit smoke.
- 11989899750: jagged white smoke breaking up; sharp anime smoke.
- 16867394877: white puffs swirling and breaking; anime smoke.
- 74793282971768: a flat splash of dust (two rows used); ground impacts.
- 16867397491: curling crescent wisps; swirls.
- 16867399811: thin wispy tendrils, faint.
- 133237828327238: a blobby cartoon puff with hollows; cartoon style.
- 132491487897938: a round explosive cloud growing (three rows used); explosions.
- 16867490141: faint small wisps.
- 14919880888 (Galaxy_1): dim soft puffs; nebula.
- 13414392494 (Flame10): white flame-tongue puffs breaking; flames.
- 18456244650: thin vertical white streaks that flicker; sparks or tiny lightning more than
  smoke.

**2x2**
- 113983969948592: rainbow-edged crescent slashes; energy arcs, not smoke.

**8x8 flipbooks** (small cells: they read best at small sizes or when tinted strongly)
- 16503766653 (boto) and 16503783638 (bot33): round smoke puffs. 16503766653 is listed in the
  test range's textures (Realm 1) but unused.
- 11632052078 (Cartoony smoke): cartoon puff dissolving into rings.
- 11627083142 (exhausted): white puffs.
- 8073306083: small, faint smoke.
- 12779603482 (EnergyVFX41), 11447021694 and 11458438415 (EnergyVFX10), 11941047152 (EnergyVFX23):
  very faint wisps; they need high Brightness or stacking.
- 12683695494 (EnergyVFX40): **in use**, the owner's first vortex cloud (Realm 4).
- 12830011666 (EnergyVfx47): small puffs.
- 104492467711366 (erica_wave_thing): small horizontal glow waves, faint.

## Second batch (2026-11-03)

The owner also sent 16172858603 and 13655845087 again (both already above). The new ones:
- 11355816590 (mera flame hand), 4x4: sparkly flame-smoke puffs breaking into embers; fire-lit
  smoke, flame auras.
- 92517106717850, 2x2: smoke jets streaking sideways; dash trails, wind-blown smoke, speed
  lines.
- 9171263549 (punch), 8x8: small puffs that grow and dissolve; punch and landing impacts.
- 11597664950, 8x8: dense white puffs; thick small smoke, steam bursts.

**In use:** 16172858603 is now the Realm 5 workbench ground mist (`MyAura.GroundMist`).

## Also in use

- 7136551175 ("Circle2 Effect", kur_Dev), single image: a soft, wispy smoke ring; portal rings,
  halos. Now the Realm 5 workbench portals' main ring.
- 81684806845935 (Stelleariumm), 4x4: a soft spiral galaxy, a full swirl in every frame, so it
  can Loop; portals, galaxies, vortex cores. Now the Realm 5 portals' main ring.

## Notes

- 95274053372063 was sent twice; it is listed once.
- Grids were judged by eye from the sheet, not from pixel sizes: Roblox won't let us read the pixels
  of images we don't own. If a flipbook plays oddly (fragments, jumps), try the next grid size.
