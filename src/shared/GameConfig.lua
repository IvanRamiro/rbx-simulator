
local GameConfig = {
    GameName = "Qi Aura Simulator",

    StartingQi = 0,

    -- Active training
    TrainingQiReward = 1, -- Qi awarded per accepted training action (server-side only)
    TrainingCooldown = 1, -- Seconds a player must wait between training actions
    TrainingKeybind = Enum.KeyCode.E, -- Keyboard shortcut for the Train button

    MaxEquippedPets = 3,

    StartingRank = "Mortal",
}

return GameConfig
