# Qi Aura Simulator — Game Design

**Platform:** Roblox · **Project:** `qi-aura-simulator` · **Last updated:** October 31, 2026

The single design reference for the game: what is fixed, what is built, and what comes next.
Exact numbers live in code and data, and the tables below are generated from them:

- `src/shared/GameConfig.lua`: ranks, Qinggong, pets, eggs and relics.
- `tools/blender/world/layout.py`: island positions and the bridges between them.
- `python3 tools/balance_report.py`: the current pacing.

---

## 0. Fixed directives

These never change without an explicit decision from the project owner.

- **Ranks** stay as designed (section 2).
- **Eggs** stay as designed: their pets, pools, chances and themes (section 5).
- **No mistakes.** Every pet, egg, island and effect is checked against this document before it is built. For a pet, that means its egg, rarity and theme.
- **Every pet and every guardian has expressive eyes**: never a plain glowing ball. A guardian's eye is an almond iris with a slit pupil and lids that give it a look (`guardian_kit.eye`), and its rig makes it live (blinks, glares).
- **Aura concept** stays as designed (section 4). The bar is not "looks like Sol's RNG": it is to genuinely compete with, and aim to surpass, Sol's RNG's most impressive auras.
- **No generic style.** Islands, pets and effects are original Blender work with their own silhouette and identity. Nothing is a recoloured copy of another piece.
- **No Chinese text** anywhere in the game: not in the UI, icons, signs or names ("people might not want to play the game because there is chinese text", November 3, 2026). The wuxia feel comes from art, effects and English names.
- **The interface is the cultivator's System** (November 3, 2026: "make it more like a game system status from solo leveling"). It is an original take on the genre, nothing copied: translucent blue windows with a glowing edge and bracketed headers such as [ STATUS ] (`client/UI`: UiTheme, UiKit, Hud). The owner tried a colourful version on their phone on November 4, 2026, and chose this one: "the UI is way too colorful, I'd actually preferred the blue one". The icons stay full colour ("too transparent and no life at all" as thin lines), so they carry the colour on the blue.
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
2. **Movement as mastery:** a bridge leads from Yggdrasil, the hub, to each other island, sealed by a Qi barrier that only opens at the island's unlock rank. Players run, leap with Qinggong or (later) ride the sword along it. Qinggong's air leaps reach the high places on the islands.
3. **Collecting and discovery:** pets, relics and hidden places reward exploration.
4. **Active and passive play:** cultivate anywhere, or at the Qi Spring for a bonus.
5. **Player expression:** the chosen aura pet sets the look of the aura.
6. **Fair, secure multiplayer:** the server validates every reward, rank-up and hatch.
7. **Original, maintainable work:** our own models, effects, UI and code.

### Core loop (built)

1. **Cultivate** to earn Qi. The Qi Spring and equipped pets increase it.
2. **Rank up** when the next rank's Qi requirement is met. Qi is not spent. Qi comes from cultivating, and in bursts from securing a guardian's egg (section 7).
3. **Unlock** more air leaps, eggs, islands and relics as ranks rise.
4. **Hatch eggs** for pets and **equip three** for their Qi bonuses.
5. **Choose an aura pet** to style the aura.
6. Qinggong to new islands, find relics and better eggs, and repeat.

### The quest path (first steps November 3, 2026; the rest November 4, 2026)

A new player is walked through the loop by the quests, one at a time in the [ QUEST ] panel (top right), each paying Spirit Stones (`GameConfig.Quests`). The first seven (270 stones in all):
1. Gather 100 Qi.
2. Equip the starter Aqua Wisp.
3. Break through to Qi Gatherer.
4. An air leap.
5. Strike the Stone Lion.
6. Steal an egg.
7. Hatch it at the Hatching Altar.


Then the path on, so a player always has a next goal (steps 8 to 23): buy a weapon; the Root of the Island's relic; cross to Jade Grove; secure a Mantis Sage egg; Qi Awakener; cross to Ember Peak; secure an Ember Xuanwu egg; forge a weapon; Foundation Initiate (sword flight); Soul Awakening; cross to Moonlit Isle; secure a Tiangou egg; Divine Initiate; cross to Origin Abyss; secure a Pangu egg; Eternal Origin. **Append only:** a save holds its step number.

- **The server decides** (`server/Quests`): it checks the current quest against the player's Qi, rank, pets, weapons, relics, island and carried egg, and the air leaps, guardian strikes and secured eggs it sees. The step is saved (`Quest`, save version 9).
- **Skip:** a player can skip them all, which asks "SURE?" and pays nothing.
- **Existing saves** were marked done at step 8 (migration 8), so they skip the first seven and start the path on at step 8.

### Core loop (planned): guardians and egg theft

Defeating a guardian is not the goal. **Stealing its egg and escaping with it is.**
Cultivate → train Qinggong → find an island's guardian → weaken it → take an egg from the stands
behind it → escape the enraged pursuit home to Yggdrasil → hatch it at the Hatching Altar → grow
stronger.
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
| Qi Initiate | 1 | 22 | Yggdrasil |
| Qi Gatherer | 2 | 24 | Jade Grove |
| Qi Awakener | 3 | 26 | Ember Peak |
| Foundation Initiate | 4 | 28 | Moonlit Isle |
| Perfect Foundation | 5 | 30 | — |
| Divine Initiate | 6 | 32 | Origin Abyss |
| Void Walker | 7 | 34 | The Void Shard above Origin Abyss |
| Dao Seeker | 8 | 44 | — |
| Primordial Awakening | 9 | 54 | — |
| Eternal Initiate | 10 | 64 | — |
| Eternal Origin | 11 | 76 | — |

The last four rows were added on November 2, 2026, when the owner found the speed at max realm wasn't enough (it had stopped growing at Void Walker): each of the last realms is a big step faster, and the highest rank runs at 76.

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

**Leap effects** (`src/client/Qinggong/QinggongFx.lua`): the cultivator rides a current of Qi rather than simply jumping.

| Moment | Effect |
|---|---|
| Takeoff (jump from the ground) | A Qi formation blooms over a turning vortex under the feet, with rising wind streaks and puffs of auspicious cloud |
| Air leap | The foot steps on the void: a small formation, a vortex and a ripple ring open, clouds burst from the step and linger, streaks shoot downward |
| Rising after a leap | Energy trails from the feet, a silk ribbon from the shoulders, a current of Qi spiralling round the body. The legs stride like climbing steps in the air: the driving knee thrusts up while the other leg pushes off, arms swinging opposite, then both knees tuck. The legs alternate: the ground jump drives the right knee, the first air leap the left, the second the right, and so on |
| Glide | Riding a cloud: clouds held under the feet, small wisps shed behind, wind lines rushing past; crane-stance glide pose |
| Running (on the ground, from 19 studs/s) | A wind trail (the owner's request, November 2, 2026): a band of wispy wind streaks streams back from each shoulder (the owner's chosen trail texture, "Images/Trails15", asset 124753331461910), a bright wind line from each hand, wind lines rush past the body and the stride kicks up wind-blown dust, all stronger the faster the run (full from 64 studs/s). Each client reads every runner's own movement, so it needs no relay |
| Landing | A starburst flare, a formation flash, two shockwave rings, sharp Qi spikes, rolling cloud and glittering Qi mist, scaled by impact speed |

- The colour follows the realm: azure (Qi Awakening, Qi Foundation), jade (Spirit Core, Spirit Soul), gold (Ascendant, Immortal), violet (Divine and above).
- Textures (formation, shockwave, cloud sheet, spike, streak, ribbon) are drawn by `tools/blender/vfx/qinggong_textures.py`. The cloud sheet holds four auspicious-cloud shapes; each particle picks one.
- From the PDS' Particles & Models Kit: a soft fog puff gives every cloud burst and the riding cloud their volume (the line-drawn clouds ride on a bank of it), plus a vortex under the formations, a starburst flare and glittering Qi mist at landing.
- Effects play at once for the player and are relayed by the server to everyone else (cosmetic only, rate-limited); other players' effects are skipped beyond 250 studs and use fewer particles.

### Stamina, dash and sword flight (November 1, 2026)

Decided by the owner:
- stamina fuels only dashes and sword flight;
- sword flight unlocks at Foundation Initiate;
- Qi barriers still hold for flyers.

- **Stamina:** one bar under the air-leap pips.
  - Air leaps keep their charges and glide stays free.
  - It refills after a 0.6 s pause: 32 per second on the ground, 14 in the air, none while flying.
- **Dash** (Q, gamepad B, or the touch Dash button): a 0.2 s burst along the move direction (or facing), on the ground or in the air.
  - It costs 25 stamina, with a 0.45 s cooldown.
  - A gust of Qi goes with it: wind streaks stream back, a soft cloud puffs out where it set off, and a faint ripple opens.
- **Sword flight** (G, gamepad Y, or the touch Sword button): the cultivator stands on a flying jian.
  - **Controls:** move with the camera (look up or down to climb or dive), hold jump to rise and Ctrl, C or L2 to sink. Still, it hovers.
  - **Cost:** 8 stamina per second moving, 4 hovering; take-off needs 25. It lands itself when stamina runs out.
  - **Stance:** upright on the blade, one foot forward, a hand raised in a sword gesture; moving, it sinks lower and leans into the speed.
  - **On the server:** `FlightService` checks the rank, puts the sword under the feet in `Workspace.FlyingSwords` and caps a flight at a full bar spent hovering.
  - **The barriers still hold:** WorldService returns anyone below a bridge's rank who reaches it or its island, at any height.
  - **Relics too:** a flyer can reach the Void Shard early but can't claim it, because the claim is rank-checked.
- **The flying sword** (`tools/blender/weapons/flying_sword.py`, 8.3 studs long): **a blade whose cutting edge is Qi**, an original design whose identity is in its shape, readable from above while it is ridden.
  - **The blade:** a narrow dark-gold spine with a band of gold cloud scrolls raised along it, and two bright lines inlaid beside the scrolls. The whole cutting edge is translucent glowing Qi in the rider's realm colour (azure, jade, gold or violet). It is narrow at the guard and flares toward the tip in soft flame licks, and the point itself is pure Qi.
  - **The hilt** is gold and white like the owner's Murim robes: broad flame-tongue wings swept back round a white-jade disc in a gold rim, a white silk grip bound in gold cord, and a gold flame finial.
  - **In flight:** a soft wake trails the blade and a white silk ribbon edged in the realm's colour streams from the pommel.
  - **Why it was redesigned:** the first version was a plain steel jian. The owner called it generic: its outline was the default sword, its details sat at the hilt under the rider, and they lived in the texture.

| Rank | Stamina | Dash speed | Flight speed |
|---|---|---|---|
| Qi Initiate | 100 | 70 | — |
| Qi Gatherer | 110 | 74 | — |
| Qi Awakener | 120 | 78 | — |
| Foundation Initiate | 135 | 82 | 48 |
| Perfect Foundation | 150 | 86 | 56 |
| Divine Initiate | 170 | 92 | 64 |
| Void Walker | 190 | 100 | 72 |
| Dao Seeker | 215 | 115 | 88 |
| Primordial Awakening | 240 | 130 | 104 |
| Eternal Initiate | 270 | 150 | 120 |
| Eternal Origin | 300 | 170 | 140 |

---

## 3. Pets

Pets give **Qi bonuses** (every equipped pet) and **aura style** (the one chosen aura pet). Players equip up to **three** and own up to 50.

**Rarities**, commonest first: Common, Uncommon, Rare, Epic, Legendary, Mythical, Secret.

- Rarer pets give more Qi.
- Pets from eggs that unlock later are stronger too, about +6% per rank of the egg's required rank, so every new egg is worth hatching.

**Roster:** all 60 pets from the original concept are in the game, plus the retired Nine-Tail Moonfox.

- **★ = sculpted in Blender:** source at `tools/blender/pets/<EggId>/<PetId>.blend`, exported to `assets/pets/<EggId>/`. A pet sits under the first egg that drops it.
- **Unmarked pets** use procedural low-poly models (`src/client/Pets/PetArchetypes.lua`) until they get their own Blender model.
- **Every pet is its own species**, with its own anatomy, silhouette and face. No two share a body plan or head design, and every pet has expressive eyes.

### Animated pets and their specials

**How they're built**

- Animated pets are exported as separate jointed parts (`tools/blender/export_pet.py --rig`).
- Each one is animated in code by `src/client/Pets/PetRig.lua`, with an idle pose, a moving pose, a flying pose and a special.

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

**Beginner Qi Egg (Yggdrasil)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Aqua Wisp ★ | Common | Water | +10% |
| Ember Wyrm ★ | Uncommon | Fire | +20% |
| Lunar Hopper ★ | Rare | Moonlight | +35% |
| Volt Fox ★ | Epic | Lightning | +50% |
| Golden Kirin ★ | Legendary | Nature | +60% |
| Astral Whale ★ | Mythical | Cosmic | +100% |
| Origin Serpent ★ | Secret | Primordial | +150% |

**Spirit Breeze Egg (Yggdrasil)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Wind Sprite | Common | Wind | +10% |
| Cloud Sheep ★ | Uncommon | Clouds | +25% |
| Spirit Crane ★ | Rare | Spiritual energy | +40% |
| Azure Sky Dragon ★ | Epic | Wind and sky | +60% |
| Stormhorn Kirin | Legendary | Storms | +70% |

**Elemental Core Egg (Yggdrasil)**

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

**Realm auras (the cultivation aura, live since November 3, 2026)**

- **Only while meditating** (the owner, November 4, 2026: "there should be no aura, if the player is not meditating"): a cultivating player wears their realm's aura, built by `src/client/Auras/RealmAura.lua`. It builds up when they start and clears when they stop. Realm 4's ground layers quicken with it.
- **Twelve realms:** each has its own layers. Palettes come from the owner's `src/shared/AuraConfig.lua`, matched to the rank's `Realm` name. The sub-rank (`Level` 1–5) moves it along one continuous level, so a breakthrough never looks weaker.
- **On every realm:** the owner's body aura (smoke, a dark shadow, sparks, star glints), fainter at low Qi and bigger at high Qi.
- **Top-realm meshes** are templates in `ReplicatedStorage.AuraMeshes.TopTier`.
- **Rebuilds** happen on rank-up and respawn; the aura goes on death.
- **Culling:** other players' auras switch off past 120 studs from the camera. Roblox draws at most 31 Highlights per client.
- **One source of truth:** the Studio test range (`workspace.AuraTestRange`) uses the same module, so a realm enhanced there is the realm the game shows.

**Pet designs over the realm aura:** an equipped Aqua Wisp or Ember Wyrm adds its design (below) on top of the realm aura while the player meditates. The default (Verdant Gale) and the element-coloured flame aura no longer show; the realm aura is the cultivation look.

**Character auras** (one module per aura, all on the `CharacterAura` interface: build, show, hide, pulse, update, destroy)

- **Shared pieces:**
  - Every aura is built on the shared helpers in `src/client/Auras/AuraKit.lua`.
  - Each is registered in `DESIGNS` in `src/client/Auras/CharacterAura.lua`.
  - Its settings live in `src/client/Auras/AuraStyles.lua`, and its meshes in `ReplicatedStorage.AuraMeshes` (sources in `tools/blender/auras`).
- **Stages:** each aura charges up, then grows from idle to charged to awakened the longer the player cultivates.
- **Fallback:** without its meshes, a pet falls back to the anime flame aura, which is coloured by the pet's element.

| Pet | Aura | What it is | Module |
|---|---|---|---|
| Aqua Wisp | **Tidecaller Sanctum** | The player meditates on a blooming water lotus inside a tidal vortex over a pool of caustic light. Spirit koi join at the charged stage; a breaking-wave crown and four water spouts rise when awakened. | `TidecallerAura.lua` |
| Ember Wyrm | **Ember Crucible** | Fast-spinning ember slashes and cloud under the player; rising debris, sparkles, a twin vortex of energy beams and body flames. The spirit bead wyrm and orbit trails join when charged; a molten fire halo forms behind the head when awakened. | `EmberCrucibleAura.lua` |
| No aura pet | **Verdant Gale** (default) | A lime swirl and slash ring spinning on the ground, a twisting wind wisp rising through the body, rising streaks, a soft lime glow and light. | `VerdantGaleAura.lua` |

**Pet auras:** each equipped pet of a cultivating player shows its own element's aura (`src/client/Auras/AuraBuilder.lua`). Aqua Wisp and Golden Kirin are done.

**Poses and breakthroughs**

- A flying pose while airborne, and each realm's own meditation idle while cultivating (below).
- A burst effect on every rank-up, bigger at milestones.

**Next:** every remaining element gets its own aura concept. Aqua Wisp's water aura is the model for this, not a shared aura recoloured.

### The twelve meditation idles (the owner, November 4, 2026)

"Make 12 unique and different idle, there should be no similar or reuse idle", and "the beginner idle should be lotus sit". Each realm has its own (`client/Character/MeditationPoses.lua`, played by `PoseController`, easing in over 3 seconds). The pose places the body itself, on the ground or up on the air; the character's own height doesn't change, and a cultivator can't walk or jump (`MeditationStillness`).

| Realm | Idle |
|---|---|
| Qi Awakening | The lotus seat on the ground, hands on the knees, a slow deep breath |
| Qi Foundation | Standing post: knees soft, the arms rounded as if round a tree, sinking and rising |
| Spirit Core | Kneeling, the hands circling each other round the core at the belly, head bowed |
| Spirit Soul | The crane: on one leg, the knee drawn high, the arms spread low like wings |
| Ascendant Realm | Floating Ascension (the owner's): reclined on the air, a wide wingspan, a knee to the sky |
| Immortal Realm | Standing on air: sword fingers at the chest, a hand behind the back, chin up |
| Divine Realm | On one knee in the air, an arm driven straight at the heavens |
| Cosmic Realm | Upside down, legs crossed above, the arms spread, orbiting slowly |
| Void Realm | Curled tight, knees to chest, tumbling end over end |
| Heavenly Dao | Cloud hands: a low stance, the hands passing in unbroken circles |
| Primordial Realm | Holding up the sky: a wide squat, both palms pressing up, the strain trembling through the body |
| Eternal Transcendence | Spread as a star, face to the sky, turning high up |

The owner's account always takes Floating Ascension, which their own aura was built round. To review any idle on any account, set `MeditationPoses.Preview` to its realm number. Tested in Play: all twelve run with no errors, planted feet stay flat within 0.07 studs of the floor, and walking and jumping return on stopping.

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

- **Hatching** (since November 2, 2026, section 7): only at Yggdrasil's **Hatching Altar**, from the player's **egg inventory** (`EggInventory`, saved as `Eggs`, at most 99 of each), filled by carrying eggs home from the guardians' stands. The stands no longer hatch; their prompt is "Take". (Before: free stand hatches with a 45-second cooldown.)
- **Chances:** follow the rarity scale: Common 45%, Uncommon 27%, Rare 15%, Epic 8%, Legendary 4%, Mythical 0.9%, Secret 0.1%.
- **Missing rarities:** when an egg has no pet of some rarity, its share goes to the next pet that has one. So later eggs give rarer pets far more often.

| Island | Egg | Needs | Chances |
|---|---|---|---|
| Yggdrasil | Beginner Qi Egg | Qi Initiate | Aqua Wisp 45%, Ember Wyrm 27%, Lunar Hopper 15%, Volt Fox 8%, Golden Kirin 4%, Astral Whale 0.9%, Origin Serpent 0.1% |
| Yggdrasil | Spirit Breeze Egg | Qi Adept | Wind Sprite 45%, Cloud Sheep 27%, Spirit Crane 15%, Azure Sky Dragon 8%, Stormhorn Kirin 5% |
| Yggdrasil | Elemental Core Egg | Foundation Initiate | Glacier Puff 45%, Thunder Jelly 27%, Crystal Beetle 15%, Gravity Imp 8%, Thunderclaw Drake 4%, Frostfang Serpent 1% |
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
- **In Studio:** an imported egg is stored with `WorldBuilder.storeEgg(model, eggId)` in `ServerStorage.EggMeshes.<EggId>`. `buildEggStands` places it at `GameConfig.EggStudsPerUnit` (1.3) studs per egg unit; the server's stand eggs and the auras use the same value.
- **All fifteen eggs are recreated.** The Moonlit Isle and Origin Abyss eggs are their own designs (`eggs_moon.py`, `eggs_origin.py`, November 1, 2026): the owner asked for each to be invented after its name, not the sheet's family designs.

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
| Celestial Egg | A piece of the night sky: glossy midnight lacquer with soft clouds of violet and teal nebula and a dusting of stars in it, cradled in a silver crescent moon whose high horn holds a glowing blue pearl, a gold constellation of six glowing stars across its front |
| Astral Sanctum Egg | A moonstone shrine (milky white with a blue and lavender sheen): six pointed-arch windows round its middle, framed in gold with a mullion and a tracery ring, glowing violet with the light inside; small gold stars between them; plinth bands round its foot; a ribbed gold dome on its crown whose spire holds a glowing violet orb |
| Heavenly Throne Egg | A pearl egg wearing a gold coronet of seven jewel-tipped tines, a gold sun on its front (an eight-pointed burst in a ring round a glowing cabochon, a curling flourish to either side), seated on a cushion of soft cloud that swells into armrests, a gold mandorla behind it as the throne's back: a pointed oval frame with a glowing inner line, rays fanning out from behind the egg, a jewel on a gold star at its point |
| Forbidden Origin Egg | The sealed egg: ancient near-black seal-stone ringed by two bands of glowing violet seal-script glyphs, every glyph its own, bound by two aged bronze chains (verdigris in the hollows, like the shrine's thorns) crossing over its front and locked where they cross by a domed bronze seal with a glowing rune |
| Void Rift Egg | The egg torn open: a shell of polished black void glass split by a jagged rift down its front, the torn edges glowing blue; through it the hollow inside is a starry blue void with a glowing heart floating in it, and jagged fragments of shell drift just off the tear |
| Primordial Abyss Egg | The first egg: primordial stone in warped dark layers with thin ochre seams, a great fossil ammonite coiled on its front with magenta light in its spiral seam and its mouth, a bronze clockwork belt of gear teeth round its base and a small gear set in each shoulder |
| Ancient Grove Egg | Carved wood planks in fourteen upright columns, each split at its own heights, every plank its own tone; dark bark in the grooves, pale heartwood showing at the crown. A mossy trunk behind it sends roots gripping the egg and branches spreading into lumpy crowns of leaves, and a spiral of Qi glows on its front |

The older family designs (`tools/blender/eggs/Eggs.blend`) are no longer used by any egg.

### Egg auras

Every egg on its stand has its own aura, built in the Workspace from particle emitters, trails, beams, billboards, glowing image planes and lights, with no meshes and no flipbooks, so it can be tuned in Studio and with VFX Studio.

- **Built by** `src/worldbuild/EggAuraVFX.lua`, one recipe per egg: `VFX.build("<Island>")` rebuilds `FloatingIslands.<Island>.EggAuras`. Each aura is a Model tagged `EggAura` that streams in whole.
- **Animated by** `src/client/Auras/EggAura.client.lua` (a LocalScript of its own), from attributes on the instances (listed in both modules' headers), so an aura tuned by hand keeps working.
- **Tuning:** tune an aura on its instances in Studio, then copy the values into its recipe, so a rebuild keeps them.
- **Depth and rhythm, never flat:**
  - No two orbiting pieces share a speed, radius and plane. Some run the other way, and each bobs on its own period.
  - Rings precess (`Wobble`) as they spin.
  - Ribbons shed dust or feathers from their heads, which leaves spiral wakes. Since November 1, 2026 every ribbon, stream and vine is a soft glow stretched along it (`T.SoftGlow`, Stretch), and no egg aura has a flat sigil, ring or sprite (the owner: "soft, smooth animation, no edges, no flat stuffs"); only the Inferno keeps its heat ripples, to the owner's own spec.
  - Mist and an updraft column give the aura volume.
  - The whole aura breathes (`Breath`, `BreathPeriod`): speed, glow and ring size swell and ease back, at each egg's own pace (table below). `BreathShape = "Heartbeat"` makes it beat instead: a double thump, then a rest (no aura uses it since Ember Peak's were removed).
  - Things can move to the beat: beams with `BeatWidth` swell, orbiting attachments with `BeatReach` are flung out, emitters and ripples with `BeatEmit` fire on each thump, `BeatHighlight` throbs a Highlight on the egg, and `BeatScreen` pulses the nearby player's screen (ColorCorrection and Bloom, client-only).
  - **Every aura is its own invention, built from the whole toolkit** (ParticleEmitter, Attachment, Beam, Trail, PointLight, Highlight, BillboardGui, SurfaceGui, TweenService, ColorCorrection, Bloom), never the same ring-and-sigil skeleton recoloured.
  - Rocks can orbit too: parts with `Orbit` carry their glowing cores and tumble (`Tumble`). With `AvoidAngle` and `AvoidRadius` an orbit pulls in as it passes a neighbouring egg, however far a pulse throws it (the Phoenix Altar's stands are only 5.9 studs apart; the Inferno's rocks were swept in Play over every angle, bob, pulse and hatch push and stay at least a third of a stud clear of both eggs). An aura with `PulseInterval` sends an energy pulse through itself every few seconds (`PulseJitter`), each piece answering `PulseDelay` later so nothing pulses at once: the aura speeds up (`PulseSpeed`) and glows (`PulseGlow`), pieces are thrown out (`PulseReach`), beams and planes swell (`PulseWidth`, `PulseSwell`), emitters and ripples fire (`PulseEmit`), and with `PulseEggGlow` the egg's own lava heats toward that colour. An aura with `CyclePeriod` runs a life cycle instead: `CycleRebirth` marks the rebirth in it (a screen flash with `CycleScreen`). Along the cycle emitters follow `CycleRate` or fire `CycleEmit` at `CycleAt`, lights follow `CycleBrightness` and `CycleColor`, the egg's glowing parts cool and heat between `CycleEggCold` and `CycleEggHot` along `CycleEggGlow`, a Highlight follows `CycleHighlight`, `CycleOutline` and `CycleFill`, and attachments sweep along a curve (`SweepFrom`, `SweepVia`, `SweepTo`, `SweepCurve`), which opens trails like wings. Every aura can be tuned by hand with `Intensity`, `Density`, `OrbitSpeed`, `LightIntensity` and `Visible`.
- **Idle** (no periodic pulse, which the owner judged unnecessary, except where an aura's own design calls for one: the Inferno's energy pulse): everything turns, orbits, drifts and emits on its own timing.
- **No hatch at the stands:** the stand aura's gather and burst (`EggAura.hatch`) was removed on November 2, 2026, with the data only it used (the `DrawIn` and `Flash` emitters, the Ember and Celestial flares, `HatchEmit`, `GatherRate`, `Gather`, `GatherPull`), from the builder and from the place. Hatching plays at the altar (`HatchCeremony`).
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
  - The Jade Grove stands are 7.5 studs apart (Yggdrasil's are 10), so its auras stay within about 3.3 studs of the egg.
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
  - `T.SmallGlow`'s glow is a speck in its image: at mote sizes it is invisible, so soft motes use `T.SoftGlow`. On the bright, white Moonlit Isle, motes need a deeper colour at lower light emission to show.
  - Neon turns violet (8a4dff, b04fff, even 7a3cff) pink; a bluer violet (643cff) stays violet.
  - On Origin Abyss the thorn branches cradle the eggs, so its eggs' lights are short and soft (range 6, brightness 0.8, `EGG_LIGHT` in WorldBuilder) and its auras add no light: three wide coloured lights painted the bronze red and violet.
  - The detailed eggs are taller than the recipes' measures, so their auras are lifted (`lift` in `EggAuraVFX`). Effects that belong to a part of the model (a gem, a lotus, a leaf crown) are anchored to points measured on the model in Blender (`anchor`).

| Egg | Breath | Aura |
|---|---|---|
| Beginner Qi | 5 s, calm | **Calm Qi, soft and slow** (redone on November 1, 2026 with every older aura: soft, smooth, no edges, nothing flat). Two soft wisps of Qi glide round it shedding Qi dust, motes rise like breath, soft twinkles of light, a soft halo and a gentle updraft. No mandala, rings or crystal sprites. |
| Spirit Breeze | 5 s, easy | **A soft breeze** (redone on November 1, 2026 to the owner's direction: soft, smooth, no edges, nothing flat). Three wisps of wind drift round it on a slow helix, auspicious clouds billow off the bowl's lip, feathers ride a gentle updraught under a faint halo. No sigil or rings. |
| Elemental Core | 4 s, a steady hum | **Concentrated elements, soft.** Four element streams (cyan, gold, blue, amber) rise off the rim as soft arcs of light and meet above the crown in a soft glow. Four element orbs glide round on their own orbits with soft tails, blue and gold motes rise, and soft light breathes off the core. No sigils, gyroscope bands or pointed sparks. |
| Jade Spirit | 4.5 s, growing | **Living jade, soft.** Three soft vines of light twine up from the rim to the crown, each at its own pace. Three soft currents of Qi drift round on their own planes, shedding leaves that tumble slowly in their wake. Qi breathes out of the jade-leaf gem in a soft green glow and rising motes, with soft twinkles. No formation, rings or leaf sprites. |
| Bloomwood | 6 s, dreamy | **Eternal blossom, soft and slow** (redone on November 1, 2026, like Spirit Breeze). Two soft wisps of blossom wind drift round it shedding slowly tumbling petals, petals float up off the rim and drift back down, golden pollen rises out of both lotus hearts with soft twinkles, and a soft glow surrounds the emblem's heart. No mandala, rings or blossom sprites; no halo (on the pale crystal egg it reads as a milky veil). |
| Ancient Grove | 7 s, deep and slow | **The world tree's heartbeat, soft.** Five soft roots of light climb the stand's golden roots up into the egg. A slow spiral of Qi climbs round it, and four forest spirits wander round on slow looping paths with soft tails. The egg's own five leaf crowns come alive: light glows inside each, fireflies drift out, and leaves fall from them, gold and green by turns. No sigils, vortex or ring of old light. |
| Inferno | 3.2 s, simmering; a pulse every 6 ± 1.5 s | **A miniature volcano with an unstable molten core.** Its own lava cracks are its light (they heat toward gold on each pulse), with a low warm light; no rings round it or at its foot. Sparks spit out of its cracks, and three spark comets race round it on tilted paths, each shedding a stream of hot sparks. Six broken volcanic rocks (modelled and baked in Blender, a slab, a shard, a wedge, a chunk, a splinter and a cinder, lava glowing in their cracks) orbit at their own distances, tumbling and shedding embers, and pull in as they pass the Magma Heart beside it. Four molten ribbons spiral round it, flames licking off them. Beneath it only ripples of heat and three vents: no sigil or ring under the egg. Embers rise, ash drifts, cinders are thrown up now and then. Every few seconds an energy pulse runs through it, each part in turn: the cracks heat, sparks burst from them and the comets, the rocks are thrown out, flames surge, the vents erupt one after another. |
| Magma Heart | — | **A blazing fire.** Eight flame columns stand round the egg just inside its widest girth, so flames lick up every side of it: bright yellow at the base through orange and red to dark red at the tips, flickering (each column's rate and speed jump every 0.15 s), a faster yellow core in every other column, embers drifting up. Roblox's built-in fire textures, no Fire object, no flipbook; tuned on a test fire on the Starting Island with the owner. |
| Celestial | 6 s, slow | **The night breathing.** Soft points of starlight swell and fade as they drift up round it, two soft shooting stars (a glowing head, a soft tail) glide round it on their own tilted paths, the pearl on its crescent breathes a blue glow, under a faint night-blue haze. |
| Astral Sanctum | 5.5 s | **Light from the sanctum.** Soft violet light drifts out through its windows and up, three lantern spirits circle it at their own heights and paces, each leaving a fading tail of light, and the orb on its spire breathes. |
| Heavenly Throne | 7 s, the slowest | **Radiance.** A soft deep-gold glow breathes behind the egg, filling its mandorla; golden dust rises off its cushion of cloud, faint wisps of cloud drift from it, and the sun jewel on its front breathes. |
| Forbidden Origin | 6.5 s | **The seal drinking light.** Soft violet motes are drawn in toward the seal from all round it, and every few seconds a slow soft swell of violet spreads from the seal and fades, as if something behind it stirs. |
| Void Rift | 5 s | **The rift breathing.** Blue void light seeps out through the tear and drifts away, the heart breathes in the void inside, and two deep-blue wisps loop slowly round it on steep tilts, like space folding. |
| Primordial Abyss | 8 s, the slowest | **Deep time.** Three soft lights sweep round it at three heights like a clock's hands, each a third the speed of the one below and drawing a short arc of light; the ammonite's mouth breathes magenta and faint pink motes drift out of its spiral. |
| Phoenix Ash | a 15 s cycle | **The Ash Cycle:** the egg dies and is reborn every 15 seconds. **Ash:** its veins and phoenix emblem dim to a smoulder under a dull ember rim, pale ash falls round it (the one aura on the altar where things fall) and a thin curl of smoke rises from its crown. **Kindling:** embers wink awake round it and the glow climbs back. **Rebirth:** the ash rushes up catching fire gold, two wings of gold light sweep open behind its own sculpted wings shedding golden feathers, a sunburst blooms over its crown, its rim races through the prism's colours (its rarest pet is the Prismatic Phoenix), its light blazes gold and a nearby player's screen flashes warm. **Burning down:** the wings fold, their feathers greying into ash as they fall, and the cycle begins again. The wings keep 1.76 studs clear of the Magma Heart egg (a raycast sweep over the whole wing path). |

**Egg stands today** (section 7): each island's three stands stand behind its guardian; their eggs are what a thief carries home. A taken egg's stand stays empty, then respawns (section 7).

---

## 6. World

Five floating islands built from original Blender work: terrain tops, sculpted undersides, landmarks and set pieces. **Yggdrasil** is the hub at the centre, about 500 studs across (three times the others), and a bridge leaves it for each other island.

**Layout** (since November 1, 2026, the owner's map; `tools/blender/world/layout.py` is the one source):
- Every island's ground is at Y 200. The four outer islands fan out north of Yggdrasil, west to east in unlock order, and the harder an island, the farther it stands (the owner's rule, November 2, 2026): each bridge takes about four seconds longer to run than the last at its unlock rank's run speed. Each island is turned by quarter turns so its gate faces the hub (terrain grids stay exact; `Turns` in the terrain data, `WorldBuilder.islandFrame` and `WorldConfig.frame` carry island-local positions into the world).
- Yggdrasil replaced the Starting Island, which carried its content over: the Beginner eggs, the Stone Lion, the Qi Spring, the Root of the Island and all its kit pieces (stored in Studio as `WorldKit.Yggdrasil`).

**Bridges:**
- Paths in `layout.py` (`BRIDGES`; `--write` generates `src/worldbuild/Placements/Bridges.lua`), built by `WorldBuilder.buildBridges()` into `FloatingIslands.Bridges`. They fan out from Yggdrasil's north rim as on the owner's map, each one straight span from Yggdrasil's ground to just inside its island's gate (no landings: the owner's call). Level, with a gentle arch (at most about 6°): Jade 191 studs, Ember 314, Moonlit 461, Origin 649, about 8, 12, 16 and 20 seconds to run at each unlock rank's speed (24 to 32 studs/s); the sword flies the last two in about 10.
- A deck 40 studs wide (doubled twice at the owner's request; room to ride the sword along it) with rails. Both ends are carried onto their islands by a solid abutment.
- At each bridge's start a gate holds a **Qi barrier** (tagged `QiBarrier`, with the destination's `RankId`): solid until the player reaches that rank, then open to them (`BridgeBarriers.client`). A player below the rank found on the bridge past the gate, or on the island it leads to, is put back in front of the gate (`WorldService`).
- Each bridge wears its island's kit, modelled in Blender (`tools/blender/world/bridge_kits.py` → `assets/world/Bridges/<Theme>Bridge.fbx`, piece offsets in `Placements/BridgeKits.lua`), laid by `buildBridges` over the walkable blockout:
  - **Jade Grove:** plank deck with lattice rails, carved jade posts, vines; a jade gate under a two-tier curved roof.
  - **Ember Peak:** hexagonal basalt column tops with lava in the seams; a gate of basalt column clusters.
  - **Moonlit Isle:** moonstone treads with gold handrails and crescent-topped posts; a gate under a great gold crescent.
  - **Origin Abyss:** cracked ancient slabs with void light in the cracks; a ruined gate split by void light.
  - Moonlit's level deck (moonstone pavers with gold seams) is its extra kit (`MoonBridgeExtra.fbx`, `BK.export("Moon", extra=True)`), added after the Moon kit was baked. Every kit was rebuilt at the 40-stud width, so posts and gates keep their shape. Every bridge is dressed end to end.
- Decorative pieces that stand where a bridge comes onto an island (rocks, shards, lilies, scattered trees: `WorldBuilder.ClearOfBridges`) are left out when the island's kit is placed, so a bridge can move or widen without re-running an island's scatter.
- Studio's importer turns each kit half round (x and z flip, as with the eggs); the builder turns each piece back.

| Island | Centre (studs), quarter turns | Feel | Relics |
|---|---|---|---|
| Yggdrasil | (0, 200, 0) | The World Tree and the spawn hub | Root of the Island (300 Qi, Qi Initiate) |
| Jade Grove | (−384, 200, −448), 0 | Ancient forest | Grove Heart, Jade Seed, Whispering Spring (800 Qi each, Qi Gatherer) |
| Ember Peak | (−128, 200, −696), 0 | Volcanic, lava pools | Ember Heart, Ashen Sigil, Caldera Crown (1,500 Qi each, Qi Awakener) |
| Moonlit Isle | (192, 200, −804), 0 | Pale and celestial | Moon Mirror, Star Well (20,000 Qi each, Soul Awakening) |
| Origin Abyss | (596, 200, −856), 0 | Hidden endgame: dark slate, void crystals and rifts, broken ruins | Origin Altar (250K Qi, Divine Initiate); the Void Shard high above it (1M Qi, Void Walker) |

**Bridge gates:** Jade Grove at Qi Gatherer, Ember Peak at Qi Awakener, Moonlit Isle at Soul Awakening, Origin Abyss at Divine Initiate. Moonlit's gate rose from Foundation Initiate on November 4, 2026 (the owner's decision): it opened about 90 minutes before the island's first egg and a guardian tuned for Soul Awakening could be used.

**Shared rules**

- **Relics:** each Spirit Relic gives a one-time Qi reward, and finds are saved.
- **Qi Spring:** the spring on Yggdrasil adds +50% Qi while cultivating in it.
- **Falling:** a player who falls 110 studs below the island they last stood on is returned to that island's checkpoint (on Yggdrasil, to their spawn slot). That line sits under the Root of the Island's cradle (86.5 down, the deepest place players stand) and above the PDS kit under Yggdrasil (its top 130.5 down), so a fall never strands anyone on the kit.
- **Hazards:** parts tagged `LavaHazard` (Ember Peak's lava) also return a player to their island's checkpoint on touch.

### Yggdrasil (built; its own meshes await import)

The World Tree stands at the centre; everything else rings it. Scripts: `ygg_island.py` (terrain and layout), `ygg_tree.py`, `ygg_meshes.py` (atlas, underside, export), `ygg_props.py` (kit and placements).

- **The World Tree:** an ancient ash about 200 studs tall. Seven buttress flutes spiral up its trunk, with Qi glowing cyan in the grooves and motes drifting up. Three great roots arch over the Root Court path and four sink into the mound. Six limbs spread into a crown of flat cloud pads in tiers, some gilded where the sun catches them, with golden seed-lanterns hanging under them on threads of light and aerial roots trailing from the limbs.
- **South:** the **Ascension Stele** (the leaderboard), the **Qi Compass** (the old spawn plaza, now the fallback spawn) and the Spawn Walk with the **six spawn slots**. Each slot is a stone dais with a jade inlay and a name stone; a player holds one while in the server, its ring lit gold and their name cut into the stone, and they spawn and return there (`WorldService`). With every slot taken, a player spawns at the Qi Compass. The server's player limit should be 6 (Game Settings).
- **West, the Market Terrace:** plots for the **Blacksmith** (exclusive weapons), the **Marketplace** and **Buy & Sell**, along a lane.
- **Plots** (`WorldBuilder.buildPlots`): each is paved, marked out by talisman stakes strung with sagging red cord, with a roofed notice board naming what is coming. A plot whose building stands (`WorldBuilder.Plots.<Name>.Built`) is left to it.
- **The Ascension Stele** (the leaderboard, built November 2, 2026, `WorldBuilder.buildLeaderboard`, `LeaderboardService`): an honour board like a memorial archway's, a dark slate board in a bronze frame on a stepped plinth between red-lacquered pillars, under a tiled roof whose corners sweep up, a pearl of Qi in a bronze cup on the ridge. It lists the ten cultivators with the most Qi across every server (an OrderedDataStore, `WorldConfig.Leaderboard`), with their rank; the top three in gold, silver and bronze. A player's Qi is written as their data loads, every two minutes while it changes, and as they leave; the board re-reads every minute. Without DataStores it ranks the players in the server. Tested in Play: the owner listed first at 4.18B.
- **The shops** (phase 2 of the weapons, `ygg_shops.py`, `Yggdrasil_Shops.fbx`, `Yggdrasil_Market.fbx`, `WorldBuilder.buildShops`), under the Stele's roof (`ygg_props.tiled_roof`) but each with its own idea:
  - **The Marketplace, the Coin-Tree Market** (November 4, 2026): a three-tier pagoda of jade-glazed tiles at the back of a courtyard; three striped stalls down each side, selling spirit peaches, silk, scrolls, elixir jars, uncut stones and gourds; a lacquer gate on the lane under a glazed roof; strings of red lanterns overhead; and at the centre a bronze money tree hung with glowing coins, with the prompt at its foot. **It sells spirit eggs for Spirit Stones** (the owner's choice, November 4, 2026: Spirit Stones, no Robux): every egg, from the player's required rank up, to hatch at the altar like a stolen one. The price is a weapon of the egg's realm (`Shop.marketEggPrice`, `SpiritStones.MarketEggShare`), 4 times what stealing one pays, with no Qi burst or element, so the guardians stay the better road. A pet's average sale value is under half the price for every egg (the highest is Forbidden Origin, at 49%), so buying eggs to sell the pets loses stones on average; a lucky rare pet can still sell for more. Tested through the real remote: too far, an unknown egg, a table, a 5,000-character string and too few stones are all refused; a real purchase took 60 stones and gave one egg (undone after).
  - **The Blacksmith, the Dragon-Kiln Forge:** a smoke-dark timber and stone smithy whose forge is a dragon's head of pale carved stone bursting from the dark back wall, fire licking inside its open jaws round a burning pearl, its eyes alight, its horns, mane and long whiskers bronze. Its bronze body coils up the round chimney and out through the roof, the tail curled over the smoking mouth. Before it an anvil with a half-forged blade glowing on it (the shop's prompt), a quench trough, bellows and coals; a rack of swords and spears along one wall.
  - **Buy & Sell, the Jade Scale:** a merchant's hall behind an open forecourt where a great bronze balance scale stands on jade paving, glowing Spirit Stones heaped in one pan and a spirit egg in the other (pets traded for stones); the shop's prompt is at its foot. Under the roof, a jade-topped counter before a wall of drawers; red paper lanterns at the eave's corners; the merchant's great bronze coin on the back wall.
  - Tested in Play (November 2, 2026): both prompts open their shops; walked from the lane to each prompt; buying and selling pass the reach check at the new prompt spots and are refused from across the island.
- **East:** the **Egg Garden** (Beginner Qi, Spirit Breeze and Elemental Core on the Starting Island's lotus pedestals, 10 studs apart), the **Stone Lion**'s lair north-west of it, and the **Qi Spring** on the rim, its waterfall pouring off the edge (the Starting Island's spring, carried over whole).
- **North:** a paved bridgehead and a waystone for each bridge.
- **Underside:** the Starting Island's stacked strata at Yggdrasil's scale, gripped by roots that climb out of the meadow, over the rim and down the strata to a taproot. Its lowest point stays above world Y 75: the PDS kit lies below.
- **Root of the Island:** from the south rim the great root winds down the cliffs, sixteen bracket-fungus shelves along it, to a bowl of roots under the strata holding the relic.
- **Nature:** spirit pines crowning low knolls near the rim, plum blossoms, mossy rocks and flowers.

### Jade Grove (built; doubled November 2, 2026)

**The owner's upgrade** (November 2, 2026, for every outer island, Yggdrasil unchanged): twice the size; the boss in the middle of the island guarding its three eggs; no obstacle in the middle, props round the sides; the bridges as they are. Jade Grove was rebuilt first for review. It is about 300 studs across, and moved out along its unchanged bridge (the bridge file regenerates byte-identical); the other islands fan apart the same way when they double (planned: each one's centre on its bridge's line, about its new radius past the bridge end; all four then clear each other by 45 studs or more).

- **Mantis Arena** (the middle): a dead-level ring of grass bordered by jade flagstones (radius 50), a path ringing it. The **Bamboo Mantis Sage**'s lair is its centre, facing the Grove Gate; the **three egg stands** (Jade Spirit, Bloomwood, Ancient Grove) stand in an arc 31 studs behind it, just past its engage radius. Nothing solid stands in it; jade lanterns and standing stones ring its edge between the paths.
- **Grove Gate** and the arrival terrace on the south-east rim, where the Jade bridge lands; a path leads straight into the arena.
- **Elder Jade Tree** to the north-east (Grove Heart in its hollow, Jade Seed in its crown, the fungus-shelf climb).
- **Whispering Hollow** to the north-west (the spring pool and the Whispering Spring).
- **Bloom Glade** to the south-west: the flagstone sanctuary ringed by standing stones, opening toward the arena. It is the Mantis Sage's safe zone, where a stolen egg is secured.
- **Ruin Court** to the south: broken pillars round a clearing.
- **Forest** ringing everything: ancient trees, bamboo, jade outcrops, ruin pillars, fallen logs, ferns and glowing mushrooms (about three times the old count).
- **Underside:** the faceted dark-jade mass, deeper (130 studs) with larger hanging jade crystals, moss curtains and vines round the longer rim.
- **Tested in Play:** walked from the bridge into the arena (3 s); the Sage woke at its engage radius, its attacks knocked back without throwing anyone off; weakened in 14 strikes; the egg stolen, the Sage leapt after the thief, and the egg was secured in the Bloom Glade after a 5.6 s run (it dropped its relic: Wind unlocked).

### Ember Peak (built; doubled November 2, 2026)

Columnar basalt is the island's signature, used for the cliffs, the climb, the altar and the underside. Doubled for the owner's upgrade like Jade Grove: about 300 studs across, moved out along its unchanged bridge.

- **Cinder Arena** (the middle): a dead-level basalt ring bordered by glowing cracked lava rock (radius 50), a path ringing it, braziers and basalt column clusters round its edge. Its centre is kept for Ember Peak's guardian (the Fire Guardian, still to design). At its back, the **Phoenix Altar**: three cinnabar-topped column pedestals, each on a pad of hexagonal basalt, holding the Inferno, Phoenix Ash (tallest, in the middle) and Magma Heart eggs.
- **Ember Gate:** the arrival on the south rim, two bundles of basalt columns with iron fire braziers under an obsidian lintel with a cinnabar plaque; braziers inside it; the path runs straight into the arena.
- **The volcano** (north, looming behind the eggs):
  - a crown of basalt columns rings its crater;
  - inside, a lava lake holds the **Caldera Crown** on a basalt pillar;
  - six basalt column steps climb its arena-facing flank as the Qinggong route to the rim.
- **Lava river:** it overflows a notch in the rim, runs down a carved channel to the north-west edge and pours off the island as a lavafall. Touching the lake or the river returns the player to Ember Peak's checkpoint.
- **Ember Forge** (east): ruined walls of stacked basalt blocks with a sooty chimney and anvils. The **Ember Heart** hovers over a hearth of glowing coals.
- **Ash Plain** (west): petrified trees around a cracked obsidian monolith carved with the glowing **Ashen Sigil**.
- **Underside:** hanging hexagonal basalt columns, like organ pipes (wider and deeper at the new size), with a magma core glowing through the gaps.
- **Dressing:** fire crystals, ember vents throwing sparks, basalt clusters and obsidian shards, about three times the old count, all round the arena.
- **Tested in Play:** from the bridge to the egg pedestals in 5 s, the prompt in reach; the lava river returns the player to the new checkpoint.

### Moonlit Isle (built; doubled November 2, 2026)

Seen from above, the island is a crescent moon: a full disc (about 250 studs across since the owner's upgrade) with a deep bay of sky cut out of its north, its horns curling around it. Moved out along its unchanged bridge.

- **Lunar Court** (the middle, a little south of the disc's centre): a level ring of moon paving bordered in salt-white stone (radius 50), ringed by hovering star lanterns along its path. Its centre is kept for Moonlit Isle's guardian (the Celestial Guardian, still to design). At its back, looking out over the bay, the three porcelain egg pedestals (a wide blue dish with gold bands at the lip and foot) hold the Celestial, Astral Sanctum and Heavenly Throne eggs.
- **Arrival:** the bridge lands on the south rim through the gold Crescent Arch; the path runs straight to the court.
- **Moon Mirror** (west): a dark reflective pool you can walk on, in a marble-and-gold rim. A curved bridge leads from its court-side bank to a moonstone lotus holding the **Moon Mirror** relic.
- **Star Well** (west horn): a marble well with a gold lip, brimming with glowing starlight, with the **Star Well** relic above it.
- **Celestial Pavilion** (east horn): eight porcelain pillars with gold crescent finials on a stepped marble platform, under a floating golden armillary (the eggs stood here before the upgrade).
- **Underside and cliffs:** marble cliffs with a gold band under the lip step inward into a belt of soft cloud, deeper at the new size. Moonstone geode crystals hang beneath, some of them glowing.
- **Dressing:** hovering porcelain star lanterns along every path, glowing frost lilies, moonstone shards, lunar rocks and spires on the horns, about three times the old count.
- **Tested in Play:** from the bridge to the egg pedestals in 4 s, the prompt in reach; across the Moon Mirror's bridge to its relic; a step into the bay returns the player to the checkpoint.

### Origin Abyss (built; doubled November 2, 2026)

The hidden endgame island, about 320 studs across since the owner's upgrade, moved out along its unchanged bridge. A void rift tears a chord across its far side; the court's side is level and open, the shelf beyond the rift raised and tilting up toward its far edge.

- **Void Court** (the middle): a level court of worn temple stone bordered by void-crystal crust (radius 50). Its centre is kept for Origin Abyss's guardian (the Primordial Guardian, still to design). At its back, the **egg plinths**: three obsidian plinths cracked with void light, each cradled by thorny bronze branches and set on a pad of hewn paving, holding the Forbidden Origin, Void Rift and Primordial Abyss eggs; each stand glows in its egg's own colour. The **Thorn Crown**, seven great bronze branches (one snapped) rooted on the court's rim behind them, hooks up and inward over them.
- **Gate of Descent** on the south-west rim, where the bridge lands: two carved pillars, one snapped, the lintel fallen onto the stump. A ruined avenue lined with snapped columns and fallen drums leads from it to the court.
- **Fallen colossus** (west of the court): a giant carved stone head sunk into the ground, its face turned toward the path to it, void light in its eyes and through a crack across its face.
- **The Rift** (behind the eggs): it pinches and gapes along a chord across the far side, open sky through it; it never comes within 82 studs of the court's centre. An **ancient broken bridge** crosses it where it narrows (pinched for it), its middle fallen away but for one hanging block: a run and a jump.
- **Origin Altar** (on the shelf): a ring of nine leaning obsidian slabs carved with glowing seal-script glyphs (one snapped, its top fallen outside the ring) around a stepped dais with a glowing spiral sigil; a gap in the ring faces the path from the bridge. The **Origin Altar** relic floats above it.
- **Void Shard:** a great obsidian-glass crystal with a glowing core, chained to a floating temple floor about 150 studs above the altar. Floating temple fragments climb to it, each rising 49 studs, so Void Walker clears every stage and Divine Initiate falls short. The **Void Shard** relic floats on the top floor.
- **Underside:** separate angular chunks (broader and deeper at the new size) with gaps between them, void light glowing through from a great lobe under the court and a smaller one under the shelf. Iron chains bind the halves beneath the rift, a glowing veil hangs deep in it, and broken-off debris drifts below.
- **Dressing:** void crystals of dark glass around glowing cores (many along the rift's lips, with rising motes), slate rocks, about three times the old count, all round the court.
- **Tested in Play:** from the bridge to the egg plinths in 5 s, the prompt in reach; across the broken bridge with a jump; from the shelf to the altar, its prompt in reach (after the ring was turned to open toward the path); a fall into the rift returns the player to the checkpoint.

### How islands are built

- **Blender scripts:** `tools/blender/world/` holds the layout and route checks (`layout.py`) and per-island scripts. Each script authors the terrain heightfield, the meshes, the texture atlas and the placements.
- **Exports:** the scripts write FBX files to `assets/world/<Island>/` and data modules to `src/worldbuild/`.
- **Assembly:** `src/worldbuild/WorldBuilder.lua` builds each island in Studio, under `Workspace.FloatingIslands.<Island>`, and the result is saved in the place. The steps are listed at the top of that file.
- **Terrain:** each island uses its own terrain materials, because terrain colours are global to the place:
  - Yggdrasil: Grass, Ground, Rock and Cobblestone (the Starting Island's).
  - Jade Grove: LeafyGrass, Mud and Sandstone.
  - Ember Peak: Basalt, CrackedLava, Asphalt (ash) and Sand (paths).
  - Moonlit Isle: Limestone, Snow (frost), Salt (paths) and Pavement.
  - Origin Abyss: Slate, Concrete (paths) and Glacier (void-crystal crust). Brick is not used: Studio snaps Brick terrain to the 4-stud voxel grid, so paving is built from meshes.
- **Meshes:** each island has one texture atlas and reusable kits, and every piece gets its own collision setting.

---

## 7. Guardians and egg theft (all five guardians are built)

### The user's decisions (November 1, 2026)

- "Qi palm strike if there's no sword yet, specially from beginner area, and make a Huge monster, for each Island, include the Health UI, Weaken state and engage", with the combat system built first, before the bosses.
- **Caught means knockback, never death.** A hit knocks the thief back and makes them drop the egg.
- **Egg inventory:** a secured egg goes to the player's egg inventory.

### The eggs are carried home (the owner's decision, November 2, 2026)

"Remove all the eggs that boss holding or covering, the only eggs exist should only those behind the 3 eggs for each map, player should be able to carry the eggs behind the boss ... so the player can hatch their egg once they came back to the main hub."

- **No guardian holds an egg.** Each guards its island's three egg stands, behind it (`server/Guardians/EggStands.lua`).
- **Below 10% health** (`WeakenedAt` 0.1) a guardian falters and one of its stands' eggs can be taken (F, half a second), if the thief's rank can hatch it; otherwise "needs <rank>". One theft at a time. Taking it empties the stand and enrages the guardian.
- **Home is Yggdrasil:** the egg is secured the moment the thief sets foot on the hub, across the island's bridge (`SafeZone = { Island = "Yggdrasil" }`; the waypoint is the bridge's hub end). The guardian can't follow off its island. The Stone Lion's eggs are already on Yggdrasil (the Egg Garden's stands): its thief carries the egg to the Hatching Altar. (A separate island for the beginner eggs is planned.)
- **The stands:** a dropped egg that times out goes back to its stand. A secured egg leaves the stand empty for 3 minutes (`EggTheft.RespawnTime`). Then the island's lowest-rank egg appears there unless another stand already shows it, so an island is never left with only eggs a new player can't take; otherwise a random one of its three eggs appears, so two stands may show the same egg. Each stand shows its egg's glow ring, light and aura (the auras are kept as templates; an aura names its stand by the attribute `Stand`).
- **Hatching** happens only at the **Hatching Altar** on Yggdrasil (`ygg_altar.py`, `WorldBuilder.buildAltar`, `GameConfig.HatchingAltar`, on the north-east lawn between the bridges and the Egg Garden): its prompt opens the hatching window (`HatcheryController`), which lists the eggs carried home with their counts; each Hatch lays the egg in the altar's cradle, where it rises, glows and breaks open in gold light (`HatchCeremony`) as the pet is named. The window sits at the screen's right edge so the cradle stays in sight. The cradle's pool is a deep amber (Neon 255, 110, 0, a little clear): a paler gold blooms to a flat lemon disc. The stands no longer hatch. Each egg rests `HatchingAltar.Stage` (2.6 s) in the cradle and the Hatch button waits as long between presses (the server takes one egg at a time per player). The egg breaks at a server time sent with the result (`BreakAt`), so a late remote still breaks it before the server takes it away; the staged egg streams to everyone (Persistent).
- **The altar:** five roots of the World Tree break out round a two-tier dais of pale stone and arch over it, curling in like a cupped hand; under them a jade lotus on a bronze stem opens round a pool of golden Qi, the cradle; between the roots five jade seal stones, one per island, each with a gem in that island's glow.
- The guardians are full Blender models.

### Securing an egg pays Qi (the owner's decision, November 4, 2026)

Securing a stolen egg pays a burst of Qi worth `EggTheft.SecureQiMinutes` (5) minutes of cultivating, with the player's pets counted and the Qi Spring not (`server/Cultivation/QiReward`). The chase becomes the fastest way to grow, and cultivating stays the steady base. The realm multiplier is the lower of the player's and the egg's, so a high realm farming a beginner's guardian earns a beginner's Qi and the way forward is the next island. Tested in a real theft: Beginner Qi Egg, Eternal Origin owner with a Volt Fox: +4,500 Qi; the top egg's burst is 768,000 before pets.

### Combat (built)

The server decides every hit; the client only sends "strike" and shows it.

- **Weapon by rank:** the Qi Palm below `SwordFlight.UnlockRank`, the flying sword from it.
  - Palm: 10 damage, range 9, arc 75°, cooldown 0.45 s.
  - Sword: 16 damage, range 12, arc 80°, cooldown 0.55 s.
  - Damage grows 12% per rank (`GameConfig.Combat.RankPowerStep`).
- **Targets:** any Model tagged `CombatTarget` with a PrimaryPart and a `HitRadius` attribute. The nearest one in range and in the arc in front is hit; an `Invulnerable` attribute skips it.
- **Validation:** cooldown (with 15% slack for latency), alive, not cultivating.
- **Output:** `ServerStorage.CombatHit` (a BindableEvent: player, target, damage, position) for the guardian code, and `CombatEvent` to every client for the effects.
- **Effects** (`CombatFx`): the Qi Palm throws a great palm print of Qi (`QiPalm` texture) in the realm's colour.
- **Weapons are held in the hand** (the owner, November 4, 2026): welded to the right hand's grip, out for 5 seconds after the last strike, and put away on death or on starting to cultivate. A held weapon has a stance (`SwordReady`; for a spear a low stance, then its guard).
- **Sword, a combo of three** (the owner: "focus solely on slashes animation", then after a phone test "way too stiff"): a diagonal cut down across the body, a backhand rising the other way, an overhead finisher that shakes the striker's camera. Strikes within 1.1 seconds continue it (`WeaponKinds.Sword.ComboWindow`). Each swing is a timeline of whole-body keys (`SLASH_KEYS`): coiled, mid-swing, the blow, a follow-through past it, and a settle toward the ready stance. The body leads and the arm whips after it, each joint a beat behind the last (`SLASH_LAG`). Standing still, the hips turn and lunge over planted feet; moving or in the air, only the upper body swings. Its crescent (`QiSlash`) lies on the arc the blade's tip really draws, measured from the swing, so re-measure `SLASHES` if the keys change.
- **Spear, thrust then slash** (the owner: "the spear should have slash and thrust"): held in both hands in the owner's stances, wide and low and side-on. The first strike is a long straight thrust with a lance of streaks; a strike within 1.7 seconds is a sweeping slash, the whole body turning with the arms locked so both hands stay on the shaft. The thrust reaches 18 studs in a narrow 35-degree arc; the slash reaches 13 studs in a wide 85-degree one (`WeaponKinds.Spear.Slash`). The server keeps the count, so a client can't choose the wider reach. Tested through the real remote: a target 60 degrees to the side is hit only by the slash, one 15 studs ahead only by the thrust.
- **Carrying an egg takes both arms** (the owner, November 4, 2026: eggs used to ride on the head): it's welded before the chest with the arms round it (`CARRY_EGG`), the weapon is put away, and the carrier can't strike or cultivate.
- **Strikes from sword flight swing but don't land** (November 4, 2026): guardians can't reach a flyer, so a flyer can't reach them. A note says so once a session.
- Input: left mouse, R2 or the touch "Strike" button.

### Encounter

The server owns every state change. Thresholds and durations are tuned in playtests.

| State | Trigger | What happens |
|---|---|---|
| 1. Guardian | 100–10% HP | Protects its stands, attacks players in its area, uses its normal abilities. No egg can be taken. |
| 2. Weakened | Below 10% HP | Attacks slow down; posture, aura and effects show it is vulnerable. One egg can be taken from its stands. |
| 3. Enraged pursuit | Egg taken | Recognises the theft and chases the thief with faster movement, leaps and area attacks, as far as its island's edge. The pursuit creates urgency without making escape feel random or impossible. |
| 4. Escape | Thief reaches Yggdrasil (the Lion's: the Hatching Altar) | The server secures the egg in the player's inventory; its stand respawns 3 minutes later. |

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

The stand: holds an egg → empty while it is carried or dropped → the same egg back (a failed theft), or empty for 3 minutes and then a random egg of the island's (a secured one).

### How guardians move (the owner: "too stiff", twice, November 2, 2026)

All guardian animation is procedural, on the client (`GuardianAnim`, one rig per guardian in `GuardianRigs/`). Each frame a rig builds a target pose from layers (state pose, gait, lean, breathing and look, one-shot moves); every joint follows it through a spring; then the feet are planted.

- **Moves are keyed** (`GuardianAnim.keyed`): told as key poses with eases, the way an animator blocks them, never one slow blend over the wind-up. Every attack has a **coil** (the opposite way: head low, haunches dropping), a **load** (rising, a shiver building), a **snap** that lands exactly when the server's hit or wave fires (eased "in", fastest at the strike), a **held impact**, and a loose **recovery**. The shockwaves: the Lion sits back on its haunches and throws its head up to roar; Tiangou sits back and howls at the sky; the Xuanwu rears, forelegs off the ground, and stamps; Pangu thrusts his palm straight up (nova) or brings the axe down from overhead (sky-splitter); the Mantis rises with its blades crossed high and flings them down and out.
- **Planted feet** (`Rig.Legs`): after the springs, each standing leg's two joints are solved so its sole stays on the ground, so a body crouches, rears, bobs and shifts its weight over its feet instead of carrying them. A leg lifts out of it as its step swings it (`anim:lift`), in the air, or for a raised paw; no foot is ever posed through the ground. Measured fold directions: the Lion's four legs and Tiangou's forelegs fold on a positive lower turn, Tiangou's hind legs and Pangu's shins on a negative one; the Mantis's and Xuanwu's sprawling legs bend on roll (left positive, right negative). Awake guardians stand on slightly flexed legs, which planted feet need as slack.
- **Gaits measured in Play** (stance feet within about 0.1 stud of the ground, swing feet clear): the Lion 20 degree swing, 45 degree fold, body about 1.8 studs low; Tiangou 22, 50, 1.4; Pangu 22 degree stride, 55 degree knee, 1.4; the Xuanwu lifts each foot 26/18 degrees with the shell 0.6 low. Turning on the spot steps the feet too.
- **Weight and follow-through** (`Rig.Springs`): a joint eases into a move, overshoots a little and settles (bodies about 3-4.5 Hz, limbs 9 Hz). A loose joint (`Drag`) keeps its angle in the world while what it hangs from turns, then swings after it: tails (Tiangou's tip a beat behind its root), the Xuanwu's serpent, the Mantis's robe, Pangu's open arm, every head.
- **Lean** (`Rig.Lean`): nose down speeding up, back braking, banked into turns.
- **Tremors** (a shudder, a quivering roar, a building shiver) go on after the springs, which would smooth them away.
- **Cost:** 0.03-0.06 ms per guardian per frame in Studio, feet included; only guardians near the camera animate.

Tuning lives in each rig: `Rig.Springs`, `Rig.Lean`, `Rig.Legs`, the gait numbers and each move's keys. Joints are listed parent first (`GuardianAnim` warns otherwise). Strikes keep their impact on the wind-up time the server sends, so effects and knockback stay in sync.

### Guardians by island

| Island | Guardian | Encounter direction |
|---|---|---|
| Yggdrasil | The Awakened Stone Lion | Introductory fight, basic Qinggong escape |
| Jade Grove | The Bamboo Mantis Sage | Escape routes through trees and elevated terrain |
| Ember Peak | The Ember Xuanwu | Escape routes around lava and volcanic hazards; jump its quake rings |
| Moonlit Isle | Tiangou the Moon-Eater | More demanding aerial movement: its leaps are long and high |
| Origin Abyss | Pangu the World-Splitter | The most demanding encounter: a fissure to dodge, a nova to jump, a titan's leap |


### The Awakened Stone Lion (Yggdrasil)

A granite temple guardian lion come to life: a mane of carved spiral curls, spiral brows and whisker curls, glowing Qi-blue eyes, a gold collar with a jade orb and gold tassels, moss in the crevices, and a tail of five stone flame tongues ending in curls. It stands about 30 studs tall, in its lair on Yggdrasil's east side, north-west of the Egg Garden, facing the World Tree (`GameConfig.Guardians.StoneLion`).

**Its eyes and orb tell its state.** The eyes (rebuilt November 2, 2026 with `guardian_kit.eye`) are a temple lion's: bulging almond irises with dark cat pupils under carved stone lids set in a frown. Asleep, carved stone eyes (the pupil cut a shade darker) and a dull jade orb; awake, Neon Qi blue (`006eff`) and jade (`00a05f`), blinking every few seconds; weakened, flickering and wide; enraged, red-orange and wider still. Darker Neon renders as a flat black disc (the pupils use that), so the sleeping look is stone and glass, not dim Neon.

**The encounter** (`src/server/Guardians/Guardian.lua`; the server decides everything):

| State | What it does |
|---|---|
| Dormant | A statue. A player within 24 studs, or a strike, wakes it. (Until November 2, 2026 it pinned its egg under its right paw.) |
| Guardian | Stays at its lair. **Slam:** the left paw comes down in front (range 24, 55° arc, 0.75 s wind-up). **Roar:** a shockwave rolls out along the ground to 44 studs at 34 studs/s; whoever is on the ground when it passes is knocked back, and a jump clears it. |
| Weakened | Below 10% of 1,200 health (a beginner's Qi Palm gets there alone in about 108 strikes) it rears and draws a paw up; its attacks come 1.7 times slower; health never falls below 1. An egg can be taken from the Egg Garden's stands. |
| Enraged | The egg is taken: it chases the thief at 21 studs/s (a beginner runs 22) and pounces from 16 to 46 studs, aiming 0.85 of the thief's motion ahead, so a straight runner is caught and a thief who turns or dashes while it is in the air is not. It takes no damage. |
| Returning / Resting | It walks home. After a secured egg it sleeps for 30 s, then guards again. |

With nobody within 60 studs for 12 s, it heals and sleeps.

- **Never killed, never kills:** every blow is a knockback (about 19 studs, then off your feet for 1.1 s), and a knocked-back thief drops the egg.
- **The egg a thief takes** is the one on the stand they take it from (their rank must open it), held over the thief's head.
- **Carried on foot:** no sword flight while carrying.
- **Grace:** for 1.5 s after taking or recovering the egg the thief can't be knocked back, so a blow already on its way doesn't take the egg straight back.
- **Dropped:** at a clear spot on the ground near where the thief was (never inside the lion), under a pillar of Qi light; only the thief sees its prompt and the 30-second countdown. A thief who leaves the game, or lets the countdown run out, sends the egg back to its stand. Falling off the island drops it where the thief last stood.
- **The Hatching Altar is its sanctuary:** the egg is secured within 12 studs of the altar's centre, the lion never comes within 12 studs of its edge, and nobody inside it can be knocked back.
- **The client** (`GuardianController`, `GuardianAnim`, `GuardianFx`): the health bar (name, state, the 10% weakened mark, a trailing loss), procedural animation (state poses, a walk turning into a gallop, breathing, the head turned toward its target, and the moves, all through springs: see How guardians move), stone-dust effects (the roar's rolling dust wall, slam and landing bursts, dust stirring where a pounce will land), camera shake, the way to the Hatching Altar for a thief, and the knockback on your own character.

**Asset:** `tools/blender/guardians/stone_lion.py` builds it; `assets/guardians/StoneLion.fbx` holds 12 jointed segments (Body, Head, Jaw, Tail and two pieces per leg). The curls are pieces of their own, so the bake's decimation leaves them whole. `WorldBuild.GuardianBuilder.store` fits the import and joins the segments with Motor6Ds at their pivots (`Placements/StoneLion.lua`), into `ServerStorage.Guardians.StoneLion`. Animation sets the joints' `Transform` on the client.

### The Bamboo Mantis Sage (Jade Grove)

A hermit sage who became the grove: a towering praying mantis of living jade bamboo, every segment a culm with pale waxy node rings, a robe of great dark leaves folded over its back, a carved jade face with faceted compound eyes and amber pupils, long drooping leaf brows and a leaf beard, a jade mala with a gold-tasselled guru bead, and jade scythes edged with glowing Qi, folded in prayer round the egg. About 36 studs tall, its legs 28 studs wide (`tools/blender/guardians/mantis_sage.py`, 16 jointed segments).

Its lair is the middle of the Mantis Arena, its three egg stands behind it (moved there when the island was doubled); a thief carries its egg home to Yggdrasil (until November 2, 2026 the Bloom Glade was its safe zone). 2,000 health: a Qi Gatherer's palm weakens it (below 10%) alone in about 165 strikes.

| State | What it does |
|---|---|
| Dormant | Meditating: head bowed, eyes dark, its blades folded in prayer. |
| Guardian | Sways like a leaf in the wind and turns to face whoever it watches, the egg turning with its arms. **Scythe:** both blades cut across the front (range 26, 65° arc). **Blade wave:** a cone of Qi blades and leaves skims out along the ground (46 studs, 50° either side); jump it. |
| Weakened | Crouches and lowers its blades. |
| Enraged | The mantis threat display (the robe flared like wings, blades raised and open, eyes red), chasing at 23 studs/s. **Leap:** long and high (up to 72 studs), its first move after the theft. |

### The Ember Xuanwu (Ember Peak)

The Black Tortoise of the north gone to the volcano (chosen by the owner, November 2, 2026): a colossal tortoise whose shell has become a small volcano, a dome of black basalt columns stepped up into a cone whose crater cradles the egg, the magma inside the shell glowing in every seam between the columns. Coiled round the shell is its companion, a molten serpent of cooled black crust broken into bands, lava glowing between them, its dragon head rising over the volcano's flank. The tortoise has a snapping turtle's wedge of a face, a hooked horn beak and a crown of small basalt columns. About 24 studs to the crater's rim, 31 to the serpent's crown, 48 from beak to tail (`tools/blender/guardians/ember_xuanwu.py`, 15 jointed segments; the basalt Shell is its own piece on the Body).

**Its eyes** (`guardian_kit.eye`): almond irises with dark slit pupils and carved lids. The tortoise's are heavy-lidded under a brow shelf, slanting down toward the beak; it blinks slowly every few seconds, glares (narrowed, red) enraged, widens and flickers weakened, and shuts them asleep. The serpent's are narrow and cold under a bony ridge; it never blinks, dulls asleep and narrows to a slit as it strikes.

Its lair is the middle of the Cinder Arena (set 3.5 studs toward the gate so its beak clears the egg pedestals when it turns), facing the Ember Gate; a thief carries its egg home to Yggdrasil (until November 2, 2026 its safe zone was the Ember Forge). 3,200 health: a Qi Awakener's starter sword weakens it (below 10%) alone in about 120 strikes. Securing its egg pays 1,500 Spirit Stones; its relic unlocks Fire.

| State | What it does |
|---|---|
| Dormant | A sleeping volcano: sunk on its plastron, head drawn in, eyes shut, the serpent drowsing low, the magma dim. |
| Guardian | Turns, slowly, to face whoever it watches, the serpent swaying over the volcano. **Serpent lash:** the serpent rears back and strikes the ground before it (range 30, 70° arc). **Quake:** it rears onto its hind legs and stamps; a ring of ash and fire rolls out all round (50 studs) and the volcano erupts; jump it. |
| Weakened | Sinks low, head down, the serpent's head hung low. |
| Enraged | Front reared, beak open, the serpent rearing high, eyes red, magma hot. Slow (20 studs/s; it stops 22 short of its thief, `ChaseStop`). **Charge:** a low, heavy lunge (16 to 56 studs) that lands with a shockwave. |

Measured in Play (November 2, 2026): wake, lash, quake, weaken (egg set down at `Egg.Offered`), steal, charge (landing knocked the thief, who dropped the egg), drop timing out and the egg returning, and a secured Phoenix Ash Egg (+1,500 stones) all work. The serpent's head maps rendered grey for a while after upload; they are re-uploads.

### Tiangou the Moon-Eater (Moonlit Isle)

The heavenly hound of the eclipse myth, the dog that swallows the moon (chosen by the owner, November 2, 2026, over a three-legged moon toad and a moon-backed spider). A lean, long-legged sighthound whose coat is the midnight sky (deep blue, faint constellations in it, silvered where moonlight falls), with a ruff, a plume of a tail and feathered legs of white fire, tall pointed ears with a flicker of fire inside, fangs and a black nose. Above its shoulders stands the eclipse it made: the swallowed moon as a black disc (dark Neon) ringed by a corona of white fire with a few long streamers, framing its head from the front, held up by streams of fire from its shoulders. The egg sits in the moon's last silver crescent, before the disc. About 14 studs at the shoulder, 33 to the top of the eclipse, 44 from nose to tail (`tools/blender/guardians/tiangou.py`, 14 jointed segments).

**Its eyes** (`guardian_kit.eye`): gold almonds with round black pupils under a low, scowling brow. It blinks every few seconds, shuts them asleep, glares (narrowed, red) enraged, and widens and flickers weakened. Its corona burns low asleep (Neon fades with transparency), gutters weakened, flickers enraged and flares as it howls.

Its lair is the middle of the Lunar Court, facing the Crescent Arch; a thief carries its egg home to Yggdrasil (until November 2, 2026 its safe zone was the Celestial Pavilion). 11,000 health: a Soul Awakening's Spirit Soul sword weakens it (below 10%) alone in about 118 strikes. Securing its egg pays 4,000 Spirit Stones; its relic unlocks Frost. Messages call it "Tiangou" (`Called`).

| State | What it does |
|---|---|
| Dormant | Asleep on its feet: head low, eyes shut, tail down, the corona burning low. |
| Guardian | Alert, turning quickly to face whoever it watches, tail waving. **Bite:** it draws back and snaps (range 25, 60° arc). **Eclipse howl:** head thrown back to the sky, the eclipse flares and a ring of frost rolls out all round (52 studs); jump it. |
| Weakened | Crouched low, panting. |
| Enraged | The hunting crouch, lips drawn back, tail up, eyes red, chasing at 27 studs/s (it stops 17 short, `ChaseStop`). **Moon leap:** long, high arcs (18 to 85 studs, 26 high), stretched flat in the air. |

Measured in Play (November 2, 2026): wake (it howls at once), bite, howl, weaken, steal (a Heavenly Throne Egg), the howl's ring knocking a grounded thief who drops the egg, recover, moon leaps aimed ahead of the runner and landing at the sanctuary's edge, and a secured egg (+4,000 stones). Most of its maps rendered grey after the first upload; they are re-uploads.

### Pangu the World-Splitter (Origin Abyss)

In the myth Pangu hatched from the cosmic egg and split the chaos inside it into heaven and earth with his axe (chosen by the owner, November 2, 2026, over Hundun and the Taotie). A titan of dark stone still cracked with the chaos he came from: violet void light in every fissure and a crack of it splitting his brow, a mane and a mantle of void drifting from him like smoke, great curved horns bound in bronze, a carved stone beard and moustache, a bronze belt with the disc of yin and yang (the split he made) over torn hangings. The world-splitting axe, a crescent of black stone with a void-lit edge, rests on his right shoulder; on his open left palm, before his chest, the cosmic egg he was born from. The island's rift is his axe stroke. About 38 studs to his crown, 46 to his horns (`tools/blender/guardians/pangu.py`, 11 jointed segments: the first guardian on two legs).

**His eyes** (`guardian_kit.eye`): deep-set violet almonds with dark pupils, the lids bearing down toward his nose (an eye's `forward` is the nose side: pointed outward, the same lids read sad). He blinks slowly, shuts them asleep, glares (narrowed, red) enraged, widens and flickers weakened. The void in his cracks burns low asleep, pulses with his breath, gutters weakened and flares as he strikes.

His lair is the middle of the Void Court, facing the Gate of Descent; a thief carries his egg home to Yggdrasil, back past him and across the bridge (until November 2, 2026 the Gate of Descent terrace). 24,000 health: a Divine Initiate's Divine sword weakens him (below 10%) alone in about 120 strikes. Securing his egg pays 12,000 Spirit Stones; his relic unlocks Void. Messages call him "Pangu".

| State | What he does |
|---|---|
| Dormant | A statue: head bowed, eyes shut, the void burning low. |
| Guardian | Turns to face whoever he watches. **Axe cleave:** the axe comes off his shoulder and over, into the ground before him (range 30, 75° arc). **Sky-splitter:** both arms raise the axe and slam it down; a fissure races 70 studs straight ahead in a narrow line (15°): jump it or step aside. **Chaos nova:** he raises the cosmic egg and the chaos bursts out all round (44 studs); jump it. |
| Weakened | Down on one knee. |
| Enraged | Squared up, the axe lifted, eyes red, chasing at 28 studs/s. **Titan leap:** 20 to 75 studs, 22 high, landing with a shockwave. |

Measured in Play (November 2, 2026): wake, cleave, sky-splitter and nova (each knocking), the axe head's path through both strikes (down to about 9 studs before him as the hit lands; first versions swung it behind his neck and landed late), the kneel (planted foot at 0.0 after the hips were dropped 8.4), steal (a Primordial Abyss Egg), the titan leap catching a thief 51 studs off (the egg dropped), and a secured egg (+12,000 stones). All 41 maps rendered on the first upload (batches of 10).

**One framework for every guardian.** Attacks are named per guardian and have a kind: a *Sweep* in front, a *Wave* along the ground (all round or in an arc, cleared by a jump), a *Pounce* onto the thief. `TurnsToFace` turns it at its lair toward whoever it watches. (No guardian holds an egg since November 2, 2026: the crater, crescent and palm built to cradle one stand empty.) Each guardian's look lives in its client rig, `GuardianRigs/<Id>` (poses, gait, moves, glow, effects).

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
7. Multiplayer ownership, exploit resistance, disconnects and edge cases. Audited November 3, 2026 (see "Data and security"). Passed in Play, one player:
   - a second stand refused while an egg is carried ("busy"), one egg in the world;
   - a recovered egg dropped on death and back on its stand after 30 s, with no egg gained;
   - the thief leaving mid-carry: the save kept its eggs and stones and released its lock.

   Passed with two players (Studio local server, November 3, 2026):
   - another player at a dropped egg: no prompt for them, and forcing the hold is refused; the thief still recovers it;
   - two players taking the same stand in the same instant: exactly one egg made, the other refused;
   - the thief leaving with the egg dropped: it is back on its stand at once, the guardian returning.

   Still to run, on live servers: a save taken over by another server.
8. The framework rolled out to every island.
9. Polish: guardian animation, auras, trails, sound, UI and cinematic feedback.

### First playable checklist

- [x] Cultivate Qi.
- [x] Use basic Qinggong movement.
- [x] Find and engage one guardian.
- [x] Damage it until it is weakened.
- [x] Steal its egg.
- [x] Trigger the enraged pursuit.
- [x] Escape and secure the egg.
- [x] Fail an escape and drop the egg.
- [x] Find and recover the dropped egg.
- [x] Try another escape with it.
- [x] Secure the egg without duplicate copies (audited November 3, 2026: no way to copy an egg or a pet; the steal, drop and return played through in Play; the two-player and two-server cases are still to run, step 7).
- [x] Hatch it with the existing pet system.

---

## 7b. Weapons and Spirit Stones (phase 1 built November 2, 2026)

### The owner's decisions
- The Blacksmith sells a **sword and a spear for each realm**; a player buys those of their realm or below.
- **Buy & Sell** buys players' pets and weapons.
- The currency is **Spirit Stones** (Qi is never spent: ranks are reached by total Qi).
- **Sword vs spear:** the sword strikes fast and wide, the spear slower, farther and harder, for the same damage over time.
- The Blacksmith will also **forge custom weapons**: a relic found on the maps or dropped by a guardian sets a forged weapon's element (its glow, trail and strike effect), and the player names it.
- **Exclusive weapons** are a separate line, designed later.

### Built (phase 1: the systems)
- `GameConfig.WeaponKinds` (Sword: 12 reach, 80° arc, 0.55 s; Spear: 18 reach, 35°, 0.85 s, ×1.55 damage), `WeaponTiers` (one per realm, named, Damage 16 to 69, Price 60 to 2.2M stones), `SpiritStones` (pet values, refunds, relic share). `shared/Shop.lua` turns them into the catalogue (`Sword<tier>`, `Spear<tier>`) and prices pets by rarity and their egg's realm.
- `server/Shop`: `Wallet` (Spirit Stones), `WeaponInventory` (owned weapons, the one wielded; a player with none gets the Reedwhisper Sword), `ShopService` (the shops' prompts, buy / wield / sell, checked on the server: reach of the shop's plot, realm, price, throttled). Saved in `PlayerData` (schema 7).
- **Combat** strikes with the wielded weapon (`Combat.strikeOf`), or the Qi Palm with none. The spear's thrust is a spear of Qi light in the realm's colour until the spears are modelled.
- **Earning stones:** selling pets (Common 6 to Secret 600, ×2.6 per realm of the pet's egg) and weapons (40% back), securing a guardian's egg and a relic's first attunement.
- **The rewards' ladder (rebalanced November 4, 2026, the owner's request; `shared/Shop.lua`):** a rank's value is the price of a weapon of its realm, rising smoothly between realms. Securing an egg pays 25% of its required rank's value (at least 40), so 40 for the first eggs up to 210,000 for the Primordial Abyss Egg; it was a flat amount per guardian, which made early weapons nearly free (a Xuanwu egg paid for 25 of them) and late ones a grind (10 thefts at Heavenly Dao). A relic pays 50% (at least 40). With pet sales, a weapon of the player's realm now takes about 2 to 6 thefts at every stage. To be checked against real playtests. Moonlit's relics rose to 20,000 Qi and need Soul Awakening, like their island.
- **Interface** (`client/Shop/ShopController`): a Stones counter by the Relics counter; the Blacksmith and Buy & Sell windows, opened at the Blacksmith's anvil and the foot of the Jade Scale (selling asks "Sure?" first; at first from the plots' notice boards). Tested in Play: buy, wield, sell, the refusals (far away, too dear, the wielded weapon), the spear strike, and saving across a restart.

### Still to build
- **Phase 2, the art:** the Blacksmith and Buy & Sell buildings (built, see Yggdrasil above), then the 24 weapons (a sword and a spear per realm, each with its own look). The first two realms' four are modelled for the owner's style review (`tools/blender/weapons/tier01.py`, `tier02.py`, shared `weapon_kit.py`; baked like the flying sword; `assets/weapons/<WeaponId>.fbx`):
  - **Reedwhisper Sword** (Qi Awakening): a sword grown from a river reed: a reed-leaf blade of celadon steel, swaying and twisting, its veins running down it and a thread of Qi on its midrib; the reed's sheaths peel away at its foot; its grip a reed flute whose finger holes and open end glow; the reed's seed plume hanging from it.
  - **Bamboo Thorn Spear** (Qi Awakening): a green bamboo culm cut on the bias into its point, Qi glowing in the hollow the cut lays open; papery shoot sheaths peeling back at the head and two hooked bamboo thorns flaring as its lugs; cord-bound, three bamboo leaves at the butt.
  - **Jadevein Sword** (Qi Foundation): a blade split from slate along a jade vein: a rough chipped stone back, a celadon jade cutting edge alight with Qi, veins of light branching across the stone, a clipped point; a dressed cornerstone guard banded in bronze with jade cabochons, a blue-corded grip, a cornerstone pommel.
  - **Jade Crane Spear** (Qi Foundation): its head a crane striking: a bronze beak for the point, a white jade head under a red crown with glowing eyes, a black jade neck curving into the socket, and the wings half spread as the lugs, black primaries, lit quills; dark teal lacquer shaft, a bronze crane's-foot butt.
  - The owner liked the concept (November 2, 2026); the other ten realms followed (`tier03.py` to `tier12.py`), each pair from its realm's aura theme:
    - **Spirit Core** (jade): **Coreflame Sword**, a dark steel blade forged round a spirit core, an armillary of bronze rings and a ring of light orbiting the glowing core as its guard, jade flame running up the blade; **Ember Fang Spear**, a fire beast's ivory fang with embers in its cracks and a smaller fang either side, bronze claws cradling a burning core.
    - **Spirit Soul** (jade): **Soulmirror Sword**, black mirror steel with runes of light and the soul's rippling echo of each edge, a round bronze mirror for a guard; **Moonpiercer Spear**, a needle of moon silver through a rune-cut crescent moon.
    - **Ascendant** (gold): **Skyrise Sword**, a diving swallow, its body the guard, its swept golden wings the quillons, its forked tail the pommel; **Cloudspine Spear**, a leaf blade out of a collar of golden ruyi cloud scrolls, cloud curls running down the sky-blue shaft.
    - **Immortal** (gold): **Lotusfall Sword**, a pearl petal blade growing from an opening lotus with a rayed halo behind it; **Crane Feather Spear**, a single great immortal's feather, its quill lit, a halo and two wings of light at the socket.
    - **Divine** (violet): **Thunderjudge Sword**, a zigzag bolt of lightning caught in a bronze judge's seal, a sigil ring floating before it, a thunder drum pommel; **Thunderhowl Spear**, a forked bolt bursting from the jaws of a horned, maned bronze thunder-beast.
    - **Cosmic** (violet): **Starriver Sword**, night-sky glass with a river of starlight and a spiral galaxy guard; **Comet Tail Spear**, an icy crystal nucleus with lit facet edges, violet glass tail fins streaming back.
    - **Void** (violet): **Voidsilence Sword**, black void glass cut into floating, turned segments, light leaking through the gaps, shards orbiting the guard; **Abyss Fang Spear**, a curved serrated black blade coming through a portal of rings and a spiralling vortex.
    - **Heavenly Dao** (violet): **Dao Heart Sword**, a blade split into white and black jade, a taiji disc guard with the eight trigrams floating round it in light; **Heaven Pillar Spear**, a white marble pillar coiled in gold, a cloud board crossing it, a four-sided jade spike inscribed with glyphs inside a radiant ring.
    - **Primordial** (violet): **Chaos Origin Sword**, a great rough-hewn obsidian blade with violet veins and glyphs, an ammonite coiled round its foot; **Primeval Dragon Spear**, a horned dragon skull whose long spiralled horn is the point, its spine down the ancient wooden shaft.
    - **Eternal Transcendence** (gold, violet and azure): **Eternity Sword**, a radiant blade with threads of three lights, an infinity-sign guard, three coloured rings orbiting it with beads of light; **Eternal Sun Spear**, a white gold flame rising from a sun of curling flames, an azure rim and a violet orbit.
  - All 24 imported and stored (November 2, 2026); every strike tested in Play with its own model.
  - **In game:** each realm weapon is stored as `ServerStorage.Weapons.<WeaponId>` (`OutfitBuilder.storeWeapon`; Kind, Hilt and Tip attributes) and copied to the clients by `CombatService`. A strike puts the striker's own weapon in their hand (the flying sword when theirs isn't modelled yet; section 7, Combat).
- **Exclusive weapons:** later (the owner's call).

### Built (phase 3: the relic forge, November 2, 2026)
- **The owner's decisions:** one element per island; a forged weapon strikes 10% harder; a relic unlocks its element for good and each forge costs Spirit Stones.
- **Elements** (`GameConfig.Forge`): Wood (the Root of the Island and Jade Grove's relics), Fire (Ember Peak's), Frost (Moonlit Isle's), Void (Origin Abyss's), Earth (the Stone Lion's relic, dropped when its egg is secured) and Wind (the Mantis Sage's). Attuning a relic or securing an egg says when it unlocks an element.
- **Forging** (the Blacksmith's Forge tab): choose an unlocked element, name the weapon (3 to 20 letters, through Roblox's text filter) and forge any owned weapon for half its price (at least 30 stones); re-forging changes both. A forged weapon deals +10% damage, sells back 40% of its price and its forging, and keeps its element and name in the save (`PlayerData` schema 8: a weapon's Element and Name, the guardians' `ForgeElements`).
- **Its strikes** take the element's colours (glow, trail, slash) and burst with it: Fire embers and a lick of flame, Frost ice shards and mist, Wood tumbling leaves, Earth thrown rock and a dust ring, Wind whipping streaks and a gust ring, Void dark smoke and violet sparks (`CombatFx`).
- **Code:** `server/Shop/Elements` (unlocked elements), `WeaponInventory` (Element, Name, `forge`), `ShopService` ("Forge" action, throttled and guarded while the name is checked), `Combat.strikeOf` (the bonus), `Guardian:secure` and `DiscoveryService` (unlocks), `client/Shop/ShopController` (the Weapons and Forge tabs).
- **Tested in Play:** the refusals (far away, no element, a locked element with where to find it, a short name, a weapon not yours); a real forge through the window (Fire, "Emberwhisper", 30 stones); the Fire strike; every element's colours and burst on a sword and a spear; the forge kept across a restart; one strike on the Stone Lion took 142 health, the forged damage (unforged 129). Not yet seen in play: a guardian's drop unlocking Earth or Wind, and a relic's attunement message naming its element.

---

## 8. Technical architecture

**Tools:** Roblox Studio and Rojo 7.7.1 (VS Code, Git), with Blender 5.2 for pets, eggs, aura pieces and islands.

**Rojo mapping**

| Folder | Maps to |
|---|---|
| `src/shared` | ReplicatedStorage |
| `src/server` | ServerScriptService |
| `src/client` | StarterPlayerScripts |
| `src/worldbuild` | `ServerStorage.WorldBuild` (build-time, except `Placements.Bridges`, which `server/World/WorldConfig` reads at runtime for the bridge landings) |

Client and server scripts are grouped by feature in folders of the same names: `Auras` (client), `Pets`, `Guardians`, `Combat`, `Qinggong`, `Cultivation`, `World`, `Character`, `UI` and `Audio` (client), `Data` and `Outfits` (server). A script requires a module in its own folder as `script.Parent:WaitForChild("Name")`, and one in another folder as `script.Parent.Parent:WaitForChild("Folder"):WaitForChild("Name")`.

**Imported models**

| Kind | Where in Studio |
|---|---|
| Pets | `ReplicatedStorage.PetMeshes/<EggId>` |
| Aura pieces | `ReplicatedStorage.AuraMeshes` |
| Eggs | `ServerStorage.EggMeshes` |
| Island kits | `ServerStorage.WorldKit/<Island>` |
| Guardians | `ServerStorage.Guardians/<GuardianId>` (`WorldBuild.GuardianBuilder`) |
| The flying sword | `ServerStorage.Weapons.FlyingSword` (`WorldBuild.OutfitBuilder.storeSword`) |
| Outfits | `ServerStorage.Outfits/<OutfitId>` (`WorldBuild.OutfitBuilder`) |
| The islands themselves | `Workspace.FloatingIslands`, saved in the place |
| Development tools (never shipped to players) | `ServerStorage.DevStage`: the PDS kit, `AuraTestRange`, `AuraWorkbench`. Drag one to Workspace to use it, and back before publishing |

**What the server owns:** Qi rewards, rank-ups, Qinggong levels, hatching, inventory, relics, world safety (spawn, checkpoints, fall reset) and saving. It never trusts the client for Qi amounts, ranks, hatch results or inventory.

**What clients handle:** UI, auras, effects, pet companions, input and Qinggong movement.

**Shared config:** ranks, Qinggong, pets, eggs and relics.

### Sound (built November 3, 2026)

The game had no audio. Every sound comes from Roblox's licensed libraries only: Pro Sound Effects and APM Music, never user uploads.
- `client/Audio/SoundCatalog` names every sound: its ids, level, pitch, reach, start, length and layers. Levels and starts were set from each file's loudness measured in Play; the files differ up to 200 times.
- `Sfx` plays them: one-shots at a point or on a part, culled past their reach; loops faded in and out; four SoundGroups (Music, Ambience, Effects, Interface).
- `AudioController` handles:
  - each island's bed and music, from the player's `Island` attribute (WorldService);
  - the taiko battle theme near an awake guardian or while carrying an egg, with a heartbeat under it for the thief. The island's music returns 4 s after the fight and resumes where it was left;
  - the sword-flight wind for every player, the cultivation hum, and a click on every HUD button.
- Each guardian has its own voice and blows (GuardianController `VOICES`), timed to the move's wind-up so the sound lands with the hit; and a weaken cry of its own.
- The egg steals, drops, returns and secures; strikes and hits; leap, dash, glide and landing (QinggongFx); the hatch's rumble, crack and reveal (a bell for Legendary and up); the breakthrough gong; and the shop's open, coins and refusal.

### Settings and analytics (November 4, 2026)

- **Settings** (the Settings button on the rail; `client/UI/SettingsController`, `server/Data/Settings`, saved as `Settings`, save version 10): Music and Sound volume, and Reduced Effects, which hides other players' auras and turns off the owner aura's screen flash and camera shake on that player's own client.
- **Analytics** (`server/Analytics/Analytics`, for the Creator Dashboard): the quest path as an onboarding funnel; every Spirit Stone in and out, by cause and item (through `Wallet`); and the moments RankUp, EggTaken, EggDropped, EggSecured, EggHatched and QuestsSkipped, each by guardian, egg or rank. Studio only prints these: real data needs a live server.

### Rewards (November 4, 2026)

A window on the rail (`server/Rewards`, `client/Rewards/RewardController`, `shared/RewardRules`), the rules in `GameConfig.Rewards`:

- **Daily:** a seven-day streak of Spirit Stones scaled by realm, 2, 3, 4, 5, 8, 10 and 25 times 2.6^(realm - 1), with minutes of Qi on days 3, 5 and 7 (2, 3 and 5). Missing a day restarts it at day 1; the same day is refused.
- **Offline Qi:** 20% of the rate for time away, up to 8 hours, from 10 minutes.
- **Codes:** `Codes.lua`, each once per player. `QIAWAKENS` pays 100 stones.
- **Group:** 200 stones for joining. Off until the owner gives a group id (`Rewards.Group.GroupId`).

Tested in Play: codes (invalid, valid, repeated, a table sent instead of text), the streak (next day, same day, a missed day) and the offline toast. Not tested: the group reward, which needs a real group.

### Icons (November 4, 2026)

Our own line drawings, white so the interface tints them: `tools/ui/draw_icons.py` writes `assets/ui/icons/`, and the uploaded ids are in `icons.json` and `UiTheme.Icons`. The owner asked for unique ones, so none is a stock symbol: a spiral of Qi, a spirit fox, a crossed-collar robe, a diving swallow, the Jade Scale, a lotus dial, a gold ingot.

### The phone tier (November 4, 2026)

`client/Quality.lua`: `Quality.Low` is true on a touch screen with no keyboard. On a PC it's false and nothing changes. Tested in Studio with it forced on: no errors, and the owner's meditating aura came to 62 emitters at 186 particles a second. The owner's phone test found flying and meditating free of issues. Sizes on a phone come from `Hud.isCompact()`: smaller rail and dock, Strike, Dash and Sword grouped round the jump button, and the STATUS panel can be minimized to the Qi alone (saved as a setting).

- **Auras:** half the emission and half the distance. The body aura sits on 6 parts instead of 15, without its ash layer, at 40% (75 emitters become 24 per meditating player, counted from the code). Other players' auras drop their Highlight and PointLight; a player's own keeps them.
- **World** (`World/WorldQuality`): the islands' own emitters run at 40%, except eggs on stands. Ember Peak alone asks for about 1,250 particles a second at full rate.
- **Egg auras:** off past 110 studs instead of 200, far ones step every third frame, no screen pulse.
- **Guardians:** animated within 150 studs instead of 400, every other frame at rest, springs at 1/120 s. Waking each of the five showed no instability, against the same test on PC settings.
- **Others' pets:** hidden past 80 studs instead of 250. **Others' poses:** stop past 80 studs. **Robes:** sway within 40 instead of 120.
- **Everyone, PC too:** the pose loop no longer allocates a table per joint per frame, a robe still loading looks for its pieces once a second instead of every frame, and the rounded interface dropped a glow stroke and eight tick frames per panel.

Not yet measured on a real phone. The owner's account wears `OwnerAura`, the costliest, so a normal account should be tested too.

### Pets arrive whole (November 4, 2026)

A pet is many mesh pieces fetched on first use, so on a phone it came in slowly, a piece at a time. `client/Pets/PetPreload` now downloads a pet before showing it (for 8 seconds at most, so one can't go missing) and fetches a player's other pets in the background once their inventory arrives. HUD icons load at start too.

### Anti-cheat fixes (November 4, 2026)

Found by a read-only security audit and tested through the real remotes unless noted:

- **Forge names:** a raw name over 200 characters is refused before any filtering (a huge one used to hold the server for 48.5 seconds; now 0.05, and nothing charged).
- **Selling:** a player's last companion can't be sold.
- **Carrying an egg:** moving faster than a dash can carry drops it, with no reward (`CARRY_SLACK` in `Guardian`).
- **Air strikes:** swing but don't land.
- **Floods:** `PetService` takes a request per half second; Qinggong effects relay at most 8 a second (rates read in code, not flooded live).
- **Movement** (`server/Security/MovementGuard`): Roblox lets each client report its own position, so the server keeps a travel allowance per player, filled at the fastest their rank can honestly go, with room for the dashes and air leaps in hand. Falling is free, and the server's own moves and a guardian's knockback are allowed for. A player who overdraws it, or jumps too far at once, is "suspect" for 5 seconds: prompts, shops, stands and strikes refuse them and it's logged. It never kicks or drags anyone back, so a wrong guess costs seconds. Tested: a run with dashes and air leaps, and sword flight at 131 studs a second, raised nothing; a 500-stud teleport beside a guardian was refused. A jump within what the top rank can honestly cover isn't caught, by design.
- **Egg thieves** can't carry an egg farther than `MovementGuard.maxTravel` allows, stay off the ground over 12 seconds, or restart the 5-minute carry limit by dropping and retaking it.
- **Earning an egg** (the owner, November 4, 2026): to take one, a player must have dealt 10% of what weakening its guardian takes (`EggTheft.TakeShare`), counting health really removed, so hitting a guardian already at 1 earns nothing. Damage resets when it heals. Someone whose egg goes back waits 30 seconds to take another (`EggTheft.RetakeCooldown`), so nobody can hold a guardian hostage. Tested on the Stone Lion: 90 of the 108 needed was refused, 110 was allowed, and a retake right after a return was refused with 17 s left.
- **Fling:** players don't collide with each other (`server/Security/CharacterCollision`), so a spinning hacked character can't throw anyone off an island.
- **Cultivating** ends on the server if the player moves over 8 studs from where they began, or holds an egg. The on/off cooldown rose to 1 second, because each cycle makes every client rebuild an aura.
- **Hatching and forge names** are rate limited, 0.25 and 2 seconds.
- **Strike rate:** the server moves a player's next strike on from when the last was due, not from when it arrived, so coming early can't add up to about 18% more strikes.

Known and accepted: one forged "Leap" completes that quest step, worth 20 stones. Stamina is client-side, and the movement allowance assumes full stamina.

### Data and security

- Validate every important action on the server.
- Save with Roblox data stores; old saves are migrated automatically.
- Test multiplayer, rejoining and invalid requests, not just the happy path.
- **The launch-safety audit (November 3, 2026)** traced the egg, pet, Spirit Stone and weapon lifecycle through disconnects, rejoins, shutdowns, save failures and repeated requests. Every save is one `UpdateAsync` checked against the session, and there is no trading, so a failed save can only roll back, never copy. Fixed:
  - The starter weapon went to anyone owning none, so selling it and rejoining minted Spirit Stones without end. It now goes to a new player only, or once to a save from before weapons (`PlayerData` migration 6).
  - A forged name was measured in characters at the forge but in bytes on load, so an accented or CJK name lost its element. Both now count characters.
  - A save asked for while one was writing, or just after, was dropped (up to 60 s of progress at risk, a secured egg included). It is now rescheduled.
  - A player whose save another server took over kept playing unsaved. They are now kicked with "Your progress continues in another server".
  - Each guardian steps in its own `pcall`: one error can't freeze the others, or an egg they carry.
- **Release rule:** never rename or remove a pet, egg or weapon id, or lower a cap: loading a save drops what it doesn't know.
- No secrets in source control; avoid third-party asset packs.

---

### Outfits (cosmetic)

Outfits are worn over the player's own avatar (`GameConfig.Outfits`). They are cosmetic only, with no aura or stats.

- **Murim Robes** (November 1, 2026), made for the owner and worn only by them for now. An original cultivator's outfit in the spirit of the owner's reference:
  - a white inner robe with a black standing collar, and a white crossed collar (left over right) embroidered in gold;
  - a long, open gold-brocade coat that deepens to dark brown at its embroidered hem, with embroidered fronts and gold half-sleeves;
  - wide white sleeves with flared cuffs;
  - a gold belt hung with a turquoise pendant, a pearl and a yellow tassel;
  - loose dark trousers, and black boots with white soles and toe caps.
- **How it is built:** `tools/blender/outfits/murim_outfit.py` makes high-detail cloth with procedural brocade and embroidery, baked to 13 game meshes (about 40,000 triangles in all), each fitted to one R15 body part of the owner's avatar.
- **Sway:** the robe skirt, the tassel and the cuffs are skinned to small bone chains. On every client, the skirt's four panels open as each thigh swings into them, trail behind movement and lift during falls and Qinggong. The tassel and cuffs swing.
- **In game:**
  - `OutfitService` checks ownership on the server, welds the pieces on and hides accessories that clash (back, waist and clothing types).
  - It saves the choice (`OutfitId`).
  - The "Robes" button beside "Pets" toggles it.
  - The worn model lives in `Workspace.WornOutfits`, welded to the body: inside the character, the Animator resets the bones each frame and the sway never shows.
- **Selling:** undecided. Setting `GamePassId` makes it a game pass today. It is fitted to the owner's body proportions, so selling it to every avatar would need per-avatar fitting (Roblox layered clothing).

## 9. Open decisions

- **Egg stands under the guardian loop:** decided (November 2, 2026): the stands give no free eggs; a guardian's eggs are stolen from them, carried home to Yggdrasil and hatched only at the Hatching Altar (section 7, "The eggs are carried home").
- **Forged weapons:** the purchase and request flow, which weapons each Qi mastery level unlocks, and how they plug into combat.
- **PvP stealing or raids:** only ever opt-in and server-checked, with protected pets, cooldowns and clear warnings. Not planned. Guardian egg theft is PvE.
- **Monetization:** cosmetic-first, never pay-to-win; no paid eggs or random rewards until Roblox's policies are checked.
- **Selling outfits:** a game pass in this game (ready: set `GamePassId`) or the Roblox Avatar Marketplace (needs the UGC program and layered clothing fitted to any avatar).
- Per-element and per-realm aura looks.
- Blender models for the remaining procedural pets.
- Balance tuning from playtests.

**North star:** players feel like cultivators who earned their power and their movement. They train Qi to grow stronger and master Qinggong to move beyond ordinary limits. They will challenge guardians for their eggs and survive the pursuit that follows. Failure is a recoverable setback, never an unfair loss.
