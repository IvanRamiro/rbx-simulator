"""Runs the paid-item rules on the REAL game modules with the Luau CLI (no Studio): EggInventory, SpinLedger, PetInventory, Codex,
AuctionRules, AuctionChecks, AuctionLedger and the shared config, bundled with a small stand-in for Roblox (game:GetService,
script.Parent, Color3, Enum ...), then PaidTest.luau and ChecksTest.lua. Use from the project root:

    python3 -I tools/roblox/auction_harness/paid_cli.py

It writes the bundle to a temporary folder and runs `luau` on it; the exit code is the tests' result.
"""
import os
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
HERE = os.path.dirname(os.path.abspath(__file__))

MODULES = {
    # name: path (every module is looked up by name, wherever the code asks for it)
    "GameConfig": "src/shared/GameConfig.lua",
    "PetRules": "src/shared/PetRules.lua",
    "Ranks": "src/shared/Ranks.lua",
    "Shop": "src/shared/Shop.lua",
    "PenLayout": "src/shared/PenLayout.lua",
    "NumberFormat": "src/shared/NumberFormat.lua",
    "SpinRules": "src/shared/SpinRules.lua",
    "PassRules": "src/shared/PassRules.lua",
    "RewardRules": "src/shared/RewardRules.lua",
    "CodexRules": "src/shared/CodexRules.lua",
    "AuctionRules": "src/shared/AuctionRules.lua",
    "Codex": "src/server/Pets/Codex.lua",
    "PetInventory": "src/server/Pets/PetInventory.lua",
    "EggInventory": "src/server/Pets/EggInventory.lua",
    "SpinLedger": "src/server/Rewards/SpinLedger.lua",
    "AuctionChecks": "src/server/Auction/AuctionChecks.lua",
    "AuctionLedger": "src/server/Auction/AuctionLedger.lua",
    "ChecksTest": "tools/roblox/auction_harness/ChecksTest.lua",
}

SHIM = r'''
-- a stand-in for the parts of Roblox these modules touch
local function anything(name)
    local proxy
    proxy = setmetatable({}, {
        __index = function(_, key)
            return anything(name .. "." .. tostring(key))
        end,
        __call = function()
            return anything(name .. "()")
        end,
        __tostring = function()
            return name
        end,
        __eq = function(a, b)
            return rawequal(a, b)
        end,
    })
    return proxy
end
local function colour()
    local c = {}
    c.Lerp = function()
        return colour()
    end
    c.ToHex = function()
        return "ffffff"
    end
    return c
end
Color3 = { fromRGB = colour, fromHex = colour, new = colour, fromHSV = colour }
Vector3 = { new = function(x, y, z) return { X = x, Y = y, Z = z } end }
Vector2 = { new = function(x, y) return { X = x, Y = y } end }
UDim2 = { new = function() return {} end, fromScale = function() return {} end, fromOffset = function() return {} end }
NumberRange = { new = function() return {} end }
NumberSequence = { new = function() return {} end }
ColorSequence = { new = function() return {} end }
NumberSequenceKeypoint = { new = function() return {} end }
Font = { new = function() return {} end }
Enum = anything("Enum")
typeof = function(v)
    return type(v)
end
warn = function(...) end
local guid = 0
local services = {
    RunService = { IsStudio = function() return STUDIO end, IsServer = function() return true end, IsClient = function() return false end },
    HttpService = { GenerateGUID = function() guid += 1 return string.format("GUID-%05d", guid) end },
}
local cache = {}
local function node(name)
    return setmetatable({ Name = name }, { __index = function(self, key)
        if key == "WaitForChild" or key == "FindFirstChild" then
            return function(_, child)
                return node(child)
            end
        elseif key == "Parent" then
            return node("Parent")
        end
        return nil
    end })
end
function require(target)
    local name = if type(target) == "table" then target.Name else tostring(target)
    if cache[name] == nil then
        local loader = MODULES[name]
        if not loader then
            cache[name] = anything(name) -- (RemoteEvents, Analytics ...: never called by these tests in a way that matters)
        else
            cache[name] = loader(node(name)) or true
        end
    end
    return cache[name]
end
game = setmetatable({}, { __index = function(_, key)
    if key == "GetService" then
        return function(_, service)
            return services[service] or node(service)
        end
    end
    return nil
end })
'''


def bundle():
    parts = ["--!nocheck", "MODULES = {}", "STUDIO = false", SHIM]
    for name, path in MODULES.items():
        with open(os.path.join(ROOT, path), encoding="utf-8") as handle:
            source = handle.read()
        parts.append("MODULES[%r] = function(script)\n%s\nend" % (name, source))
    with open(os.path.join(HERE, "PaidTest.luau"), encoding="utf-8") as handle:
        parts.append(handle.read())
    return "\n".join(parts).replace("MODULES['", 'MODULES["').replace("'] = function", '"] = function')


def main():
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "paid_bundle.luau")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(bundle())
        result = subprocess.run(["luau", path], capture_output=True, text=True)
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
