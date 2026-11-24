# 03 Migration log

Every change below is its own commit on branch `architecture-overhaul` (pushed). **Rollback of any step:** `git revert <commit>`; Rojo re-syncs the place from the working tree within seconds. Nothing was deleted: moved files keep their history (`git mv`), and the old `PetRig.lua` became `PetRig/init.lua` (history follows).

## Step 0: a way to prove a move is safe (commit b420fb8)
- New `tools/check_requires.py`: rebuilds Roblox's instance tree from `default.project.json` and walks every `script...`, `game:GetService(...)`, `ReplicatedStorage...` and local-alias chain (1,167 chains in the code at the start, 1,018 of them `require` calls) against it. It is check #7 of `tools/check.py`.
- Baseline before any move: 0 broken paths. Two false alarms were fixed in the checker (a `:WaitForChild("X", 60)` with a timeout waits for something made at run time; a dynamic island name). Mutation test: a deliberately broken require (`PetRig` -> `PetRigX`) was reported with the exact missing child, then restored.
- The first report of the original architecture is [01](01_ORIGINAL_ARCHITECTURE_REPORT.md) (written before any file moved).

## M1: graphics quality and performance code together (commit f0de805)
- Moved with `git mv` into `client/Performance/`: `Quality.lua` (was loose at the client root), `DetailCulling.client.lua`, `ShadowCulling.client.lua`, `WorldQuality.client.lua` (were in `client/World/`). `PerfProbe` was already there.
- References updated by a scripted rewrite: 27 files (26 `script.Parent.Parent:WaitForChild("Quality")` -> `...:WaitForChild("Performance"):WaitForChild("Quality")`, the 4 files now inside `Performance/` -> `script.Parent:WaitForChild("Quality")`, and `HatchCeremony`'s alias form). The validator reported exactly the 28 expected broken paths after the move and none after the rewrite.
- Docs updated: the design doc's mentions (3 places).
- Studio: Rojo synced the move into the open place (checked: `Performance` holds the five items, the old locations are gone); Play run: no errors, no "infinite yield".

## Decision reversed during implementation: `WeaponClips` stays where it is
The report proposed moving `client/Character/WeaponClips.lua` to `Combat`. On inspection it is played by `PoseController` (in `Character`) and read by `CombatFx` (in `Combat`), and it is written by a Blender generator and staged by `tests/run.py` at its current path. A move would only swap one cross-folder dependency for another and force edits to the generator and the test harness for no gain. Not moved; recorded in [01](01_ORIGINAL_ARCHITECTURE_REPORT.md) section 7.

## M3: `PetRig.lua` (17,728 lines) split into a folder module (commit 5ec56bb)
- **Before:** one ModuleScript with its core builder, a `Profiles` table, 48 special-effect functions and 58 pets' `do ... end` animation blocks (written as blocks to stay under Luau's 200-locals-per-function limit; 80 top-level locals were already forward declarations). The linter reported "code is too complex to typecheck" on it.
- **After:** `client/Pets/PetRig/` with `init.lua` (1,765 lines: header, `K` (the shared helpers), the loaders, `Profiles`, `build`, `buildSkinned`, `update`, `nova`), `Blasts.lua` (2,981: the special effects), `Animators/` (36 files, one per early pet) and `Pets/` (21 files, one per later pet with its own profile). 59 files, 18,195 lines in all (the extra lines are indentation and 59 two-line headers). `PetRig` keeps its name and shape: Rojo makes a folder with `init.lua` a ModuleScript of that name, so the nine files that require it did not change.
- **Method (so it can be reproduced and audited):** a script cut the original at its natural seams (col-0 `do ... end` blocks, `local Blasts = {}`, `local function burst`, the first tail block), wrapped each block unchanged in `return function(K) ... end`, and generated the loaders. The set of shared names each file needs from `K` was found by iterating the analyzer's unknown-global report AND the compiler's bytecode (`luau-compile --text`: every `GETIMPORT`/`GETGLOBAL` name not used by the original file). The first version of the check used only the analyzer and missed that 20 pet modules write `Blasts.X = ...` (a global written through a field is not reported); the Play run caught it (`attempt to index nil with 'RingOfYears'`), and the compiler-based check now covers it.
- **Order check:** every name an animator receives from `K` is provided by an earlier animator (0 violations), and no name is declared by two units (0 shadowed).
- **What did not change:** every line of animation and effect code (moved verbatim, indented 4 spaces; `script.Parent` in one file now reads `PetsFolder`, the same folder).
- **Docs:** the design doc's pointer and the conventions in [02](02_NEW_STRUCTURE.md) (a new pet is a new file, not another block).
- **Validator update:** `init.lua` is recognised as the folder's own module.

## Not done (and why), see [05](05_REMAINING_PROBLEMS.md)
Nesting `src/shared` (about 420 sites, the test harness reads it non-recursively); renaming `Terrain`/`Placements` pairs (the name equality is the builders' contract); splitting `WorldBuilder` (3,135 lines, a by-hand tool) or the other 1,000+-line files; deleting anything.
