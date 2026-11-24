-- NineTailMoonfox: its animation and its profile (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
local PetsFolder = script.Parent.Parent.Parent -- the Pets folder (this file is PetRig/<folder>/<Name>)
return function(K)
    local PetRig = K.PetRig



    -- The Nine-Tail Moonfox (skinned, Mythical, the Exclusive Egg; built in Blender from the owner's concept sheet 2026-11-13, nine fluffy crescent tails
    -- approved by the owner): her animation is in MoonfoxMotion (solved paws that stay planted at any speed and size, a gait that follows her speed, springs
    -- for her ears and nine tails, a head that stays level and leads her turns). The special (Full Moon, Blasts.FullMoon) fans the tails wide and lifts her
    -- head, and a light leaves every tail tip.
    do
        local MoonfoxMotion = require(PetsFolder:WaitForChild("MoonfoxMotion"))
        PetRig.Profiles.NineTailMoonfox = {
            Skinned = true,
            Bones = MoonfoxMotion.BONES,
            Points = MoonfoxMotion.POINTS,
            Effects = {
                Blast = "FullMoon", -- (its lights leave from the nine tip bones, Tail<k>_Tip)
                NovaLight = 2.5,
            },
            Colors = {
                Gold = Color3.fromRGB(150, 215, 255),
                Amber = Color3.fromRGB(40, 60, 140),
                Orange = Color3.fromRGB(90, 140, 255),
                Sun = Color3.fromRGB(235, 248, 255),
                Ivory = Color3.fromRGB(245, 250, 255),
            },
            Animate = MoonfoxMotion.animate,
        }
    end
end
