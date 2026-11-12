-- Labels over places in the world, drawn on the screen each frame (as the guardian's bar is): a BillboardGui drawn
-- AlwaysOnTop didn't show in Studio (2026-11-11: the way home read "YGGDRASIL 448m" in the middle of the screen, and nothing
-- was there). With `edge`, a place off the screen or behind the camera is shown at the screen's edge, an arrow pointing to it.
--
--   local marker = WorldMarkers.new(color, edge)   then set marker.world (a Vector3, or nil to hide it) and marker.label.Text
--   WorldMarkers.drop(marker)                      removes it
--
-- Used for the way home with a stolen egg and a dropped egg's countdown (GuardianController) and the quest's way (QuestController).
local GuiService = game:GetService("GuiService")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Hud = require(script.Parent:WaitForChild("Hud"))
local HudMetrics = require(script.Parent:WaitForChild("HudMetrics"))
local UiTheme = require(script.Parent:WaitForChild("UiTheme"))

local WorldMarkers = {}

local MARKER_EDGE = 70 -- pixels (at the HUD's scale) an edge marker keeps from the screen's edges
local markerLayer = Instance.new("ScreenGui")
markerLayer.Name = "WorldMarkers"
markerLayer.ResetOnSpawn = false
markerLayer.IgnoreGuiInset = true -- so a marker's place is the viewport's own pixel
markerLayer.DisplayOrder = -1     -- under the HUD's panels
markerLayer.Parent = Players.LocalPlayer:WaitForChild("PlayerGui")
local markers = {} -- [marker] = true

function WorldMarkers.new(color, edge)
    local frame = Instance.new("Frame")
    frame.Name = "Marker"
    frame.BackgroundTransparency = 1
    frame.AnchorPoint = Vector2.new(0.5, 0.5)
    frame.Size = UDim2.fromOffset(190, 44)
    frame.Visible = false
    frame.Parent = markerLayer
    local scale = Instance.new("UIScale")
    scale.Parent = frame
    local label = Instance.new("TextLabel")
    label.Name = "Label"
    label.BackgroundTransparency = 1
    label.Size = UDim2.new(1, 0, 0, 26)
    label.FontFace = UiTheme.Fonts.Number
    label.TextSize = 20
    label.TextColor3 = color
    label.TextStrokeTransparency = 0.25
    label.Parent = frame
    local arrow = Instance.new("TextLabel")
    arrow.Name = "Arrow"
    arrow.BackgroundTransparency = 1
    arrow.AnchorPoint = Vector2.new(0.5, 0.5)
    arrow.Position = UDim2.new(0.5, 0, 0, 40)
    arrow.Size = UDim2.fromOffset(30, 30)
    arrow.FontFace = UiTheme.Fonts.Number
    arrow.TextSize = 26
    arrow.Text = "v"
    arrow.TextColor3 = color
    arrow.TextStrokeTransparency = 0.25
    arrow.Parent = frame
    local marker = { frame = frame, label = label, arrow = arrow, scale = scale, edge = edge, world = nil }
    markers[marker] = true
    return marker
end

function WorldMarkers.drop(marker)
    if marker then
        markers[marker] = nil
        marker.frame:Destroy()
    end
end

local function placeMarkers()
    local camera = Workspace.CurrentCamera
    if not camera then
        return
    end
    -- a cinematic (the hatch's HatchCinema) has the screen: markers wait
    local cinema = Players.LocalPlayer.PlayerGui:FindFirstChild("HatchCinema")
    if cinema and cinema.Enabled then
        for marker in markers do
            marker.frame.Visible = false
        end
        return
    end
    local view = camera.ViewportSize
    local scale = HudMetrics.scale()
    local margin = MARKER_EDGE * scale
    local now = os.clock()
    for marker in markers do
        local world = marker.world
        if not world then
            marker.frame.Visible = false
            continue
        end
        marker.scale.Scale = scale
        local point = camera:WorldToViewportPoint(world)
        local x, y = point.X, point.Y
        local inside = point.Z > 0 and x >= margin and x <= view.X - margin and y >= margin and y <= view.Y - margin
        if inside or not marker.edge then
            marker.frame.Visible = point.Z > 0
            marker.frame.Position = UDim2.fromOffset(x, y)
            marker.arrow.Rotation = 0
            marker.arrow.Position = UDim2.new(0.5, 0, 0, 40 + 3 * math.sin(now * 5)) -- it bobs, pointing down at the place
            continue
        end
        -- off the screen: along the line from the screen's middle toward the place, stopped at the edge of the room the
        -- HUD leaves (clear of the left column: under it, a marker was hidden behind the menu)
        local centre = view / 2
        local toward = Vector2.new(x, y) - centre
        if point.Z <= 0 then
            toward = -toward -- behind the camera the projection is mirrored
        end
        if toward.Magnitude < 1 then
            toward = Vector2.new(0, 1)
        end
        local status = Hud.Status
        local left = math.max(margin, (if status.Visible then status.AbsolutePosition.X + status.AbsoluteSize.X else 0) + 100 * scale)
        local inset = GuiService:GetGuiInset().Y
        local top = inset + margin
        -- and under the top band's middle pieces (the currencies, a notification): at the top edge a marker sat on the
        -- notification's words (a new player's run, 2026-11-11)
        for _, piece in { Hud.Currency, Hud.Notice, Hud.Banner } do
            if piece and piece.Visible and piece.AbsoluteSize.Y > 1 and piece.AbsolutePosition.Y < centre.Y then
                local below = piece.AbsolutePosition.Y + piece.AbsoluteSize.Y + inset + 30 * scale
                if math.abs((piece.AbsolutePosition.X + piece.AbsoluteSize.X / 2) - centre.X) < view.X * 0.3 then
                    top = math.max(top, below)
                end
            end
        end
        -- and above the Cultivation dock: at the bottom of the screen, a marker went behind it (only "9m" showed)
        local dock = Hud.Dock
        local bottom = view.Y - margin
        if dock.Visible and dock.AbsoluteSize.Y > 1 then
            bottom = math.min(bottom, dock.AbsolutePosition.Y + inset - 34 * scale)
        end
        bottom = math.max(bottom, centre.Y + 1)
        local reachX = if toward.X < 0 then (centre.X - left) / -toward.X else (view.X - margin - centre.X) / math.max(toward.X, 1e-3)
        local reachY = if toward.Y < 0 then (centre.Y - top) / -toward.Y else (bottom - centre.Y) / math.max(toward.Y, 1e-3)
        local at = centre + toward * math.max(0, math.min(reachX, reachY))
        -- the words are wider than the marker's frame: at a side edge the centre comes in by half their width, so they stay
        -- on the screen (2026-11-12: "THE GREAT ROOT  398 stud" ran off the right edge)
        local halfText = marker.label.TextBounds.X / 2 + 6 * scale
        at = Vector2.new(math.clamp(at.X, math.max(left, halfText), math.max(view.X - halfText, math.max(left, halfText))), at.Y)
        -- and below the quest panel at the top right, which it lay on (2026-11-12)
        local quest = Hud.Quest
        if quest and quest.Visible and quest.AbsoluteSize.Y > 1 then
            local questTop = quest.AbsolutePosition.Y + inset
            local questBottom = questTop + quest.AbsoluteSize.Y
            if at.X + halfText > quest.AbsolutePosition.X and at.Y > questTop - 30 * scale and at.Y < questBottom + 30 * scale then
                at = Vector2.new(at.X, math.min(questBottom + 30 * scale, math.max(bottom, centre.Y + 1)))
            end
        end
        marker.frame.Visible = true
        marker.frame.Position = UDim2.fromOffset(at.X, at.Y)
        -- the arrow leans out of the label toward the place ("v" points down: rotation 0 is downward)
        local direction = toward.Unit
        marker.arrow.Rotation = math.deg(math.atan2(-direction.X, direction.Y))
        -- just outside the words, on the place's side, so it never covers them
        local halfWords = marker.label.TextBounds.X / 2 + 16
        marker.arrow.Position = UDim2.new(0.5, direction.X * halfWords, 0, 13 + direction.Y * 26)
    end
end

RunService.RenderStepped:Connect(placeMarkers)

return WorldMarkers
