-- Short, readable numbers for the HUD: 950, 12.5K, 3.4M, 4.18B.
-- Qi reaches billions in the later realms, too long to show in full.

local NumberFormat = {}

local SUFFIXES = {
    { Value = 1e12, Suffix = "T" },
    { Value = 1e9, Suffix = "B" },
    { Value = 1e6, Suffix = "M" },
    { Value = 1e3, Suffix = "K" },
}

-- Three significant figures, trailing zeros dropped: 1234 -> "1.23K", 1200000 -> "1.2M"
function NumberFormat.compact(number)
    local sign = if number < 0 then "-" else ""
    number = math.abs(number)
    for _, step in SUFFIXES do
        if number >= step.Value then
            local scaled = number / step.Value
            local decimals = if scaled >= 100 then 0 elseif scaled >= 10 then 1 else 2
            local text = string.format("%." .. decimals .. "f", math.floor(scaled * 10 ^ decimals) / 10 ^ decimals)
            text = string.gsub(text, "%.?0+$", "")
            return sign .. text .. step.Suffix
        end
    end
    return sign .. tostring(math.floor(number))
end

return NumberFormat
