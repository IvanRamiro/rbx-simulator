# HUD

Status: approved (owner: "Yes", 2026-11-24, after the round-2 mockups) (needs the owner's approval before building; mockups `design/previews/hud-walk.png`, `hud-carry.png`, `phone-closed.png`, `phone-menu.png`; today's HUD `current-hud.jpg`; re-render with `python3 design/mockups/render.py`).

## Build status (2026-11-24, tested in Play on a desktop-size screen)

**Built:** a word under each counter (QI, STONES, RELICS; desktop only, the strip is 52 high instead of 42); the standing Qi multiplier chip ("x4.4", `PassRules.qiMultiplier(player, true)`, hidden at x1; not tappable); a word under each round button (EGG, SPIN, REWARDS; hangs outside the button, hidden on a phone); the CARRYING card (`src/client/Guardians/CarryCard.client.lua`, in the right column over the quest tracker: egg name and picture, HOME and the distance, a progress bar, and the chase line while the guardian is Enraged). The card was tested by really taking an egg (the attribute and the model's `Egg`, `TargetId`, `SafeZone` and `State` it reads were seen) and drawn from attributes set on the client, because the enraged guardian knocks the test player and drops the egg within a second.
**Not built, and why:**
- **Menu rail in three tiers.** The rail is a uniform `UIGridLayout`, and `railSize()`, the slide-away animation, the phone's row and `FeedbackController` all depend on uniform tiles. It needs its own pass (a wrapping list layout and a new `railSize`).
- **Toast "+N more" count.** Toast's queue logic is spread across `Toast.lua`; its own change.
- **Waypoint as a pill, rail fading while carrying, the phone drawer.** Not started; the phone layout (a row of icons under the profile) was left alone.
- **Quest progress bar:** already exists (the tracker draws a bar for a quest with a count), so nothing to add.

**Corrections to the audit above:** the card at the top centre is the new-player "Guide call" (`GuideController`, in the Banner), not the quest tracker; the real tracker is the right-hand `Hud.Quest` region and stays hidden until the guide has been met. The reward toast hangs under the Banner, so it only overlaps the nameplate while the Banner holds something. A Qi-per-second readout and a timed-boost pill already existed beside the Qi number.

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

## Revision 2 (2026-11-24): what was added after the first mockups

The mockups are now drawn over a real in-game capture with the game's own icons and fonts (HTML in `design/mockups/`), so spacing and contrast are judged in context. New in this round:
- **Qi boost chip** on the Qi number (gold "x4.4"): the multiplier the Shop window already shows as "YOUR QI BOOST"; tapping it opens the Shop's Qi Boosts tab. Hidden at x1.
- **Carrying state** (`hud-carry.png`, new): when `CarryingEgg` is set, the quest card is replaced by a red-rimmed card: the egg's icon in a light ring (the dark Forbidden Origin egg vanishes on a dark panel), its name, "HOME · Yggdrasil" with the distance and a green progress bar, and a red line "The <guardian> is chasing you" while the guardian is Enraged. The waypoint pill turns green and points home. The left rail fades to 55% so the chase is the focus. No HUD card for carrying exists today (checked `src/client`: only touch actions, the guide arrow and combat read `CarryingEgg`).
- **Toast queue:** a "+2 more" chip when toasts are waiting.
- **Quest progress:** a thin bar under the quest title when a step counts (for example Hatch 0/1).
- **Feedback** has a chat icon; the Shop tile carries the one gold rim.

Data needed: the egg's display name and the guardian state are already attributes on the model and the player (`CarryingEgg`, the guardian's `State`, `Called`); the home distance is the SafeZone point in `GameConfig.Guardians.<id>`. Nothing needs a new remote.

## Phone (685x338 reference)

Profile chip (avatar 36, rank, a 90 x 6 bar) top left; currency pill centred (numbers only, 14 px); quest tracker as a two-line card top right with the three event buttons (44 px) under it; one MENU button (44 high) under the profile chip opens a left drawer (`phone-menu.png`: 2 columns of 62 px tiles, Shop lit, Feedback reached through Settings) over a dimmed world; the weapon slot 56 px bottom centre. Keep the circles at the bottom left (about 130 px) and bottom right (about 120 px) empty: Roblox's thumbstick and jump.

## States to build

Quest card: no active quest (hidden), complete (gold tick). Toast: queued, leaving. Menu: collapsed (only the MENU button). Badges: none, a number, 99+. Currency: loading (dashes), large numbers (abbreviate at 10,000: 10K).

## Where it lives

`src/client/UI/Hud.lua` (regions Status, Menu, Rail, top stack `layoutTop`), `HudMetrics.lua`, `Toast.lua`, `WorldMarkers.lua` (waypoint), `TitleBanner.lua`. Measures from `UiTheme`. Check with the `HudTestViewport` harness and the phone Device Emulator (notes in the vault).

## Acceptance

No overlap between toast, quest card, nameplate and title banner at 1920x1080 and 685x338; every currency and event button has a word; the rail is at most 360 px tall on desktop; nothing in the thumbstick or jump zones; all targets at least 44 px; no console errors.
