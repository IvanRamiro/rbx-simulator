-- Gifting a pet, the client's half (the owner's improvement list, item 19; server/Pets/GiftService decides everything): the picker that opens from a pet card's gift button
-- (the players here in this server), the question before it is sent, the offer that comes to the receiver (accept or no thanks), and the notices for how it went.
--   GiftUi.open(pet)   pet: a record of the inventory snapshot ({ InstanceId, PetId, Level, Size, Mutation, ... })
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GiftRules = require(ReplicatedStorage:WaitForChild("GiftRules"))
local RemoteEvents = require(ReplicatedStorage:WaitForChild("RemoteEvents"))
local UI = script.Parent.Parent:WaitForChild("UI")
local ConfirmDialog = require(UI:WaitForChild("ConfirmDialog"))
local HudMetrics = require(UI:WaitForChild("HudMetrics"))
local Portraits = require(UI:WaitForChild("Portraits"))
local Toast = require(UI:WaitForChild("Toast"))
local UiKit = require(UI:WaitForChild("UiKit"))
local UiTheme = require(UI:WaitForChild("UiTheme"))
local Sfx = require(script.Parent.Parent:WaitForChild("Audio"):WaitForChild("Sfx"))

local GiftUi = {}

local player = Players.LocalPlayer
local C = UiTheme.Colors
local PAD = UiTheme.Pad.Window
local TOP = UiTheme.Height.TitleBar + UiTheme.Space.M
local message = Toast.new("GiftMessage", C.Highlight, 5)

-- ---------- the picker ----------
local gui = Instance.new("ScreenGui")
gui.Name = "GiftPicker"
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = true
gui.DisplayOrder = 39 -- under the question (ConfirmDialog, 40)
gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
gui.Enabled = false
gui.Parent = player:WaitForChild("PlayerGui")

local shade = Instance.new("TextButton")
shade.Name = "Shade"
shade.Text = ""
shade.AutoButtonColor = false
shade.BackgroundColor3 = Color3.new(0, 0, 0)
shade.BackgroundTransparency = 0.45
shade.BorderSizePixel = 0
shade.Size = UDim2.fromScale(1, 1)
shade.Parent = gui

local panel = UiKit.panel({ Name = "Panel", Size = UDim2.fromOffset(400, 270), AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), ZIndex = 2, Parent = gui })
panel.BackgroundTransparency = 0
panel:FindFirstChildOfClass("UIGradient").Transparency = NumberSequence.new(0)
panel.Active = true
local panelScale = Instance.new("UIScale")
panelScale.Parent = panel
local function rescale()
    panelScale.Scale = HudMetrics.windowScale()
    panel.Position = UDim2.new(0.5, 0, 0.5, game:GetService("GuiService"):GetGuiInset().Y / 2)
end
HudMetrics.Changed:Connect(rescale)
rescale()
local _, closeButton = UiKit.titleBar(panel, "GIFT A PET")
local body = Instance.new("Frame")
body.Name = "Body"
body.BackgroundTransparency = 1
body.Position = UDim2.fromOffset(PAD, TOP)
body.Size = UDim2.new(1, -PAD * 2, 1, -(TOP + PAD))
body.Parent = panel
local intro = UiKit.label({ Name = "Intro", TextSize = 14, TextWrapped = true, TextColor3 = C.Text, TextYAlignment = Enum.TextYAlignment.Top, Size = UDim2.new(1, 0, 0, 40), Parent = body })
local list = UiKit.scroll({ Name = "Players", Position = UDim2.fromOffset(0, 46), Size = UDim2.new(1, 0, 1, -(46 + UiTheme.Height.Button + UiTheme.Space.M)), Parent = body })
local cancel = UiKit.button({ Name = "Cancel", Text = "CANCEL", Tone = "Quiet", AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.fromScale(0.5, 1), Size = UDim2.new(0.5, 0, 0, UiTheme.Height.Button), Parent = body })

local function close()
    gui.Enabled = false
end
cancel.Activated:Connect(close)
closeButton.Activated:Connect(close)

local function ask(pet, other)
    close()
    ConfirmDialog.show({
        Title = "GIFT A PET", Picture = Portraits.pet(pet.PetId, 72), ConfirmText = "SEND GIFT", CancelText = "NOT NOW", ConfirmTone = "Go", Seconds = 1,
        Text = "Give " .. GiftRules.describe(pet) .. " to " .. other.DisplayName .. "? They have to say yes, and then it is theirs. You can't get it back.",
        OnConfirm = function()
            RemoteEvents.GiftEvent:FireServer("Offer", other.UserId, pet.InstanceId)
        end,
    })
end

function GiftUi.open(pet)
    for _, child in list:GetChildren() do
        if child:IsA("GuiObject") then
            child:Destroy()
        end
    end
    local others = {}
    for _, other in Players:GetPlayers() do
        if other ~= player then
            table.insert(others, other)
        end
    end
    table.sort(others, function(a, b)
        return a.DisplayName:lower() < b.DisplayName:lower()
    end)
    intro.Text = "Give " .. GiftRules.describe(pet) .. " to a player in this server."
    if #others == 0 then
        UiKit.empty(list, "No one else is in this server. A gift goes to a player here with you.")
    end
    UiKit.list(list, { Padding = UDim.new(0, UiTheme.Space.S) })
    for index, other in others do
        local row = UiKit.button({ Name = "Player", Text = other.DisplayName, Tone = "Accent", LayoutOrder = index, Size = UDim2.new(1, -6, 0, UiTheme.Height.Button), Parent = list })
        row.Activated:Connect(function()
            ask(pet, other)
        end)
    end
    rescale()
    gui.Enabled = true
    Sfx.play("Open")
end

-- ---------- what the server says ----------
RemoteEvents.GiftEvent.OnClientEvent:Connect(function(kind, a, b)
    if kind == "Offer" and typeof(a) == "table" and typeof(a.Pet) == "table" then
        local seconds = if typeof(a.Seconds) == "number" then a.Seconds else GiftRules.Config.OfferSeconds
        ConfirmDialog.show({
            Title = "A GIFT FOR YOU", Picture = Portraits.pet(a.Pet.PetId, 72), ConfirmText = "ACCEPT", CancelText = "NO THANKS", ConfirmTone = "Go", Seconds = 0, AutoClose = seconds,
            Text = tostring(a.FromName) .. " wants to give you " .. GiftRules.describe(a.Pet) .. ". Take it?",
            OnConfirm = function()
                RemoteEvents.GiftEvent:FireServer("Accept")
            end,
            OnCancel = function()
                RemoteEvents.GiftEvent:FireServer("Decline")
            end,
        })
    elseif kind == "Sent" then
        message:show("Gift sent to " .. tostring(a) .. ". Waiting for them to answer.", "Info")
    elseif kind == "Accepted" then
        Sfx.play("RewardClaim")
        message:show(tostring(a) .. " took your gift.", "Success")
    elseif kind == "Declined" then
        message:show("They said no thanks. The pet is still yours.", "Info")
    elseif kind == "Lapsed" then
        message:show("No answer. The pet is still yours.", "Info")
    elseif kind == "Refused" then
        message:show(tostring(a), "Warning")
    elseif kind == "Cancelled" then
        ConfirmDialog.close()
        message:show(tostring(a), "Info")
    elseif kind == "Received" then
        Sfx.play("RewardClaim")
        message:show("You got " .. tostring(a) .. " from " .. tostring(b) .. "!", "Reward")
    end
end)

return GiftUi
