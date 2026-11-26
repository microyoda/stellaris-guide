# Focused technology route feasibility (v1.6 Phase 5)

## Decision

Extend the Guide's Python technology extractor for a focused, read-only route. Use the MIT-licensed YThibos/Stellaris-Tech-Tree model as a reference for distinct direct prerequisites, one-of conditions, tier gates, granted technology and DLC applicability. Do not bundle its Svelte application, generated game data or assets. This keeps the Windows Guide offline and avoids a Node runtime in the player package.

## Offline probe on installed Cygnus 4.5.2

| Measure | Result | Consequence |
| --- | ---: | --- |
| Base-game technology text files | 33 files, 528,039 bytes | Small enough for bounded local extraction. |
| Technology entries recognized by existing Python extractor | 677 of 677 top-level `tech_*` entries | Existing direct-prerequisite parser can be reused. |
| Entries with a `potential` block | 375 | A direct-prerequisite graph alone cannot establish availability. |
| Simple one-of technology groups found by conservative regex | 3 candidate technologies | One-of groups need a dedicated parser; this is a lower bound, not a complete count. |
| Entries with a literal zero `weight` | 76 candidates | Zero weight is a clue for granted/event technology; modifiers still need checking. |
| Tier definitions | `common/technology/tier/00_tier.txt` present | Tier rules can be read locally. |
| Orbital Rings (`tech_orbital_ring_tier_1`) | Engineering tier 3; three direct prerequisites; `has_overlord_dlc = yes` | Good acceptance case for DLC and tier display. |

The exact 2277.10.01 save has a matching installed 4.5.2 release and one named mod. The launcher playset is currently matched by names only, so its modded technology definitions are **not verified**. A base-game route for this campaign must carry a limited-data warning.

## Architecture and packaging comparison

The upstream TypeScript model distinguishes `prerequisites`, `requiresOneOf`, `availability`, `requiredDlcs`, `tier`, `drawWeight` and `granted` traits. Its extractor reads base-game and ordered mod content layers, and its UI runs through Svelte/Vite. The repository's `package.json` requires Node 22 or later for development and lists runtime packages including `sharp` and `decode-dxt`. Copying the web application would add a second build toolchain and more package and window integration work. The Python extension adds no dependency and reads the player's installed game files; an interim Windows smoke package must still confirm the final size and offline behavior.

The upstream project is MIT licensed (copyright 2026 YThibos). This phase uses its ideas and data model as research only; it does not copy source code or generated game content. If source is incorporated later, preserve its copyright and MIT notice. Do not redistribute Paradox game data or player saves.

## Truth boundary

The route can verify only parsed direct prerequisites, simple one-of `has_technology` groups, tier numbers and named DLC conditions from a matching installed base game. Unparsed availability conditions, random research draws, event grants, effects of mods, and any version mismatch remain Unknown or limited. Save research IDs and current projects come from the Guide's selected campaign, never from a second imported campaign.

## Sources inspected

- `YThibos/Stellaris-Tech-Tree` on GitHub: `LICENSE`, `package.json`, `src/domain/technology.ts`, `src/domain/tech-tree.ts`, `src/domain/tier-gate.ts`, `src/extraction/technology-reader.ts`, `src/extraction/playset.ts`.
- Installed Stellaris 4.5.2 files under `common/technology/`, especially `00_overlord_tech.txt` and `tier/00_tier.txt`.
- Local Guide `stellaris_guide/technology.py`, `stellaris_guide/saves.py` and the exact save, read-only.
