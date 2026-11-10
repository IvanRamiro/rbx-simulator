-- Realm6Motion: drives the Studio-built Realm 6 elements on a character: moves the vortex comets up their helix arms (so
-- their Trails draw). It creates nothing: every Attachment, Trail and ParticleEmitter is built in Studio (tools/roblox/realm6/build_*.lua) and found here by name on the HumanoidRootPart. The paths are in
-- Realm6MotionConfig (generated from tools/vfx/realm6_elements.py, which the offline previews use too).
--
--   local handle = Realm6Motion.start(character, { isLocal = true })
--     isLocal   the local player's own: never stops for distance
--   handle.stop()   -- stops moving them (the Trails then fade out on their own)
local RunService = game:GetService("RunService")

local Config = require(script.Parent:WaitForChild("Realm6MotionConfig"))

local Realm6Motion = {}

local TAU = 2 * math.pi

local function helix(arm, s)
    local V = Config.Vortex
    local th = arm * TAU / V.Arms + s * V.Turns * TAU
    local r = V.R0 + (V.R1 - V.R0) * s
    local y = V.Y0 + (V.Y1 - V.Y0) * s
    return Vector3.new(r * math.cos(th), y, r * math.sin(th))
end

function Realm6Motion.start(character, options)
    options = options or {}
    local root = character:WaitForChild("HumanoidRootPart", 5)
    local humanoid = character:FindFirstChildOfClass("Humanoid")
    if not root or not humanoid then
        return nil
    end
    local ground = Vector3.new(0, -(root.Size.Y / 2 + humanoid.HipHeight), 0)
    local movers = {}
    for _, spec in Config.Movers do
        local a, b = root:FindFirstChild(spec.A), root:FindFirstChild(spec.B)
        if a and b then
            table.insert(movers, { spec = spec, a = a, b = b, trail = root:FindFirstChild(spec.Trail), cycle = nil })
        end
    end
    local isLocal = options.isLocal == true
    local started = os.clock()
    local connection
    local handle = {}

    local function update()
        if not isLocal then
            local camera = workspace.CurrentCamera
            if camera and (camera.CFrame.Position - root.Position).Magnitude > Config.CullDistance then
                return
            end
        end
        local t = os.clock() - started
        for _, m in movers do
            local spec = m.spec
            if spec.Kind == "Helix" then
                local total = t / Config.Vortex.Period + spec.Phase
                local cycle = math.floor(total)
                local p = helix(spec.Arm, total - cycle)
                m.a.Position = p + ground
                m.b.Position = p + Vector3.new(0, spec.Width, 0) + ground
                if m.cycle ~= cycle then
                    -- the comet starts its run again at the bottom: clear its trail, or it draws a line down
                    m.cycle = cycle
                    if m.trail then
                        m.trail:Clear()
                    end
                end
            end
        end
    end

    connection = RunService.RenderStepped:Connect(update)
    update()

    function handle.stop()
        if connection then
            connection:Disconnect()
            connection = nil
        end
    end

    handle.movers = #movers
    return handle
end

return Realm6Motion
