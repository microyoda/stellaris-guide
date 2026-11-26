# Stellaris Guide v1.5.1

## Changes

- Moved **Worth watching** from a tall Main panel into a compact Watchlist ticker beside the campaign title. It cycles through alerts, has previous/next controls, and pauses while the player hovers or focuses it.
- Made the next-move cards more compact so the campaign trend and galaxy chart are visible sooner on a desktop screen.
- Replaced the opinion-only Main graph with **Military**, **Economy**, **Technology**, and **Opinion** tabs. Strength tabs sort save-recorded values, show your empire in its actual rank, and compare each rival with your value. Opinion is labelled **Their opinion of you** and has no strength rank or multiplier.
- Kept exact rival strength values behind the per-campaign spoiler confirmation. With spoilers off and no reliable player-visible strength data, rank and rival values say **Unknown**; the chart never invents a standing.
- Fixed direct camera capture. The previous Windows capture could return the desktop window covering Stellaris. `PrintWindow` now captures the actual game pixels while the game is behind another app, followed by the existing region selection preview.

## Install and running versions

Extract `StellarisGuide-Windows-1.5.1.zip` and run `StellarisGuide.exe`. If a dashboard still shows **v1.4.2** or another old badge, quit its tray icon near the Windows clock and reopen the executable from this ZIP. Closing its browser tab does not stop the old process. See [installation steps](INSTALL.md).

## Limits

- The rank describes **values recorded in the save** among the player's empire and contacted empires. It is not verified as the exact number Stellaris displays in every contact screen.
- The camera captures visible, non-minimized Stellaris windows. If Windows returns a blank image, restore the game or use borderless/windowed mode; the window/screen chooser remains available.
- The v1.5.0 limitations in [the previous release notes](RELEASE-1.5.md) still apply.

## Verification

The chart was checked with a representative Stellaris 4.5.2 Cygnus save: the player's military and economy ranks changed with the selected tab, while Opinion remained a relationship view. The camera was checked against a live Stellaris window behind another application, and the crop preview showed the game map rather than the covering window.
