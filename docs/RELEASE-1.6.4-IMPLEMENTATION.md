# Stellaris Guide 1.6.4 implementation and evidence

**Started October 26, 2026.** Scope: the four answer-quality regressions, versioned mechanics knowledge, Tech Tree next-target context and card explanations, and a conditional Fleet Design Finder from [Upcoming release notes](UPCOMING-RELEASE-NOTES.md). Preserve older Windows packages and the running guide. Do not relabel unverified game actions as available.

## Phase gates

| Phase | Deliverable | Acceptance gate | Status |
| --- | --- | --- | --- |
| 0 | Inspect existing code, sources and package process; baseline tests | Existing suite known and v1.6.3 files left intact | Complete |
| 1 | Built-in and optional-model question understanding, selected-save retrieval, small reviewed rules | Four screenshot questions and negative/unknown cases; spoiler and provider fallback checks; independent and security review | Complete |
| 2 | Tech Tree larger downstream paths and plain card explanations | Direct prerequisite path remains exact; benefits are verified or marked unknown; artwork and browser tests; independent review | Complete |
| 3 | Fleet Design Finder with class/goal/target controls and conditional advice | Saved designs distinguished from concepts; no fabricated buildability or enemy loadout; UI and calculator tests; independent review | Complete |
| 4 | Version, documentation, isolated Windows build and smoke | Full test suite, package smoke, accessible UI check, checksum, independent final review | Complete |

Check Codex usage before each new phase. Do not start a phase when the remaining allowance is too low to finish its verification. Changes to chat evidence or spoiler projection require separate security review. Every implementation test set needs success and failure cases.

## Baseline evidence

- The project test suite on Python 3.14 passed **116 tests, one skip** on October 26, 2026 after `TEMP` and `TMP` were directed to the writable workspace. The initial sandbox default temp location denied writes; that environmental failure was resolved without changing product code.
- Current source identifies the root answer issue: `advice.answer_question` uses broad keyword branches and substitutes the first goal for unmatched questions; `economy_answer` is empire-wide even for a named planet; `planet_answer` chooses another colony if the name is missed. The evidence packet has no `spy`/`intel` trigger. See [answer-quality research](BUILT-IN-GUIDE-ANSWER-QUALITY-RESEARCH.md).

## Evidence log

Record each phase's exact tests, UI or packaged checks, reviewer findings, fixes, and unresolved limits here before marking it complete.

### Phase 3 — October 27, 2026

- The Fleet page now starts with a Corvette, Frigate and Destroyer Finder. Goal and player-observed enemy controls feed a qualitative assessment of owned saved designs; auto-designs and unverified Guide concepts are separately named. No numeric combat score, exact cost, verified build badge or hidden enemy loadout is inferred. Unknown cost, movement and screening evidence stays insufficient even when enemy information is entered. The selected policy explanation names the recorded settings and asks the player to verify their effect in Ship Designer.
- The candidate list is visible by default; detailed comparison opens on demand. Controls restore keyboard focus after a selection. Hull artwork retains the labelled fallback. The running older release and existing packages were not changed.
- Verification: `node --check static/fleet.js`, `node tests/test_v164_fleet_finder.js`, `node tests/test_v161_fleet.js`, and the full Python suite: **131 tests passed, one skipped**. Tests cover suitable and blocked saved designs, tied choices, unknown goals, enemy defense and weapon changes, mod/version uncertainty, policy changes, spoiler isolation, keyboard focus and comparison controls. Independent review found candidate ordering, mixed weapons, opponent selection, policy, focus, arbitrary default ranking and unsupported-goal issues; fixes passed a final read-only review. Separate security review found no actionable issue; existing backend tests cover spoiler projection. Browser and packaged Windows smoke remain Phase 4 gates. An isolated local preview server was stopped after the sandbox denied loopback access, so no visual pass is claimed for Phase 3.

### Phase 4 — October 27, 2026

- Updated the app badge, API version, Windows installer instructions, README, release notes, build script and package manifest to **1.6.4**. Built `dist/StellarisGuide-Windows-1.6.4.zip` separately from the existing v1.6.3 package. The ZIP integrity test passed and its 13 entries are the executable, player guides and dependency notices; no save, config, key, screenshot or log is inside.
- Verification: **131 Python tests passed, one skipped**; all five Node UI test files passed; JavaScript syntax checks passed. The extracted Windows EXE ran with a separate local profile and the player's current Stellaris 4.5.2 save. `/`, `/app.js`, `/fleet.js`, `/api/state` and `/api/quit` returned 200; state reported 1.6.4 and the selected save date **2331.10.01**. The final package opened in the in-app browser: the badge showed v1.6.4, hull artwork and readable fallback were present, the candidate list was visible in the default desktop viewport, Damage changed the recommendation to the saved auto-design, and detailed comparison opened and closed. The evidence screenshot is `docs/v164-fleet-finder.png`.
- Independent final source/package review found no blocking defect. The separate Fleet Finder security review found no actionable issue and confirmed normal advice uses player-owned designs and spoiler-filtered contacts. All isolated v1.6.4 processes and browser tabs were closed after testing; two older v1.6.3 processes remained running. SHA-256 of the final ZIP: `B19F90DB7FACC54C1DA30AD48F0C541532E9AD180853F7B1359173E5C8132AE5`.

### Phase 1 — October 26, 2026

- The four screenshot questions route by topic and named subject; unmatched colonies and empires ask for the exact name. Espionage how-to, intel status, and operation decisions have distinct answers. A missing target never substitutes another contact or the top campaign goal.
- Optional chat packets include only relevant records and player fields. A missing named contact contributes no unrelated empire record. AI output rejects unsupported numbers, unknown record references, instruction-like text and selected off-topic answers. These checks reduce risk; they cannot prove every nonnumeric strategy claim.
- A small versioned rule catalogue provides conditional how-to steps. Malformed records fail closed, and required DLC plus installed release must match before a rule can be labelled version checked.
- Verification: `python -m unittest discover -s tests -q` with workspace `TEMP` and `TMP`: **127 tests passed, one skipped**. The first independent review identified non-Prime colony, espionage decision and missing contact gaps; the second review found those fixed. Separate security review confirmed spoiler projection precedes chat and provider data minimization, and identified residual narrative grounding risk, addressed with adversarial name tests and conditional wording. Reviewers' own full runs were limited by their sandbox temp directory; the author run used the writable workspace temp directory.

### Phase 2 — October 26, 2026

- Tech routes retain exact direct prerequisites and now expose up to five bounded downstream dependency links. Each possible future target shows its chain, other known requirements, DLC across the full chain, current tier condition and a draw/mod caveat; choosing a card opens that target's own route. Existing one or two links after a completed technology remain separately labelled.
- Cards use installed English game descriptions when they can be resolved safely, plus a verified dependency benefit. When no specific effect can be established, the page says so. Artwork still comes from the installed game with a visible fallback.
- Verification: **131 Python tests passed, one skipped**; the new route UI component test passed under Node and `node --check static/tech-route.js` passed. A separate loopback preview opened the player's selected Cygnus 4.5.2 save in the in-app browser: Cruisers displayed artwork, explanation, future cards, and the saved route; selecting Battleships opened its exact route and direct Cruisers prerequisite. The temporary preview was closed; the older release was left running. Independent review identified distance ordering, chain-wide DLC, modded tier certainty and already-offered-card risks; tests and fixes cover all four. The release header still displays the older version until Phase 4 packaging.
