# Eggbound: Cultivation Realms

A Roblox game (Luau, Rojo) about cultivating Qi, breaking through twelve realms, stealing eggs from island guardians and hatching spirit beasts.
The full design is in [Qi_Aura_Simulator_Design.md](Qi_Aura_Simulator_Design.md) (the working name of the project is Qi Aura Simulator).

## Run it

```sh
rojo serve default.project.json      # or ./tools/rojo_keepalive.sh, which restarts it if it crashes
python3 tools/check.py               # compile, lint, rojo build, the specs, sound names, no machine paths (add --fast to skip the build)
python3 tests/run.py [name ...]      # only the specs (tests/specs/<name>.spec.luau), optionally filtered
```

`check.py` also runs on every push (`.github/workflows`). Every spec file must end with `t.finish("name")`.

## Where things are

| Folder | What it holds |
| --- | --- |
| `src/server` | Server code, one folder per system (`Guardians`, `Pets`, `Shop`, `Rewards`, `Factions`, `Auction`, `Combat`, `Data`, `Security` ...). `*.server.lua` are scripts, the rest are modules they share. |
| `src/client` | Client code, the same domain folders (`UI`, `Pets`, `Combat`, `Guardians`, `Auras`, `Audio` ...). `*.client.lua` are scripts. |
| `src/shared` | Modules both sides read: `GameConfig`, the `*Rules` modules (pure functions, covered by specs), `RemoteEvents`. Rojo puts these in ReplicatedStorage. |
| `src/worldbuild` | Builders that make the islands and territories in Studio (run by hand, not in the live game); `Placements/` is generated data, `Terrain/` the terrain arrays. |
| `tests/` | `specs/*.spec.luau` (run with the `luau` CLI through `run.py`) and the tiny test harness in `env/`. |
| `tools/` | Everything that makes assets or checks things, by family: `blender` (pets, eggs, guardians, outfits, weapons, the world), `balance` and `economy` (progression and pacing sims), `ui`, `vfx`, `outfits`, `roblox` (Studio-side check scripts), `knowledge`. `check.py` is the one command above. |
| `assets/` | Source art: UI icons and frames, store art (`ui/thumbnail`), egg icons, FBX/PNG sources. Large; not all of it is checked out in CI. |
| `place/` | A snapshot of the place file (the live place is on Roblox). |
| `renders/` | Review renders and contact sheets. Local only (git-ignored). |
| `Claude Memory/`, numbered topic folders, `Knowledge/` | The project's notes (an Obsidian vault with the repository root as its root). See `Claude Memory/Vault Structure.md`. |

## Conventions that matter

- The **server decides**: damage, rewards, trades, positions and times are computed or checked in `src/server`; a remote's arguments are never trusted. New remotes are declared in `src/shared/RemoteEvents.lua` and must validate every argument.
- **Pure rules first**: a rule that needs no Instances goes in `src/shared/*Rules.lua` with a spec, and the service just applies it.
- **Sounds** are entries of `src/client/Audio/SoundCatalog.lua`, levelled by measured loudness; `check.py` fails on a name that isn't in the catalog.
- **Tuning numbers** live in `GameConfig` (and `AuraConfig`, `WeatherConfig`), not inline.
- Studio tests use a throwaway save (set `ServerStorage` attribute `StudioTestSave`) so a real save is never touched.
