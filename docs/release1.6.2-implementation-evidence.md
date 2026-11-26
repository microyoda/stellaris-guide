# Stellaris Guide v1.6.2 implementation evidence

## Decision

Installed Stellaris 4.5.2 defines Xeno Diplomacy with Federation Code as its direct prerequisite. Federation Code has its own earlier dependency chain. The route page therefore lists direct prerequisites separately, shows only the unresearched earlier chain in the map, and visually emphasizes the edge entering the selected goal. A researched dependency stops upstream traversal. A researched target shows two dependency links forward as possible paths, with draw and DLC limitations disclosed.

## Verification

| Check | Result |
| --- | --- |
| Focused route tests | 32 passed, including researched-parent cutoff, downstream alternatives, missing/present DLC, and researching/on-card state in an alternative detail panel. |
| Full source tests | 110 Python tests passed with one skipped. All three JavaScript suites and route-script syntax passed. |
| Installed game audit | 677 routes checked against direct prerequisite definitions: zero mismatches. Marking each target's direct parents researched yielded zero unexpected upstream nodes across 677 routes. 121 routes remained limited because the synthetic save listed no required DLC. |
| Browser check | Isolated source server with copied synthetic 4.5.2 save. Illustrated downstream cards displayed for researched Starbase Construction; selecting Starport opened its route. Xeno Diplomacy detail identified only Federation Code as its direct prerequisite, while the map labelled the earlier unresearched chain. Incoming goal edge is emphasized; upstream edges are subdued. |
| Windows ZIP | `dist/StellarisGuide-Windows-1.6.2.zip` built on Windows. ZIP integrity passed (`testzip` returned none). 13 allowlisted files: EXE, installation and release notes, dependency licenses; no saves, screenshots, keys, logs, or JSON data. Size 21,222,451 bytes. SHA-256 `c488adf94b2cfbf084ad842d669b4b9264ce690bddb2dfde0ee25e288f7ca72f`. |
| Extracted package smoke | The extracted v1.6.2 EXE ran with a separate local profile and copied synthetic 4.5.2 save. `/`, `/app.js`, `/fleet.js`, `/api/state`, `/tech-route.html`, and `/tech-route.js` returned 200; the state reported app version 1.6.2. Its route API showed one- and two-step cards after researched Starbase Construction, navigated Starport to its direct requirement, and identified Federation Code as Xeno Diplomacy's sole direct requirement. Installed technology artwork returned PNG 200. Fleet-limit stale campaign rejection, save, reload, clear, and Quit passed. All isolated package test processes were shut down; the v1.6.1 ZIP remains present. |
| Independent review | Reviewer found an alternative prerequisite state error in the source map detail and a gap in packaged Tech Tree smoke coverage. Both were corrected and verified. Final review found no remaining actionable issue or new security impact. |

## Release gate

All v1.6.2 release checks passed. The prior v1.6.1 release remains available separately.
