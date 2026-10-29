# Qi Aura Simulator

## Game Concept and Development Reference

**Document type:** Game Design Overview\
**Platform:** Roblox\
**Project folder:** `qi-aura-simulator`\
**Status:** Early development --- toolchain setup\
**Last updated:** October 29, 2026

------------------------------------------------------------------------

## 1. High Concept

**Qi Aura Simulator** is an original Roblox cultivation simulator where
players train their inner Qi, rise through cultivation ranks, discover
and collect aura pets, hatch eggs, and freely fly around floating
islands.

The main fantasy is to become a powerful cultivator whose growing Qi is
visible through increasingly impressive aura effects. Players should
always have a clear next goal: train for more Qi, reach the next rank,
discover a new pet, unlock an upgrade, or explore somewhere new.

The game should feel rewarding and readable, with original art and
effects rather than relying on generic asset packs.

## 2. Core Design Pillars

1.  **Visible progression:** Training, ranks, and upgrades should
    produce noticeable changes in stats and visuals.
2.  **Collecting and discovery:** Pets are rewards to find, hatch,
    collect, and improve.
3.  **Freedom of movement:** Flight makes the world fun to explore
    rather than just a set of menus.
4.  **Active and passive play:** Players can train directly or use
    training stations to earn Qi over time while playing.
5.  **Player expression:** The selected aura pet determines the player's
    aura style.
6.  **Fair, secure multiplayer:** The server validates important actions
    and progression. Competitive stealing, if added later, must have
    clear limits and protections.
7.  **Original, maintainable development:** Build our own models,
    effects, UI, and code with a structure that another developer can
    understand.

## 3. The Core Gameplay Loop

1.  **Train** to earn Qi.
2.  **Accumulate Qi** and meet the requirements for the next cultivation
    rank.
3.  **Rank up** to improve progression and unlock further opportunities.
4.  **Collect pets** by hatching eggs and discovering them through
    exploration.
5.  **Equip pets** to gain stat bonuses.
6.  **Choose an aura pet** to set the visual style of the player's aura.
7.  **Upgrade flight** and explore floating islands.
8.  **Find new training opportunities, eggs, and discoveries.**
9.  Repeat with higher requirements, stronger bonuses, and more places
    to explore.

The first playable version should make this loop satisfying before
adding complicated systems.

## 4. Qi and Cultivation Ranks

Qi is the primary progression currency and represents the player's
cultivation power.

### Ways to earn Qi

-   **Active training:** The player deliberately performs a training
    action to earn Qi.
-   **Training stations:** Designated locations provide passive or
    repeated Qi generation while the player uses them.
-   **Future discoveries:** Certain exploration rewards or events may
    provide Qi.

### Cultivation ranks

Players spend or meet a Qi requirement to advance through ranks. Each
rank can increase the player's power and aura intensity and may unlock
content.

Use a small number of original ranks in the MVP. Exact names, costs,
multipliers, and balance values are **not finalized** and should live in
shared configuration rather than being scattered through scripts.

Rank-ups must be checked by the server.

## 5. Pets and Aura System

Pets are collectible companions and progression bonuses.

### Acquisition

-   **Egg hatching:** Players obtain eggs and hatch them to receive
    pets.
-   **Exploration and discovery:** Some pets or eggs may be rewards for
    reaching locations or completing discoveries.

### Equipping

-   The MVP starts with **three pet equipment slots**.
-   Every equipped pet contributes its configured stat bonuses.
-   The player selects one equipped pet as the **aura pet**.

### Combined aura design

The system has two separate responsibilities: - **Visual style:** The
selected aura pet determines the aura's appearance, theme, and effect
style. - **Stat bonuses:** All equipped pets contribute their bonuses,
whether or not they are the selected aura pet.

This allows players to choose the look they like without losing the
bonuses from their other equipped pets.

### Originality

Pet names, silhouettes, models, rarity tiers, egg designs, and aura
effects should be original. Do not depend on third-party asset packs as
the core art direction.

## 6. Flight and Exploration

Flight is a major feature, not just a short jump ability.

### Intended experience

-   Free three-dimensional flight through the world.
-   Flight speed upgrades.
-   Floating islands and locations worth visiting.
-   Space for future discoveries, eggs, training areas, and progression
    gates.

Flight should feel controllable and responsive on the supported input
methods. Input handling and movement must be tested in Roblox Studio,
including multiplayer behavior. The server should validate important
rewards and access conditions so clients cannot simply award themselves
progress.

The MVP should start with a small original floating island rather than a
huge empty map.

## 7. World and Visual Direction

### Initial world

Build one compact, original floating island that contains: - A spawn and
orientation area. - A basic active training area. - At least one passive
training station. - A place for the first egg or pet-discovery
interaction. - Clear visual landmarks and room to test flight.

### Art direction

-   Original, readable shapes and silhouettes.
-   A cultivation-inspired atmosphere built around Qi, energy, floating
    land, and aura effects.
-   Low-poly modeling is a reasonable starting approach for creating
    original assets.
-   Effects should communicate power without obscuring the player or
    making the screen unreadable.
-   UI should clearly show Qi, current rank, pets, and the next useful
    action.

Blender can be used for original models, while Roblox Studio is used to
assemble and test the world. Final palette, detailed lore, and exact art
style remain open decisions.

## 8. MVP Scope

The Minimum Viable Product (MVP) is the smallest complete version that
proves the game is fun.

### Planned MVP features

-   One original floating island.
-   A working Qi counter.
-   Active training.
-   At least one passive training station.
-   A small set of cultivation ranks.
-   Three original pets.
-   Three pet equipment slots.
-   One selected aura pet that controls aura appearance.
-   Stat bonuses from all equipped pets.
-   A basic aura that scales with rank.
-   Basic free flight and a flight-speed upgrade.
-   A first egg-hatching or discovery flow.
-   Server-validated rewards, inventory, and progression.
-   Persistent saving for core player data.
-   Basic UI for Qi, rank, pets, and relevant interactions.

### Deliberately out of scope for the first MVP

-   A large multi-island world.
-   Dozens or hundreds of pets.
-   Complex trading or player-to-player economies.
-   Competitive stealing or raids.
-   Monetization systems before the core loop is tested.
-   Large-scale quests, clans, or PvP.

These may be considered later based on testing and development capacity.

## 9. Stealing, Raids, and Player Protection

Stealing is an optional future idea, **not an MVP requirement**.

If added, it should be implemented as a clearly defined, opt-in risk
system rather than unrestricted theft. Possible safeguards: - Only
eligible pets or rewards can be at risk. - Equipped pets and unique or
protected pets cannot be stolen. - Raids require consent or explicit
participation. - Cooldowns, clear warnings, and loss limits prevent
repeated harassment. - Server-side checks determine eligibility and
outcomes. - Players should understand the risk before participating.

The exact rules need to be designed and tested before implementation. Do
not build stealing into the initial data model or gameplay loop unless
the design is revisited deliberately.

## 10. Technical Architecture

### Current toolchain

-   **Roblox Studio:** World building, playtesting, and final in-engine
    validation.
-   **VS Code:** Editing and organizing project files.
-   **Rojo 7.7.1:** Synchronizing the filesystem project with Roblox
    Studio.
-   **Git:** Version control.
-   **Homebrew:** Installed on the development Mac and used to install
    Rojo.

### Project layout

The project folder is `qi-aura-simulator`.

``` text
qi-aura-simulator/
├── default.project.json
└── src/
    ├── shared/   # Shared definitions and configuration
    ├── server/   # Authoritative game logic
    └── client/   # Player-side presentation and controls
```

The current Rojo project configuration maps: - `src/shared` to
`ReplicatedStorage` - `src/server` to `ServerScriptService` -
`src/client` to `StarterPlayer/StarterPlayerScripts`

Keep the Rojo server terminal running while working with the live
connection. Build and test changes in small steps.

### Responsibilities

**Server-side logic** should own or validate: - Qi awards and
rank-ups. - Pet inventory, equipping, and hatching outcomes. - Important
unlocks and rewards. - Saving and loading player progression. - Any
future raid or stealing outcomes.

**Client-side logic** should primarily handle: - UI presentation. - Aura
rendering and visual effects. - Player input and flight
responsiveness. - Local visual feedback and animation.

**Shared definitions** should hold consistent configuration such as rank
requirements, pet definitions, stat bonuses, and other data used by both
sides. The server must not trust the client to tell it how much Qi to
award or what pet an egg produced.

## 11. Data and Security Principles

-   Validate important actions on the server.
-   Never trust client-provided currency amounts, rank claims, hatch
    results, or inventory changes.
-   Use Roblox's supported data persistence mechanisms for player
    progress.
-   Handle save failures and player disconnects carefully.
-   Keep code modular, readable, and easy to change.
-   Test multiplayer behavior and edge cases, not just a single-player
    happy path.
-   Avoid unnecessary dependencies and third-party assets.
-   Do not store secrets in source control.
-   Add monetization only after the core game is functional and fair.

## 12. Development Roadmap

### Phase 1 --- Project foundation *(current phase)*

-   [x] Create `qi-aura-simulator`.
-   [x] Initialize Git.
-   [x] Install and verify Rojo 7.7.1.
-   [x] Create `default.project.json`.
-   [x] Create `src/shared`, `src/server`, and `src/client`.
-   [x] Confirm a basic Rojo build succeeds.
-   [ ] Install and verify the Rojo Studio plugin.
-   [ ] Start Rojo and connect Studio.
-   [ ] Verify filesystem-to-Studio synchronization.

### Phase 2 --- First playable prototype

-   Create the basic island and spawn.
-   Implement Qi display and active training.
-   Add one passive training station.
-   Test the loop with temporary values.

### Phase 3 --- Cultivation progression

-   Define initial ranks and requirements.
-   Implement server-validated rank-ups.
-   Add rank feedback and aura scaling.

### Phase 4 --- Pets

-   Define three original pets.
-   Implement inventory and three equipment slots.
-   Add pet stat bonuses and aura-pet selection.
-   Add the first hatch or discovery interaction.

### Phase 5 --- Flight and exploration

-   Implement responsive 3D flight.
-   Add a flight-speed upgrade.
-   Connect flight to the island exploration loop.

### Phase 6 --- Persistence and reliability

-   Save and load Qi, rank, and pet progression.
-   Test rejoining, failed saves, and invalid requests.
-   Test multiplayer and exploit-resistant server validation.

### Phase 7 --- Polish and release preparation

-   Improve original models, aura effects, and UI.
-   Balance the progression loop.
-   Test on relevant devices and input methods.
-   Review Roblox platform rules and monetization choices before
    release.

Phases can overlap after their dependencies are stable. Do not add every
feature at once; keep each milestone playable and testable.

## 13. Monetization Direction

Monetization is a future design decision. First validate that training,
collecting, progression, and flight are fun without purchases.

Potential options to evaluate later include: - Cosmetic aura styles and
visual effects. - Optional convenience features that do not destroy
progression balance. - Carefully balanced game passes or developer
products.

Avoid promising pay-to-win advantages or designing the game around
pressure to spend. Any paid random-item mechanics require careful review
of Roblox policies and applicable rules. Do not implement paid eggs or
paid random rewards until the policy and disclosure requirements are
checked.

## 14. Open Decisions

These decisions are not finalized: - Exact rank names, costs, and
progression speed. - Pet rarity tiers, stat values, and acquisition
rates. - Final art palette and visual identity. - Whether the game will
have multiple islands at launch. - Whether stealing or raids will ever
be included. - Monetization features and prices. - The exact first-time
player tutorial. - Final flight controls and supported device
priorities.

Record decisions here as they become settled instead of silently
changing the concept.

## 15. Current Checkpoint

**Last known development checkpoint:** The Rojo server was started
successfully and reported:

``` text
Rojo server listening:
  Address: localhost
  Port:    34872
```

The project built successfully using:

``` bash
rojo build default.project.json -o /tmp/qi-aura-check.rbxlx
```

After that, `default.project.json` was updated to map the `src/shared`,
`src/server`, and `src/client` folders. The next action is to run the
build command again in a **second VS Code terminal**, keeping the
`rojo serve` terminal running:

``` bash
rojo build default.project.json -o /tmp/qi-aura-check.rbxlx
```

If the build succeeds, continue by verifying the Rojo Studio plugin and
live synchronization. Do not start gameplay scripting until the
connection is confirmed.

## 16. Working Rules for This Project

-   Work one step at a time.
-   The user will type **NEXT** when a step is complete.
-   Give one primary action per step and wait for confirmation.
-   Explain what each tool or file is for in beginner-friendly terms.
-   Do not assume a step succeeded without the user's confirmation.
-   Prefer original assets, readable code, and a maintainable structure.
-   Avoid unnecessary complexity before the core game loop works.
-   Keep this document updated when important design or architecture
    decisions change.

------------------------------------------------------------------------

**North-star statement:** Build an original Roblox cultivation simulator
where training, pet collection, visible aura progression, and free
flight form a satisfying loop---and build it in small, secure, testable
steps.
