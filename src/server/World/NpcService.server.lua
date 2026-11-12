-- The hub's people (WorldBuilder.buildHubNpcs, buildMerchantTemplate; tagged "HubNpc") breathe: each plays Roblox's standard
-- R15 idle, looped, at a slightly different speed so no two sway in step. Their roots are anchored, so they stay at their posts.
-- The Wandering Merchant is cloned in each time he arrives (MerchantService); his clone is picked up as it enters the Workspace.
local CollectionService = game:GetService("CollectionService")

local TAG = "HubNpc"
local IDLE = "rbxassetid://507766666" -- Roblox's default R15 idle

local animated = setmetatable({}, { __mode = "k" })

local function animate(model)
    if animated[model] or not model:IsDescendantOf(workspace) then
        return
    end
    local humanoid = model:FindFirstChildOfClass("Humanoid")
    if not humanoid then
        return
    end
    animated[model] = true
    local animator = humanoid:FindFirstChildOfClass("Animator")
    if not animator then
        animator = Instance.new("Animator")
        animator.Parent = humanoid
    end
    local animation = Instance.new("Animation")
    animation.AnimationId = IDLE
    local ok, track = pcall(function()
        return animator:LoadAnimation(animation)
    end)
    if ok and track then
        track.Looped = true
        track:Play(0.3, 1, 0.9 + math.random() * 0.2)
    else
        warn("NpcService: couldn't load the idle for " .. model:GetFullName())
    end
end

CollectionService:GetInstanceAddedSignal(TAG):Connect(function(model)
    task.defer(animate, model) -- (a clone's descendants arrive with it; let it settle in its parent first)
end)
for _, model in CollectionService:GetTagged(TAG) do
    task.spawn(animate, model)
end
