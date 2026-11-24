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

-- Input feel: a press up to BUFFER seconds before the cooldown ends still counts, and fires the moment it ends; holding the button (mouse,
-- gamepad R2, the touch button) strikes again at each cooldown. The cooldown itself stays the server's (CombatService): this only stops a
-- press that came a hair early from being thrown away. A press longer before it is dropped, as before.
local BUFFER = 0.12
local waiting = false -- a buffered press is waiting for the cooldown
local holding = nil   -- what is held: "Mouse", "Gamepad" or "Touch"

local function strike(repeating)
    local character = player.Character
    local humanoid = character and character:FindFirstChildOfClass("Humanoid")
    if not humanoid or humanoid.Health <= 0 or player:GetAttribute("IsCultivating") == true
        or player:GetAttribute("CarryingEgg") ~= nil then -- both hands are round the egg
        return
    end
    local now = os.clock()
    local kind, base = strikeBase()
    if now < readyAt then
        if not repeating and not waiting and readyAt - now <= BUFFER then
            waiting = true
            task.delay(readyAt - now + 0.002, function()
                waiting = false
                strike(true)
            end)
        end
        return
    end
    local info = FormRules.plan(kind, player:GetAttribute("Form" .. kind), Shop.playerRealmIndex(player), base, mine, now)
    if not info then
        return
    end
    readyAt = now + info.Cooldown
    mine = { Form = info.Form, Step = info.Step, At = now }
    if player:GetAttribute("IsFlying") == true and not airNoted then
        airNoted = true
        message:show("You can't hit guardians from the air. Land first.", "Warning")
    end
    CombatFx.play(player, kind, info)
    RemoteEvents.CombatEvent:FireServer()
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

-- ---------- combat forms (the owner, 2026-11-24): slot 2 of the inventory bar, key 2 ----------
-- Every weapon of a family shares that family's forms (shared/FormRules); the slot shows the form in use and pressing it asks the server (FormEvent) for
-- the next form this weapon's family has unlocked. Each family remembers its own (the server's "Form<Family>" attribute).
local formSlot = Hud.Inventory.addSlot(2, { Name = "FormSlot" })
local formNote = Toast.new("FormMessage", Color3.new(1, 1, 1), 3)

local function familyNow()
    local weapon = Shop.weapon(player:GetAttribute("WeaponId"))
    return if weapon then weapon.Kind else "Palm"
end

-- the form in use for the weapon in hand, and the unlocked ones of its family in order
local function formsNow()
    local family = familyNow()
    local realm = Shop.playerRealmIndex(player)
    local current = FormRules.resolve(family, player:GetAttribute("Form" .. family), realm)
    local open = {}
    for _, id in FormRules.Families[family] do
        if FormRules.unlocked(id, realm) then
            table.insert(open, id)
        end
    end
    return family, current, open
end

local function refreshForm()
    local family, current = formsNow()
    -- "FORM 1/3" on two lines: a form's name ("CRESCENT") does not fit the tile at its text size and wrapped mid-word (seen in the Device Simulator on a
    -- Galaxy A06); the name comes in the notice when a form is chosen
    local at = table.find(FormRules.Families[family], current) or 1
    formSlot.setEmpty("FORM\n" .. at .. "/" .. #FormRules.Families[family], "") -- (no caption: it ran into the weapon slot's)
end
for _, name in { "WeaponId", "FormSword", "FormSpear", "FormPalm" } do
    player:GetAttributeChangedSignal(name):Connect(refreshForm)
end
refreshForm()
task.spawn(function() -- a new realm can open a form: look now and then
    while true do
        task.wait(2)
        refreshForm()
    end
end)

local formAskedAt = 0
local function nextForm()
    if player:GetAttribute("IsCultivating") == true or player:GetAttribute("CarryingEgg") ~= nil then
        return
    end
    if os.clock() - formAskedAt < FormRules.SWITCH_GAP then
        return
    end
    local family, current, open = formsNow()
    if #open < 2 then
        local total = #FormRules.Families[family]
        formNote:show(if total > 1 then "More forms open as you reach higher realms." else "This weapon has one form.", "Info")
        return
    end
    formAskedAt = os.clock()
    local at = table.find(open, current) or 1
    local choice = open[at % #open + 1]
    RemoteEvents.FormEvent:FireServer(choice)
    formNote:show(FormRules.Forms[choice].Name .. ": " .. FormRules.Forms[choice].Identity, "Info")
end
formSlot.Button.Activated:Connect(nextForm)

-- while a strike button is held, the next strike comes at each cooldown; letting go (or the window losing focus) stops it
RunService.Heartbeat:Connect(function()
    if holding == "Mouse" and not UserInputService:IsMouseButtonPressed(Enum.UserInputType.MouseButton1) then
        holding = nil
    elseif holding == "Gamepad" and not UserInputService:IsGamepadButtonDown(Enum.UserInputType.Gamepad1, Enum.KeyCode.ButtonR2) then
        holding = nil
    elseif holding == "Touch" and #UserInputService:GetTouches() == 0 then
        holding = nil
    end
    if holding then
        strike(true)
    end
end)
UserInputService.WindowFocusReleased:Connect(function()
    holding = nil
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
    elseif input.KeyCode == Enum.KeyCode.Two then
        nextForm()
    end
end)
UserInputService.InputEnded:Connect(function(input)
    if input.UserInputType == Enum.UserInputType.MouseButton1 and holding == "Mouse"
        or input.KeyCode == Enum.KeyCode.ButtonR2 and holding == "Gamepad" then
        holding = nil
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
            strike()
        end
    end)
    strikeButton.InputEnded:Connect(function(input)
        if input.UserInputType == Enum.UserInputType.Touch and holding == "Touch" then
            holding = nil
        end
    end)
end
