# Settings window

Status: approved (owner: "Yes", 2026-11-24, after the round-2 mockups) (needs the owner's approval; mockup `design/previews/settings-v2.png`; today's window `current-settings.jpg`; re-render with `python3 design/mockups/render.py`).

## Build status (2026-11-24, tested in Play)

**Built:** real switches (a 56 x 30 pill, a knob that slides, green when on, ON / OFF beside it; `renderSwitch`), SOUND / DISPLAY / HELP headings, and the SHOW QUEST TRACKER row (sets `SettingShowQuest` and tells the server the same way the Quests button does). Seen in Play: the Reduced Effects switch turned on (attribute true, label ON, green, knob at the right). The window is 420 x 580 (664 for developers) and scrolls.

## What was wrong

Switches (`switchRow` in `SettingsController`) are wide buttons that say OFF/ON, so the state reads as a label, not a control. The list is flat with no groups. (The Performance readout row is already built only for developers, `isDeveloper`; the audit screenshot showed it because the test account has the Developer title. Nothing to change there.)

## Proposal (640 wide, height follows content)

- Title band 56, square red close top right.
- Three groups with 12 px Highlight capitals: SOUND, DISPLAY, HELP.
- **Sound:** MUSIC and SOUND rows keep the 44 px minus and plus buttons (touch-friendly) around a 250 x 12 gold track, with the percentage in Highlight.
- **Display:** REDUCED EFFECTS and SHOW QUEST TRACKER as real switches: a 64 x 34 pill, knob left and dark when off, knob right and green (Buy) when on, with ON / OFF beside it; each has a one-line description in Muted.
- **Help:** FEEDBACK with an OPEN button.
- SHOW QUEST TRACKER is a new row: the setting already exists (`SettingShowQuest`, saved by `server/Data/Settings.lua`) but today has no row here. The developer-only Performance readout stays as it is.
- The window is 420 wide in code (`Hud.window` Size 420 x 460, 544 for developers) and the mockup is drawn at 640: build at the code's width and scale the rows (the proportions, not the pixel widths, are the proposal).

## States

Each switch: on, off, pressed. Sliders at 0% (track empty, minus greyed) and 100% (plus greyed).

## Where it lives

`src/client/UI/SettingsController.client.lua` and `UiKit.lua` (a `UiKit.switch` helper if none exists). The settings are client preferences saved through the existing throttled remote (0.25 s); no new server surface.

## Acceptance

State is clear without reading the word; keyboard, touch and gamepad can all toggle; changes persist as they do now; no console errors.
