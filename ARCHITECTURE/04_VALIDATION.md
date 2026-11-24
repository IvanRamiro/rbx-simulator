# 04 Validation results

Everything here was run on 2026-11-24 against the migrated tree. "Not tested" lists what was NOT exercised, so a pass is never read as more than it is.

## Static validation (`python3 tools/check.py`, 8 of 8 pass after every step)
| Check | Result |
|---|---|
| compile | 359 files (301 before the split; the 58 new files are the PetRig pieces) |
| lint | 359 files, 0 warnings, 0 unknown globals (the analyzer ignores a global that is only written through a field, so the PetRig split was checked a second way: see below) |
| rojo build | succeeds |
| tests | 21 of 21 spec files pass |
| sound names | every name the client plays exists in the catalog |
| **require paths resolve** (new) | 1,171 chains walked, 1,019 requires landing on a ModuleScript, 81 not decidable (through containers Rojo does not fill), **0 broken** |
| machine paths | none in src and docs |
| FBX path scan | 182 FBX clean |

Second static check for the split (not part of `check.py`, used by the migration): the compiler's bytecode was read for every global each new file touches, and compared with the globals the original file used: after the shared names were supplied through `K`, 0 differ; and every name an early animator gets from `K` comes from an earlier animator (0 order violations, 0 shadowed names).

## Dependency validation
- Boundaries: 0 requires client to server, server to client, shared to either (measured before and unchanged: no server or shared file was edited).
- Remotes: 38 declared, each used by a client and a server file, 0 used but undeclared, 0 RemoteFunctions: unchanged (`shared/RemoteEvents.lua` and every server script untouched by the overhaul).
- Asset IDs, animation IDs, sound IDs, CollectionService tags: not touched (no ID, tag or catalog entry changed; `check.py`'s sound-name check passes).
- ObjectValue and instance-reference relationships: the moved scripts keep the same parents' names for everything they find by name outside `client/Performance` and `Pets/PetRig`; the path validator confirms every static chain.

## The PetRig split: proof that behavior is unchanged
1. **Structure snapshot taken in the live game before the change and again after** (a probe script in PlayerScripts, so it saw the live module): the module's 14 top-level members and their types, 63 profiles, and a checksum of every profile's data (functions counted, not compared) are **identical**; 63 of 63 profiles have an `Animate` function both times. (The snapshot is saved in `ARCHITECTURE/evidence/petrig_live_snapshot.txt`; the after-run printed the same 67 lines, compared with `diff`: no difference.)
2. **63 of 63 pet portraits built** through the real portrait code on the new module (`Portraits.pet`), 0 errors.
3. **Pets live:** the two equipped pets (Aqua Wisp, Nine-Tail Moonfox) stood beside the player and animated; the Beta Gift window's three pets showed different poses between two screenshots (the rig's `update` runs).
4. **Console:** no error and no "infinite yield" in any run after the final fix.
5. **A bug the first version had** (20 pet modules were missing `Blasts`) was found by the Play run, not by lint, fixed, and re-verified by 1, 2 and 4.

## Functional regression (Play, Studio, test save `ArchM1_20261124`, a developer account)
| System | What was done | Result |
|---|---|---|
| Player loading, progression, data saving | fresh session after a previous one | equipped pets, island, rank and quest step all loaded from the save |
| Inventory and equipment | Equip best (built earlier today) equipped both pets; they persisted to the next session | pass |
| Pets: following and interaction | two pets following the player; the Pets window; EQUIP BEST and the search (earlier today) | pass |
| UI navigation | Shop, Pets, Codex, Titles, Settings, Feedback, Rewards and Beta Gift windows each opened by a real click (a watcher logged each open); Robes toggled the outfit; Spin showed its notice | pass |
| Boss encounter | the Lantern Wyrm woke and was weakened over the server's combat path | pass (state Guardian, then Weakened) |
| Rewards and quests | the conquest reward ("Conquest! Abyssal Lantern Wyrm"), the rank-up rewards (930 stones, Qi x30), a new title | pass |
| VFX and animation | the rank-up breakthrough ran (`[Breakthrough] DivineInitiate own: 19 emitters, 2 beams, 6 trails, 8 parts, 2 billboards`); pets animated | pass |
| Client-server communication | EquipBestPetsEvent round trips, the guardian state attribute, the data save | pass |
| Console | clean in the final runs (the only lines are the editor plugin's notice and a long-standing asset warning, `rbxassetid://203785492`, present before the overhaul) | pass |

## Not tested (said plainly)
Server code was not edited, so server-side systems were not retested beyond the paths above. Not exercised this time: combat with a purchased weapon (the test account has none), the egg theft and chase (done earlier today with the same client code), faction trials and wars, the Auction House, the Wandering Merchant, the Spin Wheel's wheel itself, outfit changes beyond the toggle, two-player interactions, and every one of the 63 pets' individual animation states (their code is byte-identical and their profile data is checksum-identical; their runtime behavior was sampled on four pets, not all). A transient engine message about asset `130874849807693` ("content representation is being generated") appeared in one early run and did not recur; its source was not identified.
