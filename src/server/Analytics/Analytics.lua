-- Player funnels and the Spirit Stone economy, for the Creator Dashboard (AnalyticsService). Every
-- call is protected: analytics must never break play. What's logged:
--   the quest path (an onboarding funnel: where new players stop);
--   Spirit Stones in and out, by what caused them;
--   a few moments (RankUp, EggTaken, EggDropped, EggSecured, EggHatched, QuestsSkipped).
local AnalyticsService = game:GetService("AnalyticsService")

local Analytics = {}

local warned = false

local function guard(method, ...)
    local ok, err = pcall(method, AnalyticsService, ...)
    if not ok and not warned then
        warned = true
        warn("Analytics: " .. tostring(err))
    end
    return ok
end

function Analytics.questStep(player, step, name)
    return guard(AnalyticsService.LogOnboardingFunnelStepEvent, player, step, name)
end

-- flow: "Source" (stones earned) or "Sink" (stones spent); kind: what caused it; sku: the item, if any
function Analytics.stones(player, flow, amount, balance, kind, sku)
    if amount <= 0 then
        return false
    end
    return guard(AnalyticsService.LogEconomyEvent, player, Enum.AnalyticsEconomyFlowType[flow], "SpiritStones",
        amount, balance, kind or "Other", sku)
end

-- a moment, with up to two details to break it down by on the dashboard
function Analytics.event(player, name, value, detail1, detail2)
    local fields = {}
    if detail1 then
        fields[Enum.AnalyticsCustomFieldKeys.CustomField01.Name] = detail1
    end
    if detail2 then
        fields[Enum.AnalyticsCustomFieldKeys.CustomField02.Name] = detail2
    end
    return guard(AnalyticsService.LogCustomEvent, player, name, value or 1, fields)
end

return Analytics
