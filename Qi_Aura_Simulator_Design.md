# Qi Aura Simulator — Game Design

**Platform:** Roblox · **Project:** `qi-aura-simulator` · **Last updated:** October 30, 2026

This is the single design reference for the game: concept, progression, pets,
eggs, world and technical rules. Exact numbers live in
`src/shared/GameConfig.lua` (ranks, pets, eggs) and `src/server/IslandConfig.lua`
(islands); the tables below were generated from them. Run
`python3 tools/balance_report.py` for the current pacing.

The aura VFX redesign brief is kept separately in
`Qi_Aura_Simulator_Aura_VFX_Brief.md`.

---

## 1. High concept

**Qi Aura Simulator** is an original Roblox cultivation simulator. Players train
their inner Qi, rise through 60 cultivation ranks, hatch and collect spirit
pets, and fly freely between floating islands. The fantasy is becoming a
powerful cultivator whose growing Qi shows in ever more impressive auras, with
a clear next goal at all times: more Qi, the next rank, a new pet or island.

### Design pillars

1. **Visible progression:** training, ranks and pets change stats *and* visuals.
2. **Collecting and discovery:** pets are rewards to find, hatch and improve.
3. **Freedom of movement:** flight makes the world worth exploring.
4. **Active and passive play:** cultivate anywhere, or at a training station for a bonus.
5. **Player expression:** the chosen aura pet sets the look of the aura.
6. **Fair, secure multiplayer:** the server validates every reward and rank-up.
7. **Original, maintainable work:** our own models, effects, UI and code.

### Core loop

1. **Cultivate** to earn Qi (more in the Qi Spring, more with pets).
2. **Rank up** when the next rank's Qi requirement is met (Qi is not spent).
3. **Unlock** flight speed, eggs, islands and relics as ranks rise.
4. **Hatch eggs** for pets; **equip three** for their Qi bonuses.
5. **Choose an aura pet** to style the aura.
6. Fly to new islands, find relics and better eggs, and repeat.

---

## 2. Cultivation

Twelve realms of five ranks each: 60 ranks. The fifth rank of every realm is a
milestone with a bigger breakthrough effect, and so is entering a new realm.

**Qi power:** from Spirit Soul on, every realm doubles the Qi each cultivation
reward gives (x2, x4 ... x512). This is what keeps the much larger late
requirements reachable; the HUD shows the current power (e.g. "Qi x32") and
abbreviates big numbers (2.18M, 4.18B).

| # | Realm | Qi power | Ranks (Qi needed) |
|---|---|---|---|
| 1 | Qi Awakening | x1 | Qi Initiate (0), Qi Gatherer (300), Qi Condenser (900), Qi Adept (2K), Qi Awakener (4K) |
| 2 | Qi Foundation | x1 | Foundation Initiate (6.5K), Foundation Builder (10K), Foundation Adept (15K), Foundation Master (21K), Perfect Foundation (29K) |
| 3 | Spirit Core | x1 | Core Initiate (40K), Core Formation (55K), Core Adept (72K), Core Master (95K), Golden Spirit Core (120K) |
| 4 | Spirit Soul | x2 | Soul Awakening (148K), Soul Tempering (234K), Soul Refinement (335K), Soul Manifestation (451K), Spirit Soul Master (582K) |
| 5 | Ascendant Realm | x4 | Ascendant Initiate (688K), Sky Ascendant (982K), Heavenly Adept (1.33M), Celestial Master (1.73M), Ascendant Sovereign (2.18M) |
| 6 | Immortal Realm | x8 | Lesser Immortal (2.5M), True Immortal (3.48M), Golden Immortal (4.63M), Immortal Lord (5.95M), Immortal Emperor (7.45M) |
| 7 | Divine Realm | x16 | Divine Initiate (8.46M), Divine Adept (11.4M), Divine Lord (14.9M), Divine King (18.9M), Divine Emperor (23.4M) |
| 8 | Cosmic Realm | x32 | Star Initiate (26.3M), Star Forger (34.5M), Nebula Master (44.2M), Galaxy Sovereign (55.3M), Cosmic Emperor (67.9M) |
| 9 | Void Realm | x64 | Void Walker (76.4M), Void Shaper (99.9M), Void Master (128M), Space-Time Lord (160M), Void Sovereign (196M) |
| 10 | Heavenly Dao | x128 | Dao Seeker (219M), Dao Adept (282M), Dao Master (357M), Heavenly Lawkeeper (443M), Dao Sovereign (540M) |
| 11 | Primordial Realm | x256 | Primordial Awakening (604M), Ancient Origin (785M), Primordial Lord (998M), Origin Emperor (1.24B), Primordial Sovereign (1.52B) |
| 12 | Eternal Transcendence | x512 | Eternal Initiate (1.7B), Eternal Ascendant (2.19B), Infinity Master (2.77B), Transcendent One (3.43B), Eternal Origin (4.18B) |

**Pacing** (typical pets, cultivating in the Qi Spring): Qi Awakening done in
about 4 minutes, Qi Foundation by about 25, Spirit Core by about 80 minutes,
and Eternal Origin after roughly 78 hours in total.

**Flight speed** grows with rank: it unlocks at Qi Gatherer (28 studs/s) and
reaches 70 at Golden Spirit Core, then rises at the start of every later realm
up to 165 at Eternal Initiate (walking is 16).

### Aura direction per realm

| Realm | Aura theme |
|---|---|
| Qi Awakening | Faint white or pale blue glow |
| Qi Foundation | Bright blue glow and small energy particles |
| Spirit Core | Swirling energy rings |
| Spirit Soul | Floating runes and a translucent spirit silhouette |
| Ascendant Realm | Golden energy, glowing trails, enhanced flight effects |
| Immortal Realm | Layered halos and luminous energy wings |
| Divine Realm | Violet lightning, floating sigils, powerful energy fields |
| Cosmic Realm | Orbiting stars and nebula-like particles |
| Void Realm | Dark energy, spatial distortions, teleport-like trails |
| Heavenly Dao | Celestial symbols, radiant rings, divine lightning |
| Primordial Realm | Ancient glyphs and enormous layered energy effects |
| Eternal Transcendence | Cosmic rings, shifting colours, a unique ultimate effect |

Today every realm shares the anime character aura (stronger with rank) and the
pet auras; the per-realm and per-element looks are the subject of the Aura VFX
brief.

---

## 3. Pets

Pets give **Qi bonuses** (all equipped pets) and **aura style** (the one chosen
aura pet). Players equip up to **three** and can own up to 50.

Rarities, commonest first: Common, Uncommon, Rare, Epic, Legendary, Mythical,
Secret. Rarer pets give more Qi, and pets from eggs that unlock later are
stronger too (about +6% per rank of the egg's required rank), so every new egg
is worth hatching.

All 60 pets from the original concept roster are in the game, plus the retired Nine-Tail Moonfox.
★ = hand-modelled in Blender (`tools/blender/pets/<EggId>/<PetId>.blend`, exported to
`assets/pets/<EggId>/`; a pet sits under the first egg that drops it). The others use
procedural low-poly models (`src/client/PetArchetypes.lua`) until they get their
own Blender model.

Every pet is its own species with its own anatomy, silhouette and face; no two
share a body plan or head design.

**Animated pets.** Sunscale Dragon is the first pet built as separate jointed
parts (exported with `export_pet.py --rig`) and animated in code by
`src/client/PetRig.lua`: idle, moving and flying poses, plus a special ability.
Specials play when the owner ranks up and every 25 seconds while cultivating.
Sunscale Dragon (a winged solar dragon in bronze, copper and gold scale armour,
a corona frill of gold blades behind its skull and a sun-fan at its tail tip)
walks on four legs, breathes its raised wings at rest and beats them in flight;
its special, **Solar Corona**, flares its wings and lifts its head as a sun forms
before it, throwing out a ring of rays, golden scale shards and a ground wave of
sunlight. Ember Wyrm (floating beads of lava rock
with flame gills) is animated the same way; its special, **Heart Flare**, spreads
its beads apart while its molten heart blazes. Bonefire Dragon (a floating
dragon skeleton with a blue soul flame burning in its ribcage) is animated too;
its special, **Soul Lantern**, makes the soul rise out of the ribs while the
ghost of the living dragon appears around the bones. Dreadfang Cerberus (a
hulking three-headed hellhound, its dark hide split by glowing cyan cracks) trots
on the ground, gallops in the air and moves each head on its own; its special,
**Hellfire Breath**, rears all three heads and blasts cyan fire from every mouth.
Golden Kirin (a white-furred qilin with branching antlers, a mane of teal cloud
curls and teal-scaled legs) treads the air on cloud steps and gallops when it
moves; its special, **Auspicious Clouds**, rears it up and throws off a ring of
cloud puffs and rising orange flames. Moss Golem (a hunched stone guardian grown over
with moss, ferns and a sapling, one boulder fist and one root claw) lumbers and
breathes; its special, **Groundbreaker**, slams both arms down, bursting a ring
of stone shards and an emerald shockwave from the ground. Mycelium Sprite (a
glowing mushroom spirit with a dripping cap and a lattice skirt) drifts and waves
its spore puffs; its special, **Spore Bloom**, scatters spores and a ring of glowing
mushrooms. Jade Spirit Panda (a stout jade guardian with leaf ears, dark-jade eye
patches and a crystal cluster on its back) ambles heavily; its special, **Jade
Lotus**, rears up and slams down, opening rings of jade lotus petals. Jade Antler
Deer (a slender celadon deer with branching jade antlers, a jade-leaf crest and
a jade breastplate) walks with a four-beat gait; its special, **Sacred Grove**,
rears it up and grows a ring of glowing jade branches from the ground. Dawn Phoenix
(an upright sunrise firebird with raised crimson-to-gold wings, a sunburst crest
and curling flame tail feathers) breathes its wings at rest, flaps in flight and
trails gold from both wingtips; its special, **Sunrise Rebirth**, flares its wings
and bursts a rising sun with rays and spiralling flame plumes. Rune Sphinx (a
charcoal feline guardian with a stone-blade mane, an obsidian horn crown and
glowing runes of one forgotten alphabet carved across its body) prowls with a slow,
judging gaze; its special, **Rune Seal**, raises its chest and opens a spinning
seal of rising rune glyphs and amber pillars. Magma Cub (a young volcanic beast on
huge basalt forearms, its molten core glowing through cracked chest plates and
molten seams across its shoulders and arms) knuckle-walks and tilts its head
curiously; its special, **Magma Pop**, winds up, slams both fists down and hops,
bursting basalt spikes and lava blobs out of a molten pool. Specials are visual
only.


**First found in the Beginner Qi Egg (starting island)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Aqua Wisp ★ | Common | Water | +10% |
| Ember Wyrm ★ | Uncommon | Fire | +20% |
| Lunar Hopper ★ | Rare | Moonlight | +35% |
| Volt Fox ★ | Epic | Lightning | +50% |
| Golden Kirin ★ | Legendary | Nature | +60% |
| Astral Whale ★ | Mythical | Cosmic | +100% |
| Origin Serpent ★ | Secret | Primordial | +150% |

**First found in the Jade Spirit Egg (Jade Grove)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Moss Golem | Common | Earth | +10% |
| Mycelium Sprite | Uncommon | Forest | +20% |
| Jade Spirit Panda | Rare | Nature | +35% |
| Jade Antler Deer | Epic | Nature | +50% |

**First found in the Inferno Egg (Ember Peak)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Magma Cub | Common | Lava | +10% |
| Sunscale Dragon ★ | Legendary | Solar | +60% |
| Dawn Phoenix | Legendary | Fire | +60% |

**First found in the Spirit Breeze Egg (starting island)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Wind Sprite | Common | Wind | +10% |
| Cloud Sheep | Uncommon | Clouds | +25% |
| Spirit Crane | Rare | Spiritual energy | +40% |
| Azure Sky Dragon | Epic | Wind and sky | +60% |
| Stormhorn Kirin | Legendary | Storms | +70% |

**First found in the Elemental Core Egg (starting island)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Glacier Puff | Common | Ice | +15% |
| Thunder Jelly | Uncommon | Electricity | +25% |
| Crystal Beetle | Rare | Crystal | +45% |
| Gravity Imp | Epic | Gravity | +65% |
| Thunderclaw Drake | Legendary | Lightning | +80% |
| Frostfang Serpent | Mythical | Ice | +130% |

**First found in the Bloomwood Egg (Jade Grove)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Dream Moth | Common | Dreams | +15% |
| Crystal Snail | Uncommon | Crystals | +30% |
| Prism Armadillo | Rare | Crystals | +50% |
| Lantern Warden | Epic | Light | +70% |
| Jade Wyrm Turtle | Legendary | Earth | +85% |

**First found in the Ancient Grove Egg (Jade Grove)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Echo Bat | Common | Sound | +15% |
| Qi Clockwork Finch | Uncommon | Magical machinery | +30% |
| Moonfang Tiger | Rare | Moonlight | +55% |
| Thousand-Eyed Guardian | Epic | Mysticism | +80% |
| Ninefold Spirit Serpent | Legendary | Spiritual energy | +95% |
| Worldroot Colossus ★ | Mythical | Ancient nature | +160% |

**First found in the Magma Heart Egg (Ember Peak)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Sand Phantom | Common | Sand | +15% |
| Solar Butterfly | Uncommon | Solar energy | +30% |
| Obsidian Guardian | Rare | Darkness and crystal | +55% |
| Golden Mane Lion | Epic | Solar energy | +75% |
| Bonefire Dragon ★ | Legendary | Spectral fire | +90% |

**First found in the Phoenix Ash Egg (Ember Peak)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Dreadfang Cerberus ★ | Epic | Shadow | +85% |
| Prismatic Phoenix ★ | Mythical | Rainbow energy | +170% |

**First found in the Celestial Egg (Moonlit Isle)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Starfall Fox | Common | Stars | +20% |
| Cosmic Jellyfish | Uncommon | Nebulae | +40% |
| Nebula Owl | Rare | Cosmic energy | +65% |
| Celestial Snow Leopard | Epic | Ice and celestial energy | +95% |
| Comet Stag | Legendary | Comets | +115% |
| Celestial Pearl Dragon | Mythical | Celestial energy | +190% |

**First found in the Astral Sanctum Egg (Moonlit Isle)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Eclipse Cat | Epic | Darkness and eclipses | +110% |
| Timekeeper Tortoise | Legendary | Time | +130% |
| Galaxy Manta | Mythical | Cosmic energy | +220% |

**First found in the Forbidden Origin Egg (Origin Abyss)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Shadowcoil | Rare | Shadow | +100% |
| Rune Sphinx ★ | Legendary | Ancient magic | +170% |
| Thousand-Year Dream Eater ★ | Mythical | Dreams | +280% |
| The Nameless One | Secret | Unknown cosmic energy | +420% |

**First found in the Void Rift Egg (Origin Abyss)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Heavenbreaker Ape ★ | Legendary | Heavenly power | +205% |
| Voidscale Hydra | Mythical | Void | +340% |

**First found in the Primordial Abyss Egg (Origin Abyss)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Eternal Clockwork Dragon ★ | Secret | Time | +600% |

Nine-Tail Moonfox (Mythical) no longer hatches; players who own one keep it.

---

## 4. Eggs

Fifteen eggs, **three on every island**, each needing a higher rank than the
last. Hatching is free with a 45-second cooldown per egg. Chances follow the
rarity scale (Common 45%, Uncommon 27%, Rare 15%, Epic 8%, Legendary 4%,
Mythical 0.9%, Secret 0.1%); when an egg has no pet of some rarity, its share
goes to the next pet that has one, so later eggs give rarer pets far more often.

| Island | Egg | Needs | Chances |
|---|---|---|---|
| Starting island | Beginner Qi Egg | Qi Initiate | Aqua Wisp 45%, Ember Wyrm 27%, Lunar Hopper 15%, Volt Fox 8%, Golden Kirin 4%, Astral Whale 0.9%, Origin Serpent 0.1% |
| Starting island | Spirit Breeze Egg | Qi Adept | Wind Sprite 45%, Cloud Sheep 27%, Spirit Crane 15%, Azure Sky Dragon 8%, Stormhorn Kirin 5% |
| Starting island | Elemental Core Egg | Foundation Initiate | Glacier Puff 45%, Thunder Jelly 27%, Crystal Beetle 15%, Gravity Imp 8%, Thunderclaw Drake 4%, Frostfang Serpent 1% |
| Jade Grove | Jade Spirit Egg | Qi Gatherer | Moss Golem 45%, Mycelium Sprite 27%, Jade Spirit Panda 15%, Jade Antler Deer 8%, Golden Kirin 5% |
| Jade Grove | Bloomwood Egg | Foundation Adept | Dream Moth 45%, Crystal Snail 27%, Prism Armadillo 15%, Lantern Warden 8%, Jade Wyrm Turtle 5% |
| Jade Grove | Ancient Grove Egg | Core Initiate | Echo Bat 45%, Qi Clockwork Finch 27%, Moonfang Tiger 15%, Thousand-Eyed Guardian 8%, Ninefold Spirit Serpent 4%, Worldroot Colossus 1% |
| Ember Peak | Inferno Egg | Qi Awakener | Magma Cub 45%, Ember Wyrm 50%, Sunscale Dragon 2.5%, Dawn Phoenix 2.5% |
| Ember Peak | Magma Heart Egg | Perfect Foundation | Sand Phantom 45%, Solar Butterfly 27%, Obsidian Guardian 15%, Golden Mane Lion 8%, Bonefire Dragon 5% |
| Ember Peak | Phoenix Ash Egg | Core Adept | Magma Cub 45%, Ember Wyrm 42%, Dreadfang Cerberus 8%, Sunscale Dragon 2%, Bonefire Dragon 2%, Prismatic Phoenix 1% |
| Moonlit Isle | Celestial Egg | Soul Awakening | Starfall Fox 45%, Cosmic Jellyfish 27%, Nebula Owl 15%, Celestial Snow Leopard 8%, Comet Stag 4%, Celestial Pearl Dragon 1% |
| Moonlit Isle | Astral Sanctum Egg | Ascendant Initiate | Starfall Fox 45%, Cosmic Jellyfish 27%, Nebula Owl 15%, Eclipse Cat 8%, Timekeeper Tortoise 4%, Galaxy Manta 1% |
| Moonlit Isle | Heavenly Throne Egg | Lesser Immortal | Celestial Snow Leopard 47.5%, Eclipse Cat 47.5%, Comet Stag 2%, Timekeeper Tortoise 2%, Celestial Pearl Dragon 0.5%, Galaxy Manta 0.5% |
| Origin Abyss | Forbidden Origin Egg | Divine Initiate | Shadowcoil 87%, Eclipse Cat 8%, Rune Sphinx 4%, Thousand-Year Dream Eater 0.9%, The Nameless One 0.1% |
| Origin Abyss | Void Rift Egg | Void Walker | Shadowcoil 87%, Eclipse Cat 8%, Heavenbreaker Ape 4%, Voidscale Hydra 0.9%, The Nameless One 0.1% |
| Origin Abyss | Primordial Abyss Egg | Primordial Awakening | Heavenbreaker Ape 99%, Voidscale Hydra 0.45%, Thousand-Year Dream Eater 0.45%, Eternal Clockwork Dragon 0.05%, The Nameless One 0.05% |

### Egg designs

Modelled in Blender (`tools/blender/eggs/Eggs.blend`, preview
`tools/blender/eggs/Eggs_preview.png`) after the concept art, exported to
`assets/eggs/<EggId>.fbx`. Each island has one design family; the second egg
adds a jewelled gold band and the third a crown and floating halo.

| Island | Design |
|---|---|
| Starting island | Pearl egg wrapped in leafy vines, glowing Qi swirl on the front |
| Jade Grove | Faceted crystal egg held by golden roots with flowers, glowing leaf emblem |
| Ember Peak | Dark volcanic plates with lava glowing through the cracks, flame emblem, crystals at the base |
| Moonlit Isle | Porcelain egg with gold filigree, glowing star inlay, small wings and an orbiting gold ring |
| Origin Abyss | Obsidian plates cracked with void light, spiral void core, thorny bronze branches |

In the game each stand shows its egg's Blender model once it has been imported
into `ServerStorage.EggMeshes` (named by egg ID); until then a glowing
placeholder egg stands in.

---

## 5. World

Five floating islands, reached by flying:

| Island | Where | Feel | Relics |
|---|---|---|---|
| Starting island | Centre | Grassy spawn, Qi Spring training station | Root of the Island (300 Qi) |
| Jade Grove | East | Forest | 3 relics, 800 Qi each, from Qi Gatherer |
| Ember Peak | South-west | Volcanic, lava pools | 3 relics, 1,500 Qi each, from Qi Awakener |
| Moonlit Isle | Highest | Pale and celestial | 2 relics, 3,000 Qi each, from Foundation Initiate |
| Origin Abyss | Far north-west, below the others | Hidden endgame: dark slate, void crystals and rifts, broken ruins | Origin Altar (250K Qi, from Divine Initiate), Void Shard high above it (1M Qi, from Void Walker) |

The **Qi Spring** on the starting island adds +50% Qi while cultivating in it.
**Spirit Relics** give a one-time Qi reward each; finds are saved.

---

## 6. Auras and effects

- **Character aura:** an anime aura (flames, energy tongues, rings, ground
  shockwaves, lightning, floating rocks) that charges up, then grows from idle
  to charged to awakened the longer the player cultivates. Coloured by the aura
  pet's element (`src/client/CharacterAura.lua`). Aqua Wisp has its own aura,
  **Tidecaller Sanctum** (`src/client/TidecallerAura.lua`): the player meditates
  on a blooming water lotus inside a tidal vortex over a pool of caustic light;
  spirit koi join at the charged stage, and a breaking-wave crown and four water
  spouts rise when awakened. Ember Wyrm has **Ember Crucible**
  (`src/client/EmberCrucibleAura.lua`): ember slashes and cloud spin under the
  player while debris, sparkles, energy beams and body flames rise around them;
  the spirit bead wyrm and orbit trails join at the charged stage, and a molten
  fire halo forms behind the head when awakened.
- **Pet auras:** each equipped pet of a cultivating player shows its own
  element's aura (`src/client/AuraBuilder.lua`); Aqua Wisp and Golden Kirin are
  done so far.
- **Poses:** a lotus pose while cultivating and a flying pose in flight.
- **Breakthroughs:** a burst effect on every rank-up, bigger at milestones.

Next step: give every element its own aura concept (water for Aqua Wisp, and
so on) per `Qi_Aura_Simulator_Aura_VFX_Brief.md`.

---

## 7. Technical architecture

Roblox Studio + Rojo 7.7.1 (VS Code, Git). Rojo maps `src/shared` to
ReplicatedStorage, `src/server` to ServerScriptService and `src/client` to
StarterPlayerScripts. Blender 5.2 models pets, eggs and VFX pieces;
`tools/blender/export_pet.py` exports them as FBX for Studio's 3D Importer
(imported models live in `ReplicatedStorage.PetMeshes/<EggId>`, `ReplicatedStorage.AuraMeshes`
and `ServerStorage.EggMeshes`). Aura sources are in `tools/blender/auras`.

**Server** owns Qi rewards, rank-ups, hatching, inventory, relics, flight
permission and saving. **Clients** handle UI, auras, effects, pet companions,
input and flight movement. **Shared** config holds ranks, pets and eggs. The
server never trusts the client for Qi amounts, ranks, hatch results or inventory.

### Data and security

- Validate every important action on the server.
- Save with Roblox data stores; old saves are migrated automatically.
- Test multiplayer, rejoining and invalid requests, not just the happy path.
- No secrets in source control; avoid third-party asset packs.

---

## 8. Future and open decisions

- **Stealing or raids:** only ever as an opt-in, server-checked system with
  protected pets, cooldowns and clear warnings. Not planned yet.
- **Monetization:** cosmetic-first, never pay-to-win; no paid eggs or random
  rewards until Roblox's policies are checked.
- Per-element and per-realm aura looks (Aura VFX brief).
- Blender models for the procedural pets.
- Balance tuning from playtests.

**North star:** an original cultivation simulator where training, pet
collection, visible aura progression and free flight form one satisfying loop,
built in small, secure, testable steps.
