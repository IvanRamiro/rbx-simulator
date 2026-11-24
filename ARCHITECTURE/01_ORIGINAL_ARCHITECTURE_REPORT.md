# 01 Original architecture report (Phases 1 and 2)

Written on 2026-11-24 BEFORE any file was moved. Everything below was measured from the repository at commit `9f5eb4f` (branch `mvp-core-loop`) and from a read-only look at the open Studio place. Measurement scripts: `tools/check_requires.py` (new, permanent) and the one-off discovery scripts described in section 9. Companion files: [02 New structure](02_NEW_STRUCTURE.md), [03 Migration log](03_MIGRATION_LOG.md), [04 Validation](04_VALIDATION.md), [05 Remaining problems](05_REMAINING_PROBLEMS.md).

## 1. What the project is made of

| Area | Tracked files | What it holds |
|---|---|---|
| `src/` | 301 Lua files, about 100,000 lines | The game: Rojo maps `src/shared` to ReplicatedStorage, `src/server` to ServerScriptService, `src/client` to StarterPlayerScripts, `src/worldbuild` to ServerStorage.WorldBuild |
| `tests/` | 25 | 21 Luau specs for the pure rule modules, run with the plain `luau` CLI through `tests/run.py` |
| `tools/` | 372 | Asset and check scripts by family: `blender` (pets 122, world 105, weapons 44, guardians 25, eggs 12, ugc, ui, animation, vfx, relics), `roblox` (Studio-side helper scripts), `balance`, `economy`, `vfx`, `ui`, `weapon_aura`, `check.py` |
| `assets/` | 907 (1.4 GB on disk) | Source art by subject: pets 279, weapons 140, world 106, guardians 95, eggs 81, ui 62, outfits 54, relics 45, vfx, ugc, aura, npcs |
| `design/` | 49 | The UI design system, briefs and mockups (2026-11-24) |
| `place/` | 1 | A snapshot of the place file |
| notes (the Obsidian vault is the project root) | a working-notes folder (git-excluded), numbered topic folders (`07 ...`, `08 ...`, `17 ...`, `19 ...`, `22 ...`), `Knowledge/`, `BLENDER_PROFESSIONAL_EDUCATION/` | Project knowledge and the training record |
| tool folders at the root, git-excluded | `.agents`, `.aider-desk`, `aaa-game-studio`, `skills-lock.json`, `renders/` | Other tools' skill files and local review renders: not part of the game |
| root files | `README.md`, the project-instructions file, `Qi_Aura_Simulator_Design.md`, `default.project.json`, `.gitignore`, `.github/workflows/checks.yml` | |

## 2. The Studio place (read-only inspection of the open place)
- Workspace: `Camera`, `FloatingIslands` (Folder, 19,405 parts: the world, built by the worldbuild scripts), `Terrain`. Nothing else.
- ServerStorage (29,161 descendants): `BridgeKits`, `DevStage` (26,185: the owner's development toolkit: the PDS particles kit, `AuraTestRange`, `AuraDummies`, `AuraCompare`, `AuraWorkbench`; documented in the design doc, referenced by `tools/roblox/aura_compare` and a comment in `RealmAura.lua`; NOT clutter), `EggMeshes`, `Guardians` (the five guardian models), `Outfits`, `RelicMeshes`, `TrialDummy`, `UGC_EclipseExorcist`, `WanderingMerchant`, `Weapons`, `WorldAssets` (per-island asset folders), `WorldBuild` (the builder scripts and their data).
- ReplicatedStorage: the 36 shared modules directly, plus `AuraMeshes` and `PetMeshes` (8,205 descendants of pet meshes).
- Lighting: Atmosphere, AuraBloom, AuraColorCorrection, Sky. SoundService: four SoundGroups. StarterGui and StarterPack are empty (the game builds all UI from code).
- The place holds non-script content that Rojo does not manage (`$ignoreUnknownInstances`): models, meshes, terrain, the world. Only `src/` content is moved by this overhaul.

## 3. Purpose of every `src` folder (from the code's own comments and file names)

Client (`src/client`: 15 folders and one loose module):
- `Audio` (Sfx player, SoundCatalog, PetSounds, AudioController). `Auras` (realm auras, breakthrough sequences). `Character` (outfits, poses, weapon animation clips). `Combat` (strikes, weapon auras, damage numbers, combo counter). `Cultivation` (the training/meditation/tribulation controllers). `Factions` (Murim faction UI and trials). `Guardians` (controller, animation, reactions, bars, 15 modules plus `GuardianRigs`). `Performance` (the developer perf readout). `Pets` (21 files, 25,139 lines: the pets window, codex, hatching ceremony, pen, and the pet rig/animation module). `Qinggong` (flight and run effects). `Quests` (quest tracker, tutorial, guide arrow). `Rewards` (rewards window and its pages, spin wheel, beta gift). `Shop` (store, auction, merchant). `UI` (Hud, UiKit, UiTheme and the other shared UI modules, settings, titles, feedback). `World` (ambient and world scripts: weather, culling, quality, NPC talk, records boards).
- `Quality.lua` sits alone at the client root.

Server (`src/server`, 18 domain folders): `Analytics`, `Auction`, `Combat`, `Cultivation`, `Data` (PlayerData and settings persistence), `Factions`, `Feedback`, `Guardians` (the boss state machine, egg stands, conquest book), `Outfits`, `Pets`, `Qinggong`, `Quests`, `Records`, `Rewards`, `Security` (movement guard), `Shop` (wallet, purchases, merchant), `Titles`, `World` (world config, NPCs, weather, discoveries, guide).

Shared (`src/shared`, 36 flat modules): `GameConfig` (1,370 lines; the tuning numbers), other `*Config` modules (`AuraConfig`, `RecordsConfig`, `WeatherConfig`), the pure `*Rules` modules covered by specs (pets, passes, goals, titles, auction, bounty, codex, faction, form, react, reward, spin, standing, stand, territory, trial, weather, gift, coop), data tables (`Ranks`, `Shop`, `Merchant`, `BetaGift`, `PetLore`, `PetMaps`, `WeaponMaps`, `TitleArt`, `FormClips`, `BreathRules`, `PenLayout`), `NumberFormat`, and `RemoteEvents` (the declaration of all 38 remotes).

World build (`src/worldbuild`, 13 builders, `Placements` 54 data modules, `Terrain` 8 terrain arrays): scripts the owner runs by hand in Studio to build the islands, guardians' skinned imports, outfits and territories. They are not part of the shipped game.

## 4. Dependencies between systems (measured)
- 1,167 static instance-path chains in the code; 1,018 `require` calls land on a ModuleScript; 81 are not decidable (they go through containers Rojo does not fill, e.g. `ServerStorage.EggMeshes`). **0 broken paths.**
- Require forms in use: `ReplicatedStorage:WaitForChild("X")` 413, `script.Parent:WaitForChild("X")` 159, a local alias such as `UI:WaitForChild("X")` 141 plus 4 `ui`, `script.Parent.Parent:WaitForChild("X"):WaitForChild("Y")` 139, `Server:WaitForChild(...)` 54, `serverRoot:...` 20, `WorldBuild:...:Clone()` 25.
- **Boundaries hold:** 0 requires from client to server, server to client, or shared to either. 25 shared modules are used by both sides; 7 only by the client (`TitleArt`, `PetMaps`, `FormClips`, `BreathRules`, `AuraConfig`, `PetLore`, `TerritoryRules`); 4 only by the server (`StandRules`, `ReactRules`, `CoopRules`, `TrialRules`); none are unreferenced.
- Most depended-on modules: `GameConfig` 119 files, `RemoteEvents` 64, `Ranks` 49, `UiTheme` 47, `UiKit` 44, `Sfx` 39, `Shop` 32, `Hud` 30, `Toast` 30, `PlayerData` 27, `Quality` 27, `NumberFormat` 21, `PetRules` 21. Largest fan-out: `PlayerData` 27, `CodexController` 19, `Guardian` 18, `PetService` 17, `PetController` 17.
- Remotes: 38 `RemoteEvent`s declared in `RemoteEvents.lua`, every one referenced from both a server and a client file, none used but undeclared; 0 `RemoteFunction`s.
- CollectionService tags: about 35 tag expressions; the shared ones are `GameConfig.GuardianTag` (6 files), `GameConfig.Combat.TargetTag` (5), `"HubNpc"` (5), `GameConfig.RelicTag` (3), `"NightfallArenaDummy"` (3), plus per-territory spot tags used by the builders.
- Code depends on these Studio paths by name: `workspace.FloatingIslands` (39 uses), `workspace.Guardians` (4), `workspace.WorldConfig` (10), `ServerStorage.WorldBuild` (11), `.Weapons` (7), `.EggMeshes` (5), `.TrialDummy` (5), `.Guardians`, `.Outfits`, `.RelicMeshes`, `.BridgeKits`, `ReplicatedStorage.PetMeshes` and `.AuraMeshes`.
- Require cycles: none at load time. The 13 `worldbuild` builders require each other (`WorldBuilder` <-> `CrossingBuilder` <-> `DawnspireBuilder` ...) but only inside functions, at the moment a builder runs by hand: a design smell, not a failure.

## 5. Duplication, misplacement, naming, structural problems (with evidence)
1. **`src/client/Pets/PetRig.lua` is 17,728 lines in one module**: the core builder (`build`, `buildSkinned`, `update`, effects), a `Profiles` table, 48 `Blasts.*` special-effect functions (about 3,000 lines) and 58 `do ... end` blocks (12,989 lines) each holding one pet's animation, written as blocks "so its locals are freed at its end" because a Lua chunk is limited to 200 local variables. 80 top-level locals are already forward declarations. Nine files require it. This is the project's single serious structural problem: slow to open, impossible to review, near a hard language limit.
2. **Graphics quality and performance code is scattered over five places:** `client/Quality.lua` (alone at the client root, 27 dependents), `client/Performance/PerfProbe`, and `client/World/DetailCulling`, `ShadowCulling`, `WorldQuality`.
3. `client/Character/WeaponClips.lua` (keyed weapon animation clips, 731 lines) first looked misplaced (its name says weapons, its folder says character). Revised during implementation: it is played by `PoseController` (in `Character`), read by `CombatFx` and written by a Blender generator, so it stays.
4. `client/World` mixes unrelated things (ambient life, weather, culling, quality, NPC talk, the guide, relic counter, records boards, spawn camera).
5. **Same-named modules in two folders** (deliberate but confusing): `worldbuild/Terrain/<Island>` and `worldbuild/Placements/<Island>` for 8 islands (the builders look them up by the island's name, so the equal names are the contract), and `GuardianRigs/<Id>Skinned` (client rig module) beside `worldbuild/Placements/<Id>Skinned` (placements data) for 4 guardians.
6. **Inert files:** the Tiangou v3 rig, clips and placements (`TiangouV3Skinned.lua`, `TiangouV3Clips.lua`, `Placements/TiangouV3Skinned.lua`) were written for a model that was rejected and deleted on 2026-11-24; nothing requires them. Kept for now (not proven abandoned: the owner may resume the Tiangou).
7. Large files that are legitimately large (data or builders): `WorldBuilder` 3,135, `GameConfig` 1,370, `Placements/*` (data). Large code files worth watching but not split now: `CombatFx` 1,810, `Hud` 1,604, `HatchCeremony` 1,540, `RealmAura` 1,371, `BreakthroughFx` 1,294, `Guardian` 1,185.
8. **Naming:** consistent where it matters: `*Controller.client.lua` (client entry scripts), `*Service.server.lua` (server entry scripts), `*Rules` (pure, spec-covered), `*Config`, `*Builder` (world build), `*Fx`, `*Ledger/*Stores/*Core/*Checks` (auction and records layers). Exceptions are few: a client folder `Performance` holds one script; `server/Analytics` holds `PerfService`; `server/Shop` holds game-pass and product services next to the wallet; `Rewards` holds `Codes`.
9. Folder shape: no nesting deeper than `Guardians/GuardianRigs`, `worldbuild/Placements|Terrain`. No empty folders.
10. Outside `src`: the repository root mixes the game, the knowledge vault and tool folders (above). The vault is intentional (the owner uses Obsidian on the project root), and the tool folders are git-excluded, so the tracked repository itself is already tidy (`src`, `tests`, `tools`, `assets`, `design`, `place`).

## 6. What was found NOT to be a problem (and so is left alone)
- The domain split of `src/client` and `src/server` (same names on both sides) is consistent and already matches the owner's list of categories (combat, pets, bosses/guardians, quests, shop, rewards, world, UI, audio, VFX in Auras/Combat/Qinggong, data).
- `src/shared` being flat: 36 modules named by suffix. Grouping it into subfolders was evaluated and rejected: about 420 `ReplicatedStorage:WaitForChild("X")` sites, the test harness (`tests/run.py` stages `src/shared` non-recursively) and the `@shared/X` alias would all change, for a folder of 36 well-named files. The owner's rule: avoid unnecessary nesting.
- `DevStage` and the vault folders: the owner's tools and notes.

## 7. Recommended structure and destination of each resource that moves
| From | To | Why |
|---|---|---|
| `client/Quality.lua`, `client/World/DetailCulling.client.lua`, `client/World/ShadowCulling.client.lua`, `client/World/WorldQuality.client.lua` | `client/Performance/` (beside `PerfProbe`) | one home for graphics quality, culling and the perf readout |
| `client/Character/WeaponClips.lua` | ~~`client/Combat/`~~ **not moved (revised during implementation, see [03](03_MIGRATION_LOG.md))**: played by `PoseController` in `Character`, read by `CombatFx`, written by a Blender generator and staged by `tests/run.py` at this path | |
| `client/Pets/PetRig.lua` (17,728 lines) | `client/Pets/PetRig/init.lua` (the core) + `client/Pets/PetRig/Animators/<Pet>.lua` (one per pet) + `client/Pets/PetRig/Blasts.lua` or per-blast modules | split by responsibility; `PetRig` stays the name every requirer uses (Rojo maps a folder with `init.lua` to a ModuleScript of that name) |
| (new) `tools/check_requires.py` | permanent check #7 in `tools/check.py` | every move stays verifiable |
| (new) `ARCHITECTURE/` | the reports and conventions | the architecture is documented where the code is |

Not moved (decided in section 6): `src/shared`, `worldbuild/Terrain|Placements`, the vault folders, the Tiangou v3 files, `DevStage`.

## 8. Risks of reorganizing, and how each is covered
1. **A moved module breaks a require.** Covered by `tools/check_requires.py` (it fails if any path no longer resolves), compile and lint (an unknown variable after a split shows as an unknown global), and a Studio Play run with the console read.
2. **Rojo is live-syncing into the owner's open Studio:** a move changes the place at once. Mitigation: one migration per commit, validated before the next; each is reversible with `git revert`; the place is saved after the final validation only.
3. **The tests stage files by path** (`tests/run.py` knows `client/Character/WeaponClips.lua`): updated in the same commit as the move.
4. **Runtime-only paths** (`ReplicatedStorage:WaitForChild("BeastPastures", 60)`, `workspace.FloatingIslands`) are not affected by file moves, and the validator does not claim to cover them.
5. **Behavior drift in the PetRig split** is the biggest risk. A split is mechanical (each block moves unchanged into a module that receives the same upvalues); verified by the linter (no unknown globals), by comparing the set of `PetRig.*` members and `Profiles` keys before and after, and by Play runs that spawn pets.
6. **History and backups are not deleted**: this overhaul deletes nothing (the old `PetRig.lua` becomes `PetRig/init.lua`: git keeps its history).

## 9. How this was measured
`tools/check_requires.py` (instance tree rebuilt from `default.project.json`; mutation-tested: a deliberately broken require was reported and then restored), a require-graph script (balanced-parenthesis parsing of every `require(...)`), a per-folder size count, the remote-event cross-reference, and read-only Studio queries (service children and descendant counts; nothing was changed in the place).
