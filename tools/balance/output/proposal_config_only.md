# Progression simulation: proposal_config_only

Monte Carlo, 30 runs per profile (median; p10-p90). Play hours exclude offline Qi, daily rewards and spins;
the calendar columns include them (one session a day, offline Qi for the hours away, daily claim, 3 spins).

| Profile | Play hours to max (p10-p90) | Days at 2 h/day | 4 h/day | 8 h/day | Thefts | Share of time stealing | Hatches | Pets+Codex % at the end |
|---|---|---|---|---|---|---|---|---|
| Free, casual | 45.6 (42.2-48.7) | 12.6 | 7.8 | 4.9 | 350 | 40% | 371 | 911 |
| Free, efficient | 34.7 (32.5-36.8) | 10.1 | 6.0 | 3.6 | 552 | 69% | 680 | 1251 |
| Qi Boost 2x | 18.6 (17.0-20.3) | 6.0 | 3.7 | 2.0 | 293 | 69% | 345 | 1177 |
| Qi Boost 4x | 10.4 (9.5-11.2) | 3.4 | 2.0 | 1.1 | 159 | 68% | 174 | 1096 |
| Qi Boost 8x | 6.0 (5.4-6.5) | 2.0 | 1.2 | 0.7 | 85 | 68% | 92 | 948 |
| Qi Boost 16x | 3.1 (2.9-3.4) | 1.2 | 0.8 | 0.4 | 36 | 59% | 42 | 789 |
| VIP + 2x | 17.4 (16.0-18.2) | 5.4 | 3.5 | 2.0 | 270 | 69% | 314 | 1189 |
| All passes (16x, VIP, Luck, +3 slots) | 2.0 (1.8-2.3) | 1.0 | 0.5 | 0.3 | 28 | 66% | 35 | 1304 |
| VIP + 16x + 5 Exclusive Eggs | 2.4 (2.2-2.7) | 1.0 | 0.6 | 0.3 | 28 | 58% | 39 | 803 |
| Free, fast (sensitivity: a strong player) | 29.9 (27.4-32.4) | 9.3 | 5.7 | 3.0 | 591 | 69% | 719 | 1302 |
| Free, idle in the Qi Spring only | 121.5 (109.4-146.0) | 18.0 | 12.8 | 8.0 | 0 | 0% | 4 | 87 |

## Hours spent in each realm (play time, median)

| Realm | Free, casual | Free, efficient | Qi Boost 2x | Qi Boost 4x | Qi Boost 8x | Qi Boost 16x | VIP + 2x | All passes (16x, VIP, Luck, +3 slots) | VIP + 16x + 5 Exclusive Eggs | Free, fast (sensitivity: a strong player) | Free, idle in the Qi Spring only |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 Qi Awakening | 0.45 | 0.21 | 0.21 | 0.21 | 0.21 | 0.21 | 0.21 | 0.21 | 0.21 | 0.17 | 0.20 |
| 2 Qi Foundation | 0.53 | 0.18 | 0.08 | 0.03 | 0.01 | 0.01 | 0.07 | 0.01 | 0.01 | 0.16 | 0.66 |
| 3 Spirit Core | 1.04 | 0.39 | 0.21 | 0.11 | 0.06 | 0.03 | 0.20 | 0.01 | 0.01 | 0.35 | 1.82 |
| 4 Spirit Soul | 2.50 | 1.54 | 0.85 | 0.41 | 0.20 | 0.06 | 0.75 | 0.06 | 0.04 | 1.33 | 4.57 |
| 5 Ascendant Realm | 3.80 | 3.54 | 1.96 | 1.10 | 0.57 | 0.33 | 1.88 | 0.18 | 0.15 | 3.12 | 6.58 |
| 6 Immortal Realm | 4.05 | 3.25 | 1.74 | 0.98 | 0.56 | 0.27 | 1.58 | 0.16 | 0.14 | 2.36 | 8.98 |
| 7 Divine Realm | 3.77 | 3.28 | 1.76 | 0.98 | 0.56 | 0.31 | 1.64 | 0.14 | 0.23 | 2.90 | 10.14 |
| 8 Cosmic Realm | 3.88 | 3.36 | 1.82 | 1.06 | 0.65 | 0.33 | 1.77 | 0.24 | 0.26 | 2.99 | 11.89 |
| 9 Void Realm | 7.03 | 4.09 | 2.15 | 1.24 | 0.68 | 0.33 | 2.02 | 0.19 | 0.29 | 4.38 | 16.09 |
| 10 Heavenly Dao | 7.46 | 4.39 | 2.33 | 1.35 | 0.78 | 0.41 | 2.14 | 0.23 | 0.34 | 4.02 | 16.97 |
| 11 Primordial Realm | 5.73 | 5.22 | 2.79 | 1.53 | 0.87 | 0.40 | 2.51 | 0.22 | 0.35 | 4.16 | 21.98 |
| 12 Eternal Transcendence | 5.42 | 4.85 | 2.53 | 1.45 | 0.85 | 0.39 | 2.33 | 0.30 | 0.36 | 3.94 | 21.64 |

## Walls (a rank taking over twice the one before, and over 10 minutes)

- Free, casual: Void Shaper: 1.2 h (after 32 min)
- Free, efficient: Soul Tempering: 13 min (after 6 min); Sky Ascendant: 42 min (after 16 min)
- Qi Boost 2x: Soul Refinement: 11 min (after 5 min); Sky Ascendant: 23 min (after 9 min)
- Qi Boost 4x: Sky Ascendant: 12 min (after 5 min); Golden Immortal: 13 min (after 6 min)
- Qi Boost 8x: none
- Qi Boost 16x: none
- VIP + 2x: Sky Ascendant: 19 min (after 8 min)
- All passes (16x, VIP, Luck, +3 slots): none
- VIP + 16x + 5 Exclusive Eggs: none
- Free, fast (sensitivity: a strong player): Soul Tempering: 11 min (after 5 min); Sky Ascendant: 31 min (after 13 min)
- Free, idle in the Qi Spring only: none

## Minutes per rank, free efficient and Qi Boost 16x

| Rank | Free efficient | 16x |
|---|---|---|
| Qi Gatherer | 4.9 | 4.9 |
| Qi Condenser | 4.0 | 4.0 |
| Qi Adept | 0.1 | 0.1 |
| Qi Awakener | 0.1 | 0.1 |
| Foundation Initiate | 3.3 | 3.3 |
| Foundation Builder | 1.7 | 0.1 |
| Foundation Adept | 1.4 | 0.1 |
| Foundation Master | 1.4 | 0.1 |
| Perfect Foundation | 2.6 | 0.1 |
| Core Initiate | 2.9 | 0.3 |
| Core Formation | 3.7 | 0.1 |
| Core Adept | 4.6 | 0.1 |
| Core Master | 5.0 | 0.1 |
| Golden Spirit Core | 3.9 | 0.1 |
| Soul Awakening | 6.3 | 1.4 |
| Soul Tempering | 13.4 | 2.0 |
| Soul Refinement | 19.5 | 0.1 |
| Soul Manifestation | 22.1 | 0.1 |
| Spirit Soul Master | 21.6 | 0.1 |
| Ascendant Initiate | 15.7 | 1.2 |
| Sky Ascendant | 41.7 | 2.1 |
| Heavenly Adept | 40.9 | 4.7 |
| Celestial Master | 45.9 | 4.7 |
| Ascendant Sovereign | 48.6 | 4.7 |
| Lesser Immortal | 35.3 | 4.0 |
| True Immortal | 30.8 | 1.9 |
| Golden Immortal | 38.9 | 1.8 |
| Immortal Lord | 44.2 | 2.7 |
| Immortal Emperor | 42.8 | 4.6 |
| Divine Initiate | 39.5 | 3.4 |
| Divine Adept | 28.8 | 1.1 |
| Divine Lord | 40.2 | 2.4 |
| Divine King | 45.0 | 5.0 |
| Divine Emperor | 50.9 | 5.0 |
| Star Initiate | 29.9 | 5.1 |
| Star Forger | 39.1 | 4.7 |
| Nebula Master | 40.6 | 4.9 |
| Galaxy Sovereign | 48.0 | 4.9 |
| Cosmic Emperor | 47.0 | 4.9 |
| Void Walker | 28.7 | 0.2 |
| Void Shaper | 42.4 | 3.1 |
| Void Master | 45.3 | 2.1 |
| Space-Time Lord | 56.6 | 4.7 |
| Void Sovereign | 56.6 | 5.0 |
| Dao Seeker | 45.7 | 4.6 |
| Dao Adept | 40.3 | 3.6 |
| Dao Master | 54.3 | 4.8 |
| Heavenly Lawkeeper | 54.3 | 4.8 |
| Dao Sovereign | 67.9 | 6.0 |
| Primordial Awakening | 46.0 | 4.6 |
| Ancient Origin | 61.6 | 3.2 |
| Primordial Lord | 56.2 | 1.6 |
| Origin Emperor | 69.7 | 5.9 |
| Primordial Sovereign | 67.0 | 6.0 |
| Eternal Initiate | 53.4 | 6.2 |
| Eternal Ascendant | 59.2 | 4.2 |
| Infinity Master | 71.8 | 5.7 |
| Transcendent One | 68.2 | 5.2 |
| Eternal Origin | 92.7 | 7.3 |
