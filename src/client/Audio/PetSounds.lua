-- Each animated pet's voice and the sound of its special (November 9, 2026, the owner's "do the 3": pets were silent). The
-- voice is a short call the pet gives now and then as it idles in the world, a take picked at random; the special sounds on
-- its climax, as its burst goes off (PetRig). Only Roblox's licensed library (Pro Sound Effects, the "ProSoundEffects"
-- uploads), each one checked to load in this place; volumes from each file's measured loudness, so pets sit level with each
-- other and under the player's own sounds. SoundCatalog takes these in as PetVoice_<PetId> and PetSpecial_<PetId>. Pets not
-- yet animated (still to be recreated) have none.
local PetSounds = {}

local VOICE_NEAR, VOICE_REACH = 12, 70       -- studs: full volume within, silent and skipped beyond
local SPECIAL_NEAR, SPECIAL_REACH = 25, 160

-- [PetId] = { Voice = { takes }, VoiceVolume, Pitch (its voice's, a take a little either side), VoiceLength (seconds, cut),
-- VoiceStart (seconds into each take, skipping a quiet lead-in), Special = id, SpecialVolume, SpecialLength (seconds, cut), SpecialStart }. Volumes set from each file's measured loudness in Play
-- (PlaybackLoudness, November 9, 2026): a pet's voice lands at about 24, its special at about 48, under the player's own
-- moves (a leap about 38, a dash about 59). Picks by kind: the closest real creature, or for spirits a magical tone; pets of
-- one family (the lions and dragons, the kirins) told apart by their pitch.
local DATA = {
    AquaWisp = { Voice = { "9120312739", "9120312834", "9120312968" }, VoiceVolume = 0.79, Pitch = 1.15, VoiceLength = 1.6, Special = "9114455244", SpecialVolume = 0.63, SpecialLength = 3 },
    AbyssAnomalocaris = { Voice = { "9113957245", "9113957592", "9113957437" }, VoiceVolume = 1.14, Special = "9120314649", SpecialVolume = 0.49, SpecialLength = 4 },
    AstralWhale = { Voice = { "9125927348", "9125927607" }, VoiceVolume = 0.16, Pitch = 0.72, VoiceLength = 1.8, VoiceStart = 0.6, Special = "9125927614", SpecialVolume = 0.22, SpecialLength = 3.5, SpecialStart = 0.8 }, -- (the library has no whale: a shakuhachi's long tones pitched down read as a humpback's song. Measured muted in Play, 2026-11-10: the takes open with up to 1.3 s of near-silence, skipped; from there they peak at 181 and 121, the song at 219)
    AzureSkyDragon = { Voice = { "9116291350", "9116292005", "9116292195" }, VoiceVolume = 0.41, Pitch = 0.85, Special = "9120727460", SpecialVolume = 0.41 },
    BonefireDragon = { Voice = { "9125840983", "9125841207", "9125841551" }, VoiceVolume = 0.58, Pitch = 0.9, Special = "9120575099", SpecialVolume = 0.46 },
    CelestialPearlDragon = { Voice = { "9116307261", "9116307522", "9116307242" }, VoiceVolume = 0.62, Pitch = 0.8, Special = "9120027969", SpecialVolume = 0.65 },
    CelestialSnowLeopard = { Voice = { "9116310839", "9116310847", "9116311071" }, VoiceVolume = 0.21, Pitch = 1.1, Special = "9114858583", SpecialVolume = 0.71 },
    CloudSheep = { Voice = { "9119066036", "9119066291", "9119065619" }, VoiceVolume = 0.28, Pitch = 1.05, Special = "9120743085", SpecialVolume = 1.78 },
    CometStag = { Voice = { "9113636057" }, VoiceVolume = 0.6, Pitch = 0.85, Special = "9114428748", SpecialVolume = 0.3, SpecialLength = 4 },
    CosmicJellyfish = { Voice = { "9120309350", "9120309685", "9120309792" }, VoiceVolume = 0.63, Pitch = 0.8, Special = "9113604994", SpecialVolume = 0.45 },
    CrystalBeetle = { Voice = { "9114595903", "9114596112", "9114596664" }, VoiceVolume = 1.22, Special = "9114592245", SpecialVolume = 4.36 },
    CrystalSnail = { Voice = { "9125892855", "9125892982", "9125892745" }, VoiceVolume = 1.53, Special = "9118762653", SpecialVolume = 6, SpecialLength = 4 },
    DawnPhoenix = { Voice = { "9114661938", "9114661950" }, VoiceVolume = 1.78, Special = "9114431819", SpecialVolume = 0.53, SpecialLength = 4 },
    DreadfangCerberus = { Voice = { "9113973520", "9113973521" }, VoiceVolume = 0.52, Special = "9114444008", SpecialVolume = 2.29 },
    DreamMoth = { Voice = { "9116383039", "9116383270" }, VoiceVolume = 6.86, Pitch = 0.85, Special = "9116380049", SpecialVolume = 10 },
    EclipseCat = { Voice = { "9113984339", "9113984510", "9113984650" }, VoiceVolume = 1.89, Special = "9125484367", SpecialVolume = 0.83 },
    EmberWyrm = { Voice = { "9117987278", "9117987286", "9117983605" }, VoiceVolume = 0.66, Pitch = 1.3, VoiceLength = 1.2, Special = "9117984812", SpecialVolume = 0.55, SpecialLength = 3 },
    FrostfangSerpent = { Voice = { "9119299847", "9119300024", "9119300025" }, VoiceVolume = 0.38, Special = "9114856117", SpecialVolume = 0.98 },
    GalaxyManta = { Voice = { "9120653665", "9120653868", "9120653862" }, VoiceVolume = 0.52, Special = "9125635430", SpecialVolume = 0.8 },
    GlacierPuff = { Voice = { "9120310416", "9120310477", "9120310104" }, VoiceVolume = 0.72, Special = "9125611419", SpecialVolume = 0.29 },
    GoldenKirin = { Voice = { "9113634710", "9113634765", "9113634890" }, VoiceVolume = 1.41, Special = "9114432358", SpecialVolume = 0.53, SpecialLength = 4 },
    GoldenManeLion = { Voice = { "9113971433", "9113971531", "9113973128" }, VoiceVolume = 0.46, Special = "9116300504", SpecialVolume = 0.42, SpecialLength = 4 },
    GravityImp = { Voice = { "9125475127", "9125475397", "9125475418" }, VoiceVolume = 1.8, Special = "9125881584", SpecialVolume = 1.78 },
    JadeAntlerDeer = { Voice = { "9114037159", "9114037278", "9114037338" }, VoiceVolume = 1.6, Special = "9120831925", SpecialVolume = 0.46 },
    JadeSpiritPanda = { Voice = { "9117345956", "9117351080" }, VoiceVolume = 2.53, Pitch = 0.75, Special = "9125643566", SpecialVolume = 0.41 },
    JadeWyrmTurtle = { Voice = { "9120829704", "9120829553" }, VoiceVolume = 0.1, Special = "9118185409", SpecialVolume = 0.41 },
    LanternWarden = { Voice = { "9116163066", "9116162481" }, VoiceVolume = 4.8, Special = "9125635650", SpecialVolume = 0.59 },
    LunarHopper = { Voice = { "9114684818", "9114684783", "9114684660" }, VoiceVolume = 0.6, Pitch = 1.15, VoiceLength = 1, Special = "9116395089", SpecialVolume = 5.3, SpecialLength = 2.5 },
    MagmaCub = { Voice = { "9116290233", "9116290245", "9116290197" }, VoiceVolume = 0.43, Pitch = 1.15, Special = "9126194761", SpecialVolume = 2 },
    MossGolem = { Voice = { "9118664610", "9118664620", "9118665020" }, VoiceVolume = 1, Special = "9118633669", SpecialVolume = 4.8 },
    MyceliumSprite = { Voice = { "9125409791", "9125409840" }, VoiceVolume = 1.23, Special = "9119448154", SpecialVolume = 4.8, SpecialLength = 4 },
    NebulaOwl = { Voice = { "9119439931", "9119440507", "9119440685" }, VoiceVolume = 0.94, Special = "9116409574", SpecialVolume = 0.96 },
    ObsidianGuardian = { Voice = { "9113559434", "9113559450", "9113559651" }, VoiceVolume = 0.11, Special = "9114619050", SpecialVolume = 6.86 },
    OriginSerpent = { Voice = { "9125467848", "9125467833", "9125470164" }, VoiceVolume = 0.18, Pitch = 1.15, VoiceLength = 1.6, Special = "9119628762", SpecialVolume = 0.23, SpecialLength = 2.2, SpecialStart = 0.5 }, -- (a loong's deep guttural growl, lifted a step above the Golden Mane Lion's; its special a phased whomp swelling as its helix climbs. Measured muted in Play, 2026-11-10: the growls peak at 118, 126 and 144 at pitch 1.15; the whomp opens with 0.6 s of near-silence, so from 0.5 s, peaking at 213)
    PrismArmadillo = { Voice = { "9117345347", "9117345953" }, VoiceVolume = 3.2, Pitch = 1.25, Special = "9116409128", SpecialVolume = 1.5 },
    RuneSphinx = { Voice = { "9125471073", "9125470306", "9125470318" }, VoiceVolume = 0.49, Pitch = 0.9, Special = "9126102843", SpecialVolume = 1.66 },
    SandPhantom = { Voice = { "9118058248", "9118058375", "9118057950" }, VoiceVolume = 2.57, Special = "9114159710", SpecialVolume = 0.81 },
    Shadowcoil = { Voice = { "9116431311" }, VoiceVolume = 1.71, VoiceLength = 2, Special = "9114343926", SpecialVolume = 2.67, SpecialLength = 4 },
    SolarButterfly = { Voice = { "9116383508" }, VoiceVolume = 4.8, Pitch = 1.1, Special = "9125603931", SpecialVolume = 1.78 },
    SpiritCrane = { Voice = { "9125786547", "9125786586", "9125786593" }, VoiceVolume = 1.89, Special = "9116418035", SpecialVolume = 2 },
    StarfallFox = { Voice = { "9113955372", "9113955728", "9113956187" }, VoiceVolume = 2.32, Special = "9114157695", SpecialVolume = 0.86 },
    StormBumblebee = { Voice = { "9113414107", "9113414119", "9113414621" }, VoiceVolume = 1.12, Special = "9116277062", SpecialVolume = 0.3 },
    StormhornKirin = { Voice = { "9113630351", "9113629973", "9113630346" }, VoiceVolume = 1.11, Pitch = 0.9, Special = "9126100173", SpecialVolume = 0.53 },
    SunscaleDragon = { Voice = { "9120049293", "9120048536" }, VoiceVolume = 0.35, Pitch = 0.75, VoiceLength = 2.4, Special = "9114439212", SpecialVolume = 0.43, SpecialLength = 4 }, -- (tiger roars pitched below every other dragon; the special a searing fire burst for its sun. Measured muted in Play, 2026-11-11: voice means 103 and 65, peaks 603 and 372 at full volume; the special 134, peak 420 over its first 4 s)
    TheNamelessOne = { Voice = { "9126213993", "9126213984", "9126213992" }, VoiceVolume = 0.53, Special = "9119468901", SpecialVolume = 1.55, SpecialLength = 4 },
    ThunderclawDrake = { Voice = { "9113980319" }, VoiceVolume = 0.67, Pitch = 0.9, VoiceLength = 2.6, Special = "9126068434", SpecialVolume = 1.2, SpecialLength = 4 },
    TimekeeperTortoise = { Voice = { "9120881979", "9126263691", "9126264414" }, VoiceVolume = 1.47, Special = "9120288444", SpecialVolume = 4.8 },
    VoidscaleHydra = { Voice = { "9120049821", "9120049811" }, VoiceVolume = 1.41, Pitch = 0.8, Special = "9118886096", SpecialVolume = 1.6 },
    VoltFox = { Voice = { "9113955391", "9113956166", "9113956477" }, VoiceVolume = 1.4, Pitch = 1.35, Special = "9120016256", SpecialVolume = 0.39, SpecialLength = 3 }, -- (a kit: the Starfall Fox's coyote pack, other takes, pitched up; its thunder strikes down. Measured muted in Play, 2026-11-10: takes peak 16.5-19.3, the thunder 124.6)
    WindSprite = { Voice = { "9113080660", "9113080102", "9113080104" }, VoiceVolume = 0.45, Special = "9116432084", SpecialVolume = 3.43, SpecialLength = 4 },
}

PetSounds.Entries = {}
for petId, data in DATA do
    if data.Voice and #data.Voice > 0 then
        local pitch = data.Pitch or 1
        PetSounds.Entries["PetVoice_" .. petId] = { Id = data.Voice, Volume = data.VoiceVolume or 1, Pitch = { pitch * 0.95, pitch * 1.05 },
            Near = VOICE_NEAR, Reach = VOICE_REACH, Length = data.VoiceLength, Start = data.VoiceStart }
    end
    if data.Special then
        PetSounds.Entries["PetSpecial_" .. petId] = { Id = data.Special, Volume = data.SpecialVolume or 1, Near = SPECIAL_NEAR, Reach = SPECIAL_REACH, Length = data.SpecialLength,
            Start = data.SpecialStart }
    end
end

function PetSounds.voice(petId)
    local name = "PetVoice_" .. tostring(petId)
    return if PetSounds.Entries[name] then name else nil
end

function PetSounds.special(petId)
    local name = "PetSpecial_" .. tostring(petId)
    return if PetSounds.Entries[name] then name else nil
end

return PetSounds
