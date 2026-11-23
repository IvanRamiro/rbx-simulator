# Tests

Plain-Luau tests for the rule modules in `src/shared` (ranks, pets and their odds, spins, daily rewards, the Auction House, the Wandering
Merchant, weather, the Codex, factions) and for the integrity of `GameConfig` (egg pools add up, every pet has lore, every faction is
complete). They run with the `luau` command-line tool, with no Studio and no Roblox:

    python3 tests/run.py              # all specs
    python3 tests/run.py pets codex   # only specs whose file name contains one of these
    python3 tests/run.py --keep       # keep the staging folder (to debug a failing spec)
    python3 tools/check.py            # tests plus compile, lint, rojo build and hygiene: what CI runs

How: `run.py` copies `src/shared` to a temporary folder with one header line prepended to each module (no line is added, so error line
numbers match the real file). The header binds the Roblox globals the modules use while loading (`game`, `Color3`, `Random`, ...) to the
stand-ins in `env/globals.luau`; `game:GetService("ReplicatedStorage"):WaitForChild("Ranks")` then returns the alias `@shared/Ranks`, so the
modules' own `require(...)` calls load each other for real. `src/` is never touched.

Add a spec: a file `tests/specs/<name>.spec.luau` that starts with `local t = require("@env/t")`, loads modules with
`require("@shared/<Module>")`, uses `t.test(name, fn)` with `t.eq`, `t.near`, `t.ok`, `t.falsy`, `t.throws`, and ends with
`t.finish("<name>")`. `smoke.spec.luau` lists every shared module: add a new module there too.

Limits: `Random` here is a deterministic stand-in, not Roblox's generator, so test ranges and proportions over many draws, never exact
Roblox sequences. Modules that need a real player, instance or service (anything under `src/server` and `src/client`) are not covered; they
need Studio (see `tools/roblox/`). A test that has never failed proves little: after writing one, break the code on purpose in a scratch copy
and make sure it notices.
