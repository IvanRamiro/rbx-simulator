-- ThunderclawDrake: its animation and its profile (PetRig)
-- (moved out of PetRig.lua on 2026-11-24 with its code unchanged: the modules in this folder are loaded by PetRig/init.lua with its shared helpers in K)
return function(K)
    local PetRig, Debris, Players, TweenService, SPARKLE, tweenAfter, pose, smoothstep, Blasts, dropToGround, leopardGroundAt = K.PetRig, K.Debris, K.Players, K.TweenService, K.SPARKLE, K.tweenAfter, K.pose, K.smoothstep, K.Blasts, K.dropToGround, K.leopardGroundAt


    -- ---------- The Thunderclaw Drake: all of it in one block, so its locals are freed at its end (the main chunk sits at Luau's limit of 200 locals) ----------
    do
        -- The Thunderclaw Drake (skinned): a storm wyvern, a dragon that is a living lightning conductor. Its wings are its arms: on the ground it prowls on
        -- their wrists, its chest low and its head held high on its S of a neck, its hands folded back along its flanks with their glowing spurs above its
        -- back; an arc crackles between the copper lightning rods of its horns. Now and then it mantles (opens its folded hands part way) and a crackle
        -- leaps between its spurs, or it turns its head to watch you. It walks in diagonal pairs, a wrist with the opposite foot, its iron hooks striking
        -- sparks. To fly it lifts its wrists clear, opens its wings and beats them, its legs tucked. Its special, Called Down: it rears onto its hind legs,
        -- wings flung open, head to the sky; a bolt comes down onto its horns and it glows white-hot; it slams down onto its wrists, hands flung up over it,
        -- and the bolt bursts out of it along the ground (Blasts.CalledDown).
        local TW = {
            FAR = 110, -- studs from the camera past which nobody can see it fidget: its bones rest
            SOLE = 0.6151, -- metres from the middle of its box down to its feet (thunderclaw_drake.py)
            LID_HINGE = { L = Vector3.new(0.7134, -0.2711, -0.6462), R = Vector3.new(0.7134, 0.2711, 0.6462) }, -- both lids of an eye turn on this line
            BLINK_UPPER = math.rad(40),
            BLINK_LOWER = math.rad(16),
            HOVER = 0.3, -- metres it rises taking to the wing (thunderclaw_drake.py's HOVER: its tucked talons clear the ground all the way up)
            BEAT_IN = 0.85, -- its wings start to beat only once they are open, this far into its rise (thunderclaw_drake.py's BEAT_IN: sooner, the
            -- downstroke cut into its flank)
            STEP_RATE = 4.5, -- its walk, radians of its cycle a second standing to a slow prowl, and more at a run
            STEP_RUN = 4,
            -- where its glowing points are at rest, metres in its own axes (thunderclaw_drake.py), and the bone heads that carry them
            HEAD_AT = Vector3.new(0, 0.99, -0.336),
            ARC_AT = Vector3.new(0.0031, 1.228, -0.172),
            HORN_AT = { L = Vector3.new(-0.078, 1.192, -0.164), R = Vector3.new(0.078, 1.192, -0.164) },
            WRIST_AT = { L = Vector3.new(-0.45, 0.96, -0.15), R = Vector3.new(0.45, 0.96, -0.15) },
            HOOK_AT = { L = Vector3.new(-0.4941, 0.9753, -0.2156), R = Vector3.new(0.4941, 0.9753, -0.2156) },
            SPUR_AT = {
                L = { Vector3.new(-0.9046, 1.179, -0.0479), Vector3.new(-0.9793, 0.8928, 0.2301), Vector3.new(-0.7373, 0.6375, 0.4812) },
                R = { Vector3.new(0.9046, 1.179, -0.0479), Vector3.new(0.9793, 0.8928, 0.2301), Vector3.new(0.7373, 0.6375, 0.4812) },
            },
            -- its stances, solved in Blender (thunderclaw_drake.py's pose_tables: feet and wrists placed, wings folded) and checked there in every one and
            -- along every slerp the game makes between them (membrane against body, legs, tail and head; wing against wing; limb against limb; feet,
            -- talons and wrists on the ground): turns x, y, z, then a move in metres. A folded wing never goes straight to an open one: it lifts clear
            -- first (LIFT), then opens.
            PROWL = {
                Chest = { 0.05, 0, 0 }, FootL = { -0.1222, 0, 0 }, FootR = { -0.1222, 0, 0 }, Head = { 0.02, 0, 0 }, Hips = { -0.55, 0, 0, 0, -0.03, 0 },
                LegL1 = { 0.6722, 0, 0 }, LegL2 = { -0.1529, 0, 0 }, LegL3 = { 0.1529, 0, 0 }, LegR1 = { 0.6722, 0, 0 }, LegR2 = { -0.1529, 0, 0 },
                LegR3 = { 0.1529, 0, 0 }, Neck1 = { 0.32, 0, 0 }, Neck2 = { 0.2, 0, 0 }, Tail1 = { 0.26, 0, 0 }, Tail2 = { 0.12, 0, 0 }, Tail3 = { 0.04, 0, 0 },
                WingL1 = { -0.4715, -1.0172, 0.9886 }, WingL2 = { -0.1649, -0.1862, -0.1086 }, WingL3 = { 0.8366, -0.2634, -1.3873 },
                WingLF1 = { 0.2826, 0.7461, -1.1865 }, WingLF2 = { -0.2065, 0.8901, -1.183 }, WingLF3 = { -0.8079, 0.8102, -0.9276 },
                WingR1 = { -0.4715, 1.0172, -0.9886 }, WingR2 = { -0.1649, 0.1862, 0.1086 }, WingR3 = { 1.9964, 0.1401, -2.0158 },
                WingRF1 = { 0.0249, -0.3555, -2.0932 }, WingRF2 = { 0.356, -0.1851, -1.646 }, WingRF3 = { 0.7317, -0.0382, -1.4007 },
            },
            LIFT = {
                Chest = { 0.03, 0, 0 }, FootL = { -0.0546, 0, 0 }, FootR = { -0.0546, 0, 0 }, Hips = { -0.3, 0, 0, 0, -0.01, 0 }, LegL1 = { 0.3546, 0, 0 },
                LegL2 = { -0.0577, 0, 0 }, LegL3 = { 0.0577, 0, 0 }, LegR1 = { 0.3546, 0, 0 }, LegR2 = { -0.0577, 0, 0 }, LegR3 = { 0.0577, 0, 0 },
                Neck1 = { 0.18, 0, 0 }, Neck2 = { 0.12, 0, 0 }, Tail1 = { 0.12, 0, 0 }, Tail2 = { 0.05, 0, 0 }, WingL1 = { -1.0356, 0.1791, 0.6779 },
                WingL2 = { -0.5828, -0.4787, -0.4352 }, WingL3 = { 1.2293, -0.6101, -0.5634 }, WingLF1 = { -0.4518, 1.2078, 0.0382 },
                WingLF2 = { -0.6032, 0.8858, 0.0827 }, WingLF3 = { -0.9049, 0.7685, 0.0829 }, WingR1 = { -1.0356, -0.1791, -0.6779 },
                WingR2 = { -0.5828, 0.4787, 0.4352 }, WingR3 = { -1.1801, -2.8489, 0.4289 }, WingRF1 = { 0.3392, 0.153, -2.6518 },
                WingRF2 = { 0.5806, -0.0727, -2.5732 }, WingRF3 = { 0.8082, -0.0145, -2.3402 },
            },
            FLY = {
                FootL = { -0.55, 0, 0 }, FootR = { -0.55, 0, 0 }, Head = { 0.44, 0, 0 }, Hips = { -0.32, 0, 0 }, LegL1 = { -1.05, 0, 0 }, LegL2 = { 1, 0, 0 },
                LegL3 = { -0.55, 0, 0 }, LegR1 = { -1.05, 0, 0 }, LegR2 = { 1, 0, 0 }, LegR3 = { -0.55, 0, 0 }, Neck1 = { -0.28, 0, 0 }, Neck2 = { -0.08, 0, 0 },
                Neck3 = { 0.12, 0, 0 }, Tail1 = { -0.1, 0, 0 }, Tail2 = { -0.04, 0, 0 }, Tail3 = { 0.02, 0, 0 }, Tail4 = { 0.03, 0, 0 },
            },
            BEAT_UP = {
                FootL = { -0.55, 0, 0 }, FootR = { -0.55, 0, 0 }, Head = { 0.44, 0, 0 }, Hips = { -0.32, 0, 0 }, LegL1 = { -1.05, 0, 0 }, LegL2 = { 1, 0, 0 },
                LegL3 = { -0.55, 0, 0 }, LegR1 = { -1.05, 0, 0 }, LegR2 = { 1, 0, 0 }, LegR3 = { -0.55, 0, 0 }, Neck1 = { -0.28, 0, 0 }, Neck2 = { -0.08, 0, 0 },
                Neck3 = { 0.12, 0, 0 }, Tail1 = { -0.1, 0, 0 }, Tail2 = { -0.04, 0, 0 }, Tail3 = { 0.02, 0, 0 }, Tail4 = { 0.03, 0, 0 },
                WingL1 = { 0, -0.08, -0.38 }, WingR1 = { 0, 0.08, 0.38 },
            },
            BEAT_DOWN = {
                FootL = { -0.55, 0, 0 }, FootR = { -0.55, 0, 0 }, Head = { 0.44, 0, 0 }, Hips = { -0.32, 0, 0 }, LegL1 = { -1.05, 0, 0 }, LegL2 = { 1, 0, 0 },
                LegL3 = { -0.55, 0, 0 }, LegR1 = { -1.05, 0, 0 }, LegR2 = { 1, 0, 0 }, LegR3 = { -0.55, 0, 0 }, Neck1 = { -0.28, 0, 0 }, Neck2 = { -0.08, 0, 0 },
                Neck3 = { 0.12, 0, 0 }, Tail1 = { -0.1, 0, 0 }, Tail2 = { -0.04, 0, 0 }, Tail3 = { 0.02, 0, 0 }, Tail4 = { 0.03, 0, 0 }, WingL1 = { 0, 0.1, 0.6 },
                WingL3 = { 0, 0.25, 0 }, WingR1 = { 0, -0.1, -0.6 }, WingR3 = { 0, -0.25, 0 },
            },
            REAR = {
                Body = { 0.08, 0, 0 }, Chest = { 0.05, 0, 0 }, FootL = { 0.0691, 0, 0 }, FootR = { 0.0691, 0, 0 }, Head = { -0.07, 0, 0 },
                Hips = { 0.12, 0, 0, 0, 0.02, 0 }, LegL1 = { -0.1891, 0, 0 }, LegL2 = { 0.1359, 0, 0 }, LegL3 = { -0.1359, 0, 0 }, LegR1 = { -0.1891, 0, 0 },
                LegR2 = { 0.1359, 0, 0 }, LegR3 = { -0.1359, 0, 0 }, Neck1 = { 0.05, 0, 0 }, Neck2 = { 0.1, 0, 0 }, Neck3 = { 0.12, 0, 0 }, Tail1 = { -0.12, 0, 0 },
                Tail2 = { -0.06, 0, 0 }, WingL1 = { 0, 0.12, -0.32 }, WingLF1 = { 0, 0.12, 0 }, WingLF3 = { 0, -0.12, 0 }, WingR1 = { 0, -0.12, 0.32 },
                WingRF1 = { 0, -0.12, 0 }, WingRF3 = { 0, 0.12, 0 },
            },
            SLAM = {
                FootL = { -0.174, 0, 0 }, FootR = { -0.174, 0, 0 }, Head = { 0.08, 0, 0 }, Hips = { -0.6, 0, 0, 0, -0.05, 0 }, LegL1 = { 0.774, 0, 0 },
                LegL2 = { -0.2565, 0, 0 }, LegL3 = { 0.2565, 0, 0 }, LegR1 = { 0.774, 0, 0 }, LegR2 = { -0.2565, 0, 0 }, LegR3 = { 0.2565, 0, 0 },
                Neck1 = { 0.2, 0, 0 }, Neck2 = { 0.16, 0, 0 }, Neck3 = { 0.04, 0, 0 }, Tail1 = { 0.3, 0, 0 }, Tail2 = { 0.16, 0, 0 }, Tail3 = { 0.06, 0, 0 },
                WingL1 = { -0.4497, -0.9314, 0.8112 }, WingL2 = { -0.215, -0.2341, -0.1447 }, WingL3 = { 0.9028, -0.2029, -1.2604 },
                WingLF1 = { -0.6162, 0.6584, -0.4194 }, WingLF2 = { -0.7861, 0.57, -0.4313 }, WingLF3 = { -0.7962, 0.5665, -0.4334 },
                WingR1 = { -0.4497, 0.9314, -0.8112 }, WingR2 = { -0.215, 0.2341, 0.1447 }, WingR3 = { 2.033, 0.0027, -2.0118 },
                WingRF1 = { 0.7304, -0.2459, -2.0381 }, WingRF2 = { 0.8964, -0.2154, -1.89 }, WingRF3 = { 0.905, -0.2115, -1.8806 },
            },
            MANTLE = {
                Chest = { 0.05, 0, 0 }, FootL = { -0.1222, 0, 0 }, FootR = { -0.1222, 0, 0 }, Head = { 0.02, 0, 0 }, Hips = { -0.55, 0, 0, 0, -0.03, 0 },
                LegL1 = { 0.6722, 0, 0 }, LegL2 = { -0.1529, 0, 0 }, LegL3 = { 0.1529, 0, 0 }, LegR1 = { 0.6722, 0, 0 }, LegR2 = { -0.1529, 0, 0 },
                LegR3 = { 0.1529, 0, 0 }, Neck1 = { 0.32, 0, 0 }, Neck2 = { 0.2, 0, 0 }, Tail1 = { 0.26, 0, 0 }, Tail2 = { 0.12, 0, 0 }, Tail3 = { 0.04, 0, 0 },
                WingL1 = { -0.4715, -1.0172, 0.9886 }, WingL2 = { -0.1649, -0.1862, -0.1086 }, WingL3 = { 0.8366, -0.2634, -1.3873 },
                WingLF1 = { -0.15, 0.7965, -1.0964 }, WingLF2 = { -0.5021, 0.9024, -1.1025 }, WingLF3 = { -0.8079, 0.8102, -0.9276 },
                WingR1 = { -0.4715, 1.0172, -0.9886 }, WingR2 = { -0.1649, 0.1862, 0.1086 }, WingR3 = { 1.9964, 0.1401, -2.0158 },
                WingRF1 = { 0.3465, -0.2855, -1.777 }, WingRF2 = { 0.5189, -0.0954, -1.4721 }, WingRF3 = { 0.7317, -0.0382, -1.4007 },
            },
            WALK = { -- eight keys round one cycle of its prowl (thunderclaw_drake.py's walk_pose at k/8 of it)
                {
                    Chest = { 0.05, 0, 0 }, FootL = { 0.0301, 0, 0 }, FootR = { -0.1894, 0, 0 }, Head = { 0.02, 0, 0 }, Hips = { -0.55, 0, 0, 0, -0.018, 0 },
                    LegL1 = { 0.5199, 0, 0 }, LegL2 = { -0.1199, 0, 0 }, LegL3 = { 0.1199, 0, 0 }, LegR1 = { 0.7394, 0, 0 }, LegR2 = { -0.0039, 0, 0 },
                    LegR3 = { 0.0039, 0, 0 }, Neck1 = { 0.32, 0, 0 }, Neck2 = { 0.2, 0, 0 }, Tail1 = { 0.26, 0.0387, 0 }, Tail2 = { 0.12, 0.0591, 0 },
                    Tail3 = { 0.04, 0.0518, 0 }, Tail4 = { 0, 0.0201, 0 }, WingL1 = { -0.4406, -1.2021, 0.8417 }, WingL2 = { -0.0037, -0.0046, -0.0022 },
                    WingL3 = { 0.8639, -0.252, -1.2772 }, WingLF1 = { 0.3583, 0.8291, -1.2267 }, WingLF2 = { -0.181, 0.9763, -1.156 },
                    WingLF3 = { -0.8312, 0.8707, -0.8325 }, WingR1 = { -0.4806, 0.9587, -1.1413 }, WingR2 = { -0.1976, 0.2179, 0.132 },
                    WingR3 = { 1.9513, 0.2717, -2.0484 }, WingRF1 = { 0.1154, -0.3591, -2.0083 }, WingRF2 = { 0.4301, -0.1633, -1.5685 },
                    WingRF3 = { 0.7933, 0.0095, -1.3374 },
                },
                {
                    Chest = { 0.05, 0, 0 }, FootL = { -0.1166, 0, 0.0025 }, FootR = { -0.1906, 0, 0.0021 }, Head = { 0.02, -0.0212, 0 },
                    Hips = { -0.55, 0, 0.0212, 0, -0.03, 0 }, LegL1 = { 0.6664, -0.0134, -0.0191 }, LegL2 = { -0.3799, 0, 0 }, LegL3 = { 0.3799, 0, 0 },
                    LegR1 = { 0.7405, -0.0147, -0.0177 }, LegR2 = { -0.0934, 0, 0 }, LegR3 = { 0.0934, 0, 0 }, Neck1 = { 0.32, 0, 0 }, Neck2 = { 0.2, 0, 0 },
                    Tail1 = { 0.26, 0.0598, 0 }, Tail2 = { 0.12, 0.049, 0 }, Tail3 = { 0.04, 0.0152, 0 }, Tail4 = { 0, -0.0258, 0 },
                    WingL1 = { -0.5048, -1.0999, 0.8293 }, WingL2 = { -0.0937, -0.1113, -0.0596 }, WingL3 = { 0.8778, -0.2268, -1.3105 },
                    WingLF1 = { 0.346, 0.7609, -1.2057 }, WingLF2 = { -0.1496, 0.9097, -1.1915 }, WingLF3 = { -0.765, 0.8294, -0.9176 },
                    WingR1 = { -0.5761, 0.8027, -1.0519 }, WingR2 = { -0.3838, 0.368, 0.2735 }, WingR3 = { 2.0009, 0.1812, -1.9879 },
                    WingRF1 = { 0.0312, -0.4175, -2.0935 }, WingRF2 = { 0.3668, -0.2437, -1.6254 }, WingRF3 = { 0.7408, -0.0853, -1.3603 },
                },
                {
                    Chest = { 0.05, 0, 0 }, FootL = { -0.2758, 0, 0.0038 }, FootR = { -0.1426, 0, 0.003 }, Head = { 0.02, -0.03, 0 },
                    Hips = { -0.55, 0, 0.03, 0, -0.042, 0 }, LegL1 = { 0.8255, -0.0231, -0.024 }, LegL2 = { -0.4843, 0, 0 }, LegL3 = { 0.4843, 0, 0 },
                    LegR1 = { 0.6924, -0.0196, -0.0261 }, LegR2 = { -0.2075, 0, 0 }, LegR3 = { 0.2075, 0, 0 }, Neck1 = { 0.32, 0, 0 }, Neck2 = { 0.2, 0, 0 },
                    Tail1 = { 0.26, 0.0459, 0 }, Tail2 = { 0.12, 0.0102, 0 }, Tail3 = { 0.04, -0.0303, 0 }, Tail4 = { 0, -0.0565, 0 },
                    WingL1 = { -0.5401, -0.9596, 0.9207 }, WingL2 = { -0.2209, -0.2395, -0.149 }, WingL3 = { 0.8598, -0.2328, -1.3869 },
                    WingLF1 = { 0.3016, 0.7021, -1.1816 }, WingLF2 = { -0.1643, 0.8493, -1.2093 }, WingLF3 = { -0.7482, 0.7859, -0.9804 },
                    WingR1 = { -0.57, 0.7743, -0.9329 }, WingR2 = { -0.425, 0.3948, 0.3063 }, WingR3 = { 2.0607, 0.0538, -1.9512 },
                    WingRF1 = { -0.0567, -0.4289, -2.1811 }, WingRF2 = { 0.296, -0.2813, -1.6991 }, WingRF3 = { 0.6832, -0.1465, -1.4126 },
                },
                {
                    Chest = { 0.05, 0, 0 }, FootL = { -0.2986, 0, 0.0025 }, FootR = { -0.0288, 0, 0.0021 }, Head = { 0.02, -0.0212, 0 },
                    Hips = { -0.55, 0, 0.0212, 0, -0.03, 0 }, LegL1 = { 0.8485, -0.0166, -0.0164 }, LegL2 = { -0.2976, 0, 0 }, LegL3 = { 0.2976, 0, 0 },
                    LegR1 = { 0.5787, -0.0117, -0.0199 }, LegR2 = { -0.1733, 0, 0 }, LegR3 = { 0.1733, 0, 0 }, Neck1 = { 0.32, 0, 0 }, Neck2 = { 0.2, 0, 0 },
                    Tail1 = { 0.26, 0.0051, 0 }, Tail2 = { 0.12, -0.0346, 0 }, Tail3 = { 0.04, -0.058, 0 }, Tail4 = { 0, -0.0542, 0 },
                    WingL1 = { -0.5269, -0.9323, 1.0527 }, WingL2 = { -0.2334, -0.2507, -0.1582 }, WingL3 = { 0.7928, -0.2971, -1.4694 },
                    WingLF1 = { 0.2186, 0.7152, -1.1682 }, WingLF2 = { -0.2556, 0.8564, -1.1865 }, WingLF3 = { -0.8385, 0.7835, -0.9572 },
                    WingR1 = { -0.5181, 0.9615, -0.8404 }, WingR2 = { -0.2336, 0.2509, 0.1583 }, WingR3 = { 2.0607, 0.0043, -1.9727 },
                    WingRF1 = { -0.0683, -0.3828, -2.1847 }, WingRF2 = { 0.2807, -0.2392, -1.7188 }, WingRF3 = { 0.6685, -0.1148, -1.4465 },
                },
                {
                    Chest = { 0.05, 0, 0 }, FootL = { -0.1894, 0, 0 }, FootR = { 0.0301, 0, 0 }, Head = { 0.02, 0, 0 }, Hips = { -0.55, 0, 0, 0, -0.018, 0 },
                    LegL1 = { 0.7394, 0, 0 }, LegL2 = { -0.0039, 0, 0 }, LegL3 = { 0.0039, 0, 0 }, LegR1 = { 0.5199, 0, 0 }, LegR2 = { -0.1199, 0, 0 },
                    LegR3 = { 0.1199, 0, 0 }, Neck1 = { 0.32, 0, 0 }, Neck2 = { 0.2, 0, 0 }, Tail1 = { 0.26, -0.0387, 0 }, Tail2 = { 0.12, -0.0591, 0 },
                    Tail3 = { 0.04, -0.0518, 0 }, Tail4 = { 0, -0.0201, 0 }, WingL1 = { -0.4806, -0.9587, 1.1413 }, WingL2 = { -0.1976, -0.2179, -0.132 },
                    WingL3 = { 0.7504, -0.343, -1.502 }, WingLF1 = { 0.1668, 0.7495, -1.1609 }, WingLF2 = { -0.3269, 0.8842, -1.1542 },
                    WingLF3 = { -0.9179, 0.7952, -0.9108 }, WingR1 = { -0.4406, 1.2021, -0.8417 }, WingR2 = { -0.0037, 0.0046, 0.0022 },
                    WingR3 = { 1.9987, 0.0384, -2.0494 }, WingRF1 = { -0.0156, -0.2647, -2.119 }, WingRF2 = { 0.3156, -0.1072, -1.6994 },
                    WingRF3 = { 0.698, 0.0144, -1.4788 },
                },
                {
                    Chest = { 0.05, 0, 0 }, FootL = { -0.1906, 0, -0.0021 }, FootR = { -0.1166, 0, -0.0025 }, Head = { 0.02, 0.0212, 0 },
                    Hips = { -0.55, 0, -0.0212, 0, -0.03, 0 }, LegL1 = { 0.7405, 0.0147, 0.0177 }, LegL2 = { -0.0934, 0, 0 }, LegL3 = { 0.0934, 0, 0 },
                    LegR1 = { 0.6664, 0.0134, 0.0191 }, LegR2 = { -0.3799, 0, 0 }, LegR3 = { 0.3799, 0, 0 }, Neck1 = { 0.32, 0, 0 }, Neck2 = { 0.2, 0, 0 },
                    Tail1 = { 0.26, -0.0598, 0 }, Tail2 = { 0.12, -0.049, 0 }, Tail3 = { 0.04, -0.0152, 0 }, Tail4 = { 0, 0.0258, 0 },
                    WingL1 = { -0.5761, -0.8027, 1.0519 }, WingL2 = { -0.3838, -0.368, -0.2735 }, WingL3 = { 0.8326, -0.2543, -1.4376 },
                    WingLF1 = { 0.2642, 0.6854, -1.1717 }, WingLF2 = { -0.1946, 0.831, -1.2102 }, WingLF3 = { -0.7689, 0.7709, -0.9952 },
                    WingR1 = { -0.5048, 1.0999, -0.8293 }, WingR2 = { -0.0937, 0.1113, 0.0596 }, WingR3 = { 2.0187, 0.0571, -2.0128 },
                    WingRF1 = { -0.0209, -0.3332, -2.1328 }, WingRF2 = { 0.3158, -0.1762, -1.6892 }, WingRF3 = { 0.6975, -0.0458, -1.4435 },
                },
                {
                    Chest = { 0.05, 0, 0 }, FootL = { -0.1426, 0, -0.003 }, FootR = { -0.2758, 0, -0.0038 }, Head = { 0.02, 0.03, 0 },
                    Hips = { -0.55, 0, -0.03, 0, -0.042, 0 }, LegL1 = { 0.6924, 0.0196, 0.0261 }, LegL2 = { -0.2075, 0, 0 }, LegL3 = { 0.2075, 0, 0 },
                    LegR1 = { 0.8255, 0.0231, 0.024 }, LegR2 = { -0.4843, 0, 0 }, LegR3 = { 0.4843, 0, 0 }, Neck1 = { 0.32, 0, 0 }, Neck2 = { 0.2, 0, 0 },
                    Tail1 = { 0.26, -0.0459, 0 }, Tail2 = { 0.12, -0.0102, 0 }, Tail3 = { 0.04, 0.0303, 0 }, Tail4 = { 0, 0.0565, 0 },
                    WingL1 = { -0.57, -0.7743, 0.9329 }, WingL2 = { -0.425, -0.3948, -0.3063 }, WingL3 = { 0.9187, -0.1694, -1.3335 },
                    WingLF1 = { 0.3626, 0.6605, -1.1816 }, WingLF2 = { -0.0835, 0.8119, -1.2363 }, WingLF3 = { -0.6528, 0.7645, -1.0302 },
                    WingR1 = { -0.5401, 0.9596, -0.9207 }, WingR2 = { -0.2209, 0.2395, 0.149 }, WingR3 = { 2.0158, 0.1275, -1.9878 },
                    WingRF1 = { 0.0027, -0.3969, -2.1188 }, WingRF2 = { 0.3414, -0.232, -1.6549 }, WingRF3 = { 0.7198, -0.085, -1.3914 },
                },
                {
                    Chest = { 0.05, 0, 0 }, FootL = { -0.0288, 0, -0.0021 }, FootR = { -0.2986, 0, -0.0025 }, Head = { 0.02, 0.0212, 0 },
                    Hips = { -0.55, 0, -0.0212, 0, -0.03, 0 }, LegL1 = { 0.5787, 0.0117, 0.0199 }, LegL2 = { -0.1733, 0, 0 }, LegL3 = { 0.1733, 0, 0 },
                    LegR1 = { 0.8485, 0.0166, 0.0164 }, LegR2 = { -0.2976, 0, 0 }, LegR3 = { 0.2976, 0, 0 }, Neck1 = { 0.32, 0, 0 }, Neck2 = { 0.2, 0, 0 },
                    Tail1 = { 0.26, -0.0051, 0 }, Tail2 = { 0.12, 0.0346, 0 }, Tail3 = { 0.04, 0.058, 0 }, Tail4 = { 0, 0.0542, 0 },
                    WingL1 = { -0.5181, -0.9615, 0.8404 }, WingL2 = { -0.2336, -0.2509, -0.1583 }, WingL3 = { 0.9273, -0.1682, -1.2787 },
                    WingLF1 = { 0.3897, 0.7028, -1.1996 }, WingLF2 = { -0.0744, 0.8561, -1.2273 }, WingLF3 = { -0.6658, 0.7981, -0.989 },
                    WingR1 = { -0.5269, 0.9323, -1.0527 }, WingR2 = { -0.2334, 0.2507, 0.1582 }, WingR3 = { 1.9754, 0.2259, -2.0162 },
                    WingRF1 = { 0.0722, -0.3913, -2.0514 }, WingRF2 = { 0.3976, -0.2065, -1.5967 }, WingRF3 = { 0.7659, -0.0406, -1.3478 },
                },
            },
            BONES = {
                "Hips", "Body", "Chest", "Neck1", "Neck2", "Neck3", "Head", "LidUL", "LidLL", "LidUR", "LidLR",
                "Tail1", "Tail2", "Tail3", "Tail4", "Tail5", "Tail6", "LegL1", "LegL2", "LegL3", "FootL", "LegR1", "LegR2", "LegR3", "FootR",
                "WingL1", "WingL2", "WingL3", "WingLF1", "WingLF2", "WingLF3", "WingR1", "WingR2", "WingR3", "WingRF1", "WingRF2", "WingRF3",
            },
            GOLD = Color3.fromRGB(255, 235, 100),
            WHITE = Color3.fromRGB(255, 250, 200),
            VIOLET = Color3.fromRGB(170, 150, 255),
        }
        TW.CARRIER = { Head = TW.HEAD_AT, WingL3 = TW.WRIST_AT.L, WingR3 = TW.WRIST_AT.R } -- the rest heads of the bones carrying them
        for _, tag in { "L", "R" } do
            for k = 1, 3 do
                TW.CARRIER["Wing" .. tag .. "F" .. k] = TW.WRIST_AT[tag] -- (every finger springs from its wrist)
            end
        end

        function TW.cf(a, u)
            if not a then
                return CFrame.identity
            end
            local move = if a[4] then CFrame.new(a[4] * u, a[5] * u, a[6] * u) else CFrame.identity
            return move * CFrame.Angles(a[1], a[2], a[3])
        end

        -- Where each glowing point sits on the bone that carries it, worked out once while it is still at rest (a skinned piece's own CFrame stays where
        -- it was bound, so the points ride on the bones).
        function TW.initTips(rig, s)
            s.tips = {}
            local function add(key, boneName, rest)
                local bone = rig.points[boneName]
                if not bone then
                    return
                end
                local head = bone.TransformedWorldCFrame
                local world = head.Position + rig.rootPart.CFrame:VectorToWorldSpace((rest - TW.CARRIER[boneName]) * rig.meters)
                s.tips[key] = { bone = bone, offset = head:PointToObjectSpace(world) }
            end
            add("Arc", "Head", TW.ARC_AT)
            for _, tag in { "L", "R" } do
                add("Horn" .. tag, "Head", TW.HORN_AT[tag])
                add("Hook" .. tag, "Wing" .. tag .. "3", TW.HOOK_AT[tag])
                for k = 1, 3 do
                    add("Spur" .. tag .. k, "Wing" .. tag .. "F" .. k, TW.SPUR_AT[tag][k])
                end
            end
            -- its glow: a light where the arc is, and the sparks its hooks strike, riding on their bones
            local arc = s.tips.Arc
            if arc then
                local at = Instance.new("Attachment")
                at.Name = "ArcLight"
                at.CFrame = CFrame.new(arc.offset)
                at.Parent = arc.bone
                local light = Instance.new("PointLight")
                light.Name = "PulseLight"
                light.Color = TW.GOLD
                light.Range = 5 * rig.unit
                light.Brightness = 1.2
                light.Shadows = false
                light.Parent = at
                rig.light = light
            end
            s.sparks = {}
            for _, tag in { "L", "R" } do
                local hook = s.tips["Hook" .. tag]
                if hook then
                    local at = Instance.new("Attachment")
                    at.Name = "HookSparks"
                    at.CFrame = CFrame.new(hook.offset)
                    at.Parent = hook.bone
                    local sparks = Instance.new("ParticleEmitter")
                    sparks.Name = "Sparks"
                    sparks.Texture = SPARKLE
                    sparks.Enabled = false
                    sparks.Lifetime = NumberRange.new(0.18, 0.35)
                    sparks.Speed = NumberRange.new(0.8 * rig.unit, 1.8 * rig.unit)
                    sparks.SpreadAngle = Vector2.new(70, 70)
                    sparks.Acceleration = Vector3.new(0, -4 * rig.unit, 0)
                    sparks.Size = NumberSequence.new(0.06 * rig.unit, 0)
                    sparks.Color = ColorSequence.new(TW.WHITE, TW.GOLD)
                    sparks.LightEmission = 1
                    sparks.LightInfluence = 0
                    sparks.Parent = at
                    s.sparks[tag] = sparks
                end
            end
        end

        function TW.tipAt(s, key)
            local tip = s.tips and s.tips[key]
            return if tip then tip.bone.TransformedWorldCFrame:PointToWorldSpace(tip.offset) else nil
        end

        -- a run of lightning from a to b: kinked sideways at every step, most in the middle
        function TW.jag(a, b, steps, amp)
            local dir = b - a
            local side = dir:Cross(Vector3.yAxis)
            if side.Magnitude < 1e-4 then
                side = dir:Cross(Vector3.xAxis)
            end
            side = side.Unit
            local other = dir.Unit:Cross(side)
            local points = { a }
            for i = 1, steps - 1 do
                local t = i / steps
                local reach = amp * math.sin(math.pi * t) ^ 0.5
                table.insert(points, a + dir * t + side * (math.random() * 2 - 1) * reach + other * (math.random() * 2 - 1) * reach * 0.6)
            end
            table.insert(points, b)
            return points
        end

        -- the run drawn in Neon, flashing on after `delay`, flickering, gone after `life`
        function TW.zap(parent, points, width, color, life, delay)
            for i = 1, #points - 1 do
                local a, b = points[i], points[i + 1]
                local length = (b - a).Magnitude
                if length > 1e-3 then
                    local part = Instance.new("Part")
                    part.Anchored = true
                    part.CanCollide = false
                    part.CanTouch = false
                    part.CanQuery = false
                    part.CastShadow = false
                    part.Material = Enum.Material.Neon
                    part.Color = color
                    part.Size = Vector3.new(width, width, length + width * 0.5)
                    part.CFrame = CFrame.lookAt((a + b) / 2, b)
                    part.Transparency = 1
                    part.Parent = parent
                    task.delay(delay, function()
                        if part.Parent then
                            part.Transparency = 0
                        end
                    end)
                    tweenAfter(delay + life * 0.35, part, TweenInfo.new(life * 0.65, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Transparency = 1 })
                    Debris:AddItem(part, delay + life + 0.1)
                end
            end
        end

        function TW.effectsFolder(rig)
            local folder = Instance.new("Folder")
            folder.Name = "PetSpecial"
            folder.Parent = rig.model.Parent or workspace
            Debris:AddItem(folder, 2)
            return folder
        end

        function TW.reduced()
            local player = Players.LocalPlayer
            return player ~= nil and player:GetAttribute("SettingReducedEffects") == true
        end

        -- a crackle leaping between two of its points
        function TW.crackle(rig, a, b)
            if not a or not b or TW.reduced() then
                return
            end
            local u = rig.unit
            local folder = TW.effectsFolder(rig)
            local steps = math.clamp(math.floor((b - a).Magnitude / (0.12 * u)) + 2, 3, 9)
            TW.zap(folder, TW.jag(a, b, steps, 0.06 * u), 0.025 * u, TW.WHITE, 0.16, 0)
            TW.zap(folder, TW.jag(a, b, steps, 0.08 * u), 0.012 * u, TW.GOLD, 0.12, 0.06)
        end

        -- Called Down, the bolt: out of the sky onto the arc between its horns, a white core in a gold sheath, two forks, a flash
        function TW.bolt(rig, s)
            local target = TW.tipAt(s, "Arc")
            if not target then
                return
            end
            local u = rig.unit
            local folder = TW.effectsFolder(rig)
            local from = target + Vector3.new((math.random() - 0.5) * 3 * u, 16 * u, (math.random() - 0.5) * 3 * u)
            local points = TW.jag(from, target, 11, 0.9 * u)
            TW.zap(folder, points, 0.09 * u, TW.GOLD, 0.35, 0)
            TW.zap(folder, points, 0.04 * u, Color3.new(1, 1, 1), 0.3, 0)
            if not TW.reduced() then
                for _, k in { 4, 7 } do
                    local fork = points[k] + Vector3.new((math.random() - 0.5) * 3 * u, -2.2 * u, (math.random() - 0.5) * 3 * u)
                    TW.zap(folder, TW.jag(points[k], fork, 5, 0.3 * u), 0.035 * u, TW.GOLD, 0.22, 0.03)
                end
                for _, tag in { "L", "R" } do -- and on into its horns
                    TW.zap(folder, TW.jag(target, TW.tipAt(s, "Horn" .. tag) or target, 3, 0.03 * u), 0.03 * u, Color3.new(1, 1, 1), 0.4, 0.02)
                end
            end
            local flash = Instance.new("Part")
            flash.Anchored = true
            flash.CanCollide = false
            flash.CanTouch = false
            flash.CanQuery = false
            flash.Transparency = 1
            flash.Size = Vector3.one * 0.05
            flash.CFrame = CFrame.new(target)
            flash.Parent = folder
            local light = Instance.new("PointLight")
            light.Color = TW.WHITE
            light.Range = 10 * u
            light.Brightness = 2.5 -- a flash, not the whole scene washed white (brighter and wider, it was: seen in Play)
            light.Shadows = false
            light.Parent = flash
            TweenService:Create(light, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Brightness = 0 }):Play()
        end

        local function animateThunderclawDrake(rig, s, moving, fly, nova)
            if not s.tips then
                TW.initTips(rig, s) -- at rest, before any pose
            end
            local camera = workspace.CurrentCamera
            if not camera or (camera.CFrame.Position - rig.rootPart.Position).Magnitude > TW.FAR then
                return
            end
            local m, u, t, dt = rig.motors, rig.meters, s.time, rig.deltaTime

            -- the special, Called Down: it lands if it is flying; rears (through LIFT, wings opening) to 0.24; holds, head to the sky, and the bolt comes
            -- down onto its horns (0.27); strikes down (through LIFT) to its wrists from 0.38, landing at 0.42 (Blasts.CalledDown); holds; settles by 0.95
            local progress = if rig.nova then (t - rig.nova.start) / PetRig.NOVA_TIME else 0
            local active = if rig.nova then 1 else 0
            s.air = (s.air or 0) + (fly * (1 - active) - (s.air or 0)) * math.min(1, dt * 2.5)
            local air = s.air
            local rise = smoothstep(0.02, 0.24, progress) * active
            local strike = smoothstep(0.38, 0.42, progress) * active
            local settle = smoothstep(0.7, 0.95, progress) * active
            local impact = if active == 1 and progress > 0.42 then math.exp(-(progress - 0.42) * 16) else 0
            if active == 1 and progress >= 0.27 and s.bolted ~= rig.nova.start then
                s.bolted = rig.nova.start
                TW.bolt(rig, s)
            end

            -- it stands on the ground, or keeps to its owner's height on the wing
            local drop = dropToGround(rig, s, t, u, air, TW.SOLE)

            -- idle business, when it is still: it mantles (opens its folded hands part way, a crackle leaping between its spurs), or watches you
            local still = (1 - moving) * (1 - smoothstep(0.05, 0.3, air)) * (1 - active)
            s.nextIdle = s.nextIdle or t + 5
            if t >= s.nextIdle and still > 0.9 then
                s.idleAt, s.idleKind = t, if math.random() < 0.55 then "mantle" else "watch"
                s.nextIdle = t + 7 + math.random() * 7
            end
            local idle = if s.idleAt then (t - s.idleAt) / 2.4 else 1
            local env = if idle < 1 then math.sin(math.pi * idle) else 0
            local mantle = (if s.idleKind == "mantle" then smoothstep(0, 1, env) else 0) * still
            if s.idleKind == "mantle" and idle >= 0.35 and s.crackled ~= s.idleAt then
                s.crackled = s.idleAt
                local tag = if math.random() < 0.5 then "L" else "R"
                local k = math.random(1, 2)
                TW.crackle(rig, TW.tipAt(s, "Spur" .. tag .. k), TW.tipAt(s, "Spur" .. tag .. (k + 1)))
            end
            local watch = if s.idleKind == "watch" then env else 0

            -- its walk: eight keys round a cycle, a wrist planting with the opposite foot; each hook strikes sparks as it plants
            local walking = moving * (1 - smoothstep(0.05, 0.3, air))
            local before = s.step or 0
            s.step = before + dt * (TW.STEP_RATE + TW.STEP_RUN * moving) * walking
            local cycle = (s.step / (2 * math.pi)) % 1 * 8
            local key = math.floor(cycle)
            local frac = cycle - key
            local keyA, keyB = TW.WALK[key + 1], TW.WALK[(key + 1) % 8 + 1]
            if walking > 0.4 and s.sparks then
                local was, now = (before / (2 * math.pi)) % 1, (s.step / (2 * math.pi)) % 1
                if now < was and s.sparks.L then -- the left wrist plants at the cycle's start
                    s.sparks.L:Emit(4)
                end
                if was < 0.5 and now >= 0.5 and s.sparks.R then -- the right, half a cycle on
                    s.sparks.R:Emit(4)
                end
            end

            -- on the wing: its wings beat once open; it rises off the ground as they open
            s.beat = (s.beat or 0) + dt * (4.6 + 1.4 * fly) * air
            local down = 0.5 - 0.5 * math.cos(s.beat) -- 0 at the top of the stroke, 1 at the bottom
            local beating = smoothstep(TW.BEAT_IN, 1, air)
            local hover = TW.HOVER * smoothstep(0.35, 0.9, air) + 0.025 * beating * (0.5 - down)

            -- its gaze: slow, a sentinel's; it settles on you and holds; and the tail's slow sway
            local toYou = rig.rootPart.CFrame:VectorToObjectSpace((camera.CFrame.Position - rig.rootPart.Position).Unit)
            s.nextGaze = s.nextGaze or 0
            if t >= s.nextGaze then
                s.nextGaze = t + 3 + math.random() * 4
                s.atYou = math.random() < 0.5
                s.gazeYaw, s.gazePitch = (math.random() - 0.5) * 1.2, (math.random() - 0.5) * 0.5
            end
            local calm = (1 - 0.6 * walking) * (1 - smoothstep(0.02, 0.1, progress) * active)
            local wantYaw = math.clamp((if s.atYou or watch > 0 then math.atan2(-toYou.X, -toYou.Z) else s.gazeYaw) * (1 + watch), -1, 1) * calm
            local wantPitch = math.clamp(if s.atYou or watch > 0 then toYou.Y * 0.8 else s.gazePitch, -0.5, 0.5) * calm
            s.yaw = (s.yaw or 0) + (wantYaw - (s.yaw or 0)) * math.min(1, dt * 2)
            s.pitch = (s.pitch or 0) + (wantPitch - (s.pitch or 0)) * math.min(1, dt * 2)
            local breath = math.sin(t * 1.25)

            for _, name in TW.BONES do
                if string.sub(name, 1, 3) ~= "Lid" then
                    -- on the ground: the prowl, stepping as it goes, mantling now and then
                    local ground = TW.cf(TW.PROWL[name], u):Lerp(TW.cf(keyA[name], u):Lerp(TW.cf(keyB[name], u), frac), walking)
                    ground = ground:Lerp(TW.cf(TW.MANTLE[name], u), mantle)
                    -- on the wing, and between: lifted clear (LIFT) first, then open
                    local wing = TW.cf(TW.FLY[name], u):Lerp(TW.cf(TW.BEAT_UP[name], u):Lerp(TW.cf(TW.BEAT_DOWN[name], u), down), beating)
                    local cf = if air < 0.5 then ground:Lerp(TW.cf(TW.LIFT[name], u), air * 2) else TW.cf(TW.LIFT[name], u):Lerp(wing, air * 2 - 1)
                    -- the special over all of it: up through LIFT to the rear, down through LIFT to the slam, and back
                    if active == 1 then
                        local lift, rear, slam = TW.cf(TW.LIFT[name], u), TW.cf(TW.REAR[name], u), TW.cf(TW.SLAM[name], u)
                        if strike > 0 then
                            cf = if strike < 0.5 then rear:Lerp(lift, strike * 2) else lift:Lerp(slam, strike * 2 - 1)
                            cf = cf:Lerp(ground, settle)
                        elseif rise > 0 then
                            cf = if rise < 0.5 then cf:Lerp(lift, rise * 2) else lift:Lerp(rear, rise * 2 - 1)
                        end
                    end
                    -- over the stance: its breath, its gaze, its tail's sway
                    if name == "Chest" then
                        cf *= CFrame.Angles(0.02 * breath * (1 - air), 0, 0)
                    elseif name == "Neck2" or name == "Neck3" then
                        cf *= CFrame.Angles(0.2 * s.pitch, 0.3 * s.yaw, 0)
                    elseif name == "Head" then
                        cf *= CFrame.Angles(0.3 * s.pitch, 0.35 * s.yaw, 0.1 * s.yaw)
                    elseif string.sub(name, 1, 4) == "Tail" then
                        local k = tonumber(string.sub(name, 5)) or 1
                        cf *= CFrame.Angles(0, (0.02 + 0.006 * k) * math.sin(t * 0.8 - 0.55 * k) * (1 - walking), 0)
                    end
                    if name == "Hips" then
                        cf = CFrame.new(0, (hover - 0.04 * impact) * u - drop, 0) * cf
                    end
                    pose(m[name], cf)
                end
            end

            -- the arc between its horns: crackling on and off; blazing in the special
            local arc = rig.parts.Arc
            if arc then
                s.nextFlicker = s.nextFlicker or 0
                if t >= s.nextFlicker then
                    s.nextFlicker = t + 0.04 + math.random() * 0.06
                    s.arcShow = if math.random() < 0.18 then 1 else math.random() * 0.55
                end
                arc.Transparency = if active == 1 and progress > 0.25 and progress < 0.75 then 0 else s.arcShow or 0
            end

            -- the eyes: a slow blink now and then; narrowed as the bolt strikes and as it slams down
            s.nextBlink = s.nextBlink or t + 3
            local blink = 0
            if t >= s.nextBlink then
                local a = (t - s.nextBlink) / 0.28
                if a >= 1 then
                    s.nextBlink = t + 3.5 + math.random() * 4
                else
                    blink = 1 - math.abs(2 * a - 1)
                end
            end
            local narrow = 0.45 * smoothstep(0.25, 0.3, progress) * (1 - smoothstep(0.6, 0.8, progress)) * active
            local close = math.max(blink, narrow)
            for _, side in { "L", "R" } do
                pose(m["LidU" .. side], CFrame.fromAxisAngle(TW.LID_HINGE[side], -TW.BLINK_UPPER * close))
                pose(m["LidL" .. side], CFrame.fromAxisAngle(TW.LID_HINGE[side], TW.BLINK_LOWER * close))
            end
        end

        -- It has slammed down onto its wrists (animateThunderclawDrake): the bolt it took bursts out of it along the ground, a ring of light racing out and
        -- lightning running out across the ground from where its hooks struck, sparks thrown up, a flash.
        function Blasts.CalledDown(rig, fx)
            local u, metre = rig.unit, rig.meters
            local s = rig.state
            local hooks = {}
            for _, tag in { "L", "R" } do
                local at = TW.tipAt(s, "Hook" .. tag)
                if at then
                    table.insert(hooks, at)
                end
            end
            local centre = if #hooks == 2 then (hooks[1] + hooks[2]) / 2 else rig.rootPart.Position
            local params = RaycastParams.new()
            params.FilterDescendantsInstances = { rig.model }
            local hit = workspace:Raycast(centre + Vector3.new(0, 1 * u, 0), Vector3.new(0, -12 * u, 0), params)
            local groundY = if hit then hit.Position.Y else centre.Y - 0.1 * metre
            local folder = TW.effectsFolder(rig)
            local reduced = TW.reduced()

            local ripple = fx.neon(Vector3.new(0.03 * u, 0.5 * u, 0.5 * u), CFrame.new(centre.X, groundY + 0.04 * u, centre.Z) * CFrame.Angles(0, 0, math.pi / 2), TW.GOLD)
            ripple.Shape = Enum.PartType.Cylinder
            ripple.Transparency = 0.3
            TweenService:Create(ripple, TweenInfo.new(0.5, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.new(0.02 * u, 5 * u, 5 * u), Transparency = 1 }):Play()

            local count = if reduced then 5 else 9
            for k = 1, count do
                local angle = (k - 1) / count * 2 * math.pi + (math.random() - 0.5) * 0.4
                local out = fx.facing:VectorToWorldSpace(Vector3.new(math.sin(angle), 0, -math.cos(angle)))
                local from = hooks[(k % math.max(#hooks, 1)) + 1] or centre
                local points = { Vector3.new(from.X, groundY + 0.05 * u, from.Z) }
                local reach = (1.4 + 0.8 * math.random()) * u
                for i = 1, 9 do
                    local p = from + out * reach * i / 9 + out:Cross(Vector3.yAxis) * (math.random() - 0.5) * 0.3 * u
                    local ground = leopardGroundAt(Vector3.new(p.X, groundY, p.Z), metre)
                    table.insert(points, if ground then ground + Vector3.new(0, 0.03 * u, 0) else Vector3.new(p.X, groundY + 0.05 * u, p.Z))
                end
                TW.zap(folder, points, 0.025 * u, TW.WHITE, 0.32, k * 0.012) -- thin and kinked: thicker, they read as pale bands, not lightning (seen in Play)
                TW.zap(folder, points, 0.05 * u, TW.GOLD, 0.26, k * 0.012)
            end

            if not reduced then
                local sparks = Instance.new("ParticleEmitter")
                sparks.Texture = SPARKLE
                sparks.Enabled = false
                sparks.Lifetime = NumberRange.new(0.3, 0.6)
                sparks.Speed = NumberRange.new(1.5 * u, 3.2 * u)
                sparks.SpreadAngle = Vector2.new(60, 60)
                sparks.Acceleration = Vector3.new(0, -5 * u, 0)
                sparks.Size = NumberSequence.new(0.09 * u, 0)
                sparks.Color = ColorSequence.new(TW.WHITE, TW.GOLD)
                sparks.LightEmission = 1
                sparks.LightInfluence = 0
                local holder = fx.neon(Vector3.one * 0.05, CFrame.new(centre.X, groundY + 0.1 * u, centre.Z) * CFrame.Angles(-math.pi / 2, 0, 0), TW.GOLD)
                holder.Transparency = 1
                sparks.Parent = holder
                sparks:Emit(30)
            end

            local light = Instance.new("PointLight")
            light.Color = TW.GOLD
            light.Range = 8 * u
            light.Brightness = 2
            light.Shadows = false
            local lamp = fx.neon(Vector3.one * 0.05, CFrame.new(centre.X, groundY + 0.5 * u, centre.Z), TW.GOLD)
            lamp.Transparency = 1
            light.Parent = lamp
            TweenService:Create(light, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Brightness = 0 }):Play()
        end

        PetRig.Profiles.ThunderclawDrake = {
            Skinned = true,
            Bones = TW.BONES,
            Points = { "Hips", "Head", "WingL3", "WingR3", "WingLF1", "WingLF2", "WingLF3", "WingRF1", "WingRF2", "WingRF3" },
            GlowColors = {
                ffe864 = Color3.fromRGB(255, 232, 100), -- the gold balls on its horns' and spurs' tips
                fffabe = Color3.fromRGB(255, 250, 190), -- the arc between its horns
                ffffff = Color3.fromRGB(255, 255, 255), -- the catch-lights in its eyes
            },
            Effects = {
                Blast = "CalledDown",
                Pulse = "Tips",
                NovaLight = 2,
            },
            Colors = {
                Gold = TW.GOLD,
                Amber = Color3.fromRGB(190, 104, 54),
                Orange = Color3.fromRGB(255, 190, 90),
                Sun = TW.WHITE,
                Ivory = Color3.fromRGB(236, 240, 255),
            },
            Animate = animateThunderclawDrake,
        }
    end
end
