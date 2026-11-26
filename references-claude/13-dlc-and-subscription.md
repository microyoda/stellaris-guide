# DLC, subscription and base game: how they change advice

Players own different DLC, and some only have it while their **Expansion Subscription** is active. Advice that names a DLC feature the player can't use is wrong advice. This file lists what is base game in 4.5, which features each DLC gates, and how the Guide should check.

## 1. What is base game now — *OFFICIAL-FINAL*

- **On 11 May 2026, Utopia, Synthetic Dawn, the Humanoids Species Pack and most of the Galaxy Edition became part of the base game** for every PC player (the base price rose by $10). That means **Hive Minds, Machine Intelligences, and all Utopia features (megastructures such as Ring Worlds, Dyson Spheres and Habitats, plus the classic ascension paths)** are base game now. [Utopian Abundance post, 19 Mar 2026; DD418, 29 Apr 2026 — Steam feed]
- The Steam store's DLC list no longer includes those three packs (checked 20 Oct 2026). [Steam store API]
- **Custodian updates (like 4.5 Cygnus) are free.** The Pop Group rework, faction changes, Fleet Doctrine and preference policies, federation economic laws (see the caveat below) and AI changes are all in the free update. [R450]
- **Stale-content flag:** any guide that says "requires Utopia" or "requires Synthetic Dawn" is now outdated. G15 (Contingency) still says the crisis "is slightly different if you have the Synthetic Dawn DLC enabled"; for 4.5 every player has it.

## 2. Expansion Subscription — *OFFICIAL (store page)*

- $9.99 per month on Steam; gives access to all expansions, story packs and species packs, plus future content on day one, while subscribed. Requires the base game. [Steam store, app 2729490]
- **Inferred (verify):** a campaign started with subscription content lists those DLC in the save. If the subscription lapses, the player may lose access to that content and may not be able to continue that save normally. The Guide should treat a subscriber's DLC set as "may change between sessions".

## 3. Current DLC list (Steam store, 20 Oct 2026)

| Released | DLC | Type |
| --- | --- | --- |
| 2016 | Plantoids, Leviathans | Species pack, Story pack |
| 2017–2018 | Anniversary Portraits, Apocalypse, Distant Stars, MegaCorp | Free portraits, Expansion, Story pack, Expansion |
| 2019–2020 | Ancient Relics, Lithoids, Federations, Necroids | Story pack, Species pack, Expansion, Species pack |
| 2021–2022 | Nemesis, Aquatics, Overlord, Toxoids | Expansion, Species pack, Expansion, Species pack |
| 2023 | First Contact, Galactic Paragons, Astral Planes | Story pack, Expansion, Narrative expansion |
| 2024 | Expansion Subscription, Rick the Cube, The Machine Age, Cosmic Storms, Grand Archive | Subscription, Portrait, Expansion, Expansion, Story pack |
| 2025 | Stargazer, BioGenesis, Shadows of the Shroud, Infernals | Portrait, Expansion, Story pack, Species pack |
| 2026 | Vipra the Vapor, Season 10 pass, **Nomads** (15 Jun) | Portrait, Pass, Expansion |
| Coming | Willpower, Scenario Pack 1, Scenario Pack 2 (4.6) | Not Cygnus |

## 4. Features in this knowledge base that need a DLC

**Sourced** = the requirement is stated in an official note or a full-text guide. **Inferred** = from general game knowledge; verify in game files before encoding.

| Feature (file) | DLC | Basis |
| --- | --- | --- |
| Nomadic empires, Arkships, Waystations, Waylines, Wayline Pacts, Arkship/Waystation preference policies (07, 04) | Nomads | Sourced [R450, DD433, G13] |
| Defender of the Galaxy as an ambition; Stellar Cannon megastructure; Wanderlust perk | Nomads | Sourced [Nomads release post, G2] |
| Cosmogenesis for Nomads / Knights of the Toxic God / Storm Chasers | The Machine Age / Toxoids / Cosmic Storms | Sourced [R450] |
| Enigmatic Fortress, Space Dragons and their traits, **War in Heaven** (08, 09) | Leviathans | Sourced [G11, G14, G7] |
| Titans (Titans tech, Perdition Beam), Colossus Project, Enigmatic Engineering, Nihilistic Acquisition (04, 06) | Apocalypse | Sourced [G2, G4] |
| Arcology Project, Xeno-Compatibility, Matter Decompressor (06) | MegaCorp | Sourced [G2] |
| Franchising civic (05) | MegaCorp | Inferred (corporate civic) |
| Hyper Relays, Lord of War (08) | Overlord | Sourced [G12, G2] |
| Zroni and Baol precursors, Archaeostudies-gated content (08) | Ancient Relics | Sourced [G5, G2] |
| Galactic Nemesis | Nemesis | Sourced [G2] |
| Mechromancy, Reanimators (08) | Necroids | Sourced [G7, G2] |
| Thermophile species, Galactic Hyperthermia | Infernals | Sourced [G1, G2] |
| Synthetic Queen crisis, Machine Age Synthetic path variant, Arc Welders, Cybernetic Creed | The Machine Age | Sourced in part [G15, G2]; origins inferred |
| Hydrocentric perk, Ocean worlds for Aquatics | Aquatics | Sourced [G2] |
| Cosmic storms content | Cosmic Storms | Sourced [G2] |
| Bioships | BioGenesis | Sourced [G12] |
| Automation-focused civic (Corporate Thinktank variant) | Shadows of the Shroud | Sourced [G10] |
| Federation types other than the basic one, federation laws, Galactic Community depth | Federations | **Inferred.** Whether the 4.5 Federation Economic Laws need Federations DLC is not stated anywhere read. Check `potential` on the laws in game files |
| Cloaking / Ambush-style stealth doctrine content | First Contact | Inferred |
| Astral rifts | Astral Planes | Inferred |
| Grand Archive, space fauna and mutations | Grand Archive | Inferred |

## 5. How the Guide should detect DLC

The builder's code already reads `required_dlcs` from the save's `meta` (`saves.py:813`), lists them as evidence in chat (`chat_evidence.py:73`, with the note that they "do not prove the active playset"), and marks tech routes "limited" when a required DLC is missing (`tech_route.py:184–282`). Suggested refinements:

1. **Per campaign, `required_dlcs` is the best evidence.** Content from a DLC missing from that list was most likely not generated in that galaxy (no Enigmatic Fortress, no War in Heaven), even if the player owns the DLC now. *Inferred; verify with one save started with a DLC disabled.*
2. **Owning ≠ enabled.** The launcher's `dlc_load.json` can also list disabled DLC (the code reads only `enabled_mods`). *Inferred; check the file on the player's PC.*
3. **Multiplayer uses the host's DLC** for galaxy content. Label advice "based on this save's DLC list". *Inferred.*
4. **Read DLC gates from the installed game files** instead of a hard-coded table: `potential` / `possible` blocks with `has_*` DLC triggers or `host_has_dlc`. `tech_route.py:162` only matches triggers written as `has_<name>_dlc`; **some vanilla DLC triggers may not use the `_dlc` suffix** (for example names like `has_megacorp` or `has_ancrel`), and the substring match against labels like "Ancient Relics Story Pack" would miss an abbreviated trigger. *Inferred risk; list the `has_*` triggers in `common/scripted_triggers/` and test each against a real `required_dlcs` list.*
5. **Utopia, Synthetic Dawn and Humanoids triggers:** since May 2026 these are owned by everyone. Make sure an old `has_utopia`-style check (if it still exists in files) is treated as always present. *Inferred; verify in 4.5.2 files.*
6. **Subscribers:** if `required_dlcs` changes between saves of the same campaign, or a save lists DLC the installed game doesn't have enabled, show "DLC set changed; some advice may not apply".

## 6. Advice rules

1. **Never recommend a DLC-gated action unless that DLC is in the campaign's `required_dlcs`.** If unknown, show the action with "needs <DLC>". [this file]
2. **Prefer base-game alternatives.** Example: for faster fleet movement without Overlord, suggest Gateways or hyperlane chokepoint defense instead of Hyper Relays; for doomstack anti-corvette work without Apocalypse (no titans), suggest flak/PD destroyers or more cruisers with medium weapons. *Alternatives are community reasoning; label as hints.*
3. **Don't warn about threats that can't exist in that galaxy** (Enigmatic Fortress, War in Heaven, Synthetic Queen) without the matching DLC. [G11, G14, G15]
4. **Never push the player to buy DLC.** At most, mention that an option exists "with <DLC>" when the player asks.
5. **Treat Utopia, Synthetic Dawn and Humanoids as base game** and flag any source that says otherwise as outdated.
