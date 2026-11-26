# Stellaris Guide v1.5.2

## Changes

- Watchlist spans a slim row below the campaign heading and date, directly above the campaign indicators. The alert title and detail stay on one line and shorten gracefully when space is limited.
- Watchlist moves to the next item automatically every seven seconds while the dashboard tab is visible. Using an arrow starts a fresh seven-second countdown; the ticker no longer stays paused after a button keeps keyboard focus.
- On narrower windows, the detail is hidden so the alert title and controls remain usable.

## Install

Extract `StellarisGuide-Windows-1.5.2.zip` and run `StellarisGuide.exe`. Quit any older Stellaris Guide from its tray icon near the Windows clock before starting the new executable. The badge below the app name should read **v1.5.2**. See the [installation guide](INSTALL.md).

## Verification

JavaScript syntax check and 18 Python tests passed. This release changes the Watchlist presentation and rotation; save parsing and strategy calculations are unchanged. For the graph and game-window capture limits, see the [v1.5.1 notes](RELEASE-1.5.1.md).
