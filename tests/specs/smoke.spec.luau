-- Every shared module loads under the stand-ins and exports a table: the cheapest regression net there is (a stray global, a bad require,
-- a syntax error or a load-time error in any rule module fails here).
local t = require("@env/t")

local MODULES = {
    "AuctionRules", "AuraConfig", "BetaGift", "CodexRules", "ComboRules", "FactionRules", "GameConfig", "Merchant", "NumberFormat", "PassRules",
    "PenLayout", "PetLore", "PetMaps", "PetRules", "Ranks", "RecordsConfig", "RewardRules", "Shop", "SpinRules", "TitleRules",
    "TrialRules", "WeaponMaps", "WeatherConfig", "WeatherRules",
}

for _, name in MODULES do
    t.test("loads " .. name, function()
        local module = require("@shared/" .. name)
        t.eq(type(module), "table", name .. " should return a table")
    end)
end

t.finish("smoke")
