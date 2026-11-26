# Option 1 Static Web Companion & Hosting Guide

## Architecture Decision

To let players try Stellaris Guide online without downloading or trusting a `.exe`, the web build runs **100% client-side in the browser**:

- **Zero server uploads & zero hosting cost:** `.sav` files are parsed locally in a browser Web Worker running the exact same pure-Python core modules (`dlcs.py`, `saves.py`, `strategy.py`, `playbooks.py`, `guide_knowledge.py`, `advice.py`, `web_bridge.py`) via Pyodide.
- **Instant demo (<100 ms):** `scripts/build_web.py` precomputes `demo-snapshots.json` (UNE 4.5.2 Settled, Nomads 4.5.2 Arkships, and Willpower 4.6.0 Ideologies) with live DLC checkboxes so visitors can explore immediately while Pyodide loads in the background.
- **Live local save watching (Chromium):** Chrome, Edge, and Brave users can click **Watch Save Folder** (File System Access API) to poll their newest autosave every 15 seconds with read-only browser permission—no `.exe` or extension needed.
- **Browser-local state:** Pins, manual naval limits, question history, plan progress, and feedback stay in `localStorage`. Desktop-only modules (`capture.py`, `tray.py`, `route_window.py`, `server.py`) are excluded from `dist-web/`.
- **Pyodide runtime note:** The Web Worker loads pinned Pyodide `v0.27.5` from jsDelivr CDN (`static/web-worker.js`) for local `.sav` parsing (compressed saves up to 50 MB / 120 MB uncompressed in browser mode). For strict offline or self-hosted deployments, mirror the Pyodide `v0.27.5` assets on your own origin and update `PYODIDE_INDEX`.
- **No copyrighted game assets:** The static site never bundles Paradox `.dds` icons or localization files.

## Local Build & Preview

```powershell
python scripts/build_web.py
python -m http.server 8080 --directory dist-web
```

Then open `http://localhost:8080`.

## Deploying to GitHub Pages

1. Push this repository to GitHub (`main` branch).
2. In your GitHub repo, go to **Settings → Pages → Build and deployment → Source** and select **GitHub Actions**.
3. The included workflow [.github/workflows/deploy-web.yml](../.github/workflows/deploy-web.yml) runs the full Python + JS test suite, builds `dist-web/`, and publishes to GitHub Pages on every push to `main`.

## Future Auto-Update Path

If player feedback shows strong demand for background system-tray monitoring or cross-browser live watching, the existing Windows desktop app (`StellarisGuide.exe`) remains fully compatible and shares the same `stellaris_guide` rules engine.
