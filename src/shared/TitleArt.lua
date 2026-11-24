-- The art of the Developer title's banner (the owner, 2026-11-24: "apply it only to developer title"): four rendered pieces, each a steel layer and, but for the
-- plain middle strip, a white glow layer the client tints (ImageColor3) to the title's Rule colour. Made by tools/blender/ui (title_banner.py renders,
-- title_pieces.py cuts and measures); uploaded once (do NOT upload again: a new upload shows grey for minutes). The numbers are pixels (200 to a unit of the
-- art; the plate is 0.7 units high) from the art's origin: the plate's middle for the middle strip and the crown, the plate's END for a cap (its left end
-- for CapL, its right for CapR), so the client places every piece from them and guesses nothing. client/UI/TitleBanner lays them out.
--
--   TitleArt.PxPerUnit, TitleArt.PlateHeight (units), TitleArt.StubUnits (how much plate each cap carries: the middle strip is stretched to run under it)
--   TitleArt.Pieces[name] = { Steel, Light (asset ids or nil), Width, Height, Left, Top }
local TitleArt = {}

TitleArt.PxPerUnit = 200
TitleArt.PlateHeight = 0.7
TitleArt.StubUnits = 0.8
TitleArt.Pieces = {
    CapL = { Steel = "rbxassetid://84733385946403", Light = "rbxassetid://93608371670499", Width = 945, Height = 568, Left = -721.0, Top = -284.0 },
    CapR = { Steel = "rbxassetid://76821714170484", Light = "rbxassetid://111124449176547", Width = 944, Height = 568, Left = -224.0, Top = -284.0 },
    Mid = { Steel = "rbxassetid://129118197422770", Light = nil, Width = 402, Height = 170, Left = -201.0, Top = -85.0 },
    Crown = { Steel = "rbxassetid://125504313808374", Light = "rbxassetid://105018427488870", Width = 767, Height = 642, Left = -378.0, Top = -382.0 },
}

return TitleArt
