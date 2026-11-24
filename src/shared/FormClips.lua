-- Which keyed clip (client/Character/WeaponClips, made by tools/blender/animation) each chain step of a combat form plays (FormRules has the chains).
--
--   FormClips.Own[form]       the form's own clips, one per chain step, in order: CombatFx plays these
--   FormClips.Borrowed[form]  the original clips the balanced forms still play, by step (CombatFx.clipStep picks them: a sword's finisher is SwordC and its
--                             other strikes SwordA and SwordB in turn; a spear's finisher is the slash and the rest the thrust). Listed so a test can check them too
--
-- tests/specs/formclips.spec.luau keeps this table honest: a clip for every chain step, every clip exists, and each fits its strike's cooldown within the
-- retiming CombatFx allows (a clip is played 0.75x to 1.8x of its own speed to fit the cooldown: past that the blow would not land when the clip shows it).
local FormClips = {
    Own = {
        Gale = { "GaleSwift", "GaleCross", "GaleSpin", "GaleRush", "GaleStorm" },
        Mountain = { "MountainCut", "MountainChop", "MountainFall" },
        Swallow = { "SwallowQuick", "SwallowDouble", "SwallowLow", "SwallowRising", "SwallowWhirl" },
        Tiger = { "TigerFang", "TigerClaw", "TigerSlam" },
        Fist = { "PunchRight", "FistHook", "FistPalm" },
        Flurry = { "FlurryJab", "FlurryCross", "FlurryHook", "FlurryUpper", "FlurryBarrage" },
        Stone = { "StoneHammerR", "StoneHammerL", "StoneCrush" },
    },
    Borrowed = {
        Crescent = { "SwordA", "SwordB", "SwordC" },
        Lancer = { "SpearThrust", "SpearThrust", "SpearSlash" },
    },
}

return FormClips
