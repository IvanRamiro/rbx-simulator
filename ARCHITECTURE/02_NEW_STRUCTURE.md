# 02 New structure and conventions

After the overhaul of 2026-11-24 (branch `architecture-overhaul`, merged into `mvp-core-loop`). The original is in [01](01_ORIGINAL_ARCHITECTURE_REPORT.md); what changed and why is in [03](03_MIGRATION_LOG.md).

## The source tree (what Rojo builds from `default.project.json`)

```
src/
  shared/        -> ReplicatedStorage          36 flat modules: *Config, *Rules (pure, covered by specs), data tables, RemoteEvents
  server/        -> ServerScriptService        18 domain folders; *Service.server.lua are entry scripts, the rest are modules
  client/        -> StarterPlayer.StarterPlayerScripts
    Audio/ Auras/ Character/ Combat/ Cultivation/ Factions/ Guardians/ Qinggong/ Quests/ Rewards/ Shop/ UI/ World/
    Performance/   graphics quality and the performance readout, together:
                   Quality.lua  PerfProbe  DetailCulling  ShadowCulling  WorldQuality          (new home, M1)
    Pets/          the pets window, codex, hatching, pen ... and
      PetRig/      the pets' rig and animation, a FOLDER MODULE (M3):
        init.lua       the builder (build, buildSkinned, update, nova), the Profiles table, the loaders
        Animators/     one file per pet whose animation was written before the per-pet convention (36)
        Pets/          one file per pet written under the per-pet convention: its animation AND its profile (21)
        Blasts.lua     the pets' special effects (Blasts.*) and their helpers
    Guardians/     controller, animation, reactions, bars, and GuardianRigs/ (one rig module and one clips module per guardian)
  worldbuild/    -> ServerStorage.WorldBuild   13 builders the owner runs by hand, Placements/ (54 data modules), Terrain/ (8)
tests/           21 specs for src/shared, run by tests/run.py with the plain `luau` CLI
tools/           check.py (the one command), check_requires.py (path validator), and asset/check scripts by family
ARCHITECTURE/    these documents
design/          the UI design system, briefs, mockups
```

Folders are named for the feature they serve and exist on both sides when both sides have code for it (`Pets`, `Guardians`, `Combat`, `Shop`, `Quests`, `Rewards`, `World`, `Cultivation`, `Qinggong`, `Factions`); a side-only folder holds what only that side has (client: `Audio`, `Auras`, `Character`, `Performance`, `UI`; server: `Data`, `Security`, `Records`, `Titles`, `Outfits`, `Feedback`, `Analytics`, `Auction`).

## Naming conventions (already followed; now written down)
| Pattern | Meaning |
|---|---|
| `Name.client.lua` / `Name.server.lua` | an entry script (a LocalScript / Script): `*Controller` on the client, `*Service` on the server |
| `Name.lua` | a module: `*Rules` pure and spec-covered, `*Config` tuning numbers, `*Builder` world build, `*Fx` effects, `*Book`/`*Ledger`/`*Stores`/`*Core`/`*Checks` the layers of a persisted feature |
| `Folder/init.lua` | the folder IS the module of that name; its other files are private pieces (used by PetRig) |
| `Placements/<Id>`, `Terrain/<Island>` | world-build data keyed by the island's or guardian's id: the name equality is the contract the builders use |
| `GuardianRigs/<Id>Skinned` + `<Id>Clips` | a guardian's client rig and its generated clips; `worldbuild/Placements/<Id>Skinned` is the import data for the same id |

## Rules of the architecture (kept by `tools/check.py`)
1. **Boundaries:** client code never requires server modules and the reverse; `shared` requires neither side. (0 violations when measured.)
2. **Every remote is declared once** in `shared/RemoteEvents.lua`, and validated on the server.
3. **Every require path must exist** in the tree Rojo builds: `tools/check_requires.py` (check #7 of `tools/check.py`) fails when a move leaves a path dangling.
4. **Pure rules go in `shared/*Rules.lua` with a spec**; tuning numbers go in `GameConfig` and its siblings.
5. **A module in the same folder** is required as `script.Parent:WaitForChild("Name")`, one in another folder as `script.Parent.Parent:WaitForChild("Folder"):WaitForChild("Name")`, a shared one as `ReplicatedStorage:WaitForChild("Name")`.

## How to add things
- **A new pet:** a new file `client/Pets/PetRig/Pets/<PetId>.lua` containing `return function(K) ... end` (copy any neighbour): it registers `PetRig.Profiles.<PetId>` and its animation, and takes shared helpers from `K` (`pose`, `tweenAfter`, `smoothstep`, `SPARKLE`, `dropToGround`, `addStance`, `emitter`, `Blasts` ...); add its name to the list at the end of `PetRig/init.lua`. (Do not add another block to `init.lua`.)
- **A new guardian:** `GameConfig.Guardians.<Id>`, the model's import, `worldbuild/Placements/<Id>Skinned.lua`, `client/Guardians/GuardianRigs/<Id>Skinned.lua` + `<Id>Clips.lua`, sound entries, voices in `GuardianController`.
- **A new remote:** the name in `shared/RemoteEvents.lua`, a validated handler on the server, a client sender.
- **A new graphics-quality or culling script:** `client/Performance/`.
- **Before any commit:** `python3 tools/check.py` (add `--fast` to skip the build). It compiles, lints, builds with Rojo, runs the specs, checks sound names, resolves every path, and scans for machine paths.
