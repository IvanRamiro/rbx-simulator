-- UI audit (Studio only; never shipped). In Play, put this in a ModuleScript the client can require, then call
-- require(it)(Vector2.new(844, 390), "label") from the Client command bar, with the player's HudTestViewport attribute set to
-- the same size (and HudTestTouch true for the touch buttons). Returns one line per issue. Used for the UI audit of 2026-11-11.
-- VIEW = the screen size to judge against (nil: the real one).
-- Every visible element is placed on a virtual screen of that size (each top-level piece keeps its anchor to the screen's
-- edges; what's inside keeps its offset from it), then checked: text that doesn't fit, off the screen, clipped by a
-- ClipsDescendants parent, poking out of its window, small tap targets, and top-level pieces overlapping each other.
return function(VIEW, LABEL)
local p = game.Players.LocalPlayer
local pg = p.PlayerGui
local inset = game:GetService("GuiService"):GetGuiInset()
local real = workspace.CurrentCamera.ViewportSize
local V = VIEW or real
local SKIP_GUIS = { Freecam = true, GuardianBarLayer = true, WorldMarkers = true, DamageNumbers = true, PerfProbe = true, ProximityPrompts = true }

local function shown(g)
    local x = g
    while x and x ~= pg do
        if x:IsA("GuiObject") and not x.Visible then return false end
        if x:IsA("LayerCollector") and not x.Enabled then return false end
        if x:IsA("CanvasGroup") and x.GroupTransparency > 0.9 then return false end
        x = x.Parent
    end
    return true
end

-- the top-level piece an element belongs to, and where that piece sits on the virtual screen
local function rootOf(g)
    local x = g
    while x.Parent and not x.Parent:IsA("LayerCollector") do x = x.Parent end
    return x, x.Parent
end
local function virtualRect(g)
    local root, gui = rootOf(g)
    local ignore = gui:IsA("ScreenGui") and gui.IgnoreGuiInset
    local top = if ignore then 0 else inset.Y
    local H = V.Y - top
    local pos = root.Position
    local rx = pos.X.Scale * V.X + pos.X.Offset - root.AnchorPoint.X * root.AbsoluteSize.X
    local ry = pos.Y.Scale * H + pos.Y.Offset - root.AnchorPoint.Y * root.AbsoluteSize.Y + top
    local dx = g.AbsolutePosition.X - root.AbsolutePosition.X
    local dy = g.AbsolutePosition.Y - root.AbsolutePosition.Y
    return rx + dx, ry + dy, g.AbsoluteSize.X, g.AbsoluteSize.Y, root
end

local issues = {}
local seenKey = {}
local function add(kind, g, detail)
    local name = g:GetFullName():gsub("^Players%.[^.]+%.PlayerGui%.", "")
    local key = kind .. name
    if seenKey[key] then return end
    seenKey[key] = true
    table.insert(issues, kind .. " | " .. name .. (detail and (" | " .. detail) or ""))
end

local roots = {}
for _, gui in pg:GetChildren() do
    if gui:IsA("ScreenGui") and gui.Enabled and not SKIP_GUIS[gui.Name] then
        for _, d in gui:GetDescendants() do
            if d:IsA("GuiObject") and shown(d) and d.AbsoluteSize.X > 0 and d.AbsoluteSize.Y > 0 then
                local x, y, w, h, root = virtualRect(d)
                roots[root] = true
                -- text that doesn't fit
                if (d:IsA("TextLabel") or d:IsA("TextButton") or d:IsA("TextBox")) and d.Text ~= "" and d.TextTransparency < 1 and not d.TextFits then
                    add("TEXT-DOESN'T-FIT", d, string.format("'%s' size %dx%d", d.Text:sub(1, 40), w, h))
                end
                -- off the screen
                if (x < -1 or y < -1 or x + w > V.X + 1 or y + h > V.Y + 1) and not d:FindFirstAncestorWhichIsA("ScrollingFrame") then
                    if d.BackgroundTransparency < 1 or d:IsA("TextLabel") or d:IsA("TextButton") or d:IsA("ImageLabel") or d:IsA("ImageButton") then
                        add("OFF-SCREEN", d, string.format("x %d..%d y %d..%d (screen %dx%d)", x, x + w, y, y + h, V.X, V.Y))
                    end
                end
                -- clipped by a ClipsDescendants ancestor (not a scroll list, which clips on purpose)
                local a = d.Parent
                while a and a:IsA("GuiObject") do
                    if a.ClipsDescendants and not a:IsA("ScrollingFrame") then
                        local ap, as = a.AbsolutePosition, a.AbsoluteSize
                        local dp, ds = d.AbsolutePosition, d.AbsoluteSize
                        if (d:IsA("TextLabel") or d:IsA("TextButton") or d:IsA("ImageLabel")) and (dp.X < ap.X - 2 or dp.Y < ap.Y - 2 or dp.X + ds.X > ap.X + as.X + 2 or dp.Y + ds.Y > ap.Y + as.Y + 2) then
                            add("CLIPPED", d, "by " .. a.Name)
                        end
                        break
                    end
                    a = a.Parent
                end
                -- poking out of its window (HudWindows frames)
                if root.Parent and root.Parent.Name == "HudWindows" and d ~= root then
                    local rp, rs = root.AbsolutePosition, root.AbsoluteSize
                    local dp, ds = d.AbsolutePosition, d.AbsoluteSize
                    local inScroll = d:FindFirstAncestorWhichIsA("ScrollingFrame") ~= nil
                    if not inScroll and (d.BackgroundTransparency < 1 or d:IsA("TextButton")) and (dp.X < rp.X - 3 or dp.Y < rp.Y - 3 or dp.X + ds.X > rp.X + rs.X + 3 or dp.Y + ds.Y > rp.Y + rs.Y + 3) then
                        add("OUT-OF-WINDOW", d, string.format("%dx%d at %d,%d; window %d,%d %dx%d", ds.X, ds.Y, dp.X, dp.Y, rp.X, rp.Y, rs.X, rs.Y))
                    end
                end
                -- tap targets
                if d:IsA("GuiButton") and d.Active and (w < 36 or h < 28) then
                    add("SMALL-TARGET", d, string.format("%dx%d", w, h))
                end
            end
        end
    end
end

-- top-level pieces overlapping each other (each piece's visible children, so a region's empty box doesn't count)
local boxes = {}
for root in roots do
    for _, c in (if root:IsA("Frame") and root.BackgroundTransparency >= 1 and #root:GetChildren() > 0 then root:GetChildren() else { root }) do
        if c:IsA("GuiObject") and shown(c) and c.AbsoluteSize.X > 4 and c.AbsoluteSize.Y > 4 and not (c.Name == "TakeEggMarks") then
            local x, y, w, h = virtualRect(c)
            local gui = root:FindFirstAncestorWhichIsA("ScreenGui")
            table.insert(boxes, { c = c, x = x, y = y, w = w, h = h, gui = gui, root = root })
        end
    end
end
for i = 1, #boxes do
    for j = i + 1, #boxes do
        local a, b = boxes[i], boxes[j]
        if a.root ~= b.root then
            local ox = math.min(a.x + a.w, b.x + b.w) - math.max(a.x, b.x)
            local oy = math.min(a.y + a.h, b.y + b.h) - math.max(a.y, b.y)
            if ox > 4 and oy > 4 then
                local n1 = a.c:GetFullName():gsub("^Players%.[^.]+%.PlayerGui%.", "")
                local n2 = b.c:GetFullName():gsub("^Players%.[^.]+%.PlayerGui%.", "")
                table.insert(issues, string.format("OVERLAP | %s (order %d) x %s (order %d) | %dx%d", n1, a.gui.DisplayOrder, n2, b.gui.DisplayOrder, ox, oy))
            end
        end
    end
end

table.sort(issues)
return string.format("[%s] screen %dx%d (real %dx%d), %d issues\n", LABEL, V.X, V.Y, real.X, real.Y, #issues) .. table.concat(issues, "\n")
end
