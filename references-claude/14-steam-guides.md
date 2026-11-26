# Steam Community guides (crawled 21 October 2026)

Source: https://steamcommunity.com/app/281990/guides/ . Steam's robots.txt allows guide pages. Pages were fetched with 8–10 s between requests; Steam still rate-limited a burst, so the rest were fetched slowly and one stayed blocked (SG20).

## How the guides were chosen

1. Collected 280 guide ids from the "most recent", "trending" and "top rated" lists.
2. Read the created and updated dates of every guide from Steam's official file-details API (`ISteamRemoteStorage/GetPublishedFileDetails`), not from the page text.
3. **Only 1 of the 280 guides was updated after 4.5.0 shipped (22 Sep 2026) and covers gameplay: SG1.** Most of the list is older than 4.4, so it was skipped.
4. Read 19 guides that were updated during Nomads (4.4, from June 2026) or 4.5, plus the two most-favorited combat guides. Guides that were only translations, jokes, single-mod manuals or achievement checklists are listed but not mined.

**Labels** are the same as in the README. Where a guide says "4.5" but was last edited *before* 22 Sep 2026, it is marked **COMMUNITY-4.5-BETA**: it was written from the open beta or from expectations, not from the shipped game.

## Guide registry

| Tag | Guide | Author's stated version | Created → updated | Favorites | Label |
| --- | --- | --- | --- | --- | --- |
| SG1 | [Stellaris 4.5: Билдостроение ВСЕГО флота](https://steamcommunity.com/sharedfiles/filedetails/?id=3741526842) (RU, fleet builds and combat mechanics) | 4.5 | 12 Jun → **18 Oct 2026** | 407 | COMMUNITY-4.5 |
| SG2 | [Baby's First Stellaris Ships 4.5 Cygnus](https://steamcommunity.com/sharedfiles/filedetails/?id=2756897616) | 4.5 | 2022 → 10 Sep 2026 | 1,702 | COMMUNITY-4.5-BETA |
| SG3 | [Stellaris: Space Warfare Explained](https://steamcommunity.com/sharedfiles/filedetails/?id=3343565160) | marked outdated by its author | 2024 → 24 Jun 2026 | 763 | COMMUNITY-OLD |
| SG4 | [How to vassalize the entire galaxy](https://steamcommunity.com/sharedfiles/filedetails/?id=3790727683) | none (4.4) | 26 Aug 2026 | 0 | COMMUNITY-OLD |
| SG5 | [Steps to unlock Defenders of the Galaxy achievement](https://steamcommunity.com/sharedfiles/filedetails/?id=3772608591) | none (4.4 Nomads) | 27 Jul 2026 | 0 | PLAYER-REPORTED |
| SG6 | [Habitat District Prediction Guide (4.x)](https://steamcommunity.com/sharedfiles/filedetails/?id=3729287020) | 4.x | 19 → 24 May 2026 | 1 | COMMUNITY-OLD (own tests) |
| SG7 | [The Basics of the Resource Market](https://steamcommunity.com/sharedfiles/filedetails/?id=3006299788) | none | 2023 → 30 Jun 2026 | 42 | COMMUNITY-OLD |
| SG8 | [So you want to play the Wilderness!](https://steamcommunity.com/sharedfiles/filedetails/?id=3720047995) | none (4.3/4.4) | 4 → 8 May 2026 | 11 | COMMUNITY-OLD |
| SG9 | [Criminal syndicate shares his secrets](https://steamcommunity.com/sharedfiles/filedetails/?id=3038400685) (multiplayer) | none | 2023 → 7 Jun 2026 | 104 | COMMUNITY-OLD |
| SG10 | [a guide to ethics](https://steamcommunity.com/sharedfiles/filedetails/?id=3682924445) | none | 13 Mar → 5 Oct 2026 | 3 | COMMUNITY-OLD (stale DLC note) |
| SG11 | [Why Stellaris Multiplayer Says Game Version Differs](https://steamcommunity.com/sharedfiles/filedetails/?id=3725626398) | none | 13 May 2026 | 1 | COMMUNITY (tool advert) |
| SG12 | [Mod Load Order – A deception broken into pieces](https://steamcommunity.com/sharedfiles/filedetails/?id=2290164696) | none | 2020 → 12 Oct 2026 | 878 | COMMUNITY (modding) |
| SG13 | [【Stellaris 4.5.0】各Modの紹介と、互換性のメモ](https://steamcommunity.com/sharedfiles/filedetails/?id=2874656750) (JP, mod compatibility notes) | 4.5.0 | 2022 → 22 Sep 2026 | 43 | COMMUNITY (modding) |
| SG14 | [【Stellaris Ver4.5.0】今使っているMOD](https://steamcommunity.com/sharedfiles/filedetails/?id=2761231737) (JP, mod list) | 4.5.0 | 2022 → 22 Sep 2026 | 104 | Listed only (page is images) |
| SG15 | [How to FIX Gigastructural Engineering & More (WORKING 4.5)](https://steamcommunity.com/sharedfiles/filedetails/?id=3822157588) | 4.5 | 18 Oct 2026 | 0 | Not useful (a joke: delete one loading screen) |
| SG16 | [Stellaris 4.3: Билдостроение ВСЕГО флота (гайд устарел)](https://steamcommunity.com/sharedfiles/filedetails/?id=3595403016) | 4.3, marked outdated | 2025 → 13 Sep 2026 | 526 | Superseded by SG1 |
| SG17 | [Основы (и не только) для начинающих](https://steamcommunity.com/sharedfiles/filedetails/?id=3578197090) (RU, beginner basics) | none | 2025 → 7 Jul 2026 | 244 | Listed only (general basics) |
| SG18 | [群星stellaris全DLC 100%成就指南](https://steamcommunity.com/sharedfiles/filedetails/?id=1589611218) (CN, achievements) | 4.4 | 2018 → 1 Sep 2026 | 1,184 | Listed only |
| SG19 | [How to use planetary automation in 4.3](https://steamcommunity.com/sharedfiles/filedetails/?id=3736237268) | 4.3 | 31 May 2026 | 0 | Not useful (body is "Don't") |
| SG20 | [Stellaris: Space Warfare Explained 2.0 (now with bioships!)](https://steamcommunity.com/sharedfiles/filedetails/?id=3743920059) | 4.4 | 24 Jun → 15 Aug 2026 | 161 | **Not read** (Steam kept rate-limiting this page). Worth a retry. |

## What is worth keeping

### Combat mechanics — SG1 (COMMUNITY-4.5, author's own tests; check numbers in game files)

- **Hit chance = accuracy − max(0, evasion − tracking).** Example: 80% accuracy, 40% tracking vs 90% evasion corvette = 30%. SG3 gives the same rule. [SG1, SG3]
- **Damage order:** a random roll in the weapon's range, then empire bonuses, then the shield/armor modifier, then target damage reduction. Results aren't rounded. [SG1]
- **Shields and armor HP:** components are summed, then multiplied by component bonuses (e.g. shield capacitor +10%), then by empire bonuses. [SG1]
- **Regeneration:** shields regenerate a flat amount per day, five times faster out of combat. Armor regeneration modules are a percentage: in combat (armor × %)/100 per day; out of combat (armor × %)/5. [SG1]
- **Range bonuses scale both minimum and maximum range.** An artillery computer at +20% turns 45–80 into 54–96, so the blind spot grows too. [SG1]
- **Torpedo size bonus** is multiplied by the target's size. SG1 uses naval-capacity sizes: corvette 5, frigate 8, destroyer 10, cruiser 20, battleship 40, titan 80, platform 1, starbase 40, citadels 40/60/80, juggernaut 100, leviathans 250. **CONFLICT C4:** SG2 says sizes 1/2/4 with +100% damage. Read the weapon modifier and hull size from game files before showing a number.
- **Disengagement:** below 50% hull, each hit rolls a chance to leave the battle. The "Hit and Run" doctrine rolls three times per hit. Big hits beat many small hits for actually destroying ships. [SG1, SG3]
- **Emergency FTL** is ready after about 30 days. When it fires, each ship has a 5% chance to be destroyed and a 25% chance of random damage, and the fleet goes missing for a while. [SG3, COMMUNITY-OLD]
- **Ship experience:** 5 XP per day in combat, cap 10,000, rank bonuses at 100 / 1,000 / 10,000. Kills give no extra XP. [SG1]
- **Cloaking:** up to 10 levels; detection comes only from starbase modules. **An empire with enough intel on you sees your cloaked ships regardless of levels.** Bigger hulls take a cloaking penalty; space fauna don't. [SG1]
- **Splash damage:** titan T-slot 500 in radius 40 (matches G4); ion cannon T-slot 100 in radius 20; Nomad Arkship main gun 750 in radius 50. [SG1]
- **Strike craft:** each hangar launches 2 craft per day, and lost craft refill slowly. **More hangars beat bigger hangars.** Launched craft keep fighting at any distance. [SG1]
- **Point defense vs flak:** in the author's tests flak shot down missiles and torpedoes as well as point defense did, and also hit strike craft, so they call point defense "junk". Targeting order: flak goes craft → missiles → ships; PD goes missiles → craft → ships. [SG1, PLAYER-REPORTED test]
- **Fleet power is not a combat predictor.** Counters decide fights. [SG1, SG3]
- **AI pathing:** the AI avoids a system when your starbase plus citadels out-power its fleet. Crises ignore this. [SG1, PLAYER-REPORTED]

### 4.5-specific claims — SG1 vs official notes

| Claim | In official notes? | Label |
| --- | --- | --- |
| Ancient Bastion starbase module silently nerfed from +20% to **+15%** armor per module in 4.5 | **No.** Not in DD433, R450, R451 or R452 | PLAYER-REPORTED. Read the module from 4.5.2 files |
| Space fauna fleets "broken again" in 4.5; old fauna builds no longer work | Partly. **4.5.2 changed fauna mutations** (Ancient Suspension Epidermis, Ancient Energized Carapace, Null Void Epidermis; Archaeo-Engineers now add flat shields) [R452] | COMMUNITY-4.5, consistent with R452 |
| The space fauna designer sometimes swaps the chosen combat computer to "Swarm", even on upgrade | No | PLAYER-REPORTED bug. Tell fauna players to check built ships |
| Cordyceptic Drones' +50% damage and fire rate does apply to fauna though the tooltip doesn't show it | No | PLAYER-REPORTED |
| Starbase setup: prefer shields and energy weapons in starbase preference policies; 6× Ancient Bastion late; hangars early for range; ion cannons with Ancient Disruptive Gaze; keep citadels apart from the starbase to avoid splash damage | Starbase preference policies are official [DD433, R452] | COMMUNITY-4.5 advice |
| Cruisers and frigates are niche since 4.3 (starbase and leviathan killers); nanite missiles are only decoys since 4.3 | No | COMMUNITY-4.5 opinion |

### Ship meta — SG2 (COMMUNITY-4.5-BETA, written before 4.5 shipped)

- Author's "4.5 meta (with DLC)": X slots Lances; L slots Kinetic Artillery; mostly **cruisers with a hangar core**, some torpedo cruisers; flak in the hangars' P slots; defenses **all armor but one**; afterburners in auxiliary slots. One cloaked small-ship fleet to ambush or soak the first volley. [SG2]
- **Stripping weapons from starting ships no longer saves upkeep.** [SG2]
- Missiles and disruptors were "nerfed hard" and are weak late game; shield/armor bypass was nerfed in 4.4. [SG2]
- Fit ships for corvettes as well: kinetic + energy gunships, flak screens, mixed hulls for players who don't micromanage; mono-hull fleets for players who do. [SG2]
- Titan auras: Shield Dampener on the titan and Target Acquisition Array on a juggernaut; Quantum Destabilizer vs armor-heavy crises. Titans and Colossi need **Apocalypse**; juggernauts need **Federations**. [SG2, SG3]
- **Fit with 4.5:** "armor everywhere" agrees with the 4.5.2 armor upkeep cut [R452]. Specific weapon tiers aren't confirmed by official notes; treat them as a hint.

### Economy, planets and diplomacy

- **Habitat districts (SG6, own tests):** max districts per type = floor(number of deposits + sum of deposit values / 2), using **base** deposit values (remove station bonuses first). Zro, Living Metal, Unity and Dark Matter count as a deposit with value 0 (one research district each, no sum). Volatile Motes and Exotic Gases count as zero-value energy deposits. Trade and alloy deposits didn't count in a Hive Mind test. The guide also lists station-output bonuses with their DLC (Void Mining: Grand Archive; Astro-Mining civic: MegaCorp; Ice Mining Station: Aquatics). COMMUNITY-OLD; verify against 4.5 files, since 4.5 changed planet districts (Dimensional Manipulator 5 districts; see file 03).
- **Market (SG7):** base prices are energy, minerals and food 1, consumer goods 2, alloys 4, strategic resources 10. Market fee is 30% by default, minimum 5%, maximum 60%; each Trader Proxy Office −5%, Insider Trading or Adaptive Programming −10%, hosting the Galactic Market −10%, sanctions +10% per level. Stable monthly internal trade (before prices move): buy 42 / sell 64 energy, minerals or food; 21/32 consumer goods; 10/16 alloys; 4/6 basic strategic; 2/3 advanced strategic. No 4.5 note changes the market, but read fees from `defines` before using these numbers. COMMUNITY-OLD.
- **Subjects (SG4):** subjugating an overlord hands you its subjects. Overlords get −800 acceptance to diplomatic subjugation. Feudal Society exempts one more subject from Divided Patronage. Hegemony and Martial Alliance federations suit a vassal empire. Specialized subjects and loyalty are **Overlord**; federation types other than the default are **Federations**. COMMUNITY-OLD (4.4).
- **Defender of the Galaxy (SG5, Nomads):** never settle; take the perk (needs three earlier perks, not Fanatic Xenophobe or Inward Perfection); earn Valor through declared crises; become Galactic Custodian for Ambition level 4; at level 5, defeat two end-game crises spawned from the situation log, **one at a time**. The author's Prethoryn Scourge kill didn't count. PLAYER-REPORTED (4.4).
- **Wilderness (SG8):** build one forge world, then agri-worlds; pops are assembled, so skip growth traits; feed Behemoths with stripped-down "food ships"; finish the situation before attacking the final boss. COMMUNITY-OLD.

### Mods, multiplayer and the Guide's own checks

- **"Game version differs" in multiplayer** is usually not the version. In order of likelihood: different mods, different load order, a mod that silently failed to load, corrupt mod files, different DLC, and only rarely a real version gap (right after a patch). Check `Documents/Paradox Interactive/Stellaris/logs/error.log` for mods with critical errors. SG11 then advertises its own Windows tool (NullSync); it was not checked, so don't recommend it.
- **Load order rule of thumb (SG12):** graphics and basic content first; galaxy, traditions, ethics and diplomacy in the middle; big overhauls (Gigastructures) and AI mods near the end; **UI overhauls such as UIOD after everything else**; global patches last.
- **Mod compatibility after a patch (SG13):** mods that replace whole UI files or systems break first and should wait for an update; small, independent mods usually survive a version gap.

## Guidelines for the Guide

1. **Steam guides are mostly old.** Use the Steam file API's `time_updated` to label a guide, and treat anything not updated since 22 Sep 2026 as pre-4.5. A title that says "4.5" doesn't prove it. [this crawl, SG2]
2. **Recommend flak over point defense** when enemies use strike craft or a mix; offer PD only against missile-only enemies. *Player tests, not official.* Refines guideline 5 in file 04. [SG1]
3. **Explain range bonuses and blind spots** when the player designs artillery or defense platforms. [SG1]
4. **Don't treat fleet power as a forecast.** Compare weapon types against enemy shields, armor and evasion instead. [SG1, SG3]
5. **Warn fauna players** that 4.5.2 changed fauna mutations and the fauna designer may swap combat computers. [R452, SG1]
6. **Habitat advice:** estimate districts from base deposits with SG6's rule, labelled as an estimate, and let the in-game tooltip win. [SG6]
7. **On a multiplayer desync or "version differs" question,** check mods, load order and DLC before blaming the version, and point to `error.log`. [SG11]
8. **If the Guide reads the playset,** flag UI overhaul mods and big overhauls as the first suspects after a patch. [SG12, SG13]
