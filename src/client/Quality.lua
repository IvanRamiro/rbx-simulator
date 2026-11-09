-- The phone tier. Quality.Low is true on a touch screen with no keyboard (a phone or tablet): the
-- effects with a cost a phone feels read it and thin themselves. On a PC it is false and they run as
-- they always have. Roblox's own graphics quality comes on top of this; this one is about our scripts.
--
-- What Low does:
--   RealmAura     half the emission, nearer culling, the body aura on 6 parts instead of 15; other
--                 players' auras lose their Highlight and PointLight (your own keeps them)
--   OwnerAura     half the emission
--   WorldQuality  the islands' own emitters at 40%
--   EggGlow       eggs' Highlights switch off sooner
--   GuardianAnim  coarser springs; GuardianController: animated within 150 studs, half rate at rest
--   Pets          other players' pets hidden past 80 studs
--   Poses, robes  other players' poses stop past 80 studs, robes' sway past 40
--   Pet lights   other players' pets give up their PointLights (PetRig)
--   Nameplates   drawn within 55 studs instead of 90 (TitleController)
--   Tribulation  other players' storms drawn within 160 studs instead of 320, thinner cloud, no sparks
local UserInputService = game:GetService("UserInputService")

return {
    Low = UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled,
}
