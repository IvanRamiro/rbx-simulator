-- The realm weapons' maps (assets/weapons/<WeaponId>_color/_normal/_roughness/_metalness.png). Colour
-- and normal are the importer's uploads (read back and checked); roughness and metalness are ours, as
-- the importer reads neither. A blank metalness map (no metal) is one asset, shared. Read by
-- OutfitBuilder.storeWeapon and setWeaponMaps, and by the client's weapon portraits (UI/Portraits),
-- which need the colour maps because a game script can't read a SurfaceAppearance's.
return {
    Sword1 = { Color = "rbxassetid://126342512219806", Normal = "rbxassetid://114198418603711", Roughness = "rbxassetid://118152792561562", Metalness = "rbxassetid://115472245461841" },
    Sword2 = { Color = "rbxassetid://114957756239136", Normal = "rbxassetid://76004377119601", Roughness = "rbxassetid://74832818636900", Metalness = "rbxassetid://136220282728461" },
    Sword3 = { Color = "rbxassetid://114267963473644", Normal = "rbxassetid://130581894978063", Roughness = "rbxassetid://93951146607248", Metalness = "rbxassetid://130166203948537" },
    Sword4 = { Color = "rbxassetid://132721993076207", Normal = "rbxassetid://75165364979907", Roughness = "rbxassetid://86012846837692", Metalness = "rbxassetid://132451922914325" },
    Sword5 = { Color = "rbxassetid://82162527681598", Normal = "rbxassetid://100359297635111", Roughness = "rbxassetid://109355531875405", Metalness = "rbxassetid://127697224816805" },
    Sword6 = { Color = "rbxassetid://91155090143130", Normal = "rbxassetid://82425643097434", Roughness = "rbxassetid://135194061168710", Metalness = "rbxassetid://95127590587839" },
    Sword7 = { Color = "rbxassetid://72049132454459", Normal = "rbxassetid://75376604291509", Roughness = "rbxassetid://71029959427424", Metalness = "rbxassetid://80728128057125" },
    Sword8 = { Color = "rbxassetid://131679732536805", Normal = "rbxassetid://92396697689288", Roughness = "rbxassetid://125448747871986", Metalness = "rbxassetid://101740083900137" },
    Sword9 = { Color = "rbxassetid://85191829303168", Normal = "rbxassetid://124758056622838", Roughness = "rbxassetid://123492876594088", Metalness = "rbxassetid://127031228999225" },
    Sword10 = { Color = "rbxassetid://131454562204066", Normal = "rbxassetid://135735913205090", Roughness = "rbxassetid://114101995308786", Metalness = "rbxassetid://117047388045856" },
    Sword11 = { Color = "rbxassetid://92279650990496", Normal = "rbxassetid://130064514669232", Roughness = "rbxassetid://119694203067247", Metalness = "rbxassetid://127031228999225" },
    Sword12 = { Color = "rbxassetid://104063362390390", Normal = "rbxassetid://92285164370940", Roughness = "rbxassetid://107364791586665", Metalness = "rbxassetid://128435641850577" },
    Spear1 = { Color = "rbxassetid://137429368624828", Normal = "rbxassetid://104429486896228", Roughness = "rbxassetid://140587818220105", Metalness = "rbxassetid://127031228999225" },
    Spear2 = { Color = "rbxassetid://79813997829649", Normal = "rbxassetid://78809722727409", Roughness = "rbxassetid://107993289898705", Metalness = "rbxassetid://128933247463046" },
    Spear3 = { Color = "rbxassetid://92418270454144", Normal = "rbxassetid://78851032981614", Roughness = "rbxassetid://130238363197411", Metalness = "rbxassetid://86282845868049" },
    Spear4 = { Color = "rbxassetid://83445857318487", Normal = "rbxassetid://123960786457843", Roughness = "rbxassetid://74150810568412", Metalness = "rbxassetid://86091913613615" },
    Spear5 = { Color = "rbxassetid://85470182056149", Normal = "rbxassetid://108922251296167", Roughness = "rbxassetid://109951337868726", Metalness = "rbxassetid://116338575468554" },
    Spear6 = { Color = "rbxassetid://126884770834749", Normal = "rbxassetid://97557438551914", Roughness = "rbxassetid://129242378840044", Metalness = "rbxassetid://121234673442562" },
    Spear7 = { Color = "rbxassetid://130177195770741", Normal = "rbxassetid://125613071110723", Roughness = "rbxassetid://131703578237584", Metalness = "rbxassetid://132498832338577" },
    Spear8 = { Color = "rbxassetid://79324559517731", Normal = "rbxassetid://115865490297275", Roughness = "rbxassetid://117419629114434", Metalness = "rbxassetid://118923341076664" },
    Spear9 = { Color = "rbxassetid://117093102674873", Normal = "rbxassetid://124500345076780", Roughness = "rbxassetid://122298862958862", Metalness = "rbxassetid://121806759649355" },
    Spear10 = { Color = "rbxassetid://122381001629622", Normal = "rbxassetid://137540971988873", Roughness = "rbxassetid://84212514932253", Metalness = "rbxassetid://71552643321034" },
    Spear11 = { Color = "rbxassetid://134577159657984", Normal = "rbxassetid://127941738031283", Roughness = "rbxassetid://135729892378698", Metalness = "rbxassetid://127031228999225" },
    Spear12 = { Color = "rbxassetid://139864992549625", Normal = "rbxassetid://123007275019516", Roughness = "rbxassetid://115422653501703", Metalness = "rbxassetid://104235130424519" },
}
