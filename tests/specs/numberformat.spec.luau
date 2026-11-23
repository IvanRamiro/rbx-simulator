-- NumberFormat.compact: the short numbers in every window ("20.5B", "74.2M", "100K").
local t = require("@env/t")
local NumberFormat = require("@shared/NumberFormat")

local cases = {
    { 0, "0" }, { 7, "7" }, { 999, "999" }, { 1000, "1K" }, { 1500, "1.5K" }, { 1999, "1.99K" }, { 12345, "12.3K" },
    { 100000, "100K" }, -- trailing zeros of a whole number are NOT trimmed
    { 999999, "999K" }, -- floors, never rounds up into the next suffix
    { 1530000, "1.53M" }, { 74200000, "74.2M" }, { 20500000000, "20.5B" }, { 1e12, "1T" }, { 2.5e12, "2.5T" }, { 1e15, "1000T" },
    { -1500, "-1.5K" }, { -999, "-999" },
}
for _, case in cases do
    t.test("compact(" .. tostring(case[1]) .. ")", function()
        t.eq(NumberFormat.compact(case[1]), case[2])
    end)
end

t.finish("numberformat")
