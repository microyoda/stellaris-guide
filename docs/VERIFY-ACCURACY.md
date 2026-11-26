# How to Confirm Stellaris Guide Accuracy

Stellaris Guide separates **save facts**, **game-file rules**, and **strategic playbooks** so you can verify every recommendation objectively instead of trusting guesswork.

## 4-Step Accuracy Verification Protocol

### Step 1: Same-Date Save vs. In-Game Screen Check (2 minutes)
Open your campaign in Stellaris right after an autosave, then run:

```powershell
python scripts/verify_guidelines.py --save "C:\Users\<you>\Documents\Paradox Interactive\Stellaris\save games\<campaign>\autosave_YYYY.MM.DD.sav"
```

Compare the printed JSON against Stellaris's live UI on that exact date:
- **Top bar:** Monthly net & stock for Energy, Minerals, Food, Consumer Goods, Alloys, Trade, Unity, Influence, Fleet Power, Starbases, Empire Size.
- **Colonies:** For each planet, verify Stability, Free Amenities, Free Housing, and Pops match the Colony view.
- **Profile & DLCs:** Confirm `active_dlcs`, `authority`, `is_gestalt`, `is_nomad`, and `shipset_kind` match your actual empire.
- **Red flag rule:** If any parsed number drifts from the in-game screen (e.g., after a patch like 4.6), treat the rule as `needs recheck` and log the fixture diff before trusting recommendations.

### Step 2: Installed Game-Files Audit (Rules Accuracy)
Verify every playbook's release, checksum, and cited `common/` game files directly against your Steam installation:

```powershell
python scripts/verify_guidelines.py --game-dir "C:\Program Files (x86)\Steam\steamapps\common\Stellaris"
```

This checks:
1. Installed Stellaris version & checksum vs. each playbook's `validated_release` / `validated_checksum`.
2. Whether every cited `common/...` file still exists in your installed game.
3. Key constants in `common/defines/00_defines.txt` (such as Market fee and storage caps).

### Step 3: Three-Fixture Playbook Promotion Gate (Strategy Accuracy)
Before changing any playbook in `stellaris_guide/playbooks.json` from `strategy_status: "untested"` to `"tested"`:
1. **Fitting fixture:** Save where the advice clearly applies → verify the goal, steps, and in-game check are legal and helpful.
2. **Non-fitting fixture:** Save where the condition is false (or required DLC is absent / different empire type like Machine or Nomad) → verify the playbook is **not** shown.
3. **Missing-data fixture:** Save omitting an optional field → verify it degrades honestly to `investigate` / `Unknown` rather than guessing.

### Step 4: Export the Complete Web Tech Graph (Optional, Recommended after Patches)
The hosted Web app ships a core ~95-tech progression graph in `stellaris_guide/tech_graph.json`. Whenever a major patch lands (e.g., 4.6 Corona Borealis), regenerate the full 600+ tech structural graph directly from your installed Stellaris folder (IDs, tiers, prerequisites, DLC triggers only — zero copyrighted art or flavor text):

```powershell
python scripts/verify_guidelines.py --game-dir "C:\Program Files (x86)\Steam\steamapps\common\Stellaris" --export-tech-graph
python scripts/build_web.py
```

Push `stellaris_guide/tech_graph.json` to `main` and GitHub Actions will automatically test and redeploy the updated web app.
