# Stellaris 4.5 "Cygnus" knowledge base

Compiled 20 October 2026 by the Claude advisor thread for the Stellaris Guide project. **Second pass (same day)** re-verified every guideline against the full text of the sources after network access was opened. Target game version: **4.5.2 "Cygnus" (checksum 9776)**. Nothing in the existing `Stellaris-Dashboard/` project was modified; this folder is the only output.

## How to use this knowledge base

Each guideline is a short rule the advisor (or the builder agent) can apply to player advice. Every rule carries:

- **Source tags** such as `[R452]` or `[G3]`, resolved in [00-sources.md](00-sources.md).
- **A confidence label**, so the builder agent knows whether to encode it as a rule, a hint, or not at all.

| Label | Meaning | How the Guide should use it |
| --- | --- | --- |
| **OFFICIAL-FINAL** | In shipped 4.5.0 / 4.5.1 / 4.5.2 release notes, or the wiki's copy of them. | Safe to encode as a rule, still checked against installed game files. |
| **OFFICIAL-PRELIM** | In a dev diary or beta note only, not seen in final notes. | Encode only after checking the installed 4.5.2 game files. |
| **WIKI** | A Stellaris Wiki mechanics page marked as verified for 4.5 (some sections say "last verified 4.3"). | Good for formulas and thresholds; check the section's own version note. |
| **COMMUNITY-4.5** | A community guide that says it checked 4.5.x game files. | Use as a hint or explanation. Numbers must be checked in game files. |
| **COMMUNITY-OLD** | A community guide that predates 4.5 or rests on older testing. | Background only, no numbers. |
| **PLAYER-REPORTED** | Experience posted by players in Steam discussions after 4.5 released. | Use as a warning or tip ("players report…"), never as a rule. |
| **CONFLICT** | Sources still disagree after the second pass. | Don't show a number until it is read from game files. |

## How the sources were read

| Source | Access in the second pass |
| --- | --- |
| Official dev diaries, beta notes, 4.5.0 / 4.5.1 / 4.5.2 release notes | **Full text** from Paradox's official Steam news feed (same posts as the forum) |
| Stellaris Wiki (patch pages and mechanics pages) | **Full text** through a browser |
| gamerofpassion.com guides | **Full text**, with publish and modified dates |
| GitHub repos and github.io sites | **Full text** |
| Steam discussions (player experience) | **Full text** of 4.5-era threads |
| forum.paradoxplaza.com and reddit.com | **Not read.** Both sites actively block automated access, so the forum's player threads and Reddit were not used. The official forum posts are covered by their Steam copies. |

The first pass worked from search summaries. The second pass corrected those where the full text disagreed; every correction is listed in [11-conflicts-and-stale-content.md](11-conflicts-and-stale-content.md).

## Files

| File | Topic |
| --- | --- |
| [00-sources.md](00-sources.md) | Source registry with access method, dates and reliability |
| [01-version-baseline.md](01-version-baseline.md) | Release timeline, checksums, what shipped in which patch, what was pulled |
| [02-pops-factions-ethics.md](02-pops-factions-ethics.md) | Pop Group rework, factions, ethics attraction |
| [03-economy-planets.md](03-economy-planets.md) | Economy, planets, jobs, automation buildings, Arc Furnace, AI economy lessons |
| [04-military-ships-fleets.md](04-military-ships-fleets.md) | Fleet Doctrine and preference policies, ship design, fleet composition, titans, transports, starbases |
| [05-diplomacy-federations-war.md](05-diplomacy-federations-war.md) | Federation laws, war joining, occupation, subjugation, revolts |
| [06-ascension-traditions-species.md](06-ascension-traditions-species.md) | Ascension perks, Consecrated Worlds, paths, cybernetics, Hedonists |
| [07-nomads.md](07-nomads.md) | Nomadic empires, Arkships, Waystations, Operational Reserves |
| [08-exploration-precursors-guardians.md](08-exploration-precursors-guardians.md) | Precursors, The Doorway, Leviathans, Enigmatic Fortress, Hyper Relays |
| [09-endgame-crises-fallen-empires.md](09-endgame-crises-fallen-empires.md) | Fallen Empires, War in Heaven, Contingency, dangerous technology |
| [10-tools-and-data-sources.md](10-tools-and-data-sources.md) | The referenced GitHub tools and asset or tech-tree resources, and what to reuse |
| [11-conflicts-and-stale-content.md](11-conflicts-and-stale-content.md) | Corrections from the second pass, remaining conflicts, pre-4.5 risks |
| [12-player-reported.md](12-player-reported.md) | What players report after 4.5 shipped, from Steam discussions |
| [13-dlc-and-subscription.md](13-dlc-and-subscription.md) | What is base game in 4.5, which features need which DLC, the Expansion Subscription, and how the Guide should detect DLC |

**DLC rule for every file:** a guideline about a DLC feature applies only when that DLC is in the campaign's `required_dlcs`. See file 13 for the map.
