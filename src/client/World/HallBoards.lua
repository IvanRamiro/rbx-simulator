-- How each board in the Hall of Records looks (shared/RecordsConfig; drawn by HallOfRecords.client.lua). Every board has its own
-- object and its own look (the owner, 2026-11-16: "use different styles of achievement board"), in the game's own type (UiTheme:
-- Merriweather headings, Montserrat rows) so they read as one game:
--   Qi              the stele: the top three as round portraits on bronze rings (first raised), places 4-10 as engraved rows
--   PlayTime        the hourglass's ledger: rows of names and hours in the sand's colour, the top three with their portraits
--   Thieves         the notice board: pinned WANTED posters for the top three, a note for 4-8
--   Rarest          the showcase: six beast cards (the beast itself, its rarity's colour, size, odds, who hatched it)
--   RarestTitle     the showcase's name on its band
--   FirstsRealm, FirstsGuardian, FirstsBeast   the record slabs: names engraved in gold, each with its date
--   FeedLeft, FeedRight   the Chronicle's open book: the latest great moments in ink
--   HallTitle       the hall's name on the entrance's lintel
-- HallBoards.Boards[id].Draw(canvas, data, ctx) fills the SurfaceGui's canvas; ctx: the local player's numbers (ctx.you), the time
-- (ctx.now) and the canvas's size in pixels (ctx.px). Words are plain (the owner: "Use a more understandable words for players").
-- Every label, image and outline is about one draw call, and the hub is already heavy (600-1,000), so the boards are built from few
-- of them: a column of rows is one multi-line rich-text label, portraits only where a face matters, outlines only on headings
-- (measured in Play, 2026-11-16: the first build's eleven boards cost about 280 draw calls; this one about a third of that).
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GameConfig = require(ReplicatedStorage:WaitForChild("GameConfig"))
local NumberFormat = require(ReplicatedStorage:WaitForChild("NumberFormat"))
local PetRules = require(ReplicatedStorage:WaitForChild("PetRules"))
local RecordsConfig = require(ReplicatedStorage:WaitForChild("RecordsConfig"))
local UI = script.Parent.Parent:WaitForChild("UI")
local UiTheme = require(UI:WaitForChild("UiTheme"))

local HallBoards = {}

local FAMILY = "rbxasset://fonts/families/"
local F = {
    Head = UiTheme.Fonts.Header,
    Body = UiTheme.Fonts.Body,
    Strong = UiTheme.Fonts.Strong,
    Number = UiTheme.Fonts.Number,
    Heavy = UiTheme.Fonts.Heavy,
    Engraved = Font.new(FAMILY .. "RomanAntique.json", Enum.FontWeight.Regular),
    Poster = Font.new(FAMILY .. "Bangers.json", Enum.FontWeight.Regular),
    Hand = Font.new(FAMILY .. "Fondamento.json", Enum.FontWeight.Regular),
    Ink = Font.new(FAMILY .. "Merriweather.json", Enum.FontWeight.Regular),
}

local function rgb(r, g, b)
    return Color3.fromRGB(r, g, b)
end
-- the hall's own palette: bronze, gold leaf on stone, sand, parchment and ink
local C = {
    Gold = rgb(255, 214, 120), GoldDeep = rgb(214, 160, 64), Silver = rgb(222, 228, 238), BronzeLeaf = rgb(226, 150, 90),
    Bronze = rgb(176, 120, 66), Stone = rgb(26, 24, 28), StoneLine = rgb(120, 96, 66), Pale = rgb(236, 230, 214),
    Muted = rgb(176, 168, 152), Sand = rgb(244, 196, 112), Ink = rgb(58, 36, 22), InkFaded = rgb(128, 98, 70),
    Paper = rgb(238, 222, 184), PaperDark = rgb(196, 170, 120), Red = rgb(150, 34, 28), Pin = rgb(196, 44, 40),
    Outline = UiTheme.Colors.Outline,
}
local PLACE_INK = { C.Gold, C.Silver, C.BronzeLeaf }

-- ---------- pieces ----------
local function hex(c)
    return string.format("#%02X%02X%02X", math.floor(c.R * 255 + 0.5), math.floor(c.G * 255 + 0.5), math.floor(c.B * 255 + 0.5))
end

-- text safe inside rich text, cut to `most` characters
local function safe(s, most)
    s = tostring(s or "")
    if most and utf8.len(s) and utf8.len(s) > most then
        s = string.sub(s, 1, utf8.offset(s, most) - 1) .. "..."
    end
    return (string.gsub(string.gsub(string.gsub(s, "&", "&amp;"), "<", "&lt;"), ">", "&gt;"))
end

local function paint(s, color)
    return '<font color="' .. hex(color) .. '">' .. s .. "</font>"
end

local function sized(s, px)
    return '<font size="' .. math.max(1, math.floor(px)) .. '">' .. s .. "</font>"
end

local function frame(parent, props)
    local f = Instance.new("Frame")
    f.BorderSizePixel = 0
    f.BackgroundTransparency = 1
    for k, v in props do
        f[k] = v
    end
    f.Parent = parent
    return f
end

-- A label. Scaled (TextScaled) unless props.Px gives a fixed size in pixels (then rich text may set sizes and colours per line);
-- props.Outline puts a dark rim round light words on stone (headings only: each outline is another draw call).
local function text(parent, props)
    local l = Instance.new("TextLabel")
    l.BackgroundTransparency = 1
    l.BorderSizePixel = 0
    l.TextWrapped = false
    l.TextXAlignment = Enum.TextXAlignment.Left
    l.TextYAlignment = Enum.TextYAlignment.Center
    local outline, font, px = props.Outline, props.Font, props.Px
    props.Outline, props.Font, props.Px = nil, nil, nil
    for k, v in props do
        l[k] = v
    end
    l.FontFace = font or F.Body
    if px then
        l.RichText = true
        l.TextSize = math.max(1, math.floor(px))
    else
        l.TextScaled = true -- (TextTruncate would switch it off, so it is never set)
    end
    if outline then
        local s = Instance.new("UIStroke")
        s.Color = C.Outline
        s.Thickness = outline
        s.Transparency = 0.15
        s.ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual
        s.Parent = l
    end
    l.Parent = parent
    return l
end

local function headshot(parent, userId, props, ring, roundIt)
    local img = Instance.new("ImageLabel")
    img.BackgroundColor3 = C.Stone
    img.BackgroundTransparency = 0.2
    img.BorderSizePixel = 0
    img.ScaleType = Enum.ScaleType.Crop
    img.Image = if typeof(userId) == "number" and userId > 0
        then string.format("rbxthumb://type=AvatarHeadShot&id=%d&w=150&h=150", userId) else ""
    for k, v in props do
        img[k] = v
    end
    local a = Instance.new("UIAspectRatioConstraint")
    a.AspectRatio = 1
    a.Parent = img
    if roundIt ~= false then
        local c = Instance.new("UICorner")
        c.CornerRadius = UDim.new(0.5, 0)
        c.Parent = img
    end
    if ring then
        local s = Instance.new("UIStroke")
        s.Color = ring
        s.Thickness = 3
        s.ApplyStrokeMode = Enum.ApplyStrokeMode.Border
        s.Parent = img
    end
    img.Parent = parent
    return img
end

local function heading(parent, title, sub, color, font, y, h)
    text(parent, { Text = title, Font = font or F.Head, TextColor3 = color or C.Gold, Outline = 2,
        Position = UDim2.fromScale(0.04, y), Size = UDim2.fromScale(0.92, h), TextXAlignment = Enum.TextXAlignment.Center })
    if sub then
        text(parent, { Text = sub, Font = F.Strong, TextColor3 = C.Muted,
            Position = UDim2.fromScale(0.1, y + h + 0.004), Size = UDim2.fromScale(0.8, h * 0.42), TextXAlignment = Enum.TextXAlignment.Center })
    end
end

local function rule(parent, y, color, x0, x1)
    frame(parent, { BackgroundTransparency = 0.2, BackgroundColor3 = color or C.StoneLine,
        Position = UDim2.fromScale(x0 or 0.06, y), Size = UDim2.new((x1 or 0.94) - (x0 or 0.06), 0, 0, 2) })
end

local function name(row, most)
    return safe(if typeof(row.d) == "string" and row.d ~= "" then row.d else "A cultivator", most or 18)
end

-- a column of rows as one label: `lines` already rich; each row `rowPx` tall
local function column(parent, lines, x, y, w, rowPx, ctx, props)
    props = props or {}
    props.Text = table.concat(lines, "\n")
    props.Px = props.Px or rowPx * 0.72
    -- a line's pitch is about TextSize * LineHeight * 0.985 (measured in Play: 23.5 px at 20 px and 1.194): this lands each on its row
    props.LineHeight = rowPx / math.max(1, math.floor(props.Px)) / 0.985
    props.Position = UDim2.fromScale(x, y)
    props.Size = UDim2.new(w, 0, 0, rowPx * #lines + 4)
    props.TextYAlignment = Enum.TextYAlignment.Top
    return text(parent, props)
end

-- the local player's own line on a board with one (Qi, PlayTime, Thieves)
local function youText(boardId, you)
    if boardId == "Qi" then
        return if you.qi then "You: " .. NumberFormat.compact(you.qi) .. " Qi, " .. (you.rank or "") else ""
    elseif boardId == "PlayTime" then
        return if you.minutes then "You: " .. RecordsConfig.playTime(you.minutes) else ""
    elseif boardId == "Thieves" then
        return if you.eggs then "You: " .. RecordsConfig.commas(you.eggs) .. " stolen" else ""
    end
    return nil
end
HallBoards.youText = youText

-- ---------- Highest Cultivation: the stele ----------
local function drawQi(root, data, ctx)
    local H = ctx.px.Y
    frame(root, { BackgroundColor3 = C.Stone, BackgroundTransparency = 0.25, Size = UDim2.fromScale(1, 1) })
    heading(root, "HIGHEST CULTIVATION", "The most Qi, in every server", C.Gold, F.Head, 0.012, 0.066)
    local rows = data.rows or {}
    -- the top three: second, first (raised), third: a portrait on its ring, and one label of name, rank and Qi
    for _, spot in { { 2, 0.06, 0.16, 0.25 }, { 1, 0.355, 0.13, 0.29 }, { 3, 0.69, 0.16, 0.25 } } do
        local place, x, y, w = spot[1], spot[2], spot[3], spot[4]
        local row = rows[place]
        local ring = PLACE_INK[place]
        headshot(root, row and row.u, { Position = UDim2.fromScale(x + w * 0.07, y), Size = UDim2.fromScale(w * 0.86, 0.2) }, ring)
        local lines = { sized(paint("<b>" .. place .. ".</b> " .. (if row then "<b>" .. name(row, 14) .. "</b>" else "Nobody yet"), ring), H * 0.034) }
        if row then
            table.insert(lines, sized(paint(safe(row.r or ""), C.Pale), H * 0.024))
            table.insert(lines, sized(paint("<b>" .. NumberFormat.compact(row.v) .. " Qi</b>", C.Sand), H * 0.028))
        end
        text(root, { Text = table.concat(lines, "\n"), Px = H * 0.03, Font = F.Strong, LineHeight = 1.05, Position = UDim2.fromScale(x - 0.02, y + 0.215),
            Size = UDim2.fromScale(w + 0.04, 0.13), TextXAlignment = Enum.TextXAlignment.Center, TextYAlignment = Enum.TextYAlignment.Top })
    end
    rule(root, 0.5, C.Bronze)
    -- places 4 to 10: four columns, one label each
    local places, names, ranks, values = {}, {}, {}, {}
    for place = 4, 10 do
        local row = rows[place]
        table.insert(places, tostring(place))
        table.insert(names, if row then name(row, 15) else "")
        table.insert(ranks, if row then safe(row.r or "") else "")
        table.insert(values, if row then NumberFormat.compact(row.v) else "")
    end
    local rowPx = H * 0.058
    column(root, places, 0.06, 0.52, 0.06, rowPx, ctx, { Font = F.Number, TextColor3 = C.Muted, TextXAlignment = Enum.TextXAlignment.Center })
    column(root, names, 0.13, 0.52, 0.42, rowPx, ctx, { Font = F.Strong, TextColor3 = C.Pale })
    column(root, ranks, 0.55, 0.52 + 0.058 * 0.12, 0.24, rowPx, ctx, { Font = F.Body, TextColor3 = C.Muted, Px = rowPx * 0.46 })
    column(root, values, 0.8, 0.52, 0.15, rowPx, ctx, { Font = F.Number, TextColor3 = C.Sand, TextXAlignment = Enum.TextXAlignment.Right })
    rule(root, 0.93, C.Bronze)
    text(root, { Name = "You", Text = youText("Qi", ctx.you), Font = F.Strong, TextColor3 = C.Pale,
        Position = UDim2.fromScale(0.06, 0.942), Size = UDim2.fromScale(0.88, 0.045), TextXAlignment = Enum.TextXAlignment.Center })
end

-- ---------- Longest Cultivators: the hourglass's ledger ----------
local function drawPlayTime(root, data, ctx)
    local H = ctx.px.Y
    frame(root, { BackgroundColor3 = C.Stone, BackgroundTransparency = 0.3, Size = UDim2.fromScale(1, 1) })
    heading(root, "LONGEST CULTIVATORS", "Most time played", C.Sand, F.Head, 0.02, 0.085)
    rule(root, 0.15, C.Bronze)
    local rows = data.rows or {}
    if #rows == 0 then
        text(root, { Text = "Nobody yet: keep cultivating!", TextColor3 = C.Muted, Position = UDim2.fromScale(0.1, 0.45),
            Size = UDim2.fromScale(0.8, 0.06), TextXAlignment = Enum.TextXAlignment.Center })
    end
    local rowPx = H * 0.071
    local places, names, times = {}, {}, {}
    for place = 1, math.min(10, #rows) do
        local row = rows[place]
        local ink = PLACE_INK[place] or C.Pale
        table.insert(places, paint(tostring(place), ink))
        table.insert(names, paint(if place <= 3 then "<b>" .. name(row, 13) .. "</b>" else name(row, 13), ink))
        table.insert(times, RecordsConfig.playTime(row.v))
        if place <= 3 then
            headshot(root, row.u, { Position = UDim2.fromScale(0.105, 0.165 + (place - 1) * 0.071 + 0.004), Size = UDim2.fromScale(0.09, 0.063) }, ink)
        end
    end
    column(root, places, 0.02, 0.165, 0.08, rowPx, ctx, { Font = F.Number, Px = rowPx * 0.74, TextXAlignment = Enum.TextXAlignment.Center })
    column(root, names, 0.21, 0.165, 0.47, rowPx, ctx, { Font = F.Strong, Px = rowPx * 0.74 })
    column(root, times, 0.62, 0.165, 0.36, rowPx, ctx, { Font = F.Number, TextColor3 = C.Sand, Px = rowPx * 0.74,
        TextXAlignment = Enum.TextXAlignment.Right })
    rule(root, 0.885, C.Bronze)
    text(root, { Name = "You", Text = youText("PlayTime", ctx.you), Font = F.Strong, TextColor3 = C.Pale,
        Position = UDim2.fromScale(0.06, 0.9), Size = UDim2.fromScale(0.88, 0.07), TextXAlignment = Enum.TextXAlignment.Center })
end

-- ---------- Greatest Thieves: the notice board ----------
local function paper(parent, x, y, w, h, tilt)
    return frame(parent, { BackgroundColor3 = C.Paper, BackgroundTransparency = 0, BorderSizePixel = 3, BorderColor3 = C.PaperDark,
        BorderMode = Enum.BorderMode.Inset, Position = UDim2.fromScale(x, y), Size = UDim2.fromScale(w, h), Rotation = tilt })
end

local function poster(parent, row, place, x, y, w, h, tilt, ctx)
    local p = paper(parent, x, y, w, h, tilt)
    local P = ctx.px.Y * h
    local pin = frame(p, { BackgroundColor3 = C.Pin, BackgroundTransparency = 0, Position = UDim2.fromScale(0.5, 0.015),
        AnchorPoint = Vector2.new(0.5, 0), Size = UDim2.fromScale(0.09, 0.055) })
    local c = Instance.new("UICorner")
    c.CornerRadius = UDim.new(0.5, 0)
    c.Parent = pin
    text(p, { Text = '<font face="Bangers" color="' .. hex(C.Red) .. '" size="' .. math.floor(P * 0.15) .. '">WANTED</font>\n<b>EGG THIEF  No. '
        .. place .. "</b>", Px = P * 0.055, Font = F.Heavy, TextColor3 = C.Ink, LineHeight = 1.0, Position = UDim2.fromScale(0.04, 0.06),
        Size = UDim2.fromScale(0.92, 0.22), TextXAlignment = Enum.TextXAlignment.Center, TextYAlignment = Enum.TextYAlignment.Top })
    local pic = headshot(p, row and row.u, { Position = UDim2.fromScale(0.5, 0.3), AnchorPoint = Vector2.new(0.5, 0),
        Size = UDim2.fromScale(0.62, 0.4), BackgroundColor3 = C.PaperDark, BackgroundTransparency = 0, ImageColor3 = rgb(255, 236, 206),
        BorderSizePixel = 3, BorderColor3 = C.Ink }, nil, false)
    pic.BorderMode = Enum.BorderMode.Outline
    local words = if row then "<b>" .. name(row, 14) .. "</b>\n" .. '<font face="Bangers" color="' .. hex(C.Red) .. '" size="'
        .. math.floor(P * 0.072) .. '">' .. RecordsConfig.commas(row.v) .. (if row.v == 1 then " EGG STOLEN" else " EGGS STOLEN") .. "</font>"
        else "<b>Could be you</b>"
    text(p, { Text = words, Px = P * 0.08, Font = F.Heavy, TextColor3 = C.Ink, LineHeight = 1.0, Position = UDim2.fromScale(0.04, 0.72),
        Size = UDim2.fromScale(0.92, 0.25), TextXAlignment = Enum.TextXAlignment.Center, TextYAlignment = Enum.TextYAlignment.Top })
end

local function drawThieves(root, data, ctx)
    local rows = data.rows or {}
    local H = ctx.px.Y
    local strip = paper(root, 0.25, 0.0, 0.5, 0.12, -1)
    text(strip, { Text = "GREATEST THIEVES", Font = F.Poster, TextColor3 = C.Ink, Position = UDim2.fromScale(0.04, 0.08),
        Size = UDim2.fromScale(0.92, 0.84), TextXAlignment = Enum.TextXAlignment.Center })
    poster(root, rows[2], 2, 0.02, 0.17, 0.22, 0.78, -3, ctx)
    poster(root, rows[1], 1, 0.255, 0.14, 0.25, 0.84, 1.5, ctx)
    poster(root, rows[3], 3, 0.525, 0.18, 0.22, 0.76, 2.5, ctx)
    -- the note, 4 to 8, one label
    local note = paper(root, 0.77, 0.15, 0.215, 0.62, -1.5)
    local N = H * 0.62
    local lines = { paint('<font size="' .. math.floor(N * 0.07) .. '"><b>ALSO WANTED</b></font>', C.Red) }
    for place = 4, 8 do
        local row = rows[place]
        table.insert(lines, "<b>" .. place .. ". " .. (if row then name(row, 13) else "...") .. "</b>")
        table.insert(lines, sized(paint(if row then "    " .. RecordsConfig.commas(row.v) .. (if row.v == 1 then " egg" else " eggs") else " ", C.InkFaded), N * 0.06))
    end
    text(note, { Text = table.concat(lines, "\n"), Px = N * 0.068, Font = F.Strong, TextColor3 = C.Ink, LineHeight = 1.02,
        Position = UDim2.fromScale(0.07, 0.03), Size = UDim2.fromScale(0.9, 0.95), TextYAlignment = Enum.TextYAlignment.Top })
    local slip = paper(root, 0.77, 0.8, 0.215, 0.15, 2)
    text(slip, { Name = "You", Text = youText("Thieves", ctx.you), Font = F.Strong, TextColor3 = C.Ink, Position = UDim2.fromScale(0.06, 0.15),
        Size = UDim2.fromScale(0.88, 0.7), TextXAlignment = Enum.TextXAlignment.Center })
end

-- ---------- Rarest Beasts: the showcase ----------
local Portraits -- (required on first use: it builds the beasts' models)
local function drawRarest(root, data, ctx)
    local rows = data.rows or {}
    local B = ctx.px.Y * (0.5 - 0.044)
    for index = 1, RecordsConfig.Rarest.Show do
        local col, line = (index - 1) % 3, (index - 1) // 3
        local row = rows[index]
        local pet = row and GameConfig.Pets[row.p]
        local tone = if pet then GameConfig.PetRarityColors[pet.Rarity] else C.StoneLine
        -- (clear of the case's bronze mullions: 0.22 studs wide on a 15 x 6.3 face)
        local bay = frame(root, { Position = UDim2.fromScale(col / 3 + 0.011, line / 2 + 0.022), Size = UDim2.fromScale(1 / 3 - 0.022, 0.5 - 0.044),
            BackgroundColor3 = if pet then tone:Lerp(C.Stone, 0.8) else C.Stone, BackgroundTransparency = 0.1, BorderSizePixel = if pet then 3 else 0,
            BorderColor3 = tone, BorderMode = Enum.BorderMode.Inset })
        if not row then
            text(bay, { Text = "Waiting for a rare hatch", TextColor3 = C.Muted, Position = UDim2.fromScale(0.08, 0.42),
                Size = UDim2.fromScale(0.84, 0.15), TextXAlignment = Enum.TextXAlignment.Center })
            continue
        end
        -- the beast itself
        Portraits = Portraits or require(UI:WaitForChild("Portraits"))
        local ok, view = pcall(Portraits.pet, row.p, 128)
        if ok and view then
            for _, child in view:GetChildren() do
                if child:IsA("UICorner") or child:IsA("UIStroke") then
                    child:Destroy()
                end
            end
            view.Position = UDim2.fromScale(0.015, 0.06)
            view.Size = UDim2.fromScale(0.43, 0.9)
            view.BackgroundTransparency = 1
            local a = Instance.new("UIAspectRatioConstraint")
            a.AspectRatio = 1
            a.Parent = view
            view.Parent = bay
        end
        local size = if PetRules.Sizes[row.s] then row.s else "Normal"
        local kind = string.upper((if size ~= "Normal" then size .. " " else "") .. (if pet then pet.Rarity else ""))
        text(bay, { Text = "<b>" .. index .. ". " .. safe(if pet then pet.DisplayName else row.p, 26) .. "</b>\n"
            .. sized(paint(kind, if size == "Giant" then PetRules.Sizes.Giant.Color else C.Pale), B * 0.095) .. "\n"
            .. sized(paint("<b>" .. RecordsConfig.oneIn(row.o) .. "</b>", C.Sand), B * 0.15),
            Px = B * 0.105, Font = F.Heavy, TextColor3 = tone, LineHeight = 1.0, TextWrapped = true,
            Position = UDim2.fromScale(0.45, 0.05), Size = UDim2.fromScale(0.54, 0.56), TextYAlignment = Enum.TextYAlignment.Top })
        headshot(bay, row.u, { Position = UDim2.fromScale(0.45, 0.64), Size = UDim2.fromScale(0.13, 0.26) }, nil, false)
        text(bay, { Text = "<b>" .. name(row, 14) .. "</b>\n" .. sized(paint(RecordsConfig.date(row.t), C.Muted), B * 0.075), Px = B * 0.1,
            Font = F.Strong, TextColor3 = C.Pale, LineHeight = 1.0, Position = UDim2.fromScale(0.6, 0.64), Size = UDim2.fromScale(0.39, 0.3),
            TextYAlignment = Enum.TextYAlignment.Top })
    end
end

local function drawRarestTitle(root)
    text(root, { Text = "RAREST BEASTS EVER HATCHED", Font = F.Engraved, TextColor3 = C.Gold, Outline = 2,
        Position = UDim2.fromScale(0.02, 0.08), Size = UDim2.fromScale(0.96, 0.84), TextXAlignment = Enum.TextXAlignment.Center })
end

-- ---------- the Hall of Firsts: the record slabs ----------
local function drawFirsts(group)
    return function(root, data, ctx)
        local H = ctx.px.Y
        frame(root, { BackgroundColor3 = C.Stone, BackgroundTransparency = 0.35, Size = UDim2.fromScale(1, 1) })
        local list = {}
        for _, entry in RecordsConfig.Firsts do
            if entry.Group == group then
                table.insert(list, entry)
            end
        end
        local firsts = data.firsts or {}
        local head = if group == "Realm" then 0.075 else 0.1
        text(root, { Text = if group == "Realm" then "HALL OF FIRSTS" else RecordsConfig.FirstGroups[group], Font = F.Engraved, TextColor3 = C.Gold,
            Outline = 2, Position = UDim2.fromScale(0.04, 0.02), Size = UDim2.fromScale(0.92, head), TextXAlignment = Enum.TextXAlignment.Center })
        if group == "Realm" then
            text(root, { Text = "The first to get there. Set in stone forever.", Font = F.Strong, TextColor3 = C.Muted,
                Position = UDim2.fromScale(0.08, 0.1), Size = UDim2.fromScale(0.84, 0.035), TextXAlignment = Enum.TextXAlignment.Center })
        end
        local top = if group == "Realm" then 0.155 else 0.15
        rule(root, top - 0.01, C.Bronze)
        -- the realms (twelve) in two columns, the others in one; each entry one label (what, who, when): names engraved in gold, no
        -- portraits (a memorial, and twenty-two more draw calls once every first is taken)
        local columns = if #list > 6 then 2 else 1
        local perColumn = math.ceil(#list / columns)
        local h = (0.97 - top) / perColumn
        local colW = 1 / columns
        local E = H * h
        for k, entry in list do
            local e = firsts[entry.Id]
            local col = (k - 1) // perColumn
            local y = top + ((k - 1) % perColumn) * h
            local labelColor = if entry.Highlight then C.Sand elseif entry.Rarity then GameConfig.PetRarityColors[entry.Rarity] else C.Muted
            local long = #entry.Label > 16 and columns > 1 -- (a long realm name in a narrow column, smaller)
            local lines = { sized(paint("<b>" .. safe(string.upper(entry.Label)) .. "</b>", labelColor),
                E * (if columns > 1 then (if long then 0.21 else 0.3) else 0.28)) }
            local x = col * colW + 0.04
            if e then
                table.insert(lines, '<font face="Merriweather"><b>' .. name(e, if columns > 1 then 13 else 15) .. "</b></font>"
                    .. (if columns > 1 then "\n" else "   ") .. sized(paint(RecordsConfig.date(e.t), C.Muted), E * (if columns > 1 then 0.22 else 0.2)))
            else
                table.insert(lines, sized(paint("Nobody yet. Be the first!", C.Muted), E * (if columns > 1 then 0.25 else 0.24)))
            end
            text(root, { Text = table.concat(lines, "\n"), Px = E * 0.34, Font = F.Strong, TextColor3 = C.Gold,
                LineHeight = 0.98, Position = UDim2.fromScale(x, y + h * 0.04), Size = UDim2.fromScale(colW - 0.06, h * 0.94),
                TextYAlignment = Enum.TextYAlignment.Top })
        end
    end
end

-- ---------- the Chronicle: the open book ----------
local function feedWords(row)
    local who = "<b>" .. name(row, 18) .. "</b>"
    if row.k == "Hatch" then
        local pet = GameConfig.Pets[row.p]
        local size = if row.s == "Giant" or row.s == "Large" then string.upper(row.s) .. " " else ""
        local odds = if typeof(row.o) == "number" then " (" .. RecordsConfig.oneIn(row.o) .. ")" else ""
        return who .. " hatched a " .. size .. safe(if pet then pet.DisplayName else "beast") .. odds
    elseif row.k == "Realm" then
        local realm = safe(row.r)
        return who .. " reached the " .. realm .. (if string.find(realm, "Realm") then "" else " realm")
    elseif row.k == "First" then
        local first = RecordsConfig.FirstById[row.f]
        if first then
            local what = if first.Group == "Realm" then "the first to reach " .. first.Label
                elseif first.Group == "Guardian" then "the first to steal an egg from " .. first.Label
                else "the first to hatch " .. first.Label
            return who .. " became " .. paint(safe(what), rgb(140, 80, 20)) .. "!"
        end
    end
    return who .. " did something great"
end

local LEFT_LINES = 4
local function drawFeed(side)
    return function(root, data, ctx)
        local H = ctx.px.Y
        local rows = data.rows or {}
        local from, count, top
        if side == "Left" then
            text(root, { Text = "The Chronicle", Font = F.Hand, TextColor3 = C.Ink, Position = UDim2.fromScale(0.06, 0.03),
                Size = UDim2.fromScale(0.88, 0.1), TextXAlignment = Enum.TextXAlignment.Center })
            from, count, top = 1, LEFT_LINES, 0.2
        else
            from, count, top = LEFT_LINES + 1, RecordsConfig.Feed.Show - LEFT_LINES, 0.04
        end
        local entries = {}
        for k = from, from + count - 1 do
            local row = rows[k]
            if not row then
                break
            end
            table.insert(entries, feedWords(row) .. "\n" .. sized('<i><font color="' .. hex(C.InkFaded) .. '">'
                .. RecordsConfig.ago(ctx.now - (row.t or ctx.now)) .. "</font></i>", H * 0.036))
        end
        if side == "Left" and #rows == 0 then
            table.insert(entries, "<i>Great moments, in every server, are written here. Hatch something rare!</i>")
        elseif side == "Left" then
            text(root, { Text = "Great moments, in every server", Font = F.Hand, TextColor3 = C.InkFaded, Position = UDim2.fromScale(0.08, 0.13),
                Size = UDim2.fromScale(0.84, 0.05), TextXAlignment = Enum.TextXAlignment.Center })
        end
        -- the whole page in one label: entries a blank line apart
        text(root, { Name = "Page", Text = table.concat(entries, "\n" .. sized(" ", H * 0.02) .. "\n"), Font = F.Ink, Px = H * 0.045,
            TextColor3 = C.Ink, TextWrapped = true, LineHeight = 1.05, Position = UDim2.fromScale(0.06, top),
            Size = UDim2.fromScale(0.9, 0.97 - top), TextYAlignment = Enum.TextYAlignment.Top })
    end
end

local function drawHallTitle(root)
    text(root, { Text = "HALL OF RECORDS", Font = F.Engraved, TextColor3 = C.Gold, Outline = 2.5, Position = UDim2.fromScale(0.02, 0.06),
        Size = UDim2.fromScale(0.96, 0.88), TextXAlignment = Enum.TextXAlignment.Center })
end

-- board id -> { Data: the published board it shows (ReplicatedStorage.HallOfRecords.<Data>), Draw, PixelsPerStud, Ticks: redrawn
-- every half minute (the Chronicle's "minutes ago") }
HallBoards.Boards = {
    Qi = { Data = "Qi", Draw = drawQi, PixelsPerStud = 50 },
    PlayTime = { Data = "PlayTime", Draw = drawPlayTime, PixelsPerStud = 60 },
    Thieves = { Data = "Thieves", Draw = drawThieves, PixelsPerStud = 50 },
    Rarest = { Data = "Rarest", Draw = drawRarest, PixelsPerStud = 55 },
    RarestTitle = { Data = nil, Draw = drawRarestTitle, PixelsPerStud = 50 },
    FirstsRealm = { Data = "Firsts", Draw = drawFirsts("Realm"), PixelsPerStud = 55 },
    FirstsGuardian = { Data = "Firsts", Draw = drawFirsts("Guardian"), PixelsPerStud = 55 },
    FirstsBeast = { Data = "Firsts", Draw = drawFirsts("Beast"), PixelsPerStud = 55 },
    FeedLeft = { Data = "Feed", Draw = drawFeed("Left"), PixelsPerStud = 70, Ticks = true },
    FeedRight = { Data = "Feed", Draw = drawFeed("Right"), PixelsPerStud = 70, Ticks = true },
    HallTitle = { Data = nil, Draw = drawHallTitle, PixelsPerStud = 50 },
}

-- what the local player's own lines read
function HallBoards.you()
    local player = Players.LocalPlayer
    local stats = player:FindFirstChild("leaderstats")
    local qi = stats and stats:FindFirstChild("Qi")
    local rank = stats and stats:FindFirstChild("Rank")
    return { qi = qi and qi.Value, rank = rank and rank.Value, minutes = player:GetAttribute("RecordPlayMinutes"),
        eggs = player:GetAttribute("RecordEggsSecured") }
end

return HallBoards
