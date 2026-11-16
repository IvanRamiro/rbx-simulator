---
type: concept
tags: [pet, dawn-phoenix, references, blender]
updated: 2026-11-16
---

# Dawn Phoenix Reference Board

The references, the design and the echo check behind the Dawn Phoenix ("The First Light", Mythical, Inferno Egg). The owner's governing brief is
[[Dawn Phoenix Directive]]; the build status is in [[Work in Progress]]; the game facts are in [[Qi_Aura_Simulator_Design]].

## History of the design

- **First draft, rejected (2026-11-16).** A round, kestrel-based hovering firebird with big eyes and a fan tail. The owner, verbatim: "That ain't a
  phoenix, that's a freaking bird". Lesson: a chubby, plush, big-eyed body reads as a cartoon bird whatever its colours; a phoenix needs an
  elegant, mythical silhouette (long neck, long flowing tail, great wings, a crest). Its scratch renders are in
  `renders/pets/InfernoEgg/DawnPhoenix_stages/rejected_v1/`.
- **Current design:** built to the directive: a physical creature, flame-INSPIRED shapes and a sunrise palette, no literal fire.

## References (studied, not copied)

Body and anatomy:
- Kestrel hovering, the windhover (Commons photo kept for study at `renders/pets/InfernoEgg/DawnPhoenix_refs/kestrel_hover_1.jpg`,
  https://commons.wikimedia.org/wiki/Category:Falco_tinnunculus_in_flight): a raptor's head and hooked beak, primaries parting into fingers,
  the tail fanned for lift, legs let down.
- Kestrel wing and tail morphing study (RMIT/Bristol 2024, https://www.scimex.org/newsfeed/steady-flight-of-kestrels-could-help-aerial-safety-soar):
  the head held still while wings and tail work (for the animation pass).
- Bird wing mechanics (downstroke for lift, upstroke folding at the wrist, slotted wingtips): https://pmc.ncbi.nlm.nih.gov/articles/PMC5454299,
  https://s2.smu.edu/propulsion/Pages/flapping.htm.
- Resplendent quetzal: tail coverts about twice the body length
  (https://www.earth.com/animal-encyclopedia/Chordata/Trogonidae/pharomachrus-mocinno/en/): the proportion of the long central tail feathers.
- Northern cardinal crest (raised and lowered at will, a mood signal: https://www.birdnote.org/node/16277): a crest that is a feather, and can move.
- Himalayan monal crest (spatulate wire crest): looked at only to avoid the Prismatic Phoenix's ball-tipped crest language.

Mythology and motif:
- Bennu and the phoenix of Heliopolis: sun, creation and rebirth (https://en.wikipedia.org/wiki/Bennu); the self-burning nest is a later addition.
- Sunrise palettes: rose, coral, peach and gold bands (https://piktochart.com/tips/sunrise-color-palette); the directive's palette took precedence.

Game creature art (silhouette and appeal only):
- Stylised phoenix and firebird concept roundups (https://conceptartempire.com/phoenix-artwork/); 80.lv phoenix breakdowns (individual feathers,
  each different: https://80.lv/articles/recreating-phoenix-from-harry-potter-with-zbrush-ornatrix-substance-3d-painter/).

## The design, in plain words

- **Idea:** the bird that brings the first sunrise: the night going out of its feather roots and the sun coming up at their ends.
- **Silhouette:** a slender body pitched up as a bird's is in flight; a long neck in an S carrying a small, sleek head high; enormous wings held
  slightly extended and raised (wingspan 2.17x beak-to-tail-base); a long tail flowing down and sweeping up at its end, its two central feathers
  longest; a crest of flame-shaped feathers streaming back off the skull. It reads as a phoenix in black silhouette from the side, the top and at
  game distance.
- **Shape language:** long tapered S-curves and flame-shaped (waved, drawn-out) feathers; no spikes, no plates, no rounds.
- **Face:** a raptor's skull made noble: a raised forehead sloping into a deep, hooked beak in two parts, hard brow ridges over amber-gold eyes
  with calm lids. Intelligent, not fierce, not cute.
- **Palette (the directive's):** deep crimson, burnt orange and warm amber as the primaries; golden yellow, pale gold, cream and ivory as the
  secondaries; champagne, peach and pale yellow as highlights. Head warm golden orange, crest going to crimson at its tips; neck rich orange with
  golden layers; chest cream and champagne; body amber and burnt orange; wings crimson at the outer primaries, burnt orange across the flight
  feathers, golden amber in the coverts, pale gold on chosen tips; tail crimson at the root to pale yellow at the tips; legs and talons dark bronze.
- **Personality:** noble, proud, graceful, intelligent (for the animation pass, after the model is approved).

## Echo list: what it could have copied, and what it does instead

| Built pet | Its language | The Dawn Phoenix instead |
|---|---|---|
| Prismatic Phoenix (Mythical, the other phoenix) | rainbow bands, wings spread flat, a gold halo ring, a wire crest with ball tips, a fan of streamers ending in eye-gems | one sunrise gradient, wings raised and layered, no halo, a crest of flame-shaped blades, a flowing tail of true feathers with pale-gold tips, no eye-spots or gems |
| Old Dawn Phoenix (its own old model) | upright on long legs, wings raised in a V, a sunburst fan crest, curling streamer tail, wingtip trails | a flying pose with legs let down, wings slightly extended, a swept-back crest, a long S-tail; no trails or effects |
| Spirit Crane | tall pearl crane, long straight beak, lotus crown with three plumes, pearl palette | a hooked raptor beak, a flame crest, warm palette |
| Nebula Owl | wide dished face, huge gold eyes, cosmic gas feathers | a narrow raptor skull, calm amber eyes under hard brows, sunrise plumage |
| Qi Clockwork Finch | enamel plates, gilt beak in two halves, a key | soft layered feathers, a horn-gold hooked beak |
| Echo Bat | plush round fruit bat, trumpet ears | slender, no ears |
| Eclipse Dreadwing | four-legged raven-drake, glossy faceted black-violet feathers, horns | two-legged bird, soft warm feathers, no horns |
| Sunscale Dragon / Azure Sky Dragon | scaled dragons, frills, membrane wings | a feathered bird, no scales or frills |
| Solar Butterfly | stained-glass wings gold to red, sun-disc eyespots | feathered wings, no eyespots |
| Magma Cub, Ember Wyrm, Obsidian Guardian (its egg-mates) | basalt and magma cracks, campfire tail, knapped glass | no cracks, no literal fire, no glass |
| Golden Kirin | a sunburst arc behind the head | no halo or arc |

## How it was built (the directive's stages)

`tools/blender/pets/dawn_phoenix.py`, stages blockout, anatomy, wings, feathers, materials, final. Stage files
`tools/blender/pets/InfernoEgg/Dawn_Phoenix_{Blockout,Anatomy,Wings,Final}.blend`; stage renders in
`renders/pets/InfernoEgg/DawnPhoenix_stages/` (with every earlier round in `iterations/`); the QA set in `renders/pets/InfernoEgg/DawnPhoenix_final/`.

Rounds that mattered: blockout 1 (flat wings vanished front-on: raised them 30 degrees, blunt secondaries); wings 2 (a muzzle and a tube beak read
as a llama: forehead sloping into a deep hooked beak; coverts floated off the wing: lifts cut); wings 3 (crest blades lay flat, and splayed side
feathers read as goat ears: blades on edge, sides removed); paint 1 (pale mask, googly eyes, a nose-coloured beak, an egg-white chest: all toned
down); game 1 (black torn patches on the wings from the ray bake: feathers painted straight into their UV islands; a 423-triangle head melted its
brows: the head kept through the reduction and subdivided once); head 2 (eyes too big and bulging: smaller, set in under a hard brow).

## The model as delivered for approval (2026-11-16)

Files: `tools/blender/pets/InfernoEgg/Dawn_Phoenix_{Blockout,Anatomy,Wings,Final}.blend`; FBX and maps in `assets/pets/InfernoEgg/DawnPhoenix_Model/`
(kept apart from the live pet's `DawnPhoenix.fbx` until approval and rigging); QA renders in `renders/pets/InfernoEgg/DawnPhoenix_final/`.

- **Triangles: 19,136** (evaluated, triangulated, every piece; limit 20,000; about 1,100 over the 16-18k target, spent on the head and on
  smoother neck and breast feathers). Body 1,992, Neck 1,277, Head 2,459, BeakUpper 316, BeakLower 156, EyeL/EyeR 234 each, LidUpperL/R 196
  each, LidLowerL/R 100 each, Crest 528, NeckFeathers 1,536, Chest 792, BodyFeathers 944, LeftWing/RightWing (arm structure) 256 each,
  LeftWingFeathers/RightWingFeathers 2,504 each (95 feathers a wing), Legs 888, Talons 448, TailFeathers 1,220.
- **Size:** wingspan 1.69 m, beak tip to tail base 0.81 m: ratio 2.09 (the directive asks 2.0-2.4); 1.23 m tall; its talons on the ground (z = 0).
- **Material:** one, `DawnPhoenix_Plumage` (Principled: colour, normal, roughness). Maps: colour 2048 (sRGB), normal 1024 and roughness 1024
  (non-colour). No metalness, no emission, no transparency. The skin, eyes, beak, legs and talons are baked from the painted sculpt; every feather is
  painted straight into its own UV islands from its own place (the ray bake caught the wrong layer through stacked feathers).
- **Hierarchy:** DawnPhoenix_Root (empty) > Body > { Neck > { Head > { BeakUpper, BeakLower, EyeL, EyeR, LidUpperL, LidUpperR, LidLowerL,
  LidLowerR, Crest }, NeckFeathers }, Chest, BodyFeathers, LeftWing > LeftWingFeathers, RightWing > RightWingFeathers, Legs > Talons,
  TailFeathers }. Every transform the identity, the origin on the ground under it.
- **QA (blender-asset-qa, profile roblox): PASS, 0 errors.** Accepted warnings: open boundaries by design (each feather is two unjoined sheets;
  the skin is cut into Head, Neck and Body under the neck's feathers; the eyes' hidden backs and the lids are open); 78 hidden back-to-back face
  pairs where a feather's underside lies on another piece (194 since the polish: the feathers now overlap properly). Z-fighting 0 after the
  separating pass. Nothing floating or
  enclosed; no n-gons, degenerate faces or duplicate vertices; UV overlap 0.

### QA checklist (the directive's section 13)

- [x] Original phoenix identity (see the echo list).
- [x] Proper avian anatomy.
- [x] Distinctive skull and beak (head-on, a raptor's beak still reads long: see the limits).
- [x] Expressive golden eyes.
- [x] Unique flame-inspired feather crest.
- [x] Proper neck and chest construction (layered feathers; the cream breast blends through amber and gold rows into a pale throat).
- [x] Streamlined torso.
- [x] Two structurally complete wings (one broad, layered surface each, after the polish round).
- [x] Layered primary and secondary feathers.
- [x] Proper coverts.
- [x] Anatomically believable legs.
- [x] Properly constructed talons.
- [x] Elegant multi-feather tail.
- [x] Sophisticated sunrise colour palette.
- [x] No repetitive or generic feather geometry (each feather its own length, angle and lift; the blades share one profile per kind).
- [x] No floating parts.
- [x] No major intersections.
- [x] Clean normals.
- [x] Below 20,000 triangles.
- [x] Suitable for Roblox export: not yet imported into Studio, so the import itself is unverified.

### Polish round (2026-11-16, the coordinator's review: "not AAA yet")

| Asked | Before | After |
|---|---|---|
| Wings read as combs or rakes | narrow feathers fanned far apart, alternate slat tilts (a louvre), one plane seen edge-on front and back | wider feathers overlapping by a third to a half in every row, fingers only at the outer four primaries, a continuous trailing edge, coverts closing the leading half, steady stacking instead of tilts; the wing raised 40 degrees and twisted along its length (inner wing +34 degrees, hand -24 degrees, as a bird's is), so it shows area from the front, back, three-quarter and a player's camera |
| Tail tip folded into a flat hook | the feather's frame measured against one fixed up, which flipped where the tip curled toward it | a frame carried along the curve (no flip); a gentler end lift; the central pair sway together (apart, they closed into a loop from behind) |
| Chest a pale oval pasted on | a cream patch with hard edges | amber warming to gold to cream over several rows, a pale throat running down into it, the breast's sides in shade; free feather edges lighter, never darker |
| Faceted feathers, dark slivers | 3 steps a feather, dark skin in the gaps | fewer, larger body feathers; 6 steps on the neck and breast; the skin under them no longer darkened |
| Head front: long beak, wide eyes | the lower beak ran out past the hook (a lip) | eyes a little closer and more forward, a broader beak base with a darker ridge, the lower beak tucked under the hook |
| Game distance a stick figure | thin wings, framed at 45 studs | broad warm wings; a player's view at 25 studs added (10_game_distance_25studs) beside the 45-stud one |

The before set is kept in `renders/pets/InfernoEgg/DawnPhoenix_stages/iterations/final_before_polish/`.

### Limits, stated plainly

- Head-on the face is better but still the weakest view: the hook's dark tip reads a little like a nose tip.
- From dead front the breast is still the palest, roundest shape on it (it is meant to be cream), though it now blends into the throat and flanks.
- The feathers are flat blades with painted vanes, not modelled vanes; the wing coverts up close are visibly separate cards.
- 19,136 triangles: under the limit, but over the 16-18k target.
- The wings extended and folded in the QA renders use a temporary review skeleton, not the creature's rig, which comes after approval.
- The colour map (`DawnPhoenix_color.png`) is an atlas of many small feather shapes. The owner should look at it before importing, since the
  import uploads it.
