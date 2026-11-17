-- The beast pens' shape and levels, shared by their builder (ServerStorage.WorldBuild.PastureBuilder), the server (PenService,
-- PetInventory) and every client (PenController, PenPicker), so a pen's beasts roam exactly inside the fence everyone sees.
-- The owner, 2026-11-15: "Just 1 pen per player, but the size for pen is upgradable like the steal an egg". Each player in the server
-- holds one of the hub's six Beast Pastures (Placements/Pastures.lua) and has ONE pen there, of their own Level: each level holds one
-- more beast and stands visibly bigger, up to the largest that fits the pasture. A level is bought with Spirit Stones (Shop.penPrice).
--
-- A pasture's frame: its centre on the ground, its -Z toward the World Tree. The pen's front fence (with its gate, at the middle) stays
-- on the same line at every level, just inside the pasture's front; the pen grows back (+Z) and out to both sides. The owner's board
-- stands before the gate. A ring of paving marks the pasture's whole ground at the largest level, so it reads as one place.
--
--   PenLayout.level(n)              level n's entry (clamped to 1..Max): { Slots, Width, Depth, Realm }
--   PenLayout.capacity(n)           how many beasts level n holds
--   PenLayout.penFrame(n)           the pen's centre on the ground at level n, in the pasture's frame
--   PenLayout.roamHalf(n, radius)   how far from the pen's centre a beast of that footprint radius (half its diagonal) may walk:
--                                   Vector2 (X, Z)
--   PenLayout.displayScale(n, across) the extra scale a beast `across` studs over its footprint's diagonal (as built at its size) is
--                                   shown at in a level-n pen: 1, or less so it can still turn in it
--   PenLayout.parkScale(n, foot)    the extra scale a big beast standing still (parked) is shown at: its footprint `foot` (Vector2:
--                                   across, nose to tail, as built) facing the gate within the pen's width and ParkDepth of its depth
--   PenLayout.parkZ(n, length)      where a parked beast `length` studs long stands (Z in the pen's frame): against the back fence
local PenLayout = {}

-- Slots: beasts it holds. Width (X) and Depth (Z): studs inside the fence. Realm: whose weapon price buys this level (Shop.penPrice;
-- level 1 is free). Each level is 3 studs wider and 5 deeper, so an upgrade is seen at once.
PenLayout.Levels = {
    { Slots = 2, Width = 18, Depth = 22 },
    { Slots = 3, Width = 21, Depth = 27, Realm = 1 },
    { Slots = 4, Width = 24, Depth = 32, Realm = 2 },
    { Slots = 5, Width = 27, Depth = 37, Realm = 3 },
    { Slots = 6, Width = 30, Depth = 42, Realm = 4 },
    { Slots = 7, Width = 33, Depth = 47, Realm = 5 },
    { Slots = 8, Width = 36, Depth = 52, Realm = 7 },
    { Slots = 9, Width = 39, Depth = 57, Realm = 9 },
    { Slots = 10, Width = 42, Depth = 62, Realm = 11 },
}
PenLayout.Max = #PenLayout.Levels
PenLayout.MostSlots = PenLayout.Levels[PenLayout.Max].Slots

PenLayout.Fence = 1         -- a fence's thickness
PenLayout.Gate = 6          -- the gate's opening, in the front fence's middle
PenLayout.FenceHeight = 3.2
PenLayout.Margin = 1.2      -- studs a beast keeps from the fence
PenLayout.MaxDisplay = 28   -- the widest a beast is ever shown in a pen, across its footprint's diagonal (so it can turn on the spot
                            -- without touching the fence); the pen's own room caps it first below level 7. Since 2026-11-17 a Giant
                            -- is 2.4 to 5 times its Normal size (PetRules.Sizes), 30 to 50 across: it fills its pen at every level,
                            -- shown as large as the pen lets it turn
PenLayout.ParkAt = { Large = 1.4, Giant = 2, Colossal = 3 } -- a Large, Giant or Colossal shown smaller than this many times its
                            -- Normal size so it can turn stands still instead, as large as fits facing the gate (parkScale): in a small
                            -- pen a Giant still fills it, and a Colossal (30 to 54 studs long) is parked in nearly every pen
PenLayout.ParkDepth = 0.8   -- the share of the pen's depth a parked beast may take (the front stays free for the others)
PenLayout.Hip = 3.9         -- how high a Normal beast's root rides over the ground (as beside its owner: PetCompanionController)
PenLayout.Front = -32       -- where the front fence's line is, in the pasture's frame (Z)
PenLayout.Ring = { Width = 50, Depth = 70, Band = 4 } -- the paving ring's centre line round the pasture, and how wide it is
PenLayout.Board = -38       -- where the owner's board stands, before the gate (Z)

function PenLayout.level(n)
    n = if typeof(n) == "number" then math.clamp(math.floor(n), 1, PenLayout.Max) else 1
    return PenLayout.Levels[n]
end

function PenLayout.capacity(n)
    return PenLayout.level(n).Slots
end

function PenLayout.penFrame(n)
    local entry = PenLayout.level(n)
    return CFrame.new(0, 0, PenLayout.Front + PenLayout.Fence / 2 + entry.Depth / 2)
end

function PenLayout.roamHalf(n, radius)
    local entry = PenLayout.level(n)
    return Vector2.new(math.max(0.5, entry.Width / 2 - PenLayout.Margin - radius), math.max(0.5, entry.Depth / 2 - PenLayout.Margin - radius))
end

function PenLayout.displayScale(n, across)
    local entry = PenLayout.level(n)
    local cap = math.min(PenLayout.MaxDisplay, math.min(entry.Width, entry.Depth) - 2 * PenLayout.Margin - 2)
    return if across > cap then cap / across else 1
end

function PenLayout.parkScale(n, foot)
    local entry = PenLayout.level(n)
    local width, depth = entry.Width - 2 * PenLayout.Margin, (entry.Depth - 2 * PenLayout.Margin) * PenLayout.ParkDepth
    return math.min(1, width / math.max(foot.X, 0.1), depth / math.max(foot.Y, 0.1))
end

function PenLayout.parkZ(n, length)
    local entry = PenLayout.level(n)
    return math.max(0, entry.Depth / 2 - PenLayout.Margin - length / 2)
end

for n, entry in PenLayout.Levels do
    assert(entry.Slots == n + 1, "PenLayout.Levels[" .. n .. "]: each level holds one more beast")
    assert(n == 1 or (entry.Realm and entry.Width > PenLayout.Levels[n - 1].Width and entry.Depth > PenLayout.Levels[n - 1].Depth),
        "PenLayout.Levels[" .. n .. "]: each level is bigger and has a Realm (its price)")
    assert(PenLayout.Front + entry.Depth + 2 * PenLayout.Fence <= PenLayout.Ring.Depth / 2 - PenLayout.Ring.Band / 2
        and entry.Width / 2 + PenLayout.Fence <= PenLayout.Ring.Width / 2 - PenLayout.Ring.Band / 2,
        "PenLayout.Levels[" .. n .. "] doesn't fit inside the pasture's ring")
end

return PenLayout
