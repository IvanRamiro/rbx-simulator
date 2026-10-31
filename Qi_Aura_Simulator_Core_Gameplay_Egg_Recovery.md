# Qi Aura Simulator — Core Gameplay & Egg Recovery Design

**Document type:** Gameplay design addendum
**Status:** Proposed direction. Implementation starts after the Starting Island rebuild is complete.
**Purpose:** Define the intended core gameplay loop around Qi cultivation, Qinggong movement, guardian encounters, egg theft, pursuit and egg recovery.

This addendum extends [Qi_Aura_Simulator_Design.md](Qi_Aura_Simulator_Design.md) and [Qi_Aura_Simulator_Aura_VFX_Brief.md](Qi_Aura_Simulator_Aura_VFX_Brief.md). Where it does not say otherwise, those documents still apply.

## 0. Project directives (fixed, do not change)

- **Ranks:** no changes to the rank ladder.
- **Eggs:** no changes to the existing eggs (their pets, pools and themes stay as designed).
- **Mandatory rules stay:** "no mistakes" design quality, and every pet must always have expressive eyes.
- **Aura concept:** no changes to the aura concept. The goal is not an aura that merely looks similar to Sol's RNG. It is to genuinely compete with, and potentially surpass, the visual quality of Sol's RNG's most impressive auras.
- **Weapons for battle:** players can purchase or request a forged weapon, with the weapon available to them depending on their Qi mastery.
- **Sword flight:** the sword can also be used for flight. This is the only free flight in the game; Qinggong replaces general flight.

## 1. Core game identity

Qi Aura Simulator is a cultivation action-adventure game built around a high-risk egg-theft loop.

Players cultivate Qi to increase their power, master Qinggong to improve their movement, challenge guardians protecting rare eggs, weaken those guardians, steal their eggs, and escape before being caught.

The key distinction is:

> **Defeating the guardian is not the final objective. Stealing the egg and successfully escaping with it is.**

**Core promise:** Cultivate. Challenge. Steal. Escape. Recover.

## 2. Core gameplay loop

1. **Cultivate Qi:** train to increase combat strength and unlock progression.
2. **Train Qinggong:** improve aerial movement, dashes, control and escape capability.
3. **Discover a guardian:** find the boss protecting an egg on an island.
4. **Fight the guardian:** deal enough damage to force it into a Weakened state.
5. **Steal the egg:** interact with the exposed egg while the guardian is weakened.
6. **Trigger the pursuit:** the guardian realises its egg has been stolen and becomes enraged.
7. **Escape:** use Qinggong, routes, timing and Qi abilities to reach safety.
8. **Secure the egg:** reach the extraction or safe zone to add the egg to the player's inventory.
9. **Hatch the egg:** use the existing pet collection and hatching system.
10. **Grow stronger:** equip pets, improve Qi, advance ranks and challenge stronger guardians.

## 3. Qi and Qinggong

Qi and Qinggong have distinct purposes.

### Qi: power

Qi represents cultivation strength and supports:

- Combat damage and combat progression.
- Cultivation ranks and realm advancement.
- Access to stronger islands and guardians.
- Qi-based abilities, where appropriate.
- Existing Qi rewards and progression systems.
- Which forged weapons a player can purchase or request.

### Qinggong: mobility

Qinggong represents movement mastery and supports:

- Air steps and aerial running.
- Directional dashes and evasive movement.
- Acceleration and movement control.
- Longer or more demanding escape routes.
- Advanced movement challenges on later islands.

Qinggong should feel like martial-arts movement through the air, not ordinary flight. Players run, leap, step and dash through the air using momentum and skill. The old free-flight progression is redesigned around Qinggong rather than renamed; sword flight is the separate, later exception.

## 4. Guardian encounter structure

Each guardian encounter has clear states. The server owns every state transition.

| Phase | Trigger | What happens |
|---|---|---|
| 1. Guardian | 100–40% HP | The boss protects the egg, attacks players and uses its normal abilities. |
| 2. Weakened | Below 40% HP | The boss becomes vulnerable, its attacks slow down, and the egg becomes available to steal. |
| 3. Enraged Pursuit | Egg stolen | The boss becomes enraged, chases the thief and uses faster attacks to stop the escape. |
| 4. Escape | Successful extraction | The player reaches a safe zone and secures the stolen egg. |

The 40% threshold is the starting proposal; the exact health threshold and Weakened duration are tuned during playtesting.

### State 1: Guardian

- The guardian protects its egg.
- It attacks players who enter its encounter area.
- Its attacks and movement communicate its identity and threat level.
- The egg cannot yet be stolen.

### State 2: Weakened

- The guardian enters this state when its health reaches the configured threshold.
- Its attacks become less frequent or less effective for a short period.
- Its posture, animation, aura and effects clearly communicate that it is vulnerable.
- The egg becomes available to steal.

### State 3: Egg stolen / enraged pursuit

- A player successfully interacts with the exposed egg.
- The server records that the egg has been taken.
- The guardian immediately recognises the theft and becomes enraged.
- Its behaviour changes from defending its nest to pursuing the thief.
- The guardian may use faster movement, aggressive attacks, leaps or area attacks to stop the escape.

The pursuit creates urgency without making escape feel random or impossible.

### State 4: Escape / recovery

There are two possible outcomes:

- **Successful escape:** the player reaches the required safe zone or extraction point while carrying the egg. The server secures the egg in the player's inventory.
- **Caught by the guardian:** the guardian catches the player and the stolen egg drops into the world. The egg is never permanently destroyed or silently deleted.

## 5. Egg recovery rule

If the guardian catches the player, the egg must be recoverable. This is a core gameplay rule, not an optional bonus.

### What happens when the player is caught

1. The guardian catches or defeats the player during the pursuit.
2. The egg is removed from the player's carried state.
3. The egg drops at a clear, recoverable location near the catch point, or at another safe, readable location chosen by the server.
4. The egg remains in the world for the recovery period.
5. The player can return and interact with the dropped egg to pick it up again.
6. Once it is picked up, the pursuit resumes or the player gets another escape attempt, according to the encounter's retry rules.

The egg is not permanently lost because the player failed one escape attempt.

### Recovery design principles

- **Clear feedback:** tell the player that the egg was dropped and show where it landed.
- **Fair placement:** never place the egg inside geometry, beneath the map, inside the guardian, or anywhere unreachable.
- **Readable ownership:** the server tracks which player or encounter owns the dropped egg.
- **No accidental deletion:** a failed escape must not silently destroy the egg.
- **Meaningful risk:** the player loses time and may need to fight or evade the guardian again, but the effort spent weakening the boss is not automatically wasted.
- **Multiplayer safety:** other players cannot steal, duplicate or claim the dropped egg unless a deliberate multiplayer rule explicitly allows it.
- **Reliable cleanup:** if an encounter is abandoned or the server shuts down, the temporary egg state resolves safely and never awards duplicate copies.

### Retry behaviour (first playable version)

- The egg drops when the thief is caught.
- The same player can recover it.
- Recovering it starts another escape attempt.
- The guardian remains enraged while the egg is unsecured.
- The egg becomes permanently secured only after the player reaches the extraction zone.

This creates a tense recovery moment: the player decides whether to rush back for the egg, wait for an opening, or use Qinggong to evade the guardian before trying again.

## 6. Egg ownership and security

The server is authoritative for:

- Guardian health and damage validation.
- Guardian state transitions.
- Whether the egg is available to steal.
- Which player successfully steals the egg.
- Whether the egg is being carried or dropped.
- Who is allowed to recover the dropped egg.
- Whether the player has reached the extraction zone.
- When the egg is permanently added to inventory.
- Preventing duplicate egg rewards.

The client may display animations, UI, trails, aura effects, hit effects and movement feedback. It never decides that an egg has been stolen, recovered or secured.

Egg lifecycle, with every transition validated by the server:

```
Guarded → Available → Carried → Dropped → Carried → Secured
```

Invalid or repeated requests never create additional eggs.

## 7. Island progression

The five-island structure stays as the world foundation. Each island gets its own guardian, egg acquisition challenge and Qinggong difficulty, developed around its theme.

| Island | Environment | Guardian | Encounter direction |
|---|---|---|---|
| Starting Island | Grassy cultivation grounds; central spawn and Qi Spring | Beginner Guardian | Introductory guardian and basic Qinggong escape |
| Jade Grove | Ancient forest, east | Nature Guardian | Routes through trees or elevated terrain |
| Ember Peak | Volcanic terrain, south-west | Fire Guardian | Escape routes around lava and volcanic hazards |
| Moonlit Isle | Celestial landscape, highest island | Celestial Guardian | More demanding aerial movement |
| Origin Abyss | Void ruins; hidden endgame island far north-west, below the others | Primordial Guardian | The most demanding encounter |

These are proposals. Guardian names, exact attacks, health, egg pools, unlock requirements and rewards still need design and balancing.

## 8. Pet and egg collection

The existing egg and pet systems stay and connect to the new loop:

- Guardians protect the eggs players are trying to obtain.
- Successfully extracted eggs enter the player's egg inventory.
- Players hatch secured eggs with the existing hatching system.
- Hatched pets are collected and equipped.
- Equipped pets keep their configured Qi bonuses.
- The selected aura pet still determines the player's pet-themed aura, where supported.

The egg theft and escape encounter becomes the main acquisition challenge; hatching remains the collection and reward experience.

## 9. Aura and visual direction

Keep the game's visual identity, but make effects communicate gameplay states. There are three distinct visual categories:

1. **Cultivation aura:** the player's Qi realm, power and cultivation state.
2. **Pet aura:** the selected pet's element, personality and identity.
3. **Guardian aura:** the boss's identity, strength, vulnerability and rage.

Guardian visual states must be easy to read:

- **Guardian:** stable, controlled, powerful aura.
- **Weakened:** flickering energy, unstable formations, cracked or collapsing visual elements, and a clear vulnerable core.
- **Enraged:** stronger, more aggressive effects, faster energy movement, and a visibly intensified aura.

The three categories are never interchangeable recolours. Each has its own visual purpose and identity, held to the same bar as the aura concept: compete with, and aim to surpass, Sol's RNG's best auras.

## 10. System responsibilities

| System | Responsibility |
|---|---|
| QiSystem | Cultivation and Qi progression |
| QinggongSystem | Air movement, dashing, speed and stamina |
| CombatSystem | Damage, abilities and combat validation (including forged weapons) |
| BossSystem | Boss behaviour and encounter phases |
| EggTheftSystem | Stealing, ownership and extraction |
| PetSystem | Inventory, hatching and equipment |
| AuraSystem | Character, pet and boss visual effects |

## 11. Development order

Build one complete encounter before expanding the system across every island.

1. Update the design document and core loop to reflect Qi, Qinggong, guardians, egg theft, pursuit and recovery.
2. Implement the first playable Qinggong movement abilities.
3. Build one guardian with server-controlled health and state transitions.
4. Implement the Weakened state and egg interaction.
5. Implement the enraged pursuit.
6. Implement egg dropping, recovery, retry and successful extraction.
7. Connect secured eggs to the existing egg inventory and hatching system.
8. Test multiplayer ownership, exploit resistance, disconnects and edge cases.
9. Expand the encounter framework to the remaining islands.
10. Polish guardian animations, auras, movement trails, sound, UI and cinematic feedback.

## 12. First playable prototype: completion checklist

The first prototype is not complete until a player can:

- [ ] Cultivate Qi.
- [ ] Use basic Qinggong movement.
- [ ] Find and engage one guardian.
- [ ] Damage the guardian until it becomes weakened.
- [ ] Steal the guardian's egg.
- [ ] Trigger the guardian's enraged pursuit.
- [ ] Escape and secure the egg successfully.
- [ ] Fail an escape and cause the egg to drop.
- [ ] Locate and recover the dropped egg.
- [ ] Attempt another escape with the recovered egg.
- [ ] Secure the egg without receiving duplicate copies.
- [ ] Hatch the secured egg through the existing pet system.

## 13. Open questions

- **Egg stands on the islands:** today, eggs are hatched directly at egg stands (the Starting Island's lotus pedestals). Under this loop, eggs come from guardians. Decide whether the stands become the hatching spot for secured eggs, a starter egg source, or are removed.
- **Forged weapons:** the shop or request flow, which weapons each Qi mastery level unlocks, and how weapons tie into CombatSystem.
- **Sword flight:** how it unlocks (which weapon or Qi mastery level), and how it coexists with Qinggong routes that gate islands by air leaps.
- **Qinggong stamina and dashes:** the current build has air leaps, gliding and run speed by rank; stamina and directional dashes are not built yet.

## 14. Design north star

The game should make players feel like cultivators who have earned their power and movement skill. They train Qi to become stronger, master Qinggong to move beyond ordinary limits, challenge guardians for their eggs, and survive the dangerous pursuit that follows.

Failure creates a recoverable setback; it never erases the player's progress unfairly.

**Cultivate your power. Master the air. Steal the egg. Escape the guardian. Recover what you dropped.**
