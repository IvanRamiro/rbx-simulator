#!/usr/bin/env python3
"""Checks that every static module/instance path the code walks exists in the tree Rojo builds from default.project.json.

    python3 tools/check_requires.py            # exit code 0 = every path resolves

Why: `luau-analyze` knows nothing about Roblox's instance tree, so a require such as
`require(script.Parent.Parent:WaitForChild("Quality"))` still compiles and lints after `Quality.lua` is moved, and only fails when Studio runs it
(an "Infinite yield possible" warning and a script that never starts). Moving files is only safe with this check.

How it works: the folders and files under every `$path` of the Rojo project are turned into a tree of instances (a folder is a Folder; `Name.lua`
a ModuleScript; `Name.server.lua` a Script; `Name.client.lua` a LocalScript; a folder holding `init.lua` is a ModuleScript with children), the
same names Rojo gives them. Then every chain written in the code as `script`, `script.Parent...`, `game:GetService("X")`, `game.X.Y` or a local
alias (`local UI = script.Parent.Parent:WaitForChild("UI")`) followed by `.Parent`, `:WaitForChild("Name")` or `.Name` steps is walked, and each
`:WaitForChild` / `.Name` step must find its child in the tree. A chain that passes through a container Rojo does not fill (`ServerStorage.EggMeshes`,
`workspace`, a player's gui) is not checked past that point, and `:FindFirstChild` is never checked (it is how the code asks for optional things).
Also checked: a `require(...)` whose chain resolves must land on a ModuleScript.
"""
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVICES = {"ReplicatedStorage", "ServerScriptService", "ServerStorage", "StarterPlayer", "StarterGui", "StarterPack", "Workspace",
            "Players", "Lighting", "SoundService", "TweenService", "RunService", "UserInputService", "CollectionService", "Debris"}


class Node:
    def __init__(self, name, cls, path=None, static=False):
        self.name, self.cls, self.path, self.static = name, cls, path, static
        self.parent, self.children = None, {}

    def add(self, child):
        child.parent = self
        self.children[child.name] = child
        return child

    def full(self):
        parts, n = [], self
        while n and n.parent:
            parts.append(n.name)
            n = n.parent
        return ".".join(reversed(parts))


def lua_name(filename):
    base = filename
    for suffix, cls in ((".server.lua", "Script"), (".client.lua", "LocalScript"), (".lua", "ModuleScript"), (".luau", "ModuleScript")):
        if base.endswith(suffix):
            return base[: -len(suffix)], cls
    return None, None


def build_dir(node, directory):
    """Fills `node` (already created) from a directory, Rojo style."""
    entries = sorted(os.listdir(directory))
    for entry in entries:
        full = os.path.join(directory, entry)
        if os.path.isdir(full):
            child = node.add(Node(entry, "Folder", full, static=True))
            init = next((i for i in ("init.lua", "init.server.lua", "init.client.lua") if os.path.exists(os.path.join(full, i))), None)
            if init:
                child.cls = {"init.lua": "ModuleScript", "init.server.lua": "Script", "init.client.lua": "LocalScript"}[init]
            build_dir(child, full)
        else:
            name, cls = lua_name(entry)
            if name and not name.startswith("init"):
                node.add(Node(name, cls, full, static=True))


def build_tree():
    project = json.load(open(os.path.join(REPO, "default.project.json"), encoding="utf-8"))
    root = Node("game", "DataModel", static=False)

    def walk(node, spec):
        for key, value in spec.items():
            if key.startswith("$") or not isinstance(value, dict):
                continue
            child = node.add(Node(key, value.get("$className", "Folder"), static=False))
            if "$path" in value:
                child.static = True
                build_dir(child, os.path.join(REPO, value["$path"]))
            walk(child, value)

    walk(root, project["tree"])
    return root


def file_node(root, path):
    rel = os.path.relpath(path, REPO)

    def find(node):
        if node.path and os.path.abspath(node.path) == os.path.abspath(path):
            return node
        for c in node.children.values():
            r = find(c)
            if r:
                return r
        return None

    return find(root), rel


STEP = r'(?:\.Parent|:WaitForChild\("[A-Za-z0-9_]+"(?:\s*,\s*[0-9.]+)?\)|:FindFirstChild\("[A-Za-z0-9_]+"(?:\s*,\s*(?:true|false))?\)|\.[A-Za-z_][A-Za-z0-9_]*)'
BASE = r'(?:script|game:GetService\("[A-Za-z]+"\)|game\.[A-Za-z]+|[A-Za-z_][A-Za-z0-9_]*)'
CHAIN = re.compile(r"(?<![A-Za-z0-9_.:\"'])(" + BASE + r")((?:" + STEP + r")+)")
STEP_RE = re.compile(r'\.Parent|:WaitForChild\("([A-Za-z0-9_]+)"|:FindFirstChild\("([A-Za-z0-9_]+)"|\.([A-Za-z_][A-Za-z0-9_]*)')
ALIAS = re.compile(r"^\s*local\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(" + BASE + r"(?:" + STEP + r")*)\s*(?:--.*)?$", re.M)


def resolve(root, me, aliases, base, steps):
    """Returns (node or None, problem or None, stopped): None node with no problem means 'cannot tell, skip'."""
    node = None
    if base == "script":
        node = me
    elif base.startswith("game:GetService("):
        node = root.children.get(re.search(r'"([A-Za-z]+)"', base).group(1))
    elif base.startswith("game."):
        node = root.children.get(base[5:])
    elif base in aliases:
        node = aliases[base]
    elif base in SERVICES and base in root.children:
        node = root.children[base]
    if node is None:
        return None, None
    for m in STEP_RE.finditer(steps):
        whole = m.group(0)
        if whole == ".Parent":
            node = node.parent
            if node is None:
                return None, None
            continue
        wait, find, dot = m.group(1), m.group(2), m.group(3)
        if find or (wait and "," in m.group(0) + steps[m.end():m.end() + 12].split(")")[0]):
            return None, None  # optional lookups and waits with a timeout (for things made at run time) are never checked
        name = wait or dot
        if name in ("Name", "ClassName", "Parent", "Clone", "Destroy", "Source"):
            return None, None
        if not node.static and not (node.cls in ("Folder", "ModuleScript", "Script", "LocalScript") and node.path):
            child = node.children.get(name)
            if child is None:
                return None, None  # a container Rojo does not fill: dynamic
        child = node.children.get(name)
        if child is None:
            if wait or (dot and node.static and node.cls == "Folder"):
                return None, f'"{name}" is not a child of {node.full() or node.name}'
            return None, None
        node = child
    return node, None


def check():
    root = build_tree()
    problems, checked, requires_ok, skipped = [], 0, 0, 0
    for d, _, files in os.walk(os.path.join(REPO, "src")):
        for f in files:
            if not f.endswith(".lua"):
                continue
            path = os.path.join(d, f)
            me, rel = file_node(root, path)
            text = open(path, encoding="utf-8").read()
            if me is None:
                problems.append(f"{rel}: not part of the Rojo tree (is its folder mapped in default.project.json?)")
                continue
            aliases = {}
            for _ in range(6):  # aliases can refer to earlier aliases
                for m in ALIAS.finditer(text):
                    node, problem = resolve(root, me, aliases, *re.match(r"(" + BASE + r")((?:" + STEP + r")*)$", m.group(2)).groups())
                    if node is not None:
                        aliases[m.group(1)] = node
            for lineno, line in enumerate(text.split("\n"), 1):
                code = line.split("--")[0] if "--" in line and '"' not in line.split("--")[0][-1:] else line
                for m in CHAIN.finditer(code):
                    base, steps = m.group(1), m.group(2)
                    if ":WaitForChild(" not in steps and base != "script":
                        continue
                    node, problem = resolve(root, me, aliases, base, steps)
                    checked += 1
                    if problem:
                        problems.append(f"{rel}:{lineno}: {base}{steps[:90]} -> {problem}")
                    elif node is None:
                        skipped += 1
                    else:
                        before = code[: m.start()].rstrip()
                        direct = before.endswith("require(") and re.match(r"\s*(:Clone\(\))?\s*\)", code[m.end():])
                        if direct and node.cls not in ("ModuleScript",):
                            problems.append(f"{rel}:{lineno}: require() of a {node.cls} ({node.full()}), not a ModuleScript")
                        elif direct:
                            requires_ok += 1
    return problems, checked, requires_ok, skipped


def main():
    problems, checked, requires_ok, skipped = check()
    print(f"chains walked {checked}, requires landing on a ModuleScript {requires_ok}, not decidable (dynamic containers) {skipped}")
    for p in problems:
        print("  PROBLEM", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
