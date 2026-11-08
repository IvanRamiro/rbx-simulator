-- Each imported pet's colour map (ReplicatedStorage.PetMeshes: every part of a pet shares one).
-- Read from the place's SurfaceAppearances (2026-11-03), because a game script can't read them:
-- the client's pet portraits (UI/Portraits) need it, since a SurfaceAppearance renders black in a
-- ViewportFrame. A pet missing here has no SurfaceAppearance (palette-textured or procedural).
-- Re-read after re-importing a pet's maps.
return {
    AbyssAnomalocaris = "rbxassetid://72650000114111",
    AzureSkyDragon = "rbxassetid://102035306549567",
    CelestialPearlDragon = "rbxassetid://88231363393309",
    CelestialSnowLeopard = "rbxassetid://73710725624687",
    CloudSheep = "rbxassetid://137454504415941",
    CosmicJellyfish = "rbxassetid://113526835581631",
    CrystalSnail = "rbxassetid://119626589372847",
    DawnPhoenix = "rbxassetid://125937144749128",
    DreadfangCerberus = "rbxassetid://90383585387525",
    DreamMoth = "rbxassetid://116224404517599",
    EclipseCat = "rbxassetid://85885755382252",
    GalaxyManta = "rbxassetid://93932467864746",
    GoldenKirin = "rbxassetid://74047466096461",
    GoldenManeLion = "rbxassetid://89135149772900",
    JadeAntlerDeer = "rbxassetid://70823879643174",
    JadeSpiritPanda = "rbxassetid://81210826866538",
    JadeWyrmTurtle = "rbxassetid://131491500035808",
    LanternWarden = "rbxassetid://122411668861659",
    MagmaCub = "rbxassetid://106636941111453",
    MossGolem = "rbxassetid://135523265460762",
    MyceliumSprite = "rbxassetid://94221576326290",
    NebulaOwl = "rbxassetid://85013631717001",
    PrismArmadillo = "rbxassetid://125786671185533",
    RuneSphinx = "rbxassetid://125628324690653",
    Shadowcoil = "rbxassetid://88845337375470",
    SpiritCrane = "rbxassetid://117737637798913",
    StarfallFox = "rbxassetid://100336403205239",
    StormhornKirin = "rbxassetid://96870617770871",
    SunscaleDragon = "rbxassetid://72856050814489",
    TheNamelessOne = "rbxassetid://89179027531207",
    VoidscaleHydra = "rbxassetid://134504797181991",
    WindSprite = "rbxassetid://100955540073927",
}
