# Eggbound UI design system ("Cultivation Bold")

Status: describes the look the game already has (read from `src/client/UI/UiTheme.lua`, 2026-11-24). Nothing here is a new style: the owner dropped a full restyle ("Celestine") on 2026-11-16 and asked to keep this one. The proposals in `design/features/` refine layout and clarity inside it.

Mockups were made in a private Figma draft (2026-11-24) and exported here as previews in `design/previews/`. The Figma file is not needed to build: every number is below.

## Colours (UiTheme.Colors)

| Token | RGB | Use |
| --- | --- | --- |
| Panel | 24, 25, 68 | window glass, HUD cards (0.86 to 0.9 opacity on the HUD) |
| Raised | 34, 33, 84 | rows, tiles, quiet buttons |
| Well | 8, 9, 26 | bar tracks, wells, key caps |
| Edge | 226, 182, 92 | gold trim |
| EdgeDim | 128, 102, 62 | quiet frames, separators |
| Accent | 236, 190, 90 | progress, secondary actions |
| AccentFill | 255, 200, 76 | the one lit primary button on a screen |
| Highlight | 255, 216, 104 | a reward, the rank, section headings |
| Buy | 46, 190, 88 | buying and equipping (green, as in every Roblox shop) |
| BuyBright | 168, 255, 176 | Buy's rim |
| Danger / DangerDeep | 255, 76, 92 / 96, 18, 32 | guardians, refusals, close |
| Text / Muted | 246, 245, 255 / 172, 170, 204 | body text / secondary text |
| Sky | 150, 226, 255 | Qi, distances |
| Outline | 10, 8, 26 | the dark outline on heavy words |

## Type (UiTheme.Fonts, sizes from UiTheme.Text)

Merriweather Bold for a window's name (22), a rank, a quest title (18 to 20). Montserrat for everything else: Medium body (13), SemiBold, ExtraBold for labels and numbers, Heavy/Black for prices and button words (15, 18 on a main action). Section headings are 12 px ExtraBold capitals, letter-spaced. Captions 10 to 11. English only.

## Measures (UiTheme.Space / Radius / Stroke / Height)

Gaps 4, 8, 12, 16, 24. Radii: window 14, card 10, button 10, chip 6. Strokes 2 (fine 1). Touch target 44 minimum (button 44, main action 52, tab 44, title band 52). Margin from the screen edge 16 to 24.

## Rules that hold on every surface

1. One lit thing: a screen has one AccentFill or Buy primary button.
2. Buying and equipping are green; closing is the square red button with a white X at the top right of a window; a locked or unusable thing is dimmed (grey), with a lock where it is locked.
3. Every number says what it counts (a word or an icon plus a caption). A badge is a number, top right of what it counts.
4. Nothing sits in the screen's centre column except the currency pill and its toast slot. The player's nameplate and title banner live there.
5. Phone first: layouts must fit 685x338 and leave Roblox's own thumbstick (left bottom) and jump (right bottom) areas clear. Minor menus collapse behind one MENU button on a phone.
6. Windows are one at a time (`Hud.window`); build the empty, loading, locked and error state of each, not just the full one.
7. Valuable actions are decided on the server; the client only asks.

## Sources read for this pass

Roblox's own pages "UI and UX design" and "Adaptive design guidelines" (create.roblox.com). They give conventions rather than numbers: show only what matters in context, collapse minor buttons into a menu on small screens, square red X to close, grey for what cannot be used, a price in red when it cannot be afforded, the biggest offer drawn larger, high contrast and no thin or very decorative fonts on small screens, test on a real device at the smallest size. They give no touch-target or safe-area numbers; the 44 px target is the game's own convention. A look at top simulator games' HUDs was not found as a dated analysis: nothing here claims to copy a specific game.
