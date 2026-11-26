# Corrections, conflicts and pre-4.5 risks

## Corrections made in the second pass (full text vs first-pass search summaries)

| # | First pass said | Full text shows | Source |
| --- | --- | --- | --- |
| X1 | Armor upkeep cut was in DD433 (4.5.0) | **4.5.2 only.** Not in DD433 or the 4.5.0 wiki page | R452, W2 |
| X2 | Maulers 160 → 140 speed in DD433 | **4.5.2, "slightly slower", no number published.** The 160/140 figures had no official source | R452 |
| X3 | Operational Reserves Conserve change in DD433 | **4.5.2** | R452 |
| X4 | Franchising subjugation change in DD433 | **4.5.2** | R452 |
| X5 | Pilot Project Cyborg-only in DD433 | **4.5.2**, with values +15% Elites / +7.5% Specialists / +10% Workers / +5% all | R452 |
| X6 | Cybernetic +10% timing unclear | **4.5.0** (DD433 lists both the +5% feature and the 5% → 10% balance line) | DD433, W1 |
| X7 | Arc Furnace switching only in beta | **Shipped**: 4.5.0 notes fix the Smelting tab and retooling | DD430, W1 |
| X8 | FE awakening thresholds conflict (70k vs 90k) | **Resolved:** wiki confirms 70k; 90k came from a mod | W-FE |
| X9 | Precursor guide published "one day before 4.5.0" | Correct, but **updated 18 Oct 2026** | G5 |
| X10 | Fleet composition guide is a 4.5 guide | **First published 2021**, updated 14 Oct 2026, compositions from 4.3/4.4 testing | G3 |
| X11 | Consecrated Worlds guide is new | **First published 2023**, rewritten for 4.5 | G1 |
| X12 | tuttu assets site unknown | Covers up to Shadows of the Shroud (4.3) only | R6 |

## Remaining conflicts

| # | Topic | Conflict | Resolution for the Guide |
| --- | --- | --- | --- |
| C1 | Consecrated Worlds amenities | Official notes: +10/20/40%. Guide (claims 4.5.1 files): +5/10/20% | Read the `Consecrated World Worship` modifier from installed files |
| C2 | War in Heaven second awakening timing | Wiki: 50% within a decade. Guide: mean ~5 years | Don't show a timing |
| C3 | "4.5 did not change weapon or hull stats" (G3) | 4.5.2 changed armor upkeep and Mauler speed | Treat G3 ratios as 4.3/4.4 data |

## Content that may predate 4.5

| Source | Risk | Why |
| --- | --- | --- |
| G16 Dangerous Technology | High | Written October 2021 |
| Older Consecrated Worlds advice anywhere | High | Random tier system removed in 4.5 |
| G3 Fleet composition | Medium | Based on 4.3/4.4 testing |
| G6 The Doorway | Medium | Published before 4.5 |
| G7 Leviathan Traits | Low–Medium | No version stated |
| Wiki Jobs page and parts of Population, FE awakening section | Medium | "Last verified for version 4.3" |
| R1 Overmind meta | High if reused | Locked to 4.4.6 |
| R4 tech data, R6 assets | Medium | No 4.5 / no Nomads coverage |
| "Technological Ascendancy gives flat research" / "Eternal Vigilance gives free platforms" | High | Changed since 4.3 [G2, W-AP] |
| "One titan per 200 naval capacity" | High | Pre-4.3 [G4] |
| "Colony ascension tier = +25%" | High | +10% since 4.3 [G2] |
| Any "Biomorphosis is slow" rule | High | Halved in 4.5.0 |
| Pop advice treating one Pop Group as one ethic/faction | High | 4.5 Pop Group rework |
| "Requires Utopia / Synthetic Dawn / Humanoids" anywhere (incl. G15's Synthetic Dawn note) | High | Base game since 11 May 2026 [13-dlc] |

## Check of the builder's `docs/CYGNUS-4.5-STRATEGY.md`

It agrees on dates, checksums, the Pop Group rework, preference policies, federation laws, war joining and Exclusive Harvesting Rights being pulled, and it correctly puts armor upkeep in 4.5.2. Gaps it could add:

1. The 4.5.0 balance list (Biomorphosis, Cybernetic +10%, Hedonist rules, short-range station weapons, missile defenses vs PD, Consecrated Worlds).
2. 4.5.2's Conserve, Mauler, Pilot Project values and Experiment Engineer changes.
3. 4.5.1's disabled auto-disengage and fixed fleet automation.
4. The occupation rule (a starbase is needed for full occupation).
