# HUD

Status: draft (needs the owner's approval before building; mockups in `design/previews/hud-desktop-proposed.png` and `hud-phone-proposed.png`, today's HUD in `current-hud.jpg`).

## What was wrong (seen in Play, 2026-11-24, 1920 wide)

1. The reward toast appears at the screen's centre at about y 250 to 330, on top of the quest card and the player's title nameplate ("Developer" was cut off behind it).
2. The quest card sits top centre, over the same space as the nameplate.
3. The left menu rail is 8 equal 118 px tiles: about 570 px of the screen's height, and Shop/Pets weigh the same as Feedback.
4. The currency pill shows three icons and numbers with no words ("0 / 11").
5. Three round buttons top right (egg offer, spin, rewards) have no labels and their "!" and "3" badges overlap the ring.
6. The waypoint "SEREN, GUIDE 76 studs" is loose outlined text at the right edge.
7. Air Leaps is a wide bar holding a single diamond.

## Proposal (desktop 1920x1080 reference)

- **Profile card** top left at (24, 24), hug width (about 330 x 100): 72 px avatar ring, name, rank (Merriweather 20, Highlight), 170 x 10 progress bar with "1 / 5", next step caption.
- **Menu rail** under it, 204 wide, three tiers: MENU toggle (34 high) then Shop and Pets 100 x 100 (Shop has the gold rim as the one lit tile), then Codex, Robes, Quests, Titles in 2x2 of 100 x 76, then Settings and Feedback as 100 x 36 chips with a small icon and a 10 px word. About 350 px tall in all. Badges (0/6, 23, 7) in the tile's top right corner, drawn above it.
- **Currency pill** top centre at y 16, hug width (about 305): icon + number (22 ExtraBold) with a 9 px caption under each: QI, STONES, RELICS.
- **Toast slot** centred at y 100 (hug width, 52 high): 6 px gold stripe, icon, small gold word, then the line. One at a time, queued, a few seconds each. It never appears anywhere else.
- **Right column** at x 1556, y 24, width 340: quest tracker (kicker, title Merriweather 18, a Sky "76 studs" chip and the hint), Air Leaps (40 high, label left, diamond and 1/1 right), then the three event buttons (64 px rings) each with a 10 px label (EGG, SPIN, REWARDS) and a red badge on the ring's corner.
- **Waypoint pill** at the right edge, y about 520: gold-edged pill, name (Highlight), distance, an arrow.
- **Weapon slot** unchanged: 88 x 88 at the bottom centre with its key cap and hint line.

## Phone (685x338 reference)

Profile chip (avatar 36, rank, a 90 x 6 bar) top left; currency pill centred (numbers only, 14 px); quest tracker as a two-line card top right with the three event buttons (44 px) under it; one MENU button (44 high) under the profile chip opens the menu as it does today; the weapon slot 56 px bottom centre. Keep the circles at the bottom left (about 130 px) and bottom right (about 120 px) empty: Roblox's thumbstick and jump.

## States to build

Quest card: no active quest (hidden), complete (gold tick). Toast: queued, leaving. Menu: collapsed (only the MENU button). Badges: none, a number, 99+. Currency: loading (dashes), large numbers (abbreviate at 10,000: 10K).

## Where it lives

`src/client/UI/Hud.lua` (regions Status, Menu, Rail, top stack `layoutTop`), `HudMetrics.lua`, `Toast.lua`, `WorldMarkers.lua` (waypoint), `TitleBanner.lua`. Measures from `UiTheme`. Check with the `HudTestViewport` harness and the phone Device Emulator (notes in the vault).

## Acceptance

No overlap between toast, quest card, nameplate and title banner at 1920x1080 and 685x338; every currency and event button has a word; the rail is at most 360 px tall on desktop; nothing in the thumbstick or jump zones; all targets at least 44 px; no console errors.
