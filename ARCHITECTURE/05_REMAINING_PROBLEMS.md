# 05 Remaining architectural problems and recommendations

Honest list, ordered by value. None blocks the game; each was left alone on purpose or out of scope.

## Remaining problems
1. **Six PetRig pieces still make the analyzer say "type inference failed to complete":** `Animators/TimekeeperTortoise` and `Pets/AstralWhale`, `NinefoldSpiritSerpent`, `OriginSerpent`, `StormBumblebee`, `ThunderclawDrake` (the last is also the biggest piece, 632 lines). Their `animate` functions run several hundred lines each. The original single file had two such messages; the file-level problem is solved, the function-level one is not (type errors are ignored by `check.py`, so nothing fails).
2. **`PetRig/Blasts.lua` is 2,981 lines** (48 independent effect functions plus helpers). It is one concern in one file, so it was kept whole; it could become one file per blast if it grows.
3. **`worldbuild/WorldBuilder.lua` is 3,135 lines** and the 13 builders require each other lazily (inside functions, at run time: `WorldBuilder` <-> `CrossingBuilder` <-> `DawnspireBuilder`). Not a load-time cycle, but a hidden coupling. They are tools the owner runs by hand, so the risk is low.
4. **Other files over 1,000 lines of live code:** `CombatFx` 1,810, `Hud` 1,604, `HatchCeremony` 1,540, `RealmAura` 1,371, `BreakthroughFx` 1,294, `Guardian` 1,185 (and `GameConfig` 1,370 and the `Placements/*` data, which are data). Each is one feature; splitting would need the same care as the PetRig split (and the same proof).
5. **`src/shared` is 36 flat modules.** Navigable by suffix, but a folder per kind (`Config`, `Rules`, `Data`) would read better. Blocked by about 420 `ReplicatedStorage:WaitForChild("X")` sites and the test harness (`tests/run.py` stages it non-recursively); a codemod plus a harness change would do it.
6. **`client/World` is still a catch-all** (ambient life, weather, NPC talk, the guide, relic counter, records boards, spawn camera, egg glow, bridge barriers): 11 files with little in common. A split into `World` (ambience) and a records/NPC folder is possible once the owner agrees which belongs where.
7. **Inert files for a rejected model:** the Tiangou v3 rig, clips and placements (`TiangouV3Skinned.lua` x2, `TiangouV3Clips.lua`) and half-finished generator edits (`tiangou_v3.py`, `tiangou_v3_model.py` modified; `tiangou_v3_clay.py` untracked). Not deleted: not proven abandoned (the owner may resume the Tiangou).
8. **Same-named pairs** (`Terrain/<Island>` + `Placements/<Island>`, `GuardianRigs/<Id>Skinned` + `Placements/<Id>Skinned`): deliberate, but a newcomer will think they are duplicates. A one-line comment at the top of each folder's first file would help.
9. **The place file** holds 29,000 development instances (`ServerStorage.DevStage`, the owner's toolkit): not shipped to players but it makes every save and publish heavier (already noted in the release checklist).
10. **The repository root** mixes the game, the knowledge vault, a training-notes folder and git-excluded tool folders. Intentional (the vault is the project root), but a newcomer opening the folder meets 22 visible entries. Not changed.
11. **Not deleted, by rule:** nothing was removed in this overhaul; the previous cleanup's removals are in git history.

## Recommendations for the future
- Keep `python3 tools/check.py` mandatory before every commit (CI already runs it); the path check is what makes further moves cheap.
- Split the largest `animate` functions (1) when a pet is next edited, not as a separate project.
- When the owner next adds many shared modules, do the `src/shared` grouping (5) with a codemod and the harness change in one step.
- Give each new pet its own file under `PetRig/Pets/` (the convention is in [02](02_NEW_STRUCTURE.md)), never another block in `init.lua`.
- Consider a small Studio-side check that walks every ModuleScript under PlayerScripts and requires it in a test place, to catch run-time-only paths (the static check cannot see `ReplicatedStorage:WaitForChild("BeastPastures", 60)`-style waits).
