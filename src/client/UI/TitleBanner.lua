-- The banner round the Developer title's words on its nameplate (the owner, 2026-11-24: "apply it only to developer title"): rendered art (shared/TitleArt:
-- four pieces made in Blender, tools/blender/ui) laid out round the title's words, which keep their own lettering and sheen on top.
--
--   TitleBanner.new(gui)                          the banner's root frame (ZIndex 0, under the title's depth layer and letters), nothing drawn yet
--   TitleBanner.apply(banner, style, share, low)  draws it for words that fill `share` of the nameplate's width: the plate as long as the words plus
--                                                 room for the sparkles, a cap at each end, the crown over the middle; the glow layers tinted to the
--                                                 style's Rule colour. low: a lighter one for a weak device (no white-hot overlay)
--   TitleBanner.clear(banner)
--
-- The layout is all from TitleArt's recorded numbers. Units are the art's (the plate 0.7 high, 0.85 with its rim): one unit is SY of the nameplate's
-- height and SX of its width. The middle strip is stretched sideways to run under the caps' stubs; a cap is placed by its plate END, the crown by the middle.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local TitleArt = require(ReplicatedStorage:WaitForChild("TitleArt"))

local TitleBanner = {}

local ASPECT = 8 / 1.7 -- the nameplate's width over its height (its Size in studs, TitleController)
local YC = 0.25 -- the middle of the title's half of the nameplate
local PLATE_SHARE = 0.66 -- the plate's height, its rim included, as a share of the nameplate's height: its inner panel (0.59 of that) holds the letters
local PAD = 0.8 -- units of plate either side of the words: room for the sparkle in each cap's stub
local MIN_LENGTH = 2.6 -- the shortest plate, in units
local PX = TitleArt.PxPerUnit
local SY = PLATE_SHARE / (TitleArt.Pieces.Mid.Height / PX)
local SX = SY / ASPECT
local WHITE = Color3.new(1, 1, 1)

function TitleBanner.new(gui)
    local root = Instance.new("Frame")
    root.Name = "Banner"
    root.BackgroundTransparency = 1
    root.ZIndex = 0
    root.Size = UDim2.fromScale(1, 1)
    root.Parent = gui
    return { root = root }
end

function TitleBanner.clear(banner)
    banner.root:ClearAllChildren()
    banner.style, banner.length, banner.low = nil, nil, nil
end

-- one image: its left edge and top, in units from the nameplate's middle and the title row's middle, and its size in art pixels
local function image(root, name, z, id, left, top, width, height, color, transparency)
    local label = Instance.new("ImageLabel")
    label.Name = name
    label.BackgroundTransparency = 1
    label.BorderSizePixel = 0
    label.Image = id
    label.ZIndex = z
    label.ImageColor3 = color or WHITE
    label.ImageTransparency = transparency or 0
    label.Position = UDim2.fromScale(0.5 + left * SX, YC + top * SY)
    label.Size = UDim2.fromScale(width / PX * SX, height / PX * SY)
    label.Parent = root
    return label
end

function TitleBanner.apply(banner, style, share, low)
    local length = math.max(MIN_LENGTH, share / SX + 2 * PAD)
    if banner.style == style and banner.length and math.abs(banner.length - length) < 0.05 and banner.low == low then
        return
    end
    TitleBanner.clear(banner)
    banner.style, banner.length, banner.low = style, length, low
    if not style then
        return
    end
    local root, pieces, tint = banner.root, TitleArt.Pieces, style.Rule
    local function place(piece, name, z, xe)
        local p = pieces[piece]
        local left, top = xe + p.Left / PX, p.Top / PX
        image(root, name .. "Steel", z, p.Steel, left, top, p.Width, p.Height)
        if p.Light then
            image(root, name .. "Glow", z + 1, p.Light, left, top, p.Width, p.Height, tint)
            if not low then -- the glow's hot core: the same layer white, half seen, over the tinted one
                image(root, name .. "Core", z + 1, p.Light, left, top, p.Width, p.Height, WHITE, 0.5)
            end
        end
    end
    -- the plain middle strip, stretched to run under both stubs
    local mid = pieces.Mid
    local midLength = length - TitleArt.StubUnits
    local strip = Instance.new("ImageLabel")
    strip.Name = "MidSteel"
    strip.BackgroundTransparency = 1
    strip.BorderSizePixel = 0
    strip.Image = mid.Steel
    strip.ZIndex = 1
    strip.Position = UDim2.fromScale(0.5 - midLength / 2 * SX, YC + mid.Top / PX * SY)
    strip.Size = UDim2.fromScale(midLength * SX, mid.Height / PX * SY)
    strip.Parent = root
    place("CapL", "CapL", 2, -length / 2)
    place("CapR", "CapR", 2, length / 2)
    place("Crown", "Crown", 4, 0)
end

return TitleBanner
