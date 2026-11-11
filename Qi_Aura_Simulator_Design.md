# Qi Aura Simulator — Game Design

**Platform:** Roblox · **Project:** `qi-aura-simulator` · **Last updated:** November 5, 2026

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
- **Every pet and every guardian has expressive eyes** (the owner's one exception: the Cosmic Jellyfish has none): never a plain glowing ball. A guardian's eye is an almond iris with a slit pupil and lids that give it a look (`guardian_kit.eye`), and its rig makes it live (blinks, glares).
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

- **The way there (November 5, 2026):** a quest with a `Way` in `GameConfig.Quests` shows an arrow that turns with the camera, the place and the distance in studs. It rests within 25 studs of the place, and while a stolen egg's own way home is showing.
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

### The Heavenly Tribulation (November 9, 2026)

The owner chose it from the suggestions ("do the 3"). Breaking through **into a new realm** (11 times: Qi Foundation to Eternal Transcendence) is no longer a button alone: the heavens test the cultivator. Ranks within a realm stay instant.

- **The button** reads FACE THE TRIBULATION: <REALM>. Pressing it stops meditation and lands a sword flight; neither can start until it is over, and it can't begin while carrying a guardian's egg.
- **The storm:** dark cloud gathers 55 studs over them and follows them, lightning flickering inside it; the world dims for them (not with Reduced Effects). After 2.5 seconds, rings of light mark the ground where bolts will fall, each filling as its bolt comes, a beam of light above it; then the bolt falls, with a flash, a scorch and sparks. They dodge on foot, leaping and dashing.
- **Harder each realm** (`GameConfig.Tribulation`): 8 bolts entering Qi Foundation up to 18 entering Eternal Transcendence; the warning from 1.45 down to 0.85 seconds; the gap between bolts from 1.1 to 0.6; from the Ascendant Realm, two fall at once, from the Cosmic Realm three (the others ringing the cultivator, closing the easy ways out); and more and more aimed where they are running, not where they stand.
- **Three lives** (gold diamonds on the panel at the top, which also counts the bolts to come). A bolt reaches 6 studs round its ring's middle, at any height (a column of lightning); bolts falling together cost one life between them. Three hits and it is over: no Qi lost, and the button counts down a minute before they may try again. Survive every bolt and the breakthrough is theirs, with its usual effect. Dying counts as failing it, with the same minute's wait (the owner, 2026-11-11: otherwise a reset skipped the wait); leaving the game ends it with no wait.
- **Fair and server-checked:** the server places every ring and judges every hit from where the cultivator really is (`server/Cultivation/Tribulation`); every client draws everyone's storm within 320 studs (`client/Cultivation/TribulationController`). A hit flashes the screen white and shakes the camera (not with Reduced Effects). Analytics: TribulationStarted, TribulationPassed, TribulationFailed.
- **Sounds** (licensed Pro Sound Effects, levels still to be judged by ear): a deep pulsing rumble under the storm, thunder rolling in, a charging arc for each ring, a crack and a boom for each bolt.
- **Tested in Play** on a test save: standing still, three hits and a fall, the rank kept, the button counting down 60 s; dodging, every bolt missed and the rank went up (into Qi Foundation, then Spirit Core); the storm and the darkening cleared after; no errors.

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
- **Every pet is its own species**, with its own anatomy, silhouette and face. No two share a body plan or head design. Its eyes suit what it is: big, expressive eyes where the creature calls for them, natural ones where they would fight it (the Galaxy Manta has a real manta's small, deep eyes on the sides of its head). The Cosmic Jellyfish has none, by the owner's decision (November 6, 2026). Never a plain glowing ball.

### Duplicates

Hatching can give a pet the player already has, so a spare always has a use (`shared/PetRules`, `GameConfig.PetFusion`):

- **Fuse (Pets window):** a spare copy goes into another of its kind, and their levels add up to Level 5. Each level past the first adds 10% of the pet's base Qi bonus, so a Level 5 pet gives 1.4 times its bonus. The server picks the copy, the lowest level free one.
- **Sell (Buy & Sell):** a pet sells for its value times its level, so fusing never loses what its copies were worth. **Sell all spares** sells every extra copy up to Epic in one go and keeps the best of each kind; Legendary and rarer only ever sell one by one.
- **Lock (the padlock on each pet's card):** a locked pet can't be sold or fused away. Mythical and Secret pets hatch locked.
- **Equipped pets** can't be sold or fused away either.
- **Secret pets** take one more step: a dialog naming what is being given up, its button waiting 3 seconds. The server refuses to sell or fuse one without that confirmation.

### Spirit Beast Codex

A book of every beast (the Codex button on the HUD's rail; `client/Pets/CodexController`, `server/Pets/Codex`, `shared/CodexRules`, `shared/PetLore`, saved as `Codex`), so collecting stays worth it after a stronger companion. An entry stays for good: selling or fusing the pet leaves it in the book. Every pet owned before the Codex existed is entered when the player loads.

- **Pages:** one per egg, in the order they unlock, drawing only that page's portraits. A **Lost Lineages** page appears for a retired beast the player owns (Nine-Tail Moonfox); those don't count toward the goals.
- **The game's creators** (`GameConfig.Codex.CreatorUserIds`, the owner's account; November 8, 2026) have every beast in their book from the start, those added later included; their rewards are claimed as anyone's are.
- **An undiscovered beast** is a black silhouette named "???", with its rarity and the eggs that hatch it.
- **A discovered beast's entry:** a turning portrait, theme, Qi bonus, the player's best level, its description, each egg that hatches it with the chance, and its special, with **Watch it**: a copy appears before the player and performs the special, seen only by them.
- **Rewards, claimed once:**

| Goal | Lasting Qi | Spirit Stones (share of a weapon of the player's realm) |
|---|---|---|
| Discover 5 | +2% | 0.25 |
| Discover 10 | +3% | 0.5 |
| Discover 20 | +5% | 0.75 |
| Discover 30 | +5% | 1 |
| Discover 40 | +10% | 1.5 |
| Discover 50 | +10% | 2 |
| Discover every beast | +25% | 5 |
| An egg's full page | none | 0.25 up to Legendary, 0.5 with a Mythical, 1 with a Secret |

### Animated pets and their specials

**How they're built**

- Animated pets are exported as separate jointed parts (`tools/blender/export_pet.py --rig`).
- The recreated pets are one smooth skin on a skeleton instead, starting with the Wind Sprite (`tools/blender/pets/wind_sprite.py`). `PetRig.buildSkinned` builds them and poses their Bones through the same `rig.motors` the jointed pets use. Each mesh keeps a Motor6D from the part that holds the bones, or it stays in its bind pose.
- Each one is animated in code by `src/client/Pets/PetRig.lua`, with an idle pose, a moving pose, a flying pose and a special.

**When specials play**

- When the owner ranks up.
- Every 25 seconds while the owner cultivates.

Specials are visual only.

| Pet | Look and motion | Special |
|---|---|---|
| Aqua Wisp | A small water seahorse (recreated 2026-11-09): sea-blue going to clear aqua, pale as foam on its belly, sunlight netted over it; a crown of curling wave-crests tipped with foam, big ocean eyes, a short snout with a little round mouth, a see-through fan on its back, little fins behind its cheeks, leafy fronds, its tail curled into a spiral. It hovers upright, its fan rippling fast; twirls, curls its tail, blows bubbles | **Tide Spiral:** curls tight and twirls until three ribbons of water spiral up around it and burst into a shower of droplets, ripples running out across the ground |
| Sunscale Dragon | Winged solar dragon in bronze, copper and gold scale armour, a corona frill of gold blades and a sun-fan tail tip; walks on four legs, breathes its raised wings at rest and beats them in flight | **Solar Corona:** flares its wings and lifts its head as a sun forms before it, throwing out a ring of rays, golden scale shards and a ground wave of sunlight |
| Ember Wyrm | A campfire salamander (recreated 2026-11-09): a chubby baby wyrm of charcoal crust cracked with glowing magma, ember spots down its flanks, a warm ember belly, sleepy ember eyes and coal-glow cheeks, a crest of little flames down its back and a tail tip burning like a campfire. Sits low and content; walks with a salamander's sprawl; wags, sniffs, stretches; naps curled after a while | **Bonfire:** rears up and swings its burning tail over its back, stoking its campfire into a roaring bonfire, embers showering and a ring of fire running out across the ground |
| Lunar Hopper | The jade rabbit of the moon (recreated 2026-11-10): a round, soft rabbit sat up on big flat feet, pearl white with a cool moonlit sheen and faint craters on its haunches; long lop ears hanging beside full cheeks, their tips dipped in moonlight blue; big moonstone eyes and a glowing crescent on its brow; a little jade pestle in its front paws. Moves in floaty hops that hang a moment at the top, moon dust where it lands; flicks and perks its ears, wiggles its tail, taps its pestle; loafs with its eyes shut after a while | **Moon Elixir:** raises its pestle and pounds three times, each stroke chiming; on the third a little moon of elixir rises out of it to hang over its head, then bursts in a flash of moonlight, a ring of crescent moons spilling out and settling across the ground round it and motes of moonlight rising; it holds its pestle up, proud |
| Volt Fox | A thundercloud fox kit, after the raijū, the thunder beast that runs in the storm clouds (recreated 2026-11-10): storm grey with a pale muzzle, chest and cheek tufts; great ears with a slate rim, forked at their tips in electric blue; zigzag bolts of blue down its legs and on its cheeks; bright storm-blue eyes; its tail a short stalk carrying a little thundercloud of its own (a little see-through), lightning flickering inside it and hanging under it. Trots, diagonal pairs together, its cloud bobbing behind; flicks an ear, sits a while, drops into a playful bow with its cloud wagging, looks up as its cloud rumbles; sits and nods off after a while, its cloud dimming | **Thunder Comes Home:** lifts its cloud high, billowing dark and flashing; a bolt leaps from it over its head and strikes the ground in front of it twice, and the strike becomes a crackling ball of lightning that bounces back to it in two hops and leaps home into its cloud, which flashes bright; it shakes out its fur |
| Astral Whale | The starsong humpback (recreated 2026-11-10), after a humpback calf: a big soft head with knobbly tubercles along its rostrum and chin, a gentle smile arching back to its eye, a deep throat pleated from chin to navel, a small dorsal fin on a hump, the knuckles of its back running to wide notched flukes with a scalloped edge, and long wing-like flippers knobbed along their leading edge. Its skin is the sky at dusk from the zenith down: night indigo on its back with faint stars, dusk violet, a band of rose with a thin gold horizon, pearl beneath. Golden strings lie in its throat grooves and its flipper knobs are small pale stars. Swims in the air in slow strokes, flippers gliding, and looks at you often; its strings breathe softly and its stars twinkle; spouts a puff of stardust, waves a flipper, hums (a ripple of light along its strings) or rolls slowly over; sleeps tilted head-up as humpbacks do | **Song Between Stars:** rolls belly-up and arches into its song, its strings shimmering like a strummed harp; three golden rings of sound ripple out through the air and each faint star hanging round it chimes bright as a ring reaches it; it rolls back and spouts stardust |
| Origin Serpent | The first spirit vein, a loong (recreated 2026-11-10; the owner liked the old one, rebuilt and improved): its long body corkscrews up through the air round an invisible axis, its tail trailing below like a root of light, its neck carrying its head forward over the top; faceted carp scales of dark primordial slate edged in silver, the world's first Qi glowing cyan in their seams, a vein of light down each flank, a pale plated belly, a row of spines down its back and a frond tuft at its tail. A big, fierce head (the owner: "more bigger and fiercer"): a long flat-topped muzzle with a ridge down it, heavy brows over narrowed cyan slit eyes, a jaw open on great fangs and rows of teeth, spiny cheek frills, swept stag antlers tipped in cyan, two long glowing barbels. Two Qi rings, magenta and cyan, orbit round it in opposite directions. A slow wave runs up its coils; light pulses up its veins from tail to head; it looks at you often, growling low; roars, snaps, flicks its tail, rises in its coil or glares; settles half-lidded when left alone | **The First Vein:** its coils rise and its head rears as light races up its veins and its rings spin up; it roars and a double helix of cyan and magenta light erupts from its coil and climbs into the sky |
| Bonefire Dragon | A hulking dragon of bare bone held together and up off the ground by the blue soul fire burning in its ribs: it hangs in a predator's crouch; a heavy skull with two great dark ram horns, hooded brows over empty sockets that each hold a point of cold light, flames streaming from them; fangs, and the fire in its throat; tall blades of spine over its shoulders; the bare bones of its wings raised and half folded like a burnt tree; a long tail ending in a spiked knot of bone. Its fire flickers up through the ribs, which are scorched black where it licks them | **Ossuary Pyre:** rears up as its fire blazes, then slams down: a ring of burning bone spires bursts up from the ground round it and a pillar of soul fire roars out of its chest |
| Dreadfang Cerberus | Hulking three-headed hellhound, dark hide split by glowing cyan cracks; trots on the ground, gallops in the air, each head moves on its own | **Hellfire Breath:** rears all three heads and blasts cyan fire from every mouth |
| Golden Kirin | A radiant celestial kirin: pearl-white, legs dipped in gold to the knee, gold flame-scrolls on its shoulders and haunches, big golden sun-eyes, two gold crescent horns, long gold barbels, a mane and tail of gold silk ribbons, a sunburst arc of light behind its head; it never touches the ground, a lotus of light under each hoof (recreated 2026-11-09) | **Lotus Bloom:** rears up, its halo flaring, and a great lotus of golden light blooms on the air beneath it, a ring of light running out across the ground |
| Moss Golem | Hunched stone guardian grown over with moss, ferns and a sapling, one boulder fist and one root claw; lumbers and breathes | **Groundbreaker:** slams both arms down, bursting stone shards and an emerald shockwave |
| Mycelium Sprite | Glowing mushroom spirit with a dripping cap and a lattice skirt; drifts and waves its spore puffs | **Spore Bloom:** scatters spores and a ring of glowing mushrooms |
| Jade Spirit Panda | Stout jade guardian with leaf ears, dark-jade eye patches and a crystal cluster on its back; ambles heavily | **Jade Lotus:** rears up and slams down, opening rings of jade lotus petals |
| Jade Antler Deer | Slender celadon deer with branching jade antlers, a jade-leaf crest and a jade breastplate; four-beat gait | **Sacred Grove:** rears up and grows a ring of glowing jade branches from the ground |
| Dawn Phoenix | Upright sunrise firebird with raised crimson-to-gold wings, a sunburst crest and curling flame tail feathers; trails gold from both wingtips | **Sunrise Rebirth:** flares its wings and bursts a rising sun with rays and spiralling flame plumes |
| Rune Sphinx | Charcoal feline guardian with a stone-blade mane, an obsidian horn crown and glowing runes of one forgotten alphabet; prowls with a slow, judging gaze | **Rune Seal:** raises its chest and opens a spinning seal of rising rune glyphs and amber pillars |
| Magma Cub | Young volcanic beast on huge basalt forearms, molten core glowing through cracked chest plates; knuckle-walks and tilts its head | **Magma Pop:** winds up, slams both fists down and hops, bursting basalt spikes and lava blobs out of a molten pool |
| Azure Sky Dragon | A great dragon of the high sky (recreated 2026-11-12, after the owner's reference: a dragon gliding through an aurora above the clouds, jaws open): it never lands. Built in a glide: broad wings spread wide, legs drawn up, a long thick neck reaching forward. A heavy, deep-chested, muscular body; a long wedge of a head with heavy brows over narrow glowing ice eyes, a ridged snout, rows of sharp teeth and a pale light in its throat; two great horns sweeping back from behind its eyes over a crown of swept spikes, spiked cheeks and a row of spikes along its jaw; a shaggy mane of spines down its neck and a row down its back and long tail. Deep slate-teal scales lit with ice blue, a pale grey-blue belly, aurora-pale wing membranes (lavender-white to ice cyan), dark talons. Slow heavy wingbeats, rising on each downstroke; banks into its turns; looks about and at you, its jaw working; now and then roars, snaps, banks round, lashes its tail or reaches its claws forward | **Aurora Gale:** rears back, wings raised, the light gathering in its throat; then lunges and breathes a cone of aurora wind (ice, violet and green streaks), a ring of pressure rolling from its jaws, ice glitter in the gale |
| Spirit Crane | Tall pearl-and-silver celestial crane, misty slate flight feathers, three pearl plumes from a turquoise lotus crown, gold eyes ringed in turquoise, spiralling tail streamers | **Halo Ascension:** lifts its neck skyward as three luminous rings rise from feet to crown and burst into drifting pearl feathers |
| Wind Sprite | A baby wind spirit whose body runs into one great scroll of wind: big teal eyes, a sly one-fanged smile, a curled topknot, seed-key wings, little robe sleeves with coral cuffs, a jade bead on a cord; blinks, glances about, raises a brow and reaches out a sleeve to tug twice | **Tugging Gale:** fills its cheeks, then blows three ribbons of wind that wind round each other and carry petals away while its tail unwinds |
| Galaxy Manta | A great ray whose back is deep space: a nebula spiralling out across both wings, gold constellations and edging, pearl beneath; a true manta's flat head with small deep eyes on its sides and curled horn fins, a comet on its whip tail. Under its wings a small galaxy really turns, with a ringed planet and a moon going round in it. Waves run along its wings, it banks into turns, feeds with its mouth open and barrel-rolls | **Turning of the Heavens:** rears until the galaxy faces forward, spins it up, then sweeps down and throws it open in a wheel of stars with a ring of light |
| Stormhorn Kirin | A tall deer-dragon of storm-slate, scaled over neck and shoulder with a pale plated throat, on an arched neck and a heavy, stern head with one gold eye on each side. Its horn rises from a bronze sheath as a forked bolt of lightning; its mane and tail stream on a wind only it feels, lightning flickering in the mane; veins of lightning run under its hide; cloven bronze hooves spark where they land. Walks a rocking canter on the air, paws and tosses its head at rest | **Thunder Answers:** rears with its horn raised, then brings its hooves down in a burst of sparks as lightning flares through its mane |
| Cloud Sheep | A fat little sheep whose fleece is a real cumulus, sunlit on top, rain-grey beneath, a silver lining at the edge; a small slate-blue face, drooping ears, little ram curls, half-closed gold eyes; breathes with its whole fleece, paddles its hooves on the air, nods off and starts awake, yawns | **Cloud Bloom:** tucks its legs and draws in a huge breath, swelling up, then lets it go in one long sigh of soft cloud |
| Jade Wyrm Turtle | A mountain that took a step. Its shell starts at the rim as polished imperial jade, plates seamed in gold, and rises into a crag of terraced rock and moss: a spring running down the cliff into a pool, one old plum in blossom leaning over the rim, a dark pine, and a tiny red-pillared pavilion that gives the scale. Out of the front comes the wyrm: a long S of a neck with a low sail, two swept horns, an old gold beak, pale stripes, a heavy-lidded amber eye. Elephant-thick legs on three-clawed feet. It stands on the ground instead of hovering, treads one foot at a time with the crag rocking over it, turns its neck round to look at its garden, chews slowly, and rows on the air like a sea turtle; petals drift off the plum | **Between One Step and the Next:** raises one forefoot, slowly, the whole mountain leaning off it, then sets it down: dust and stone chips along the ground, a flurry of petals, and the garden has grown |
| Nebula Owl | An owl whose wings are a stellar nursery, and who already knows what you are about to do. A wide head, a dished pale face, huge gold eyes (each iris a disc of dust winding in to a dark centre) under lids that rest low: an unimpressed stare. Every feather is its own, and one sky runs across them all: indigo, violet and magenta gas with dark lanes of dust, a few new stars burning in the wings; pale and chevroned beneath. It hovers in silence on slow overlapping wingbeats, beats and glides in flight. Its head snaps to a new place and holds still, turns right round to look behind it, one brow raised; it blinks one eye at a time | **Stars Not Yet Born:** spreads its wings as gas gathers before its breast, and a new star lights exactly when it knew it would; one silent wingbeat, and it goes back to looking unimpressed |
| Cosmic Jellyfish | A real see-through glass bell with a small nebula slowly turning inside it, rose and amber gas with teal at its edges and four gold horseshoes, as a moon jelly has; fine canals run from it to the scalloped rim; frilled arms and six long tentacles hang below. It has no eyes (the owner, November 6, 2026). It swims in beats: the bell closes quickly, it rises, it opens slowly and sinks, and all below follows late. Its bell leans gently toward you wherever you stand | **Rolling Nebula:** opens its bell wide as the nebula spins up, then closes once, hard, and a ring of glowing gas rolls off its rim and sinks away |
| Starfall Fox | A young silver fox: black fur tipped with silver and the odd hair-tip catching like a real star, white cheek ruff and bib, a big brush with a white tip, gold dust on its forepaws and muzzle from digging. Its face is unlike any other pet's: one long canine wedge with no eyeballs, each eye a flat almond of amber inlaid in an ink rim, with a slit pupil that slides across it and lids that close by stretching from the rim; it wears a sly, narrowed look. Quick, snapping head, watches the sky, digs furtively and checks over its shoulder; flying, it stretches out in long bounds with its tail streaming behind like a comet | **Star In Its Teeth:** a falling star comes down at a slant; it crouches, rump up and wiggling, leaps, and takes it out of the air with a flash in its teeth and a little gold falling away; it lands holding it, digs fast, and buries it |
| Lantern Warden | A stooped wayfarer spirit: three tiers of old straw rain-cape gone to moss at the shoulders, a tilted conical hat with pink blossom growing on it, long thin bird legs with cloth wrappings and root toes, long pale hands. A gnarled crook grows from its back, arches over the hat and hangs a bronze and paper lantern out to its left, where it swings on a chain. Its face is unlike any other pet's: a pale lacquered mask with a very small mouth and two upward crescents cut right through; small ember pupils slide about behind them and blink by drawing back into the dark. Very still, then slowly tilts its head; its light sometimes sinks and it taps the lantern; flying, it holds its hat on | **The Long Way Round:** it lifts the crook and reaches for the lantern, and the flame stands up; a path of small lights runs out from its feet, winds once round it and comes back to exactly where it started; it watches them all the way, and tilts its head |
| Dream Moth | A plump, fluffy moth: a snow-white pom-pom ruff, a banded rose and lilac body with a soft brush at the tip, feathery fern-leaf antennae, a coiled tongue. Four broad dusty wings with scalloped edges: lilac forewings with a cream crescent moon, rose hindwings each with an eyespot drawn as a sleeping eye, its lid closed and lashed. Its face is unlike any other pet's: misty lilac compound eyes, finely faceted, each with the dark pseudopupil a real insect's eye has, which turns to face whoever is looking. Flutters, never quite straight; fans its wings slowly; uncurls its tongue to taste the air | **A Forgotten Dream:** its tongue uncurls, and faint threads of a dream nobody remembers drift in, spiralling, to the tip of it; one slow, great wingbeat, and a shimmer of scale dust drifts down |
| Prism Armadillo | An armadillo armoured in cut crystal: a shield over the shoulders, four bands that slide over each other, a shield over the hips, every plate faceted like quartz with a faint spectral sheen on its bevels; a crown of crystal tiles on its head, a ringed crystal tail; dusty-rose skin, a long pink snout, tall pink ears, stubby legs with big digging claws. A row of small prisms down its back, each drifting slowly through the spectrum. Its face is unlike any other pet's: small bead eyes under a crystal brow with no upper lids; soft cheek pads turn up round each eye from below, half up when it is pleased, all the way for a blink. Sniffs at everything, rears up to look about, rolls up now and then purely to show off; flying, it rolls up and spins through the air | **Every Colour:** rolls up into its armour and spins in place, faster and faster, its crest blazing; it pops open in a fan of thin rays of every colour and a scatter of rainbow glints, then waits, squinting, to be admired |
| Crystal Snail | A glossy jade snail, its soft wet body pebbled with fine tubercles, its neck lifted, a pale gliding foot; on its back a coiled shell of pearly aquamarine banded along its growth, with a small spire on one side, and clusters of geode crystal growing out of it, the tallest in each cluster glowing. Its face is unlike any other pet's: two eyes on long stalks with no lids; like a real snail it blinks by drawing a stalk in, one at a time, and its feelings show in how the stalks lean, wave and droop; a small smile and a soft blush below. It glides on a slow wave of its foot, stretching and gathering, and leaves a faint road of crystal glints behind it; shy now and then, it draws both stalks in | **A Hundred Years:** draws itself in under its shell, stalks first, as its crystals brighten; a road of crystal grows up behind it shard by shard along the way it came; then its eyes come out first, to see whether anyone noticed, and the rest of it after |
| Golden Mane Lion | High-shouldered royal lion, a tiered mane of flame-tipped locks in bronze, gold and champagne, a crest of reddish-gold locks, deep-set amber eyes; heavy, deliberate stride | **Sovereign Roar:** opens its jaw as golden shockwave rings roll out, solar rays flare behind its crest and a ring spreads beneath its paws |
| Abyss Anomalocaris | The Primordial Abyss Egg's own pet (November 8, 2026): a hunter from the first sea, made of the egg's primordial stone (dark slate, warped strata, thin ochre seams), paler beneath. A low oval head shield ringed in ochre; a flattened trunk of nine segments rimmed in ochre, setal ridges along its back; nine pairs of shingled flaps, each front flap resting over the next, the only light on it a thin magenta line round the skirt's scalloped outer edge and along its tail blades; a tail fan of three pairs of long blades raised in a V; two great ringed arms curled like fern fronds under its head, each segment armed with a pair of curved bone-pale spines; two large kidney-shaped compound eyes on short thick stalks, faceted, black-violet; a round mouth cone of plates beneath. It always swims through the air: a wave runs back along its flaps, its trunk undulates, it banks into turns, its arms flex as if tasting the water and its eyes swivel on their stalks | **The First Hunt:** opens its arms wide as it draws back, lunges, and snaps them shut; sparks fly from the spines and two rings of magenta light ripple out from it, level, like the surface of the first sea closing over the strike |
| Voidscale Hydra | Recreated November 8, 2026 (it had only a placeholder): not a serpent but a low, sprawling reptile on four splayed legs with three-clawed feet of pale glass, a heavy tail curling to one side, and three necks from its shoulders: the two outer ones long, ending in big viper heads, triangular and heavy-browed; the middle one shorter, forking into two small young heads, the two the void grew where one was cut. Its scales are separate plates of polished black void glass in a snake's diamond lattice, and between them there is simply nothing: a starry deep-blue void shows through every gap, each plate's edge catching a thin bright-blue rim; broad scutes beneath. Its eyes are glowing pale-blue slits under the brows (no eyeballs, no lids); each mouth hides a forked tongue of blue light. It walks like a monitor lizard, legs out in diagonal pairs, body swaying, tail following; each neck sways and each head chooses its own gaze, tongues flicking each in its own time, and now and then the two young heads turn on each other and hiss | **The Void Between:** all four heads rise and draw back as a rift tears open in the air before it, two jagged edges of blue light drawn apart over a starry dark; they strike into it together, tongues out, and it closes |
| The Nameless One | Recreated November 8, 2026 (it had only a placeholder): not an animal. A tall figure with no legs, floating, wound in loose pale ribbons round a body of nothing (matte indigo-black, no light in it): straps crossing its chest and over its high square shoulders, a band round the chest, spirals round a narrow waist, and below it eight ragged streamers drifting out as if in water. Long thin arms bandaged tight, and from each wrist two loose ribbon ends where a hand would be, their tips glowing: the ends that write. No face: the front of its hood is a deep oval hollow with one small point of white light floating in it, framed by a brow band and a chin band; the hood's point droops behind. Two loose scarves lift off its shoulders, weightless, and rise beside a thin octagonal halo with one side missing. Every ribbon carries one line of large handwriting in faded violet ink, some words struck through, some nearly erased. It bobs, its hood turning toward you and tilting as if trying to read you; now and then one arm lifts and its glowing ends write a loop of light in the air | **Unwritten:** raises both arms, and words in a hand nobody can read write themselves in a ring of light around it; each is struck through, the writing fades, and for a moment it is gone |
| Eclipse Cat | Recreated November 8, 2026 (it had only a placeholder), after the owner's concept sheet: a stylized black cat with a big head on a compact, fluffy body. Very large pointed ears, violet in their hollows, filled with soft white-lavender fur and rimmed in gold; a frame of fluffy locks round its face; a glowing gold crescent on its forehead; a small pointed mauve nose. Big almond eyes, violet going light below, a ring of amber gold round a slit pupil, black liner wings at their corners, real lids. A fluffy bib of violet-tipped locks, and over it a navy collar with gold rims and studs; from it a gold crescent framing a dark disc, the eclipse, with a violet gem below. Black fur lit violet where it faces up, a gold spiral on each haunch and shoulder, white-lavender socks. Its tail is a huge crescent: deep violet to bright, faint stars, a gold rim and a thread of gold light along its edge; sparkles drift off it. It walks a cat's lateral walk with its tail high, sits after a few seconds still, and gives you a slow blink when it looks at you; its ears swivel and its tail tip flicks | **Totality:** it sits and looks up as a black moon slides across a golden sun; at totality the corona flares, a ring of dark rolls out and the world dims for a moment while it purrs; then the diamond ring flashes and the light comes back |
| Shadowcoil | Recreated November 8, 2026 (it had only a placeholder): a shadow stoat, in the stylized look of the Eclipse Cat but its own design language of S-curves, loops and smoke. A long, sinuous, low body on short legs; a big round head with rounded ears, smoky lavender in their hollows; big eyes of pale mint-silver eyeshine with a round pupil under real lids, a small slate nose, two pale brow spots. Ink-black fur with soft wisps of smoke at its nape, cheeks, throat, elbows and hocks, and pale mint-silver toe tips. Its long tail is one bushy swirl of smoke, soft ridges twisting along it, black at the root drifting to dusky lavender-grey, coiling up into a spiral with smoke trailing off its point; a faint smoke drifts off it. It bounds like a stoat, its back humping; still a moment, it rears up on its hind legs to look about; still a while, it lies down curled, tail coiled, and dozes; its glances are quick and sly, its eyes darting ahead of its head | **First Move:** its eyes go wide and it pours itself down into its own shadow; the shadow races round a loop along the ground, two points of eyeshine in it, leaving a fading trail, then it bursts back up out of it in a leap and a spray of dark drops and smoke |
| Celestial Pearl Dragon | Recreated November 9, 2026 (it had only a placeholder serpent): a real dragon, and a fierce one (the owner's word). A deep-chested, heavily muscled body on four strong legs with big hooked claws; a thick S-curved neck thrusting a long wedge of a head forward; two great wings raised behind it, a hooked claw at each wrist, their membranes ribbed like scallop shells and cut in deep scallops between the finger tips. Its head is all angles: a hard brow ridge sloping down to the snout in a scowl over narrow sapphire eyes with a silver slit pupil and dark lids, fangs showing over the lip, carved slit nostrils, a long pair of moon-silver horns twisted like conch shells and a short pair from the jaw. Swept-back blade scales run from the crown down the neck, back and tail. Pearl-white nacre in overlapping scale rows with a slow rainbow sheen, ivory belly plates, moon-silver claws and wing-fingers. It stands on three legs and holds the flawless pearl to its chest in its right forefoot, talons curled over it; the pearl glows and motes of light drift off it. Standing, it breathes with its raised wings, flexes them now and then or tosses its head with a snort, and holds you in a slow, deliberate stare; to go anywhere it lifts off on heavy wingbeats and hovers low, legs tucked | **Heaven Condensed:** it rears on its hind legs, wings flared, and raises the pearl to the sky; a column of heaven's light pours down into it, rings closing on the pearl and motes streaming in; then it lunges, head and pearl thrust forward, wings snapping down, and the light bursts out: a flash, a ring rolling along the ground, shards of pearl light |
| Celestial Snow Leopard | Recreated November 9, 2026 (it had only a placeholder): a grown snow leopard, a majestic hunter (the owner's choice), the opposite of the Eclipse Cat's big-headed look. A long, low, plush body with a deep chest; a small head carried low and forward with a domed brow, a short broad muzzle, a thick cheek ruff and small rounded ears set wide; huge snowshoe paws; a very long tail thick with fur all the way. Smoky ice-white fur with a faint frost sheen, a white belly; broken dark rosettes with smoky centres, solid spots on the head and legs, a dark tail tip; the rosettes along its back hold the night sky, deep blue speckled with ice-blue stars. Pale ice eyes going to aquamarine with a round pupil and dark rims, a pink-grey nose, frosted white whiskers, icy blue-grey paw pads; a fine frost drifts off its tail. It prowls low with its shoulder blades rolling; still a moment, it sinks into a stalking crouch and stares, haunches wiggling; still a while, it lies down sphinx-like with its tail curled beside it; its stare is steady and intense | **Where the Sky Begins:** it crouches, wiggles and pounces in a long leap; frost bursts up where it sprang, and a trail of its pawprints freezes into the ground ahead of it one by one, glowing with starlight, then shatters into glittering snow |
| Comet Stag | Recreated November 9, 2026 (it had only a placeholder): a powerful stag whose antlers are comet tails (the owner's choice). A red deer's build, deep-chested, with a thick shaggy blue-grey neck ruff, carried on sturdy legs; a long fine head with big dark eyes (a ring of icy silver round a horizontal pupil) and large leaf-shaped ears. Its antlers do not branch up: they sweep straight back from the crown like a comet's two tails, each a broad palm (the dust tail, icy white going to gold, streaked lengthwise) with a fine straighter tine above it (the ion tail, white going to vivid blue) and a short brow tine forward; a comet's nucleus glows on its brow between them. Deep night-blue hide with pale icy dapples drawn out backward along its back as if streaming in the wind of its speed, a white rump patch round a short tail, icy silver hooves; comet dust drifts off its antler tips. It trots with its head high, tosses its antlers or paws the ground now and then, and lies down with its legs folded after a long while still; in the air it runs in long bounds, a comet's trail streaming from its brow | **Once in a Lifetime:** it rears, forelegs striking, and a comet leaves its brow, a white-hot head with a narrow blue ion tail and a broad gold dust tail, arcing up and across the sky while the stag watches it go; at the top of its arc it bursts into glittering dust that falls over it |
| Sand Phantom | Recreated November 9, 2026 (it had only a placeholder blob): a desert jerboa spirit (the owner's choice). It sits up on long kangaroo hind legs and huge flat feet, tiny forepaws held to its chest; a big round head with enormous broad ears (pink-sand inside) and enormous dark eyes rimmed in amber gold and flecked with gold like sand in the light, a short muzzle with a little pink nose and very long whiskers; a very long thin tail held out behind for balance, ending in a flat brush, a dark band and a cream tip. Sand-gold fur with wind-laid dune ripples across its back, a cream belly, muzzle and feet, a pale stripe across each haunch; fine sand streams off its tail's brush and its ears. It hops on both feet together, its tail swinging to balance each hop; still, it sits up tall to look about, freezes when something catches its eye, or washes its face with its forepaws; its gaze darts, quick and shy | **Mirage:** it sits up tall and stares straight at you, then blows away downwind as sand; a dust devil spins up beside where it stood, it re-forms inside it, shakes the sand off and hops back |
| Solar Butterfly | Recreated November 9, 2026 (it had only a placeholder blob): a swallowtail of sunset glass (the owner's choice). A slender, smooth, dark body with fine gold lines; a small head with big glossy dark bead eyes rimmed in honey gold; long thin antennae ending in gold clubs; short black legs tucked under it. Angular wings, the hindwings drawn out into slim swallow tails, made like stained glass: black veins and two rows of cross-veins frame panes running from noon gold at the root through amber to sunset red at the edge, each pane its own shade; a black margin set with gold lunules; on each hindwing a glowing sun-disc eyespot ringed in black and red; warm motes of stored sunlight drift off the eyespots, more after dark. It flies in slow, deep wingbeats with glides between, bobbing; still a few seconds, it drifts down and lands on its legs to bask, wings spread flat, now and then closing them over its back | **Afterglow:** it rises and spreads its wings wide and still as the sunlight gathers; then lets it go in one slow wingbeat: a warm flare turning through sunset rose to dusk, motes of gold drifting up and away, and for whoever is near the world glows like evening for a moment |
| Obsidian Guardian | Recreated November 9, 2026 (it had only a placeholder golem): a black-glass gargoyle (the owner's choice), in a design language of its own: knapped stone. It perches as gargoyles do, crouched on its haunches with its long arms down before it and its hands on the ledge, its head thrust out low between high shoulders and its tail curled round its feet, ending in a knapped spearhead. All of it is volcanic glass worked like a stone blade: cut into flat facets with shallow flake scars and ripple rings in them, glassy black with thin streaks of violet flow-banding. Only its face is polished, a dark violet mirror over its muzzle and between its eyes, cut in a few broad planes; its eyes are two slits of violet light set deep under a heavy brow, under two brow shards that move; two tusks from its lower jaw; thick faceted horns swept back. Its wings are a bony arm and broad, jagged shards of glass with gaps between them, never feathers or membrane: folded, each wrist is a peak above its shoulder with a short spike, and the shards hang round it like a cloak, their thin edges smoky violet. Still as the stone it is, then its head snaps round to watch you and holds, its brow shards lowering; now and then it mantles, raising its wings forward over its shoulders, or a shiver rattles through its wings; its tail's point twitches. When its owner goes anywhere it takes off and flies low beside them in slow, heavy beats with long glides, legs tucked and tail trailing, and lands the moment they stop | **Honest Glass:** it rises on its haunches with its wings spread wide and holds you in its stare; its mirror face flashes, and a figure of black glass in your shape stands before it, facing you, for a moment; then the figure cracks and falls apart into shards of violet glass |
| Glacier Puff | Recreated November 9, 2026 (it had only a placeholder blob): an ice pufferfish (the owner's choice), in a design language of its own: polished glacier ice. A round little fish that swims through the air, deep blue at its heart, frosted pale with rime on top, white-blue beneath, banded faintly with the layers of old glacier ice, air bubbles caught in it. A blunt face; big domed eyes in raised rims and no lids (a fish), sapphire irises round big black pupils, each eye swivelling on its own; a small round pursed mouth with a beak of white teeth. Stubby whirring pectoral fins, small rippling dorsal and anal fins, a rounded tail fan, all pale and fine-rayed. Calm, it is smooth: hoarfrost spines lie hidden just under its ice. It hangs half a metre up, its body wagging as a fish's does; its eyes wander, now and then both fixing on you; every few seconds it gulps and a few frost bubbles rise; now and then something startles it and it half puffs, spines pricking out, then settles | **Hoarfrost Bloom:** it takes a great gulp of air and swells into a ball of hoarfrost spines (its body balloons round its middle, its face and tail keeping their size, the spines sliding out of the ice); frost bursts off them in a glittering cloud and a breath of icy mist rolls out; it hangs there turning slowly, then sighs the air out in frost bubbles |
| Storm Bumblebee | New November 9, 2026, in place of the Thunder Jelly (a jellyfish was there already: the Cosmic Jellyfish): a fat, fuzzy bumblebee charged with static (the owner's choice), in a design language of its own: static electricity in fur. A round plush body in overlapping clumps of fur, bristling along its back: an electric-gold collar and a storm-grey back on its thorax; a gold band, a storm-grey band and a snow-white tail on its abdomen, every band's edge a jagged zigzag; a frizzed cowlick on its crown, its tips charged gold. Little arcs of static crackle across its fur. Small smoky wings with dark veins, a blur of a figure-eight beat. Big dark compound eyes, faceted, with a violet storm sheen; a fuzzy gold face; short elbowed feelers with a spark at each tip. In the baskets of its hind legs, where a bee carries pollen, it carries balls of stored lightning; its sting is a needle of light sheathed in its tail. It hovers and bobs, looks round at you, twitches a feeler; now and then it zips off to one side and back, throws a barrel roll, or shivers, every hair crackling at once | **A Lesson Learned Once:** it rises, buzzing harder, fur crackling and glowing; curls its tail under, its sting sliding out; dives and drives the sting into the ground: lightning cracks out across the ground, forking as it runs |
| Timekeeper Tortoise | Recreated November 9, 2026 (it had only a placeholder): a sundial tortoise (the owner's choice), in a design language of its own: an ancient sundial grown into a living shell. A giant land tortoise, its high dome a weathered stone of domed scutes with growth rings following their outlines, lichen on its old crown; on the crown a dial of bronze inlaid in the stone, a ring with twelve hour lines fanning from a tall bronze gnomon blade, and numerals of an age nobody remembers (bars and dots) round it, the bronze gone green with verdigris; a thin line of gold light along the gnomon's sloped edge. A wrinkled old sage of a face: long flowing white brows (which move), a hooked beak of dark horn, small dark amber-ringed eyes under heavy lids that blink slowly; armoured forelegs of big raised scales, columnar hind legs, blunt nails; a short tail. It walks impossibly slowly in a deliberate diagonal step and is never left behind; standing, it turns its old head slowly to look about or at you, its brows lifting, chews on nothing; when its owner flies it pulls itself into its shell, its face peeking out between its folded forelegs, and drifts beside them like a stone | **Stopped Hour:** it plants its feet and raises its head; its gnomon's gold edge flares and a ring of twelve hour marks lights round it on the ground one by one; for a heartbeat time stops (it does not move at all, motes of gold hang dead still, the world fades toward sepia), then the hour moves on |
| Gravity Imp | Recreated November 9, 2026 (it had only a placeholder blob): a pocket-planet imp (the owner's choice), in a design language of its own: a small creature with a world of its own. A big-headed, pot-bellied violet imp, its back darker, its belly and muzzle pale lilac; long leaf-shaped ears, pink inside, out to its sides; heavy-lidded gold eyes under sly brows that rise outward (one rises further when it looks at you); a wide smirk with a single fang showing at its raised corner; blushing cheeks and a few freckles; a short cowlick; long thin arms, long curled-toed feet, a thin tail ending in a spade. It lives on a moonlet about its body's size, pale moonstone pocked with craters, violet veins of gravity glowing in its cracks, three pebbles circling it like little moons round the imp's own middle. Its feet stand on the moonlet wherever it likes, and that way is down: it stands on top with its fists on its hips; now and then it strolls over the front and down under its moonlet, turns to face you and hangs there upside down, smirking, then carries on over the back to the top. When its owner goes anywhere it treads its moonlet round under it like a treadmill; when they fly it sits on top, leaning back on its hands, legs out round its belly | **Which Way Is Down:** it lifts one foot out to the side like a sumo, its arms out for balance, and stamps on its moonlet; the ground round it lets go of its stones, which rise into a ring round the moonlet, spin faster and faster and are flung off to fall; it puts its fists back on its hips |
| Crystal Beetle | Recreated November 9, 2026 (it had only a placeholder blob): a crystal-horn rhinoceros beetle (the owner's choice), in a design language of its own: a living geode of glass and chitin. A stout, proud rhinoceros beetle: a great rounded pronotum and head of glossy indigo chitin with an oil-slick sheen, finely pitted; its wing cases two smooth domes of clear cyan crystal, deep teal at their rims, light caught inside them, phantom growth layers within following their outline, one for every year it has lived; its great horn a single quartz crystal grown in stacked hexagonal segments, one a year, curving up as a rhinoceros beetle's does, frosted at its edges, its newest, the terminated tip, glowing. Big glossy compound eyes; short clubbed antennae of amber lamellae; stout toothed legs with amber hairs and amber-tipped teeth, beaded amber feet with hooked claws; under it, ribbed plates fringed with amber. Every piece of it a rigid plate, as an insect's are. It stands square, turning its head slowly, proud; now and then it tosses its horn, shoves at nothing with its head down, flicks its antennae, settles its wing cases with a shrug; it walks in a tripod gait; when its owner flies it opens its wing cases, swings its smoky hind wings out from under them and buzzes alongside, legs hanging | **Ring of Years:** it rears on its hind legs, horn high, and slams its front down; a ring of crystal points bursts up from the ground round it, one after another, one for every year it has lived, a ripple of cyan light running out along the ground; then the points shatter into glitter |
| Thunderclaw Drake | Recreated November 9, 2026 (it had only a placeholder; a first, wingless conductor-spine drake was rejected by the owner: "I NEED A DRAGON NOT A CROCODILE"): a storm wyvern (the owner's choice), in a design language of its own: a dragon that is a living lightning conductor. Two powerful bird-jointed hind legs with great honed iron talons; its wings are its arms, and on the ground it prowls on their wrists, each armed with a big iron hook, its hands folded back along its flanks, their glowing spurs riding above its back. A lean body pitched up from the hips, a slender S of a neck carrying its head high like a sentinel's: a short angular wedge under a hard brow, a dark mask round molten-gold slit eyes, two fangs over the lip, small iron spikes swept back from the cheeks. Its horns are lightning rods: two copper rods sweeping up and back, each threaded with white porcelain insulators and tipped with a glowing gold ball, an arc crackling between them. Three long fingers to a wing, each ending in a copper spur with a glowing gold tip; storm-cloud slate membranes veined with branching gold lightning, their trailing edges torn jagged; a long tail ending in a copper blade shaped like a lightning bolt; storm-indigo hide, a pale banded belly, a zig-zag bolt down each flank. It walks in diagonal pairs, a wrist with the opposite foot, its hooks striking sparks; now and then it mantles, a crackle leaping between its spurs, or turns its head to watch you; to fly it lifts its wrists clear, opens its wings and beats them, legs tucked | **Called Down:** it rears onto its hind legs, wings flung open, head to the sky; a bolt comes down onto its horns and it glows white-hot; it slams down onto its wrists, hands flung up over it, and the lightning bursts out of it across the ground: a ring of gold light and bolts racing out along it, sparks thrown up |
| Frostfang Serpent | Recreated November 9, 2026 (it had only a placeholder serpent): a frozen-hood king cobra (the owner's choice), in a design language of its own: frozen motion. A huge king cobra, its long tail coiled in a flat spiral on the ground, its front reared in an S; its great hood frosted ice on the front, faceted into plates with fine blue cracks and bold white frost veins, deep glacier blue behind with a frost crescent, and round its rim a crown of clear ice blades. A broad flat head under heavy brow plates, a dark mask through lidless ice-pale eyes with pinpoint pupils (it never blinks), a stern mouth line; its jaw opens on two glowing crystal fangs that swing down from its palate, and a dark forked tongue flicks. Glacier-blue scales crossed by frost crossbands (chevrons pointing to its head, a white line down their middle), a pale banded belly. Shards of ice drift off it and hang still in the air; now and then it sheds a pane of clear ice that slides off its coil and shatters. It never uncoils: it glides, leaning in, a ripple running round its coil, frost forming where it passes; on the wing it hovers, coiled | **The Moment That Matters:** it rears, hood flared, fangs bared, and strikes; where it bites, a hexagon of stopped time spreads across the ground, shards of ice hanging still in the air; then the moment ends and everything shatters |

### Pet voices and specials' sounds (November 9, 2026)

The owner chose it from the suggestions ("do the 3"): the pets were silent. Each animated pet (49 of the 50 with a rig; the Sunscale Dragon still has none, 2026-11-11) has a **voice**, a short call it gives every 9 to 18 seconds as it idles in the world (a take picked at random, its pitch a little either side of its own), and a **sound on its special**, played at its climax as the burst goes off (`client/Audio/PetSounds`, played from `PetRig`). Never from a Codex portrait, never over a special, heard within 70 studs (a special within 160).

- **Only Roblox's licensed library** (Pro Sound Effects), each file checked to load in this place: 168 measured. Picks by kind: the closest real creature (the bee's buzz, the serpent's snake hiss, the lion's growl, the sheep's bleat, the fox's yips, the owl a reverberant cosmic cry since the library's owl hoots are all long), or for spirits and stranger things a magical tone (the crane's soft synth tones, the Nameless One's unintelligible whispers, the Obsidian Guardian's low ceramic ring, the Lantern Warden's key dings). Specials match their moment (fire bursts for the fire beasts, ice crackles and shatters for the ice ones, a lightning burst for the bee's sting, a tuning fork for the Timekeeper's stopped time).
- **No two pets share a voice**; pets of one family (the lions and the dragons that borrow lion growls, the two kirins, the panda and the armadillo's grunts) are told apart by pitch. The Thunderclaw Drake has a giant creature growl, not the hiss the Ember Xuanwu guardian uses.
- **Levels from measured loudness** (PlaybackLoudness in Play, muted): a pet's voice lands at about 24 and its special at about 48, under the player's own moves (a leap about 38, a dash about 59). Takes too quiet to carry (some wing flutters, a key ding, the first spore pops) were swapped for louder ones of the same kind.
- **Not yet listened to:** the owner judges them by ear; to change one, edit its line in `PetSounds` (ids, volume, pitch).

### Roster by first egg

**Beginner Qi Egg (Beginner Isle)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Aqua Wisp ★ | Common | Water | +10% |
| Ember Wyrm ★ | Uncommon | Fire | +20% |
| Lunar Hopper ★ | Rare | Moonlight | +35% |
| Volt Fox ★ | Epic | Lightning | +50% |
| Golden Kirin ★ | Legendary | Nature | +60% |
| Astral Whale ★ | Mythical | Cosmic | +100% |
| Origin Serpent ★ | Secret | Primordial | +150% |

**Spirit Breeze Egg (Beginner Isle)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Wind Sprite ★ | Common | Wind | +10% |
| Cloud Sheep ★ | Uncommon | Clouds | +25% |
| Spirit Crane ★ | Rare | Spiritual energy | +40% |
| Azure Sky Dragon ★ | Epic | Wind and sky | +55% |
| Stormhorn Kirin ★ | Legendary | Storms | +70% |

**Elemental Core Egg (Beginner Isle)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Glacier Puff ★ | Common | Ice | +15% |
| Storm Bumblebee ★ | Uncommon | Electricity | +25% |
| Crystal Beetle ★ | Rare | Crystal | +45% |
| Gravity Imp ★ | Epic | Gravity | +65% |
| Thunderclaw Drake ★ | Legendary | Lightning | +80% |
| Frostfang Serpent ★ | Mythical | Ice | +130% |

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
| Dream Moth ★ | Common | Dreams | +15% |
| Crystal Snail ★ | Uncommon | Crystals | +30% |
| Prism Armadillo ★ | Rare | Crystals | +50% |
| Lantern Warden ★ | Epic | Light | +70% |
| Jade Wyrm Turtle ★ | Legendary | Earth | +85% |

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
| Obsidian Guardian ★ | Rare | Darkness and crystal | +55% |
| Sunscale Dragon ★ | Legendary | Solar | +60% |
| Dawn Phoenix ★ | Legendary | Fire | +60% |

**Magma Heart Egg (Ember Peak)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Sand Phantom ★ | Common | Sand | +15% |
| Solar Butterfly ★ | Uncommon | Solar energy | +30% |
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
| Starfall Fox ★ | Common | Stars | +20% |
| Cosmic Jellyfish ★ | Uncommon | Nebulae | +40% |
| Nebula Owl ★ | Rare | Cosmic energy | +65% |
| Celestial Snow Leopard ★ | Epic | Ice and celestial energy | +95% |
| Comet Stag ★ | Legendary | Comets | +115% |
| Celestial Pearl Dragon ★ | Mythical | Celestial energy | +190% |

**Astral Sanctum Egg (Moonlit Isle)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Eclipse Cat ★ | Epic | Darkness and eclipses | +110% |
| Timekeeper Tortoise ★ | Legendary | Time | +130% |
| Galaxy Manta ★ | Mythical | Cosmic energy | +220% |

**Forbidden Origin Egg (Origin Abyss)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Shadowcoil ★ | Rare | Shadow | +100% |
| Rune Sphinx ★ | Legendary | Ancient magic | +170% |
| Thousand-Year Dream Eater ★ | Mythical | Dreams | +280% |
| The Nameless One ★ | Secret | Unknown cosmic energy | +420% |

**Void Rift Egg (Origin Abyss)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Heavenbreaker Ape ★ | Legendary | Heavenly power | +205% |
| Voidscale Hydra ★ | Mythical | Void | +340% |

**Primordial Abyss Egg (Origin Abyss)**

| Pet | Rarity | Theme | Qi bonus |
|---|---|---|---|
| Abyss Anomalocaris ★ | Legendary | Primordial seas | +230% |
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
- **Twelve realms:** each has its own layers, matched to the rank's `Realm` name. The sub-rank (`Level` 1–5) moves it along one continuous level, so a breakthrough never looks weaker.
- **Colours (the owner's set, November 11, 2026: "Don't repeat same color to aura"):** no two realms alike, each a gradient from a hot colour to a deep one, in `src/shared/AuraConfig.lua` (`Palette`):

  | Realm | Colour |
  |---|---|
  | Qi Awakening | jade green |
  | Qi Foundation | teal |
  | Spirit Core | gold |
  | Spirit Soul | royal blue |
  | Ascendant Realm | solar orange |
  | Immortal Realm | silver-white |
  | Divine Realm | crimson |
  | Cosmic Realm | violet |
  | Void Realm | ice blue round a black core |
  | Heavenly Dao | rose pink |
  | Primordial Realm | lava: an orange core, dark red, black edges |
  | Eternal Transcendence | prismatic: gold, cyan, magenta |

- **On every realm, the owner's base aura** (built by the owner on dummy 1 of `Workspace.AuraDummies`, November 11, 2026: "apply that aura to all realms ... The higher the realm, the bigger the effects"):
  - **On the ground:** a burst, a smoke spreading outward, a slash and a crescent turning. Each but the burst is a light layer over a half-strength black copy of itself.
  - **A wisp** rising from the feet past the head, narrowing to a point, and **sparkles** rising from a ring round the feet.
  - **A soft glow** over the body (none round a void core), and from Ascendant on, the breathing outline and PointLight.
  - **Scale:** the dummy's look is Ascendant's base. Sizes and reach run from 0.6 times that at Qi Awakening to 1.8 times at Eternal's Peak. The ground layers' count barely grows and they dim as they grow, so a high realm's core never burns white.
- **On every realm, the owner's body aura:** smoke, a dark shadow, sparks and star glints, fainter at low Qi and bigger at high Qi.
- **Each realm's unique piece** (the owner, November 11, 2026: "add each realm a unique particle emitter, trails or beam", built in Studio as instances, no code): a Model per realm in `ReplicatedStorage.AuraMeshes.RealmUnique` (`Tier01` to `Tier12`, pivot where the root stands), copied onto the player by `RealmAura`. Edit them there in Studio.

  | Realm | Unique piece |
  |---|---|
  | Qi Awakening | First Breath: jade motes drawn in toward the body |
  | Qi Foundation | Meridian Current: flowing teal currents round the waist and chest |
  | Spirit Core | Core Pulse: a golden shell swelling out from the chest |
  | Spirit Soul | Soul Flames: blue flames on both shoulders (the owner's FireFB16 flipbook) |
  | Ascendant Realm | Ascending Gale: white-gold wind streaks rushing upward |
  | Immortal Realm | Heaven's Light: three pillars of light falling from the sky |
  | Divine Realm | Divine Lightning: split-second crimson bolts round the body |
  | Cosmic Realm | Star Drift: violet stars drifting and twinkling |
  | Void Realm | Void Pull: dark shards and ice streaks sucked inward |
  | Heavenly Dao | Radiant Rays: a fan of rose light rays behind the back |
  | Primordial Realm | Magma Rise: magma chunks thrown up and falling back (stays on the floor) |
  | Eternal Transcendence | Aurora Veil: gold, cyan and violet curtains overhead |

- **Ribbons** (from Ascendant: more of them, larger and quicker with the level; the owner's look, November 11, 2026: their flipbook 98818011129942): thin, sharp, glowing swooshes whipping round the body. Each swoosh is a particle playing the owner's 8x8 flipbook of one stroke circling once. It lies round the body at a small random tilt, so it rings the body in 3D and the body hides its back half. A softer, wider copy behind it is its glow. The realm's hot colour fades to its main colour.
- **Floating poses:** the meditation poses move the body, not the root, and from Ascendant up the body floats. The body glow, the outline's light, the void core and the unique piece follow the hips' shift from rest each frame (players' rigs join with AnimationConstraints, the test dummies with Motor6Ds; both are read). Ground layers stay on the floor.
- **Only particles, beams and trails** (the owner, November 11, 2026: "Remove all the magic circle for all realms", "Remove the hard objects on the aura"). There are no ground circles and no meshes. The sigils, Realm 4's Soul Seal, the signature meshes (crown, orrery, shards, coils) and the top two realms' rigs are gone, along with their mesh templates. The only parts are invisible emitter hosts.
- **Rebuilds** happen on rank-up and respawn; the aura goes on death.
- **Culling:** other players' auras switch off past 120 studs from the camera. Roblox draws at most 31 Highlights per client.
- **One source of truth:** the Studio test range (`ServerStorage.DevStage.AuraTestRange`; drag it to Workspace to use it) uses the same module, so a realm enhanced there is the realm the game shows.

**No pet auras** (removed November 11, 2026, before the public test): the per-pet aura layer (`CharacterAura`, `AuraBuilder`) never ran, because no pet had a design of its own after the old ones went (the Tidecaller Sanctum, Ember Crucible, the Aqua Wisp's droplets and the Golden Kirin's leaves, 2026-11-09; the owner dropped their replacements, 2026-11-10). It was deleted with its flame-aura fallback. The realm aura is the cultivation look. `AuraStyles` keeps each pet's colours and the breakthrough settings, and `AuraKit` keeps the shared sequence helpers.

**Poses and breakthroughs**

- A flying pose while airborne, and each realm's own meditation idle while cultivating (below).
- A burst effect on every rank-up, bigger at milestones.

### The twelve meditation idles (the owner, November 4, 2026)

"Make 12 unique and different idle, there should be no similar or reuse idle", and "the beginner idle should be lotus sit". Each realm has its own (`client/Character/MeditationPoses.lua`, played by `PoseController`, easing in over 3 seconds). The pose places the body itself, on the ground or up on the air; the character's own height doesn't change, and a cultivator can't walk or jump (`MeditationStillness`).

| Realm | Idle |
|---|---|
| Qi Awakening | The lotus seat on the ground, hands on the knees, a slow deep breath |
| Qi Foundation | Standing post: knees soft, the arms rounded as if round a tree, sinking and rising |
| Spirit Core | Kneeling, the hands circling each other round the core at the belly, head bowed |
| Spirit Soul | The crane: on one leg, the knee drawn high, the arms spread low like wings |
| Ascendant Realm | Floating Ascension: reclined on the air, a wide wingspan, a knee to the sky |
| Immortal Realm | Standing on air: sword fingers at the chest, a hand behind the back, chin up |
| Divine Realm | On one knee in the air, an arm driven straight at the heavens |
| Cosmic Realm | Upside down, legs crossed above, the arms spread, orbiting slowly |
| Void Realm | Curled tight, knees to chest, tumbling end over end |
| Heavenly Dao | Cloud hands: a low stance, the hands passing in unbroken circles |
| Primordial Realm | Holding up the sky: a wide squat, both palms pressing up, the strain trembling through the body |
| Eternal Transcendence | Spread as a star, face to the sky, turning high up |

Every account, the owner's too, takes its realm's idle (the owner's own aura and fixed pose were removed on November 11, 2026, before the public test: "remove my character aura, and let me use our game aura"). To review any idle on any account, set `MeditationPoses.Preview` to its realm number. Tested in Play: all twelve run with no errors, planted feet stay flat within 0.07 studs of the floor, and walking and jumping return on stopping.

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

Fifteen eggs, **three on each of the five outer islands** (none on Yggdrasil, the hub), each needing a higher rank than the last.

- **Hatching** (since November 2, 2026, section 7): only at Yggdrasil's **Hatching Altar**, from the player's **egg inventory** (`EggInventory`, saved as `Eggs`, at most 99 of each), filled by carrying eggs home from the guardians' stands. The stands no longer hatch; their prompt is "Take". (Before: free stand hatches with a 45-second cooldown.)
- **Three separate numbers** (`GameConfig`; the owner's request, November 5, 2026): a pet's **Rarity** is its classification (colour, sell value, what's protected), its **QiBonus** what it adds to cultivation, and its **HatchChance** how likely one egg is to hatch it, set per egg in percent. None is worked out from another, so an egg can be balanced without changing what a rarity means. Each egg's chances must add up to 100, or the server refuses to start. `tools/balance_report.py` prints each egg's average Qi and any rarer pet that's the weaker.
- **Chances:** the usual scale is a starting point, not a rule: Common 45%, Uncommon 27%, Rare 15%, Epic 8%, Legendary 4%, Mythical 0.9%, Secret 0.1%.
- **The altar shows them:** each egg at the Hatching Altar opens to list everything it can hatch, with each pet's rarity and its exact chance. A beast not yet in the player's Codex stays a silhouette named "???", marked New (the owner's choice); the others show their name, Qi bonus and how many the player holds.
- **The hatch cinematic (November 10, 2026; brief approved by the owner: a horizontal reel, about 5 s; `HatchCeremony`):** the server picks the beast and lays the egg in the cradle; the hatcher sees five beats. (1) Letterbox bars close in, the HUD steps aside, the world dims and greys a little, and the camera glides round to the egg. (2) The egg rises, turns and shivers harder while a reel of the egg's beasts races past a gold marker and slows (ease-out quint over the 3.8 s `HatchingAltar.Stage`), ticking as each card passes. The cards are drawn at the egg's real odds (the player's lucky odds with the Luck pass), and undiscovered beasts are silhouettes. (3) As it slows, the marker and the egg's glow take the winner's rarity colour: rarity first, beast second. (4) It lands as the egg cracks, in a burst that grows with rarity: a flash and sparks; from Rare a ground shockwave and rays of light; from Legendary a screen flash, a camera shake and a banner (LEGENDARY!, MYTHICAL!, SECRET!); a Secret has a beat of darkness first. (5) A reveal card: the beast turning in a sunburst of its rarity colour, its name, rarity, chance and Qi, and NEW or Duplicate. A tap skips to the crack, then dismisses the card (it closes by itself after 2.2 s). Reduced Effects drops the shake, the flashes and most particles. The roll never stages near misses: it only shows the odds.
- **Luck pass and Roblox's paid random items policy:** a luck boost counts as a paid odds modifier, so the Shop's ODDS panel shows every egg's chances by rarity without and with it, before purchase. The altar shows the owner's live lucky odds, and players where PolicyService `ArePaidRandomItemsRestricted` is true see "Not available here" and can't buy it. Earned eggs themselves need no disclosure, but the altar shows their odds anyway.
- **Missing rarities:** when an egg has no pet of some rarity, its share goes to the next pet that has one. So later eggs give rarer pets far more often.
- **Inferno and Phoenix Ash, rebalanced (the owner's decision, November 5, 2026):** the Inferno Egg gave half its hatches to Ember Wyrm with nothing Rare or Epic, and the Phoenix Ash Egg 87% Magma Cub or Ember Wyrm with its Epic better than its Legendary, so both paid less Qi on average than the eggs before them. They now follow the scale, at about +26% and +35%, and within each egg a rarer pet is never the weaker one.

| Island | Egg | Needs | Chances |
|---|---|---|---|
| Beginner Isle | Beginner Qi Egg | Qi Initiate | Aqua Wisp 45%, Ember Wyrm 27%, Lunar Hopper 15%, Volt Fox 8%, Golden Kirin 4%, Astral Whale 0.9%, Origin Serpent 0.1% |
| Beginner Isle | Spirit Breeze Egg | Qi Adept | Wind Sprite 45%, Cloud Sheep 27%, Spirit Crane 15%, Azure Sky Dragon 8%, Stormhorn Kirin 5% |
| Beginner Isle | Elemental Core Egg | Foundation Initiate | Glacier Puff 45%, Storm Bumblebee 27%, Crystal Beetle 15%, Gravity Imp 8%, Thunderclaw Drake 4%, Frostfang Serpent 1% |
| Jade Grove | Jade Spirit Egg | Qi Gatherer | Moss Golem 45%, Mycelium Sprite 27%, Jade Spirit Panda 15%, Jade Antler Deer 8%, Golden Kirin 5% |
| Jade Grove | Bloomwood Egg | Foundation Adept | Dream Moth 45%, Crystal Snail 27%, Prism Armadillo 15%, Lantern Warden 8%, Jade Wyrm Turtle 5% |
| Jade Grove | Ancient Grove Egg | Core Initiate | Echo Bat 45%, Qi Clockwork Finch 27%, Moonfang Tiger 15%, Thousand-Eyed Guardian 8%, Ninefold Spirit Serpent 4%, Worldroot Colossus 1% |
| Ember Peak | Inferno Egg | Qi Awakener | Magma Cub 45%, Ember Wyrm 27%, Obsidian Guardian 15%, Azure Sky Dragon 8%, Sunscale Dragon 2.5%, Dawn Phoenix 2.5% |
| Ember Peak | Magma Heart Egg | Perfect Foundation | Sand Phantom 45%, Solar Butterfly 27%, Obsidian Guardian 15%, Golden Mane Lion 8%, Bonefire Dragon 5% |
| Ember Peak | Phoenix Ash Egg | Core Adept | Sand Phantom 45%, Solar Butterfly 27%, Obsidian Guardian 15%, Dreadfang Cerberus 8%, Bonefire Dragon 4%, Prismatic Phoenix 1% |
| Moonlit Isle | Celestial Egg | Soul Awakening | Starfall Fox 45%, Cosmic Jellyfish 27%, Nebula Owl 15%, Celestial Snow Leopard 8%, Comet Stag 4%, Celestial Pearl Dragon 1% |
| Moonlit Isle | Astral Sanctum Egg | Ascendant Initiate | Starfall Fox 45%, Cosmic Jellyfish 27%, Nebula Owl 15%, Eclipse Cat 8%, Timekeeper Tortoise 4%, Galaxy Manta 1% |
| Moonlit Isle | Heavenly Throne Egg | Lesser Immortal | Celestial Snow Leopard 47.5%, Eclipse Cat 47.5%, Comet Stag 2%, Timekeeper Tortoise 2%, Celestial Pearl Dragon 0.5%, Galaxy Manta 0.5% |
| Origin Abyss | Forbidden Origin Egg | Divine Initiate | Shadowcoil 87%, Eclipse Cat 8%, Rune Sphinx 4%, Thousand-Year Dream Eater 0.9%, The Nameless One 0.1% |
| Origin Abyss | Void Rift Egg | Void Walker | Shadowcoil 87%, Eclipse Cat 8%, Heavenbreaker Ape 4%, Voidscale Hydra 0.9%, The Nameless One 0.1% |
| Origin Abyss | Primordial Abyss Egg | Primordial Awakening | Heavenbreaker Ape 60%, Abyss Anomalocaris 39%, Voidscale Hydra 0.45%, Thousand-Year Dream Eater 0.45%, Eternal Clockwork Dragon 0.05%, The Nameless One 0.05% |

### Egg designs

- **Source:** the 15-egg concept sheet. The designs in the table below were the first generation; its scripts and exports were removed from the project on November 5, 2026 and remain in git history. Eggs are modelled in Blender by a script (second generation, below; shared helpers in `egg_kit.py`) and exported to `assets/eggs/<EggId>.fbx`. An export holds an `<EggId>_Body` mesh coloured by an atlas (`<EggId>_atlas.png`) and `<EggId>_Glow_<hex>` parts, which become Neon in that colour.
- **Detailed eggs, built like the sculpted pets:**
  - High-detail pieces with procedural Cycles shaders (`egg_hi.py`): knotted bark with grain, veined leaves, marbled jade, gold-veined crystal, carved wood planks, leafy crowns.
  - Baked by `egg_bake.py` onto one game mesh of about 14,000 triangles, with `<EggId>_color.png` (ambient occlusion included), `_normal.png`, `_roughness.png` and `_metalness.png`.
  - Studio's importer turns the colour and normal maps into a SurfaceAppearance. Roughness and metalness are set on it in Studio.
  - Glowing parts stay separate Neon pieces, and every open glow piece is wound to face outward, because Roblox culls back faces.
  - Gold is 0.6 metallic, not 1: fully metallic gold shows black wherever it has nothing bright to reflect.
  - The shaders' ambient occlusion is local to each piece. While baking, the game mesh lies on the high-detail surface, and a scene-wide AO sees it everywhere: the whole egg then bakes as one deep crevice (too dark, or red-hot on the lava shaders).
- **In Studio:** an imported egg is stored with `WorldBuilder.storeEgg(model, eggId)` in `ServerStorage.EggMeshes.<EggId>`. `buildEggStands` places it at `GameConfig.EggStudsPerUnit` (1.3) studs per egg unit; the server's stand eggs and the auras use the same value.
- **All fifteen eggs are recreated.** The Moonlit Isle and Origin Abyss eggs are their own designs (November 1, 2026): the owner asked for each to be invented after its name, not the sheet's family designs.

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

**Second generation (in the game since November 4, 2026):** all 15 eggs rebuilt, each with its own idea written at the top of its script, reviewed and passed by the owner on a flat board. Scripts: `tools/blender/eggs/egg_forge.py` and `v2_<island>.py`. Output: `assets/eggs/` (the first generation's meshes stay in `ServerStorage.DevStage.EggMeshesV1`). Magma Heart ("fresh from the forge"), Astral Sanctum ("the astrolabe") and Heavenly Throne ("the sky itself") are **just an egg**, the whole idea on the shell, on the owner's word; they replace those three eggs' earlier designs in the table above. Magma Heart has no Neon part. `File > Import 3D` reads all four maps from these FBX files.

### Egg effects

**Only a Highlight and bloom, no aura and no smoke** (the owner, November 4, 2026: "just add highlight and bloomeffects for eggs, no need for aura or smoke"). Nothing may hide the egg. The aura system (`EggAuraVFX`, `EggAura.client`, the `EggAuras` folders) was removed the same day; it is in git history before that date if it is ever wanted.

- **`src/client/World/EggGlow.client.lua`:** every egg, on a stand, carried, dropped or hatching, is a part tagged `GameConfig.EggGlowTag` (the server tags them: `EggModel`, `EggStands`). The client gives the nearest ones a Highlight in the egg's colour (`GameConfig.EggGlow`): a clear outline and a very faint fill, so the baked detail stays. At most 8 within 140 studs, on a phone 4 within 90.
- **Bloom:** one `EggBloom` effect rises to 0.3 as the camera comes within 25 to 70 studs of an egg. It lights the whole screen, not only the egg, so it stays gentle (threshold 0.97; at 0.75 it washed out the grass). Reduced Effects turns it off.
- **Stands** keep their glow ring and PointLight. `EggRest` is where an egg rests on a stand.

## 6. World

Six floating islands built from original Blender work: terrain tops, sculpted undersides, landmarks and set pieces. **Yggdrasil** is the hub at the centre, about 500 studs across (three times the others), and a bridge leaves it for each other island. The **Beginner Isle** (November 4, 2026) lies just west of it, on a short bridge open from the start, so from the hub the islands run left to right in realm order: Beginner Isle, Jade Grove, Ember Peak, Moonlit Isle, Origin Abyss (the owner).

**Layout** (since November 1, 2026, the owner's map; `tools/blender/world/layout.py` is the one source):
- Every island's ground is at Y 200. The four outer islands fan out north of Yggdrasil, west to east in unlock order, and the harder an island, the farther it stands (the owner's rule, November 2, 2026): each bridge takes about four seconds longer to run than the last at its unlock rank's run speed. Each island is turned by quarter turns so its gate faces the hub (terrain grids stay exact; `Turns` in the terrain data, `WorldBuilder.islandFrame` and `WorldConfig.frame` carry island-local positions into the world).
- Yggdrasil replaced the Starting Island, which carried its content over: the Qi Spring, the Root of the Island and all its kit pieces (stored in Studio as `WorldKit.Yggdrasil`).

**Bridges:**
- Paths in `layout.py` (`BRIDGES`; `--write` generates `src/worldbuild/Placements/Bridges.lua`), built by `WorldBuilder.buildBridges()` into `FloatingIslands.Bridges`. They fan out from Yggdrasil's north rim as on the owner's map, each one straight span from Yggdrasil's ground to just inside its island's gate (no landings: the owner's call). Level, with a gentle arch (at most about 6°): Jade 191 studs, Ember 314, Moonlit 461, Origin 649, about 8, 12, 16 and 20 seconds to run at each unlock rank's speed (24 to 32 studs/s); the sword flies the last two in about 10.
- A deck 40 studs wide (doubled twice at the owner's request; room to ride the sword along it) with rails. Both ends are carried onto their islands by a solid abutment.
- At each bridge's start a gate holds a **Qi barrier** (tagged `QiBarrier`, with the destination's `RankId`): solid until the player reaches that rank, then open to them (`BridgeBarriers.client`). While sealed, each player sees a plain wall of transparent light in that gate's own colour with "Sealed / Reach <rank> to pass" (the owner: "just match the color of entrance with their realm level"; a swirling texture was tried and read as water); once they qualify the wall is gone for them. A player below the rank found on the bridge past the gate, or on the island it leads to, is put back in front of the gate (`WorldService`).
- Each bridge wears its island's kit, modelled in Blender (`tools/blender/world/bridge_kits.py` → `assets/world/Bridges/<Theme>Bridge.fbx`, piece offsets in `Placements/BridgeKits.lua`), laid by `buildBridges` over the walkable blockout:
  - **Beginner Isle:** plain stone deck; at the hub's end a gate of two lacquered posts on stone drums under a tiled lintel with upswept ends, lower and plainer than the Lion Gate it leads to.
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
| Beginner Isle | (−480, 200, 24), 2.13292 | The outer court of a cultivation sect | None: the Stone Lion and the three Beginner eggs |
| Jade Grove | (−384, 200, −448), 0 | Ancient forest | Grove Heart, Jade Seed, Whispering Spring (800 Qi each, Qi Gatherer) |
| Ember Peak | (−128, 200, −696), 0 | Volcanic, lava pools | Ember Heart, Ashen Sigil, Caldera Crown (1,500 Qi each, Qi Awakener) |
| Moonlit Isle | (192, 200, −804), 0 | Pale and celestial | Moon Mirror, Star Well (20,000 Qi each, Soul Awakening) |
| Origin Abyss | (596, 200, −856), 0 | Hidden endgame: dark slate, void crystals and rifts, broken ruins | Origin Altar (250K Qi, Divine Initiate); the Void Shard high above it (1M Qi, Void Walker) |

**Bridge gates:** the Beginner Isle at Qi Initiate (open to all), Jade Grove at Qi Gatherer, Ember Peak at Qi Awakener, Moonlit Isle at Soul Awakening, Origin Abyss at Divine Initiate. Moonlit's gate rose from Foundation Initiate on November 4, 2026 (the owner's decision): it opened about 90 minutes before the island's first egg and a guardian tuned for Soul Awakening could be used.

**Shared rules**

- **Relics:** each Spirit Relic gives a one-time Qi reward, and finds are saved.
- **Qi Spring:** the spring on Yggdrasil adds +50% Qi while cultivating in it.
- **Falling:** a player who falls 110 studs below the island they last stood on is returned to that island's checkpoint (on Yggdrasil, to their spawn slot). That line sits under the Root of the Island's cradle (86.5 down, the deepest place players stand) and above the PDS kit under Yggdrasil (its top 130.5 down), so a fall never strands anyone on the kit.
- **Hazards:** parts tagged `LavaHazard` (Ember Peak's lava) also return a player to their island's checkpoint on touch.

### Yggdrasil (built; its own meshes await import)

**Paved, November 5, 2026 (the owner: the same upgrade as the outer islands; `island_upgrades.py`):** the paths are roads now, flagstones in a dark kerb that follow the ground (`YG_Roads`), with paved rounds at the bridges (`YG_Bridgeheads`), a band round each plot (`YG_PlotEdges`) and a ring round the Qi Compass (`YG_CompassRing`). None of them collide. The old Egg Garden and lion lair are gone from the terrain, the land round the Hatching Altar is level, the Spawn Walk's east end stops at a grove, and the trees, rocks and flowers are thinned and kept off the roads. Terrain grass grows up through a mesh laid on it, so everything under paving is Ground or Cobblestone. Walked in Play along the roads to the shops, the altar, the bridges and the Spring; the scan reaches 11,029 of 11,650 floor cells, the rest being inside the great roots and past the bridges' barriers.

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
- **East:** the **Qi Spring** on the rim, its waterfall pouring off the edge (the Starting Island's spring, carried over whole), The Egg Garden and the Stone Lion's lair stood here until November 4, 2026 (the owner: "there should be no boss in the main hub"); no guardian and no egg stands are on the hub now.
- **West, past the Market lane:** the road and waystone to the Beginner Isle's bridge, through the gap between the Blacksmith and the Marketplace.
- **North:** a paved bridgehead and a waystone for each bridge.
- **Underside:** the Starting Island's stacked strata at Yggdrasil's scale, gripped by roots that climb out of the meadow, over the rim and down the strata to a taproot. Its lowest point stays above world Y 75: the PDS kit lies below.
- **Root of the Island:** from the south rim the great root winds down the cliffs, sixteen bracket-fungus shelves along it, to a bowl of roots under the strata holding the relic.
- **Nature:** spirit pines crowning low knolls near the rim, plum blossoms, mossy rocks and flowers.

### Beginner Isle (the owner, November 4, 2026)

**Its layout kept, its edges made crisp, November 5, 2026 (`island_upgrades.py`):** a paved apron round the court's kerb to radius 67.5 (`BI_CourtApron`), paved roads to the gate, the Hall, the bell and the pavilion (`BI_Roads`), and a floor for the training yard (`BI_YardFloor`). The court's jade ring and bronze paw had been built facing down and never shown; they show now. The pavilion's road stops at the foot of its knoll, and eight stone steps (`BI_PavilionSteps`) climb from there to its front step between stepped dark walls, a bronze-capped post each side at the foot. Walked in Play from the bridge to every one of them; up and down the steps without a jump, and on the grass beside them.

"Create the beginner island so you can transfer the eggs there, and there should be no boss in the main hub." The first island a new player crosses to, in the first ten minutes: the outer court of a cultivation sect. Scripts: `beginner_island.py` (terrain and layout), `beginner_meshes.py` (underside), `beginner_props.py` (kit and placements). About 280 studs across. It shares Yggdrasil's terrain materials (Grass, Ground, Rock, Cobblestone).

- **The route:** the Market lane → a 118-stud Lion-themed bridge (`BeginnerRoute`) → the Lion Gate → a cobbled path → the Lion Court, all on one straight line through the island's centre (the owner: "don't tilt the island"). That takes a turn that isn't a whole number of quarter turns (`Turns` 2.13292), so its terrain is sampled turned and written straight onto the world's grid (`BakedTurn`).
- **The Lion Court:** cobblestone paving 52 studs in radius at the island's centre. The Stone Lion stands in the middle, facing the gate, its three stands (Beginner Qi, Spirit Breeze, Elemental Core) in an arc behind it at radius 31.
- **Round it:** a hall behind the court, a training yard with dummies, a weapon rack and lifting stones to the south, a pavilion and bell on a knoll to the north, spirit pines from Yggdrasil's kit.
- **Ground under the bridge:** cut a little below the abutment and bare (Ground, not Grass), so no terrain or grass blades come through the deck. Looking at this from far away, or in a capture whose camera only moved for a moment, coarse distant terrain can draw across the deck; it is gone once the camera is really there.

### Jade Grove (built; doubled November 2, 2026)

**The owner's upgrade** (November 2, 2026, for every outer island, Yggdrasil unchanged): twice the size; the boss in the middle of the island guarding its three eggs; no obstacle in the middle, props round the sides; the bridges as they are. Jade Grove was rebuilt first for review. It is about 300 studs across, and moved out along its unchanged bridge (the bridge file regenerates byte-identical); the other islands fan apart the same way when they double (planned: each one's centre on its bridge's line, about its new radius past the bridge end; all four then clear each other by 45 studs or more).

- **Mantis Arena** (the middle): a dead-level ring of grass bordered by jade flagstones (radius 50), a path ringing it. The **Bamboo Mantis Sage**'s lair is its centre, facing the Grove Gate; the **three egg stands** (Jade Spirit, Bloomwood, Ancient Grove) stand in an arc 31 studs behind it, just past its engage radius. Nothing solid stands in it; jade lanterns and standing stones ring its edge between the paths. **Since November 5, 2026** (the owner: keep the arena in the middle and the eggs, improve the rest to the Beginner Isle's standard) it is paved: `JG_ArenaFloor`, ring on ring of worn stone with jade slabs among them, a jade kerb and a jade-and-gold star at the centre.
- **Grove Gate** and the arrival terrace on the south-east rim, where the Jade bridge lands; a path leads straight into the arena.
- **Elder Jade Tree** to the north-east (Grove Heart in its hollow, Jade Seed in its crown, the fungus-shelf climb).
- **Whispering Hollow** to the north-west (the spring pool and the Whispering Spring).
- **Bloom Glade** to the south-west: the flagstone sanctuary ringed by standing stones, opening toward the arena. (A stolen egg is now carried home to Yggdrasil, not here.)
- **The Sage's Hermitage** (`JG_Hermitage`, November 5, 2026) behind the eggs, on the line from the gate through the arena (radius 82), on its own level pad: a bamboo hut on stilts under a double roof of living leaves, open toward the arena, with stone steps and a low shrine inside. You can walk in.
- **Ruin Court** to the south: broken pillars round a clearing.
- **Forest** ringing everything: six groves of ancient trees and bamboo round the rim (thinned out and gathered on November 5, 2026: 30 trees in groves instead of 46 scattered), so the way in and the view across the arena stay open; jade outcrops, ruin pillars, fallen logs, ferns and glowing mushrooms between them.
- **Underside:** the faceted dark-jade mass, deeper (130 studs) with larger hanging jade crystals, moss curtains and vines round the longer rim.
- **Tested in Play:** walked from the bridge into the arena (3 s); the Sage woke at its engage radius, its attacks knocked back without throwing anyone off; weakened in 14 strikes; the egg stolen, the Sage leapt after the thief, and the egg was secured in the Bloom Glade after a 5.6 s run (it dropped its relic: Wind unlocked).

### Ember Peak (built; doubled November 2, 2026)

Columnar basalt is the island's signature, used for the cliffs, the climb, the altar and the underside. Doubled for the owner's upgrade like Jade Grove: about 300 studs across, moved out along its unchanged bridge.

- **Cinder Arena** (the middle): a dead-level basalt ring bordered by glowing cracked lava rock (radius 50), a path ringing it, braziers and basalt column clusters round its edge. Its centre is kept for Ember Peak's guardian (the Fire Guardian, still to design). At its back, the **Phoenix Altar**: three cinnabar-topped column pedestals, each on a pad of hexagonal basalt, holding the Inferno, Phoenix Ash (tallest, in the middle) and Magma Heart eggs. **Since November 5, 2026** it has a floor (`EP_ArenaFloor`, `EP_ArenaGlow`): hexagonal column tops with lava glowing in the seams, an obsidian kerb, a broken channel of fire outside it, a cinnabar sun at the centre. Four **fire pylons** (`EP_FirePylon`, `EP_PylonFire`) hold fire high at its corners, either side of the way in and of the volcano.
- **Ember Gate:** the arrival on the south rim, two bundles of basalt columns with iron fire braziers under an obsidian lintel with a cinnabar plaque; braziers inside it; the path runs straight into the arena.
- **The volcano** (north, looming behind the eggs):
  - a crown of basalt columns rings its crater;
  - inside, a lava lake holds the **Caldera Crown** on a basalt pillar;
  - six basalt column steps climb its arena-facing flank as the Qinggong route to the rim.
- **Lava river:** it overflows a notch in the rim, runs down a carved channel to the north-west edge and pours off the island as a lavafall. Touching the lake or the river returns the player to Ember Peak's checkpoint.
- **Ember Forge** (east): ruined walls of stacked basalt blocks with a sooty chimney and anvils. The **Ember Heart** hovers over a hearth of glowing coals.
- **Ash Plain** (west): petrified trees around a cracked obsidian monolith carved with the glowing **Ashen Sigil**.
- **Underside:** hanging hexagonal basalt columns, like organ pipes (wider and deeper at the new size), with a magma core glowing through the gaps.
- **Dressing:** fire crystals, ember vents throwing sparks, basalt clusters and obsidian shards, all round the arena, thinned out on November 5, 2026 so each can be seen.
- **Tested in Play:** from the bridge to the egg pedestals in 5 s, the prompt in reach; the lava river returns the player to the new checkpoint.

### Moonlit Isle (built; doubled November 2, 2026)

Seen from above, the island is a crescent moon: a full disc (about 250 studs across since the owner's upgrade) with a deep bay of sky cut out of its north, its horns curling around it. Moved out along its unchanged bridge.

- **Lunar Court** (the middle, a little south of the disc's centre): a level ring of moon paving bordered in salt-white stone (radius 50), ringed by hovering star lanterns along its path. Its centre is kept for Moonlit Isle's guardian (the Celestial Guardian, still to design). At its back, looking out over the bay, the three porcelain egg pedestals (a wide blue dish with gold bands at the lip and foot) hold the Celestial, Astral Sanctum and Heavenly Throne eggs. **Since November 5, 2026** it is a moon dial (`MI_ArenaFloor`): pale marble inside, a band of the night sky holding the eight phases of the moon, gold rings and a gold star at the centre. The eggs' glow rings stand 0.2 higher here (`RingLift`) to clear it.
- **Arrival:** the bridge lands on the south rim through the gold Crescent Arch; the path runs straight to the court.
- **The Moon Gate** (`MI_MoonGate`, November 5, 2026) on the lip of the bay behind the eggs, on the line from the arch through the lair: a great ring of blue porcelain and gold on a stepped dais, framing the open sky, a crescent on its crown. You can climb the dais and stand under it.
- **Moon Mirror** (west): a dark reflective pool you can walk on, in a marble-and-gold rim. A curved bridge leads from its court-side bank to a moonstone lotus holding the **Moon Mirror** relic.
- **Star Well** (west horn): a marble well with a gold lip, brimming with glowing starlight, with the **Star Well** relic above it.
- **Celestial Pavilion** (east horn): eight porcelain pillars with gold crescent finials on a stepped marble platform, under a floating golden armillary (the eggs stood here before the upgrade).
- **Underside and cliffs:** marble cliffs with a gold band under the lip step inward into a belt of soft cloud, deeper at the new size. Moonstone geode crystals hang beneath, some of them glowing.
- **Dressing:** hovering porcelain star lanterns along every path, frost lilies in drifts, spires standing round the court like the hours of a dial, moonstone shards and lunar rocks (thinned out on November 5, 2026).
- **Tested in Play:** from the bridge to the egg pedestals in 4 s, the prompt in reach; across the Moon Mirror's bridge to its relic; a step into the bay returns the player to the checkpoint.

### Origin Abyss (built; doubled November 2, 2026)

The hidden endgame island, about 320 studs across since the owner's upgrade, moved out along its unchanged bridge. A void rift tears a chord across its far side; the court's side is level and open, the shelf beyond the rift raised and tilting up toward its far edge.

- **Void Court** (the middle): a level court of worn temple stone bordered by void-crystal crust (radius 50). Its centre is kept for Origin Abyss's guardian (the Primordial Guardian, still to design). At its back, the **egg plinths**: three obsidian plinths cracked with void light, each cradled by thorny bronze branches and set on a pad of hewn paving, holding the Forbidden Origin, Void Rift and Primordial Abyss eggs; each stand glows in its egg's own colour. The **Thorn Crown**, seven great bronze branches (one snapped) rooted on the court's rim behind them, hooks up and inward over them. **Since November 5, 2026** it has a broken temple floor (`OA_ArenaFloor`, `OA_ArenaGlow`): rings of worn slabs, void light in the cracks running out from a spiral at the centre, a kerb of dark crystal. **What is left of a colonnade** (`OA_Colonnade`) rounds its flanks at radius 70: some columns whole, runs of them still carrying their stone, the rest broken at different heights, open on the gate's side and at the back. You can walk between them.
- **Gate of Descent** on the south-west rim, where the bridge lands: two carved pillars, one snapped, the lintel fallen onto the stump. A ruined avenue lined with snapped columns and fallen drums leads from it to the court.
- **Fallen colossus** (west of the court): a giant carved stone head sunk into the ground, its face turned toward the path to it, void light in its eyes and through a crack across its face.
- **The Rift** (behind the eggs): it pinches and gapes along a chord across the far side, open sky through it; it never comes within 82 studs of the court's centre. An **ancient broken bridge** crosses it where it narrows (pinched for it), its middle fallen away but for one hanging block: a run and a jump.
- **Origin Altar** (on the shelf): a ring of nine leaning obsidian slabs carved with glowing seal-script glyphs (one snapped, its top fallen outside the ring) around a stepped dais with a glowing spiral sigil; a gap in the ring faces the path from the bridge. The **Origin Altar** relic floats above it.
- **Void Shard:** a great obsidian-glass crystal with a glowing core, chained to a floating temple floor about 150 studs above the altar. Floating temple fragments climb to it, each rising 49 studs, so Void Walker clears every stage and Divine Initiate falls short. The **Void Shard** relic floats on the top floor.
- **Underside:** separate angular chunks (broader and deeper at the new size) with gaps between them, void light glowing through from a great lobe under the court and a smaller one under the shelf. Iron chains bind the halves beneath the rift, a glowing veil hangs deep in it, and broken-off debris drifts below.
- **Dressing:** void crystals of dark glass around glowing cores (many along the rift's lips, with rising motes), in patches on the open ground as if the void were coming up through it (November 5, 2026), and slate rocks.
- **Tested in Play:** from the bridge to the egg plinths in 5 s, the prompt in reach; across the broken bridge with a jump; from the shelf to the altar, its prompt in reach (after the ring was turned to open toward the path); a fall into the rift returns the player to the checkpoint.

- **Tested in Play (November 5, 2026), all four islands:** walked from the gate to the arena's centre and to every egg stand; into the Hermitage, onto the Moon Gate's dais and through the colonnade on both sides; over Origin's broken bridge with one jump at walking speed 16; the lava river still returns a player to the checkpoint; guardians wake and hold their ground. Passability scan (real collision, 4-stud grid, gate to lair): each island has a clear route, every stand within 8 studs of walkable ground. A guardian chasing a thief across the new floors was not tested, as it means stealing a real egg.

### How islands are built

- **Blender scripts:** `tools/blender/world/` holds the layout and route checks (`layout.py`) and per-island scripts. Each script authors the terrain heightfield, the meshes, the texture atlas and the placements.
- **Exports:** the scripts write FBX files to `assets/world/<Island>/` and data modules to `src/worldbuild/`.
- **Assembly:** `src/worldbuild/WorldBuilder.lua` builds each island in Studio, under `Workspace.FloatingIslands.<Island>`, and the result is saved in the place. The steps are listed at the top of that file.
- **Terrain:** each island uses its own terrain materials, because terrain colours are global to the place:
  - Yggdrasil and the Beginner Isle: Grass, Ground, Rock and Cobblestone (the Starting Island's).
  - Jade Grove: LeafyGrass, Mud and Sandstone.
  - Ember Peak: Basalt, CrackedLava, Asphalt (ash) and Sand (paths).
  - Moonlit Isle: Limestone, Snow (frost), Salt (paths) and Pavement.
  - Origin Abyss: Slate, Concrete (paths) and Glacier (void-crystal crust). Brick is not used: Studio snaps Brick terrain to the 4-stud voxel grid, so paving is built from meshes. Sand also lies under the court's floor, out of sight.
  - **Under a mesh floor, use a terrain material that renders level at its height.** Basalt, CrackedLava and Glacier render about a stud of bumps, which come through a floor; Concrete snaps to the voxel grid as Brick does. Sand, LeafyGrass and Pavement stay level. And never leave Grass under any mesh: its blades grow up through it.
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
- **Home is Yggdrasil:** the egg is secured the moment the thief sets foot on the hub, across the island's bridge (`SafeZone = { Island = "Yggdrasil" }`; the waypoint is the bridge's hub end). The guardian can't follow off its island. The Stone Lion's eggs are on the Beginner Isle (November 4, 2026), so its thief too carries the egg home over a bridge.
- **The stands:** a dropped egg that times out goes back to its stand. A secured egg leaves the stand empty for 3 minutes (`EggTheft.RespawnTime`). Then the island's lowest-rank egg appears there unless another stand already shows it, so an island is never left with only eggs a new player can't take; otherwise a random one of its three eggs appears, so two stands may show the same egg. Each stand shows its egg's glow ring, light and aura (the auras are kept as templates; an aura names its stand by the attribute `Stand`).
- **Hatching** happens only at the **Hatching Altar** on Yggdrasil (`ygg_altar.py`, `WorldBuilder.buildAltar`, `GameConfig.HatchingAltar`, on the north-east lawn, east of the bridges): its prompt opens the hatching window (`HatcheryController`), which lists the eggs carried home with their counts; each Hatch lays the egg in the altar's cradle, where it rises, glows and breaks open in gold light (`HatchCeremony`) as the pet is named. The window sits at the screen's right edge so the cradle stays in sight. The cradle's pool is a deep amber (Neon 255, 110, 0, a little clear): a paler gold blooms to a flat lemon disc. The stands no longer hatch. Each egg rests `HatchingAltar.Stage` (2.6 s) in the cradle and the server takes one egg at a time per player. The Hatch button waits for the server's answer: until the egg breaks if it was accepted, at once if not, and every refusal says why and that the egg is safe (`NotAtAltar`, `HatchBusy`, `NoEgg`). The window closes 4 studs past the prompt's range, inside the server's limit. A new pet goes to the top of the Pets window with a NEW tag until the window is closed, because only about four cards fit and it could sort out of sight (the owner, November 5, 2026: "sometimes after hatching the pet don't show in the pet inventory"). The egg breaks at a server time sent with the result (`BreakAt`), so a late remote still breaks it before the server takes it away; the staged egg streams to everyone (Persistent).
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
- **Critical strikes** (the owner, November 11, 2026): a strike that lands has a 10% chance of striking 1.5 times as hard (`GameConfig.Combat.Crit`). The server rolls it; a client only shows it.
- **Output:** `ServerStorage.CombatHit` (a BindableEvent: player, target, damage, position) for the guardian code, and `CombatEvent` to every client for the effects: the striker, the kind of strike, and for one that landed where (on the target's near side, at the height of the striker's chest), its damage, whether it was critical and the target.
- **Effects** (`CombatFx`): the Qi Palm throws a great palm print of Qi (`QiPalm` texture) in the realm's colour.
- **Weapons are held in the hand** (the owner, November 4, 2026): welded to the right hand's grip, out for 5 seconds after the last strike, and put away on death or on starting to cultivate. A held weapon has a stance (`SwordReady`; for a spear a low stance, then its guard).
- **Sword, a combo of three:** a diagonal cut down across the body, a backhand rising the other way, an overhead finisher that shakes the striker's camera. Strikes within 1.1 seconds continue it (`WeaponKinds.Sword.ComboWindow`).
- **Spear, thrust then slash** (the owner: its slash "goes in different direction", its thrust "didn't make a good impression because it lasted a second"): held in both hands in the owner's stances. The thrust coils, lunges with a real step and holds its reach with the shaft humming (0.85 s). A strike within 1.7 seconds is one wide slash, right to left round the body.
- **Bare hands** (the owner, November 4, 2026: "add that punch animation, if the player avatar is not equipped with weapons"): a straight punch, right then left within 1.1 seconds, the hips first and the fist last, still with the Qi Palm's print, damage and cooldown.
- **Running stays Roblox's default run** (the owner, November 4, 2026). A keyed sprint with torn 2D edges on the limbs was tried after hovark_'s video and removed: "just revert it to the original running position, we will keep only the punch animation".
- **Both are keyed in Blender** (`tools/blender/animation`: `r15_rig.py`, `stances.py`, `weapon_moves.py`; the owner: "try to create in blender"): an exact copy of the game's R15 skeleton with two-bone IK, where the weapon itself is animated through space and the hands, arms, hips and feet follow. `M.export_all()` bakes 60 frames a second to `client/Character/WeaponClips.lua`, played by `PoseController`. Each clip carries the arc its tip truly drew, fitted when baked, so the crescent of light can't disagree with the weapon, and the sound and impact wait for the moment of the blow. Moving or airborne, the hips and legs stay out of it and the chest takes the hips' turn.
- **Carrying an egg takes both arms** (the owner, November 4, 2026: eggs used to ride on the head): it's welded before the chest with the arms round it (`CARRY_EGG`), the weapon is put away, and the carrier can't strike or cultivate.
- **A blow that lands is felt** (the owner, November 11, 2026: "Combat / Impact VFX ... Weapon VFX"; `CombatFx.hit`, `DamageNumbers`). Each layer says one thing, and the three kinds of blow look different:
  - **A cut** (a sword, a spear's slash): a line of light through the point along the blade's own path, and sharp sparks thrown the way it travelled.
  - **A pierce** (a spear's thrust): a ring punched out round the point, a lance of light driving in through it, sparks spraying back off it.
  - **A blunt blow** (bare hands): a broad ring, sparks all round and a puff of dust, under the Qi Palm's print.
  - **Every blow:** the target flashes (one Highlight, moved to whichever was struck); the striker's pose holds for an instant (hit-stop: 0.045 s, 0.07 s for the sword's finisher, 0.09 s for a critical strike); the striker's own camera kicks; and the striker's own strikes show their damage as a number that pops, rises and fades.
  - **A critical strike:** bigger, gold, crossed with a flare of light and a second ring, rung with an anvil's ding, its number gold with a "!".
  - **Sounds:** a blade's cut, a spear's thrust and a fist each have their own impact, and the spear its own swings (it used the sword's, pitched down).
  - Other players' blows on a phone, and all with Reduced Effects, throw fewer sparks; another player's blow on a phone doesn't flash the target. Numbers are only ever your own.
- **The weapon's light** (`CombatFx`): its trail is a soft sheet with a thin bright edge at the tip that sharpens to a point as it fades; the crescent of a slash draws on along the blade's path behind the blade, then swells and fades; the sword's finisher leaves its light longer and a second, paler crescent after the first.
- **Each clip's arc knows which way the blade went round it** (`weapon_moves.fit_crescent`): from the tip's own motion at the arc's middle. It was taken from the arc's two ends, which is backwards for a sweep of more than half a turn (the spear's slash) and was for the sword's backhand.
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
- **Planted feet** (`Rig.Legs`): after the springs, each standing leg's two joints are solved so its sole stays on the ground, so a body crouches, rears, bobs and shifts its weight over its feet instead of carrying them. A leg lifts out of it as its step swings it (`anim:lift`), in the air, or for a raised paw; no foot is ever posed through the ground. Measured fold directions: the Lion's four legs and Tiangou's forelegs fold on a positive lower turn, Tiangou's hind legs and Pangu's shins on a negative one; the Mantis's and Xuanwu's sprawling legs bend on roll (left positive, right negative). Awake guardians stand on slightly flexed legs, which planted feet need as slack. A leg with `Hop` (the mantis's) steps through the air when told to be somewhere else at once, when the body sets off or stops hard, a lock lets go or a swing begins far from its pose, instead of popping or skating across the ground.
- **Gaits measured in Play** (stance feet within about 0.1 stud of the ground, swing feet clear): the Lion 20 degree swing, 45 degree fold, body about 1.8 studs low; Tiangou 22, 50, 1.4; Pangu 22 degree stride, 55 degree knee, 1.4; the Xuanwu lifts each foot 26/18 degrees with the shell 0.6 low. Turning on the spot steps the feet too.
- **Weight and follow-through** (`Rig.Springs`): a joint eases into a move, overshoots a little and settles (bodies about 3-4.5 Hz, limbs 9 Hz). A loose joint (`Drag`) keeps its angle in the world while what it hangs from turns, then swings after it: tails (Tiangou's tip a beat behind its root), the Xuanwu's serpent, the Mantis's robe, Pangu's open arm, every head.
- **Lean** (`Rig.Lean`): nose down speeding up, back braking, banked into turns.
- **Tremors** (a shudder, a quivering roar, a building shiver) go on after the springs, which would smooth them away.
- **Cost:** 0.03-0.06 ms per guardian per frame in Studio, feet included; only guardians near the camera animate.

**Skinned guardians** (`rig.Skinned`, Tiangou first): the same layers drive `Bone.Transform` instead of Motor6Ds, written as `rest:Inverse() * T * rest` so a pose reads in the guardian's own axes. Signs: positive swings a hanging limb's far end forward and up, lowers the tail, lays an ear back and lifts the nose.

Tuning lives in each rig: `Rig.Springs`, `Rig.Lean`, `Rig.Legs`, the gait numbers and each move's keys. Joints are listed parent first (`GuardianAnim` warns otherwise). Strikes keep their impact on the wind-up time the server sends, so effects and knockback stay in sync.

### Guardians by island

| Island | Guardian | Encounter direction |
|---|---|---|
| Beginner Isle | The Awakened Stone Lion | Introductory fight, basic Qinggong escape |
| Jade Grove | The Bamboo Mantis Sage | Escape routes through trees and elevated terrain |
| Ember Peak | The Ember Xuanwu | Escape routes around lava and volcanic hazards; jump its quake rings |
| Moonlit Isle | Tiangou the Moon-Eater | More demanding aerial movement: long, low bounds that close the distance fast |
| Origin Abyss | Pangu the World-Splitter | The most demanding encounter: a fissure to dodge, a nova to jump, a titan's leap |


### The Awakened Stone Lion (Beginner Isle)

A real lion carved in weathered granite and come to life: a heavy mane of chiselled locks, glowing Qi-blue eyes, a gold collar with a jade orb and gold tassels, moss on its upward faces, and a long tail with a heavy tuft. It stands about 28 studs tall, in the Lion Court at the middle of the Beginner Isle, its egg stands behind it, facing the Lion Gate (`GameConfig.Guardians.StoneLion`).

**Its eyes and orb tell its state.** The eyes (rebuilt November 2, 2026 with `guardian_kit.eye`) are a temple lion's: bulging almond irises with dark cat pupils under carved stone lids set in a frown. Asleep, carved stone eyes (the pupil cut a shade darker) and a dull jade orb; awake, Neon Qi blue (`006eff`) and jade (`00a05f`), blinking every few seconds; weakened, flickering and wide; enraged, red-orange and wider still. Darker Neon renders as a flat black disc (the pupils use that), so the sleeping look is stone and glass, not dim Neon.

**The encounter** (`src/server/Guardians/Guardian.lua`; the server decides everything):

| State | What it does |
|---|---|
| Dormant | A statue, seated on its haunches. A player within 24 studs, or a strike, wakes it, and it rises for 2.6 s before its first blow (`AwakenTime`; other guardians 1.6). |
| Guardian | Stays at its lair. **Slam:** the left paw comes down in front (range 24, 55° arc, 0.75 s wind-up). **Roar:** a shockwave rolls out along the ground to 44 studs at 34 studs/s; whoever is on the ground when it passes is knocked back, and a jump clears it. |
| Weakened | Below 10% of 1,200 health (a beginner's Qi Palm gets there alone in about 108 strikes) its foreleg gives, it catches itself and holds the left paw off the ground; its attacks come 1.7 times slower; health never falls below 1. An egg can be taken from the Egg Garden's stands. |
| Enraged | The egg is taken: it chases the thief at 21 studs/s (a beginner runs 22) and pounces from 16 to 46 studs, aiming 0.85 of the thief's motion ahead, so a straight runner is caught and a thief who turns or dashes while it is in the air is not. It takes no damage. |
| Returning / Resting | It walks home. After a secured egg it sleeps for 30 s, then guards again. |

With nobody within 60 studs for 12 s, it heals and sleeps.

- **Never killed, never kills:** every blow is a knockback (about 19 studs, then off your feet for 1.1 s), and a knocked-back thief drops the egg.
- **Softer on the first two guardians (the owner, November 5, 2026):** the Stone Lion and the Mantis Sage throw weaker (Knockback 28, 26 and 34 where it was 45, 40 and 55), for 0.8 s off your feet, and can't knock the same player again for 4 s and 3.5 s (`KnockGrace`; 0.6 s on the others), so a beginner isn't walking back all fight. At Qi Gatherer with the starter sword: the Lion weakens in 41 s (7 knocks), the Sage in 72 s (15 knocks).
- **The egg a thief takes** is the one on the stand they take it from (their rank must open it), held over the thief's head.
- **Carried on foot:** no sword flight while carrying.
- **Grace:** for 1.5 s after taking or recovering the egg the thief can't be knocked back, so a blow already on its way doesn't take the egg straight back.
- **Dropped:** at a clear spot on the ground near where the thief was (never inside the lion), under a pillar of Qi light; only the thief sees its prompt and the 30-second countdown. A thief who leaves the game, or lets the countdown run out, sends the egg back to its stand. Falling off the island drops it where the thief last stood.
- **The Hatching Altar is its sanctuary:** the egg is secured within 12 studs of the altar's centre, the lion never comes within 12 studs of its edge, and nobody inside it can be knocked back.
- **The client** (`GuardianController`, `GuardianAnim`, `GuardianFx`): the health bar (name, state, the 10% weakened mark, a trailing loss), procedural animation (state poses, a walk turning into a gallop, breathing, the head turned toward its target, and the moves, all through springs: see How guardians move), stone-dust effects (the roar's rolling dust wall, slam and landing bursts, dust stirring where a pounce will land), camera shake, the way to the Hatching Altar for a thief, and the knockback on your own character.

**Rebuilt from nothing (November 5, 2026, the owner: "like a total change", "Make a more realistic animation"):** `tools/blender/guardians/stone_lion_v2.py` makes a lion in carved granite, not a temple dog: one skin on 39 bones, the mane one carving, the gold collar and jade orb a rigid piece on the neck, no egg. A foreleg is a shoulder blade, an upper arm, a forearm, a pastern and toes; a hind leg a thigh, a shin, a hock and toes (`rig.Legs` `Chain` carries the joints below the two solved ones). It sits as a statue until it wakes, rises, and shakes its mane; it walks in a lateral sequence with its head level, and gallops in a rotary gallop with its back gathering and stretching. `write_clips` generates `GuardianRigs/StoneLionClips.lua`, played by `GuardianRigs/StoneLionSkinned.lua`; `write_placement` writes `Placements/StoneLionSkinned.lua`. A move is solved every frame, so a planted paw doesn't leave its spot, and the tail is lifted just enough to stay above the ground; while it walks or runs, a landed paw is locked to its spot in the world until it lifts (`rig.Legs` `Lock`).

**Asset:** `assets/guardians/StoneLionV2.fbx` and its maps; `GuardianBuilder.storeSkinned` fits the import and sets the model's `Rig` attribute.

### The Bamboo Mantis Sage (Jade Grove)

A hermit sage who became the grove: a towering praying mantis of living jade bamboo, every segment a culm with pale waxy node rings, a robe of great dark leaves folded over its back, a carved jade face with faceted compound eyes and amber pupils, long drooping leaf brows and a leaf beard, a jade mala with a gold-tasselled guru bead, and jade scythes edged with glowing Qi, folded in prayer. About 37 studs tall, 53 long and 32 wide across its legs (`tools/blender/guardians/mantis_sage_v2.py`, rebuilt November 5, 2026 as one skinned model: 44 bones, painted weights).

**Its arms** are a real mantis's raptorial legs: a spined femur, a hinge at a deep knee lobe, a curved jade tibia with two rows of teeth and a hooked point, and a slim jointed foot with two tiny claws at the tibia's end. The robe grows from the top of the thorax and lies along its back, and opens like wings in rage and in the air.

Its lair is the middle of the Mantis Arena, its three egg stands behind it (moved there when the island was doubled); a thief carries its egg home to Yggdrasil (until November 2, 2026 the Bloom Glade was its safe zone). 2,000 health: a Qi Gatherer's palm weakens it (below 10%) alone in about 165 strikes.

| State | What it does |
|---|---|
| Dormant | Meditating: head bowed, eyes dark, its blades folded in prayer. |
| Guardian | Sways like a leaf in the wind and turns to face whoever it watches, **Scythe:** both blades cut across the front (range 26, 65° arc). **Blade wave:** a cone of Qi blades and leaves skims out along the ground (46 studs, 50° either side); jump it. |
| Weakened | Crouches and lowers its blades. |
| Enraged | The mantis threat display (the robe flared like wings, blades raised and open, eyes red), chasing at 23 studs/s. **Leap:** long and high (up to 72 studs), its first move after the theft. |

### The Ember Xuanwu (Ember Peak)

The Black Tortoise of the north gone to the volcano (chosen by the owner, November 2, 2026): a colossal tortoise whose shell has become a small volcano, a dome of black basalt columns stepped up into a cone, the magma inside the shell glowing in every seam between the columns. Coiled round the shell is its companion, a molten serpent of cooled black crust broken into bands, lava glowing between them, its dragon head rising over the volcano's flank. The tortoise has a snapping turtle's wedge of a face, a hooked horn beak and a crown of small basalt columns. About 24 studs to the crater's rim, 31 to the serpent's crown, 48 from beak to tail (`tools/blender/guardians/ember_xuanwu.py`, 15 jointed segments; the basalt Shell is its own piece on the Body).

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

The heavenly hound of the eclipse myth, the dog that swallows the moon (chosen by the owner, November 2, 2026, over a three-legged moon toad and a moon-backed spider). A lean, long-legged sighthound whose coat is the midnight sky (deep blue, faint constellations in it, silvered where moonlight falls), with a ruff, a plume of a tail and feathered legs of white fire, tall pointed ears with a flicker of fire inside, fangs and a black nose. Above its shoulders stands the eclipse it made: the swallowed moon as a black disc (dark Neon) ringed by a corona of white fire with a few long streamers, framing its head from the front, held up by streams of fire from its shoulders. About 14 studs at the shoulder, 33 to the top of the eclipse, 44 from nose to tail.

**Rebuilt with a skeleton (November 5, 2026), the first of the owner's boss rebuilds** ("all the boss in the game is actually stiff"; "please put rig, skeleton and more weight paint"): `tools/blender/guardians/tiangou_v2.py` makes one continuous skinned body on 32 bones with painted weights. Its gallop was approved in clay first: 44 studs a stride, so a planted paw stays still at its chase speed. In Studio, `GuardianBuilder.storeSkinned` fits the import (`Placements/TiangouSkinned`) and sets the model's `Rig` attribute. Importer facts: File > Import 3D keeps bones and all four maps, drops a bone that only single-bone pieces use (`AddBones` puts Jaw and Eyes back), and can leave pieces about 300 studs off in height. A missing bone would freeze the animation with no error, so `GuardianAnim` waits for every bone.

**Its eyes** (`guardian_kit.eye`): gold almonds with round black pupils under a low, scowling brow. It blinks every few seconds, shuts them asleep, glares (narrowed, red) enraged, and widens and flickers weakened. Its corona burns low asleep (Neon fades with transparency), gutters weakened, flickers enraged and flares as it howls.

Its lair is the middle of the Lunar Court, facing the Crescent Arch; a thief carries its egg home to Yggdrasil (until November 2, 2026 its safe zone was the Celestial Pavilion). 11,000 health: a Soul Awakening's Spirit Soul sword weakens it (below 10%) alone in about 118 strikes. Securing its egg pays 4,000 Spirit Stones; its relic unlocks Frost. Messages call it "Tiangou" (`Called`).

| State | What it does |
|---|---|
| Dormant | Asleep on its feet: head low, eyes shut, tail down, the corona burning low. |
| Guardian | Alert, turning quickly to face whoever it watches, tail waving. **Bite:** it draws back and snaps (range 25, 60° arc). **Eclipse howl:** head thrown back to the sky, the eclipse flares and a ring of frost rolls out all round (52 studs); jump it. |
| Weakened | Crouched low, panting. |
| Enraged | The hunting crouch, lips drawn back, tail up, eyes red, chasing at 27 studs/s (it stops 17 short, `ChaseStop`). **Moon leap:** long, low bounds (18 to 85 studs, 12 high; the owner found 26 too high, November 5, 2026), stretched flat in the air. |

Measured in Play (November 2, 2026): wake (it howls at once), bite, howl, weaken, steal (a Heavenly Throne Egg), the howl's ring knocking a grounded thief who drops the egg, recover, moon leaps aimed ahead of the runner and landing at the sanctuary's edge, and a secured egg (+4,000 stones). Most of its maps rendered grey after the first upload; they are re-uploads.

### Pangu the World-Splitter (Origin Abyss)

In the myth Pangu hatched from the cosmic egg and split the chaos inside it into heaven and earth with his axe (chosen by the owner, November 2, 2026, over Hundun and the Taotie). A titan of dark stone still cracked with the chaos he came from: violet void light in every fissure and a crack of it splitting his brow, a mane and a mantle of void drifting from him like smoke, great curved horns bound in bronze, a carved stone beard and moustache, a bronze belt with the disc of yin and yang (the split he made) over torn hangings. The world-splitting axe, a crescent of black stone with a void-lit edge, rests on his right shoulder His left hand is free. (He holds no egg: no guardian does.) The island's rift is his axe stroke. About 38 studs to his crown, 46 to his horns (`tools/blender/guardians/pangu_v2.py`: the first guardian on two legs).

**His eyes** (`guardian_kit.eye`): deep-set violet almonds with dark pupils, the lids bearing down toward his nose (an eye's `forward` is the nose side: pointed outward, the same lids read sad). He blinks slowly, shuts them asleep, glares (narrowed, red) enraged, widens and flickers weakened. The void in his cracks burns low asleep, pulses with his breath, gutters weakened and flares as he strikes.

His lair is the middle of the Void Court, facing the Gate of Descent; a thief carries his egg home to Yggdrasil, back past him and across the bridge (until November 2, 2026 the Gate of Descent terrace). 24,000 health: a Divine Initiate's Divine sword weakens him (below 10%) alone in about 120 strikes. Securing his egg pays 12,000 Spirit Stones; his relic unlocks Void. Messages call him "Pangu".

| State | What he does |
|---|---|
| Dormant | A statue: head bowed, eyes shut, the void burning low. |
| Guardian | Turns to face whoever he watches. **Axe cleave:** the axe comes off his shoulder and over, into the ground before him (range 30, 75° arc). **Sky-splitter:** both arms raise the axe and slam it down; a fissure races 70 studs straight ahead in a narrow line (15°): jump it or step aside. **Chaos nova:** he thrusts his open left palm to the sky and the chaos bursts out all round (44 studs); jump it. |
| Weakened | Down on his right knee, the left hand braced on the raised knee, the axe lowered. |
| Enraged | Squared up, the axe lifted, eyes red, chasing at 28 studs/s. **Titan leap:** 20 to 75 studs, 22 high, landing with a shockwave. |

**Rebuilt with a skeleton (November 5, 2026, the owner's second boss rebuild):** `tools/blender/guardians/pangu_v2.py` makes one continuous skin on 41 bones, bound with the arms spread, heavier than before (no waist, slab chest, pillar legs), with a crescent battle-axe. A held weapon's grip is built into the hand: fingers round the haft, the edge along the knuckles, the hand and arm solved to it. His legs are solved, so a planted foot stays planted and the strides are measured (walk 17.33 studs, run 33). `write_clips` generates `GuardianRigs/PanguClips.lua`, the poses, gaits and moves as data; `GuardianRigs/PanguSkinned.lua` plays them through the springs, 0.1 s ahead so each blow lands with its effect. The left arm is free: he holds no egg. His left hand is open: a broad palm past a narrower wrist, four fingers curled toward the palm, the thumb forward as he stands; on the kneel it lies over the raised knee, and on the Sky-splitter it closes on the haft beside the right fist. Each arm's twist is shared by shoulder, elbow and wrist (half, 30%, 20%), because the skin has no twist bones and a joint turned too far about the limb pinches. Importer facts: Axe and Eyes are dropped and go back with `AddBones` (a bone-local value is Blender's with X and Z flipped, in position and rotation); `storeSkinned` works out every piece's destination before moving any, because the importer's motors join the pieces and moving one moves them all, and it checks where each would land first.

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

## 7c. Titles (November 9, 2026)

The owner asked for titles ("BETA TESTER, DEVELOPER, AND THE 12 REALMS TITLES etc."; then "Also add content Creator and add sheen effects on the title"), and chose: a nameplate above every player plus a Titles window to choose one; Beta Tester for everyone who plays before launch; a unique epithet per realm; and all four extras (guardian, beast collector, secret beast, relic seeker).

- **The nameplate:** over every player's head, the title they wear over their display name, in the title's own lettering and colour. Now and then a sheen sweeps across it (the owner asked for it, then found it hardly visible): a wide slanted band with a white-hot core and a halo of the title's colour, lighting the letters and their outline together. The grandest sweep more often, their halo their own Shimmer colour; each player's sweeps keep their own moment, so a crowd never flashes at once.
- **Typography** (the owner: "try to add typography for the titles"): each title has lettering of its own from Roblox's font families (TitleRules' FONTS), chosen for its meaning: Developer in Sarpanch Heavy (engineered), Content Creator in Luckiest Guy (a bold thumbnail face), Beta Tester in Michroma (futuristic); the realms from brush calligraphy (Fondamento: the Awakened, Cloud Strider) through stone (Oswald: Bedrock Disciple), forged metal (Sarpanch: Core Forger), book type (Accanthis: Soul-Tempered, Keeper of the Dao), Roman inscription (Roman Antique: the Deathless, the Eternal) and blackletter (Grenze Gotisch: Heaven's Chosen, the Primeval) to far-future faces (Jura: Starborn; Zekton: Void-Touched); the guardians' and collectors' as they suggest (Keeper of Secrets in blackletter, Relic Seeker in an explorer's typewriter face). It replaces Roblox's own name (their health bar stays) and fades out past 90 studs. Everyone sees everyone's.
- **The Titles window** (Titles on the HUD's rail, between Quests and Settings, an honour-banner icon): every title by section, earned or locked, with how to earn it; WEAR on any earned one. **AUTO** (the default) shows Developer, else Content Creator, else Beta Tester, else their highest realm's title; **HIDE** shows none. A new title is announced at the top of the screen and counted on the button's badge; the ones a returning player already qualifies for are announced together, once.
- **Saved** in PlayerData as Titles (schema 14): what they have earned (kept for good, even if their Qi ever fell back) and what they chose. Developer and Content Creator are never saved: they follow their lists in `GameConfig.Titles`, so one can be taken away.

| Section | Title | How it is earned |
|---|---|---|
| Special | Developer | The game's creators (`GameConfig.Titles.DeveloperUserIds`); its row shows only to them |
| Special | Content Creator | Given: their UserId in `GameConfig.Titles.ContentCreatorUserIds` (the owner, November 9, 2026); off the list, they lose it on their next join |
| Special | Beta Tester | Playing before the launch (`GameConfig.Titles.BetaEndsAt`, a Unix time; while it is nil the beta runs and everyone earns it). **Set it before the launch.** |
| Realms | the Awakened, Bedrock Disciple, Core Forger, Soul-Tempered, Cloud Strider, the Deathless, Heaven's Chosen, Starborn, Void-Touched, Keeper of the Dao, the Primeval, the Eternal | Reaching each of the twelve realms in turn (Qi Awakening to Eternal Transcendence), in the realm's colour; from the Divine Realm up a light runs across them |
| Guardians | Pride Thief, Bamboo Shadow, Ashwalker, Moon-Saver, Pangu's Rival | Carrying an egg home from the Stone Lion, the Mantis Sage, the Ember Xuanwu, Tiangou, Pangu (they are robbed, never beaten). Counted from now on: eggs secured before titles existed aren't recorded |
| Collection | Beast Seeker, Beast Tamer, Beast Master, Keeper of the Codex | 10, 25, 45 and every beast (61) in the Spirit Beast Codex |
| Collection | Keeper of Secrets | A Secret beast in the Codex (owned at least once) |
| Collection | Relic Seeker | Every relic on the islands found |

Code: `shared/TitleRules` (every title: text, colours, how), `server/Titles/TitleBook` (each player's book, saved) and `TitleService` (gives them out: on joining, every 2 seconds for realms, the Codex and relics, and at once on a secured egg; takes the choice to wear), `client/UI/TitleController` (nameplates, the window, the notices). The player's `Title` attribute is the title they show.

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

- **Settings** (the Settings button on the rail; `client/UI/SettingsController`, `server/Data/Settings`, saved as `Settings`, save version 10): Music and Sound volume, and Reduced Effects, which hides other players' auras and turns off screen flashes and camera shake on that player's own client.
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
- **Egg Highlights:** at most 4, within 90 studs (8 within 140 elsewhere).
- **Guardians:** animated within 150 studs instead of 400, every other frame at rest, springs at 1/120 s. Waking each of the five showed no instability, against the same test on PC settings.
- **Others' pets:** hidden past 80 studs instead of 250. **Others' poses:** stop past 80 studs. **Robes:** sway within 40 instead of 120.
- **Everyone, PC too:** the pose loop no longer allocates a table per joint per frame, a robe still loading looks for its pieces once a second instead of every frame, and the rounded interface dropped a glow stroke and eight tick frames per panel.

Not yet measured on a real phone.

**The phone pass (November 9, 2026, the owner's "do the 3"):**
- **Measured on real devices, as players play** (`client/Performance/PerfProbe`, `server/Analytics/PerfService`): every client measures its own frame rate (the average and the slow end, its slowest 5% of frames) and memory, and reports every two minutes after the first minute; they land on the Creator Dashboard as the custom events **ClientFps** (value: average frames a second; by device, Phone, Tablet, PC or Console, marked when the phone tier is on; and the slow end in a band) and **ClientMemory** (value: MB; by device; in a band). Phone versus tablet is by the screen's shorter side (under 600 px: a phone).
- **A live readout for developers:** Settings shows them PERFORMANCE READOUT (not saved): frame rate, its slow end, memory, instances and parts drawn, at the top left, to read on their own phone.
- **The phone tier, extended to what came after it:** other players' pets give up their point lights (PetRig); nameplates are drawn within 55 studs instead of 90; other players' tribulation storms within 160 studs instead of 320, with thinner cloud and no sparks.

### Pets arrive whole (November 4, 2026)

A pet is many mesh pieces fetched on first use, so on a phone it came in slowly, a piece at a time. `client/Pets/PetPreload` now downloads a pet before it's built (for 8 seconds at most, so one can't go missing) and fetches a player's other pets in the background once their inventory arrives. HUD icons load at start too.

### The interface's look (the owner, November 4, 2026)

The owner sent a reference of dark ornate panels with gold, and said: "something like this UI but not too much". Deep navy with a touch of indigo (the owner had earlier found strong colours too much and preferred blue), fine gold trim, gold for what matters (the main button, progress, the rank), a small cloud-scroll ornament on the corners of the main panels (`tools/ui/draw_frame.py`, original drawings, `assets/ui/frame`). The **Cultivation dock** (`Hud.CultivationDock`, the owner: "I want that to be better like in the image, just that part") joins the Qinggong line and Cultivate into one plate (no wings: tried, and the owner said "we don't need the wings"): a round silver emblem with a gold ring and a gold cultivator seated in the lotus (the owner: "the icon for that cultivation is a person doing lotus sit"), "Cultivation" and the air leaps left, the stamina bar ending in a diamond, and a gold pill for the button. The air leaps are now a count instead of a row of diamonds. Merriweather for names and titles, Montserrat for the rest. Left out of the reference on purpose: its wings, tassels and heavy glow, and Teleport, which the owner excluded earlier. All colours live in `UiTheme`.

### The interface's life (the owner, November 4, 2026)

"Find a way to make it better, like more interactive or more appealing in the eye of players." How it responds lives in `client/UI/UiFx.lua`, used through `UiKit` and `Hud`, so every screen has it:

- **Buttons:** on hover they lift and a band of light crosses them, and a rail button's icon grows. Pressed, they sink with a ripple from the touch. A phone gets the press and ripple; a touch never leaves, so it has no hover state.
- **One main action:** tone `Primary` (gold, a halo, a line of light along the top) is for Cultivate alone, and light crosses it now and then. A breakthrough waiting (`Highlight`) has the same halo in gold and breathes, and the status bar turns gold. Everything else stays calm: a bright button loses its meaning when there are fifteen.
- **Windows:** they rise and unfold with a line of light running down them, their edge flashes, their rows settle in one after another, and light travels slowly round the edge. They shrink away on closing. All windows share the open sound.
- **Numbers:** Qi, Spirit Stones and Relics roll to their new value and the difference floats off under the chip ("+40", red when spent), with the icon jumping. A stream of small gains floats as one number at most every 0.9 seconds. Nothing floats for the first 4 seconds, while a save loads.
- **Bars:** a band of light runs along what's been filled.
- **Text:** a notification and a new quest write themselves on.
- **Joining:** the HUD arrives from the screen's edges, once.
- A rule learned the hard way: light needs a child sized by its parent, so it skips any frame sized by its contents, which it would stretch.

### The HUD's layout (the owner, November 4, 2026)

Laid out from a reference image the owner sent ("I mean the position"), leaving out its teleport and skill bar, with Roblox's chat left at the top. On every screen: the profile top left (portrait, name, rank, realm, progress; tapping the portrait folds it, and that's saved); the menu down the left (Pets, Robes, Quests, Settings); Qi, Spirit Stones and Relics top centre, beside Roblox's own buttons; Rewards as a round button top right; the quest panel on the right, which the Quests button shows or hides (saved as `ShowQuest`); the guardian's bar and messages under the currencies; Cultivate and the Qinggong strip bottom centre; Strike, Dash and Sword round the jump button. It replaced a folding phone menu built an hour before. Seen in Play at desktop size; the fit on a phone is worked out from the owner's screenshots, not yet seen there.

### The HUD at any screen size, and what it shows (the owner's list, November 5, 2026)

- **Screen sizes (`client/UI/HudMetrics`):** a screen is a Phone (under 500 px on its shorter side), Tablet (under 800) or Desktop, and pieces change their layout for it instead of the whole interface only shrinking. The scale runs from 0.8 up to 1.6, so a big monitor keeps the same share of HUD. Text is never drawn under 10 px, whatever the scale. A window on a small screen keeps the scale and gets shorter, its list scrolling. On a phone the menu is a row of icons under the profile, leaving the thumbstick's corner free. In Studio, the player's `HudTestViewport` attribute stands in for the screen's size.
- **Counters:** Qi, Spirit Stones and Relics share one slim strip.
- **Touch buttons (`client/UI/TouchActions`):** never more than two beside the jump button. Near something to fight: Strike and Dash. Otherwise: Sword (once it can be ridden) and Dash. Riding: Sword, to land. Cultivating: none.
- **Cultivate:** while running, the button turns from gold to jade and reads CULTIVATING - STOP, a band of light keeps crossing it, the emblem's ring turns and its well glows.
- **Quest panel:** its header folds it to the quest's title. It starts folded on a phone, and a new quest opens it for 8 seconds.
- **Stamina:** the dock keeps its Cultivation title (the owner's choice); the bar has STAMINA and a percentage written on it, ticks mark what a dash costs so the dashes left can be counted, it pulses red when there isn't enough for one, and it shakes when a dash is refused for that reason.
- **Guardian's bar:** a taller bar with larger numbers. Weakened, it fills gold, its edge pulses, and the guardian is outlined in gold through anything in the way.
- **Taking an egg:** while a player really can take one (the server's `CanTakeEgg` attribute, by the same rules as the take itself), a panel says so and points to the nearest stand, then names the key to hold, and each stand holding an egg their rank can carry is marked TAKE on the screen. The marks stand clear of the eggs, which keep only their Highlight and bloom.

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
- **Monetization:** changed by the owner (November 10, 2026): game passes that boost play are now sold (the Store, below), replacing the old "cosmetic-first, never pay-to-win" rule. Paid eggs: only as the Exclusive Egg, once its beast exists, showing its odds and not offered where Roblox restricts paid random items (PolicyService `ArePaidRandomItemsRestricted`).
- **The Shop (game passes, November 10, 2026):** the first button on the left rail, a gift box named "Shop" (on a phone, where the rail is bare icons, a gold SHOP label stays under it) opens it. Four passes, each sold once its GamePassId is set in `GameConfig.GamePasses` (until then "Coming soon"), its live price read from Roblox: **Lucky Cultivator** (149 R$): every Rare-or-rarer beast that is also rarer than the egg's commonest hatches twice as often, the others giving up the difference (`PassRules.luckyPool`; the altar shows the owner's own odds, marked "2x luck"); **Qi Surge** (199 R$): 2x Qi from cultivating, offline Qi and every Qi reward; **+3 Pet Slots** (249 R$): 6 beasts equipped instead of 3 (three more follow spots); **VIP** (299 R$): the gold VIP title, a gold [VIP] chat tag, +10% Qi (stacking: 2.2x with Qi Surge) and +50% daily Spirit Stones. The server checks ownership on joining and counts purchases (`GamePassService`), setting `Pass_<Id>` attributes; a player found not to own the slots pass has beasts over 3 unequipped. The **Exclusive Egg** shows as a locked "Coming soon" card. In Studio, ServerStorage's `StudioTestPasses` ("All" or ids) tests the passes.
- **Selling outfits:** a game pass in this game (ready: set `GamePassId`) or the Roblox Avatar Marketplace (needs the UGC program and layered clothing fitted to any avatar).
- Per-element and per-realm aura looks.
- Blender models for the remaining procedural pets.
- Balance tuning from playtests.
- **No rebirth** (the owner, November 4, 2026): breaking through to the next realm is the progression. A small area with a Qi multiplier may come later.

**North star:** players feel like cultivators who earned their power and their movement. They train Qi to grow stronger and master Qinggong to move beyond ordinary limits. They will challenge guardians for their eggs and survive the pursuit that follows. Failure is a recoverable setback, never an unfair loss.
