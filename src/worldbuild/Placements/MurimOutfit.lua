-- Generated from assets/outfits/MurimOutfit_pieces.json (tools/blender/outfits/murim_outfit.py): each piece of
-- the Murim Outfit, the body part it rides and its centre as authored, in studs relative to the
-- HumanoidRootPart of the owner's avatar at rest (front toward -Z). BodyParts are that avatar's
-- part centres at rest. OutfitBuilder.store fits the imported pieces with these.
return {
    Pieces = {
        Belt = { Part = "LowerTorso", Centre = Vector3.new(0.0000, -1.1122, -0.1599), Skinned = true },
        LeftBoot = { Part = "LeftLowerLeg", Centre = Vector3.new(-0.3952, -2.0038, -0.0054), Skinned = false },
        LeftCuff = { Part = "LeftLowerArm", Centre = Vector3.new(-1.4441, -0.3356, 0.0415), Skinned = true },
        LeftShoe = { Part = "LeftFoot", Centre = Vector3.new(-0.4050, -2.6350, -0.1167), Skinned = false },
        LeftSleeve = { Part = "LeftUpperArm", Centre = Vector3.new(-1.2150, 0.5442, 0.0000), Skinned = false },
        LeftTrouser = { Part = "LeftUpperLeg", Centre = Vector3.new(-0.4049, -1.2659, -0.0002), Skinned = false },
        RightBoot = { Part = "RightLowerLeg", Centre = Vector3.new(0.4148, -2.0038, -0.0054), Skinned = false },
        RightCuff = { Part = "RightLowerArm", Centre = Vector3.new(1.4643, -0.3355, 0.0416), Skinned = true },
        RightShoe = { Part = "RightFoot", Centre = Vector3.new(0.4050, -2.6350, -0.1167), Skinned = false },
        RightSleeve = { Part = "RightUpperArm", Centre = Vector3.new(1.2150, 0.5442, 0.0000), Skinned = false },
        RightTrouser = { Part = "RightUpperLeg", Centre = Vector3.new(0.4053, -1.2659, 0.0007), Skinned = false },
        Skirt = { Part = "LowerTorso", Centre = Vector3.new(-0.0094, -1.4933, 0.0396), Skinned = true },
        Torso = { Part = "UpperTorso", Centre = Vector3.new(-0.0046, 0.1048, 0.0035), Skinned = false },
    },
    BodyParts = {
        UpperTorso = Vector3.new(0.000, 0.204, 0.000),
        LowerTorso = Vector3.new(0.000, -0.717, 0.000),
        LeftUpperArm = Vector3.new(-1.215, 0.359, 0.000),
        RightUpperArm = Vector3.new(1.215, 0.359, 0.000),
        LeftLowerArm = Vector3.new(-1.215, -0.189, 0.000),
        RightLowerArm = Vector3.new(1.215, -0.189, 0.000),
        LeftUpperLeg = Vector3.new(-0.405, -1.296, 0.000),
        RightUpperLeg = Vector3.new(0.405, -1.296, 0.000),
        LeftLowerLeg = Vector3.new(-0.405, -2.028, 0.000),
        RightLowerLeg = Vector3.new(0.405, -2.028, 0.000),
        LeftFoot = Vector3.new(-0.405, -2.634, 0.000),
        RightFoot = Vector3.new(0.405, -2.634, 0.000),
    },
    -- uploaded by us: the importer reads only colour and normal, and its uploads failed (grey in Play).
    -- The right sleeve, boot and shoe maps are re-uploads with one corner pixel changed (the first broke).
    Maps = {
        Belt = { Color = "rbxassetid://140425118164421", Normal = "rbxassetid://99909690936172", Roughness = "rbxassetid://136206143641995", Metalness = "rbxassetid://129664010152839" },
        LeftBoot = { Color = "rbxassetid://89582902623230", Normal = "rbxassetid://84936900431720", Roughness = "rbxassetid://119517234271407", Metalness = "rbxassetid://127031228999225" },
        LeftCuff = { Color = "rbxassetid://92093127307934", Normal = "rbxassetid://91066879258860", Roughness = "rbxassetid://125988268546977", Metalness = "rbxassetid://127031228999225" },
        LeftShoe = { Color = "rbxassetid://79466100011349", Normal = "rbxassetid://74140785491257", Roughness = "rbxassetid://77661598497036", Metalness = "rbxassetid://127031228999225" },
        LeftSleeve = { Color = "rbxassetid://113920703530657", Normal = "rbxassetid://104972552476088", Roughness = "rbxassetid://136065247067935", Metalness = "rbxassetid://105111891528264" },
        LeftTrouser = { Color = "rbxassetid://84313495200165", Normal = "rbxassetid://118384129578708", Roughness = "rbxassetid://111836627937165", Metalness = "rbxassetid://127031228999225" },
        RightBoot = { Color = "rbxassetid://84039528659289", Normal = "rbxassetid://92286024276042", Roughness = "rbxassetid://97312492832969", Metalness = "rbxassetid://127031228999225" },
        RightCuff = { Color = "rbxassetid://71160637130387", Normal = "rbxassetid://104882427456302", Roughness = "rbxassetid://117159926938972", Metalness = "rbxassetid://127031228999225" },
        RightShoe = { Color = "rbxassetid://121189834315844", Normal = "rbxassetid://111152670089518", Roughness = "rbxassetid://78407956292800", Metalness = "rbxassetid://127031228999225" },
        RightSleeve = { Color = "rbxassetid://80776508621104", Normal = "rbxassetid://108074918557126", Roughness = "rbxassetid://125727545668808", Metalness = "rbxassetid://86685670965297" },
        RightTrouser = { Color = "rbxassetid://137419766108089", Normal = "rbxassetid://81529826906560", Roughness = "rbxassetid://81469319568438", Metalness = "rbxassetid://127031228999225" },
        Skirt = { Color = "rbxassetid://119075011331617", Normal = "rbxassetid://116098527125069", Roughness = "rbxassetid://116572754926944", Metalness = "rbxassetid://124405903083581" },
        Torso = { Color = "rbxassetid://119100684500807", Normal = "rbxassetid://89830157762507", Roughness = "rbxassetid://82210357852794", Metalness = "rbxassetid://103811658070280" },
    },
}
