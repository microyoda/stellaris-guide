# Stellaris Guide — technical guide

**Baseline:** v1.6.2, October 20, 2026. This describes the current Windows implementation. Sections labelled **Proposed** are extension guidance rather than behavior already in the app. See [Product plan](PRODUCT.md) for priorities and [System architecture](SYSTEM-ARCHITECTURE.md) for boundaries and diagrams.

## Build and run

The app is Python with a local HTTP server and a static HTML/CSS/JavaScript client. [requirements.txt](../requirements.txt) specifies Pillow, pystray, and PyInstaller. The portable EXE is built on Windows by [build_windows.bat](../build_windows.bat), which bundles `static/` and creates `dist/StellarisGuide-Windows-1.6.2.zip`.

From a PowerShell prompt in the repository root:

```powershell
py -3 -m pip install -r requirements.txt
py -3 app.py
```

The source run opens the browser and starts the tray menu. For a package, run `build_windows.bat`, extract the resulting ZIP, and start `StellarisGuide.exe`. The application does not bundle Stellaris or its art. The [installation guide](INSTALL.md) covers the player-facing flow.

## Code map

| File | Current responsibility |
| --- | --- |
| [app.py](../app.py) | Small executable entry point into the server. |
| [server.py](../stellaris_guide/server.py) | Startup, 15-second save watcher, process state, config and plan persistence, local API, public/spoiler projection, AI requests, and shutdown. |
| [saves.py](../stellaris_guide/saves.py) | Discover `.sav` files, read ZIP `meta` and `gamestate`, parse Clausewitz-style blocks, and normalize empire, colony, technology, diplomacy, policy, and ship data. |
| [strategy.py](../stellaris_guide/strategy.py) | Deterministic five-to-ten-year goals, steps, alerts, and progress. |
| [advice.py](../stellaris_guide/advice.py) | Built-in answers and dispatch for common economy, planet, research, ship, and threat questions. |
| [technology.py](../stellaris_guide/technology.py) | Focused prerequisite lookup from installed game technology definitions. |
| [assets.py](../stellaris_guide/assets.py) | Optional flag composition and local game icon conversion. |
| [capture.py](../stellaris_guide/capture.py) | Enumerate Windows windows and capture a selected target. |
| [tray.py](../stellaris_guide/tray.py) | Reopen, refresh, and quit commands in the notification area. |
| [static/app.js](../static/app.js), [static/index.html](../static/index.html), CSS | Client state, tabs, charts, Watchlist, chat, settings, screenshot crop, and responsive layout. |

## Save lifecycle and state

1. Startup loads `%LOCALAPPDATA%\StellarisGuide\config.json` and the saved plan, scans once, starts the watcher, binds `127.0.0.1` to an available port, starts the tray icon, and opens the browser.
2. `recent_saves()` walks the configured save folder. If it finds autosaves, it uses autosaves; otherwise it considers other `.sav` files. It chooses the newest modified file and up to six recent files from that campaign folder. This is **file modification order**, not necessarily the highest in-game date across all campaigns.
3. `scan_once()` skips a file whose path and modification time match the current snapshot. It parses the newest file in detail and older selected files for compact history. A bad older file does not suppress a readable newest file.
4. `parse_save()` requires ZIP members `meta` and `gamestate`, rejects a `gamestate` over 350 MB uncompressed, and creates a Python snapshot. Missing or unstable fields should be represented as missing/Unknown, not invented values.
5. `make_advice()` combines the newest snapshot, history, and persisted plan. State is held in memory under a reentrant lock. The watcher rescans every 15 seconds; the client also requests `/api/state` every 15 seconds. Manual refresh calls `/api/refresh`.
6. `/api/state` sends a public projection of snapshot and history. The browser renders it in the active view. The game save remains read-only.

The snapshot has campaign identity and save date, player data, contacts, policies and flag data. The latest snapshot also carries `planets`, `technology`, and `ship_builds`; historical snapshots intentionally omit those detailed collections. Advice currently has `goals` and `alerts`. These are plain dictionaries rather than a versioned public schema.

## Local API

| Method and path | Purpose |
| --- | --- |
| `GET /api/state` | Status, public snapshot, six-save history, advice, public config, request token, poll interval, app version and capture availability. |
| `GET /api/flag`, `/api/tech-icon`, `/api/planet-icon` | Render optional local Stellaris art, with fallbacks when unavailable. |
| `POST /api/config`, `/api/choose-folder`, `/api/refresh` | Update settings, choose a folder, or scan immediately. |
| `POST /api/spoilers` | Enable with acknowledgement and confirmation phrase, or disable, for the current campaign. |
| `POST /api/capture-targets`, `/api/capture` | List capture choices and obtain a one-shot Windows image. |
| `POST /api/ask` | Built-in or selected-model answer, with optional image and active-view context. |
| `POST /api/history`, `/api/history/clear` | Read or clear recent/frequent question text. |
| `POST /api/quit` | Stop the local server. |

The server accepts a local Host value, binds only to loopback, and requires the random token returned by `/api/state` on POST requests. It bounds POST bodies at 8 MB and image bytes at 4 MB, checks JPEG/PNG signatures, and serves static files only from the bundled `static` directory. These controls should be retained when adding routes; the token is a local request guard, not account authentication.

Tech routes open in an Edge app window with a per-route profile under `%LOCALAPPDATA%\StellarisGuide\route-windows`. The Close action checks the exact route title, the Edge executable, and that its process began with this route launch before sending a window-close message. A route that opens as a tab in an older Edge window is left for the player to close with the tab's X. This keeps unrelated Edge windows out of the close path. Local route profiles are removed shortly after a successful close when Edge releases them.

For research routes, `tech_route.py` reads direct prerequisites from the installed base-game definitions. The selected technology's detail panel lists only those direct links. Its map traverses earlier dependencies only until a technology already researched in the selected save, so completed ancestors do not remain highlighted as work to do. For a researched target, the page follows dependency links up to two steps forward; these cards are possible paths and never guarantee a research draw. Alternative links, tier gates, DLC and mod uncertainty remain separate from prerequisite edges. This is the v1.6.2 route interpretation decision; see [release evidence](release1.6.2-implementation-evidence.md).

## Privacy, spoilers, and AI

`public_snapshot()` removes hidden foreign values unless the **exact selected save** has spoiler consent. The consent key is the selected save's SHA-256 fingerprint and is stored in config; it turns off at the next autosave or a replacement campaign. The browser asks for acknowledgement before enabling, and the API also requires `enable=true`, `acknowledged=true`, and `confirmation="ENABLE SPOILERS"`. New endpoints and AI context must use the public projection, not the raw snapshot.

The default provider is `off`, which calls the deterministic built-in guide. Ollama uses local `/api/chat` on port 11434; LM Studio uses its local OpenAI-compatible endpoint on port 1234; OpenRouter uses an online chat-completions endpoint. The selected model must support images for screenshot questions. Provider failures return a built-in text fallback; screenshot failure is explicitly reported as not analyzed. The OpenRouter API key is held in process memory for the run rather than written into `config.json`.

On a camera click, the Windows package identifies a visible, non-minimized `stellaris.exe` window when possible. `capture.py` uses Win32 `PrintWindow` to read its pixels, then the client lets the player crop or keep the full image. If direct capture fails, the chooser offers other windows or the screen. Browser-only source mode uses the browser share picker. Capture is one-shot; the cropped image is attached to the question and submitted only when the player sends it. Question history stores text, counts, and whether an image was used; it does not store images or answers.

## Local data and ownership

| Path | Purpose | Migration concern |
| --- | --- | --- |
| `%LOCALAPPDATA%\StellarisGuide\config.json` | Save folder, game folder, provider/model, and spoiler campaign. | Keep unknown/new fields optional; avoid persisting provider secrets. |
| `%LOCALAPPDATA%\StellarisGuide\plan-v1.4.json` | Stable goal targets by campaign. | Filename is historical; version schema before changing structure. |
| `%LOCALAPPDATA%\StellarisGuide\question-history.json` | Up to 60 distinct recent/frequent questions. | Preserve user privacy and provide clear/reset behavior. |
| `%LOCALAPPDATA%\StellarisGuide\fleet-limits.json` | Optional manual naval limit keyed by validated campaign ID. | Token-protected local API rejects stale campaigns and invalid limits; same-directory atomic replacement preserves previous limits on write failure. This is a player entry, not a save fact or AI evidence. |
| Stellaris save and game folders | Read-only input for parsing and optional art. | Never write, rename, or “fix” a game file. |

## Verification and release

From the repository root:

```powershell
$env:PYTHONPATH='.'
py -3 -m unittest discover -s tests -v
node --check static/app.js
build_windows.bat
```

On restricted Windows environments, point `TEMP` and `TMP` at the workspace `.test-temp` directory before tests that create temporary files. The tests cover save parsing, strategy, spoiler filtering, AI formats, question history, camera routing, and selected 4.5 behavior. The package should also be checked for ZIP integrity, bundled assets, startup, local API, tray reopen/quit, and a same-date Stellaris save. See [v1.5.2 release notes](RELEASE-1.5.2.md) for that build's verification scope.

For a new release, update the version badge in `static/index.html`, `server.py` response/version, build paths, installation text, and release notes together. Treat any claimed game-version support as a separate validation decision.

## Proposed extension workflow

1. Gather representative saves and matching in-game screens for the target version and empire types. Scrub personal paths before sharing fixtures.
2. Add the field as an optional normalized fact in `saves.py`, with a clear visibility/provenance rule. Add tests for absent, malformed, and low-intel cases.
3. Pass the fact through the server's public projection. Verify spoiler mode off, on, restart, and campaign switch; include the AI context path.
4. Add a deterministic rule only when its action, cost, eligibility and trade-off can be checked. Otherwise provide a review suggestion and an in-game check.
5. Render the value in the narrowest useful view, preserve a one-screen Main, and test desktop and smaller widths.
6. Update product copy, architecture/data contract, compatibility matrix, and release notes before packaging.

The current parser, planner, API, and UI use flexible dictionaries and some shared process state. **Proposed:** introduce versioned normalized facts and recommendation records incrementally, with adapters for game versions and mods. Keep a stable public API while moving one feature at a time; avoid a full rewrite merely to add a new field.
