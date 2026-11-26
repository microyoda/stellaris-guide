# Version baseline: what is "4.5 Cygnus"

## Release timeline

| Build | Date | Checksum | Status | Sources |
| --- | --- | --- | --- | --- |
| 4.5 open beta | 7 Jul – Sep 2026 | bfcc, aa56, e6fd, bc43, … (nine updates) | Beta only; not proof of shipped behavior | DD428, OB2–OB5, DD431, R450 |
| **4.5.0 "Cygnus"** | 22 Sep 2026 | **8697** | Shipped | R450, W1 |
| 4.5.1 hotfix | 24 Sep 2026 | 358e | Shipped | R451, W2 |
| **4.5.2 hotfix** | 6 Oct 2026 | **9776** | Shipped, current | R452, W2 |
| 4.6 "Corona Borealis" + Willpower | Upcoming | — | **Not Cygnus** | DD435, DD436 |

## Guidelines

1. **Version-gate everything.** The save's version decides which rules apply; don't reuse 4.4 rules without a check. *OFFICIAL-FINAL* [R450]
2. **4.4 saves don't load correctly in 4.5,** and a save opened in 4.5 can't go back to 4.4. Paradox offers a "Stellaris 4.4 Rollback" Steam beta branch. Never compare 4.4 and 4.5 snapshots as one campaign. *OFFICIAL-FINAL* [R450]
3. **Final notes beat diaries.** DD434 (tentative 4.5.2) and beta notes are superseded by R452. *OFFICIAL-FINAL* [R452]
4. **4.5.0 is the largest bugfix patch in Stellaris history:** 525 change lines, 350+ bug fixes, and 46.7% of lines came from player reports. Old "bug-based" tips may no longer work. *OFFICIAL-FINAL* [R450]
5. **Changes that shipped in 4.5.2, not 4.5.0** (the first pass had several of these wrong):
   - Armor upkeep (energy and alloys) set equal to a same-tier shield, down from double.
   - Maulers slightly slower (no number given in the notes).
   - Operational Reserves "Conserve": −50% Specialist Job Efficiency instead of −50% Bureaucrat and Researcher output.
   - Franchising can ignore Opinion, Trust and Embassy requirements for Subjugation.
   - Pilot Project bonuses only for Cyborg pops: +15% Elites, +7.5% Specialists, +10% Workers, +5% all.
   - Defense platforms get their own weapon and defense preference policies; Nomads get Arkship weapon and Waystation defense preferences instead of starbase ones; starting Doctrine and preferences are randomized toward empire defaults.
   - A revolt backed by another empire joins that empire.
   *OFFICIAL-FINAL* [R452, W2]
6. **4.5.1 changes:** a Nomad-built Synaptic Lathe in another empire's system keeps its owner; fleet automation now follows the options you pick; the new "auto-disengage after 15 days without combat" rule was **disabled** until it is made less aggressive. *OFFICIAL-FINAL* [R451]
7. **Content opened to Nomads in 4.5:** Cosmogenesis ambition (The Machine Age), Knights of the Toxic God origin (Toxoids), Storm Chasers origin (Cosmic Storms). *OFFICIAL-FINAL* [R450]
8. **Did NOT ship:** Exclusive Harvesting Rights (pulled for more balancing, expected later); summer experiments from DD429; 4.6 Ideologies. Never recommend them. *OFFICIAL-FINAL* [DD433, R450, R451 (Harvesting Agreements automation setting removed "since the Trade Action has been removed")]
9. **Other 4.5.0 headline features:** empire map/ship colors chosen independently; native Apple Silicon build. Not advice-relevant. [R450]
