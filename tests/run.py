#!/usr/bin/env python3
"""Runs the Luau specs in tests/specs with the plain `luau` command-line tool (no Studio, no Roblox).

    python3 tests/run.py                # every spec
    python3 tests/run.py ranks codex    # only specs whose file name contains one of these words
    python3 tests/run.py --keep         # keep the staging folder and print where it is (to debug a failing spec)

How it works: the modules in src/shared are copied to a temporary folder with ONE header line prepended (no newline added, so line numbers in
an error still match the real file). The header binds the Roblox globals the modules use at load time (game, Color3, Random, ...) to the
stand-ins in tests/env/globals.luau. `game:GetService("ReplicatedStorage"):WaitForChild("Ranks")` then returns the alias path "@shared/Ranks",
so the modules' own `require(...)` calls load each other for real. src/ is never modified. Exit code 0 = every spec passed.
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
GLOBALS = [
    "game", "workspace", "Color3", "Vector3", "Vector2", "CFrame", "Enum", "UDim", "UDim2", "Instance", "TweenInfo", "NumberRange",
    "NumberSequence", "ColorSequence", "NumberSequenceKeypoint", "ColorSequenceKeypoint", "Random", "DateTime", "task", "warn",
]
HEADER = 'local __G = require("@env/globals"); local ' + ", ".join(GLOBALS) + " = " + ", ".join("__G." + g for g in GLOBALS) + "; "


def stage(root):
    shared = os.path.join(root, "shared")
    os.makedirs(shared)
    for name in sorted(os.listdir(os.path.join(REPO, "src", "shared"))):
        if not name.endswith(".lua"):
            continue
        with open(os.path.join(REPO, "src", "shared", name), encoding="utf-8") as f:
            source = f.read()
        with open(os.path.join(shared, name), "w", encoding="utf-8") as f:
            f.write(HEADER + source)  # same line as the module's first line: line numbers are unchanged
    # the keyed combat clips (data only, no Roblox globals): lives in the client folder, staged beside the shared modules so a spec can check them
    clips = os.path.join(REPO, "src", "client", "Character", "WeaponClips.lua")
    with open(clips, encoding="utf-8") as f:
        source = f.read()
    with open(os.path.join(shared, "WeaponClips.lua"), "w", encoding="utf-8") as f:
        f.write(HEADER + source)
    shutil.copytree(os.path.join(HERE, "env"), os.path.join(root, "env"))
    shutil.copytree(os.path.join(HERE, "specs"), os.path.join(root, "specs"))
    with open(os.path.join(root, ".luaurc"), "w") as f:
        f.write('{ "aliases": { "shared": "./shared", "env": "./env" } }')


def main(argv):
    keep = "--keep" in argv
    words = [a for a in argv if not a.startswith("--")]
    luau = shutil.which("luau")
    if not luau:
        print("the `luau` command-line tool is not installed (brew install luau)")
        return 2
    root = tempfile.mkdtemp(prefix="qi_tests_")
    try:
        stage(root)
        specs = sorted(n for n in os.listdir(os.path.join(root, "specs")) if n.endswith(".spec.luau"))
        if words:
            specs = [s for s in specs if any(w in s for w in words)]
        if not specs:
            print("no specs match")
            return 2
        failed = 0
        for spec in specs:
            result = subprocess.run([luau, os.path.join("specs", spec)], cwd=root, capture_output=True, text=True, timeout=120)
            out = (result.stdout + result.stderr).strip()
            status = "ok  " if result.returncode == 0 else "FAIL"
            if result.returncode != 0:
                failed += 1
            print(f"{status} {spec}")
            if out:
                print("\n".join("     " + line for line in out.splitlines()))
        print(f"\n{len(specs) - failed} of {len(specs)} spec files passed")
        if keep:
            print(f"staging kept at {root}")
        return 1 if failed else 0
    finally:
        if not keep:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
