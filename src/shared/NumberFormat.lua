local NumberFormat = {}

local SUFFIXES = {
    { Value = 1e12, Suffix = "T" },
    { Value = 1e9, Suffix = "B" },
    { Value = 1e6, Suffix = "M" },
    { Value = 1e3, Suffix = "K" },
}

function NumberFormat.compact(number)
    local sign = if number < 0 then "-" else ""
    number = math.abs(number)
    for _, step in SUFFIXES do
        if number >= step.Value then
            local scaled = number / step.Value
            local decimals = if scaled >= 100 then 0 elseif scaled >= 10 then 1 else 2
            local text = string.format("%." .. decimals .. "f", math.floor(scaled * 10 ^ decimals) / 10 ^ decimals)
            if decimals > 0 then
                -- trim trailing decimal zeros only: 100K must keep its own zeros
                text = string.gsub(string.gsub(text, "0+$", ""), "%.$", "")
            end
            return sign .. text .. step.Suffix
        end
    end
    return sign .. tostring(math.floor(number))
end

return NumberFormat
