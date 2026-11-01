# Qi Aura Simulator — Game Design

**Platform:** Roblox · **Project:** `qi-aura-simulator` · **Last updated:** October 31, 2026

The single design reference for the game: what is fixed, what is built, and what comes next.
Exact numbers live in code and data, and the tables below are generated from them:

- `src/shared/GameConfig.lua`: ranks, Qinggong, pets, eggs and relics.
- `tools/blender/world/layout.py`: island positions and Qinggong routes.
- `python3 tools/balance_report.py`: the current pacing.

---

## 0. Fixed directives

These never change without an explicit decision from the project owner.

- **Ranks** stay as designed (section 2).
- **Eggs** stay as designed: their pets, pools, chances and themes (section 5).
- **No mistakes.** Every pet, egg, island and effect is checked against this document before it is built. For a pet, that means its egg, rarity and theme.
- **Every pet has expressive eyes.**
- **Aura concept** stays as designed (section 4). The bar is not "looks like Sol's RNG": it is to genuinely compete with, and aim to surpass, Sol's RNG's most impressive auras.
- **No generic style.** Islands, pets and effects are original Blender work with their own silhouette and identity. Nothing is a recoloured copy of another piece.
- **Weapons:** players purchase or request a **forged weapon**, and their Qi mastery decides which weapons they can get.
- **Sword flight:** a sword can also be ridden for flight. It is the only free flight in the game; everywhere else, players move with Qinggong.

---

## 1. Concept

**Qi Aura Simulator** is an original Roblox cultivation action-adventure.

- **Qi** is power: players cultivate it to rise through 60 ranks.
- **Qinggong** is mobility: martial-arts leaps that carry players between floating islands.
- **Pets** are spirit companions that strengthen cultivation and style the aura.

The fantasy is becoming a cultivator whose growing power shows in ever more spectacular auras and movement. There is always a clear next goal: the next rank, the next island, a new pet.

### Design pillars

1. **Visible progression:** ranks, Qinggong and pets change stats *and* visuals.
2. **Movement as mastery:** a bridge leads from the Starting Island to each other island, sealed by a Qi barrier that only opens at the island's unlock rank. Players run, leap with Qinggong or (later) ride the sword along it. Qinggong's air leaps reach the high places on the islands.
3. **Collecting and discovery:** pets, relics and hidden places reward exploration.
4. **Active and passive play:** cultivate anywhere, or at the Qi Spring for a bonus.
5. **Player expression:** the chosen aura pet sets the look of the aura.
6. **Fair, secure multiplayer:** the server validates every reward, rank-up and hatch.
7. **Original, maintainable work:** our own models, effects, UI and code.

### Core loop (built)

1. **Cultivate** to earn Qi. The Qi Spring and equipped pets increase it.
2. **Rank up** when the next rank's Qi requirement is met. Qi is not spent.
3. **Unlock** more air leaps, eggs, islands and relics as ranks rise.
4. **Hatch eggs** for pets and **equip three** for their Qi bonuses.
5. **Choose an aura pet** to style the aura.
6. Qinggong to new islands, find relics and better eggs, and repeat.

### Core loop (planned): guardians and egg theft

Defeating a guardian is not the goal. **Stealing its egg and escaping with it is.**
Cultivate → train Qinggong → find an island's guardian → weaken it → steal the egg →
escape the enraged pursuit → secure the egg at a safe zone → hatch it → grow stronger.
See section 7 for the full design.

---

## 2. Cultivation

Twelve realms of five ranks each: 60 ranks. The fifth rank of every realm is a milestone with a bigger breakthrough effect, and so is entering a new realm.

**Qi power:** from Spirit Soul on, every realm doubles the Qi each cultivation reward gives (x2, x4 ... x512). This keeps the much larger late requirements reachable. The HUD shows the current power (for example "Qi x32") and abbreviates big numbers (2.18M, 4.18B).

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

**Pacing** (typical pets, cultivating in the Qi Spring):

- Qi Awakening is done in about 4 minutes.
- Qi Foundation by about 25.
- Spirit Core by about 80 minutes.
- Eternal Origin after roughly 78 hours in total.

### Qinggong

Qinggong is martial-arts movement through the air.

- **Air leaps:** players jump, then leap again in mid-air, once per air leap.
- **Glide:** hold jump while falling to glide.
- **Recharge:** leaps refill on landing.
- **Rank:** air leaps and run speed grow with rank, at the ranks that open new islands.

| Rank | Air leaps | Run speed | Opens |
|---|---|---|---|
| Qi Initiate | 1 | 22 | Starting Island |
| Qi Gatherer | 2 | 24 | Jade Grove |
| Qi Awakener | 3 | 26 | Ember Peak |
| Foundation Initiate | 4 | 28 | Moonlit Isle |
| Perfect Foundation | 5 | 30 | — |
| Divine Initiate | 6 | 32 | Origin Abyss |
| Void Walker | 7 | 34 | The Void Shard above Origin Abyss |

Measured reach with Roblox gravity:

| Air leaps | Flat reach | Peak height |
|---|---|---|
| 1 | 31 studs | 14 studs |
| 2 | 50 | 21 |
| 3 | 71 | 28 |
| 4 | 97 | 34 |
| 5 | 124 | 41 |
| 6 | 153 | 48 |
| 7 | 187 | 55 |

The islands were first linked by floating stepping stones tuned to each rank's leaps; on November 1, 2026 the owner replaced them with bridges (section 6), since the stones made the islands too hard to reach.

**Leap effects** (`src/client/QinggongFx.lua`): the cultivator rides a current of Qi rather than simply jumping.

| Moment | Effect |
|---|---|
| Takeoff (jump from the ground) | A Qi formation blooms over a turning vortex under the feet, with rising wind streaks and puffs of auspicious cloud |
| Air leap | The foot steps on the void: a small formation, a vortex and a ripple ring open, clouds burst from the step and linger, streaks shoot downward |
| Rising after a leap | Energy trails from the feet, a silk ribbon from the shoulders, a current of Qi spiralling round the body. The legs stride like climbing steps in the air: the driving knee thrusts up while the other leg pushes off, arms swinging opposite, then both knees tuck. The legs alternate: the ground jump drives the right knee, the first air leap the left, the second the right, and so on |
| Glide | Riding a cloud: clouds held under the feet, small wisps shed behind, wind lines rushing past; crane-stance glide pose |
| Landing | A starburst flare, a formation flash, two shockwave rings, sharp Qi spikes, rolling cloud and glittering Qi mist, scaled by impact speed |

- The colour follows the realm: azure (Qi Awakening, Qi Foundation), jade (Spirit Core, Spirit Soul), gold (Ascendant, Immortal), violet (Divine and above).
- Textures (formation, shockwave, cloud sheet, spike, streak, ribbon) are drawn by `tools/blender/vfx/qinggong_textures.py`. The cloud sheet holds four auspicious-cloud shapes; each particle picks one.
- From the PDS' Particles & Models Kit: a soft fog puff gives every cloud burst and the riding cloud their volume (the line-drawn clouds ride on a bank of it), plus a vortex under the formations, a starburst flare and glittering Qi mist at landing.
- Effects play at once for the player and are relayed by the server to everyone else (cosmetic only, rate-limited); other players' effects are skipped beyond 250 studs and use fewer particles.

**Planned:** directional dashes and Qinggong stamina; sword flight (section 0).

---

## 3. Pets

Pets give **Qi bonuses** (every equipped pet) and **aura style** (the one chosen aura pet). Players equip up to **three** and own up to 50.

**Rarities**, commonest first: Common, Uncommon, Rare, Epic, Legendary, Mythical, Secret.

- Rarer pets give more Qi.
- Pets from eggs that unlock later are stronger too, about +6% per rank of the egg's required rank, so every new egg is worth hatching.

**Roster:** all 60 pets from the original concept are in the game, plus the retired Nine-Tail Moonfox.

- **★ = sculpted in Blender:** source at `tools/blender/pets/<EggId>/<PetId>.blend`, exported to `assets/pets/<EggId>/`. A pet sits under the first egg that drops it.
- **Unmarked pets** use procedural low-poly models (`src/client/PetArchetypes.lua`) until they get their own Blender model.
- **Every pet is its own species**, with its own anatomy, silhouette and face. No two share a body plan or head design, and every pet has expressive eyes.

### Animated pets and their specials

**How they're built**

- Animated pets are exported as separate jointed parts (`tools/blender/export_pet.py --rig`).
- Each one is animated in code by `src/client/PetRig.lua`, with an idle pose, a moving pose, a flying pose and a special.

**When specials play**

- When the owner ranks up.
- Every 25 seconds while the owner cultivates.

Specials are visual only.

| Pet | Look and motion | Special |
|---|---|---|
| Sunscale Dragon | Winged solar dragon in bronze, copper and gold scale armour, a corona frill of gold blades and a sun-fan tail tip; walks on four legs, breathes its raised wings at rest and beats them in flight | **Solar Corona:** flares its wings and lifts its head as a sun forms before it, throwing out a ring of rays, golden scale shards and a ground wave of sunlight |
| Ember Wyrm | Floating beads of lava rock with flame gills | **Heart Flare:** its beads spread apart while its molten heart blazes |
| Bonefire Dragon | Floating dragon skeleton with a blue soul flame in its ribcage | **Soul Lantern:** the soul rises out of the ribs while the ghost of the living dragon appears around the bones |
| Dreadfang Cerberus | Hulking three-headed hellhound, dark hide split by glowing cyan cracks; trots on the ground, gallops in the air, each head moves on its own | **Hellfire Breath:** rears all three heads and blasts cyan fire from every mouth |
| Golden Kirin | White-furred qilin with branching antlers, a mane of teal cloud curls and teal-scaled legs; treads the air on cloud steps | **Auspicious Clouds:** rears up and throws off a ring of cloud puffs and rising orange flames |
| Moss Golem | Hunched stone guardian grown over with moss, ferns and a sapling, one boulder fist and one root claw; lumbers and breathes | **Groundbreaker:** slams both arms down, bursting stone shards and an emerald shockwave |
| Mycelium Sprite | Glowing mushroom spirit with a dripping cap and a lattice skirt; drifts and waves its spore puffs | **Spore Bloom:** scatters spores and a ring of glowing mushrooms |
| Jade Spirit Panda | Stout jade guardian with leaf ears, dark-jade eye patches and a crystal cluster on its back; ambles heavily | **Jade Lotus:** rears up and slams down, opening rings of jade lotus petals |
| Jade Antler Deer | Slender celadon deer with branching jade antlers, a jade-leaf crest and a jade breastplate; four-beat gait | **Sacred Grove:** rears up and grows a ring of glowing jade branches from the ground |
| Dawn Phoenix | Upright sunrise firebird with raised crimson-to-gold wings, a sunburst crest and curling flame tail feathers; trails gold from both wingtips | **Sunrise Rebirth:** flares its wings and bursts a rising sun with rays and spiralling flame plumes |
| Rune Sphinx | Charcoal feline guardian with a stone-blade mane, an obsidian horn crown and glowing runes of one forgotten alphabet; prowls with a slow, judging gaze | **Rune Seal:** raises its chest and opens a spinning seal of rising rune glyphs and amber pillars |
| Magma Cub | Young volcanic beast on huge basalt forearms, molten core glowing through cracked chest plates; knuckle-walks and tilts its head | **Magma Pop:** winds up, slams both fists down and hops, bursting basalt spikes and lava blobs out of a molten pool |
| Azure Sky Dragon | Lean upright sapphire wyvern with silver crest blades, crystal-studded wings with crescent tips, wind ribbons and a layered tail fan; strides on two legs | **Skyburst:** spreads its wings and throws up three rising wind spirals, gust rings and sky-crystal shards |
| Spirit Crane | Tall pearl-and-silver celestial crane, misty slate flight feathers, three pearl plumes from a turquoise lotus crown, gold eyes ringed in turquoise, spiralling tail streamers | **Halo Ascension:** lifts its neck skyward as three luminous rings rise from feet to crown and burst into drifting pearl feathers |
| Cloud Sheep | Satin celestial sheep under a mantle of scroll-curl clouds, a breaking-wave forelock, ivory-to-sky ribbon horns, heavy-lidded sky-blue eyes; hovers and paddles its hooves | **Cloud Bloom:** lifts with its legs tucked and blooms a ring of cloud puffs while luminous droplets rain onto a widening sky ring |
| Golden Mane Lion | High-shouldered royal lion, a tiered mane of flame-tipped locks in bronze, gold and champagne, a crest of reddish-gold locks, deep-set amber eyes; heavy, deliberate stride | **Sovereign Roar:** opens its jaw as golden shockwave rings roll out, solar rays flare behind its crest and a ring spreads beneath its paws |

### Roster by first egg

**Beginner Qi Egg (Starting Island)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Aqua Wisp ★ | Common | Water | +10% |
| Ember Wyrm ★ | Uncommon | Fire | +20% |
| Lunar Hopper ★ | Rare | Moonlight | +35% |
| Volt Fox ★ | Epic | Lightning | +50% |
| Golden Kirin ★ | Legendary | Nature | +60% |
| Astral Whale ★ | Mythical | Cosmic | +100% |
| Origin Serpent ★ | Secret | Primordial | +150% |

**Spirit Breeze Egg (Starting Island)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Wind Sprite | Common | Wind | +10% |
| Cloud Sheep ★ | Uncommon | Clouds | +25% |
| Spirit Crane ★ | Rare | Spiritual energy | +40% |
| Azure Sky Dragon ★ | Epic | Wind and sky | +60% |
| Stormhorn Kirin | Legendary | Storms | +70% |

**Elemental Core Egg (Starting Island)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Glacier Puff | Common | Ice | +15% |
| Thunder Jelly | Uncommon | Electricity | +25% |
| Crystal Beetle | Rare | Crystal | +45% |
| Gravity Imp | Epic | Gravity | +65% |
| Thunderclaw Drake | Legendary | Lightning | +80% |
| Frostfang Serpent | Mythical | Ice | +130% |

**Jade Spirit Egg (Jade Grove)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Moss Golem ★ | Common | Earth | +10% |
| Mycelium Sprite ★ | Uncommon | Forest | +20% |
| Jade Spirit Panda ★ | Rare | Nature | +35% |
| Jade Antler Deer ★ | Epic | Nature | +50% |

**Bloomwood Egg (Jade Grove)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Dream Moth | Common | Dreams | +15% |
| Crystal Snail | Uncommon | Crystals | +30% |
| Prism Armadillo | Rare | Crystals | +50% |
| Lantern Warden | Epic | Light | +70% |
| Jade Wyrm Turtle | Legendary | Earth | +85% |

**Ancient Grove Egg (Jade Grove)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Echo Bat | Common | Sound | +15% |
| Qi Clockwork Finch | Uncommon | Magical machinery | +30% |
| Moonfang Tiger | Rare | Moonlight | +55% |
| Thousand-Eyed Guardian | Epic | Mysticism | +80% |
| Ninefold Spirit Serpent | Legendary | Spiritual energy | +95% |
| Worldroot Colossus ★ | Mythical | Ancient nature | +160% |

**Inferno Egg (Ember Peak)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Magma Cub ★ | Common | Lava | +10% |
| Sunscale Dragon ★ | Legendary | Solar | +60% |
| Dawn Phoenix ★ | Legendary | Fire | +60% |

**Magma Heart Egg (Ember Peak)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Sand Phantom | Common | Sand | +15% |
| Solar Butterfly | Uncommon | Solar energy | +30% |
| Obsidian Guardian | Rare | Darkness and crystal | +55% |
| Golden Mane Lion ★ | Epic | Solar energy | +75% |
| Bonefire Dragon ★ | Legendary | Spectral fire | +90% |

**Phoenix Ash Egg (Ember Peak)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Dreadfang Cerberus ★ | Epic | Shadow | +85% |
| Prismatic Phoenix ★ | Mythical | Rainbow energy | +170% |

**Celestial Egg (Moonlit Isle)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Starfall Fox | Common | Stars | +20% |
| Cosmic Jellyfish | Uncommon | Nebulae | +40% |
| Nebula Owl | Rare | Cosmic energy | +65% |
| Celestial Snow Leopard | Epic | Ice and celestial energy | +95% |
| Comet Stag | Legendary | Comets | +115% |
| Celestial Pearl Dragon | Mythical | Celestial energy | +190% |

**Astral Sanctum Egg (Moonlit Isle)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Eclipse Cat | Epic | Darkness and eclipses | +110% |
| Timekeeper Tortoise | Legendary | Time | +130% |
| Galaxy Manta | Mythical | Cosmic energy | +220% |

**Forbidden Origin Egg (Origin Abyss)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Shadowcoil | Rare | Shadow | +100% |
| Rune Sphinx ★ | Legendary | Ancient magic | +170% |
| Thousand-Year Dream Eater ★ | Mythical | Dreams | +280% |
| The Nameless One | Secret | Unknown cosmic energy | +420% |

**Void Rift Egg (Origin Abyss)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Heavenbreaker Ape ★ | Legendary | Heavenly power | +205% |
| Voidscale Hydra | Mythical | Void | +340% |

**Primordial Abyss Egg (Origin Abyss)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Eternal Clockwork Dragon ★ | Secret | Time | +600% |

Nine-Tail Moonfox (Mythical) no longer hatches; players who own one keep it.

---

## 4. Auras

### Aura direction per realm

| Realm | Aura theme |
|---|---|
| Qi Awakening | Faint white or pale blue glow |
| Qi Foundation | Bright blue glow and small energy particles |
| Spirit Core | Swirling energy rings |
| Spirit Soul | Floating runes and a translucent spirit silhouette |
| Ascendant Realm | Golden energy, glowing trails, enhanced Qinggong effects |
| Immortal Realm | Layered halos and luminous energy wings |
| Divine Realm | Violet lightning, floating sigils, powerful energy fields |
| Cosmic Realm | Orbiting stars and nebula-like particles |
| Void Realm | Dark energy, spatial distortions, teleport-like trails |
| Heavenly Dao | Celestial symbols, radiant rings, divine lightning |
| Primordial Realm | Ancient glyphs and enormous layered energy effects |
| Eternal Transcendence | Cosmic rings, shifting colours, a unique ultimate effect |

### Three kinds of aura, never interchangeable

1. **Cultivation aura:** the player's realm, power and cultivation state.
2. **Pet aura:** the chosen aura pet's element, personality and identity.
3. **Guardian aura** (planned): a boss's identity, strength, vulnerability and rage (section 7).

Each kind has its own visual purpose. None is a recolour of another.

### Built so far

**Character auras** (one module per aura, all on the `CharacterAura` interface: build, show, hide, pulse, update, destroy)

- **Shared pieces:**
  - Every aura is built on the shared helpers in `src/client/AuraKit.lua`.
  - Each is registered in `DESIGNS` in `src/client/CharacterAura.lua`.
  - Its settings live in `src/client/AuraStyles.lua`, and its meshes in `ReplicatedStorage.AuraMeshes` (sources in `tools/blender/auras`).
- **Stages:** each aura charges up, then grows from idle to charged to awakened the longer the player cultivates.
- **Fallback:** without its meshes, a pet falls back to the anime flame aura, which is coloured by the pet's element.

| Pet | Aura | What it is | Module |
|---|---|---|---|
| Aqua Wisp | **Tidecaller Sanctum** | The player meditates on a blooming water lotus inside a tidal vortex over a pool of caustic light. Spirit koi join at the charged stage; a breaking-wave crown and four water spouts rise when awakened. | `TidecallerAura.lua` |
| Ember Wyrm | **Ember Crucible** | Fast-spinning ember slashes and cloud under the player; rising debris, sparkles, a twin vortex of energy beams and body flames. The spirit bead wyrm and orbit trails join when charged; a molten fire halo forms behind the head when awakened. | `EmberCrucibleAura.lua` |
| No aura pet | **Verdant Gale** (default) | A lime swirl and slash ring spinning on the ground, a twisting wind wisp rising through the body, rising streaks, a soft lime glow and light. | `VerdantGaleAura.lua` |

**Pet auras:** each equipped pet of a cultivating player shows its own element's aura (`src/client/AuraBuilder.lua`). Aqua Wisp and Golden Kirin are done.

**Poses and breakthroughs**

- A lotus pose and levitation while cultivating, and a flying pose while airborne.
- A burst effect on every rank-up, bigger at milestones.

**Next:** every remaining element gets its own aura concept. Aqua Wisp's water aura is the model for this, not a shared aura recoloured.

### Aura VFX brief (the project owner's requirements, kept verbatim)

> **ROBLOX ANIME RPG — SOL'S RNG-QUALITY AURA VFX**
>
> I want you to redesign and upgrade my Roblox game's aura VFX to the visual quality of the aura showcases in Sol's RNG. I want that same level of creativity, detail, cinematic presentation, and impressive 3D effects, but with original aura designs for my own game.
>
> You have creative freedom. Do not limit yourself to basic Roblox ParticleEmitters or simple neon parts. You are allowed to use Blender to create custom 3D models, meshes, animated objects, textures, and other assets. You may modify, replace, or completely redesign my existing VFX if it improves the final result.
>
> **1. Inspect my project first.**
> - Examine my existing aura system, character rig, scripts, and assets.
> - Identify what looks basic, outdated, unfinished, or visually weak.
> - Understand how the existing system works before modifying it.
> - Make the actual changes wherever your tools allow.
>
> **2. Create spectacular aura designs.**
> I want auras that feel like complete visual experiences surrounding the character, not just glowing particles. Explore creative combinations of:
> - Large floating 3D structures, rings, halos, weapons, wings, crystals, and other thematic objects.
> - Orbiting objects with different speeds, rotations, and movement patterns.
> - Layered energy flames, flowing ribbons, lightning, glowing particles, and animated trails.
> - Ground circles, runes, shockwaves, energy pillars, and environmental effects.
> - Custom Blender meshes and animated geometry that give each aura a distinctive silhouette.
> - Dynamic lighting, emissive materials, transparency, color transitions, and atmospheric effects.
> - Floating symbols, magical formations, celestial objects, and dramatic effects when appropriate.
>
> Do not force every effect into every aura. Design each one around a strong visual concept.
>
> **3. Make the animation feel alive.** Every component should have purposeful motion. Combine rotation, orbiting, floating, pulsing, scaling, fading, particles, and smooth animation curves. Make the aura feel dynamic from every camera angle, with visual layers moving at different speeds and distances. Create polished activation effects, idle loops, charging sequences, power surges, and deactivation effects where appropriate.
>
> **4. Use Blender and Roblox together.** Use Blender whenever custom geometry or animation can improve the result. Create and import assets as needed, then integrate them into Roblox Studio using appropriate meshes, attachments, particles, beams, trails, lighting, and scripts. You are not restricted to my current assets or implementation. Find the best practical approach for the intended visual result.
>
> **5. Make the auras feel rare and memorable.** Design an extensible system where different auras can have different levels of visual complexity, scale, effects, and presentation. A powerful or prestigious aura should feel extraordinary because of its composition, animation, detail, and visual impact, not merely because it has more particles. Use original concepts instead of directly copying specific Sol's RNG aura designs or assets.
>
> **6. Actually implement the changes.** Do not stop at suggestions, mockups, or example code. Modify the existing project and create the necessary assets wherever possible. Write complete Luau scripts, configure the required objects, and integrate the effects with my current character system. If you cannot directly access Roblox Studio or Blender, use the tools and files available to produce the actual assets and implementation you can, and clearly identify any remaining manual steps.
>
> **7. Polish and optimize.** Make the effects look excellent in-game while maintaining performance. Handle character respawning, effect cleanup, multiplayer visibility, and lower-end devices. Use local cosmetic effects where appropriate and avoid unnecessary server replication. Test the results whenever possible, fix visible issues, and refine the animation and composition.
>
> **FINAL GOAL:** I want my Roblox game to have original, breathtaking, Sol's RNG-quality aura VFX with custom 3D assets, intricate animated details, floating structures, beautiful particles, and cinematic presentation. Take initiative, experiment with different techniques, and prioritize the best visual result over the simplest implementation.

---

## 5. Eggs

Fifteen eggs, **three on every island**, each needing a higher rank than the last.

- **Hatching:** free, with a 45-second cooldown per egg.
- **Chances:** follow the rarity scale: Common 45%, Uncommon 27%, Rare 15%, Epic 8%, Legendary 4%, Mythical 0.9%, Secret 0.1%.
- **Missing rarities:** when an egg has no pet of some rarity, its share goes to the next pet that has one. So later eggs give rarer pets far more often.

| Island | Egg | Needs | Chances |
|---|---|---|---|
| Starting Island | Beginner Qi Egg | Qi Initiate | Aqua Wisp 45%, Ember Wyrm 27%, Lunar Hopper 15%, Volt Fox 8%, Golden Kirin 4%, Astral Whale 0.9%, Origin Serpent 0.1% |
| Starting Island | Spirit Breeze Egg | Qi Adept | Wind Sprite 45%, Cloud Sheep 27%, Spirit Crane 15%, Azure Sky Dragon 8%, Stormhorn Kirin 5% |
| Starting Island | Elemental Core Egg | Foundation Initiate | Glacier Puff 45%, Thunder Jelly 27%, Crystal Beetle 15%, Gravity Imp 8%, Thunderclaw Drake 4%, Frostfang Serpent 1% |
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

- **Source:** the 15-egg concept sheet. Each island's eggs are modelled in Blender by a script (`tools/blender/eggs/eggs_<island>.py`, shared helpers in `egg_kit.py`, preview renders by `egg_render.py`) and exported to `assets/eggs/<EggId>.fbx`. An export holds an `<EggId>_Body` mesh coloured by an atlas (`<EggId>_atlas.png`) and `<EggId>_Glow_<hex>` parts, which become Neon in that colour.
- **Detailed eggs (Jade Grove onward), built like the sculpted pets** (`eggs_jade.py`, `eggs_ember.py`):
  - High-detail pieces with procedural Cycles shaders (`egg_hi.py`): knotted bark with grain, veined leaves, marbled jade, gold-veined crystal, carved wood planks, leafy crowns.
  - Baked by `egg_bake.py` onto one game mesh of about 14,000 triangles, with `<EggId>_color.png` (ambient occlusion included), `_normal.png`, `_roughness.png` and `_metalness.png`.
  - Studio's importer turns the colour and normal maps into a SurfaceAppearance. Roughness and metalness are set on it in Studio.
  - Glowing parts stay separate Neon pieces, and every open glow piece is wound to face outward, because Roblox culls back faces.
  - Gold is 0.6 metallic, not 1: fully metallic gold shows black wherever it has nothing bright to reflect.
  - The shaders' ambient occlusion is local to each piece. While baking, the game mesh lies on the high-detail surface, and a scene-wide AO sees it everywhere: the whole egg then bakes as one deep crevice (too dark, or red-hot on the lava shaders).
- **In Studio:** an imported egg is stored with `WorldBuilder.storeEgg(model, eggId)` in `ServerStorage.EggMeshes.<EggId>`. `buildEggStands` places it at 1.3 studs per egg unit.
- **Recreated so far:** the Starting Island, Jade Grove and Ember Peak eggs. The other six keep the older family designs below until they are recreated from the sheet.

| Egg | Design |
|---|---|
| Beginner Qi Egg | Cut blue crystal: long irregular facets in six blues, from ice-white to cobalt, with Qi light glowing along the cuts from a core inside |
| Spirit Breeze Egg | Sky-blue porcelain brushed with white wind bands, a gold crescent swirl on its shoulder holding a glowing breeze sigil, resting on a bed of gold-rimmed auspicious clouds |
| Elemental Core Egg | Dark cracked stone in an angular gold cage (belt, raised plates, straps and a clawed crown), a large cyan core crystal set in its front, smaller gems round the belt, Qi light seeping through the cracks |
| Jade Spirit Egg | Large cut facets of glossy marbled jade, Qi glowing in the seams between them, caged by thick knotted bark branches; leaves sprout along every branch, with twigs ending in leaf clusters. Two branches arch over a bark-bound glowing jade-leaf gem in the front, veined in bark |
| Bloomwood Egg | Facets of blossom-pink crystal veined with gold, gold filigree branching down over the crown, two rows of broad veined leaves cupping the lower half, a three-layer leaf emblem in relief with a gold rim round a glowing heart, and a cupped lotus in bloom either side of its base |
| Inferno Egg | Plates of black volcanic rock, molten lava glowing in the seams between them and in thin veins across them, their edges heated red; chunks of rock break away from its right shoulder and fly off up and out |
| Magma Heart Egg | A core of cut crimson crystal veined with molten orange, grown through with crystal shards: a tall crown crystal, shards flaring outward and upward round it (the largest at the base), and ember-hot chips glowing between them |
| Phoenix Ash Egg | A crimson shell veined with molten gold, wrapped in two wings of flame feathers that sweep up and curl round it, a crest of feathers on its crown, tail feathers low at the back, and a glowing phoenix flame on its front in a gold rim |
| Ancient Grove Egg | Carved wood planks in fourteen upright columns, each split at its own heights, every plank its own tone; dark bark in the grooves, pale heartwood showing at the crown. A mossy trunk behind it sends roots gripping the egg and branches spreading into lumpy crowns of leaves, and a spiral of Qi glows on its front |

**Older family designs** (`tools/blender/eggs/Eggs.blend`, preview `Eggs_preview.png`): each island has one design family. The second egg adds a jewelled gold band, and the third a crown and floating halo.

| Island | Design |
|---|---|
| Moonlit Isle | Porcelain egg with gold filigree, glowing star inlay, small wings and an orbiting gold ring |
| Origin Abyss | Obsidian plates cracked with void light, spiral void core, thorny bronze branches |

### Egg auras

Every egg on its stand has its own aura, built in the Workspace from particle emitters, trails, beams, billboards, glowing image planes and lights, with no meshes and no flipbooks, so it can be tuned in Studio and with VFX Studio.

- **Built by** `src/worldbuild/EggAuraVFX.lua`, one recipe per egg: `VFX.build("<Island>")` rebuilds `FloatingIslands.<Island>.EggAuras`. Each aura is a Model tagged `EggAura` that streams in whole.
- **Animated by** `src/client/EggAura.lua`, from attributes on the instances (listed in both modules' headers), so an aura tuned by hand keeps working.
- **Tuning:** tune an aura on its instances in Studio, then copy the values into its recipe, so a rebuild keeps them.
- **Depth and rhythm, never flat:**
  - No two orbiting pieces share a speed, radius and plane. Some run the other way, and each bobs on its own period.
  - Rings precess (`Wobble`) as they spin.
  - Ribbons shed dust or feathers from their heads, which leaves spiral wakes.
  - Mist and an updraft column give the aura volume.
  - The whole aura breathes (`Breath`, `BreathPeriod`): speed, glow and ring size swell and ease back, at each egg's own pace (table below). `BreathShape = "Heartbeat"` makes it beat instead: a double thump, then a rest (no aura uses it since Ember Peak's were removed).
  - Things can move to the beat: beams with `BeatWidth` swell, orbiting attachments with `BeatReach` are flung out (and with `GatherPull` drawn in while a hatch gathers), emitters and ripples with `BeatEmit` fire on each thump, `BeatHighlight` throbs a Highlight on the egg, and `BeatScreen` pulses the nearby player's screen (ColorCorrection and Bloom, client-only) and flashes it on the burst.
  - **Every aura is its own invention, built from the whole toolkit** (ParticleEmitter, Attachment, Beam, Trail, PointLight, Highlight, BillboardGui, SurfaceGui, TweenService, ColorCorrection, Bloom), never the same ring-and-sigil skeleton recoloured.
  - Rocks can orbit too: parts with `Orbit` carry their glowing cores and tumble (`Tumble`). With `AvoidAngle` and `AvoidRadius` an orbit pulls in as it passes a neighbouring egg, however far a pulse or a hatch throws it (the Phoenix Altar's stands are only 5.9 studs apart; the Inferno's rocks were swept in Play over every angle, bob, pulse and hatch push and stay at least a third of a stud clear of both eggs). An aura with `PulseInterval` sends an energy pulse through itself every few seconds (`PulseJitter`), each piece answering `PulseDelay` later so nothing pulses at once: the aura speeds up (`PulseSpeed`) and glows (`PulseGlow`), pieces are thrown out (`PulseReach`), beams and planes swell (`PulseWidth`, `PulseSwell`), emitters and ripples fire (`PulseEmit`), and with `PulseEggGlow` the egg's own lava heats toward that colour. An aura with `CyclePeriod` runs a life cycle instead: `CycleRebirth` marks the rebirth in it (a screen flash with `CycleScreen`, and a hatch jumps the cycle there). Along the cycle emitters follow `CycleRate` or fire `CycleEmit` at `CycleAt`, lights follow `CycleBrightness` and `CycleColor`, the egg's glowing parts cool and heat between `CycleEggCold` and `CycleEggHot` along `CycleEggGlow`, a Highlight follows `CycleHighlight`, `CycleOutline` and `CycleFill`, and attachments sweep along a curve (`SweepFrom`, `SweepVia`, `SweepTo`, `SweepCurve`), which opens trails like wings. Every aura can be tuned by hand with `Intensity`, `Density`, `OrbitSpeed`, `LightIntensity` and `Visible`.
- **Idle and hatch** (no periodic pulse, which the owner judged unnecessary, except where an aura's own design calls for one: the Inferno's energy pulse):
  - Idle: everything turns, orbits, drifts and emits on its own timing.
  - Hatch, in two parts. First the aura gathers: everything speeds up and draws in, energy is pulled into the egg, and the egg glows in the aura's tint. Then it bursts: the rings fling outward, ripples run across the rim, and the egg flashes.
- **Hatch hook:** on a successful hatch, `PetController` calls `EggAura.hatch(eggId)`. It plays at the player's nearest stand of that egg.
- **Cost:** full emission within 90 studs of the camera, half rates to 200, off beyond that. Each aura's textures are preloaded when it streams in.
- **Textures:** VFX Studio's library, the PDS kit, and our own, drawn and rendered by `tools/blender/vfx/egg_aura_textures.py` into `assets/vfx/eggs/`.
- **Measured in Play:**
  - Flat (VelocityPerpendicular) particles do not render in these auras, so every flat element is a SurfaceGui image plane. Rings have the image on both faces.
  - A ring must dip its front toward the viewer, or it goes edge-on from the usual camera height.
  - Additive beams (LightEmission 1) wash out to white in daylight, so the element streams use 0.35.
  - VFX Studio's hairline rings are too faint in daylight, so the rings use bolder textures of our own.
  - Some VFX Studio textures (its swirl vortex and radial burst among them) are white on black with no alpha. They work on additive particles, but show as black squares on a SurfaceGui plane, so check a texture's alpha before putting it on a plane.
  - Leaves, petals and ribbons that should read as colour, not light, use low light emission (about 0.15 to 0.35): fully additive, they wash out to pale streaks in daylight.
  - On a pale egg (Spirit Breeze, Bloomwood) a strong halo and light blow the egg out to white, so those auras keep them faint.
  - The Jade Grove stands are 7.5 studs apart (Starting Island's are 10), so its auras stay within about 3.3 studs of the egg.
  - An emitter on a part spreads over the part's whole box, and Cylinder runs along the part's X axis. For flames round a rim, use one emitter per attachment round the ring (unrotated: they rise straight up).
  - In Edit mode, `ContentProvider` can report textures as failed that render fine in Play. Judge textures in Play.
  - A ring built of beams joined end to end shows its texture once per arc (TextureLength set to the arc's length), so the flow runs on through the joints; otherwise every joint restarts the pattern and the ring reads as dashes.
  - A molten band over a bright sky needs no light emission and a bright inner beam on top: the dark band keeps its crimson and black, the inner stream glows.
  - Dark smoke round an egg on a column either hides behind the egg or drifts up into a grey smudge; contrast comes better from dark crust textures and the rocks.
  - Sparks need a texture with real alpha (`AuraSpark`): the library's dots and stars are white on black, so below full light emission they show black squares, and fully additive over a bright sky their orange turns pink and white. Velocity-aligned particles (`VelocityParallel`, like `VelocityPerpendicular`) do not render in these auras: sparks face the camera.
  - Fire round an egg needs one emitter per attachment in a ring at the egg's girth: an emitter on a bed under the egg starts its flames inside the egg mesh, and a ring-shaped (Disc surface) emitter scatters them into thin smoke. Flames at full light emission wash out to pale smoke in daylight; 0.6 keeps the yellow, orange and red.
  - A beam whose texture carries its own colour uses LightEmission 0: any light emission adds the red over the blue sky and turns it pale pink. Brightness keeps the hot core bright.
  - A Highlight fill stronger than about 0.15 paints over an egg's baked facets, so the beat Highlight is a faint fill with a strong rim.
  - Evenly spaced beams of one size all meeting at a point read as a cage, whatever their texture. Give each its own angle, bow, width and pace, and leave the egg's front open.
  - The detailed eggs are taller than the recipes' measures, so their auras are lifted (`lift` in `EggAuraVFX`). Effects that belong to a part of the model (a gem, a lotus, a leaf crown) are anchored to points measured on the model in Blender (`anchor`).

| Egg | Breath | Aura |
|---|---|---|
| Beginner Qi | 5 s, calm | **Calm Qi.** A lotus mandala turns beneath. A bold Qi ring with comet streaks and a broken ring of breath cross on diagonals, and two silk Qi arcs glide round. Three blue crystal shards (modelled and rendered in Blender) drift round, rocking. Motes rise like breath, with star glints and a soft halo. |
| Spirit Breeze | 3.5 s, gusty | **Wind.** A wind-rose sigil turns beneath. Light-blue and white wind rings (two crescent gusts and a broken ring of breeze) whirl on three planes. Three white wind trails spiral up and down, auspicious clouds drift off the rim, and feathers ride the updraught. |
| Elemental Core | 2.5 s, a thrum | **Concentrated elements.** The five-element sigil and a gold mandala turn against each other beneath. Four element streams (cyan, gold, blue, amber) rise off the formation into a turning cage of light that meets above the crown. Round the egg are a gyroscope of three gold element bands, four element orbs racing round with trails, blue and gold motes, and sparks off the core. On the hatch the core gem flares. |
| Jade Spirit | 4.5 s, growing | **Living jade.** A vine-and-leaf formation turns beneath. A jade ring and a swooshing crescent of Qi cross round the egg. Three vines of light twine up from the rim to the crown, each at its own pace. Three currents of Qi race round on their own planes, shedding leaves that tumble in their wake, and three broad leaves drift round, rocking. Qi breathes out of the jade-leaf gem in a soft green glow and rising motes. |
| Bloomwood | 6 s, dreamy | **Eternal blossom.** A blossom mandala turns over a slow bloom of golden light. A pink ring and a gold breeze cross round the egg. Two streams of blossom wind circle it, shedding petals, and a fountain throws petals up off the rim to drift back down. Four blossoms float round, rocking. Golden pollen rises out of both lotus hearts, and a soft glow surrounds the emblem's heart. No halo: on the pale crystal egg it reads as a milky veil. |
| Ancient Grove | 7 s, deep and slow | **The world tree's heartbeat.** An ancient tree's growth rings turn slowly beneath a counter-turning vortex of Qi. Five roots of light climb the stand's golden roots up into the egg. A spiral of Qi climbs round it, and four forest spirits wander round on slow looping paths. The egg's own five leaf crowns come alive: light glows inside each, fireflies drift out, and leaves fall from them, gold and green by turns. A wide ring of old light circles it. |
| Inferno | 3.2 s, simmering; a pulse every 6 ± 1.5 s | **A miniature volcano with an unstable molten core.** Its own lava cracks are its light (they heat toward gold on each pulse), with a low warm light; no rings round it or at its foot. Sparks spit out of its cracks, and three spark comets race round it on tilted paths, each shedding a stream of hot sparks. Six broken volcanic rocks (modelled and baked in Blender, a slab, a shard, a wedge, a chunk, a splinter and a cinder, lava glowing in their cracks) orbit at their own distances, tumbling and shedding embers, and pull in as they pass the Magma Heart beside it. Four molten ribbons spiral round it, flames licking off them. Beneath it only ripples of heat and three vents: no sigil or ring under the egg. Embers rise, ash drifts, cinders are thrown up now and then. Every few seconds an energy pulse runs through it, each part in turn: the cracks heat, sparks burst from them and the comets, the rocks are thrown out, flames surge, the vents erupt one after another. On the hatch the rocks are pushed out, the comets and ribbons drawn in, then everything erupts. |
| Magma Heart | — | **A blazing fire.** Eight flame columns stand round the egg just inside its widest girth, so flames lick up every side of it: bright yellow at the base through orange and red to dark red at the tips, flickering (each column's rate and speed jump every 0.15 s), a faster yellow core in every other column, embers drifting up. Roblox's built-in fire textures, no Fire object, no flipbook; tuned on a test fire on the Starting Island with the owner. |
| Phoenix Ash | a 15 s cycle | **The Ash Cycle:** the egg dies and is reborn every 15 seconds. **Ash:** its veins and phoenix emblem dim to a smoulder under a dull ember rim, pale ash falls round it (the one aura on the altar where things fall) and a thin curl of smoke rises from its crown. **Kindling:** embers wink awake round it and the glow climbs back. **Rebirth:** the ash rushes up catching fire gold, two wings of gold light sweep open behind its own sculpted wings shedding golden feathers, a sunburst blooms over its crown, its rim races through the prism's colours (its rarest pet is the Prismatic Phoenix), its light blazes gold and a nearby player's screen flashes warm. **Burning down:** the wings fold, their feathers greying into ash as they fall, and the cycle begins again. A hatch is a rebirth. The wings keep 1.76 studs clear of the Magma Heart egg (a raycast sweep over the whole wing path). |

**Egg stands today:** each island has a shrine with three stands where eggs are hatched directly. Under the planned guardian loop, eggs come from guardians instead; the stands' future role is an open question (section 9).

---

## 6. World

Five floating islands built from original Blender work: terrain tops, sculpted undersides, landmarks and set pieces. The Starting Island is the hub, and a bridge leaves it for each other island.

**Bridges** (since November 1, 2026, replacing the stepping stones):
- Paths in `tools/blender/world/layout.py` (`BRIDGES`; `--write` generates `src/worldbuild/Placements/Bridges.lua`), built by `WorldBuilder.buildBridges()` into `FloatingIslands.Bridges`. Each starts beside its route's waystone and lands at the island's arrival (the Grove Gate, the Ember Gate, the Crescent Arch, the Origin Route's Descent Ledge).
- A deck 20 studs wide (doubled at the owner's request; room to ride the sword along it) with rails. Jade (161 studs, a gentle arch), Ember (241, rising 24), Moonlit (a stairway of three flights zigzagging 430 studs up 192, with a landing 30 studs across at each turn and a last stretch straight through the Crescent Arch, at most 32°), Origin (534, a long low arch).
- Both ends of every bridge are carried onto their islands by a solid abutment (level with the deck, 8 studs on and 7 deep), so the deck meets the ground with no gap or overhang; measured across the deck's width, every end is within about half a stud of its island's ground (the Moonlit top within a stud). At the Origin end the Descent Ledge's void-fire brazier stands on the deck's end, marking where players glide down.
- The bridges' arrivals are kept clear: a few scattered props there were removed (a moonstone shard and a lunar rock on Moonlit Isle, an obsidian shard on Ember Peak), and the island prop scripts now leave the arrivals free.
- At each bridge's start a gate holds a **Qi barrier** (tagged `QiBarrier`, with the destination's `RankId`): solid until the player reaches that rank, then open to them (`BridgeBarriers.client`). A player below the rank found on the bridge past the gate, or on the island it leads to, is put back in front of the gate (`WorldService`). Tested in Play both ways.
- Each bridge wears its island's kit, modelled in Blender and baked like the eggs (`tools/blender/world/bridge_kits.py` → `assets/world/Bridges/<Theme>Bridge.fbx`, piece offsets in `Placements/BridgeKits.lua`), laid by `buildBridges` over the walkable blockout, which turns into invisible collision:
  - **Jade Grove:** plank deck with lattice rails, carved jade posts, vines winding the rails and trailing over the edges; under it cross-beams whose roots hold glowing jade lanterns; a jade gate wound with vines under a two-tier curved roof with a gold-rimmed leaf emblem.
  - **Ember Peak:** hexagonal basalt column tops with lava glowing in the seams, walls of basalt columns; organ-pipe columns hanging beneath with molten drips; a gate of basalt column clusters under a slab split by a molten crack.
  - **Moonlit Isle:** level moonstone treads with gold nosings, gold handrails and crescent-topped posts; round landings with a gold ring and crescent, moon-lantern posts round them; moonstone crescents hanging on gold chains beneath; a gate of gold-ringed pillars under a great gold crescent with a lantern in the doorway.
  - **Origin Abyss:** cracked ancient slabs with void light in the cracks and a broken parapet; a hanging stone arch with chunks on bronze chains; a ruined gate, one pillar broken short, its lintel split by void light and carved with a glowing rune.
- Studio's importer turns each kit half round (x and z flip, as with the eggs); the builder turns each piece back.

| Island | Centre (studs) | Feel | Relics | Bridge from the Starting Island (the old stepping-stone route) |
|---|---|---|---|---|
| Starting Island | (0, 200, 0) | Grassy cultivation grounds and the spawn hub | Root of the Island (300 Qi, Qi Initiate) | — |
| Jade Grove | (330, 206, −70), east | Ancient forest | Grove Heart, Jade Seed, Whispering Spring (800 Qi each, Qi Gatherer) | 3 stones, 39-stud gaps, **2 air leaps** |
| Ember Peak | (−318, 222, 262), south-west | Volcanic, lava pools | Ember Heart, Ashen Sigil, Caldera Crown (1,500 Qi each, Qi Awakener) | 57-stud gaps, **3 air leaps** |
| Moonlit Isle | (80, 392, −330), highest | Pale and celestial | Moon Mirror, Star Well (3,000 Qi each, Foundation Initiate) | Climbs 27 studs per stone, **4 air leaps** |
| Origin Abyss | (−560, 95, −540), far north-west and below the others | Hidden endgame: dark slate, void crystals and rifts, broken ruins | Origin Altar (250K Qi, Divine Initiate); the Void Shard high above it (1M Qi, Void Walker) | 132-stud gaps, **6 air leaps**, then a glide down; the Void Shard climb needs **7** |

**Shared rules**

- **Relics:** each Spirit Relic gives a one-time Qi reward, and finds are saved.
- **Qi Spring:** the spring on the Starting Island adds +50% Qi while cultivating in it.
- **Falling:** a player who falls far below the island they last stood on is returned to that island's checkpoint.
- **Hazards:** parts tagged `LavaHazard` (Ember Peak's lava) also return a player to their island's checkpoint on touch.

### Starting Island (built)

- **Qi Compass:** the spawn plaza is an octagonal platform with the eight trigrams in the Earlier Heaven arrangement, a jade compass rose and glowing Qi channels in the tile joints.
- **Qi Spring:** a shallow pool with lotus stepping stones and a stacked scholar's rock at its source. A stone spillway carries the water to a waterfall that pours off the island's edge.
- **Egg garden:** three lotus pedestals hold the Beginner Qi, Spirit Breeze and Elemental Core eggs.
- **Waystones:** one beside each bridge's gate, naming its destination and the rank that opens its bridge.
- **Underside:** stacked rock slabs held by braided roots. A climb down twelve bracket-fungus shelves on the great path root leads to the **Root of the Island** in a root cradle.
- **Nature:** spirit pines with flat canopies players can stand on, plum blossoms, mossy rocks and flowers.

### Jade Grove (built)

- **Grove Gate:** a moon gate at the arrival.
- **Elder Jade Tree:**
  - three root pillars form a walk-in hollow holding the **Grove Heart**;
  - buttress roots, one arching high enough to walk under;
  - a Qinggong climb of fungus shelves and leaf-cloud canopy tiers up to the crown nest and the **Jade Seed**.
- **Bloom Glade:** a flagstone shrine ringed by standing stones, with golden-root pedestals for the Jade Spirit, Bloomwood and Ancient Grove eggs.
- **Whispering Hollow:** a sunken spring with whisper stones and the **Whispering Spring**.
- **Underside:** a faceted dark-jade mass with hanging jade crystals, moss curtains and vines.
- **Forest:** ancient trees with walkable canopy tiers, bamboo, ferns, glowing mushrooms, jade crystal outcrops, ruin pillars and fallen logs.

### Ember Peak (built)

Columnar basalt is the island's signature, used for the cliffs, the climb, the altar and the underside.

- **Ember Gate:** the arrival, two bundles of basalt columns with iron fire braziers under an obsidian lintel with a cinnabar plaque.
- **The volcano:**
  - a crown of basalt columns rings its crater;
  - inside, a lava lake holds the **Caldera Crown** on a basalt pillar;
  - six basalt column steps climb the flank as the Qinggong route to the rim.
- **Lava river:** it overflows a notch in the rim, runs down a carved channel and pours off the island's edge as a lavafall. Touching the lake or the river returns the player to Ember Peak's checkpoint.
- **Ember Forge:** ruined walls of stacked basalt blocks with a sooty chimney and anvils. The **Ember Heart** hovers over a hearth of glowing coals; this nods to the planned forged weapons.
- **Ash Plain:** petrified trees around a cracked obsidian monolith carved with the glowing **Ashen Sigil**.
- **Phoenix Altar:** a hex-basalt floor with three cinnabar-topped column pedestals that step up in height. They hold the Inferno, Magma Heart and Phoenix Ash eggs, the rarest highest.
- **Underside:** hanging hexagonal basalt columns, like organ pipes, with a magma core glowing through the gaps.
- **Dressing:** fire crystals, ember vents throwing sparks, basalt clusters and obsidian shards.

### Moonlit Isle (built)

Seen from above, the island is a crescent moon: a full disc with a larger offset disc cut away, its horns curling around an open bay of sky.

- **Arrival and route:** a gold crescent arch between two moonstone spires. Each route stone is a small floating crescent.
- **Moon Mirror:** a dark reflective pool you can walk on, in a marble-and-gold rim. A curved bridge leads to a moonstone lotus holding the **Moon Mirror** relic.
- **Star Well:** on the west horn, a marble well with a gold lip, brimming with glowing starlight, with the **Star Well** relic above it.
- **Celestial Pavilion:** eight porcelain pillars with gold crescent finials on a stepped marble platform, under a floating golden armillary.
  - Its porcelain egg pedestals have blue glaze bands, small gold wings and an orbiting gold ring, after the Moonlit egg design.
  - They hold the Celestial, Astral Sanctum and Heavenly Throne eggs.
- **Underside and cliffs:** marble cliffs with a gold band under the lip step inward into a belt of soft cloud. Moonstone geode crystals hang beneath, some of them glowing.
- **Dressing:** hovering porcelain star lanterns, glowing frost lilies, moonstone shards, lunar rocks and spires on the horns.

### Origin Abyss (built)

The hidden endgame island, torn in two by a void rift that zig-zags across it from north-east to south-west, pinching and gaping as it goes. The north-west half stands higher and tilts up toward its far edge.

- **Arrival and route:** the Origin Route ends at the Descent Ledge, a broken temple landing high above the island with steps that end in the air and a violet void fire. Players glide down from it. Each route stone is a floating obsidian shard.
- **Gate of Descent:** two carved pillars, one snapped. The lintel has fallen onto the stump. A ruined avenue lined with snapped columns and fallen column drums leads from the gate to the rift.
- **Broken bridge:** an ancient stone bridge crosses the rift at its narrowest point. Its middle has fallen away, leaving one block hanging in the gap to jump across.
- **Origin Altar:** on the north-west half, a ring of nine leaning obsidian slabs carved with glowing seal-script glyphs (one snapped, its top fallen outside the ring) around a stepped dais with a glowing spiral sigil. The **Origin Altar** relic floats above it.
- **Void Shard:** a great obsidian-glass crystal with a glowing core, chained to a floating temple floor about 150 studs above the altar. Floating temple fragments climb to it, each rising 49 studs, so Void Walker clears every stage and Divine Initiate falls short. The **Void Shard** relic floats on the top floor.
- **Egg shrine:** three obsidian plinths cracked with void light, each cradled by thorny bronze branches, after the Origin Abyss egg design. They hold the Forbidden Origin, Void Rift and Primordial Abyss eggs, and each stand glows in its egg's own colour. The Thorn Crown, seven great bronze branches rooted behind the shrine, arches over them.
- **Fallen colossus:** a giant carved stone head sunk into the ground, its face turned toward the path. Void light shows in its eyes and through a crack across its face.
- **Underside:** separate angular chunks with gaps between them, void light glowing through. Iron chains bind the halves beneath the rift, a glowing veil hangs deep in the rift, and broken-off debris drifts below.
- **Dressing:** void crystals of dark glass around glowing cores (most along the rift's lips, with rising motes), slate rocks, and hewn paving on the temple terraces with stones missing toward the edges.

### How islands are built

- **Blender scripts:** `tools/blender/world/` holds the layout and route checks (`layout.py`) and per-island scripts. Each script authors the terrain heightfield, the meshes, the texture atlas and the placements.
- **Exports:** the scripts write FBX files to `assets/world/<Island>/` and data modules to `src/worldbuild/`.
- **Assembly:** `src/worldbuild/WorldBuilder.lua` builds each island in Studio, under `Workspace.FloatingIslands.<Island>`, and the result is saved in the place. The steps are listed at the top of that file.
- **Terrain:** each island uses its own terrain materials, because terrain colours are global to the place:
  - Starting Island: Grass, Ground, Rock and Cobblestone.
  - Jade Grove: LeafyGrass, Mud and Sandstone.
  - Ember Peak: Basalt, CrackedLava, Asphalt (ash) and Sand (paths).
  - Moonlit Isle: Limestone, Snow (frost), Salt (paths) and Pavement.
  - Origin Abyss: Slate, Concrete (paths) and Glacier (void-crystal crust). Brick is not used: Studio snaps Brick terrain to the 4-stud voxel grid, so paving is built from meshes.
- **Meshes:** each island has one texture atlas and reusable kits, and every piece gets its own collision setting.

---

## 7. Guardians and egg theft (planned)

### Encounter

The server owns every state change. Thresholds and durations are tuned in playtests.

| State | Trigger | What happens |
|---|---|---|
| 1. Guardian | 100–40% HP | Protects its egg, attacks players in its area, uses its normal abilities. The egg cannot be stolen. |
| 2. Weakened | Below 40% HP | Attacks slow down; posture, aura and effects show it is vulnerable. The egg becomes available to steal. |
| 3. Enraged pursuit | Egg stolen | Recognises the theft and chases the thief with faster movement, leaps and area attacks. The pursuit creates urgency without making escape feel random or impossible. |
| 4. Escape | Thief reaches the safe zone | The server secures the egg in the player's inventory. |

### Caught: the egg is recoverable

If the guardian catches the thief:

1. The egg leaves the player's carried state.
2. It drops at a clear, reachable spot chosen by the server near the catch point. It is never placed inside geometry, under the map or inside the guardian.
3. It stays for the recovery period.
4. The same player can pick it up again, which starts another escape attempt.
5. The guardian stays enraged while the egg is unsecured.
6. The egg is secured only at the extraction zone.

A failed escape never silently destroys the egg.

- **Ownership:** other players cannot steal, duplicate or claim a dropped egg unless a deliberate multiplayer rule allows it.
- **Cleanup:** abandoned encounters and server shutdowns resolve the temporary egg state safely and never award duplicates.

### Server authority

The server decides:

- guardian health and damage;
- every state change;
- whether the egg can be stolen, and who stole it;
- whether the egg is carried or dropped, and who may recover it;
- whether the player has reached the extraction zone;
- when the egg enters the inventory.

The client only shows animations, UI, trails, auras, hit effects and movement feedback.

Egg lifecycle, with every transition validated and repeated requests ignored:

```
Guarded → Available → Carried → Dropped → Carried → Secured
```

### Guardians by island

| Island | Guardian | Encounter direction |
|---|---|---|
| Starting Island | Beginner Guardian | Introductory fight, basic Qinggong escape |
| Jade Grove | Nature Guardian | Escape routes through trees and elevated terrain |
| Ember Peak | Fire Guardian | Escape routes around lava and volcanic hazards |
| Moonlit Isle | Celestial Guardian | More demanding aerial movement |
| Origin Abyss | Primordial Guardian | The most demanding encounter |

Names, attacks, health, egg pools, unlocks and rewards are still to be designed.

**Guardian aura states**

- **Guardian:** stable, controlled, powerful.
- **Weakened:** flickering energy, unstable formations, cracked or collapsing elements, a clear vulnerable core.
- **Enraged:** stronger, faster, visibly intensified.

### Systems

| System | Responsibility |
|---|---|
| QiSystem | Cultivation and Qi progression |
| QinggongSystem | Air movement, dashing, speed and stamina |
| CombatSystem | Damage, abilities, forged weapons and combat validation |
| BossSystem | Boss behaviour and encounter states |
| EggTheftSystem | Stealing, ownership and extraction |
| PetSystem | Inventory, hatching and equipment |
| AuraSystem | Character, pet and guardian visual effects |

### Build order

Build one complete encounter before expanding to every island.

1. First playable Qinggong abilities: dashes and stamina, on top of today's air leaps and glide.
2. One guardian with server-controlled health and states.
3. The Weakened state and the egg interaction.
4. The enraged pursuit.
5. Egg dropping, recovery, retry and extraction.
6. Secured eggs connected to the existing inventory and hatching.
7. Multiplayer ownership, exploit resistance, disconnects and edge cases.
8. The framework rolled out to every island.
9. Polish: guardian animation, auras, trails, sound, UI and cinematic feedback.

### First playable checklist

- [x] Cultivate Qi.
- [x] Use basic Qinggong movement.
- [ ] Find and engage one guardian.
- [ ] Damage it until it is weakened.
- [ ] Steal its egg.
- [ ] Trigger the enraged pursuit.
- [ ] Escape and secure the egg.
- [ ] Fail an escape and drop the egg.
- [ ] Find and recover the dropped egg.
- [ ] Try another escape with it.
- [ ] Secure the egg without duplicate copies.
- [ ] Hatch it with the existing pet system.

---

## 8. Technical architecture

**Tools:** Roblox Studio and Rojo 7.7.1 (VS Code, Git), with Blender 5.2 for pets, eggs, aura pieces and islands.

**Rojo mapping**

| Folder | Maps to |
|---|---|
| `src/shared` | ReplicatedStorage |
| `src/server` | ServerScriptService |
| `src/client` | StarterPlayerScripts |
| `src/worldbuild` | `ServerStorage.WorldBuild` (build-time only, never required by game scripts) |

**Imported models**

| Kind | Where in Studio |
|---|---|
| Pets | `ReplicatedStorage.PetMeshes/<EggId>` |
| Aura pieces | `ReplicatedStorage.AuraMeshes` |
| Eggs | `ServerStorage.EggMeshes` |
| Island kits | `ServerStorage.WorldKit/<Island>` |
| The islands themselves | `Workspace.FloatingIslands`, saved in the place |

**What the server owns:** Qi rewards, rank-ups, Qinggong levels, hatching, inventory, relics, world safety (spawn, checkpoints, fall reset) and saving. It never trusts the client for Qi amounts, ranks, hatch results or inventory.

**What clients handle:** UI, auras, effects, pet companions, input and Qinggong movement.

**Shared config:** ranks, Qinggong, pets, eggs and relics.

### Data and security

- Validate every important action on the server.
- Save with Roblox data stores; old saves are migrated automatically.
- Test multiplayer, rejoining and invalid requests, not just the happy path.
- No secrets in source control; avoid third-party asset packs.

---

## 9. Open decisions

- **Egg stands under the guardian loop:** a hatching spot for secured eggs, a starter egg source, or removed?
- **Forged weapons:** the purchase and request flow, which weapons each Qi mastery level unlocks, and how they plug into combat.
- **Sword flight:** how it unlocks. The bridges are wide enough to ride along; whether flight may cross a Qi barrier is still open (today the server returns anyone below the rank who reaches a bridge or island past it).
- **Qinggong:** dashes and stamina.
- **PvP stealing or raids:** only ever opt-in and server-checked, with protected pets, cooldowns and clear warnings. Not planned. Guardian egg theft is PvE.
- **Monetization:** cosmetic-first, never pay-to-win; no paid eggs or random rewards until Roblox's policies are checked.
- Per-element and per-realm aura looks.
- Blender models for the remaining procedural pets.
- Balance tuning from playtests.

**North star:** players feel like cultivators who earned their power and their movement. They train Qi to grow stronger and master Qinggong to move beyond ordinary limits. They will challenge guardians for their eggs and survive the pursuit that follows. Failure is a recoverable setback, never an unfair loss.
