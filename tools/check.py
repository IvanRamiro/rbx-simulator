#!/usr/bin/env python3
"""The one command to run before a commit or a release (CI runs the same thing):

    python3 tools/check.py          # everything
    python3 tools/check.py --fast   # skip the rojo build

What it checks, in order (it needs `luau`, `luau-compile`, `luau-analyze` and `rojo` on the PATH):
  1. compile   every Lua file under src/ compiles
  2. lint      luau-analyze reports no lint warning (unused variable, shadowing, a function that sometimes returns nothing ...) and no
               unknown GLOBAL that is not a Roblox engine one (that is how a misspelt or stale variable shows up). The analyzer has no Roblox
               type definitions here, so its type errors are noise and are ignored: only lint warnings and unknown globals count.
  3. build     `rojo build` of default.project.json succeeds
  4. tests     tests/run.py: the shared rule modules (ranks, pets, spins, auction, weather, codex, factions, config integrity)
  5. hygiene   no machine path (a macOS home folder) in src/, the design doc or the project file; no tracked FBX that embeds the home
               path of the Mac it runs on (worked out at run time: no user name is stored in this file)
Exit code 0 = all passed. The FBX part only runs where the FBX files are checked out (CI checks out src/ and tests/ only).
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME_PATH = os.path.expanduser("~").encode()  # this Mac's home folder, e.g. what an exported FBX would remember (nothing is stored in the file)
ENGINE_GLOBALS = {
    "CFrame", "Color3", "ColorSequence", "ColorSequenceKeypoint", "DateTime", "Enum", "Font", "Instance", "NumberRange", "NumberSequence",
    "NumberSequenceKeypoint", "OverlapParams", "PhysicalProperties", "Random", "RaycastParams", "Region3", "TweenInfo", "UDim", "UDim2",
    "Vector2", "Vector3", "game", "script", "task", "warn", "workspace", "Axes", "Faces", "BrickColor", "Ray", "Rect", "Vector3int16",
    "Vector2int16", "Region3int16", "PathWaypoint", "SharedTable", "CatalogSearchParams", "DockWidgetPluginGuiInfo", "shared", "plugin",
    "tick", "time", "utf8", "typeof", "require", "spawn", "delay", "wait", "elapsedTime", "settings", "stats", "version", "printidentity",
}
results = []


def run(command, **kwargs):
    return subprocess.run(command, cwd=REPO, capture_output=True, text=True, **kwargs)


def record(name, ok, detail=""):
    results.append((name, ok, detail))
    print(("PASS  " if ok else "FAIL  ") + name + (("  " + detail) if detail else ""))


def lua_files():
    found = []
    for folder, _, files in os.walk(os.path.join(REPO, "src")):
        found += [os.path.relpath(os.path.join(folder, f), REPO) for f in files if f.endswith(".lua")]
    return sorted(found)


def check_tools():
    missing = [t for t in ("luau", "luau-compile", "luau-analyze", "rojo") if not shutil.which(t)]
    if missing:
        print("missing tools on the PATH: " + ", ".join(missing))
        sys.exit(2)


def check_compile(files):
    bad = []
    for path in files:
        if run(["luau-compile", "--text", path]).returncode != 0:
            bad.append(path)
    record("compile", not bad, f"{len(files)} files" if not bad else "does not compile: " + ", ".join(bad[:5]))


def check_lint(files):
    out = run(["luau-analyze", "--mode=nonstrict", "--formatter=plain"] + files)
    text = out.stdout + out.stderr
    lint, unknown = [], set()
    for line in text.splitlines():
        if "(W" not in line or ": (" not in line:
            continue
        if "TypeError" in line or "UnknownType" in line:
            match = re.search(r"Unknown global '([^']+)'", line)
            if match and match.group(1) not in ENGINE_GLOBALS:
                unknown.add(match.group(1))
            continue
        lint.append(line.strip())
    ok = not lint and not unknown
    detail = f"{len(files)} files"
    if lint:
        detail = f"{len(lint)} lint warnings, first: {lint[0]}"
    elif unknown:
        detail = "unknown globals (a misspelt or stale name?): " + ", ".join(sorted(unknown))
    record("lint", ok, detail)


def check_build():
    out = os.path.join(tempfile.mkdtemp(prefix="qi_build_"), "check.rbxlx")
    result = run(["rojo", "build", "default.project.json", "-o", out])
    record("rojo build", result.returncode == 0, "" if result.returncode == 0 else (result.stderr or result.stdout).strip()[:200])
    shutil.rmtree(os.path.dirname(out), ignore_errors=True)


def check_tests():
    result = run([sys.executable, "tests/run.py"])
    summary = [l for l in result.stdout.splitlines() if "spec files passed" in l]
    record("tests", result.returncode == 0, summary[0].strip() if summary else result.stdout.strip()[-200:])
    if result.returncode != 0:
        print("\n".join("      " + l for l in result.stdout.splitlines()))


def check_hygiene():
    hits = run(["git", "grep", "-I", "-n", "-E", r"/Users/[A-Za-z]+|C:\\Users", "--", "src", "Qi_Aura_Simulator_Design.md", "default.project.json"])
    lines = hits.stdout.strip().splitlines()
    record("no machine paths in src and docs", not lines, lines[0][:140] if lines else "")
    tracked = run(["git", "ls-files", "-z", "*.fbx"]).stdout.split("\0")
    present = [f for f in tracked if f and os.path.exists(os.path.join(REPO, f))]
    leaks = []
    for f in present:
        with open(os.path.join(REPO, f), "rb") as fh:
            if HOME_PATH in fh.read():
                leaks.append(f)
    if present:
        record("no FBX embeds this Mac's home path", not leaks, f"{len(present)} FBX" if not leaks else f"{len(leaks)} leak it, first {leaks[0]}")
    else:
        print("SKIP  FBX path scan (no FBX files checked out here)")


def main(argv):
    check_tools()
    files = lua_files()
    check_compile(files)
    check_lint(files)
    if "--fast" not in argv:
        check_build()
    check_tests()
    check_hygiene()
    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)} of {len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
