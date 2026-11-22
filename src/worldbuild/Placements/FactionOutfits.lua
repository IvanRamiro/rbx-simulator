-- The three factions' robes: the Murim Robes with only their colour maps swapped (tools/outfits/faction_recolor.py made the maps from
-- assets/outfits/MurimOutfit_<Piece>_color.png; the owner approved the three sheets on 2026-11-22 and they were uploaded then).
-- Every other map (normal, roughness, metalness), the meshes, the bones and the fitting stay the Murim Robes'. Read by
-- OutfitBuilder.storeVariant, which stores each as ServerStorage.Outfits.<OutfitId> (GameConfig.Outfits).
return {
    Base = "Murim",
    Variants = {
        OrthodoxRobes = {
            Belt = "rbxassetid://125476417291351", LeftBoot = "rbxassetid://123112505154498", LeftCuff = "rbxassetid://113823441275078",
            LeftShoe = "rbxassetid://127976578691632", LeftSleeve = "rbxassetid://120455138307360", LeftTrouser = "rbxassetid://105699730358671",
            RightBoot = "rbxassetid://131699022297552", RightCuff = "rbxassetid://130030141572856", RightShoe = "rbxassetid://102078974875788",
            RightSleeve = "rbxassetid://101941522468466", RightTrouser = "rbxassetid://118189873131890", Skirt = "rbxassetid://91121635680208",
            Torso = "rbxassetid://76134630050467",
        },
        UnorthodoxRobes = {
            Belt = "rbxassetid://104172781211817", LeftBoot = "rbxassetid://125241523276070", LeftCuff = "rbxassetid://76056502365392",
            LeftShoe = "rbxassetid://135501790000239", LeftSleeve = "rbxassetid://122751546811488", LeftTrouser = "rbxassetid://81444186092834",
            RightBoot = "rbxassetid://135261084741282", RightCuff = "rbxassetid://102471822264634", RightShoe = "rbxassetid://108133307721742",
            RightSleeve = "rbxassetid://102137415634026", RightTrouser = "rbxassetid://86241015742773", Skirt = "rbxassetid://128720729536576",
            Torso = "rbxassetid://118281085419174",
        },
        DemonicRobes = {
            Belt = "rbxassetid://104473660637403", LeftBoot = "rbxassetid://135451226729472", LeftCuff = "rbxassetid://122427401061211",
            LeftShoe = "rbxassetid://96956209484761", LeftSleeve = "rbxassetid://99893982133923", LeftTrouser = "rbxassetid://99894086219696",
            RightBoot = "rbxassetid://135564169628604", RightCuff = "rbxassetid://106273995789494", RightShoe = "rbxassetid://109561762444433",
            RightSleeve = "rbxassetid://95691675657168", RightTrouser = "rbxassetid://138716621497936", Skirt = "rbxassetid://117161957102798",
            Torso = "rbxassetid://89219114173645",
        },
    },
}
