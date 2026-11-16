-- Draws the Hall of Records' boards (HallBoards: each board's look) on the hall's face parts (WorldBuilder.buildHallOfRecords:
-- invisible parts tagged RecordsConfig.Tag, each with a Board attribute), from the data RecordsService publishes in
-- ReplicatedStorage.HallOfRecords (one StringValue of JSON per board). A board is redrawn only when its data changes; the
-- Chronicle's "minutes ago" and the players' own "You" lines are refreshed in place. Each SurfaceGui lives in PlayerGui, adorned to
-- its face part (a ViewportFrame, the Rarest Beasts' portraits, only draws in a SurfaceGui there: seen in Studio, 2026-11-16); a face
-- part that streams out takes its board away, and it is drawn again when the part streams back in.
-- The SurfaceGuis light themselves (LightInfluence 0: readable at night without lamps) and hide past MaxDistance.
local CollectionService = game:GetService("CollectionService")
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local RecordsConfig = require(ReplicatedStorage:WaitForChild("RecordsConfig"))
local HallBoards = require(script.Parent:WaitForChild("HallBoards"))

local MAX_DISTANCE = 110 -- (from the hall's path and court; not from across the hub)
local TICK = 30 -- seconds between refreshes of the Chronicle's times and the "You" lines

local player = Players.LocalPlayer
local folder = ReplicatedStorage:WaitForChild(RecordsConfig.FolderName)

local data = {} -- [data id] = the decoded board data
local faces = {} -- [face part] = { gui, board id }

local function decode(value)
    local ok, result = pcall(HttpService.JSONDecode, HttpService, value.Value)
    return if ok and typeof(result) == "table" then result else {}
end

local function draw(part)
    local entry = faces[part]
    local board = entry and HallBoards.Boards[entry.board]
    if not board then
        return
    end
    local canvas = entry.gui:FindFirstChild("Canvas")
    if canvas then
        canvas:Destroy()
    end
    canvas = Instance.new("Frame")
    canvas.Name = "Canvas"
    canvas.BackgroundTransparency = 1
    canvas.Size = UDim2.fromScale(1, 1)
    local ok, err = pcall(board.Draw, canvas, if board.Data then data[board.Data] or {} else {}, {
        you = HallBoards.you(), now = os.time(), px = Vector2.new(part.Size.X, part.Size.Y) * board.PixelsPerStud })
    if not ok then
        warn("HallOfRecords: couldn't draw " .. entry.board .. ": " .. tostring(err))
    end
    canvas.Parent = entry.gui
end

local function addFace(part)
    local boardId = part:GetAttribute("Board")
    local board = HallBoards.Boards[boardId]
    if not (part:IsA("BasePart") and board) or faces[part] then
        return
    end
    local gui = Instance.new("SurfaceGui")
    gui.Name = "Board"
    gui.Face = Enum.NormalId.Front
    gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
    gui.PixelsPerStud = board.PixelsPerStud
    gui.LightInfluence = 0
    gui.Brightness = 1
    gui.MaxDistance = MAX_DISTANCE
    gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
    gui.ClipsDescendants = true
    gui.ResetOnSpawn = false
    gui.Adornee = part
    gui.Name = "HallBoard_" .. boardId
    gui.Parent = player:WaitForChild("PlayerGui")
    faces[part] = { gui = gui, board = boardId }
    draw(part)
end

local function removeFace(part)
    local entry = faces[part]
    if entry then
        entry.gui:Destroy()
        faces[part] = nil
    end
end

local function redrawData(dataId)
    for part, entry in faces do
        local board = HallBoards.Boards[entry.board]
        if board and board.Data == dataId then
            draw(part)
        end
    end
end

local function watch(value)
    data[value.Name] = decode(value)
    value.Changed:Connect(function()
        data[value.Name] = decode(value)
        redrawData(value.Name)
    end)
end
for _, value in folder:GetChildren() do
    if value:IsA("StringValue") then
        watch(value)
    end
end
folder.ChildAdded:Connect(function(value)
    if value:IsA("StringValue") then
        watch(value)
        redrawData(value.Name)
    end
end)

CollectionService:GetInstanceAddedSignal(RecordsConfig.Tag):Connect(addFace)
CollectionService:GetInstanceRemovedSignal(RecordsConfig.Tag):Connect(removeFace)
for _, part in CollectionService:GetTagged(RecordsConfig.Tag) do
    task.spawn(addFace, part)
end

-- the boards with a "You" line follow the player's own numbers; the Chronicle's times move on
local function refreshYou()
    local you = HallBoards.you()
    for _, entry in faces do
        local words = HallBoards.youText(entry.board, you)
        local label = words and entry.gui:FindFirstChild("You", true)
        if label then
            label.Text = words
        end
    end
end
player:GetAttributeChangedSignal("RecordEggsSecured"):Connect(refreshYou)
player:GetAttributeChangedSignal("RecordPlayMinutes"):Connect(refreshYou)

while true do
    task.wait(TICK)
    refreshYou()
    for part, entry in faces do
        if HallBoards.Boards[entry.board].Ticks then
            draw(part)
        end
    end
end
