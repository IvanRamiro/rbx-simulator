# Progression simulation: market_on

Monte Carlo, 30 runs per profile (median; p10-p90). Play hours exclude offline Qi, daily rewards and spins;
the calendar columns include them (one session a day, offline Qi for the hours away, daily claim, 3 spins).

| Profile | Play hours to max (p10-p90) | Days at 2 h/day | 4 h/day | 8 h/day | Thefts | Share of time stealing | Hatches | Pets+Codex % at the end |
|---|---|---|---|---|---|---|---|---|
| Free, casual | 31.1 (28.9-34.3) | 10.1 | 6.2 | 3.7 | 236 | 40% | 261 | 977 |
| Free, efficient (with the free boosts) | 26.0 (24.2-28.0) | 8.0 | 5.0 | 2.9 | 439 | 97% | 587 | 1265 |
| Free, fast (sensitivity: a strong player) | 23.1 (21.1-24.3) | 8.0 | 4.7 | 2.7 | 448 | 97% | 601 | 1259 |
| 2x pass only | 14.9 (13.9-15.9) | 5.0 | 3.0 | 1.7 | 251 | 97% | 307 | 1203 |
| 4x pass only | 8.5 (8.1-9.4) | 3.0 | 2.0 | 1.0 | 138 | 95% | 153 | 1130 |
| 4x + VIP | 8.1 (7.4-8.4) | 2.9 | 1.7 | 1.0 | 129 | 95% | 141 | 1110 |
| PAYING PLAYER: 4x + VIP + 30 min of timed boost a day | 7.2 (6.5-7.9) | 2.5 | 1.6 | 0.9 | 110 | 95% | 122 | 1114 |
| 4x + VIP + 4 h of timed boost a day (all play time) | 4.8 (4.2-5.0) | 2.0 | 1.0 | 0.6 | 71 | 92% | 77 | 993 |
| 2x + VIP + 15 min of timed boost a day | 12.9 (12.1-13.8) | 4.6 | 2.8 | 1.6 | 214 | 97% | 253 | 1233 |
| All passes (4x, VIP, Luck, +3 slots) + 4 h boost + 5 Exclusive Eggs | 2.8 (2.5-3.1) | 1.2 | 0.7 | 0.4 | 39 | 86% | 50 | 1591 |
| Owner of the retired 16x pass (counts as the cap) | 8.5 (8.1-9.4) | 3.0 | 2.0 | 1.0 | 138 | 95% | 153 | 1130 |
| Free, idle in the Qi Spring only | 122.6 (104.7-152.1) | 17.1 | 12.5 | 7.4 | 0 | 0% | 3 | 74 |

## Hours spent in each realm (play time, median)

| Realm | Free, casual | Free, efficient (with the free boosts) | Free, fast (sensitivity: a strong player) | 2x pass only | 4x pass only | 4x + VIP | PAYING PLAYER: 4x + VIP + 30 min of timed boost a day | 4x + VIP + 4 h of timed boost a day (all play time) | 2x + VIP + 15 min of timed boost a day | All passes (4x, VIP, Luck, +3 slots) + 4 h boost + 5 Exclusive Eggs | Owner of the retired 16x pass (counts as the cap) | Free, idle in the Qi Spring only |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 Qi Awakening | 0.39 | 0.20 | 0.17 | 0.20 | 0.20 | 0.20 | 0.20 | 0.20 | 0.20 | 0.20 | 0.20 | 0.13 |
| 2 Qi Foundation | 0.54 | 0.17 | 0.15 | 0.07 | 0.01 | 0.01 | 0.01 | 0.01 | 0.03 | 0.01 | 0.01 | 0.71 |
| 3 Spirit Core | 1.03 | 0.39 | 0.35 | 0.22 | 0.14 | 0.13 | 0.06 | 0.06 | 0.11 | 0.03 | 0.14 | 1.94 |
| 4 Spirit Soul | 2.56 | 1.49 | 1.38 | 0.82 | 0.44 | 0.40 | 0.18 | 0.18 | 0.72 | 0.09 | 0.44 | 4.85 |
| 5 Ascendant Realm | 2.90 | 2.38 | 1.81 | 1.42 | 0.90 | 0.82 | 0.75 | 0.49 | 1.36 | 0.20 | 0.90 | 6.63 |
| 6 Immortal Realm | 2.93 | 2.09 | 1.79 | 1.19 | 0.71 | 0.63 | 0.64 | 0.38 | 1.12 | 0.21 | 0.71 | 9.04 |
| 7 Divine Realm | 3.49 | 3.16 | 2.72 | 1.72 | 0.98 | 0.89 | 0.89 | 0.50 | 1.31 | 0.31 | 0.98 | 10.09 |
| 8 Cosmic Realm | 3.49 | 3.23 | 2.90 | 1.88 | 1.03 | 0.94 | 1.02 | 0.57 | 1.67 | 0.33 | 1.03 | 12.02 |
| 9 Void Realm | 3.70 | 3.54 | 3.11 | 2.00 | 1.21 | 1.07 | 0.74 | 0.63 | 1.73 | 0.37 | 1.21 | 16.15 |
| 10 Heavenly Dao | 3.29 | 3.08 | 2.70 | 1.78 | 1.11 | 1.07 | 0.93 | 0.60 | 1.63 | 0.38 | 1.11 | 17.15 |
| 11 Primordial Realm | 3.83 | 3.35 | 3.08 | 1.83 | 1.05 | 1.01 | 1.05 | 0.60 | 1.72 | 0.35 | 1.05 | 22.04 |
| 12 Eternal Transcendence | 3.32 | 2.87 | 2.78 | 1.69 | 0.82 | 0.78 | 0.84 | 0.48 | 1.25 | 0.36 | 0.82 | 21.86 |

## Walls (a rank taking over twice the one before, and over 10 minutes)

- Free, casual: none
- Free, efficient (with the free boosts): Soul Tempering: 14 min (after 6 min); Sky Ascendant: 35 min (after 14 min)
- Free, fast (sensitivity: a strong player): Soul Tempering: 11 min (after 6 min)
- 2x pass only: Soul Refinement: 11 min (after 5 min); Sky Ascendant: 21 min (after 9 min)
- 4x pass only: Sky Ascendant: 12 min (after 5 min)
- 4x + VIP: Sky Ascendant: 12 min (after 4 min); Void Shaper: 12 min (after 5 min)
- PAYING PLAYER: 4x + VIP + 30 min of timed boost a day: Star Forger: 13 min (after 5 min)
- 4x + VIP + 4 h of timed boost a day (all play time): none
- 2x + VIP + 15 min of timed boost a day: Sky Ascendant: 21 min (after 8 min)
- All passes (4x, VIP, Luck, +3 slots) + 4 h boost + 5 Exclusive Eggs: none
- Owner of the retired 16x pass (counts as the cap): Sky Ascendant: 12 min (after 5 min)
- Free, idle in the Qi Spring only: none

## Minutes per rank, free efficient and the paying player

| Rank | Free efficient | Paying player |
|---|---|---|
| Qi Gatherer | 4.8 | 4.8 |
| Qi Condenser | 4.0 | 4.0 |
| Qi Adept | 0.1 | 0.1 |
| Qi Awakener | 0.1 | 0.1 |
| Foundation Initiate | 3.3 | 3.3 |
| Foundation Builder | 0.1 | 0.1 |
| Foundation Adept | 1.7 | 0.1 |
| Foundation Master | 1.3 | 0.1 |
| Perfect Foundation | 2.6 | 0.1 |
| Core Initiate | 3.8 | 0.3 |
| Core Formation | 3.7 | 0.1 |
| Core Adept | 3.9 | 1.1 |
| Core Master | 5.0 | 0.1 |
| Golden Spirit Core | 3.9 | 1.1 |
| Soul Awakening | 6.4 | 1.4 |
| Soul Tempering | 14.0 | 2.1 |
| Soul Refinement | 19.0 | 0.1 |
| Soul Manifestation | 21.7 | 2.1 |
| Spirit Soul Master | 21.5 | 3.9 |
| Ascendant Initiate | 14.0 | 3.0 |
| Sky Ascendant | 35.4 | 6.9 |
| Heavenly Adept | 28.0 | 8.0 |
| Celestial Master | 27.8 | 9.4 |
| Ascendant Sovereign | 27.6 | 11.0 |
| Lesser Immortal | 21.3 | 7.6 |
| True Immortal | 21.8 | 6.4 |
| Golden Immortal | 24.5 | 7.3 |
| Immortal Lord | 26.5 | 9.0 |
| Immortal Emperor | 28.1 | 8.9 |
| Divine Initiate | 25.3 | 7.4 |
| Divine Adept | 28.8 | 8.5 |
| Divine Lord | 38.9 | 10.1 |
| Divine King | 40.0 | 15.0 |
| Divine Emperor | 52.3 | 14.9 |
| Star Initiate | 29.9 | 5.1 |
| Star Forger | 39.2 | 13.4 |
| Nebula Master | 41.0 | 9.8 |
| Galaxy Sovereign | 43.2 | 14.6 |
| Cosmic Emperor | 42.6 | 14.6 |
| Void Walker | 28.3 | 9.7 |
| Void Shaper | 41.7 | 11.1 |
| Void Master | 41.7 | 9.5 |
| Space-Time Lord | 47.1 | 9.4 |
| Void Sovereign | 43.3 | 9.4 |
| Dao Seeker | 33.8 | 4.8 |
| Dao Adept | 31.1 | 8.8 |
| Dao Master | 39.8 | 10.6 |
| Heavenly Lawkeeper | 39.5 | 13.5 |
| Dao Sovereign | 46.2 | 13.5 |
| Primordial Awakening | 31.9 | 10.2 |
| Ancient Origin | 35.6 | 10.4 |
| Primordial Lord | 38.0 | 13.0 |
| Origin Emperor | 50.6 | 13.1 |
| Primordial Sovereign | 47.7 | 12.9 |
| Eternal Initiate | 35.1 | 10.4 |
| Eternal Ascendant | 36.4 | 11.2 |
| Infinity Master | 45.4 | 12.5 |
| Transcendent One | 44.2 | 12.4 |
| Eternal Origin | 59.1 | 16.5 |
