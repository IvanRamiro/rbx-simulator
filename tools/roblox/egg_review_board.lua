-- The egg review board (run in Studio's command bar, in Edit). Safe to run again.
--
-- Lays the second-generation eggs (assets/eggs_v2) on a flat surface in rows by island, no auras.
-- Nothing here touches the game: ServerStorage.EggMeshes and the stands are left alone. New imports
-- found in Workspace are moved to ServerStorage.EggMeshesV2, so they survive a clean-up. A second
-- board behind the first shows the eggs that are in the game now, to compare.
--
-- When the review is over, move Workspace.EggReviewBoard to ServerStorage.DevStage so it never ships.

local ServerStorage = game:GetService("ServerStorage")

local ROWS = {
	{ "Yggdrasil", "BeginnerQiEgg", "SpiritBreezeEgg", "ElementalCoreEgg" },
	{ "Jade Grove", "JadeSpiritEgg", "BloomwoodEgg", "AncientGroveEgg" },
	{ "Ember Peak", "InfernoEgg", "MagmaHeartEgg", "PhoenixAshEgg" },
	{ "Moonlit Isle", "CelestialEgg", "AstralSanctumEgg", "HeavenlyThroneEgg" },
	{ "Origin Abyss", "ForbiddenOriginEgg", "VoidRiftEgg", "PrimordialAbyssEgg" },
}
-- the importer reads the colour and normal maps only (ids from assets/eggs_v2/textures.json)
local MAPS = {
	AncientGroveEgg = { roughness = "rbxassetid://101248903530737" },
	AstralSanctumEgg = { metalness = "rbxassetid://99527034272474", roughness = "rbxassetid://93444807171414" },
	BeginnerQiEgg = { roughness = "rbxassetid://81422875948724" },
	BloomwoodEgg = { metalness = "rbxassetid://134761823431035", roughness = "rbxassetid://108732093534715" },
	CelestialEgg = { metalness = "rbxassetid://125465078506764", roughness = "rbxassetid://97856533912471" },
	ElementalCoreEgg = { metalness = "rbxassetid://108005921327136", roughness = "rbxassetid://80014023375789" },
	ForbiddenOriginEgg = { metalness = "rbxassetid://85702488942372", roughness = "rbxassetid://131963581615558" },
	HeavenlyThroneEgg = { metalness = "rbxassetid://131369971607987", roughness = "rbxassetid://79616802336337" },
	InfernoEgg = { roughness = "rbxassetid://103584733048288" },
	JadeSpiritEgg = { roughness = "rbxassetid://114711020831126" },
	MagmaHeartEgg = { roughness = "rbxassetid://100690162274173" },
	PhoenixAshEgg = { metalness = "rbxassetid://74383836886984", roughness = "rbxassetid://124469575162582" },
	PrimordialAbyssEgg = { metalness = "rbxassetid://71211336983953", roughness = "rbxassetid://72065620988271" },
	SpiritBreezeEgg = { metalness = "rbxassetid://123149759733826", roughness = "rbxassetid://127118763764394" },
	VoidRiftEgg = { roughness = "rbxassetid://101879434802559" },
}
local ORIGIN = Vector3.new(0, 900, 2400)
local SPACING, SCALE = 22, 3

-- collect any imports waiting in Workspace
local store = ServerStorage:FindFirstChild("EggMeshesV2")
if not store then
	store = Instance.new("Folder")
	store.Name = "EggMeshesV2"
	store.Parent = ServerStorage
end
local imported = 0
for _, row in ROWS do
	for i = 2, 4 do
		local id = row[i]
		local body
		for _, d in workspace:GetDescendants() do
			if d:IsA("MeshPart") and d.Name == id .. "_Body" and not d:FindFirstAncestor("EggReviewBoard") then
				body = d
				break
			end
		end
		if body then
			local top = body
			while top.Parent ~= workspace do
				top = top.Parent
			end
			local old = store:FindFirstChild(id)
			if old then
				old:Destroy()
			end
			local m = Instance.new("Model")
			m.Name = id
			for _, d in top:GetDescendants() do
				if d:IsA("MeshPart") and d.Name:sub(1, #id) == id then
					d.Parent = m
				end
			end
			top:Destroy()
			m.Parent = store
			imported += 1
		end
	end
end

local old = workspace:FindFirstChild("EggReviewBoard")
if old then
	old:Destroy()
end
local board = Instance.new("Model")
board.Name = "EggReviewBoard"

local function surface(name, centre, color)
	local p = Instance.new("Part")
	p.Name = name
	p.Anchored = true
	p.Material = Enum.Material.SmoothPlastic
	p.Color = color
	p.Size = Vector3.new(SPACING * 3 + 8, 1, SPACING * 5 + 8)
	p.CFrame = CFrame.new(centre)
	p.Parent = board
	return p
end

local function label(text, at)
	local tag = Instance.new("Part")
	tag.Name = text .. "_Label"
	tag.Anchored = true
	tag.CanCollide = false
	tag.Transparency = 1
	-- a Top-face SurfaceGui reads along the part's Z, so the tag is turned to read from the board's front
	tag.Size = Vector3.new(3, 0.1, SPACING - 2)
	tag.CFrame = CFrame.new(at) * CFrame.Angles(0, math.rad(-90), 0)
	local g = Instance.new("SurfaceGui")
	g.Face = Enum.NormalId.Top
	g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	g.PixelsPerStud = 40
	g.LightInfluence = 0
	g.Parent = tag
	local t = Instance.new("TextLabel")
	t.BackgroundTransparency = 1
	t.Size = UDim2.fromScale(1, 1)
	t.Font = Enum.Font.GothamBold
	t.TextScaled = true
	t.TextColor3 = Color3.fromRGB(25, 27, 32)
	t.Text = text
	t.Parent = g
	tag.Parent = board
end

local function lay(folder, centre, withMaps)
	local topY = centre.Y + 0.5
	local count = 0
	for r, row in ROWS do
		for c = 1, 3 do
			local id = row[c + 1]
			local x, z = centre.X + (c - 2) * SPACING, centre.Z + (r - 3) * SPACING
			label(id:gsub("Egg$", ""), Vector3.new(x, topY + 0.06, z + SPACING / 2 - 2))
			local src = folder and folder:FindFirstChild(id)
			if src then
				local m = src:Clone()
				for _, p in m:GetDescendants() do
					if p:IsA("MeshPart") then
						p.Anchored = true
						p.CanCollide = false
						local hex = p.Name:match("_Glow_(%x+)$")
						if hex then
							p.Material = Enum.Material.Neon
							p.Color = Color3.fromHex(hex)
							p.TextureID = ""
						elseif withMaps then
							local sa = p:FindFirstChildOfClass("SurfaceAppearance")
							if sa and MAPS[id] then
								if MAPS[id].roughness then sa.RoughnessMap = MAPS[id].roughness end
								if MAPS[id].metalness then sa.MetalnessMap = MAPS[id].metalness end
							end
						end
					end
				end
				m:ScaleTo(SCALE)
				local cf, size = m:GetBoundingBox()
				-- facing the board's front edge (+Z), standing on the surface
				m:PivotTo(m:GetPivot() + (Vector3.new(x, topY + size.Y / 2, z) - cf.Position))
				m.Parent = board
				count += 1
			end
		end
	end
	return count
end

surface("Surface", ORIGIN, Color3.fromRGB(196, 192, 184))
surface("InGameNowSurface", ORIGIN - Vector3.new(0, 0, SPACING * 5 + 24), Color3.fromRGB(120, 118, 114))
local new = lay(store, ORIGIN, true)
local current = lay(ServerStorage:FindFirstChild("EggMeshes"), ORIGIN - Vector3.new(0, 0, SPACING * 5 + 24), false)
board.Parent = workspace
return string.format("imported %d, new on board %d of 15, in-game eggs on the second board %d", imported, new, current)
