# Stellaris Guide v1.5.0

## Delivered

- **Main:** compact expandable empire health summary for resource balances, science, empire size, naval use, and starbase use/capacity. Goals and next steps stay near the top of the page.
- **Planets:** Cygnus workforce by job type, filled/capacity/allowed values when recorded, and conditional job suggestions alongside colony build advice.
- **Empires:** separate Military, Economy, Technology, Diplomacy, and Intel views. Your empire remains pinned as a reference. Known contacts show player intel and recorded spy networks; missing intelligence says **Unknown**.
- **Spoiler control:** off for each campaign. A warning, acknowledgement check, and final Enable action are required. Exact foreign power and selected stockpiles are withheld from ordinary state, history, and chat context while off.
- **Ship Builds:** reads saved slot components and required components, then provides a cautious review of owned designs.
- **Camera:** the Windows app detects `stellaris.exe` and captures its visible window directly when there is one match. The player then selects a region or full image before sending. When no game window is found or capture fails, a window/screen chooser appears.
- **Version:** UI and portable package identify v1.5.0.

## Important limits

- Stellaris 4.5.2 Cygnus saves were used for validation. Mods and future game updates may change fields.
- Foreign Military/Economy/Technology values may remain **Unknown** in normal mode when the save does not contain a reliable player-visible rating. Spoiler mode labels exact save-derived values as hidden in game.
- Naval use is read; a reliable naval capacity value was not established. The UI says **Unknown** instead of inventing a limit.
- Subject ties, claims, diplomatic weight, victory standings, ascension paths, and detailed espionage operations need validated save fields. Opinion by itself does not predict war.
- Ship suggestions review saved designs and slots. Build eligibility, costs, enemy counters, and battle outcomes must be checked in game.
- Fullscreen, minimized-window, and multi-monitor capture behavior depends on Windows and the running game. Browser-only source mode uses the browser share picker.

## Install

Extract `dist/StellarisGuide-Windows-1.5.0.zip`, then double-click `StellarisGuide.exe`. See [the installation steps](INSTALL.md) or the `INSTALL-WINDOWS.txt` inside the ZIP.

## Verification

Run `python -m unittest discover -s tests -v` from the project root, then `build_windows.bat`. The release was checked against a representative 4.5.2 autosave and a live Stellaris window. This folder is not a Git checkout, so v1.5.0 is a package/UI version rather than a Git tag.
