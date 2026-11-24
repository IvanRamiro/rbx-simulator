-- The pets' special effects (Blasts.*) and their helpers (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local Debris, Lighting, Players, RunService, TweenService, SPARKLE, tweenAfter, smoothstep, ANOMALO_GLOW, ANOMALO_RING, BFLY_DUSK, BFLY_GOLD, BFLY_ROSE, CAT_CORONA, CAT_SOLE, CAT_SUN, FOX_STAR, GUARD_GLASS, GUARD_PALE, GUARD_VIOLET, HYDRA_LIGHT, IMP, LEOPARD_ICE, LEOPARD_SOLE, LEOPARD_STAR, NAMELESS_HALO, NAMELESS_SPARK, PEARL_SOLE, PUFF_FROST, PUFF_ICE, SAND_AWAY, SAND_DUSK, SAND_GOLD, SAND_PALE, SAND_SOLE, SHADOW_EYESHINE, SHADOW_INK, SHADOW_RIM, SHADOW_SOLE, SNAIL_SOLE, STAG_DUST, STAG_ICE, STAG_ION, TORT, WARDEN_SOLE, pearlAt, shadowDisc = K.Debris, K.Lighting, K.Players, K.RunService, K.TweenService, K.SPARKLE, K.tweenAfter, K.smoothstep, K.ANOMALO_GLOW, K.ANOMALO_RING, K.BFLY_DUSK, K.BFLY_GOLD, K.BFLY_ROSE, K.CAT_CORONA, K.CAT_SOLE, K.CAT_SUN, K.FOX_STAR, K.GUARD_GLASS, K.GUARD_PALE, K.GUARD_VIOLET, K.HYDRA_LIGHT, K.IMP, K.LEOPARD_ICE, K.LEOPARD_SOLE, K.LEOPARD_STAR, K.NAMELESS_HALO, K.NAMELESS_SPARK, K.PEARL_SOLE, K.PUFF_FROST, K.PUFF_ICE, K.SAND_AWAY, K.SAND_DUSK, K.SAND_GOLD, K.SAND_PALE, K.SAND_SOLE, K.SHADOW_EYESHINE, K.SHADOW_INK, K.SHADOW_RIM, K.SHADOW_SOLE, K.SNAIL_SOLE, K.STAG_DUST, K.STAG_ICE, K.STAG_ION, K.TORT, K.WARDEN_SOLE, K.pearlAt, K.shadowDisc

    local Blasts = {}


    function Blasts.HellBreath(rig, fx)
        local colors, u, neon = rig.profile.Colors, rig.unit, fx.neon
        for name, mouth in rig.points do
            local tag = string.match(name, "^Head(%a)_Mouth$")
            local head = tag and rig.parts["Head" .. tag]
            if not head then
                continue
            end
            local from = mouth.WorldPosition
            local direction = (from - head.Position)
            direction = Vector3.new(direction.X, direction.Y * 0.3, direction.Z).Unit
            for index = 1, 9 do
                task.delay(index * 0.045, function()
                    local reach = (1.4 + index * 0.28) * u
                    local ball = neon(Vector3.one * 0.14 * u, CFrame.new(from), if index % 3 == 0 then colors.Sun else colors.Gold)
                    ball.Shape = Enum.PartType.Ball
                    local spread = Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5) * 0.35 * u
                    TweenService:Create(ball, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
                        CFrame = CFrame.new(from + direction * reach + spread),
                        Size = Vector3.one * (0.45 + index * 0.04) * u,
                        Transparency = 1,
                        Color = colors.Amber,
                    }):Play()
                end)
            end
            local light = Instance.new("PointLight")
            light.Color = colors.Gold
            light.Range = 8 * u
            light.Brightness = 4
            light.Parent = head
            TweenService:Create(light, TweenInfo.new(0.9), { Brightness = 0 }):Play()
            Debris:AddItem(light, 1)
        end
        if rig.burst then
            rig.burst:Emit(25)
        end
    end

    function Blasts.SporeBloom(rig, fx)
        local colors, u, origin, facing, neon = rig.profile.Colors, rig.unit, fx.origin, fx.facing, fx.neon

        for index = 1, 22 do
            local dir = Vector3.new(math.random() - 0.5, math.random() * 0.8 - 0.1, math.random() - 0.5).Unit
            local size = (0.08 + math.random() * 0.12) * u
            local spore = neon(Vector3.one * size, CFrame.new(origin), if index % 3 == 0 then colors.Orange else colors.Gold)
            spore.Shape = Enum.PartType.Ball
            spore.Transparency = 0.1
            TweenService:Create(spore, TweenInfo.new(1.1 + math.random() * 0.4, Enum.EasingStyle.Quint, Enum.EasingDirection.Out), {
                CFrame = CFrame.new(origin + dir * (2 + math.random() * 2.5) * u + Vector3.new(0, 1 * u, 0)),
                Size = Vector3.one * size * 0.4,
                Transparency = 1,
            }):Play()
        end

        local ground = origin - Vector3.new(0, 1.6 * u, 0)
        for index = 1, 9 do
            local angle = index / 9 * 2 * math.pi + math.random() * 0.3
            local spot = ground + facing:VectorToWorldSpace(Vector3.new(math.cos(angle), 0, math.sin(angle))) * (1.6 + math.random() * 1.2) * u
            local height = (0.35 + math.random() * 0.35) * u
            local stem = neon(Vector3.new(0.08 * u, 0.02, 0.08 * u), CFrame.new(spot), colors.Ivory)
            stem.Shape = Enum.PartType.Cylinder
            stem.CFrame = CFrame.new(spot) * CFrame.Angles(0, 0, math.pi / 2)
            stem.Size = Vector3.new(0.02, 0.08 * u, 0.08 * u)
            local cap = neon(Vector3.new(0.02, 0.02, 0.02), CFrame.new(spot), if index % 2 == 0 then colors.Gold else colors.Orange)
            cap.Shape = Enum.PartType.Ball
            local grow = TweenInfo.new(0.35, Enum.EasingStyle.Back, Enum.EasingDirection.Out)
            TweenService:Create(stem, grow, {
                Size = Vector3.new(height, 0.08 * u, 0.08 * u),
                CFrame = CFrame.new(spot + Vector3.new(0, height / 2, 0)) * CFrame.Angles(0, 0, math.pi / 2),
            }):Play()
            local pop = TweenService:Create(cap, grow, {
                Size = Vector3.new(0.4, 0.18, 0.4) * u,
                CFrame = CFrame.new(spot + Vector3.new(0, height, 0)),
            })
            pop.Completed:Once(function()
                local fade = TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
                TweenService:Create(cap, fade, { Transparency = 1 }):Play()
                TweenService:Create(stem, fade, { Transparency = 1 }):Play()
            end)
            pop:Play()
        end

        local glow = neon(Vector3.one * 0.5 * u, CFrame.new(origin), colors.Sun)
        glow.Shape = Enum.PartType.Ball
        glow.Transparency = 0.4
        TweenService:Create(glow, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 3.5 * u, Transparency = 1 }):Play()
        if rig.burst then
            rig.burst:Emit(30)
        end
    end

    function Blasts.Groundbreaker(rig, fx)
        local colors, u, origin, facing, neon = rig.profile.Colors, rig.unit, fx.origin, fx.facing, fx.neon
        local ground = origin - Vector3.new(0, 1.3 * u, 0)

        local ring = neon(Vector3.new(0.1 * u, 1.2 * u, 1.2 * u), CFrame.new(ground) * CFrame.Angles(0, 0, math.pi / 2), colors.Gold)
        ring.Shape = Enum.PartType.Cylinder
        ring.Transparency = 0.25
        TweenService:Create(ring, TweenInfo.new(0.8, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
            Size = Vector3.new(0.04 * u, 9 * u, 9 * u),
            Transparency = 1,
        }):Play()

        for index = 1, 10 do
            local angle = index / 10 * 2 * math.pi + math.random() * 0.3
            local out = facing:VectorToWorldSpace(Vector3.new(math.cos(angle), 0, math.sin(angle)))
            local base = ground + out * (1.2 + math.random() * 1.6) * u
            local size = Vector3.new(0.45 + math.random() * 0.25, 1 + math.random() * 0.9, 0.5 + math.random() * 0.3) * u
            local spike = Instance.new("WedgePart")
            spike.Anchored = true
            spike.CanCollide = false
            spike.CanQuery = false
            spike.CanTouch = false
            spike.CastShadow = false
            spike.Material = Enum.Material.Slate
            spike.Color = colors.Amber
            spike.Size = size
            spike.CFrame = CFrame.new(base - Vector3.new(0, size.Y, 0)) * CFrame.Angles(0, angle + math.pi / 2, 0)
                * CFrame.Angles(-0.35 - math.random() * 0.25, 0, math.random() * 0.4 - 0.2)
            spike.Parent = ring.Parent
            local up = TweenService:Create(spike, TweenInfo.new(0.18, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {
                CFrame = spike.CFrame + Vector3.new(0, size.Y * 0.9, 0),
            })
            up.Completed:Once(function()
                TweenService:Create(spike, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
                    CFrame = spike.CFrame - Vector3.new(0, size.Y, 0),
                    Transparency = 1,
                }):Play()
            end)
            up:Play()

            local leaf = neon(Vector3.new(0.18, 0.04, 0.3) * u, CFrame.new(base), if index % 2 == 0 then colors.Gold else colors.Orange)
            TweenService:Create(leaf, TweenInfo.new(1, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
                CFrame = CFrame.new(base + out * 1.5 * u + Vector3.new(0, 2.5 * u, 0)) * CFrame.Angles(math.random() * 6, math.random() * 6, 0),
                Transparency = 1,
            }):Play()
        end

        local light = Instance.new("PointLight")
        light.Color = colors.Gold
        light.Range = 9 * u
        light.Brightness = 1.6
        light.Parent = ring
        TweenService:Create(light, TweenInfo.new(0.9), { Brightness = 0 }):Play()
        if rig.burst then
            rig.burst:Emit(25)
        end
    end

    function Blasts.JadeLotus(rig, fx)
        local colors, u, origin, neon = rig.profile.Colors, rig.unit, fx.origin, fx.neon
        local ground = origin - Vector3.new(0, 1.2 * u, 0)

        local function oval(size, cframe, color)
            local part = neon(size, cframe, color)
            local mesh = Instance.new("SpecialMesh")
            mesh.MeshType = Enum.MeshType.Sphere
            mesh.Parent = part
            return part
        end

        local ring = neon(Vector3.new(0.1 * u, 1.5 * u, 1.5 * u), CFrame.new(ground) * CFrame.Angles(0, 0, math.pi / 2), colors.Orange)
        ring.Shape = Enum.PartType.Cylinder
        ring.Transparency = 0.3
        TweenService:Create(ring, TweenInfo.new(1, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
            Size = Vector3.new(0.04 * u, 8 * u, 8 * u),
            Transparency = 1,
        }):Play()

        for layer, spec in { { count = 8, radius = 0.9, length = 1.6, tilt = 1.15, color = colors.Gold }, { count = 6, radius = 0.45, length = 1.2, tilt = 0.6, color = colors.Sun } } do
            for index = 1, spec.count do
                local angle = (index + layer * 0.5) / spec.count * 2 * math.pi
                local base = CFrame.new(ground + Vector3.new(math.sin(angle), 0, math.cos(angle)) * spec.radius * u) * CFrame.Angles(0, angle, 0)
                local size = Vector3.new(0.55, spec.length, 0.12) * u
                local petal = oval(size * 0.4, base * CFrame.new(0, size.Y * 0.2, 0), spec.color)
                petal.Transparency = 0.15
                TweenService:Create(petal, TweenInfo.new(0.45, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {
                    Size = size,
                    CFrame = base * CFrame.Angles(spec.tilt, 0, 0) * CFrame.new(0, size.Y / 2, 0),
                }):Play()
                TweenService:Create(petal, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, 0.6), {
                    Transparency = 1,
                }):Play()
            end
        end

        for index = 1, 7 do
            local angle = index / 7 * 2 * math.pi
            local out = Vector3.new(math.sin(angle), 0, math.cos(angle))
            local shard = Instance.new("WedgePart")
            shard.Anchored = true
            shard.CanCollide = false
            shard.CanQuery = false
            shard.CanTouch = false
            shard.CastShadow = false
            shard.Material = Enum.Material.Glass
            shard.Transparency = 0.2
            shard.Color = colors.Gold
            shard.Size = Vector3.new(0.18, 0.55, 0.3) * u
            shard.CFrame = CFrame.new(ground + out * 0.6 * u) * CFrame.Angles(0, angle, 0)
            shard.Parent = ring.Parent
            local swirl = angle + 0.9
            TweenService:Create(shard, TweenInfo.new(1.2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
                CFrame = CFrame.new(ground + Vector3.new(math.sin(swirl), 0, math.cos(swirl)) * 2.6 * u + Vector3.new(0, 2.2 * u, 0))
                    * CFrame.Angles(math.random() * 6, swirl, math.random() * 6),
                Transparency = 1,
            }):Play()
        end

        for index = 1, 10 do
            local angle = math.random() * 2 * math.pi
            local start = ground + Vector3.new(math.sin(angle), 0, math.cos(angle)) * (0.4 + math.random()) * u + Vector3.new(0, 0.3 * u, 0)
            local leaf = oval(Vector3.new(0.12, 0.03, 0.36) * u, CFrame.new(start) * CFrame.Angles(0, angle, 0), if index % 3 == 0 then colors.Sun else colors.Gold)
            TweenService:Create(leaf, TweenInfo.new(1.3, Enum.EasingStyle.Sine, Enum.EasingDirection.Out), {
                CFrame = CFrame.new(start + Vector3.new(math.sin(angle), 0, math.cos(angle)) * 1.4 * u + Vector3.new(0, (1.8 + math.random()) * u, 0))
                    * CFrame.Angles(math.random() * 3, angle + 2, math.random() * 3),
                Transparency = 1,
            }):Play()
        end

        local light = Instance.new("PointLight")
        light.Color = colors.Gold
        light.Range = 10 * u
        light.Brightness = 1.8
        light.Parent = ring
        TweenService:Create(light, TweenInfo.new(1.1), { Brightness = 0 }):Play()
        if rig.burst then
            rig.burst:Emit(25)
        end
    end

    function Blasts.SacredGrove(rig, fx)
        local colors, u, origin, neon = rig.profile.Colors, rig.unit, fx.origin, fx.neon
        local ground = origin - Vector3.new(0, 1.3 * u, 0)

        local ring = neon(Vector3.new(0.1 * u, 1.4 * u, 1.4 * u), CFrame.new(ground) * CFrame.Angles(0, 0, math.pi / 2), colors.Gold)
        ring.Shape = Enum.PartType.Cylinder
        ring.Transparency = 0.3
        TweenService:Create(ring, TweenInfo.new(1, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
            Size = Vector3.new(0.04 * u, 9 * u, 9 * u),
            Transparency = 1,
        }):Play()

        local function grow(base, direction, length, width, color, delay)
            local axis = CFrame.lookAt(base, base + direction) * CFrame.Angles(-math.pi / 2, 0, 0)
            local limb = neon(Vector3.new(0.05 * u, width, width), axis * CFrame.Angles(0, 0, math.pi / 2), color)
            limb.Shape = Enum.PartType.Cylinder
            limb.Transparency = 0.1
            local stretch = TweenService:Create(limb, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out, 0, false, delay), {
                Size = Vector3.new(length, width, width),
                CFrame = axis * CFrame.new(0, length / 2, 0) * CFrame.Angles(0, 0, math.pi / 2),
            })
            stretch:Play()
            TweenService:Create(limb, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, delay + 0.6), {
                Transparency = 1,
            }):Play()
            return base + direction.Unit * length
        end

        for index = 1, 8 do
            local angle = index / 8 * 2 * math.pi
            local out = Vector3.new(math.sin(angle), 0, math.cos(angle))
            local base = ground + out * 2.1 * u
            local height = (1.1 + 0.3 * math.random()) * u
            local top = grow(base, Vector3.new(0, 1, 0) + out * 0.25, height, 0.12 * u, colors.Gold, 0.05 * index)
            local side = Vector3.new(-out.Z, 0, out.X)
            grow(top - Vector3.new(0, 0.35 * u, 0), Vector3.new(0, 1, 0) + side * 0.8, 0.55 * u, 0.06 * u, colors.Orange, 0.05 * index + 0.2)
            grow(top - Vector3.new(0, 0.2 * u, 0), Vector3.new(0, 1, 0) - side * 0.7, 0.45 * u, 0.06 * u, colors.Sun, 0.05 * index + 0.25)
        end

        for index = 1, 9 do
            local angle = math.random() * 2 * math.pi
            local start = ground + Vector3.new(math.sin(angle), 0, math.cos(angle)) * (0.6 + math.random() * 1.2) * u
            local shard = Instance.new("WedgePart")
            shard.Anchored = true
            shard.CanCollide = false
            shard.CanQuery = false
            shard.CanTouch = false
            shard.CastShadow = false
            shard.Material = Enum.Material.Glass
            shard.Transparency = 0.2
            shard.Color = if index % 2 == 0 then colors.Gold else colors.Orange
            shard.Size = Vector3.new(0.12, 0.35, 0.2) * u
            shard.CFrame = CFrame.new(start) * CFrame.Angles(0, angle, 0)
            shard.Parent = ring.Parent
            TweenService:Create(shard, TweenInfo.new(1.25, Enum.EasingStyle.Sine, Enum.EasingDirection.Out), {
                CFrame = CFrame.new(start + Vector3.new(0, (2 + math.random() * 1.2) * u, 0)) * CFrame.Angles(math.random() * 6, angle + 2.5, math.random() * 6),
                Transparency = 1,
            }):Play()
        end

        for index = 1, 10 do
            local angle = math.random() * 2 * math.pi
            local start = ground + Vector3.new(math.sin(angle), 0, math.cos(angle)) * (0.8 + math.random() * 1.5) * u + Vector3.new(0, 2.6 * u, 0)
            local leaf = neon(Vector3.new(0.1, 0.02, 0.28) * u, CFrame.new(start) * CFrame.Angles(0, angle, 0), if index % 3 == 0 then colors.Sun else colors.Gold)
            local mesh = Instance.new("SpecialMesh")
            mesh.MeshType = Enum.MeshType.Sphere
            mesh.Parent = leaf
            TweenService:Create(leaf, TweenInfo.new(1.3, Enum.EasingStyle.Sine, Enum.EasingDirection.In), {
                CFrame = CFrame.new(start - Vector3.new(0, 2.2 * u, 0) + Vector3.new(math.sin(angle), 0, math.cos(angle)) * 0.8 * u)
                    * CFrame.Angles(math.random() * 3, angle + 3, math.random() * 3),
                Transparency = 1,
            }):Play()
        end

        local light = Instance.new("PointLight")
        light.Color = colors.Gold
        light.Range = 10 * u
        light.Brightness = 1.8
        light.Parent = ring
        TweenService:Create(light, TweenInfo.new(1.1), { Brightness = 0 }):Play()
        if rig.burst then
            rig.burst:Emit(30)
        end
    end

    local RUNE_GLYPHS = {
        { { { 0, -1 }, { 0, 1 } }, { { 0, 0.2 }, { 0.6, 0.8 } }, { { 0, -0.4 }, { -0.6, 0.1 } } },
        { { { -0.5, -1 }, { -0.5, 1 } }, { { 0.5, -1 }, { 0.5, 1 } }, { { -0.5, 0.6 }, { 0.5, -0.2 } } },
        { { { 0, -1 }, { 0, 1 } }, { { -0.6, 0.4 }, { 0, 1 } }, { { 0, 1 }, { 0.6, 0.4 } } },
        { { { 0, -1 }, { 0, 0.3 } }, { { -0.6, 0.3 }, { 0.6, 0.3 } }, { { -0.6, 0.3 }, { 0, 1 } }, { { 0, 1 }, { 0.6, 0.3 } } },
        { { { -0.6, -1 }, { 0, 1 } }, { { 0, 1 }, { 0.6, -1 } }, { { -0.3, -0.1 }, { 0.3, -0.1 } } },
        { { { 0, -1 }, { 0, 1 } }, { { -0.55, -0.55 }, { 0.55, 0.55 } }, { { -0.55, 0.55 }, { 0.55, -0.55 } } },
        { { { -0.5, 1 }, { 0.5, 1 } }, { { 0, 1 }, { 0, -1 } }, { { -0.5, -1 }, { 0.5, -1 } } },
    }

    function Blasts.RuneSeal(rig, fx)
        local colors, u, origin, neon = rig.profile.Colors, rig.unit, fx.origin, fx.neon
        local ground = origin - Vector3.new(0, 0.95 * u, 0)

        for index, radius in { 2.2, 1.6 } do
            local ring = neon(Vector3.new(0.05 * u, 0.4 * u, 0.4 * u), CFrame.new(ground) * CFrame.Angles(0, 0, math.pi / 2), if index == 1 then colors.Gold else colors.Orange)
            ring.Shape = Enum.PartType.Cylinder
            ring.Transparency = 0.2
            TweenService:Create(ring, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
                Size = Vector3.new(0.03 * u, radius * 2 * u, radius * 2 * u),
            }):Play()
            TweenService:Create(ring, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, 0.6), { Transparency = 1 }):Play()
        end

        for index = 1, 8 do
            local angle = index / 8 * 2 * math.pi
            local out = Vector3.new(math.cos(angle), 0, math.sin(angle))
            local centre = ground + out * 1.9 * u + Vector3.new(0, 0.05 * u, 0)
            local frame = CFrame.lookAt(centre, centre - out) * CFrame.Angles(-math.pi / 2, 0, 0)
            local size = 0.28 * u
            for _, stroke in RUNE_GLYPHS[(index - 1) % #RUNE_GLYPHS + 1] do
                for step = 1, #stroke - 1 do
                    local a, b = stroke[step], stroke[step + 1]
                    local from = frame * Vector3.new(a[1] * size, 0, -a[2] * size)
                    local to = frame * Vector3.new(b[1] * size, 0, -b[2] * size)
                    local mid = (from + to) / 2
                    local bar = neon(Vector3.new(0.05 * u, 0.03 * u, (to - from).Magnitude + 0.05 * u), CFrame.lookAt(mid, to), colors.Gold)
                    local rise = Vector3.new(0, (0.7 + 0.1 * (index % 3)) * u, 0)
                    TweenService:Create(bar, TweenInfo.new(1.2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out, 0, false, 0.05 * index), {
                        CFrame = CFrame.new(rise) * CFrame.lookAt(mid, to),
                        Transparency = 1,
                    }):Play()
                end
            end
        end

        for index = 1, 4 do
            local angle = index / 4 * 2 * math.pi + math.pi / 4
            local base = ground + Vector3.new(math.cos(angle), 0, math.sin(angle)) * 2.2 * u
            local pillar = neon(Vector3.new(0.05 * u, 0.12 * u, 0.12 * u), CFrame.new(base) * CFrame.Angles(0, 0, math.pi / 2), colors.Orange)
            pillar.Shape = Enum.PartType.Cylinder
            pillar.Transparency = 0.2
            TweenService:Create(pillar, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
                Size = Vector3.new(3 * u, 0.12 * u, 0.12 * u),
                CFrame = CFrame.new(base + Vector3.new(0, 1.5 * u, 0)) * CFrame.Angles(0, 0, math.pi / 2),
            }):Play()
            TweenService:Create(pillar, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, 0.7), { Transparency = 1 }):Play()
        end

        local light = Instance.new("PointLight")
        light.Color = colors.Gold
        light.Range = 11 * u
        light.Brightness = 2
        light.Parent = fx.neon(Vector3.one * 0.05, CFrame.new(origin), colors.Gold)
        TweenService:Create(light, TweenInfo.new(1.2), { Brightness = 0 }):Play()
        if rig.burst then
            rig.burst:Emit(25)
        end
    end

    function Blasts.SolarCorona(rig, fx)
        local colors, u, origin, neon = rig.profile.Colors, rig.unit, fx.origin, fx.neon
        local facing = fx.facing
        local centre = origin + facing:VectorToWorldSpace(Vector3.new(0, 1.6 * u, 0.6 * u))
        local ground = origin - Vector3.new(0, 1 * u, 0)

        local core = neon(Vector3.one * 0.25 * u, CFrame.new(centre), colors.Sun)
        core.Shape = Enum.PartType.Ball
        core.Transparency = 0.2
        TweenService:Create(core, TweenInfo.new(0.5, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Size = Vector3.one * 1.3 * u }):Play()
        tweenAfter(0.55, core, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
            Size = Vector3.one * 2.4 * u,
            Transparency = 1,
        })

        local plane = CFrame.lookAt(centre, centre + facing.LookVector)
        for index = 1, 12 do
            local angle = index / 12 * 2 * math.pi
            local out = plane:VectorToWorldSpace(Vector3.new(math.cos(angle), math.sin(angle), 0))
            local length = (if index % 2 == 0 then 1.9 else 1.3) * u
            local ray = neon(Vector3.new(0.14 * u, 0.04 * u, 0.1 * u), CFrame.lookAt(centre, centre + out), if index % 2 == 0 then colors.Gold else colors.Orange)
            ray.Transparency = 0.1
            TweenService:Create(ray, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.Out, 0, false, 0.12), {
                Size = Vector3.new(0.12 * u, 0.03 * u, length),
                CFrame = CFrame.lookAt(centre, centre + out) * CFrame.new(0, 0, -(0.7 * u + length / 2)),
            }):Play()
            TweenService:Create(ray, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, 0.7), { Transparency = 1 }):Play()
        end

        local ring = neon(Vector3.new(0.08 * u, 1.2 * u, 1.2 * u), CFrame.new(ground) * CFrame.Angles(0, 0, math.pi / 2), colors.Orange)
        ring.Shape = Enum.PartType.Cylinder
        ring.Transparency = 0.25
        TweenService:Create(ring, TweenInfo.new(1, Enum.EasingStyle.Quad, Enum.EasingDirection.Out, 0, false, 0.4), {
            Size = Vector3.new(0.03 * u, 9 * u, 9 * u),
            Transparency = 1,
        }):Play()

        for index = 1, 10 do
            local angle = math.random() * 2 * math.pi
            local start = centre + plane:VectorToWorldSpace(Vector3.new(math.cos(angle), math.sin(angle), 0)) * 0.5 * u
            local flake = Instance.new("WedgePart")
            flake.Anchored = true
            flake.CanCollide = false
            flake.CanQuery = false
            flake.CanTouch = false
            flake.CastShadow = false
            flake.Material = Enum.Material.Glass
            flake.Transparency = 0.15
            flake.Color = if index % 2 == 0 then colors.Gold else colors.Orange
            flake.Size = Vector3.new(0.05, 0.22, 0.18) * u
            flake.CFrame = CFrame.new(start) * CFrame.Angles(math.random() * 6, math.random() * 6, 0)
            flake.Parent = ring.Parent
            TweenService:Create(flake, TweenInfo.new(1.2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
                CFrame = CFrame.new(start + (start - centre).Unit * 2.4 * u - Vector3.new(0, 0.8 * u, 0)) * CFrame.Angles(math.random() * 6, math.random() * 6, 0),
                Transparency = 1,
            }):Play()
        end

        local light = Instance.new("PointLight")
        light.Color = colors.Gold
        light.Range = 14 * u
        light.Brightness = 2.4
        light.Parent = core
        TweenService:Create(light, TweenInfo.new(1.2), { Brightness = 0 }):Play()
        if rig.burst then
            rig.burst:Emit(35)
        end
    end

    function Blasts.MagmaPop(rig, fx)
        local colors, u, origin, neon = rig.profile.Colors, rig.unit, fx.origin, fx.neon
        local ground = origin - Vector3.new(0, 0.6 * u, 0) + fx.facing.LookVector * 0.5 * u

        local pool = neon(Vector3.new(0.08 * u, 0.6 * u, 0.6 * u), CFrame.new(ground) * CFrame.Angles(0, 0, math.pi / 2), colors.Orange)
        pool.Shape = Enum.PartType.Cylinder
        pool.Transparency = 0.15
        TweenService:Create(pool, TweenInfo.new(0.35, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Size = Vector3.new(0.06 * u, 2.6 * u, 2.6 * u) }):Play()
        tweenAfter(0.5, pool, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
            Size = Vector3.new(0.02 * u, 3.4 * u, 3.4 * u),
            Transparency = 1,
        })

        for index = 1, 9 do
            local angle = index / 9 * 2 * math.pi + math.random() * 0.4
            local out = Vector3.new(math.cos(angle), 0, math.sin(angle))
            local size = Vector3.new(0.3 + math.random() * 0.2, 0.5 + math.random() * 0.5, 0.3 + math.random() * 0.2) * u
            local spike = Instance.new("WedgePart")
            spike.Anchored = true
            spike.CanCollide = false
            spike.CanQuery = false
            spike.CanTouch = false
            spike.CastShadow = false
            spike.Material = Enum.Material.Basalt
            spike.Color = colors.Amber
            spike.Size = size
            local base = ground + out * (0.8 + math.random() * 0.6) * u
            spike.CFrame = CFrame.new(base - Vector3.new(0, size.Y, 0)) * CFrame.Angles(0, angle + math.pi / 2, 0) * CFrame.Angles(-0.3, 0, 0)
            spike.Parent = pool.Parent
            local up = TweenService:Create(spike, TweenInfo.new(0.16, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {
                CFrame = spike.CFrame + Vector3.new(0, size.Y * 0.85, 0),
            })
            up.Completed:Once(function()
                TweenService:Create(spike, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.In, 0, false, 0.25), {
                    CFrame = spike.CFrame - Vector3.new(0, size.Y, 0),
                    Transparency = 1,
                }):Play()
            end)
            up:Play()
        end

        for index = 1, 12 do
            local angle = math.random() * 2 * math.pi
            local blob = neon(Vector3.one * (0.12 + math.random() * 0.1) * u, CFrame.new(ground + Vector3.new(0, 0.2 * u, 0)), if index % 3 == 0 then colors.Sun else colors.Gold)
            blob.Shape = Enum.PartType.Ball
            local peak = ground + Vector3.new(math.cos(angle), 0, math.sin(angle)) * (0.8 + math.random()) * u + Vector3.new(0, (1.4 + math.random()) * u, 0)
            local land = peak + Vector3.new(math.cos(angle), 0, math.sin(angle)) * 0.6 * u - Vector3.new(0, (1.8 + math.random()) * u, 0)
            local rise = TweenService:Create(blob, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CFrame = CFrame.new(peak) })
            rise.Completed:Once(function()
                TweenService:Create(blob, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
                    CFrame = CFrame.new(land),
                    Color = colors.Amber,
                    Transparency = 1,
                }):Play()
            end)
            rise:Play()
        end

        local light = Instance.new("PointLight")
        light.Color = colors.Orange
        light.Range = 9 * u
        light.Brightness = 2
        light.Parent = pool
        TweenService:Create(light, TweenInfo.new(1), { Brightness = 0 }):Play()
        if rig.burst then
            rig.burst:Emit(30)
        end
    end

    -- One long sigh: soft cloud leaves its whole fleece, drifting out, thinning as it goes. Real smoke, not shapes, and nothing beyond the sheep itself.
    function Blasts.CloudBloom(rig, fx)
        local u = rig.unit
        local holder = fx.neon(Vector3.new(1.3, 0.9, 1.5) * u, rig.rootPart.CFrame * CFrame.new(0, 0.25 * u, 0.2 * u), Color3.new(1, 1, 1))
        holder.Transparency = 1
        local puffs = Instance.new("ParticleEmitter")
        puffs.Texture = "rbxasset://textures/particles/smoke_main.dds"
        puffs.Rate = 0
        puffs.Speed = NumberRange.new(0.5 * u, 1.4 * u)
        puffs.SpreadAngle = Vector2.new(180, 180)
        puffs.Drag = 1.8
        puffs.Lifetime = NumberRange.new(1, 1.6)
        puffs.Rotation = NumberRange.new(0, 360)
        puffs.RotSpeed = NumberRange.new(-20, 20)
        puffs.Acceleration = Vector3.new(0, 0.2 * u, 0)
        puffs.LightEmission = 0
        puffs.LightInfluence = 0.75
        puffs.Color = ColorSequence.new(Color3.fromRGB(250, 252, 255))
        puffs.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.3 * u), NumberSequenceKeypoint.new(1, 1.05 * u) })
        puffs.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5), NumberSequenceKeypoint.new(0.35, 0.62), NumberSequenceKeypoint.new(1, 1) })
        puffs.Parent = holder
        puffs:Emit(20)
    end

    -- The foot comes down: earth thrown out along the ground where it lands, chips of stone falling back, and the plum shaken, its petals coming down all at once. All of it in the world's light.
    function Blasts.BetweenSteps(rig, fx)
        local u = rig.unit
        local foot = rig.points.FootFR
        local at = if foot then foot.TransformedWorldCFrame.Position - Vector3.new(0, 0.14 * rig.meters, 0) else fx.origin
        local holder = fx.neon(Vector3.new(0.4, 0.05, 0.4) * u, CFrame.new(at), Color3.new(1, 1, 1))
        holder.Transparency = 1

        local dust = Instance.new("ParticleEmitter")
        dust.Texture = "rbxassetid://82029518693714"
        dust.FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4
        dust.FlipbookMode = Enum.ParticleFlipbookMode.OneShot
        dust.Rate = 0
        dust.EmissionDirection = Enum.NormalId.Top
        dust.SpreadAngle = Vector2.new(88, 88)
        dust.Speed = NumberRange.new(1.2 * u, 2.6 * u)
        dust.Drag = 3.4
        dust.Lifetime = NumberRange.new(0.8, 1.25)
        dust.Rotation = NumberRange.new(0, 360)
        dust.RotSpeed = NumberRange.new(-25, 25)
        dust.Acceleration = Vector3.new(0, -0.5 * u, 0)
        dust.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2 * u), NumberSequenceKeypoint.new(1, 0.68 * u) })
        dust.Color = ColorSequence.new(Color3.fromRGB(198, 182, 150), Color3.fromRGB(150, 150, 130))
        dust.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.55), NumberSequenceKeypoint.new(0.5, 0.72), NumberSequenceKeypoint.new(1, 1) })
        dust.LightEmission = 0
        dust.LightInfluence = 0.85
        dust.Parent = holder
        dust:Emit(11)

        local chips = Instance.new("ParticleEmitter")
        chips.Texture = "rbxassetid://86117030913477"
        chips.Rate = 0
        chips.EmissionDirection = Enum.NormalId.Top
        chips.SpreadAngle = Vector2.new(55, 55)
        chips.Speed = NumberRange.new(1.4 * u, 3 * u)
        chips.Acceleration = Vector3.new(0, -13 * u, 0)
        chips.Lifetime = NumberRange.new(0.45, 0.8)
        chips.Rotation = NumberRange.new(0, 360)
        chips.RotSpeed = NumberRange.new(-420, 420)
        chips.Size = NumberSequence.new(0.042 * u, 0.028 * u)
        chips.LightEmission = 0
        chips.LightInfluence = 0.9
        chips.Parent = holder
        chips:Emit(10)

        for _, petals in rig.state.petals or {} do
            petals:Emit(16)
        end
    end

    -- The star lights where the gas gathered: its own painted flare, a thin shell of gas thrown off, and for a moment a little of its light on the owl. Nothing else in the sky changes.
    function Blasts.StarsNotYetBorn(rig, fx)
        local s, metre = rig.state, rig.meters
        if s.gather then
            s.gather.Enabled = false -- (the grown seed ends on this same frame: its lifetime is the time to the burst)
            s.gather = nil
        end
        local at = s.starAt or fx.origin
        s.starAt = nil
        local holder = fx.neon(Vector3.one * 0.05, CFrame.new(at), Color3.new(1, 1, 1))
        holder.Transparency = 1

        local flare = Instance.new("ParticleEmitter")
        flare.Texture = "rbxassetid://95572555201628"
        flare.Rate = 0
        flare.Lifetime = NumberRange.new(1.35)
        flare.Speed = NumberRange.new(0.25 * metre)
        flare.EmissionDirection = Enum.NormalId.Top
        flare.SpreadAngle = Vector2.new(4, 4)
        flare.Drag = 0.5
        flare.Rotation = NumberRange.new(0, 360)
        flare.RotSpeed = NumberRange.new(-10, 10)
        flare.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.3 * metre), NumberSequenceKeypoint.new(0.07, 2.3 * metre), NumberSequenceKeypoint.new(0.3, 1.25 * metre), NumberSequenceKeypoint.new(1, 0.5 * metre) })
        flare.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.6, 0.12), NumberSequenceKeypoint.new(1, 1) })
        flare.LightEmission = 1
        flare.LightInfluence = 0
        flare.Parent = holder
        flare:Emit(1)

        local shell = Instance.new("ParticleEmitter")
        shell.Texture = "rbxassetid://13655845087"
        shell.FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4
        shell.FlipbookMode = Enum.ParticleFlipbookMode.OneShot
        shell.Rate = 0
        shell.Lifetime = NumberRange.new(0.85)
        shell.Speed = NumberRange.new(0)
        shell.Rotation = NumberRange.new(0, 360)
        shell.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5 * metre), NumberSequenceKeypoint.new(1, 2.6 * metre) })
        shell.Color = ColorSequence.new(Color3.fromRGB(200, 150, 255), Color3.fromRGB(120, 76, 230))
        shell.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.3), NumberSequenceKeypoint.new(1, 1) })
        shell.LightEmission = 0.7
        shell.LightInfluence = 0
        shell.Parent = holder
        shell:Emit(1)

        local light = Instance.new("PointLight")
        light.Color = Color3.fromRGB(200, 160, 255)
        light.Range = 3.2 * metre
        light.Brightness = 2.4
        light.Shadows = false
        light.Parent = holder
        TweenService:Create(light, TweenInfo.new(1), { Brightness = 0 }):Play()
    end

    -- The bell closes: a ring of glowing gas rolls off its rim and sinks away below it, as the ring a real jellyfish's beat leaves in the water, with a little of the nebula torn off round it. Nothing else in the scene changes.
    function Blasts.RollingNebula(rig, fx)
        local metre = rig.meters
        local at = rig.rootPart.CFrame:PointToWorldSpace(Vector3.new(0, 0.42 * metre, 0))
        local holder = fx.neon(Vector3.new(1.3, 0.05, 1.3) * metre, CFrame.new(at), Color3.new(1, 1, 1))
        holder.Transparency = 1

        local ring = Instance.new("ParticleEmitter")
        ring.Texture = "rbxassetid://13655845087"
        ring.FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4
        ring.FlipbookMode = Enum.ParticleFlipbookMode.OneShot
        ring.Orientation = Enum.ParticleOrientation.VelocityPerpendicular
        ring.EmissionDirection = Enum.NormalId.Bottom
        ring.Shape = Enum.ParticleEmitterShape.Box
        ring.Rate = 0
        ring.SpreadAngle = Vector2.new(0, 0)
        ring.Speed = NumberRange.new(1.1 * metre)
        ring.Drag = 1.4
        ring.Lifetime = NumberRange.new(1.35)
        ring.Rotation = NumberRange.new(0, 360)
        ring.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1.3 * metre), NumberSequenceKeypoint.new(1, 3.4 * metre) })
        ring.Color = ColorSequence.new(Color3.fromRGB(255, 70, 170), Color3.fromRGB(110, 60, 240))
        ring.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.6, 0.25), NumberSequenceKeypoint.new(1, 1) })
        ring.LightEmission = 1
        ring.LightInfluence = 0
        ring.Parent = holder
        ring:Emit(1)

        local torn = Instance.new("ParticleEmitter")
        torn.Texture = "rbxassetid://16867371255"
        torn.FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4
        torn.FlipbookMode = Enum.ParticleFlipbookMode.OneShot
        torn.Shape = Enum.ParticleEmitterShape.Disc
        torn.ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface
        torn.ShapePartial = 1
        torn.EmissionDirection = Enum.NormalId.Bottom
        torn.Rate = 0
        torn.SpreadAngle = Vector2.new(24, 24)
        torn.Speed = NumberRange.new(0.5 * metre, 1 * metre)
        torn.Drag = 2
        torn.Lifetime = NumberRange.new(0.8, 1.3)
        torn.Rotation = NumberRange.new(0, 360)
        torn.RotSpeed = NumberRange.new(-30, 30)
        torn.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.07 * metre), NumberSequenceKeypoint.new(1, 0.27 * metre) })
        torn.Color = ColorSequence.new(Color3.fromRGB(255, 96, 170), Color3.fromRGB(128, 84, 226))
        torn.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.45), NumberSequenceKeypoint.new(0.4, 0.4), NumberSequenceKeypoint.new(1, 1) })
        torn.LightEmission = 0.7
        torn.LightInfluence = 0
        torn.Parent = holder
        torn:Emit(26)
    end

    -- It has the star. A flash in its teeth, a little gold falling away from its mouth, and the star stays there, held, until it goes down the hole. Nothing else in the scene changes.
    function Blasts.StarInItsTeeth(rig, fx)
        local s, metre = rig.state, rig.meters
        if s.foxStar then
            s.foxStar:Destroy()
            s.foxStar = nil
        end
        local mouth = rig.points.Mouth
        if not mouth then
            return
        end
        local holder = fx.neon(Vector3.one * 0.05, CFrame.new(mouth.TransformedWorldCFrame.Position), Color3.new(1, 1, 1))
        holder.Transparency = 1

        local flash = Instance.new("ParticleEmitter")
        flash.Texture = FOX_STAR
        flash.Rate = 0
        flash.Lifetime = NumberRange.new(0.34)
        flash.Speed = NumberRange.new(0)
        flash.Rotation = NumberRange.new(0, 360)
        flash.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2 * metre), NumberSequenceKeypoint.new(0.2, 0.95 * metre), NumberSequenceKeypoint.new(1, 0.3 * metre) })
        flash.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.5, 0.2), NumberSequenceKeypoint.new(1, 1) })
        flash.LightEmission = 1
        flash.LightInfluence = 0
        flash.Parent = holder
        flash:Emit(1)

        local sparks = Instance.new("ParticleEmitter")
        sparks.Texture = SPARKLE
        sparks.Rate = 0
        sparks.Lifetime = NumberRange.new(0.45, 0.85)
        sparks.Speed = NumberRange.new(0.8 * metre, 2.2 * metre)
        sparks.SpreadAngle = Vector2.new(180, 180)
        sparks.Drag = 2.5
        sparks.Acceleration = Vector3.new(0, -2.4 * metre, 0)
        sparks.Size = NumberSequence.new(0.07 * metre, 0)
        sparks.Color = ColorSequence.new(Color3.fromRGB(255, 240, 200), Color3.fromRGB(248, 192, 92))
        sparks.LightEmission = 1
        sparks.LightInfluence = 0
        sparks.Parent = holder
        sparks:Emit(16)

        -- held in its teeth through the fall and the landing
        local held = Instance.new("ParticleEmitter")
        held.Name = "HeldStar"
        held.Texture = FOX_STAR
        held.Rate = 0
        held.Lifetime = NumberRange.new(0.82)
        held.Speed = NumberRange.new(0)
        held.LockedToPart = true
        held.Rotation = NumberRange.new(0, 360)
        held.RotSpeed = NumberRange.new(60, 60)
        held.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.3 * metre), NumberSequenceKeypoint.new(0.8, 0.24 * metre), NumberSequenceKeypoint.new(1, 0) })
        held.LightEmission = 1
        held.LightInfluence = 0
        held.Parent = mouth
        held:Emit(1)
        Debris:AddItem(held, 1)

        local light = Instance.new("PointLight")
        light.Color = Color3.fromRGB(255, 225, 170)
        light.Range = 2.4 * metre
        light.Brightness = 2
        light.Shadows = false
        light.Parent = holder
        TweenService:Create(light, TweenInfo.new(0.7), { Brightness = 0 }):Play()
    end

    -- A path of small lights runs out from its feet, winds once round it, and comes back to exactly where it started. Follow it and you arrive. Nothing else in the scene changes.
    function Blasts.TheLongWayRound(rig, fx)
        local metre = rig.meters
        local centre = rig.rootPart.Position
        local rays = RaycastParams.new()
        rays.RespectCanCollide = true
        local floor = workspace:Raycast(centre, Vector3.new(0, -8 * metre, 0), rays)
        local groundY = if floor then floor.Position.Y else centre.Y - WARDEN_SOLE * metre
        local LIGHTS, GAP = 13, 0.085
        local start = math.random() * 2 * math.pi
        local spin = if math.random() < 0.5 then 1 else -1
        for index = 1, LIGHTS do
            local q = index / (LIGHTS + 1)
            local angle = start + spin * 2 * math.pi * q
            local reach = 1.65 * metre * math.sin(math.pi * q) ^ 0.8
            local at = fx.facing:VectorToWorldSpace(Vector3.new(math.cos(angle) * reach, 0, math.sin(angle) * reach)) + centre
            local here = workspace:Raycast(Vector3.new(at.X, centre.Y + metre, at.Z), Vector3.new(0, -8 * metre, 0), rays)
            local y = (if here then here.Position.Y else groundY) + 0.03
            task.delay(index * GAP, function()
                if not rig.model.Parent then
                    return
                end
                local size = 0.17 * metre * (1 - 0.3 * math.abs(q - 0.5))
                local light = fx.neon(Vector3.new(0.02, size, size), CFrame.new(at.X, y, at.Z) * CFrame.Angles(0, 0, math.pi / 2), Color3.fromRGB(255, 118, 26))
                light.Shape = Enum.PartType.Cylinder
                TweenService:Create(light, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1, Size = Vector3.new(0.02, size * 0.4, size * 0.4) }):Play()
                local spark = Instance.new("ParticleEmitter")
                spark.Texture = SPARKLE
                spark.Rate = 0
                spark.Lifetime = NumberRange.new(0.4, 0.7)
                spark.Speed = NumberRange.new(0.35 * metre, 0.7 * metre)
                spark.EmissionDirection = Enum.NormalId.Right
                spark.SpreadAngle = Vector2.new(30, 30)
                spark.Size = NumberSequence.new(0.05 * metre, 0)
                spark.Color = ColorSequence.new(Color3.fromRGB(255, 225, 160), Color3.fromRGB(255, 130, 50))
                spark.LightEmission = 1
                spark.LightInfluence = 0
                spark.Parent = light
                spark:Emit(2)
            end)
        end
    end

    -- It drinks the dream: a soft bloom of light at its tongue's tip, and a shimmer of scale dust drifting down from its wings as it gives its one slow beat. Nothing else in the scene changes.
    function Blasts.AForgottenDream(rig, fx)
        local s, metre = rig.state, rig.meters
        if s.mothThreads then
            for _, thread in s.mothThreads do
                thread.part:Destroy()
            end
            s.mothThreads = nil
        end
        local tip = rig.points.Tongue12
        local at = if tip then tip.TransformedWorldCFrame.Position else fx.origin
        local holder = fx.neon(Vector3.one * 0.05, CFrame.new(at), Color3.new(1, 1, 1))
        holder.Transparency = 1

        local bloom = Instance.new("ParticleEmitter")
        bloom.Texture = SPARKLE
        bloom.Rate = 0
        bloom.Lifetime = NumberRange.new(0.45)
        bloom.Speed = NumberRange.new(0)
        bloom.Rotation = NumberRange.new(0, 360)
        bloom.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1 * metre), NumberSequenceKeypoint.new(0.25, 0.42 * metre), NumberSequenceKeypoint.new(1, 0) })
        bloom.Color = ColorSequence.new(Color3.fromRGB(255, 236, 250), Color3.fromRGB(214, 180, 255))
        bloom.LightEmission = 1
        bloom.LightInfluence = 0
        bloom.Parent = holder
        bloom:Emit(1)

        -- the dust: from all over the wings, drifting down slowly, glinting
        local cloud = fx.neon(Vector3.new(1.6, 0.2, 0.9) * metre, CFrame.new(fx.origin) * fx.facing, Color3.new(1, 1, 1))
        cloud.Transparency = 1
        local dust = Instance.new("ParticleEmitter")
        dust.Texture = SPARKLE
        dust.Shape = Enum.ParticleEmitterShape.Box
        dust.Rate = 0
        dust.Lifetime = NumberRange.new(1.1, 1.6)
        dust.Speed = NumberRange.new(0.05 * metre, 0.2 * metre)
        dust.SpreadAngle = Vector2.new(180, 180)
        dust.Acceleration = Vector3.new(0, -0.35 * metre, 0)
        dust.Drag = 1.2
        dust.Rotation = NumberRange.new(0, 360)
        dust.RotSpeed = NumberRange.new(-40, 40)
        dust.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.04 * metre), NumberSequenceKeypoint.new(1, 0) })
        dust.Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 220, 244)), ColorSequenceKeypoint.new(0.5, Color3.fromRGB(214, 190, 255)), ColorSequenceKeypoint.new(1, Color3.fromRGB(190, 220, 255)) })
        dust.LightEmission = 0.8
        dust.LightInfluence = 0.2
        dust.Parent = cloud
        dust:Emit(34)

        local light = Instance.new("PointLight")
        light.Color = Color3.fromRGB(240, 200, 255)
        light.Range = 2.4 * metre
        light.Brightness = 1.6
        light.Shadows = false
        light.Parent = holder
        TweenService:Create(light, TweenInfo.new(0.8), { Brightness = 0 }):Play()
    end

    -- It pops open, and its plates split the light: a fan of thin spectral rays round it, every colour once, and a scatter of rainbow glints. Nothing else in the scene changes.
    function Blasts.EveryColour(rig, fx)
        local metre = rig.meters
        local centre = fx.origin + Vector3.new(0, 0.12 * metre, 0)
        local RAYS = 7
        for k = 1, RAYS do
            local angle = (k - 1) / RAYS * 2 * math.pi + math.random() * 0.3
            local out = fx.facing:VectorToWorldSpace(Vector3.new(math.cos(angle), 0.35, math.sin(angle))).Unit
            local length = 0.75 * metre
            local colour = Color3.fromHSV((k - 1) / RAYS, 0.55, 1)
            local ray = fx.neon(Vector3.new(0.025 * metre, 0.025 * metre, length), CFrame.lookAt(centre + out * (0.25 * metre + length / 2), centre + out * metre * 3), colour)
            ray.Transparency = 0.15
            TweenService:Create(ray, TweenInfo.new(0.55, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Transparency = 1, CFrame = ray.CFrame + out * 0.35 * metre, Size = Vector3.new(0.01 * metre, 0.01 * metre, length * 1.3) }):Play()
        end
        local holder = fx.neon(Vector3.one * 0.05, CFrame.new(centre), Color3.new(1, 1, 1))
        holder.Transparency = 1
        local glints = Instance.new("ParticleEmitter")
        glints.Texture = SPARKLE
        glints.Rate = 0
        glints.Lifetime = NumberRange.new(0.45, 0.8)
        glints.Speed = NumberRange.new(0.8 * metre, 1.8 * metre)
        glints.SpreadAngle = Vector2.new(180, 60)
        glints.Drag = 3
        glints.Acceleration = Vector3.new(0, -1.2 * metre, 0)
        glints.Size = NumberSequence.new(0.06 * metre, 0)
        glints.Color = ColorSequence.new({
            ColorSequenceKeypoint.new(0, Color3.fromHSV(0.95, 0.5, 1)), ColorSequenceKeypoint.new(0.25, Color3.fromHSV(0.12, 0.5, 1)), ColorSequenceKeypoint.new(0.5, Color3.fromHSV(0.35, 0.5, 1)),
            ColorSequenceKeypoint.new(0.75, Color3.fromHSV(0.58, 0.5, 1)), ColorSequenceKeypoint.new(1, Color3.fromHSV(0.78, 0.5, 1)),
        })
        glints.LightEmission = 1
        glints.LightInfluence = 0
        glints.Parent = holder
        glints:Emit(22)
        local light = Instance.new("PointLight")
        light.Color = Color3.fromRGB(230, 210, 255)
        light.Range = 2.2 * metre
        light.Brightness = 1.8
        light.Shadows = false
        light.Parent = holder
        TweenService:Create(light, TweenInfo.new(0.7), { Brightness = 0 }):Play()
    end

    -- A road of crystal grows up behind it, shard by shard along the way it came, each pair springing up from the ground and fading. Nothing else in the scene changes.
    function Blasts.AHundredYears(rig, fx)
        local metre = rig.meters
        local base = rig.rootPart.CFrame
        local rays = RaycastParams.new()
        rays.RespectCanCollide = true
        local floor = workspace:Raycast(base.Position, Vector3.new(0, -8 * metre, 0), rays)
        local groundY = if floor then floor.Position.Y else base.Position.Y - SNAIL_SOLE * metre
        local COUNT = 8
        local colours = { Color3.fromRGB(60, 220, 190), Color3.fromRGB(90, 205, 230), Color3.fromRGB(120, 235, 210) }
        for index = 1, COUNT do
            local q = index / COUNT
            local at = base:PointToWorldSpace(Vector3.new(0.32 * math.sin(q * math.pi * 1.3) * metre, 0, (0.45 + q * 1.8) * metre))
            local here = workspace:Raycast(Vector3.new(at.X, base.Position.Y + metre, at.Z), Vector3.new(0, -8 * metre, 0), rays)
            local y = if here then here.Position.Y else groundY
            task.delay(q * 0.4, function()
                if not rig.model.Parent then
                    return
                end
                for k = 1, 2 do
                    local h = (0.15 + 0.1 * math.random()) * metre * (1 - 0.35 * q)
                    local w = (0.045 + 0.015 * math.random()) * metre
                    local root = CFrame.new(at.X + (k - 1.5) * 0.07 * metre, y, at.Z) * CFrame.Angles((math.random() - 0.5) * 0.7, math.random() * math.pi, (math.random() - 0.5) * 0.7) * CFrame.Angles(0, math.pi / 4, 0)
                    local shard = fx.neon(Vector3.new(w, 0.01 * metre, w), root, colours[(index + k) % #colours + 1])
                    shard.Transparency = 0.1
                    TweenService:Create(shard, TweenInfo.new(0.25, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Size = Vector3.new(w, h, w), CFrame = root * CFrame.new(0, h / 2 - 0.02 * metre, 0) }):Play()
                    task.delay(0.65, function()
                        if shard.Parent then
                            TweenService:Create(shard, TweenInfo.new(0.45), { Transparency = 1, Size = Vector3.new(w * 0.5, h * 0.6, w * 0.5) }):Play()
                        end
                    end)
                end
            end)
        end
        local holder = fx.neon(Vector3.one * 0.05, base * CFrame.new(0, -SNAIL_SOLE * metre * 0.6, 1.2 * metre), Color3.new(1, 1, 1))
        holder.Transparency = 1
        local glints = Instance.new("ParticleEmitter")
        glints.Texture = SPARKLE
        glints.Shape = Enum.ParticleEmitterShape.Box
        glints.Rate = 0
        glints.Lifetime = NumberRange.new(0.5, 0.9)
        glints.Speed = NumberRange.new(0.2 * metre, 0.6 * metre)
        glints.EmissionDirection = Enum.NormalId.Top
        glints.SpreadAngle = Vector2.new(50, 50)
        glints.Drag = 2
        glints.Size = NumberSequence.new(0.05 * metre, 0)
        glints.Color = ColorSequence.new(Color3.fromRGB(210, 255, 240), Color3.fromRGB(90, 220, 200))
        glints.LightEmission = 1
        glints.LightInfluence = 0
        holder.Size = Vector3.new(0.4, 0.05, 1.8) * metre
        glints.Parent = holder
        glints:Emit(18)
    end

    -- The First Hunt: its arms snap shut, a few sparks fly from their spines, and two rings of magenta light ripple out from it, level, like the surface of
    -- the first sea closing over the strike. Nothing else in the scene changes.
    function Blasts.TheFirstHunt(rig, fx)
        local metre = rig.meters
        local base = rig.rootPart.CFrame
        local head = rig.points.Head
        local centre = if head then head.TransformedWorldCFrame.Position else fx.origin
        local level = CFrame.new(centre) * (base - base.Position)
        for k, delay in { 0, 0.18 } do
            task.delay(delay, function()
                if not rig.model.Parent then
                    return
                end
                local ring = fx.neon(Vector3.new(0.6 * metre, 0.02, 0.6 * metre), level * CFrame.new(0, -0.05 * metre * k, 0), ANOMALO_GLOW)
                ring.Transparency = 1
                for _, face in { Enum.NormalId.Top, Enum.NormalId.Bottom } do
                    local gui = Instance.new("SurfaceGui")
                    gui.Face = face
                    gui.LightInfluence = 0
                    gui.Brightness = 2.2
                    gui.MaxDistance = 250
                    gui.Parent = ring
                    local image = Instance.new("ImageLabel")
                    image.Size = UDim2.fromScale(1, 1)
                    image.BackgroundTransparency = 1
                    image.Image = ANOMALO_RING
                    image.ImageColor3 = if k == 1 then ANOMALO_GLOW else Color3.fromRGB(255, 160, 225)
                    image.Parent = gui
                    TweenService:Create(image, TweenInfo.new(1.1, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { ImageTransparency = 1 }):Play()
                end
                local reach = (if k == 1 then 4.2 else 3.2) * metre
                TweenService:Create(ring, TweenInfo.new(1.1, Enum.EasingStyle.Quart, Enum.EasingDirection.Out), { Size = Vector3.new(reach, 0.02, reach) }):Play()
            end)
        end
        for _, key in { "ArmL5", "ArmR5" } do
            local bone = rig.points[key]
            if bone then
                local holder = fx.neon(Vector3.one * 0.05, CFrame.new(bone.TransformedWorldCFrame.Position), Color3.new(1, 1, 1))
                holder.Transparency = 1
                local sparks = Instance.new("ParticleEmitter")
                sparks.Texture = SPARKLE
                sparks.Rate = 0
                sparks.Lifetime = NumberRange.new(0.25, 0.5)
                sparks.Speed = NumberRange.new(0.6 * metre, 1.4 * metre)
                sparks.SpreadAngle = Vector2.new(180, 180)
                sparks.Drag = 3
                sparks.Size = NumberSequence.new(0.07 * metre, 0)
                sparks.Color = ColorSequence.new(Color3.fromRGB(255, 220, 245), ANOMALO_GLOW)
                sparks.LightEmission = 1
                sparks.LightInfluence = 0
                sparks.Parent = holder
                sparks:Emit(9)
            end
        end
    end

    -- The Void Between: a rift tears open in the air before it, two jagged edges of blue light drawn apart over a starry dark, the heads strike into it,
    -- and it closes. Nothing else in the scene changes.
    function Blasts.TheVoidBetween(rig, fx)
        local metre = rig.meters
        local base = rig.rootPart.CFrame
        local heads = {}
        for _, key in { "HeadL", "HeadR", "HeadML", "HeadMR" } do
            local bone = rig.points[key]
            if bone then
                table.insert(heads, bone.TransformedWorldCFrame.Position)
            end
        end
        local centre = base.Position
        if #heads > 0 then
            centre = Vector3.zero
            for _, p in heads do
                centre += p
            end
            centre /= #heads
        end
        local at = CFrame.new(centre + base.LookVector * 0.32 * metre) * (base - base.Position) -- just ahead of the heads, facing the way it faces
        local height = 0.55 * metre
        local STEPS = 7
        local function edge(sign)
            local points = {}
            for k = 0, STEPS do
                local f = k / STEPS
                local y = (f - 0.5) * height
                local jag = if k == 0 or k == STEPS then 0 else (if k % 2 == 0 then 0.35 else -0.35) * (0.6 + 0.4 * math.random())
                local open = math.sin(math.pi * f) ^ 0.7
                table.insert(points, { y = y, x = sign * (0.012 + 0.07 * open + 0.025 * jag * open) * metre })
            end
            return points
        end
        local pieces = {}
        for _, sign in { -1, 1 } do
            local pts = edge(sign)
            for k = 1, #pts - 1 do
                local a, b = Vector3.new(pts[k].x, pts[k].y, 0), Vector3.new(pts[k + 1].x, pts[k + 1].y, 0)
                local mid, length = (a + b) / 2, (b - a).Magnitude
                local seg = fx.neon(Vector3.new(0.012 * metre, length + 0.006 * metre, 0.012 * metre), at * CFrame.lookAt(mid, mid + (b - a), Vector3.zAxis) * CFrame.Angles(math.pi / 2, 0, 0), HYDRA_LIGHT)
                seg.Transparency = 0.05
                table.insert(pieces, { part = seg, x = mid.X })
            end
        end
        -- the dark between the edges, with its stars
        local dark = fx.neon(Vector3.new(0.1 * metre, height * 0.9, 0.004 * metre), at, Color3.fromRGB(4, 6, 22))
        dark.Material = Enum.Material.SmoothPlastic
        dark.Transparency = 0.15
        local stars = Instance.new("ParticleEmitter")
        stars.Texture = SPARKLE
        stars.Rate = 0
        stars.Lifetime = NumberRange.new(0.5, 0.9)
        stars.Speed = NumberRange.new(0.05 * metre, 0.25 * metre)
        stars.SpreadAngle = Vector2.new(180, 180)
        stars.Size = NumberSequence.new(0.035 * metre, 0)
        stars.Color = ColorSequence.new(Color3.fromRGB(230, 240, 255), HYDRA_LIGHT)
        stars.LightEmission = 1
        stars.LightInfluence = 0
        stars.Parent = dark
        stars:Emit(14)
        -- it opens wide at once, holds, and closes
        for _, piece in pieces do
            local from = piece.part.CFrame
            local inward = at:VectorToWorldSpace(Vector3.new(-piece.x, 0, 0)) -- toward the rift's middle line, in the rift's own frame
            piece.part.CFrame = from + inward * 0.7
            TweenService:Create(piece.part, TweenInfo.new(0.12, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CFrame = from }):Play()
            task.delay(0.75, function()
                if piece.part.Parent then
                    TweenService:Create(piece.part, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { CFrame = from + inward, Transparency = 1 }):Play()
                end
            end)
        end
        TweenService:Create(dark, TweenInfo.new(0.12), { Size = Vector3.new(0.15 * metre, height * 0.9, 0.004 * metre) }):Play()
        task.delay(0.75, function()
            if dark.Parent then
                TweenService:Create(dark, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Size = Vector3.new(0.004 * metre, height * 0.9, 0.004 * metre), Transparency = 1 }):Play()
            end
        end)
    end

    -- Its writing: words in a hand nobody can read, written in the air round it at the height of its chest, a stroke at a time, all six at once; each struck
    -- through; then the whole ring rises a little and is gone.
    function Blasts.Unwritten(rig, fx)
        local metre = rig.meters
        local chest = rig.points.Chest
        local centre = (if chest then chest.TransformedWorldCFrame.Position else fx.origin) + Vector3.new(0, 0.08 * metre, 0)
        local facing = fx.facing
        local radius, span, thick = 0.6 * metre, 0.62, 0.016 * metre
        local WORDS, SAMPLES = 6, 6
        local function at(arc, height)
            local angle = arc / radius
            return centre + facing:VectorToWorldSpace(Vector3.new(math.sin(angle) * radius, height, -math.cos(angle) * radius))
        end
        local strokes = {}
        local function stroke(a, b, color, delay)
            local mid, length = (a + b) / 2, (b - a).Magnitude
            if length < 1e-3 then
                return
            end
            local seg = fx.neon(Vector3.new(thick, thick, length + thick), CFrame.lookAt(mid, b), color)
            seg.Transparency = 1
            TweenService:Create(seg, TweenInfo.new(0.06, Enum.EasingStyle.Linear, Enum.EasingDirection.Out, 0, false, delay), { Transparency = 0.05 }):Play()
            table.insert(strokes, seg)
        end
        for w = 0, WORDS - 1 do
            local letters = math.random(3, 4)
            local width = radius * span / letters -- each letter's share of the word, in studs
            local start = ((w + 0.5) / WORDS * 2 * math.pi - span / 2 + (math.random() - 0.5) * 0.15) * radius
            local base = ((math.random() - 0.5) * 0.06 - 0.03) * metre
            local points = {}
            for l = 0, letters - 1 do
                local kind = math.random()
                local h = (if kind < 0.25 then 0.13 elseif kind < 0.4 then -0.08 else 0.065) * metre
                local loop = 0.25 + 0.12 * math.random() -- past a sixth of a letter the pen runs back on itself: a loop
                for k = 0, SAMPLES - 1 do
                    local turn = k / SAMPLES * 2 * math.pi
                    local y = h * (1 - math.cos(turn)) / 2
                    local x = (l + turn / (2 * math.pi) - loop * math.sin(turn)) * width + 0.3 * y -- leaning
                    table.insert(points, at(start + x, base + y))
                end
            end
            table.insert(points, at(start + letters * width, base))
            local delay = 0.02 + w * 0.06
            for k = 1, #points - 1 do
                stroke(points[k], points[k + 1], NAMELESS_HALO, delay + k * 0.014)
            end
            -- struck through, left to right, once
            local strike = 0.6 + w * 0.03
            local middle = base + 0.035 * metre
            for j = 0, 2 do
                stroke(at(start - 0.02 * metre + j / 3 * (letters * width + 0.04 * metre), middle + j * 0.004 * metre), at(start - 0.02 * metre + (j + 1) / 3 * (letters * width + 0.04 * metre), middle + (j + 1) * 0.004 * metre), NAMELESS_SPARK, strike + j * 0.04)
            end
        end
        -- then all of it rises a little and fades
        for _, seg in strokes do
            tweenAfter(0.95, seg, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1, CFrame = seg.CFrame + Vector3.new(0, 0.12 * metre, 0) })
        end
        local light = Instance.new("PointLight")
        light.Color = NAMELESS_HALO
        light.Range = 3 * metre
        light.Brightness = 2
        light.Parent = fx.neon(Vector3.one * 0.05, CFrame.new(centre), NAMELESS_HALO)
        light.Parent.Transparency = 1
        TweenService:Create(light, TweenInfo.new(1.3), { Brightness = 0 }):Play()
        if rig.burst then
            rig.burst:Emit(12)
        end
    end

    -- Totality: above it a gold sun, and a black moon sliding across it; at totality the corona flares in streamers, a ring of dark rolls out along the
    -- ground and, for whoever is near, the world dims for a moment (not with Reduced Effects); Baily's beads on the moon's edge, the diamond ring, and the
    -- light comes back. All of it faces the camera that sees it.
    function Blasts.Totality(rig, fx)
        local metre = rig.meters
        local head = rig.points.Head
        local camera = workspace.CurrentCamera
        local centre = (if head then head.TransformedWorldCFrame.Position else fx.origin) + Vector3.new(0, 0.5 * metre, 0) -- just above it: in sight of a third-person camera
        local toCamera = if camera then (camera.CFrame.Position - centre).Unit else fx.facing.LookVector
        local face = CFrame.lookAt(centre, centre + toCamera)
        local right, up = face.RightVector, face.UpVector
        local radius = 0.2 * metre
        local disc = CFrame.Angles(0, math.pi / 2, 0) -- a cylinder's axis is its X: turned to face the camera
        local function fade(part, seconds, delay, to)
            tweenAfter(delay, part, TweenInfo.new(seconds, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Transparency = to })
        end

        local sun = fx.neon(Vector3.new(0.01 * metre, 2 * radius, 2 * radius), face * disc, CAT_SUN)
        sun.Shape = Enum.PartType.Cylinder
        sun.Transparency = 1
        fade(sun, 0.15, 0, 0.05)
        fade(sun, 0.35, 1.05, 1)

        local moonAt = face * CFrame.new(0, 0, -0.02 * metre)
        local moon = fx.neon(Vector3.new(0.012 * metre, 2.04 * radius, 2.04 * radius), (moonAt + right * 2.4 * radius) * disc, Color3.fromRGB(6, 4, 14))
        moon.Material = Enum.Material.SmoothPlastic
        moon.Shape = Enum.PartType.Cylinder
        TweenService:Create(moon, TweenInfo.new(0.42, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CFrame = moonAt * disc }):Play()
        tweenAfter(0.85, moon, TweenInfo.new(0.4, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { CFrame = (moonAt - right * 2.4 * radius) * disc, Transparency = 1 })

        -- the corona at totality: streamers of light all round the moon's edge, and a thin ring
        for k = 1, 14 do
            local angle = (k / 14) * 2 * math.pi + math.random() * 0.3
            local direction = right * math.cos(angle) + up * math.sin(angle)
            local length = (0.3 + 0.45 * math.random()) * radius
            local at = centre + toCamera * (0.005 * metre) + direction * (radius + length / 2)
            local streamer = fx.neon(Vector3.new(0.012 * metre, 0.012 * metre, length), CFrame.lookAt(at, at + direction), CAT_CORONA)
            streamer.Transparency = 1
            fade(streamer, 0.08, 0.42, 0.15)
            fade(streamer, 0.4, 0.62, 1)
        end
        for k = 1, 24 do
            local a, b = (k / 24) * 2 * math.pi, ((k + 1) / 24) * 2 * math.pi
            local pa = centre + (right * math.cos(a) + up * math.sin(a)) * radius * 1.04
            local pb = centre + (right * math.cos(b) + up * math.sin(b)) * radius * 1.04
            local arc = fx.neon(Vector3.new(0.014 * metre, 0.014 * metre, (pb - pa).Magnitude), CFrame.lookAt((pa + pb) / 2, pb), CAT_CORONA)
            arc.Transparency = 1
            fade(arc, 0.08, 0.42, 0.05)
            fade(arc, 0.3, 0.95, 1)
        end

        -- Baily's beads, where the sun comes back, and then the diamond ring
        for k = -2, 2 do
            local angle = k * 0.28
            local bead = fx.neon(Vector3.one * 0.03 * metre, CFrame.new(centre + toCamera * (0.03 * metre) + (right * math.cos(angle) + up * math.sin(angle)) * radius), CAT_CORONA)
            bead.Shape = Enum.PartType.Ball
            bead.Transparency = 1
            fade(bead, 0.06, 0.85 + 0.02 * (k + 2), 0)
            fade(bead, 0.2, 1.0, 1)
        end
        local ringAt = centre + toCamera * (0.04 * metre) + right * radius
        local diamond = fx.neon(Vector3.one * 0.07 * metre, CFrame.new(ringAt), CAT_CORONA)
        diamond.Shape = Enum.PartType.Ball
        diamond.Transparency = 1
        fade(diamond, 0.06, 0.98, 0)
        fade(diamond, 0.35, 1.08, 1)
        for _, axis in { right, up } do
            local ray = fx.neon(Vector3.new(0.012 * metre, 0.012 * metre, 0.02 * metre), CFrame.lookAt(ringAt, ringAt + axis), CAT_CORONA)
            ray.Transparency = 1
            tweenAfter(0.98, ray, TweenInfo.new(0.12, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Transparency = 0, Size = Vector3.new(0.012 * metre, 0.012 * metre, 0.9 * radius) })
            fade(ray, 0.3, 1.12, 1)
        end

        -- a ring of dark rolls out along the ground from it
        local ground = rig.rootPart.Position - Vector3.new(0, CAT_SOLE * metre, 0)
        local shade = fx.neon(Vector3.new(0.01 * metre, 0.2 * metre, 0.2 * metre), CFrame.new(ground + Vector3.new(0, 0.01 * metre, 0)) * CFrame.Angles(0, 0, math.pi / 2), Color3.fromRGB(8, 6, 20))
        shade.Material = Enum.Material.SmoothPlastic
        shade.Shape = Enum.PartType.Cylinder
        shade.Transparency = 1
        tweenAfter(0.42, shade, TweenInfo.new(0.55, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.new(0.01 * metre, 4 * metre, 4 * metre), Transparency = 0.45 })
        fade(shade, 0.45, 0.97, 1)

        -- for whoever is near: the world goes dark for a moment
        local player = Players.LocalPlayer
        if camera and (camera.CFrame.Position - centre).Magnitude < 45 and not (player and player:GetAttribute("SettingReducedEffects") == true) then
            local dim = Instance.new("ColorCorrectionEffect")
            dim.Name = "TotalityDim"
            dim.Parent = Lighting
            tweenAfter(0.42, dim, TweenInfo.new(0.15, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Brightness = -0.16, Saturation = -0.35, TintColor = Color3.fromRGB(205, 196, 255) })
            tweenAfter(0.85, dim, TweenInfo.new(0.4, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Brightness = 0, Saturation = 0, TintColor = Color3.new(1, 1, 1) })
            Debris:AddItem(dim, 1.4)
        end

        local light = Instance.new("PointLight")
        light.Color = CAT_CORONA
        light.Range = 3 * metre
        light.Brightness = 0
        light.Parent = diamond
        tweenAfter(0.98, light, TweenInfo.new(0.1, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Brightness = 3 })
        tweenAfter(1.1, light, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Brightness = 0 })
        if rig.burst then
            rig.burst:Emit(10)
        end
    end

    -- It is gone into its shadow (animateShadowcoil): the shadow races off round a loop along the ground, two points of eyeshine in it, leaving a
    -- trail that fades; back where it began it heaves, and the Shadowcoil bursts up out of it in a spray of dark drops and smoke.
    local SHADOW_RACE, SHADOW_STEPS = 0.78, 18 -- seconds round the loop; the loop's pieces
    local SHADOW_LOOP_AHEAD, SHADOW_LOOP_SIDE = 1.15, 0.8 -- metres the loop reaches ahead of it and off to its right

    local shadowRay = RaycastParams.new()
    shadowRay.RespectCanCollide = true

    function Blasts.FirstMove(rig, fx)
        local metre = rig.meters
        local start = rig.rootPart.Position - Vector3.new(0, SHADOW_SOLE * metre + (rig.state.drop or 0), 0)
        local ahead = (fx.facing.LookVector * Vector3.new(1, 0, 1)).Unit
        local right = (fx.facing.RightVector * Vector3.new(1, 0, 1)).Unit
        local centre = start + right * SHADOW_LOOP_SIDE * metre

        -- the loop, laid on whatever ground is under it (a player's character doesn't count)
        local points = {}
        for k = 0, SHADOW_STEPS do
            local angle = (k / SHADOW_STEPS) * 2 * math.pi
            local at = centre - right * (SHADOW_LOOP_SIDE * metre * math.cos(angle)) + ahead * (SHADOW_LOOP_AHEAD * metre * math.sin(angle))
            local hit = workspace:Raycast(at + Vector3.new(0, 0.6 * metre, 0), Vector3.new(0, -1.2 * metre, 0), shadowRay)
            local onCharacter = hit and hit.Instance.Parent and hit.Instance.Parent:FindFirstChildOfClass("Humanoid")
            points[k] = if hit and not onCharacter then Vector3.new(at.X, hit.Position.Y, at.Z) else at
        end
        points[0], points[SHADOW_STEPS] = start, start
        local step = SHADOW_RACE / SHADOW_STEPS
        local race = TweenInfo.new(step, Enum.EasingStyle.Linear)

        -- the shadow and its faint violet rim (its top lower than the shadow's: the two never share a surface), off round the loop
        local pool = fx.neon(Vector3.one, CFrame.new(start), SHADOW_INK)
        pool.Material = Enum.Material.SmoothPlastic
        pool.Shape = Enum.PartType.Cylinder
        pool.Transparency = 0.12
        shadowDisc(pool, start, 0.02, 0.012, 0.8, metre)
        local rim = fx.neon(Vector3.one, CFrame.new(start), SHADOW_RIM)
        rim.Shape = Enum.PartType.Cylinder
        rim.Transparency = 0.55
        shadowDisc(rim, start, 0.0145, 0.014, 0.9, metre)
        local flat = CFrame.Angles(0, 0, math.pi / 2)
        for k = 1, SHADOW_STEPS do
            tweenAfter((k - 1) * step, pool, race, { CFrame = CFrame.new(points[k] + Vector3.new(0, 0.014 * metre, 0)) * flat })
            tweenAfter((k - 1) * step, rim, race, { CFrame = CFrame.new(points[k] + Vector3.new(0, 0.0075 * metre, 0)) * flat })
        end

        -- two points of eyeshine in it, looking where it goes, blinking once
        local function heading(k)
            local from, to = points[math.min(k, SHADOW_STEPS - 1)], points[math.min(k, SHADOW_STEPS - 1) + 1]
            local d = (to - from) * Vector3.new(1, 0, 1)
            return if d.Magnitude > 1e-3 then d.Unit else ahead
        end
        for _, side in { -1, 1 } do
            local function eyeAt(k)
                local forward = heading(k)
                local across = forward:Cross(Vector3.yAxis)
                return CFrame.new(points[k] + (forward * 0.2 + across * 0.07 * side + Vector3.new(0, 0.026, 0)) * metre)
            end
            local eye = fx.neon(Vector3.one * 0.045 * metre, eyeAt(0), SHADOW_EYESHINE)
            eye.Shape = Enum.PartType.Ball
            eye.Transparency = 1
            for k = 1, SHADOW_STEPS do
                tweenAfter((k - 1) * step, eye, race, { CFrame = eyeAt(k) })
            end
            local quick = TweenInfo.new(0.05, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
            tweenAfter(0.05, eye, TweenInfo.new(0.1, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Transparency = 0 })
            tweenAfter(0.42, eye, quick, { Transparency = 1 })
            tweenAfter(0.5, eye, quick, { Transparency = 0 })
            tweenAfter(0.72, eye, TweenInfo.new(0.06, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1 })
        end

        -- the trail: a stain where it passed, fading as it shrinks; three heights in turn, so neighbouring stains never share a surface
        for k = 1, SHADOW_STEPS do
            local stain = fx.neon(Vector3.one, CFrame.new(points[k]), SHADOW_INK)
            stain.Material = Enum.Material.SmoothPlastic
            stain.Shape = Enum.PartType.Cylinder
            stain.Transparency = 1
            local top = 0.004 + 0.003 * (k % 3)
            shadowDisc(stain, points[k], top, 0.003, 0.66, metre)
            local passed = k * step
            tweenAfter(passed - 0.04, stain, TweenInfo.new(0.04, Enum.EasingStyle.Linear), { Transparency = 0.4 })
            tweenAfter(passed, stain, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
                Transparency = 1,
                Size = Vector3.new(0.003 * metre, 0.15 * metre, 0.15 * metre),
            })
        end

        -- back where it began: the shadow heaves and shrinks away, its rim flashes outward, dark drops and smoke burst up
        local out = SHADOW_RACE + 0.02
        tweenAfter(out + 0.04, pool, TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
            Transparency = 1,
            Size = Vector3.new(0.012 * metre, 0.1 * metre, 0.1 * metre),
        })
        tweenAfter(out, rim, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
            Transparency = 1,
            Size = Vector3.new(0.014 * metre, 2.2 * metre, 2.2 * metre),
        })
        for k = 1, 10 do
            local angle = (k / 10) * 2 * math.pi + math.random() * 0.4
            local outward = right * math.cos(angle) + ahead * math.sin(angle)
            local drop = fx.neon(Vector3.one * 0.07 * metre, CFrame.new(start + Vector3.new(0, 0.03 * metre, 0)), SHADOW_INK)
            drop.Material = Enum.Material.SmoothPlastic
            drop.Shape = Enum.PartType.Ball
            drop.Transparency = 1
            local top = start + outward * (0.3 + 0.1 * math.random()) * metre + Vector3.new(0, (0.3 + 0.15 * math.random()) * metre, 0)
            tweenAfter(out, drop, TweenInfo.new(0.05, Enum.EasingStyle.Linear), { Transparency = 0.05 })
            tweenAfter(out, drop, TweenInfo.new(0.28, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CFrame = CFrame.new(top) })
            tweenAfter(out + 0.28, drop, TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
                CFrame = CFrame.new(start + outward * 0.6 * metre + Vector3.new(0, 0.02 * metre, 0)),
                Transparency = 1,
            })
        end
        local puff = fx.neon(Vector3.one * 0.05, CFrame.new(start), SHADOW_INK)
        puff.Transparency = 1
        local smoke = Instance.new("ParticleEmitter")
        smoke.Texture = "rbxasset://textures/particles/smoke_main.dds"
        smoke.Enabled = false
        smoke.Lifetime = NumberRange.new(0.6, 0.9)
        smoke.Speed = NumberRange.new(0.6 * metre, 1.4 * metre)
        smoke.SpreadAngle = Vector2.new(35, 35)
        smoke.EmissionDirection = Enum.NormalId.Top
        smoke.Drag = 3
        smoke.Rotation = NumberRange.new(0, 360)
        smoke.RotSpeed = NumberRange.new(-60, 60)
        smoke.Size = NumberSequence.new(0.2 * metre, 0.55 * metre)
        smoke.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(1, 1) })
        smoke.Color = ColorSequence.new(Color3.fromRGB(60, 46, 96), Color3.fromRGB(20, 14, 34))
        smoke.LightEmission = 0
        smoke.LightInfluence = 0.5
        smoke.Parent = puff
        task.delay(out, function()
            if smoke.Parent then
                smoke:Emit(14)
            end
        end)
    end

    -- It has reared, pearl raised (animatePearlDragon). Heaven's light pours down out of the sky onto the pearl in a column, and the pearl draws it in:
    -- rings closing on it, motes of light streaming into it. As it lunges, the condensed light bursts out: a flash, a ring rolling out along the ground,
    -- shards of pearl light flung outward, and a glow on everything near.
    local PEARL_BURST = 0.68 -- seconds from the start of the blast to the lunge (animatePearlDragon's lunge, at progress 0.68 of NOVA_TIME, from 0.42)
    local PEARL_LIGHT, PEARL_LILAC, PEARL_VIOLET = Color3.fromRGB(255, 240, 214), Color3.fromRGB(196, 176, 255), Color3.fromRGB(132, 96, 250)

    function Blasts.HeavenCondensed(rig, fx)
        local metre = rig.meters
        local pearl = pearlAt(rig, rig.state)
        local ground = rig.rootPart.Position - Vector3.new(0, PEARL_SOLE * metre + (rig.state.drop or 0), 0)

        -- the column: from above down onto the pearl, narrowing as it is drawn in. Two layers, as the breakthrough pillar has: a broad violet sheath and a
        -- bright core, both strong enough to read against a daytime sky (a single pale beam faded to nothing there, seen in Play)
        local sky = fx.neon(Vector3.one * 0.05, CFrame.new(pearl + Vector3.new(0, 5 * metre, 0)), PEARL_LIGHT)
        sky.Transparency = 1
        local into = fx.neon(Vector3.one * 0.05, CFrame.new(pearl), PEARL_LIGHT)
        into.Transparency = 1
        local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
        a0.Parent, a1.Parent = sky, into
        for layer = 1, 2 do
            local core = layer == 2
            local column = Instance.new("Beam")
            column.Attachment0, column.Attachment1 = a0, a1
            column.Segments = 1
            column.FaceCamera = true
            column.LightEmission = if core then 0.8 else 0.6
            column.LightInfluence = 0
            column.Brightness = if core then 2.2 else 1.6
            column.ZOffset = if core then 0.1 else 0
            column.Color = if core then ColorSequence.new(PEARL_LIGHT) else ColorSequence.new(PEARL_VIOLET, PEARL_LILAC)
            column.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.85), NumberSequenceKeypoint.new(0.3, if core then 0.1 else 0.3), NumberSequenceKeypoint.new(1, 0) })
            column.Width0, column.Width1 = 0, 0
            column.Parent = sky
            local w = if core then 0.32 else 1.1
            TweenService:Create(column, TweenInfo.new(0.16, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Width0 = w * metre, Width1 = w * 0.3 * metre }):Play()
            tweenAfter(0.3, column, TweenInfo.new(PEARL_BURST - 0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Width0 = 0, Width1 = 0 })
        end

        -- drawn in: rings closing on the pearl, and motes streaming into it from all round
        local holder = fx.neon(Vector3.one * 2.4 * metre, CFrame.new(pearl), PEARL_LIGHT)
        holder.Transparency = 1
        local rings = Instance.new("ParticleEmitter")
        rings.Texture = "rbxassetid://13655845087"
        rings.FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4
        rings.FlipbookMode = Enum.ParticleFlipbookMode.OneShot
        rings.Shape = Enum.ParticleEmitterShape.Box
        rings.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
        rings.Rate = 0
        rings.Speed = NumberRange.new(0)
        rings.Lifetime = NumberRange.new(0.32)
        rings.Rotation = NumberRange.new(0, 360)
        rings.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1.6 * metre), NumberSequenceKeypoint.new(1, 0.05 * metre) })
        rings.Color = ColorSequence.new(PEARL_LIGHT, PEARL_LILAC)
        rings.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.6), NumberSequenceKeypoint.new(0.5, 0.15), NumberSequenceKeypoint.new(1, 0.6) })
        rings.LightEmission = 1
        rings.LightInfluence = 0
        rings.LockedToPart = true
        rings.Parent = into
        for _, at in { 0.06, 0.2, 0.34 } do
            task.delay(at, function()
                if rings.Parent then
                    rings:Emit(1)
                end
            end)
        end
        local motes = Instance.new("ParticleEmitter")
        motes.Texture = SPARKLE
        motes.Shape = Enum.ParticleEmitterShape.Sphere
        motes.ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface
        motes.ShapeInOut = Enum.ParticleEmitterShapeInOut.Inward
        motes.Rate = 70
        motes.Speed = NumberRange.new(2.2 * metre, 2.8 * metre)
        motes.Lifetime = NumberRange.new(0.42, 0.5)
        motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.05 * metre), NumberSequenceKeypoint.new(0.6, 0.09 * metre), NumberSequenceKeypoint.new(1, 0) })
        motes.Color = ColorSequence.new(PEARL_LILAC, PEARL_LIGHT)
        motes.LightEmission = 1
        motes.LightInfluence = 0
        motes.Parent = holder
        task.delay(PEARL_BURST - 0.45, function()
            motes.Enabled = false
        end)

        -- the burst, as it lunges: a flash in its hand, a ring rolling out along the ground, shards flung out, a glow on everything near
        local flash = fx.neon(Vector3.one * 0.1 * metre, CFrame.new(pearl), PEARL_LIGHT)
        flash.Shape = Enum.PartType.Ball
        flash.Transparency = 1
        tweenAfter(PEARL_BURST, flash, TweenInfo.new(0.08, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Transparency = 0.1, Size = Vector3.one * 0.55 * metre })
        tweenAfter(PEARL_BURST + 0.08, flash, TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1, Size = Vector3.one * 0.8 * metre })
        local glow = Instance.new("PointLight")
        glow.Color = PEARL_LIGHT
        glow.Range = 5 * metre
        glow.Brightness = 0
        glow.Shadows = false
        glow.Parent = flash
        tweenAfter(PEARL_BURST, glow, TweenInfo.new(0.06), { Brightness = 6 })
        tweenAfter(PEARL_BURST + 0.06, glow, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Brightness = 0 })

        local floor = fx.neon(Vector3.new(0.3, 0.05, 0.3) * metre, CFrame.new(ground + Vector3.new(0, 0.05 * metre, 0)), PEARL_LIGHT)
        floor.Transparency = 1
        local wave = Instance.new("ParticleEmitter")
        wave.Texture = "rbxassetid://13655845087"
        wave.FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4
        wave.FlipbookMode = Enum.ParticleFlipbookMode.OneShot
        wave.Orientation = Enum.ParticleOrientation.VelocityPerpendicular
        wave.EmissionDirection = Enum.NormalId.Top
        wave.Shape = Enum.ParticleEmitterShape.Box
        wave.Rate = 0
        wave.SpreadAngle = Vector2.new(0, 0)
        wave.Speed = NumberRange.new(0.01)
        wave.Lifetime = NumberRange.new(0.75)
        wave.Rotation = NumberRange.new(0, 360)
        wave.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.6 * metre), NumberSequenceKeypoint.new(1, 5 * metre) })
        wave.Color = ColorSequence.new(PEARL_LIGHT, PEARL_LILAC)
        wave.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.5, 0.3), NumberSequenceKeypoint.new(1, 1) })
        wave.LightEmission = 1
        wave.LightInfluence = 0
        wave.Parent = floor
        task.delay(PEARL_BURST + 0.04, function()
            if wave.Parent then
                wave:Emit(1)
            end
        end)

        local facing = fx.facing.LookVector * Vector3.new(1, 0, 1)
        facing = if facing.Magnitude > 1e-3 then facing.Unit else Vector3.new(0, 0, -1)
        for k = 1, 9 do
            local angle = (k - 5) * 0.32 + (math.random() - 0.5) * 0.15
            local out = (CFrame.fromAxisAngle(Vector3.yAxis, angle) * facing) + Vector3.new(0, 0.25 + 0.35 * math.random(), 0)
            local shard = fx.neon(Vector3.new(0.035, 0.035, 0.11) * metre, CFrame.lookAt(pearl, pearl + out), if k % 2 == 0 then PEARL_LIGHT else PEARL_LILAC)
            shard.Transparency = 1
            local to = pearl + out.Unit * (1.6 + 0.6 * math.random()) * metre
            tweenAfter(PEARL_BURST, shard, TweenInfo.new(0.04), { Transparency = 0 })
            tweenAfter(PEARL_BURST, shard, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CFrame = CFrame.lookAt(to, to + out) })
            tweenAfter(PEARL_BURST + 0.3, shard, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1, Size = Vector3.new(0.01, 0.01, 0.04) * metre })
        end
        local sparks = Instance.new("ParticleEmitter")
        sparks.Texture = SPARKLE
        sparks.Enabled = false
        sparks.Lifetime = NumberRange.new(0.5, 0.9)
        sparks.Speed = NumberRange.new(2 * metre, 4 * metre)
        sparks.Drag = 4
        sparks.SpreadAngle = Vector2.new(180, 180)
        sparks.Size = NumberSequence.new(0.1 * metre, 0)
        sparks.Color = ColorSequence.new(PEARL_LIGHT, PEARL_LILAC)
        sparks.LightEmission = 1
        sparks.LightInfluence = 0
        sparks.Parent = flash
        task.delay(PEARL_BURST, function()
            if sparks.Parent then
                sparks:Emit(18)
            end
        end)
    end

    -- It springs (animateSnowLeopard): frost bursts up from where it left the ground, and ahead of it, one after another, a line of its pawprints freezes
    -- into the ground, glowing ice-blue with starlight; then each print shatters into a puff of glittering snow.
    local LEOPARD_PRINTS = 6
    local LEOPARD_PRINT_SIZE = 2 -- its prints, twice its paw: at a pet's size, a print the size of its paw is lost on pale ground (seen in Play)
    local LEOPARD_PRINT_GLOW = Color3.fromRGB(70, 160, 255)

    local leopardRay = RaycastParams.new()
    leopardRay.RespectCanCollide = true
    -- The roads and paved floors are decoration laid over the terrain (no collision, invisible to rays) and drawn about 0.4 studs above it (measured in
    -- Play with markers at stepped heights): a mark meant to lie on the ground goes that far above a terrain hit, or the paving covers it
    local LEOPARD_OVER_TERRAIN = 0.45

    -- where a mark on the ground goes, at a point: on whatever is under it, lifted clear of paving over terrain; nil if nothing is under it
    local function leopardGroundAt(at, metre)
        local hit = workspace:Raycast(at + Vector3.new(0, 0.5 * metre, 0), Vector3.new(0, -1 * metre, 0), leopardRay)
        if not hit or (hit.Instance.Parent and hit.Instance.Parent:FindFirstChildOfClass("Humanoid")) then
            return nil
        end
        return Vector3.new(at.X, hit.Position.Y + (if hit.Instance:IsA("Terrain") then LEOPARD_OVER_TERRAIN else 0.03), at.Z)
    end

    function Blasts.WhereTheSkyBegins(rig, fx)
        local metre = rig.meters
        local ground = rig.rootPart.Position - Vector3.new(0, LEOPARD_SOLE * metre + (rig.state.drop or 0), 0)
        local ahead = (fx.facing.LookVector * Vector3.new(1, 0, 1)).Unit
        local right = (fx.facing.RightVector * Vector3.new(1, 0, 1)).Unit

        -- frost bursting up where it sprang, and a ring of rime across the ground
        local holder = fx.neon(Vector3.new(0.5, 0.05, 0.5) * metre, CFrame.new(ground + Vector3.new(0, 0.03 * metre, 0)), LEOPARD_ICE)
        holder.Transparency = 1
        local frost = Instance.new("ParticleEmitter")
        frost.Texture = "rbxasset://textures/particles/smoke_main.dds"
        frost.Enabled = false
        frost.Lifetime = NumberRange.new(0.6, 1)
        frost.Speed = NumberRange.new(0.8 * metre, 1.6 * metre)
        frost.SpreadAngle = Vector2.new(60, 60)
        frost.EmissionDirection = Enum.NormalId.Top
        frost.Drag = 3
        frost.Rotation = NumberRange.new(0, 360)
        frost.RotSpeed = NumberRange.new(-50, 50)
        frost.Size = NumberSequence.new(0.18 * metre, 0.5 * metre)
        frost.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.3), NumberSequenceKeypoint.new(1, 1) })
        frost.Color = ColorSequence.new(Color3.fromRGB(246, 252, 255), LEOPARD_ICE)
        frost.LightEmission = 0.3
        frost.LightInfluence = 0.4
        frost.Parent = holder
        frost:Emit(16)
        local glitter = Instance.new("ParticleEmitter")
        glitter.Texture = SPARKLE
        glitter.Enabled = false
        glitter.Lifetime = NumberRange.new(0.5, 0.9)
        glitter.Speed = NumberRange.new(1 * metre, 2.2 * metre)
        glitter.SpreadAngle = Vector2.new(70, 70)
        glitter.EmissionDirection = Enum.NormalId.Top
        glitter.Drag = 2
        glitter.Acceleration = Vector3.new(0, -1.5 * metre, 0)
        glitter.Size = NumberSequence.new(0.06 * metre, 0)
        glitter.Color = ColorSequence.new(Color3.new(1, 1, 1), LEOPARD_STAR)
        glitter.LightEmission = 1
        glitter.LightInfluence = 0
        glitter.Parent = holder
        glitter:Emit(24)
        local rimeAt = leopardGroundAt(ground, metre) or ground
        local rime = fx.neon(Vector3.new(0.008 * metre, 0.3 * metre, 0.3 * metre), CFrame.new(rimeAt) * CFrame.Angles(0, 0, math.pi / 2), LEOPARD_ICE)
        rime.Shape = Enum.PartType.Cylinder
        rime.Material = Enum.Material.Glass
        rime.Transparency = 0.35
        TweenService:Create(rime, TweenInfo.new(0.4, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.new(0.008 * metre, 2.4 * metre, 2.4 * metre) }):Play()
        tweenAfter(0.35, rime, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1 })

        -- its pawprints, freezing into the ground ahead of it one by one: a big heel pad and four toes, staggered left and right
        for k = 1, LEOPARD_PRINTS do
            local side = if k % 2 == 0 then 1 else -1
            local at = ground + ahead * (0.45 + 0.42 * k) * metre + right * side * 0.12 * metre
            at = leopardGroundAt(at, metre) or at
            local face = CFrame.lookAt(at, at + ahead)
            local appear = 0.06 + 0.07 * k
            local pads = { { 0, 0.02, 0.09, 0.075 } }
            for j = -1.5, 1.5 do
                table.insert(pads, { j * 0.028, -0.05 - 0.012 * (1 - math.abs(j) / 1.5), 0.038, 0.042 })
            end
            for _, pad in pads do
                local k2 = LEOPARD_PRINT_SIZE
                local cf = face * CFrame.new(pad[1] * k2 * metre, 0, pad[2] * k2 * metre) * CFrame.Angles(0, 0, math.pi / 2)
                local mark = fx.neon(Vector3.new(0.004 * metre, pad[4] * k2 * metre, pad[3] * k2 * metre), cf, LEOPARD_PRINT_GLOW)
                mark.Shape = Enum.PartType.Cylinder
                mark.Transparency = 1
                tweenAfter(appear, mark, TweenInfo.new(0.08, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Transparency = 0 })
                tweenAfter(appear + 0.55, mark, TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1 })
            end
            -- as it freezes in, a few motes of starlight rise off it: they show above grass, which hides anything flat on the ground
            task.delay(appear, function()
                if not holder.Parent then
                    return
                end
                local glint = fx.neon(Vector3.one * 0.05, CFrame.new(at + Vector3.new(0, 0.03 * metre, 0)), LEOPARD_ICE)
                glint.Transparency = 1
                local rise = glitter:Clone()
                rise.EmissionDirection = Enum.NormalId.Top
                rise.SpreadAngle = Vector2.new(15, 15)
                rise.Speed = NumberRange.new(0.5 * metre, 0.9 * metre)
                rise.Acceleration = Vector3.zero
                rise.Drag = 3
                rise.Lifetime = NumberRange.new(0.5, 0.8)
                rise.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.07 * metre), NumberSequenceKeypoint.new(1, 0) })
                rise.Color = ColorSequence.new(LEOPARD_ICE, LEOPARD_PRINT_GLOW)
                rise.Parent = glint
                rise:Emit(5)
            end)
            task.delay(appear + 0.6, function()
                if not holder.Parent then
                    return
                end
                local puff = fx.neon(Vector3.one * 0.05, CFrame.new(at + Vector3.new(0, 0.02 * metre, 0)), LEOPARD_ICE)
                puff.Transparency = 1
                local snow = glitter:Clone()
                snow.Speed = NumberRange.new(0.3 * metre, 0.8 * metre)
                snow.Size = NumberSequence.new(0.045 * metre, 0)
                snow.Lifetime = NumberRange.new(0.35, 0.6) -- gone before the special's folder is (2 s)
                snow.Parent = puff
                snow:Emit(7)
            end)
        end
    end

    -- It has reared (animateCometStag). A comet leaves its brow: a white-hot head with a straight blue ion tail and a broad, curving gold dust tail, arcing
    -- up and across the sky; at the top of its arc it bursts into a shower of glittering dust that falls slowly over the stag.
    local STAG_ARC_TIME, STAG_ARC_STEPS = 1.05, 14

    function Blasts.OnceInALifetime(rig, fx)
        local metre = rig.meters
        local s = rig.state
        local from = if s.nucleus then s.nucleus.WorldPosition else fx.origin
        local ahead = (fx.facing.LookVector * Vector3.new(1, 0, 1)).Unit
        local right = (fx.facing.RightVector * Vector3.new(1, 0, 1)).Unit
        -- the arc: up from its brow and forward over its head, a little to its right, bursting above and ahead of it. Low and forward, so the burst stays in a
        -- following camera's view over the pet, wherever the pet is on screen (higher, or across to the side, it left the screen or went behind the HUD's
        -- corner panels: seen in Play and measured on screen)
        local p1 = from + Vector3.yAxis * 1.6 * metre + ahead * 0.4 * metre
        local p2 = from + Vector3.yAxis * 1.1 * metre + right * 0.5 * metre + ahead * 2.2 * metre
        local function arc(f)
            local a = from:Lerp(p1, f)
            local b = p1:Lerp(p2, f)
            return a:Lerp(b, f)
        end

        local head = fx.neon(Vector3.one * 0.14 * metre, CFrame.new(from), STAG_ICE)
        head.Shape = Enum.PartType.Ball
        local glow = Instance.new("PointLight")
        glow.Color = STAG_ICE
        glow.Range = 4 * metre
        glow.Brightness = 3
        glow.Parent = head
        local function tail(half, life, color, width)
            local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
            a0.Position, a1.Position = Vector3.new(0, half * metre, 0), Vector3.new(0, -half * metre, 0)
            a0.Parent, a1.Parent = head, head
            local trail = Instance.new("Trail")
            trail.Attachment0, trail.Attachment1 = a0, a1
            trail.Lifetime = life
            trail.FaceCamera = true
            trail.LightEmission = 1
            trail.LightInfluence = 0
            trail.MinLength = 0
            trail.WidthScale = width
            trail.Color = color
            trail.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.6, 0.35), NumberSequenceKeypoint.new(1, 1) })
            trail.Parent = head
        end
        tail(0.05, 0.35, ColorSequence.new(STAG_ICE, STAG_ION), NumberSequence.new(1, 0.4))                                  -- the ion tail: narrow, straight, blue
        tail(0.14, 0.6, ColorSequence.new({ ColorSequenceKeypoint.new(0, STAG_ICE), ColorSequenceKeypoint.new(0.3, STAG_DUST), ColorSequenceKeypoint.new(1, Color3.fromRGB(236, 176, 92)) }),
            NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5), NumberSequenceKeypoint.new(0.4, 1), NumberSequenceKeypoint.new(1, 0.6) }))   -- the dust tail: broad and gold
        local step = STAG_ARC_TIME / STAG_ARC_STEPS
        for k = 1, STAG_ARC_STEPS do
            local f = k / STAG_ARC_STEPS
            local eased = 1 - (1 - f) ^ 1.6 -- fast off its brow, slowing at the top of the arc
            tweenAfter((k - 1) * step, head, TweenInfo.new(step, Enum.EasingStyle.Linear), { CFrame = CFrame.new(arc(eased)) })
        end
        -- a flash at its brow as the comet leaves
        local flash = fx.neon(Vector3.one * 0.08 * metre, CFrame.new(from), STAG_ICE)
        flash.Shape = Enum.PartType.Ball
        TweenService:Create(flash, TweenInfo.new(0.25, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 0.6 * metre, Transparency = 1 }):Play()

        -- the burst at the top of the arc: the head flares and goes, and its dust falls glittering
        tweenAfter(STAG_ARC_TIME, head, TweenInfo.new(0.15, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 0.5 * metre, Transparency = 1 })
        tweenAfter(STAG_ARC_TIME, glow, TweenInfo.new(0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Brightness = 0 })
        local shower = fx.neon(Vector3.one * 0.05, CFrame.new(arc(1)), STAG_DUST)
        shower.Transparency = 1
        local dust = Instance.new("ParticleEmitter")
        dust.Texture = SPARKLE
        dust.Enabled = false
        dust.Lifetime = NumberRange.new(0.5, 0.8)
        dust.Speed = NumberRange.new(0.6 * metre, 1.5 * metre)
        dust.SpreadAngle = Vector2.new(180, 180)
        dust.Acceleration = Vector3.new(0, -2 * metre, 0)
        dust.Drag = 1.5
        dust.Rotation = NumberRange.new(0, 360)
        dust.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.12 * metre), NumberSequenceKeypoint.new(1, 0) })
        dust.Color = ColorSequence.new(STAG_DUST, STAG_ION)
        dust.LightEmission = 1
        dust.LightInfluence = 0
        dust.Parent = shower
        task.delay(STAG_ARC_TIME, function()
            if dust.Parent then
                dust:Emit(40)
            end
        end)
    end

    -- It has blown away as sand (animateSandPhantom). A dust devil spins up a little to its right, tall and twisting, a ring of sand skittering round its
    -- foot; it re-forms inside it and the devil collapses in a puff as it shakes the sand off. Then it hops back.
    local SAND_DEVIL_TIME = 1.0

    function Blasts.Mirage(rig, fx)
        local metre = rig.meters
        local right = (fx.facing.RightVector * Vector3.new(1, 0, 1)).Unit
        local ground = rig.rootPart.Position - Vector3.new(0, SAND_SOLE * metre + (rig.state.drop or 0), 0)
        local at = ground + right * SAND_AWAY * metre

        -- the devil: a funnel of sand, narrow at the ground and flaring at the top, spinning; its holders turn, so the sand comes off them in a twist.
        -- Dense, warm and barely lit by the world: thin and pale, the first version was nearly invisible against grass (seen in Play)
        local function funnel(width, height, y, rate, size, speed, spread)
            local holder = fx.neon(Vector3.new(width, height, width) * metre, CFrame.new(at + Vector3.new(0, y * metre, 0)), SAND_GOLD)
            holder.Transparency = 1
            local spin = TweenInfo.new(0.2, Enum.EasingStyle.Linear)
            for k = 0, math.floor(SAND_DEVIL_TIME / 0.2) do
                tweenAfter(k * 0.2, holder, spin, { CFrame = CFrame.new(holder.Position) * CFrame.Angles(0, (k + 1) * math.pi * 0.8, 0) })
            end
            local sand = Instance.new("ParticleEmitter")
            sand.Texture = "rbxasset://textures/particles/smoke_main.dds"
            sand.Shape = Enum.ParticleEmitterShape.Cylinder
            sand.ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface
            sand.ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward
            sand.EmissionDirection = Enum.NormalId.Top
            sand.Rate = rate
            sand.Lifetime = NumberRange.new(0.45, 0.75)
            sand.Speed = NumberRange.new(speed * 0.6 * metre, speed * metre)
            sand.SpreadAngle = Vector2.new(spread, spread)
            sand.Drag = 1.5
            sand.Rotation = NumberRange.new(0, 360)
            sand.RotSpeed = NumberRange.new(200, 360)
            sand.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, size * metre), NumberSequenceKeypoint.new(1, size * 2.2 * metre) })
            sand.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.55, 0.15), NumberSequenceKeypoint.new(1, 1) })
            sand.Color = ColorSequence.new(SAND_DUSK:Lerp(SAND_GOLD, 0.5), SAND_DUSK)        -- a deeper ochre: it must stand out against yellow-green grass
            sand.LightEmission = 0.15
            sand.LightInfluence = 0.25
            sand.Parent = holder
            task.delay(SAND_DEVIL_TIME - 0.2, function()
                sand.Enabled = false
            end)
            return holder
        end
        local holder = funnel(0.22, 0.5, 0.25, 150, 0.2, 0.9, 10)         -- the narrow foot of it
        funnel(0.45, 0.4, 0.75, 120, 0.28, 0.7, 30)                         -- the middle
        funnel(0.8, 0.3, 1.15, 100, 0.34, 0.45, 55)                         -- the flared top
        -- three ribbons of sand winding up round it, widening as they climb: what makes a haze read as a whirlwind (seen in Play)
        local steps = 16
        local step = (SAND_DEVIL_TIME - 0.25) / steps
        for r = 0, 2 do
            local function spiral(k)
                local f = k / steps
                local angle = r * 2 * math.pi / 3 + f * 4 * math.pi
                local radius = (0.08 + 0.32 * f) * metre
                return CFrame.new(at + Vector3.new(math.cos(angle) * radius, (0.05 + 1.25 * f) * metre, math.sin(angle) * radius))
            end
            local head = fx.neon(Vector3.one * 0.05, spiral(0), SAND_GOLD)
            head.Transparency = 1
            local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
            a0.Position, a1.Position = Vector3.new(0, 0.05 * metre, 0), Vector3.new(0, -0.05 * metre, 0)
            a0.Parent, a1.Parent = head, head
            local ribbon = Instance.new("Trail")
            ribbon.Attachment0, ribbon.Attachment1 = a0, a1
            ribbon.Lifetime = 0.35
            ribbon.FaceCamera = true
            ribbon.LightEmission = 0.2
            ribbon.LightInfluence = 0.3
            ribbon.Color = ColorSequence.new(SAND_PALE, SAND_DUSK)
            ribbon.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1), NumberSequenceKeypoint.new(1, 1) })
            ribbon.WidthScale = NumberSequence.new(1, 0.3)
            ribbon.Parent = head
            for k = 1, steps do
                tweenAfter(0.05 * r + (k - 1) * step, head, TweenInfo.new(step, Enum.EasingStyle.Linear), { CFrame = spiral(k) })
            end
        end

        -- grains glinting in it
        local grains = Instance.new("ParticleEmitter")
        grains.Texture = SPARKLE
        grains.Shape = Enum.ParticleEmitterShape.Cylinder
        grains.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
        grains.EmissionDirection = Enum.NormalId.Top
        grains.Rate = 40
        grains.Lifetime = NumberRange.new(0.5, 0.8)
        grains.Speed = NumberRange.new(1 * metre, 1.8 * metre)
        grains.SpreadAngle = Vector2.new(35, 35)
        grains.Size = NumberSequence.new(0.04 * metre, 0)
        grains.Color = ColorSequence.new(SAND_PALE)
        grains.LightEmission = 1
        grains.LightInfluence = 0
        grains.Parent = holder
        task.delay(SAND_DEVIL_TIME - 0.2, function()
            grains.Enabled = false
        end)

        -- the ring of sand round its foot, skittering out along the ground
        local foot = fx.neon(Vector3.new(0.3, 0.05, 0.3) * metre, CFrame.new(at + Vector3.new(0, 0.05 * metre, 0)), SAND_GOLD)
        foot.Transparency = 1
        local skitter = Instance.new("ParticleEmitter")
        skitter.Texture = "rbxasset://textures/particles/smoke_main.dds"
        skitter.Shape = Enum.ParticleEmitterShape.Disc
        skitter.ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface
        skitter.ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward
        skitter.EmissionDirection = Enum.NormalId.Top
        skitter.Rate = 30
        skitter.Lifetime = NumberRange.new(0.4, 0.6)
        skitter.Speed = NumberRange.new(0.2 * metre, 0.4 * metre)
        skitter.SpreadAngle = Vector2.new(80, 80)
        skitter.Acceleration = Vector3.new(0, -1 * metre, 0)
        skitter.Size = NumberSequence.new(0.12 * metre, 0.26 * metre)
        skitter.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.15), NumberSequenceKeypoint.new(1, 1) })
        skitter.Color = ColorSequence.new(SAND_GOLD, SAND_DUSK)
        skitter.LightInfluence = 0.25
        skitter.Parent = foot
        task.delay(SAND_DEVIL_TIME - 0.2, function()
            skitter.Enabled = false
        end)

        -- the collapse: as it shakes off, a last puff of sand bursts out round it
        task.delay(0.8, function()
            if not holder.Parent then
                return
            end
            local puff = skitter:Clone()
            puff.Speed = NumberRange.new(0.6 * metre, 1.1 * metre)
            puff.SpreadAngle = Vector2.new(60, 60)
            puff.Parent = foot
            puff.Enabled = false
            puff:Emit(18)
        end)
    end

    -- It has gathered the afternoon's sunlight in its wings (animateSolarButterfly) and lets it go: a warm light flares from it and turns through sunset to
    -- dusk as it fades; motes of gold drift up and out from its wings, reddening and dimming as they go; for whoever is near, the world takes on a sunset's
    -- warmth for a moment, then the colour of dusk, then is itself again.
    function Blasts.Afterglow(rig, fx)
        local metre = rig.meters
        local at = rig.rootPart.Position
        local holder = fx.neon(Vector3.new(1.2, 0.2, 0.8) * metre, CFrame.new(at), BFLY_GOLD)
        holder.Transparency = 1

        -- the light: a flare of noon gold, turning to sunset rose and then to dusk as it fades
        local glow = Instance.new("PointLight")
        glow.Color = BFLY_GOLD
        glow.Range = 2 * metre
        glow.Brightness = 0
        glow.Shadows = false
        glow.Parent = holder
        TweenService:Create(glow, TweenInfo.new(0.15, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Brightness = 5, Range = 6 * metre }):Play()
        tweenAfter(0.25, glow, TweenInfo.new(0.5, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut), { Color = BFLY_ROSE, Brightness = 3.5 })
        tweenAfter(0.8, glow, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Color = BFLY_DUSK, Brightness = 0 })

        -- the motes: gold drifting up and outward from the wings, reddening to dusk and dimming
        local motes = Instance.new("ParticleEmitter")
        motes.Texture = SPARKLE
        motes.Enabled = false
        motes.Shape = Enum.ParticleEmitterShape.Box
        motes.Lifetime = NumberRange.new(0.9, 1.4)
        motes.Speed = NumberRange.new(0.4 * metre, 0.9 * metre)
        motes.SpreadAngle = Vector2.new(70, 70)
        motes.EmissionDirection = Enum.NormalId.Top
        motes.Drag = 1.6
        motes.Acceleration = Vector3.new(0, 0.3 * metre, 0)
        motes.Rotation = NumberRange.new(0, 360)
        motes.RotSpeed = NumberRange.new(-60, 60)
        motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.05 * metre), NumberSequenceKeypoint.new(0.25, 0.1 * metre), NumberSequenceKeypoint.new(1, 0) })
        motes.Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, BFLY_GOLD), ColorSequenceKeypoint.new(0.5, BFLY_ROSE), ColorSequenceKeypoint.new(1, BFLY_DUSK) })
        motes.LightEmission = 1
        motes.LightInfluence = 0
        motes.Parent = holder
        motes:Emit(36)
        -- a soft glow round it, the warmth leaving its wings
        local haze = Instance.new("ParticleEmitter")
        haze.Texture = "rbxasset://textures/particles/smoke_main.dds"
        haze.Enabled = false
        haze.Lifetime = NumberRange.new(0.8, 1.1)
        haze.Speed = NumberRange.new(0.1 * metre, 0.3 * metre)
        haze.SpreadAngle = Vector2.new(180, 180)
        haze.Size = NumberSequence.new(0.5 * metre, 1.4 * metre)
        haze.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.6), NumberSequenceKeypoint.new(1, 1) })
        haze.Color = ColorSequence.new(BFLY_GOLD, BFLY_ROSE)
        haze.LightEmission = 1
        haze.LightInfluence = 0
        haze.Parent = holder
        haze:Emit(6)

        -- for whoever is near: a sunset's warmth for a moment, then dusk, then the world is itself again
        local player = Players.LocalPlayer
        local camera = workspace.CurrentCamera
        if camera and (camera.CFrame.Position - at).Magnitude < 45 and not (player and player:GetAttribute("SettingReducedEffects") == true) then
            local grade = Instance.new("ColorCorrectionEffect")
            grade.Name = "AfterglowGrade"
            grade.Parent = Lighting
            TweenService:Create(grade, TweenInfo.new(0.2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { TintColor = Color3.fromRGB(255, 226, 196), Brightness = 0.04, Saturation = 0.12 }):Play()
            tweenAfter(0.45, grade, TweenInfo.new(0.45, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut), { TintColor = Color3.fromRGB(226, 206, 246), Brightness = -0.04, Saturation = -0.05 })
            tweenAfter(1.0, grade, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { TintColor = Color3.new(1, 1, 1), Brightness = 0, Saturation = 0 })
            Debris:AddItem(grade, 1.6)
        end
    end

    -- It has planted itself under its gnomon (animateTimekeeperTortoise) and stops the hour: the gnomon's edge flares, a ring of hour marks lights round it
    -- one after another on the ground, golden motes stop dead in the air, and for whoever is near the world fades toward an old photograph's sepia for a
    -- heartbeat; then time starts again, the motes drift on and fade, the marks go out and the colour comes back.
    function Blasts.StoppedHour(rig, fx)
        local u, neon = rig.unit, fx.neon
        local body = rig.points.Body
        local centre = if body then body.TransformedWorldCFrame.Position else rig.rootPart.Position
        local params = RaycastParams.new()
        params.FilterDescendantsInstances = { rig.model }
        local hit = workspace:Raycast(centre + Vector3.new(0, 2 * u, 0), Vector3.new(0, -12 * u, 0), params)
        local groundY = if hit then hit.Position.Y else centre.Y - 0.36 * rig.meters
        local ground = Vector3.new(centre.X, groundY + 0.05, centre.Z)

        -- the hour marks: twelve bars of gold light laid flat round it like a dial's, lit one after another in a quarter second, out after the stopped beat;
        -- each finds the ground under it (laid at the height of its middle, on uneven ground half of them were buried and grass hid the rest: seen in Play)
        -- as each lights, a few gold sparks rise off it and stop dead in the air with the rest of time: they show above grass, which hides anything flat
        local facing = fx.facing
        local rise = Instance.new("ParticleEmitter")
        rise.Texture = SPARKLE
        rise.Enabled = false
        rise.EmissionDirection = Enum.NormalId.Top
        rise.SpreadAngle = Vector2.new(12, 12)
        rise.Lifetime = NumberRange.new(1.2, 1.5)
        rise.Speed = NumberRange.new(2.4 * u, 3.4 * u)
        rise.Drag = 7
        rise.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1 * u), NumberSequenceKeypoint.new(0.75, 0.08 * u), NumberSequenceKeypoint.new(1, 0) })
        rise.Color = ColorSequence.new(TORT.GOLD, TORT.SEPIA)
        rise.LightEmission = 0.9
        rise.LightInfluence = 0.1
        for k = 0, 11 do
            local a = k / 12 * 2 * math.pi
            local out = facing:VectorToWorldSpace(Vector3.new(math.sin(a), 0, -math.cos(a)))
            local long = if k % 3 == 0 then 0.55 else 0.32
            local at = leopardGroundAt(ground + out * (2.4 * u), rig.meters)
            if not at then
                continue -- nothing under it (a ledge): that hour stays dark
            end
            local mark = neon(Vector3.new(0.1 * u, 0.04, long * u), CFrame.lookAt(at, at + out), TORT.GOLD)
            mark.Transparency = 1
            tweenAfter(k * 0.022, mark, TweenInfo.new(0.08), { Transparency = 0.15 })
            tweenAfter(0.9, mark, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1 })
            local sparks = rise:Clone()
            sparks.Parent = mark
            task.delay(k * 0.022, function()
                if sparks.Parent then
                    sparks:Emit(if k % 3 == 0 then 4 else 2)
                end
            end)
        end
        rise:Destroy()

        -- the motes: gold, thrown out a little and stopped dead by their drag, hanging as time stands still, then sinking away
        local holder = neon(Vector3.one * 1.6 * u, CFrame.new(centre), TORT.GOLD)
        holder.Shape = Enum.PartType.Ball
        holder.Transparency = 1
        local motes = Instance.new("ParticleEmitter")
        motes.Texture = SPARKLE
        motes.Enabled = false
        motes.Shape = Enum.ParticleEmitterShape.Sphere
        motes.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
        motes.Lifetime = NumberRange.new(1.4, 1.8)
        motes.Speed = NumberRange.new(0.6 * u, 1.2 * u)
        motes.SpreadAngle = Vector2.new(180, 180)
        motes.Drag = 9
        motes.Acceleration = Vector3.new(0, -0.15 * u, 0)
        motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.12 * u), NumberSequenceKeypoint.new(0.7, 0.12 * u), NumberSequenceKeypoint.new(1, 0) })
        motes.Color = ColorSequence.new(TORT.GOLD, TORT.SEPIA)
        motes.LightEmission = 0.8
        motes.LightInfluence = 0.2
        motes.Parent = holder
        motes:Emit(40)

        local light = Instance.new("PointLight")
        light.Color = TORT.GOLD
        light.Range = 5 * u
        light.Brightness = 0
        light.Shadows = false
        light.Parent = holder
        TweenService:Create(light, TweenInfo.new(0.1), { Brightness = 1.6 }):Play()
        tweenAfter(0.8, light, TweenInfo.new(0.5), { Brightness = 0 })

        -- for whoever is near: the world fades toward sepia for the stopped beat, then its colour comes back
        local player = Players.LocalPlayer
        local camera = workspace.CurrentCamera
        if camera and (camera.CFrame.Position - centre).Magnitude < 45 and not (player and player:GetAttribute("SettingReducedEffects") == true) then
            local grade = Instance.new("ColorCorrectionEffect")
            grade.Name = "StoppedHourGrade"
            grade.Parent = Lighting
            TweenService:Create(grade, TweenInfo.new(0.12, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { TintColor = TORT.SEPIA, Saturation = -0.55, Contrast = 0.06 }):Play()
            tweenAfter(0.75, grade, TweenInfo.new(0.45, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut), { TintColor = Color3.new(1, 1, 1), Saturation = 0, Contrast = 0 })
            Debris:AddItem(grade, 1.6)
        end
    end

    -- It has stamped on its moonlet (animateGravityImp) and the ground round it lets go of its stones: they tear out of the ground in puffs of dust, rise to
    -- circle the moonlet round its middle, spin faster and faster with violet motes drawn in after them, and are flung off to fall where they like; a
    -- ripple of violet runs out along the ground. Their orbit lies outside the pebbles' and clear of the imp however it hangs (gravity_imp.py's numbers).
    function Blasts.WhichWayIsDown(rig, fx)
        local u, metre, neon = rig.unit, rig.meters, fx.neon
        local core = rig.points.Core
        local function middle()
            return if core then core.TransformedWorldCFrame.Position else rig.rootPart.Position
        end
        local centre = middle()
        local params = RaycastParams.new()
        params.FilterDescendantsInstances = { rig.model }
        local hit = workspace:Raycast(centre + Vector3.new(0, 1 * u, 0), Vector3.new(0, -14 * u, 0), params)
        local groundY = if hit then hit.Position.Y else centre.Y - 0.45 * metre
        local player = Players.LocalPlayer
        local reduced = player and player:GetAttribute("SettingReducedEffects") == true
        local count = if reduced then 6 else 12

        local stones = {}
        for k = 1, count do
            local a0 = (k - 1) / count * 2 * math.pi + math.random() * 0.4
            local r0 = (1.8 + math.random() * 1.2) * u
            local at = leopardGroundAt(Vector3.new(centre.X + math.cos(a0) * r0, groundY, centre.Z + math.sin(a0) * r0), metre)
            if at then
                local size = (0.17 + math.random() * 0.13) * u
                local stone = neon(Vector3.new(size, size * (0.6 + math.random() * 0.4), size * (0.7 + math.random() * 0.5)), CFrame.new(at), IMP.STONE:Lerp(IMP.DUST, math.random() * 0.4))
                stone.Material = Enum.Material.Slate
                if not reduced then
                    local dust = Instance.new("ParticleEmitter")
                    dust.Texture = "rbxasset://textures/particles/smoke_main.dds"
                    dust.Enabled = false
                    dust.Lifetime = NumberRange.new(0.5, 0.9)
                    dust.Speed = NumberRange.new(0.3 * u, 0.8 * u)
                    dust.SpreadAngle = Vector2.new(70, 70)
                    dust.EmissionDirection = Enum.NormalId.Top
                    dust.Drag = 3
                    dust.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.15 * u), NumberSequenceKeypoint.new(1, 0.4 * u) })
                    dust.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.45), NumberSequenceKeypoint.new(1, 1) })
                    dust.Color = ColorSequence.new(IMP.DUST)
                    dust.LightInfluence = 1
                    dust.Parent = stone
                    dust:Emit(4)
                end
                table.insert(stones, {
                    part = stone,
                    from = at,
                    a = math.atan2(at.Z - centre.Z, at.X - centre.X),
                    r = (1.65 + math.random() * 0.35) * u, -- (outside the pebbles' orbit, which reaches 1.35 u)
                    h = (math.random() - 0.5) * 0.4 * u,
                    turn = Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5) * 9,
                })
            end
        end

        -- a ripple of violet along the ground
        local ripple = neon(Vector3.new(0.03 * u, 0.6 * u, 0.6 * u), CFrame.new(centre.X, groundY + 0.04 * u, centre.Z) * CFrame.Angles(0, 0, math.pi / 2), IMP.VIOLET)
        ripple.Shape = Enum.PartType.Cylinder
        ripple.Transparency = 0.35
        TweenService:Create(ripple, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.new(0.02 * u, 5.2 * u, 5.2 * u), Transparency = 1 }):Play()

        -- violet motes drawn in toward the moonlet as the stones whirl
        local holder = neon(Vector3.one * 3.6 * u, CFrame.new(centre), IMP.VIOLET)
        holder.Shape = Enum.PartType.Ball
        holder.Transparency = 1
        if not reduced then
            local motes = Instance.new("ParticleEmitter")
            motes.Texture = SPARKLE
            motes.Shape = Enum.ParticleEmitterShape.Sphere
            motes.ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface
            motes.ShapeInOut = Enum.ParticleEmitterShapeInOut.Inward
            motes.Rate = 40
            motes.Lifetime = NumberRange.new(0.5, 0.7)
            motes.Speed = NumberRange.new(2 * u, 2.6 * u)
            motes.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1 * u), NumberSequenceKeypoint.new(1, 0) })
            motes.Color = ColorSequence.new(IMP.VIOLET, IMP.DEEP)
            motes.LightEmission = 0.8
            motes.LightInfluence = 0.1
            motes.Parent = holder
            task.delay(0.9, function()
                motes.Enabled = false
            end)
        end

        -- the stones: up out of the ground to the ring (0.45 s), round it faster and faster (to 1.3 s), flung off and falling (to 1.95 s)
        local start = os.clock()
        local connection
        connection = RunService.Heartbeat:Connect(function()
            local e = os.clock() - start
            if e > 1.95 or #stones == 0 or not stones[1].part.Parent then
                connection:Disconnect()
                return
            end
            local now = middle()
            holder.Position = now
            for _, st in stones do
                local p
                if e < 1.3 then
                    local orbit = if e < 0.45 then 0.8 * e else 0.36 + 1.5 * (e - 0.45) + 7.5 / 2 * (e - 0.45) ^ 2 / 0.85
                    local ang = st.a + orbit
                    local ring = now + Vector3.new(math.cos(ang) * st.r, st.h, math.sin(ang) * st.r)
                    if e < 0.45 then
                        local f = 1 - (1 - e / 0.45) ^ 3
                        p = st.from:Lerp(ring, f) + Vector3.new(0, math.sin(math.pi * e / 0.45) * 0.3 * u, 0)
                    else
                        p = ring
                    end
                    st.last, st.lastAng = p, ang
                else
                    if not st.fling then
                        local ang = st.lastAng
                        st.fling = { at = st.last, v = Vector3.new(-math.sin(ang), 0, math.cos(ang)) * 9 * st.r * 0.35 + Vector3.new(math.cos(ang), 0, math.sin(ang)) * 1.2 * u + Vector3.new(0, 1.2 * u, 0) }
                    end
                    local tau = e - 1.3
                    p = st.fling.at + st.fling.v * tau + Vector3.new(0, -14 * u * tau * tau, 0)
                    st.part.Transparency = math.clamp((e - 1.7) / 0.25, 0, 1)
                end
                st.part.CFrame = CFrame.new(p) * CFrame.Angles(st.turn.X * e, st.turn.Y * e, st.turn.Z * e)
            end
        end)
    end

    -- It has swollen into a ball of hoarfrost (animateGlacierPuff): frost bursts off its spines, a flash of cold light, glittering frost scattering out and
    -- drifting down, and a breath of icy mist rolling out round it.
    function Blasts.HoarfrostBloom(rig, fx)
        local u, neon = rig.unit, fx.neon
        local body = rig.points.Body
        local at = if body then body.TransformedWorldCFrame.Position else rig.rootPart.Position
        -- (the holder is the size of the puffed ball, and everything leaves its surface outward: emitted from its middle, it all stopped inside the fish)
        local holder = neon(Vector3.one * 0.48 * rig.meters, CFrame.new(at), PUFF_FROST)
        holder.Shape = Enum.PartType.Ball
        holder.Transparency = 1

        local light = Instance.new("PointLight")
        light.Color = PUFF_ICE
        light.Range = 4 * u
        light.Brightness = 0
        light.Shadows = false
        light.Parent = holder
        TweenService:Create(light, TweenInfo.new(0.08), { Brightness = 1.8 }):Play()
        tweenAfter(0.1, light, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Brightness = 0 })

        -- the frost: fine glittering crystals thrown off the spines, slowing, drifting down
        local frost = Instance.new("ParticleEmitter")
        frost.Texture = SPARKLE
        frost.Enabled = false
        frost.Shape = Enum.ParticleEmitterShape.Sphere
        frost.ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface
        frost.ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward
        frost.Lifetime = NumberRange.new(0.8, 1.4)
        frost.Speed = NumberRange.new(2 * u, 3.5 * u)
        frost.SpreadAngle = Vector2.new(20, 20)
        frost.Drag = 2.5
        frost.Acceleration = Vector3.new(0, -0.6 * u, 0)
        frost.Rotation = NumberRange.new(0, 360)
        frost.RotSpeed = NumberRange.new(-90, 90)
        frost.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.14 * u), NumberSequenceKeypoint.new(0.3, 0.2 * u), NumberSequenceKeypoint.new(1, 0) }) -- (smaller did not read in Play)
        frost.Color = ColorSequence.new(Color3.new(1, 1, 1), PUFF_ICE)
        frost.LightEmission = 0.8
        frost.LightInfluence = 0.2
        frost.Parent = holder
        frost:Emit(48)

        -- the mist: a breath of cold air rolling out round it and thinning away
        local mist = Instance.new("ParticleEmitter")
        mist.Texture = "rbxasset://textures/particles/smoke_main.dds"
        mist.Enabled = false
        mist.Shape = Enum.ParticleEmitterShape.Sphere
        mist.ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface
        mist.ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward
        mist.Lifetime = NumberRange.new(0.9, 1.3)
        mist.Speed = NumberRange.new(0.8 * u, 1.4 * u)
        mist.SpreadAngle = Vector2.new(15, 15)
        mist.Drag = 2.5
        mist.Rotation = NumberRange.new(0, 360)
        mist.RotSpeed = NumberRange.new(-30, 30)
        mist.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5 * u), NumberSequenceKeypoint.new(1, 1.6 * u) })
        mist.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.4), NumberSequenceKeypoint.new(1, 1) })
        mist.Color = ColorSequence.new(PUFF_FROST)
        mist.LightEmission = 0.2
        mist.LightInfluence = 0.6
        mist.Parent = holder
        mist:Emit(10)
    end

    -- It has held you in its gaze (animateObsidianGuardian) and gives you back to yourself: its mirror face flashes, and for a moment a figure of black glass
    -- stands before it in your shape, facing you; then the figure cracks and falls apart into shards of violet glass that tumble and fade. Whose shape: its
    -- owner's (rig.owner, set by whoever builds it), else whoever stands nearest it.
    local GUARD_MOST_PIECES = 60 -- a figure made of more parts than this keeps only the first ones (a costume of a hundred accessories costs too much)

    local function guardOwnerCharacter(rig)
        local owner = rig.owner
        if owner and owner.Character and owner.Character:FindFirstChild("HumanoidRootPart") then
            return owner.Character
        end
        local best, bestDistance = nil, 30 * rig.unit
        for _, player in Players:GetPlayers() do
            local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
            if root then
                local distance = (root.Position - rig.rootPart.Position).Magnitude
                if distance < bestDistance then
                    best, bestDistance = player.Character, distance
                end
            end
        end
        return best
    end

    local function guardShatter(copy, centre, u, folder)
        local size = copy.Size
        for _ = 1, 2 do
            local shard = Instance.new("WedgePart")
            shard.Anchored = true
            shard.CanCollide = false
            shard.CanTouch = false
            shard.CanQuery = false
            shard.CastShadow = false
            shard.Material = Enum.Material.Glass
            shard.Color = GUARD_GLASS:Lerp(GUARD_VIOLET, 0.35 + 0.3 * math.random())
            shard.Reflectance = 0.3
            shard.Transparency = 0.1
            local k = math.clamp(math.min(size.X, size.Y, size.Z) / u, 0.12, 0.35)
            shard.Size = Vector3.new(0.04, 0.6 + 0.5 * math.random(), 0.45 + 0.4 * math.random()) * k * u
            local offset = Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5) * size * 0.6
            local at = copy.CFrame * CFrame.new(offset)
            shard.CFrame = at * CFrame.Angles(math.random() * 6.28, math.random() * 6.28, math.random() * 6.28)
            shard.Parent = folder
            local away = (at.Position - centre) * Vector3.new(1, 0, 1)
            away = if away.Magnitude > 1e-3 then away.Unit else Vector3.new(math.random() - 0.5, 0, math.random() - 0.5).Unit
            local out = at.Position + away * (0.8 + 1.2 * math.random()) * u + Vector3.new(0, (0.3 + 0.4 * math.random()) * u, 0)
            local spin = CFrame.Angles(math.random() * 3, math.random() * 3, math.random() * 3)
            TweenService:Create(shard, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CFrame = CFrame.new(out) * spin * shard.CFrame.Rotation }):Play()
            tweenAfter(0.35, shard, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
                CFrame = CFrame.new(out - Vector3.new(0, (1 + 0.6 * math.random()) * u, 0) + away * 0.4 * u) * spin * spin * shard.CFrame.Rotation,
                Transparency = 1,
            })
        end
    end

    function Blasts.HonestGlass(rig, fx)
        local u, neon = rig.unit, fx.neon
        local facing = fx.facing.LookVector
        local head = rig.points.Head
        local face = (if head then head.TransformedWorldCFrame.Position else rig.rootPart.Position) + facing * 0.12 * rig.meters

        -- the mirror flashes: a violet-white flare at its face, a burst of glints, a light that cools to violet as it fades
        local flare = neon(Vector3.one * 0.2 * u, CFrame.new(face), GUARD_PALE)
        flare.Shape = Enum.PartType.Ball
        flare.Transparency = 0.1
        TweenService:Create(flare, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 1.1 * u, Transparency = 1 }):Play()
        local folder = flare.Parent
        local light = Instance.new("PointLight")
        light.Color = GUARD_PALE
        light.Range = 4.5 * u
        light.Brightness = 0
        light.Shadows = false
        light.Parent = flare
        TweenService:Create(light, TweenInfo.new(0.06), { Brightness = 2.2 }):Play() -- (a brighter or wider light washed the whole scene white in Play)
        tweenAfter(0.08, light, TweenInfo.new(0.4, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Brightness = 0, Color = GUARD_VIOLET })
        local glints = Instance.new("ParticleEmitter")
        glints.Texture = SPARKLE
        glints.Enabled = false
        glints.Lifetime = NumberRange.new(0.4, 0.8)
        glints.Speed = NumberRange.new(1.5 * u, 3 * u)
        glints.SpreadAngle = Vector2.new(180, 180)
        glints.Drag = 3
        glints.Rotation = NumberRange.new(0, 360)
        glints.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.12 * u), NumberSequenceKeypoint.new(1, 0) })
        glints.Color = ColorSequence.new(GUARD_PALE, GUARD_VIOLET)
        glints.LightEmission = 1
        glints.LightInfluence = 0
        glints.Parent = flare
        glints:Emit(24)

        -- the figure: whoever it shows, made of black glass, standing between it and them, facing them; not drawn with reduced effects or from far off
        local player = Players.LocalPlayer
        local camera = workspace.CurrentCamera
        local character = guardOwnerCharacter(rig)
        local ownerRoot = character and character:FindFirstChild("HumanoidRootPart")
        if not ownerRoot or not camera or (camera.CFrame.Position - face).Magnitude > 70 or (player and player:GetAttribute("SettingReducedEffects") == true) then
            return
        end
        local toOwner = (ownerRoot.Position - rig.rootPart.Position) * Vector3.new(1, 0, 1)
        if toOwner.Magnitude < 0.5 then
            toOwner = facing * Vector3.new(1, 0, 1)
        end
        local spot = rig.rootPart.Position + toOwner.Unit * math.clamp(toOwner.Magnitude * 0.45, 1.2 * u, 2.4 * u)
        local params = RaycastParams.new()
        params.FilterDescendantsInstances = { character, rig.model, folder }
        local hit = workspace:Raycast(spot + Vector3.new(0, 6 * u, 0), Vector3.new(0, -20 * u, 0), params)
        local groundY = if hit then hit.Position.Y else rig.rootPart.Position.Y - 1.5 * u
        local humanoid = character:FindFirstChildOfClass("Humanoid")
        local standing = (if humanoid then humanoid.HipHeight else 2) + ownerRoot.Size.Y / 2
        local at = Vector3.new(spot.X, groundY + standing, spot.Z)
        local target = CFrame.lookAt(at, Vector3.new(ownerRoot.Position.X, at.Y, ownerRoot.Position.Z))
        local glass = {}
        for _, piece in character:GetDescendants() do
            if #glass >= GUARD_MOST_PIECES then
                break
            end
            if piece:IsA("BasePart") and piece ~= ownerRoot and piece.Transparency < 0.95 then
                local copy = piece:Clone() -- (nil when a piece may not be copied)
                if copy then
                    for _, child in copy:GetChildren() do
                        if not child:IsA("DataModelMesh") then
                            child:Destroy()
                        end
                    end
                    copy.Anchored = true
                    copy.CanCollide = false
                    copy.CanTouch = false
                    copy.CanQuery = false
                    copy.CastShadow = false
                    copy.Material = Enum.Material.Glass
                    copy.Color = GUARD_GLASS
                    copy.Reflectance = 0.25
                    copy.Transparency = 1
                    if copy:IsA("MeshPart") then
                        copy.TextureID = ""
                    end
                    local mesh = copy:FindFirstChildWhichIsA("SpecialMesh")
                    if mesh then
                        mesh.TextureId = ""
                    end
                    copy.CFrame = target * ownerRoot.CFrame:ToObjectSpace(piece.CFrame)
                    copy.Parent = folder
                    table.insert(glass, copy)
                    TweenService:Create(copy, TweenInfo.new(0.18), { Transparency = 0.2 }):Play()
                end
            end
        end
        local glow = Instance.new("PointLight")
        glow.Color = GUARD_VIOLET
        glow.Range = 4 * u
        glow.Brightness = 1.5
        glow.Shadows = false
        glow.Parent = neon(Vector3.one * 0.05, CFrame.new(at), GUARD_VIOLET)

        -- it cracks, and falls apart into shards
        task.delay(0.55, function()
            if not folder.Parent then
                return
            end
            for _, copy in glass do
                guardShatter(copy, at, u, folder)
                copy.Transparency = 1
            end
            glow.Brightness = 3
            TweenService:Create(glow, TweenInfo.new(0.5), { Brightness = 0 }):Play()
            local burst = Instance.new("ParticleEmitter")
            burst.Texture = SPARKLE
            burst.Enabled = false
            burst.Lifetime = NumberRange.new(0.4, 0.9)
            burst.Speed = NumberRange.new(1 * u, 2.5 * u)
            burst.SpreadAngle = Vector2.new(180, 180)
            burst.Drag = 2
            burst.Acceleration = Vector3.new(0, -2 * u, 0)
            burst.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1 * u), NumberSequenceKeypoint.new(1, 0) })
            burst.Color = ColorSequence.new(GUARD_PALE, GUARD_VIOLET)
            burst.LightEmission = 1
            burst.LightInfluence = 0
            burst.Parent = glow.Parent
            burst:Emit(30)
        end)
    end

    -- Three ribbons of wind leave its mouth, wind round each other as they run ahead of it, and curl up and away; rings of breath and a scatter of
    -- tumbling leaves go with them.
    function Blasts.TuggingGale(rig, fx)
        local colors, u, facing, neon = rig.profile.Colors, rig.unit, fx.facing, fx.neon
        local mouthBone = rig.points.Blow
        local mouth = if mouthBone then mouthBone.TransformedWorldCFrame.Position else fx.origin
        local ahead = facing:VectorToWorldSpace(Vector3.new(0, 0, -1))
        local right = facing:VectorToWorldSpace(Vector3.new(1, 0, 0))
        local up = Vector3.yAxis
        local function along(angle, f)
            local out = 1 - (1 - f) ^ 2
            local a = angle + f * 8.5
            local radius = (0.14 + 1.05 * f ^ 1.4) * u
            return mouth + ahead * (3.7 * out * u) + up * (2.6 * f ^ 2.2 * u) + right * (math.cos(a) * radius) + up * (math.sin(a) * radius)
        end

        local ribbons = {}
        for index = 1, 3 do
            local head = neon(Vector3.one * 0.05 * u, CFrame.new(mouth), colors.Sun)
            head.Shape = Enum.PartType.Ball
            head.Transparency = 1 -- only its ribbon shows
            local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
            a0.Position = Vector3.new(0, 0.11 * u, 0)
            a1.Position = Vector3.new(0, -0.11 * u, 0)
            a0.Parent, a1.Parent = head, head
            local trail = Instance.new("Trail")
            trail.Attachment0, trail.Attachment1 = a0, a1
            trail.Lifetime = 0.42
            trail.FaceCamera = true
            trail.LightEmission = 0.7
            trail.LightInfluence = 0
            trail.Color = ColorSequence.new(colors.Sun, if index == 2 then colors.Gold else colors.Orange)
            trail.Transparency = NumberSequence.new({
                NumberSequenceKeypoint.new(0, 0.1),
                NumberSequenceKeypoint.new(0.6, 0.45),
                NumberSequenceKeypoint.new(1, 1),
            })
            trail.WidthScale = NumberSequence.new(1, 0.15)
            trail.Parent = head
            table.insert(ribbons, { part = head, angle = index / 3 * 2 * math.pi })
        end
        local started = os.clock()
        local stepper
        stepper = RunService.RenderStepped:Connect(function()
            local f = (os.clock() - started) / 1.25
            if f >= 1 or not ribbons[1].part.Parent then
                stepper:Disconnect()
                for _, ribbon in ribbons do
                    if ribbon.part.Parent then
                        ribbon.part:FindFirstChildOfClass("Trail").Enabled = false
                    end
                end
                return
            end
            for _, ribbon in ribbons do
                ribbon.part.CFrame = CFrame.new(along(ribbon.angle, f))
            end
        end)

        -- rings of breath, each wider and later than the last
        for index = 1, 3 do
            local delay = (index - 1) * 0.11
            local start = CFrame.lookAt(mouth + ahead * 0.2 * u, mouth + ahead * 2 * u) * CFrame.Angles(0, math.pi / 2, 0)
            local ring = neon(Vector3.new(0.05 * u, 0.3 * u, 0.3 * u), start, colors.Gold)
            ring.Shape = Enum.PartType.Cylinder
            ring.Transparency = 1
            -- (a second tween on the same property cancels the first, even one still waiting out its delay: so one tween each, started late)
            task.delay(delay, function()
                if ring.Parent then
                    ring.Transparency = 0.45
                    TweenService:Create(ring, TweenInfo.new(0.62, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
                        CFrame = start + ahead * (1.8 + index * 0.6) * u,
                        Size = Vector3.new(0.015 * u, (1.1 + index * 0.55) * u, (1.1 + index * 0.55) * u),
                        Transparency = 1,
                    }):Play()
                end
            end)
        end

        -- the leaves it has picked up, coral among the green, tumbling along and lifting away
        for index = 1, 12 do
            local angle = math.random() * 2 * math.pi
            local f = 0.45 + math.random() * 0.5
            local petal = (0.09 + math.random() * 0.07) * u
            local leaf = neon(Vector3.new(0.012 * u, petal, petal), CFrame.new(mouth), if index % 4 == 0 then colors.Amber elseif index % 2 == 0 then colors.Gold else colors.Sun)
            leaf.Shape = Enum.PartType.Cylinder -- a thin disc: a petal, not a chip
            leaf.Transparency = 1
            local spin = CFrame.Angles(math.random() * 9 - 4.5, math.random() * 9 - 4.5, math.random() * 9 - 4.5)
            local goal = CFrame.new(along(angle, f) + right * (math.random() - 0.5) * 1.2 * u) * spin
            task.delay(0.02 + math.random() * 0.2, function()
                if leaf.Parent then
                    leaf.Transparency = 0.05
                    TweenService:Create(leaf, TweenInfo.new(1.05, Enum.EasingStyle.Sine, Enum.EasingDirection.Out), { CFrame = goal }):Play()
                    task.delay(0.8, function()
                        if leaf.Parent then
                            TweenService:Create(leaf, TweenInfo.new(0.25), { Transparency = 1 }):Play()
                        end
                    end)
                end
            end)
        end

        local light = Instance.new("PointLight")
        light.Color = colors.Gold
        light.Range = 5 * u
        light.Brightness = 0.8
        light.Parent = ribbons[1].part
        TweenService:Create(light, TweenInfo.new(1), { Brightness = 0 }):Play()
        if rig.burst then
            rig.burst:Emit(14)
        end
    end

    -- It rears and brings its hooves down: sparks fly from all four, and lightning flares through its mane. Its own lightning only: no weather.
    function Blasts.ThunderAnswers(rig, fx)
        for _, name in { "FL", "FR", "BL", "BR" } do
            local sparks = rig.state.sparks and rig.state.sparks[name]
            if sparks then
                sparks:Emit(14)
            end
        end
        rig.state.flickerUntil = rig.state.time + 0.6
    end

    -- The galaxy under its wings, thrown open: stars in three arms wheel outward from its heart in front of it, three of them drawing ribbons, with a ring of light going out.
    function Blasts.TurningOfTheHeavens(rig, fx)
        local colors, u, facing, neon = rig.profile.Colors, rig.unit, fx.facing, fx.neon
        local heart = rig.points.SpiralInner
        local centre = if heart then heart.TransformedWorldCFrame.Position else fx.origin
        local ahead = facing:VectorToWorldSpace(Vector3.new(0, 0, -1))
        local right = facing:VectorToWorldSpace(Vector3.new(1, 0, 0))
        local up = Vector3.yAxis

        local glow = rig.profile.GlowColors
        local gold, violet, pale = glow["ffc878"], glow["8a6bff"], glow["e6e0ff"]
        local stars = {}
        for arm = 1, 3 do
            for index = 1, 16 do
                local f = index / 16
                -- a thin streak of light, turned along its path each frame: a block this size reads as confetti
                local thick = (0.042 - 0.018 * f) * u * (0.8 + 0.4 * math.random())
                local star = neon(Vector3.new(thick, thick, thick * (5 + 3 * math.random())), CFrame.new(centre),
                    if f < 0.32 then gold elseif index % 5 == 0 then pale elseif index % 7 == 0 then colors.Orange else violet)
                if index % 4 == 0 then
                    local a0, a1 = Instance.new("Attachment"), Instance.new("Attachment")
                    a0.Position = Vector3.new(0, 0.035 * u, 0)
                    a1.Position = Vector3.new(0, -0.035 * u, 0)
                    a0.Parent, a1.Parent = star, star
                    local trail = Instance.new("Trail")
                    trail.Attachment0, trail.Attachment1 = a0, a1
                    trail.Lifetime = 0.34
                    trail.FaceCamera = true
                    trail.LightEmission = 0.8
                    trail.LightInfluence = 0
                    trail.Color = ColorSequence.new(pale, violet)
                    trail.Transparency = NumberSequence.new(0.15, 1)
                    trail.WidthScale = NumberSequence.new(1, 0.2)
                    trail.Parent = star
                end
                table.insert(stars, { part = star, angle = arm / 3 * 2 * math.pi + f * 2.6 + (math.random() - 0.5) * 0.14, reach = (0.22 + 1.65 * f) * (0.94 + 0.12 * math.random()) })
            end
        end
        local started = os.clock()
        local stepper
        stepper = RunService.RenderStepped:Connect(function()
            local f = (os.clock() - started) / 1.3
            if f >= 1 or not stars[1].part.Parent then
                stepper:Disconnect()
                return
            end
            local opening = 1 - (1 - f) ^ 2.4
            for _, star in stars do
                local angle = star.angle - 3.2 * opening
                local radius = star.reach * (0.15 + 1.25 * opening) * u
                local at = centre + ahead * (0.25 + 0.9 * opening) * u + right * (math.cos(angle) * radius) + up * (math.sin(angle) * radius)
                if star.last and (at - star.last).Magnitude > 1e-3 then
                    star.part.CFrame = CFrame.lookAt(at, at + (at - star.last))
                else
                    star.part.CFrame = CFrame.new(at)
                end
                star.last = at
                star.part.Transparency = smoothstep(0.62, 1, f)
            end
        end)

        local flash = neon(Vector3.one * 0.3 * u, CFrame.new(centre), colors.Sun)
        flash.Shape = Enum.PartType.Ball
        flash.Transparency = 0.25
        TweenService:Create(flash, TweenInfo.new(0.42, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 1.5 * u, Transparency = 1 }):Play()

        local start = CFrame.lookAt(centre, centre + ahead) * CFrame.Angles(0, math.pi / 2, 0)
        local ring = neon(Vector3.new(0.03 * u, 0.5 * u, 0.5 * u), start, colors.Gold)
        ring.Shape = Enum.PartType.Cylinder
        ring.Transparency = 0.8 -- a filled disc: stronger than this, it reads as a lens across the whole view
        TweenService:Create(ring, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
            CFrame = start + ahead * 1.2 * u,
            Size = Vector3.new(0.01 * u, 3.6 * u, 3.6 * u),
            Transparency = 1,
        }):Play()

        local light = Instance.new("PointLight")
        light.Color = colors.Gold
        light.Range = 6 * u
        light.Brightness = 1.2
        light.Parent = flash
        TweenService:Create(light, TweenInfo.new(0.9), { Brightness = 0 }):Play()
        if rig.burst then
            rig.burst:Emit(18)
        end
    end

    function Blasts.SovereignRoar(rig, fx)
        local colors, u, origin, neon = rig.profile.Colors, rig.unit, fx.origin, fx.neon
        local mouthPoint, crownPoint = rig.points.Jaw_Mouth, rig.points.Head_Crown
        local mouth = if mouthPoint then mouthPoint.WorldPosition else origin
        local crown = if crownPoint then crownPoint.WorldPosition else origin + Vector3.new(0, 0.3 * u, 0)
        local body = rig.parts.Body and rig.parts.Body.Position or rig.rootPart.Position
        local forward = (mouth - body) * Vector3.new(1, 0, 1)
        forward = if forward.Magnitude > 1e-3 then forward.Unit else fx.facing.LookVector

        for index, delay in { 0, 0.14, 0.28 } do
            local ring = neon(Vector3.new(0.04 * u, 0.3 * u, 0.3 * u), CFrame.lookAt(mouth, mouth + forward) * CFrame.Angles(0, math.pi / 2, 0),
                if index == 2 then colors.Sun else colors.Gold)
            ring.Shape = Enum.PartType.Cylinder
            ring.Transparency = 1
            local finish = mouth + forward * (1.1 + 0.5 * index) * u
            TweenService:Create(ring, TweenInfo.new(0.06, Enum.EasingStyle.Linear, Enum.EasingDirection.Out, 0, false, delay), { Transparency = 0.35 }):Play()
            tweenAfter(delay + 0.06, ring, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
                CFrame = CFrame.lookAt(finish, finish + forward) * CFrame.Angles(0, math.pi / 2, 0),
                Size = Vector3.new(0.02 * u, (1.6 + 0.5 * index) * u, (1.6 + 0.5 * index) * u),
                Transparency = 1,
            })
        end

        local behind = crown - forward * 0.12 * u
        local right = forward:Cross(Vector3.yAxis).Unit
        for index = 1, 12 do
            local angle = (index - 0.5) / 12 * math.pi
            local out = (right * math.cos(angle) + Vector3.yAxis * math.sin(angle)).Unit
            local length = (if index % 2 == 0 then 0.55 else 0.4) * u
            local base = behind + out * 0.18 * u
            local ray = neon(Vector3.new(0.05 * u, 0.05 * u, 0.1 * u), CFrame.lookAt(base, base + out), if index % 2 == 0 then colors.Sun else colors.Gold)
            ray.Transparency = 1
            local tip = base + out * length * 0.5
            TweenService:Create(ray, TweenInfo.new(0.1, Enum.EasingStyle.Linear, Enum.EasingDirection.Out, 0, false, 0.05), { Transparency = 0.2 }):Play()
            TweenService:Create(ray, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.Out, 0, false, 0.05), {
                CFrame = CFrame.lookAt(tip, tip + out),
                Size = Vector3.new(0.025 * u, 0.025 * u, length),
            }):Play()
            tweenAfter(0.6, ray, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1 })
        end

        local paws = {}
        for _, name in { "LegFL_Paw", "LegFR_Paw", "LegBL_Paw", "LegBR_Paw" } do
            if rig.points[name] then
                table.insert(paws, rig.points[name].WorldPosition)
            end
        end
        local ground = origin - Vector3.new(0, 0.8 * u, 0)
        if #paws > 0 then
            local sum = Vector3.zero
            for _, position in paws do
                sum += position
            end
            ground = sum / #paws
        end
        local stomp = neon(Vector3.new(0.04 * u, 0.5 * u, 0.5 * u), CFrame.new(ground + Vector3.new(0, 0.03 * u, 0)) * CFrame.Angles(0, 0, math.pi / 2), colors.Orange)
        stomp.Shape = Enum.PartType.Cylinder
        stomp.Transparency = 0.4
        TweenService:Create(stomp, TweenInfo.new(0.8, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
            Size = Vector3.new(0.02 * u, 3.6 * u, 3.6 * u),
            Transparency = 1,
        }):Play()

        local light = Instance.new("PointLight")
        light.Color = colors.Gold
        light.Range = 12 * u
        light.Brightness = 2.2
        light.Parent = neon(Vector3.one * 0.05, CFrame.new(mouth), colors.Gold)
        TweenService:Create(light, TweenInfo.new(1.1), { Brightness = 0 }):Play()
        if rig.burst then
            rig.burst:Emit(25)
        end
    end

    local blastWarned = {} -- [petId] = true once its special has failed and been reported

    -- Heaven Quake (the Heavenbreaker Ape): its fists land and a gold ring of force runs out over the ground, chips of light kicked up behind it.
    function Blasts.HeavenQuake(rig, fx)
        local colors, u, neon = rig.profile.Colors, rig.unit, fx.neon
        local ground = rig.rootPart.Position - Vector3.new(0, rig.profile.Sole * u, 0)
        local ring = neon(Vector3.new(0.12 * u, 1, 1), CFrame.new(ground) * CFrame.Angles(0, 0, math.rad(90)), colors.Gold)
        ring.Shape = Enum.PartType.Cylinder
        ring.Transparency = 0.2
        TweenService:Create(ring, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
            Size = Vector3.new(0.04 * u, 9 * u, 9 * u), Transparency = 1, Color = colors.Sun,
        }):Play()
        for i = 1, 10 do
            local a = i / 10 * math.pi * 2
            local chip = neon(Vector3.one * 0.18 * u, CFrame.new(ground + Vector3.new(math.cos(a), 0.2, math.sin(a)) * u), colors.Orange)
            TweenService:Create(chip, TweenInfo.new(0.7, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
                CFrame = CFrame.new(ground + Vector3.new(math.cos(a) * 3, 1.4 + (i % 3) * 0.4, math.sin(a) * 3) * u) * CFrame.Angles(a, a, 0),
                Size = Vector3.one * 0.05 * u, Transparency = 1,
            }):Play()
        end
    end

    -- Rootwake (the Worldroot Colossus): its fists strike the earth and green shoots spring up in a ring round it, open, and fade.
    function Blasts.Rootwake(rig, fx)
        local colors, u, neon = rig.profile.Colors, rig.unit, fx.neon
        local ground = rig.rootPart.Position - Vector3.new(0, rig.profile.Sole * u, 0)
        for i = 1, 12 do
            local a = i / 12 * math.pi * 2
            local at = ground + Vector3.new(math.cos(a), 0, math.sin(a)) * (2 + (i % 2) * 0.6) * u
            task.delay(i * 0.03, function()
                local shoot = neon(Vector3.new(0.12 * u, 0.05 * u, 0.12 * u), CFrame.new(at), colors.Orange)
                TweenService:Create(shoot, TweenInfo.new(0.35, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {
                    Size = Vector3.new(0.12 * u, 1.3 * u, 0.12 * u), CFrame = CFrame.new(at + Vector3.new(0, 0.65 * u, 0)),
                }):Play()
                local leaf = neon(Vector3.one * 0.08 * u, CFrame.new(at), colors.Gold)
                TweenService:Create(leaf, TweenInfo.new(0.9, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
                    CFrame = CFrame.new(at + Vector3.new(0, 1.6 * u, 0)) * CFrame.Angles(0, a, math.rad(45)), Size = Vector3.new(0.4, 0.05, 0.25) * u,
                    Transparency = 1,
                }):Play()
                task.delay(0.45, function()
                    TweenService:Create(shoot, TweenInfo.new(0.5), { Transparency = 1, Size = Vector3.new(0.05, 1.3, 0.05) * u }):Play()
                end)
            end)
        end
    end

    -- Prism Bloom (the Prismatic Phoenix): with its wings swept wide, seven feathers of light in the colours of the spectrum open round it like a
    -- fan, turn once, and scatter.
    function Blasts.PrismBloom(rig, fx)
        local u, neon = rig.unit, fx.neon
        local at = (rig.parts.Body or rig.rootPart).Position
        local facing = fx.facing
        local hues = { "ff5061", "ffa227", "ffe538", "7ced7c", "38e1ff", "6190ff", "c46cff" }
        for i, hex in hues do
            local a = math.rad(-90 + (i - 1) * 30)
            local dir = facing:VectorToWorldSpace(Vector3.new(math.sin(a), math.cos(a), 0.4))
            local feather = neon(Vector3.new(0.12, 0.7, 0.05) * u, CFrame.lookAt(at, at + dir) * CFrame.Angles(math.rad(90), 0, 0), Color3.fromHex(hex))
            feather.Transparency = 0.15
            TweenService:Create(feather, TweenInfo.new(0.45, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {
                CFrame = CFrame.lookAt(at + dir * 1.6 * u, at + dir * 3 * u) * CFrame.Angles(math.rad(90), 0, 0), Size = Vector3.new(0.18, 1.2, 0.05) * u,
            }):Play()
            task.delay(0.6, function()
                TweenService:Create(feather, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
                    CFrame = CFrame.lookAt(at + dir * 3.4 * u, at + dir * 5 * u) * CFrame.Angles(math.rad(90), math.rad(180), 0), Transparency = 1,
                }):Play()
            end)
        end
    end

    -- Clockstrike (the Eternal Clockwork Dragon): a dial of gold opens behind it, twelve hour marks round its rim; the hand sweeps once round
    -- and every mark flashes as it passes, then the dial fades.
    function Blasts.Clockstrike(rig, fx)
        local colors, u, neon = rig.profile.Colors, rig.unit, fx.neon
        local centre = (rig.parts.Body or rig.rootPart).CFrame.Position + fx.facing:VectorToWorldSpace(Vector3.new(0, 1.2, 1.2)) * u
        local dial = fx.facing + centre
        local marks = {}
        for i = 1, 12 do
            local a = i / 12 * math.pi * 2
            local mark = neon(Vector3.new(0.08, 0.35, 0.05) * u, dial * CFrame.Angles(0, 0, a) * CFrame.new(0, 1.6 * u, 0), colors.Gold)
            mark.Transparency = 0.4
            marks[i] = mark
        end
        local hand = neon(Vector3.new(0.07, 1.5, 0.05) * u, dial * CFrame.new(0, 0.75 * u, 0), colors.Sun)
        for step = 1, 12 do
            task.delay(step * 0.06, function()
                local a = step / 12 * math.pi * 2
                hand.CFrame = dial * CFrame.Angles(0, 0, a) * CFrame.new(0, 0.75 * u, 0)
                local mark = marks[step]
                mark.Transparency = 0
                mark.Color = colors.Orange
                TweenService:Create(mark, TweenInfo.new(0.5), { Color = colors.Gold, Transparency = 0.3 }):Play()
            end)
        end
        task.delay(0.85, function()
            for _, piece in { hand, table.unpack(marks) } do
                TweenService:Create(piece, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1 }):Play()
            end
        end)
    end

    -- Swallowed Dream (the Thousand-Year Dream Eater): pale motes drift in toward its open mouth from all round, and it closes on them in a
    -- soft flash.
    function Blasts.SwallowedDream(rig, fx)
        local colors, u, neon = rig.profile.Colors, rig.unit, fx.neon
        local mouth = (rig.parts.Head or rig.rootPart).Position
        for i = 1, 14 do
            local a = i / 14 * math.pi * 2
            local from = mouth + Vector3.new(math.cos(a) * 3, math.sin(a * 2) * 1.2 + 0.4, math.sin(a) * 3) * u
            local mote = neon(Vector3.one * 0.14 * u, CFrame.new(from), if i % 2 == 0 then colors.Orange else colors.Gold)
            mote.Shape = Enum.PartType.Ball
            TweenService:Create(mote, TweenInfo.new(0.7 + (i % 3) * 0.08, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
                CFrame = CFrame.new(mouth), Size = Vector3.one * 0.04 * u, Transparency = 0.6,
            }):Play()
        end
        task.delay(0.95, function()
            local flash = neon(Vector3.one * 0.3 * u, CFrame.new(mouth), colors.Sun)
            flash.Shape = Enum.PartType.Ball
            TweenService:Create(flash, TweenInfo.new(0.4, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.one * 1.4 * u, Transparency = 1 }):Play()
        end)
    end

    -- Devour the Stars (the Eclipse Dreadwing): a black eclipse opens above its back, between the raised wings, ringed by a violet corona;
    -- motes of starlight spiral in from all round and it swallows them, swells, then collapses into one dark violet ring. (burst's folder
    -- clears it all by 2 s.)
    function Blasts.DevourStars(rig, fx)
        local colors, u, neon = rig.profile.Colors, rig.unit, fx.neon
        local body = rig.parts.Body or rig.rootPart
        local at = body.Position + Vector3.new(0, 1.3 * u, 0)
        local sun = neon(Vector3.one * 0.05 * u, CFrame.new(at), Color3.new(0, 0, 0))
        sun.Shape = Enum.PartType.Ball
        sun.Material = Enum.Material.SmoothPlastic
        local corona = neon(Vector3.one * 0.06 * u, CFrame.new(at), colors.Orange)
        corona.Shape = Enum.PartType.Ball
        corona.Transparency = 0.55
        local grow = TweenInfo.new(0.5, Enum.EasingStyle.Back, Enum.EasingDirection.Out)
        TweenService:Create(sun, grow, { Size = Vector3.one * 0.55 * u }):Play()
        TweenService:Create(corona, grow, { Size = Vector3.one * 0.75 * u }):Play()
        for i = 1, 16 do
            local a = i / 16 * math.pi * 2
            local from = at + Vector3.new(math.cos(a) * 3.2, math.sin(a * 3) * 1 - 0.4, math.sin(a) * 3.2) * u
            local star = neon(Vector3.one * 0.12 * u, CFrame.new(from), if i % 3 == 0 then colors.Sun else colors.Gold)
            star.Shape = Enum.PartType.Ball
            task.delay(0.2 + 0.03 * i, function()
                TweenService:Create(star, TweenInfo.new(0.75, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
                    CFrame = CFrame.new(at), Size = Vector3.one * 0.03 * u, Transparency = 0.5,
                }):Play()
            end)
        end
        task.delay(1.0, function() -- fed, it swells
            local swell = TweenInfo.new(0.25, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
            TweenService:Create(sun, swell, { Size = Vector3.one * 0.8 * u }):Play()
            TweenService:Create(corona, swell, { Size = Vector3.one * 1.1 * u, Transparency = 0.35 }):Play()
        end)
        task.delay(1.25, function() -- and collapses into the ring
            local shut = TweenInfo.new(0.2, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
            TweenService:Create(sun, shut, { Size = Vector3.one * 0.02 * u }):Play()
            TweenService:Create(corona, shut, { Size = Vector3.one * 0.02 * u, Transparency = 1 }):Play()
            local ring = neon(Vector3.new(0.05 * u, 0.6 * u, 0.6 * u), CFrame.new(at) * CFrame.Angles(0, 0, math.rad(90)), colors.Orange)
            ring.Shape = Enum.PartType.Cylinder
            ring.Transparency = 0.3
            local hole = Instance.new("SpecialMesh")
            hole.MeshType = Enum.MeshType.Cylinder
            hole.Parent = ring
            TweenService:Create(ring, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
                Size = Vector3.new(0.02 * u, 5 * u, 5 * u), Transparency = 1,
            }):Play()
        end)
    end

    -- Eternal Frost (Crysalith): with its head and antlers raised, a ring of frost spreads over the ground round it and six shards of ice rise,
    -- glint, and melt back into the air.
    function Blasts.EternalFrost(rig, fx)
        local colors, u, neon = rig.profile.Colors, rig.unit, fx.neon
        local body = rig.parts.Body or rig.rootPart
        local ground = body.Position - Vector3.new(0, (rig.profile.Sole or 2) * u * 0.95, 0)
        local frost = neon(Vector3.new(0.04 * u, 0.8 * u, 0.8 * u), CFrame.new(ground) * CFrame.Angles(0, 0, math.rad(90)), colors.Sun)
        frost.Shape = Enum.PartType.Cylinder
        frost.Transparency = 0.25
        TweenService:Create(frost, TweenInfo.new(0.9, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
            Size = Vector3.new(0.02 * u, 6 * u, 6 * u), Transparency = 1,
        }):Play()
        for i = 1, 6 do
            local a = i / 6 * math.pi * 2 + 0.3
            local at = ground + Vector3.new(math.cos(a) * 1.8, 0, math.sin(a) * 1.8) * u
            task.delay(0.08 * i, function()
                local shard = neon(Vector3.new(0.18, 0.05, 0.18) * u, CFrame.new(at) * CFrame.Angles(0, a, math.rad(8)), colors.Gold)
                shard.Transparency = 0.2
                TweenService:Create(shard, TweenInfo.new(0.35, Enum.EasingStyle.Back, Enum.EasingDirection.Out), {
                    Size = Vector3.new(0.22, 1.1, 0.22) * u, CFrame = CFrame.new(at + Vector3.new(0, 0.55 * u, 0)) * CFrame.Angles(0, a, math.rad(8)),
                }):Play()
                task.delay(0.7, function()
                    TweenService:Create(shard, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
                        Transparency = 1, Size = Vector3.new(0.05, 1.4, 0.05) * u,
                    }):Play()
                end)
            end)
        end
    end

    -- Full Moon (the Nine-Tail Moonfox): its tails fan wide (MoonfoxMotion) and a light leaves every tail tip; the nine meet above
    -- its head and swell into a full moon, which flares once, rings the air with pale light and fades.
    function Blasts.FullMoon(rig, fx)
        local colors, u, neon = rig.profile.Colors, rig.unit, fx.neon
        local headBone = rig.points.Head -- a skinned rig's head is a bone
        local headAt = if rig.parts.Head then rig.parts.Head.Position elseif headBone then headBone.TransformedWorldCFrame.Position else rig.rootPart.Position
        local above = headAt + Vector3.new(0, 2.2 * u, 0)
        for i = 1, 9 do
            local tail, tipBone = rig.parts["Tail" .. i], rig.points["Tail" .. i .. "_Tip"]
            if tail or tipBone then
                local tip = if tipBone then tipBone.TransformedWorldCFrame.Position else (tail.CFrame * CFrame.new(0, tail.Size.Y / 2, 0)).Position
                task.delay(0.04 * i, function()
                    local mote = neon(Vector3.one * 0.16 * u, CFrame.new(tip), colors.Gold)
                    mote.Shape = Enum.PartType.Ball
                    TweenService:Create(mote, TweenInfo.new(0.55, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
                        CFrame = CFrame.new(above), Size = Vector3.one * 0.08 * u, Color = colors.Sun,
                    }):Play()
                end)
            end
        end
        task.delay(0.62, function()
            local moon = neon(Vector3.one * 0.2 * u, CFrame.new(above), colors.Sun)
            moon.Shape = Enum.PartType.Ball
            moon.Transparency = 0.1
            TweenService:Create(moon, TweenInfo.new(0.35, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Size = Vector3.one * 1.1 * u }):Play()
            task.delay(0.55, function()
                TweenService:Create(moon, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.In), {
                    Size = Vector3.one * 1.5 * u, Transparency = 1, Color = colors.Gold,
                }):Play()
            end)
            local light = Instance.new("PointLight")
            light.Color = colors.Gold
            light.Range = 9 * u
            light.Brightness = 3
            light.Shadows = false
            light.Parent = moon
            TweenService:Create(light, TweenInfo.new(1.05, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Brightness = 0 }):Play()
            -- a thin ring of moonlight widening round it, level with the moon
            local ring = neon(Vector3.new(0.05 * u, 0.6 * u, 0.6 * u), CFrame.new(above) * CFrame.Angles(0, 0, math.rad(90)), colors.Ivory)
            ring.Shape = Enum.PartType.Cylinder
            ring.Transparency = 0.35
            local hole = Instance.new("SpecialMesh") -- (a flat disc that thins as it widens reads as a ring)
            hole.MeshType = Enum.MeshType.Cylinder
            hole.Parent = ring
            TweenService:Create(ring, TweenInfo.new(0.8, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
                Size = Vector3.new(0.02 * u, 4.2 * u, 4.2 * u), Transparency = 1,
            }):Play()
        end)
    end


    return { Blasts = Blasts, blastWarned = blastWarned, guardOwnerCharacter = guardOwnerCharacter, leopardGroundAt = leopardGroundAt }
end
