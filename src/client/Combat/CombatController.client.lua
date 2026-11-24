-- Striking with the equipped weapon (the "WeaponId" attribute; GameConfig.WeaponKinds) or the Qi
-- Palm (GameConfig.Combat.Palm): left click, gamepad R2 or the touch Strike button. The strike's
-- effects play here at once (CombatFx) and the server is asked to resolve it (CombatEvent); the
-- server relays every strike back for everyone's effects, where it landed, and what it did there
-- (its damage, whether it was critical, the target struck).
--
-- Equipping and putting away (the owner, 2026-11-11, and 2026-11-16: "replace it with the box for inventory weapon"): the weapon
-- sits in slot 1 of the inventory bar (Hud.Inventory); pressing the slot, key 1 or gamepad X asks the server (WeaponDrawEvent)
-- to draw it into the hand or put it back across the back. With no weapon the slot is empty and says where to buy one.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local Shop = require(ReplicatedStorage:WaitForChild("Shop"))
local FormRules = require(ReplicatedStorage:WaitForChild("FormRules"))
local CombatFx = require(script.Parent:WaitForChild("CombatFx"))
local ComboCounter = require(script.Parent:WaitForChild("ComboCounter"))
local UI = script.Parent.Parent:WaitForChild("UI")
local Hud = require(UI:WaitForChild("Hud"))
local Toast = require(UI:WaitForChild("Toast"))
local UiKit = require(UI:WaitForChild("UiKit"))
local TouchActions = require(UI:WaitForChild("TouchActions"))
local Portraits = require(UI:WaitForChild("Portraits"))

local player = Players.LocalPlayer
local readyAt = 0
local airNoted = false -- the note about striking from sword flight shows once a session
local message = Toast.new("CombatMessage", Color3.new(1, 1, 1), 4)

-- "Palm", "Sword" or "Spear", and the weapon's own numbers (FormRules.plan scales them by the form's step, as the server does: the damage isn't ours to
-- know, so it is 1 here)
local function strikeBase()
    local weapon = Shop.weapon(player:GetAttribute("WeaponId"))
    if not weapon then
        local palm = GameConfig.Combat.Palm
        return "Palm", { Damage = 1, Range = palm.Range, Arc = palm.Arc, Cooldown = palm.Cooldown }
    end
    local kind = GameConfig.WeaponKinds[weapon.Kind]
    return weapon.Kind, { Damage = 1, Range = kind.Range, Arc = kind.Arc, Cooldown = kind.Cooldown }
end
local mine = nil -- { Form, Step, At }: our last strike in its form's chain, as the server counts it (the server's answer corrects it)
local UNIT = { Damage = 1, Range = 10, Arc = 80, Cooldown = 1 } -- a strike's step and finisher don't depend on these

-- Input feel (the owner, 2026-11-24: "attacks should respond immediately ... sensible animation cancel windows ... preserve combo continuity"): a press that comes while the
-- last strike is still recovering is kept for up to BUFFER seconds and fires at the cancel point, LEAD of the last strike's cooldown before it ends (the keyed clips end a
-- little before their cooldown, so the next one begins out of the recovery, not after a pause). The cooldown stays the server's (CombatService): readyAt moves on by whole
-- cooldowns from when the last was due, exactly as the server's schedule does, so striking at the cancel point never adds up to more strikes a second (the server accepts a
-- strike up to its COOLDOWN_SLACK early, 0.2, and LEAD is half of that). Holding the button (mouse, gamepad R2, the touch button) strikes again at each cancel point.
local BUFFER = 0.3
local LEAD = 0.1
local lastCooldown = 0.5 -- the cooldown of the strike that set readyAt
local waiting = false -- a buffered press is waiting for the cancel point
local queuedHeavy = false
local holding = nil   -- what is held: "Mouse", "Gamepad" or "Touch"
local touchHeld = nil  -- the InputObject of the finger holding the Strike button (its UserInputState tells when it lifts)
local touchStart = nil -- where that finger began, to tell a swipe up (a heavy strike) from a hold
local beginCharge, endCharge -- (the heavy strike's, below)

local function strike(repeating, heavy)
    local character = player.Character
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    if not humanoid or humanoid.Health <= 0 or player:GetAttribute("IsCultivating") == true
        or player:GetAttribute("CarryingEgg") ~= nil then -- both hands are round the egg
        return
    end
    local now = os.clock()
    local kind, base = strikeBase()
    local cancelAt = readyAt - lastCooldown * LEAD
    if now < cancelAt then
        if not repeating and not waiting and cancelAt - now <= BUFFER then
            waiting = true
            queuedHeavy = heavy == true
            task.delay(cancelAt - now + 0.002, function()
                waiting = false
                strike(true, queuedHeavy)
            end)
        end
        return
    end
    local info = FormRules.plan(kind, nil, Shop.playerRealmIndex(player), base, mine, now, heavy == true)
    if not info then
        return
    end
    readyAt = math.max(now, readyAt) + info.Cooldown
    lastCooldown = info.Cooldown
    mine = { Form = info.Form, Step = info.Step, At = now }
    if player:GetAttribute("IsFlying") == true and not airNoted then
        airNoted = true
        message:show("You can't hit guardians from the air. Land first.", "Warning")
    end
    CombatFx.play(player, kind, info)
    RemoteEvents.CombatEvent:FireServer(if heavy == true then true else nil)
end

-- ---------- drawing and sheathing ----------
local DRAW_KEYS = { [Enum.KeyCode.One] = true, [Enum.KeyCode.ButtonX] = true }

-- a weapon to draw, and nothing in the way: not cultivating, not carrying an egg
local function canToggle()
    return player:GetAttribute("WeaponId") ~= nil and player:GetAttribute("IsCultivating") ~= true
        and player:GetAttribute("CarryingEgg") == nil
end

local function toggleDrawn()
    if canToggle() then
        RemoteEvents.WeaponDrawEvent:FireServer(player:GetAttribute("WeaponDrawn") ~= true)
    end
end

-- slot 1 of the inventory bar: the weapon's picture (its forged element's glow too) and name, lit and marked EQUIPPED while in hand
local slot = Hud.Inventory.addSlot(1, { Name = "WeaponSlot" })
local shownWeapon = nil -- the weapon and element the slot's picture shows: it's rebuilt only when they change
slot.Button.Activated:Connect(function()
    if player:GetAttribute("WeaponId") == nil then
        message:show("You have no weapon. Buy one at the Blacksmith on Yggdrasil.", "Info")
    elseif player:GetAttribute("CarryingEgg") ~= nil then
        message:show("Your hands are full: bring the egg home first.", "Warning")
    elseif player:GetAttribute("IsCultivating") == true then
        message:show(if UiKit.usingTouch() then "Stop cultivating first (tap the lotus)." else "Stop cultivating first (press E).", "Info")
    else
        toggleDrawn()
    end
end)

local function refreshSlot()
    local weaponId = player:GetAttribute("WeaponId")
    local weapon = Shop.weapon(weaponId)
    if not weapon then
        shownWeapon = nil
        slot.setEmpty("NO\nWEAPON", "Buy one at the Blacksmith")
        return
    end
    local elementName = player:GetAttribute("WeaponElement")
    local key = weaponId .. "|" .. tostring(elementName)
    if key ~= shownWeapon then
        shownWeapon = key
        local element = Shop.element(elementName)
        local picture = Portraits.weapon(weaponId, element and element.Color, 56)
        picture.BackgroundTransparency = 1
        local edge = picture:FindFirstChildOfClass("UIStroke")
        if edge then
            edge:Destroy()
        end
        slot.setItem(weapon.Name, picture)
    end
    slot.setEquipped(player:GetAttribute("WeaponDrawn") == true)
end
for _, name in { "WeaponId", "WeaponElement", "WeaponDrawn" } do
    player:GetAttributeChangedSignal(name):Connect(refreshSlot)
end
refreshSlot()

-- ---------- combat forms (shared/FormRules) ----------
-- There is no form button (the owner, 2026-11-24: "remove the form button, we don't need that"): a player fights with the highest form of their weapon's family that their
-- realm has unlocked (FormRules.resolve with no choice), the server and the client alike, so a new form simply arrives with the realm that opens it.

-- ---------- the heavy strike: hold, and let go (FormRules.heavy) ----------
-- Holding R (gamepad: D-pad right) or swiping up from the touch Strike button draws the body into the wind-up of the form's finisher (CombatFx.charge); letting go after
-- FormRules.HEAVY_HOLD strikes that finisher at once from anywhere in the chain, and the chain begins again after it. Letting go sooner is an ordinary light strike.
-- (Not the right mouse button: it turns the camera.) The server prices a heavy strike so that nothing but heavy strikes deals no more than the chain does.
local HEAVY_KEY = Enum.KeyCode.R
local HEAVY_PAD = Enum.KeyCode.DPadRight
local SWIPE = 40 -- pixels up from where a finger began on the Strike button
local charge = nil -- { Source = "Key" | "Gamepad" | "Touch", Since }

local function heavyPlan()
    local kind, base = strikeBase()
    return kind, FormRules.plan(kind, nil, Shop.playerRealmIndex(player), base, mine, os.clock(), true)
end

beginCharge = function(source)
    local humanoid = player.Character and player.Character:FindFirstChildOfClass("Humanoid")
    if charge or not humanoid or humanoid.Health <= 0 or player:GetAttribute("IsCultivating") == true or player:GetAttribute("CarryingEgg") ~= nil then
        return
    end
    charge = { Source = source, Since = os.clock() }
    if player:GetAttribute("WeaponId") ~= nil and player:GetAttribute("WeaponDrawn") ~= true then
        RemoteEvents.WeaponDrawEvent:FireServer(true) -- (a weapon is in the hand to wind up with)
    end
end

endCharge = function(fire)
    local held = charge and os.clock() - charge.Since or 0
    charge = nil
    if fire and held >= FormRules.HEAVY_HOLD then
        strike(false, true)
    else
        CombatFx.chargeEnd(player)
        if fire then
            strike(false, false) -- (a short press of the heavy input is a light strike)
        end
    end
end

-- while a strike button is held, the next strike comes at each cooldown; letting go (or the window losing focus) stops it
RunService.Heartbeat:Connect(function()
    if holding == "Mouse" and not UserInputService:IsMouseButtonPressed(Enum.UserInputType.MouseButton1) then
        holding = nil
    elseif holding == "Gamepad" and not UserInputService:IsGamepadButtonDown(Enum.UserInputType.Gamepad1, Enum.KeyCode.ButtonR2) then
        holding = nil
    elseif holding == "Touch" and (not touchHeld or touchHeld.UserInputState == Enum.UserInputState.End
        or touchHeld.UserInputState == Enum.UserInputState.Cancel) then
        -- (the finger that began the hold has lifted, wherever: its button's own InputEnded only fires when it lifts over the button. UserInputService has no
        -- GetTouches: this line called it from 2026-11-18, and on every frame of a held Strike tap on a phone it raised an error and the hold never repeated)
        holding = nil
    end
    -- a swipe up from the Strike button is a heavy strike's charge, not another light one
    if holding == "Touch" and touchHeld and touchStart and touchStart.Y - touchHeld.Position.Y >= SWIPE then
        holding = nil
        beginCharge("Touch")
    end
    if holding then
        strike(true)
    end
    if charge then
        local source = charge.Source
        if source == "Touch" and (not touchHeld or touchHeld.UserInputState == Enum.UserInputState.End
            or touchHeld.UserInputState == Enum.UserInputState.Cancel) then
            endCharge(true)
        elseif source == "Key" and not UserInputService:IsKeyDown(HEAVY_KEY) then
            endCharge(true)
        elseif source == "Gamepad" and not UserInputService:IsGamepadButtonDown(Enum.UserInputType.Gamepad1, HEAVY_PAD) then
            endCharge(true)
        elseif charge then
            local kind, info = heavyPlan()
            if info then
                CombatFx.charge(player, kind, info, math.min(1, (os.clock() - charge.Since) / FormRules.HEAVY_HOLD))
            end
        end
    end
end)
UserInputService.WindowFocusReleased:Connect(function()
    holding = nil
    if charge then
        endCharge(false)
    end
end)

UserInputService.InputBegan:Connect(function(input, gameProcessed)
    if gameProcessed then
        return
    end
    if input.UserInputType == Enum.UserInputType.MouseButton1 then
        holding = "Mouse"
        strike()
    elseif input.KeyCode == Enum.KeyCode.ButtonR2 then
        holding = "Gamepad"
        strike()
    elseif DRAW_KEYS[input.KeyCode] then
        toggleDrawn()
    elseif input.KeyCode == HEAVY_KEY then
        beginCharge("Key")
    elseif input.KeyCode == HEAVY_PAD then
        beginCharge("Gamepad")
    end
end)
UserInputService.InputEnded:Connect(function(input)
    if input.UserInputType == Enum.UserInputType.MouseButton1 and holding == "Mouse"
        or input.KeyCode == Enum.KeyCode.ButtonR2 and holding == "Gamepad" then
        holding = nil
    end
    if charge and (input.KeyCode == HEAVY_KEY and charge.Source == "Key" or input.KeyCode == HEAVY_PAD and charge.Source == "Gamepad") then
        endCharge(true)
    end
end)

RemoteEvents.CombatEvent.OnClientEvent:Connect(function(source, kind, position, step, damage, critical, target, form, hits)
    if typeof(source) ~= "Instance" or not source:IsA("Player") then
        return
    end
    -- the strike as the server counted it: its form and its step in that form's chain
    local info = if typeof(form) == "string" and typeof(step) == "number" then FormRules.strike(form, step, UNIT) else nil
    if source ~= player then
        CombatFx.play(source, kind, info)
    else
        if info and mine then
            mine = { Form = info.Form, Step = info.Step, At = mine.At } -- a press the server dropped can't leave our count wrong
        end
        ComboCounter.set(hits, info ~= nil and info.Finisher)
    end
    if typeof(position) == "Vector3" then
        CombatFx.hit(source, position, {
            damage = if typeof(damage) == "number" then damage else nil,
            critical = critical == true,
            target = if typeof(target) == "Instance" and target:IsA("Model") then target else nil,
        })
    elseif source == player then
        CombatFx.missed(player) -- (a blow shown from our own look at it, before this answer, is dropped)
    end
end)

-- the touch button strikes as the finger lands and keeps striking while it stays down (so a tap's release does nothing more)
local strikeButton = TouchActions.add("Strike", "Strike", function() end)
if strikeButton then
    strikeButton.InputBegan:Connect(function(input)
        if input.UserInputType == Enum.UserInputType.Touch then
            holding = "Touch"
            touchHeld = input
            touchStart = input.Position
            strike()
        end
    end)
    strikeButton.InputEnded:Connect(function(input)
        if input.UserInputType == Enum.UserInputType.Touch and holding == "Touch" then
            holding = nil
        end
    end)
end
