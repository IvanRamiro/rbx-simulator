# Pets window

Status: draft (needs the owner's approval; mockup `design/previews/pets-window-proposed.png`, today's window `current-pets.jpg`).

## What was wrong

With two pets the window shows two very wide cards and about 70% empty panel; a player with 40 pets would scroll a long list of wide cards. There is no search, no "equip best" and no pen capacity count in the window code (checked 2026-11-24: no such code in `src/client/Pets`), so a player cannot find a pet quickly or equip the best set in one tap (the gift icon and the lock sit as small unlabeled squares beside Equip).

## Proposal (1100 x 820 window on desktop)

- Title band 56 high, "PETS" in Merriweather 22, square red close at the top right.
- Toolbar at y 72: tabs MY PETS / PEN (44 high, the active one AccentFill), a 240 x 44 search field, chips EQUIPPED 0 / 6 and QI BONUS +0%.
- **Grid:** 5 columns of 120 x 138 tiles, gap 12: the pet's picture (104 x 90) and "+120% Qi" under it, a rarity-coloured 2 px rim (Mythical in Danger red, Common in Muted), the selected tile with a 4 px AccentFill rim, a green tick on equipped pets. Empty pen spaces drawn as dashed EMPTY tiles so the capacity is visible.
- **Detail panel** 300 wide on the right: large picture, name (Merriweather 20), rarity chip, the bonus large (26 Black, Highlight), one line of help, then EQUIP (Buy green, 52 high), and GIFT and LOCK as labelled 44 px buttons side by side.
- **Footer:** PEN 2 / 20 and EQUIP BEST (AccentFill, 48 high).

## Phone

The grid goes to 3 columns of 96 px tiles and the detail panel becomes a sheet that slides up over the grid when a tile is tapped (EQUIP, GIFT, LOCK as 44 px buttons in a row). Toolbar: search collapses to an icon.

## States

Empty (no pets: the same grid of dashed tiles with a line "Hatch an egg to get your first beast" and a button to the hatchery or shop), loading (tiles shimmer), locked pet (lock badge, EQUIP greyed), pen full (PEN 20 / 20 in Danger), gifting open (the existing GiftPicker), error (a red line under the toolbar).

## Where it lives

`src/client/Pets/PetController.client.lua`, `PenPicker.lua`, `GiftUi.lua`, window shell `Hud.window`. Equip, lock and gift stay as server-validated remotes; "Equip best" needs a new server rule (equip the highest Qi bonus pets up to the slot count) with a spec, and must be rate-limited like the other pet remotes.

## Acceptance

Works with 0, 2 and 60 pets; the grid never shows a horizontal scrollbar; selected, equipped, locked and empty are told apart without colour alone (tick, lock, dashes); all targets at least 44 px; no console errors; the server still decides equip, lock and gift.
