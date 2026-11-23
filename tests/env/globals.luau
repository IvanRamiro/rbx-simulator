-- Stand-ins for the Roblox globals the shared rule modules touch while they load, so the plain `luau` command-line tool can run them.
-- `tests/run.py` prepends a header to a temporary copy of every module in src/shared that binds these names as locals, so nothing here
-- leaks into src/. Only what the modules really use is modelled; anything else will fail loudly in the test that needs it.
local G = {}

G.warnings = {}

-- a deterministic Random (a linear congruential generator): the same seed gives the same numbers on every machine, which is what a
-- test needs. It is NOT Roblox's generator: assert ranges and invariants over many draws, never exact Roblox sequences.
local Random = {}
Random.__index = Random
function Random.new(seed)
    local self = setmetatable({}, Random)
    self.state = ((seed or 0) * 2654435761 + 12345) % 4294967296
    return self
end
function Random:_next()
    self.state = (self.state * 1664525 + 1013904223) % 4294967296
    return self.state / 4294967296
end
function Random:NextNumber(minimum, maximum)
    if minimum == nil then
        return self:_next()
    end
    return minimum + (maximum - minimum) * self:_next()
end
function Random:NextInteger(minimum, maximum)
    return minimum + math.floor(self:_next() * (maximum - minimum + 1))
end
G.Random = Random

-- value constructors: the modules only build data with them at load time
local function vec(...)
    local keys = { ... }
    return function(...)
        local values = { ... }
        local v = {}
        for i, k in keys do
            v[k] = values[i] or 0
        end
        return v
    end
end
G.Vector3 = { new = vec("X", "Y", "Z"), zero = { X = 0, Y = 0, Z = 0 }, one = { X = 1, Y = 1, Z = 1 } }
G.Vector2 = { new = vec("X", "Y"), zero = { X = 0, Y = 0 } }
local ColorMethods = {
    Lerp = function(a, b, alpha)
        return setmetatable({ R = a.R + (b.R - a.R) * alpha, G = a.G + (b.G - a.G) * alpha, B = a.B + (b.B - a.B) * alpha }, getmetatable(a))
    end,
}
local ColorMeta = { __index = ColorMethods }
G.Color3 = {
    fromRGB = function(r, g, b)
        return setmetatable({ R = (r or 0) / 255, G = (g or 0) / 255, B = (b or 0) / 255 }, ColorMeta)
    end,
    new = function(r, g, b)
        return setmetatable({ R = r or 0, G = g or 0, B = b or 0 }, ColorMeta)
    end,
    fromHSV = function(h, s, v)
        return { H = h, S = s, V = v }
    end,
    fromHex = function(hex)
        hex = string.gsub(hex, "#", "")
        return setmetatable({
            R = (tonumber(string.sub(hex, 1, 2), 16) or 0) / 255,
            G = (tonumber(string.sub(hex, 3, 4), 16) or 0) / 255,
            B = (tonumber(string.sub(hex, 5, 6), 16) or 0) / 255,
        }, ColorMeta)
    end,
}

-- anything else (Enum.X.Y, CFrame.new, UDim2.fromScale, TweenInfo.new, ...) is a "ghost": every index or call gives another ghost
local ghost
ghost = setmetatable({}, {
    __index = function()
        return ghost
    end,
    __call = function()
        return ghost
    end,
})
G.Enum, G.CFrame, G.UDim, G.UDim2, G.Instance, G.TweenInfo = ghost, ghost, ghost, ghost, ghost, ghost
G.NumberRange, G.NumberSequence, G.ColorSequence, G.NumberSequenceKeypoint, G.ColorSequenceKeypoint = ghost, ghost, ghost, ghost, ghost

G.DateTime = {
    now = function()
        return { UnixTimestamp = os.time() }
    end,
}

G.task = {
    wait = function() end,
    spawn = function(f, ...)
        f(...)
    end,
    defer = function(f, ...)
        f(...)
    end,
    delay = function() end,
}

G.warn = function(...)
    table.insert(G.warnings, table.concat({ ... }, " "))
end

-- the services: only the calls the shared modules make
local function container(extra)
    local c = {}
    c.WaitForChild = function(_, name)
        return "@shared/" .. name -- the real thing returns the ModuleScript; here `require` takes this alias path instead
    end
    c.FindFirstChild = function()
        return nil
    end
    c.GetAttribute = function(self, name)
        return (self.attributes or {})[name]
    end
    c.SetAttribute = function(self, name, value)
        self.attributes = self.attributes or {}
        self.attributes[name] = value
    end
    for k, v in extra or {} do
        c[k] = v
    end
    return c
end

G.workspace = container({
    GetServerTimeNow = function()
        return os.time()
    end,
})
local services = {
    ReplicatedStorage = container(),
    Workspace = G.workspace,
    RunService = container({
        IsStudio = function()
            return false
        end,
        IsServer = function()
            return true
        end,
        IsClient = function()
            return false
        end,
    }),
    Players = container({
        GetPlayers = function()
            return {}
        end,
    }),
}
G.services = services
G.game = {
    GetService = function(_, name)
        return services[name] or container()
    end,
}

return G
