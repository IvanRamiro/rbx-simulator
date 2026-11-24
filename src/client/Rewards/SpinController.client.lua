-- The Spin Wheel (GameConfig.SpinWheel, shared/SpinRules; the server: server/Rewards/SpinService). Three parts:
--   the world wheel   in the hub (SpinWheelBuilder): it shows this player's own amounts, and turns, for everyone, onto the segment
--                     the server picked (SpinEvent "Turn"): 4 to 6 turns easing out, a little overshoot and settle, a tick at
--                     each peg, the segment flashing as it lands;
--   the HUD button    round, beside Rewards: its badge counts the spins left, it glows while there are any; pressed far from the
--                     wheel it points the way (a marker), near it it opens the window;
--   the window        opened by the wheel's prompt: the spins left, when new ones come, the eight prizes and their chances, SPIN,
--                     and two green Robux buttons for more spins (GameConfig.SpinWheel.SpinProducts: ProductService pays them),
--                     most prominent once the spins run out. The odds are on the same page, above the buttons, before anyone
--                     buys (a paid spin is a paid random item); where those are restricted the buttons say so instead.
-- What was won shows when the wheel stops (SpinEvent "Won"), with a sound by its size.
local MarketplaceService = game:GetService("MarketplaceService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Ranks = require(ReplicatedStorage:WaitForChild("Ranks"))
local SpinRules = require(ReplicatedStorage:WaitForChild("SpinRules"))
local UI = script.Parent.Parent:WaitForChild("UI")
local Hud = require(UI:WaitForChild("Hud"))
local HudMetrics = require(UI:WaitForChild("HudMetrics"))
local Toast = require(UI:WaitForChild("Toast"))
local UiFx = require(UI:WaitForChild("UiFx"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local WorldMarkers = require(UI:WaitForChild("WorldMarkers"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local player = Players.LocalPlayer
local C = UiTheme.Colors
local config = GameConfig.SpinWheel
local SETTLE = 0.6       -- seconds the overshoot settles back (SpinService's SETTLE)
local OVERSHOOT = 3      -- degrees past the landing, before settling back
local NEAR = 30          -- studs from the wheel's prompt the HUD button opens the window (and the window stays open)
local ANIMATE_RANGE = 450 -- studs from the camera the wheel's turning is drawn every frame
local ROBUX = utf8.char(0xE002) -- Roblox's Robux sign, in its own fonts (as in the Shop)

local message = Toast.new("SpinMessage", C.Highlight, 5)

-- ---------- what each segment is for this player ----------
local function rankName()
    return Ranks.getPlayerRankName(player)
end

local function iconOf(info)
    if info.Icon == "Stones" then
        return UiTheme.Icons.Stones
    elseif info.Icon == "Qi" then
        return UiTheme.Icons.Qi
    elseif info.Icon == "Egg" then
        return UiTheme.EggIcons[info.EggId] or UiTheme.Icons.Hatch
    end
    return nil
end

-- ---------- the world wheel ----------
local wheel = nil -- { model, axle, parts, offsets, pointer, prompt, angle, turn }
local function setAngle(degrees)
    if not wheel then
        return
    end
    wheel.angle = degrees
    local turn = wheel.axle * CFrame.Angles(0, 0, -math.rad(degrees))
    local cframes = table.create(#wheel.parts)
    for i, offset in wheel.offsets do
        cframes[i] = turn * offset
    end
    workspace:BulkMoveTo(wheel.parts, cframes, Enum.BulkMoveMode.FireCFrameChanged)
end

-- the wheel's face shows this player's own amounts and egg
local function labelWheel()
    if not wheel then
        return
    end
    local gui = wheel.face and wheel.face:FindFirstChildOfClass("SurfaceGui")
    if not gui then
        return
    end
    for index = 1, SpinRules.Count do
        local info = SpinRules.describe(index, rankName(), player)
        local holder = gui:FindFirstChild("Seg" .. index)
        if holder then
            local icon, words = holder:FindFirstChild("Icon"), holder:FindFirstChild("Words")
            if icon then
                icon.Image = iconOf(info) or ""
            end
            if words then
                words.Text = info.Short
            end
        end
    end
end

local function bindWheel(model)
    local axlePart = model:WaitForChild("Axle", 10)
    local rotor = model:WaitForChild("Rotor", 10)
    if not (axlePart and rotor) then
        return
    end
    local parts, offsets = {}, {}
    local axle = axlePart.CFrame
    for _, d in rotor:GetDescendants() do
        if d:IsA("BasePart") then
            table.insert(parts, d)
            table.insert(offsets, axle:ToObjectSpace(d.CFrame))
        end
    end
    local promptPart = model:FindFirstChild("Prompt")
    wheel = {
        model = model, axle = axle, axlePart = axlePart, rotor = rotor, parts = parts, offsets = offsets,
        pointer = model:FindFirstChild("Pointer"), prompt = promptPart, face = rotor:FindFirstChild("Face"), angle = 0, turn = nil,
    }
    setAngle(model:GetAttribute("Rest") or 0)
    labelWheel()
end

task.spawn(function()
    local root = workspace:WaitForChild("FloatingIslands")
    local island = root:WaitForChild("Yggdrasil")
    local model = island:WaitForChild("SpinWheel", 60)
    if model then
        bindWheel(model)
        -- a turn this client never saw (it joined meanwhile): it rests where the server says
        model:GetAttributeChangedSignal("Rest"):Connect(function()
            task.delay(0.5, function()
                if wheel and not wheel.turn and (model:GetAttribute("TurningUntil") or 0) < workspace:GetServerTimeNow() then
                    setAngle(model:GetAttribute("Rest") or 0)
                end
            end)
        end)
    end
end)

-- the landed segment lights up: its wedges pulse toward white, its icon jumps
local function flashSegment(index)
    if not wheel then
        return
    end
    local segment = SpinRules.Segments[index]
    local wedges = {}
    for _, part in wheel.parts do
        if part.Name == "Seg" .. index then
            table.insert(wedges, part)
        end
    end
    local bright = segment.Color:Lerp(Color3.new(1, 1, 1), 0.6)
    local pulse = TweenInfo.new(0.22, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, 3, true)
    for _, wedge in wedges do
        wedge.Color = segment.Color
        TweenService:Create(wedge, pulse, { Color = bright }):Play()
    end
    local gui = wheel.face and wheel.face:FindFirstChildOfClass("SurfaceGui")
    local icon = gui and gui:FindFirstChild("Seg" .. index) and gui["Seg" .. index]:FindFirstChild("Icon")
    if icon then
        local rest = UDim2.fromOffset(100, 100)
        icon.Size = UDim2.fromOffset(150, 150)
        TweenService:Create(icon, TweenInfo.new(0.5, Enum.EasingStyle.Back), { Size = rest }):Play()
    end
end

-- where the wheel is at `elapsed` seconds into a turn (eased out past the landing, then settling back)
local function angleAt(turn, elapsed)
    local over = if turn.To >= turn.From then OVERSHOOT else -OVERSHOOT
    if elapsed < turn.Seconds then
        local u = math.clamp(elapsed / turn.Seconds, 0, 1)
        local eased = 1 - (1 - u) ^ 3
        return turn.From + (turn.To + over - turn.From) * eased
    elseif elapsed < turn.Seconds + SETTLE then
        local v = (elapsed - turn.Seconds) / SETTLE
        return turn.To + over * (1 - v * v * (3 - 2 * v))
    end
    return turn.To
end

-- the peg under the pointer: segment edges sit half a step either side of each segment's middle
local function pegOf(degrees)
    return math.floor((degrees + SpinRules.Step / 2) / SpinRules.Step)
end

local function runTurn(turn)
    if not wheel then
        return
    end
    wheel.turn = turn
    local mine = turn.UserId == player.UserId
    local lastPeg = pegOf(turn.From)
    local landed = false
    Sfx.play("WheelStart", wheel.axlePart)
    local connection
    connection = RunService.RenderStepped:Connect(function()
        if not wheel or wheel.turn ~= turn then
            connection:Disconnect()
            return
        end
        local elapsed = workspace:GetServerTimeNow() - turn.Start
        local angle = angleAt(turn, elapsed)
        local camera = workspace.CurrentCamera
        local near = camera and (camera.CFrame.Position - wheel.axle.Position).Magnitude < ANIMATE_RANGE
        if near then
            setAngle(angle)
            local peg = pegOf(angle)
            if peg ~= lastPeg then
                lastPeg = peg
                Sfx.play("WheelTick", wheel.pointer or wheel.axlePart)
            end
        end
        if not landed and elapsed >= turn.Seconds then
            landed = true
            flashSegment(turn.Segment)
            Sfx.play("WheelStop", wheel.axlePart)
            if SpinRules.Segments[turn.Segment].Kind == "Jackpot" and not mine then
                Sfx.play("SpinJackpotWorld", wheel.axlePart)
            end
        end
        if elapsed >= turn.Seconds + SETTLE then
            setAngle(turn.To % 360)
            wheel.turn = nil
            connection:Disconnect()
        end
    end)
end

-- ---------- the HUD button ----------
local button, setBadge = Hud.topButton("SpinButton", "", 0, "Spin")
do
    local icon = button:FindFirstChild("Icon")
    if icon then
        icon.Visible = false -- (no picture of a wheel uploaded yet: a small turning wheel instead)
    end
end
-- a small copy of the wheel's face, turning slowly while there are spins
local mini = Instance.new("ViewportFrame")
mini.Name = "Wheel"
mini.BackgroundTransparency = 1
mini.AnchorPoint = Vector2.new(0.5, 0.5)
mini.Position = UDim2.fromScale(0.5, 0.5)
mini.Size = UDim2.fromScale(0.86, 0.86)
mini.Ambient = Color3.fromRGB(210, 210, 220)
mini.LightColor = Color3.new(1, 1, 1)
mini.LightDirection = Vector3.new(0, -0.3, -1)
mini.ZIndex = 3
mini.Parent = button
local miniCamera = Instance.new("Camera")
miniCamera.FieldOfView = 30
miniCamera.Parent = mini
mini.CurrentCamera = miniCamera
UiKit.corner(mini, 999)

local function buildMini()
    if not wheel then
        return
    end
    mini:ClearAllChildren()
    miniCamera = Instance.new("Camera")
    miniCamera.FieldOfView = 30
    miniCamera.Parent = mini
    mini.CurrentCamera = miniCamera
    local copy = Instance.new("Model")
    for i, part in wheel.parts do
        if part.Transparency < 1 then
            local clone = part:Clone()
            clone:ClearAllChildren()
            clone.CFrame = wheel.offsets[i]
            clone.Parent = copy
        end
    end
    copy.Parent = mini
end

-- the gentle glow while spins are waiting: a gold ring breathing round the button
local glow = Instance.new("Frame")
glow.Name = "Glow"
glow.BackgroundTransparency = 1
glow.AnchorPoint = Vector2.new(0.5, 0.5)
glow.Position = UDim2.fromScale(0.5, 0.5)
glow.Size = UDim2.new(1, 8, 1, 8)
glow.Visible = false
glow.Parent = button
UiKit.corner(glow, 999)
local ring = Instance.new("UIStroke")
ring.Color = C.Highlight
ring.Thickness = 2.5
ring.Transparency = 0.2
ring.Parent = glow
local breathing = TweenService:Create(ring, TweenInfo.new(1.1, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true),
    { Transparency = 0.85 })

local miniAngle = 0
RunService.RenderStepped:Connect(function(dt)
    if glow.Visible and mini.Visible then
        miniAngle = (miniAngle + dt * 40) % 360
    end
    miniCamera.CFrame = CFrame.Angles(0, 0, math.rad(miniAngle)) * CFrame.new(0, 0, 26) -- in front of the face, rolled: the wheel turns
end)

local function spinsLeft()
    return player:GetAttribute("SpinsLeft") or 0
end

local function renderButton()
    local left = spinsLeft()
    setBadge(if left > 0 then tostring(left) else nil, "Highlight")
    local on = left > 0
    if on ~= glow.Visible then
        glow.Visible = on
        if on then
            breathing:Play()
        else
            breathing:Cancel()
        end
    end
end

-- ---------- the way there ----------
local marker = nil
local markerUntil = 0
local function promptPosition()
    return wheel and wheel.prompt and wheel.prompt.Position
end

local function distanceToWheel()
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    local at = promptPosition()
    return if root and at then (root.Position - at).Magnitude else math.huge
end

local function showWay()
    if not wheel then
        return
    end
    if not marker then
        marker = WorldMarkers.new(C.Highlight, true)
    end
    markerUntil = os.clock() + 90
    marker.world = wheel.axle.Position + Vector3.new(0, 9, 0)
    if spinsLeft() <= 0 then
        message:show("Out of spins: buy more at the wheel. Follow the arrow.", "Info")
    else
        message:show("The Spin Wheel is on the east side of the hub, past the Ring Road. Follow the arrow.", "Info")
    end
end

task.spawn(function()
    while true do
        task.wait(0.25)
        if marker and marker.world then
            local distance = distanceToWheel()
            if distance < 18 or os.clock() > markerUntil then
                marker.world = nil
            else
                marker.label.Text = "SPIN WHEEL  " .. math.floor(distance) .. " studs"
            end
        end
    end
end)

-- ---------- the window ----------
local TILE_H, TILE_GAP = 58, 8
local INFO_H = 42
local GRID_Y = INFO_H + 8
local GRID_H = TILE_H * 2 + TILE_GAP
local SPIN_Y = GRID_Y + GRID_H + UiTheme.Space.M
local HINT_Y = SPIN_Y + UiTheme.Height.ButtonLarge + UiTheme.Space.S
local HINT_H = 16
local BUY_Y = HINT_Y + HINT_H + UiTheme.Space.XS
local BUY_H = 48 -- (a thumb's 44 and more)
local BODY = BUY_Y + BUY_H
local WIDTH = 360
local FRAME_EXTRA = UiTheme.Height.TitleBar + UiTheme.Space.M + UiTheme.Pad.Window -- a window's title band and padding
local FULL_HEIGHT = BODY + FRAME_EXTRA
-- A short screen (a phone on its side) can't fit the window's height: it goes wide instead, the prizes on the left and SPIN with
-- the Robux buttons on the right, so the buttons are never cut off.
local WIDE_WIDTH = 690
local WIDE_LEFT = 0.5 -- the prizes' share of the width
local WIDE_HEIGHT = GRID_Y + GRID_H + FRAME_EXTRA
local window = Hud.window({
    Name = "SpinWindow", Title = "SPIN THE WHEEL",
    Size = Vector2.new(WIDTH, FULL_HEIGHT),
    AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, -UiTheme.Margin, 0.5, 0), Side = true,
})
local body = window.Body
local leftLabel = UiKit.boldLabel({ Name = "SpinsLeft", TextSize = 18, Size = UDim2.new(1, 0, 0, 22), RichText = true, Parent = body })
local resetLabel = UiKit.label({ Name = "Reset", TextSize = 13, TextColor3 = C.Muted, Position = UDim2.fromOffset(0, 23),
    Size = UDim2.new(1, 0, 0, 18), Parent = body })

local tiles = {}
local COLUMNS = 4
for index = 1, SpinRules.Count do
    local column, row = (index - 1) % COLUMNS, math.floor((index - 1) / COLUMNS)
    local share = 1 / COLUMNS
    local tile = UiKit.card({
        Name = "Prize" .. index, Position = UDim2.new(column * share, TILE_GAP / 2, 0, GRID_Y + row * (TILE_H + TILE_GAP)),
        Size = UDim2.new(share, -TILE_GAP, 0, TILE_H), Stripe = SpinRules.Segments[index].Color, Parent = body,
    })
    local picture = Instance.new("ImageLabel")
    picture.Name = "Icon"
    picture.BackgroundTransparency = 1
    picture.ScaleType = Enum.ScaleType.Fit
    picture.AnchorPoint = Vector2.new(0.5, 0)
    picture.Position = UDim2.new(0.5, 0, 0, 5)
    picture.Size = UDim2.fromOffset(26, 26)
    picture.Parent = tile
    local mark = UiKit.boldLabel({ Name = "Mark", Text = "+1", TextSize = 18, TextColor3 = C.Highlight, AnchorPoint = Vector2.new(0.5, 0),
        Position = UDim2.new(0.5, 0, 0, 5), Size = UDim2.fromOffset(26, 26), TextXAlignment = Enum.TextXAlignment.Center, Visible = false,
        Parent = tile })
    local words = UiKit.boldLabel({ Name = "Words", TextSize = 11, Position = UDim2.fromOffset(2, 32), Size = UDim2.new(1, -4, 0, 13),
        TextXAlignment = Enum.TextXAlignment.Center, TextTruncate = Enum.TextTruncate.AtEnd, Parent = tile })
    local chance = UiKit.label({ Name = "Chance", Font = "Strong", TextSize = 10, TextColor3 = C.Muted, Position = UDim2.fromOffset(2, 44),
        Size = UDim2.new(1, -4, 0, 12), TextXAlignment = Enum.TextXAlignment.Center, Parent = tile })
    tiles[index] = { tile = tile, picture = picture, mark = mark, words = words, chance = chance }
end

local spinButton = UiKit.button({ Name = "Spin", Tone = "Go", TextSize = UiTheme.Text.ButtonLarge, Text = "SPIN!",
    Position = UDim2.fromOffset(0, SPIN_Y), Size = UDim2.new(1, 0, 0, UiTheme.Height.ButtonLarge), Parent = body })

-- ---------- more spins for Robux ----------
local PRODUCTS = config.SpinProducts
local livePrices = {} -- [ProductId] = its price on Roblox, once asked
local asking = {} -- [ProductId] = true while Roblox is being asked
local hint = UiKit.label({ Name = "BuyHint", Font = "Strong", TextSize = 12, TextColor3 = C.Muted, Position = UDim2.fromOffset(0, HINT_Y),
    Size = UDim2.new(1, 0, 0, HINT_H), TextXAlignment = Enum.TextXAlignment.Center, Parent = body })
local buys = {}
for i, product in PRODUCTS do -- (placed by renderBuys)
    local buy = UiKit.button({ Name = "Buy" .. product.Spins, Tone = "Buy", Text = "", Size = UDim2.new(0.5, 0, 0, BUY_H), Parent = body })
    -- the words on their own label, so they carry an outline (the button's own stroke is its border)
    local words = UiKit.label({ Name = "Price", Font = "Heavy", Text = "", TextSize = 18, TextColor3 = Color3.new(1, 1, 1),
        TextXAlignment = Enum.TextXAlignment.Center, Size = UDim2.fromScale(1, 1), ZIndex = buy.ZIndex + 1, Parent = buy })
    UiKit.outline(words, 1.5)
    buys[i] = { product = product, button = buy, words = words }
end

-- the layout, tall or wide (by the window's height after Hud fits it to the screen)
local buyArea = { x = 0, width = 1, inset = 0, y = BUY_Y } -- where the Robux buttons go: a share of the body's width, and a top
local renderBuys -- (below)

local function layout()
    local frame = window.Frame
    local view, scale = HudMetrics.viewport(), Hud.windowScale()
    local wide = frame.Size.Y.Offset < FULL_HEIGHT - 1
    if wide then
        local across = (view.X - 24) / scale
        local size = UDim2.fromOffset(math.min(WIDE_WIDTH, across), math.min(frame.Size.Y.Offset, WIDE_HEIGHT))
        if frame.Size ~= size then
            frame.Size = size
        end
    end
    local left = if wide then WIDE_LEFT else 1
    local gap = UiTheme.Space.M
    local share = left / COLUMNS
    for index, t in tiles do
        local column, row = (index - 1) % COLUMNS, math.floor((index - 1) / COLUMNS)
        t.tile.Position = UDim2.new(column * share, TILE_GAP / 2, 0, GRID_Y + row * (TILE_H + TILE_GAP))
        t.tile.Size = UDim2.new(share, -TILE_GAP, 0, TILE_H)
    end
    leftLabel.Size = UDim2.new(left, 0, 0, 22)
    resetLabel.Size = UDim2.new(left, 0, 0, 18)
    if wide then
        -- the right column ends level with the prizes' last row
        local x, w = UDim.new(left, gap), UDim.new(1 - left, -gap)
        local buyY = GRID_Y + GRID_H - BUY_H
        local hintY = buyY - UiTheme.Space.XS - HINT_H
        spinButton.Position = UDim2.new(x, UDim.new(0, hintY - UiTheme.Space.S - UiTheme.Height.ButtonLarge))
        spinButton.Size = UDim2.new(w, UDim.new(0, UiTheme.Height.ButtonLarge))
        hint.Position = UDim2.new(x, UDim.new(0, hintY))
        hint.Size = UDim2.new(w, UDim.new(0, HINT_H))
        buyArea = { x = left, width = 1 - left, inset = gap, y = buyY }
    else
        spinButton.Position = UDim2.fromOffset(0, SPIN_Y)
        spinButton.Size = UDim2.new(1, 0, 0, UiTheme.Height.ButtonLarge)
        hint.Position = UDim2.fromOffset(0, HINT_Y)
        hint.Size = UDim2.new(1, 0, 0, HINT_H)
        buyArea = { x = 0, width = 1, inset = 0, y = BUY_Y }
    end
    renderBuys(spinsLeft())
end

-- nil until the server has asked Roblox (SpinService); true where paid random items are restricted
local function restriction()
    return player:GetAttribute("RandomItemsRestricted")
end

local function boughtSpins()
    return player:GetAttribute("SpinsBought") or 0
end

function renderBuys(left)
    local restricted = restriction()
    local out = left <= 0
    hint.Text = if restricted == true then "Spins can't be bought here."
        elseif out then "Out of spins? Buy more. They never run out."
        else "Bought spins never run out."
    hint.TextColor3 = if out and restricted ~= true then C.Highlight else C.Muted
    for i, entry in buys do
        local product = entry.product
        local area = buyArea
        if restricted == nil or restricted == true then
            -- one wide note in place of both buttons
            entry.button.Visible = i == 1
            entry.button.Position = UDim2.new(area.x, area.inset, 0, area.y)
            entry.button.Size = UDim2.new(area.width, -area.inset, 0, BUY_H)
            entry.button:SetAttribute("Tone", "Quiet")
            entry.words.Text = if restricted then "NOT AVAILABLE IN YOUR REGION" else "PLEASE WAIT..."
            entry.words.TextSize = 15
            entry.words.TextColor3 = C.Muted
        else
            -- n buttons share the area (less its inset on the left) with gaps between them
            local n, gap = #buys, UiTheme.Space.S
            local share, less = area.width / n, (area.inset + (n - 1) * gap) / n
            entry.button.Visible = true
            entry.button.Position = UDim2.new(area.x + share * (i - 1), area.inset + (i - 1) * (gap - less), 0, area.y)
            entry.button.Size = UDim2.new(share, -less, 0, BUY_H)
            entry.button:SetAttribute("Tone", "Buy")
            entry.words.Text = "+" .. product.Spins .. (if product.Spins == 1 then " SPIN  " else " SPINS  ") .. ROBUX .. " "
                .. tostring(livePrices[product.ProductId] or product.Price)
            entry.words.TextSize = if out then 19 else 16 -- (bigger once the spins run out)
            entry.words.TextColor3 = Color3.new(1, 1, 1)
        end
    end
end

-- each product's live price, once (a price changed on Roblox shows without a new release)
local function fetchPrices()
    for _, product in PRODUCTS do
        if (product.ProductId or 0) > 0 and not livePrices[product.ProductId] and not asking[product.ProductId] then
            asking[product.ProductId] = true
            task.spawn(function()
                local ok, info = pcall(MarketplaceService.GetProductInfo, MarketplaceService, product.ProductId, Enum.InfoType.Product)
                asking[product.ProductId] = nil -- (on a failure, asked again next time the window opens)
                if ok and info and typeof(info.PriceInRobux) == "number" then
                    livePrices[product.ProductId] = info.PriceInRobux
                    renderBuys(spinsLeft())
                end
            end)
        end
    end
end

window.Frame:GetPropertyChangedSignal("Size"):Connect(layout)
layout()

for _, entry in buys do
    entry.button.Activated:Connect(function()
        local restricted = restriction()
        if restricted == nil then
            return
        elseif restricted then
            Sfx.play("Error")
            message:show("Spins can't be bought where you live: Roblox has rules about paying for random prizes.", "Warning")
            return
        end
        if boughtSpins() + entry.product.Spins > config.MaxBought then
            Sfx.play("Error")
            message:show("You're holding as many bought spins as you can. Use some first.", "Warning")
            return
        end
        Sfx.play("Click")
        MarketplaceService:PromptProductPurchase(player, entry.product.ProductId)
    end)
end

local waiting = false -- a spin asked for, the server's answer not here yet
local myTurnUntil = 0 -- os.clock() this player's own spin is still turning

local function resetText()
    local seconds = SpinRules.secondsToReset(workspace:GetServerTimeNow())
    local hours, minutes = math.floor(seconds / 3600), math.floor(seconds % 3600 / 60)
    return "New free spins in " .. (if hours > 0 then hours .. "h " .. minutes .. "m" else minutes .. "m " .. math.floor(seconds % 60) .. "s")
end

local function renderWindow()
    local left = spinsLeft()
    local function hex(color)
        return string.format("#%02X%02X%02X", math.floor(color.R * 255), math.floor(color.G * 255), math.floor(color.B * 255))
    end
    local gold = hex(C.Highlight)
    local bought = boughtSpins()
    leftLabel.Text = "Spins left: <font color=\"" .. gold .. "\">" .. left .. "</font>"
        .. (if bought > 0 then "  <font size=\"13\" color=\"" .. hex(C.Muted) .. "\">(" .. bought .. " bought)</font>" else "")
    resetLabel.Text = resetText()
    renderBuys(left)
    local name = rankName()
    for index, t in tiles do
        local info = SpinRules.describe(index, name, player)
        local image = iconOf(info)
        t.picture.Image = image or ""
        t.picture.Visible = image ~= nil
        t.mark.Visible = image == nil
        t.words.Text = info.Short
        t.words.TextColor3 = if info.Kind == "Jackpot" then C.Highlight else C.Text
        local percent = info.Chance * 100 -- (under 1%, one decimal: the jackpot's 0.2 would round to "0%")
        t.chance.Text = (if percent < 1 then string.format("%.1f", percent) else tostring(math.floor(percent + 0.5))) .. "% chance"
    end
    local turning = wheel and (wheel.model:GetAttribute("TurningUntil") or 0) > workspace:GetServerTimeNow()
    local ready = left > 0 and not waiting and not turning and os.clock() >= myTurnUntil
    spinButton.Active = ready
    spinButton.AutoButtonColor = false
    spinButton:SetAttribute("Tone", if ready then "Go" else "Quiet")
    spinButton.Text = if waiting or os.clock() < myTurnUntil then "SPINNING..."
        elseif turning then "THE WHEEL IS TURNING..."
        elseif left <= 0 then "NO SPINS LEFT"
        else "SPIN!"
end

spinButton.Activated:Connect(function()
    if not spinButton.Active then
        return
    end
    waiting = true
    renderWindow()
    RemoteEvents.SpinEvent:FireServer("Spin")
    task.delay(4, function() -- no answer (a lost request): the button comes back
        if waiting then
            waiting = false
            renderWindow()
        end
    end)
end)

local function openWindow()
    fetchPrices()
    renderWindow()
    window.open()
end

window.link(button)
button.Activated:Connect(function()
    if window.isOpen() then
        window.close()
    elseif distanceToWheel() <= NEAR then
        openWindow()
    else
        showWay()
    end
end)

-- the window keeps time while open, and closes when the player walks away
task.spawn(function()
    while true do
        task.wait(0.5)
        if window.isOpen() then
            renderWindow()
            if spinsLeft() <= 0 and restriction() == false and os.clock() % 2.4 < 0.5 then -- (out of spins: light crosses the buttons)
                for _, entry in buys do
                    UiFx.sweep(entry.button, C.Highlight, 0.7)
                end
            end
            if distanceToWheel() > NEAR and os.clock() >= myTurnUntil then
                window.close()
            end
        end
    end
end)

-- ---------- the server's words ----------
local function winSound(won)
    if won.Jackpot then
        Sfx.play("SpinJackpot")
    elseif won.Big then
        Sfx.play("SpinWinBig")
    else
        Sfx.play("RewardClaim")
    end
end

-- On a phone the window is wide and covers the wheel the player is spinning (the wheel is in the world, the window over it): it steps away while their spin
-- turns, and comes back when the prize is told (or after a while, if the answer is lost), so the player sees the wheel stop and can spin again at once.
local closedForSpin = 0
local function reopenAfterSpin(this)
    if closedForSpin == this and not window.isOpen() and distanceToWheel() <= NEAR then
        closedForSpin = 0
        openWindow()
    end
end

RemoteEvents.SpinEvent.OnClientEvent:Connect(function(kind, data)
    if kind == "Open" then
        if marker then
            marker.world = nil
        end
        openWindow()
    elseif kind == "Refused" and typeof(data) == "string" then
        waiting = false
        renderWindow()
        Sfx.play("Error")
        message:show(data, "Warning")
    elseif kind == "Spun" and typeof(data) == "table" then
        waiting = false
        myTurnUntil = os.clock() + config.Seconds + SETTLE
        renderWindow()
        if Hud.isCompact() and window.isOpen() then
            local this = os.clock()
            closedForSpin = this
            window.close()
            task.delay(config.Seconds + SETTLE + 4, reopenAfterSpin, this) -- (the fallback: the prize's own word reopens it sooner)
        end
    elseif kind == "Turn" and typeof(data) == "table" then
        runTurn(data)
        renderWindow()
    elseif kind == "Won" and typeof(data) == "table" then
        myTurnUntil = if data.Late then 0 else os.clock() + SETTLE -- (the wheel still settles: SPINNING... until it rests)
        winSound(data)
        local tile = tiles[data.Segment]
        if tile and window.isOpen() then
            UiFx.flash(tile.tile, C.Highlight)
        end
        local text = if data.Late then "Your last spin's prize: " .. data.Text
            elseif data.Jackpot then "JACKPOT! You won " .. data.Text
            else "You won " .. data.Text .. (if string.find(data.Text, "[!.]$") then "" else "!")
        message:show(text, "Reward")
        renderWindow()
        if closedForSpin ~= 0 then
            task.delay(1.8, reopenAfterSpin, closedForSpin) -- (long enough to see the wheel rest and read the notice)
        end
    elseif kind == "Bought" and typeof(data) == "table" and typeof(data.Spins) == "number" then
        Sfx.play("PremiumPurchase")
        message:show("+" .. data.Spins .. (if data.Spins == 1 then " spin!" else " spins!") .. " They're yours until you use them. Thank you for supporting the game!", "Reward")
        if window.isOpen() then
            UiFx.flash(spinButton, C.Highlight)
        end
        renderWindow()
    elseif kind == "Jackpot" and typeof(data) == "string" and data ~= player.DisplayName then
        message:show(data .. " won an Exclusive Egg on the Spin Wheel!", "Info")
    end
end)

-- ---------- keeping it current ----------
local function relabel()
    labelWheel()
    if window.isOpen() then
        renderWindow()
    end
end
player:GetAttributeChangedSignal("RandomItemsRestricted"):Connect(relabel) -- (there the jackpot shows its stones, and no spins are sold)
player:GetAttributeChangedSignal("SpinsBought"):Connect(function()
    if window.isOpen() then
        renderWindow()
    end
end)
player:GetAttributeChangedSignal("Pass_VIP"):Connect(function() -- (VIP's +50% shows on the wheel's stones)
    labelWheel()
    if window.isOpen() then
        renderWindow()
    end
end)
player:GetAttributeChangedSignal("SpinsLeft"):Connect(function()
    renderButton()
    if window.isOpen() then
        renderWindow()
    end
end)
task.spawn(function()
    local rank = player:WaitForChild("leaderstats"):WaitForChild("Rank")
    rank.Changed:Connect(function()
        labelWheel()
        if window.isOpen() then
            renderWindow()
        end
    end)
    labelWheel()
end)
task.spawn(function()
    while not wheel do
        task.wait(0.5)
    end
    buildMini()
    labelWheel()
end)
renderButton()
