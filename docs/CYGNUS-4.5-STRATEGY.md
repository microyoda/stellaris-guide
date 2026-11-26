# Stellaris 4.5 Cygnus: strategy and dashboard implications

Reviewed 17 October 2026. This is a research summary for Stellaris Guide's next release, not a list of rules already implemented in the dashboard. It prioritizes changes that affect planet, economy, technology, fleet, policy, faction, and diplomacy advice.

## Release status and source order

- **4.5.0 Cygnus shipped on 22 September 2026.** Its release announcement confirms the Pop Group, faction, military policy, federation law, and Nomad AI changes summarized below.
- **4.5.2 Cygnus shipped on 6 October 2026 (checksum 9776).** Its final hotfix notes supersede the tentative 4.5.2 notes in diary #434, especially for military preference policies.
- Diaries #428–#432 describe development and open beta states. Diary #433 provides *preliminary* 4.5.0 notes. An experiment or beta feature is not proof that it shipped.
- **Exclusive Harvesting Rights was removed before 4.5.0** for more balancing work, despite its appearance in diary #430. Do not recommend this agreement as an available Cygnus action.
- Diary #429 explicitly separates summer experiments from the beta changes. Ideas such as flag recoloring experiments should not be treated as shipped mechanics without later confirmation.

## Changes that matter for player advice

| Area | Confirmed Cygnus change or development finding | Implication for Stellaris Guide |
| --- | --- | --- |
| **Save and population data** | 4.5 reworks Pop Groups: a group tracks percentages belonging to ethics and factions instead of splitting into separate groups. The 4.5 release warns that saves from 4.4 and earlier are incompatible. | Version-gate the parser and snapshot history. For faction or planet advice, use actual population shares and trends; do not count each group as one homogeneous ethic/faction. Avoid comparing incompatible 4.4 and 4.5 save structures as if identical. |
| **Factions and ethics** | Ethics and faction attraction have more visible drivers, and their membership changes more readily. Diary #431 describes attraction and supporter change by colony in the UI. | Add a faction indicator only after verifying the 4.5 save fields. Explain *which colony or policy* is driving support or approval. Do not promise a precise conversion rate from a single autosave. |
| **Fleet and research policies** | 4.5 adds Fleet Doctrine and weapon/defense preference policies that steer automated ship designs and technology research. 4.5.2 separates defense platform preferences and adds Arkship/Waystation variants for applicable empires. | Read current military policies before recommending ship designs or a weapon research path. Suggest a policy change only if the empire can select it, and explain how it affects the proposed fleet goal. Never assume the same policy set for settled and Nomad empires. |
| **Federation diplomacy** | Federation laws can grant members automatic Research Agreements or Commercial/Wayline Pacts; some federation types already provide equivalent benefits. | Before suggesting a pact or federation law, check current membership, federation type, law, and existing benefits. Avoid recommending a redundant agreement. |
| **War support** | Diary #430 changed AI willingness to join ongoing wars: it weighs war size, existing wars, opinions and the side being supported; defensive participation is easier to secure than offensive participation. | Treat an ally joining a proposed attack as uncertain. Under a war goal, show what is known about support and advise checking the in-game acceptance screen. Do not turn a friendly opinion into a guaranteed coalition. |
| **Economy and planets** | Beta diaries #429 and #432 describe AI changes around district specialization, economic targets, shortages, and revisiting colony designations. These are AI decision improvements, not automatic player bonuses. | Use them as design lessons for goal-to-action advice: name a viable district or building, check resource upkeep and stockpile runway, re-evaluate planet specialization, and keep housing/amenity needs in balance with production. Validate each suggested action against the player's actual save and 4.5 game definitions. |

## Recommended next-release behavior

1. **Under each “Your next moves” goal, show one or two executable steps.** A fleet target might first check alloys, naval capacity, current Fleet Doctrine, and weapon preference. A minerals goal might name a planet with available mining capacity or a known system that can be claimed before stations are built.
2. **Use eligibility checks before optional AI explanation.** Parse current policies, federation state, relations/intel, researched technology, planet capacity, and resources. The LLM should explain verified options and trade-offs, not invent an available policy or diplomatic action.
3. **Show uncertainty honestly.** The save may contain hidden foreign data. Diplomacy and war advice should use only player-visible contact/intel; label unknown fleet power and unverified ally acceptance.
4. **Replan when a meaningful event occurs** (new war, resource deficit, major policy/federation change, colony development), while preserving the 5–10 year goal when it is still valid.
5. **Read rules from the installed game version.** The local installation contains `common/policies/06_policies_fleets_and_starbases.txt` with fleet, weapon, defense, starbase, platform, Arkship, and Waystation policy categories. Use version-matched game files and enabled mods to validate IDs and availability. A file's presence alone does not prove an option is selectable for this empire.

## 4.5.2 final hotfix: additional advice checks

The user supplied the full **6 October 2026** hotfix text (checksum **9776**), matching the official Stellaris release announcement. These details refine the policy, ship, technology, and diplomacy advice above:

| Shipped 4.5.2 detail | Dashboard consequence |
| --- | --- |
| Starting Fleet Doctrine, Weapon Preferences, and Defense Preferences can be randomized, weighted toward an empire's defaults. | Read the actual choices from each save; do not infer them from empire type or a starting template. |
| Defense platforms have separate weapon and defense preference policies; Nomads gain Arkship weapon and Waystation defense preferences and do not have starbase/platform preference policies. | Show only the policy family relevant to the player's empire and the asset being discussed. |
| Starbase explosive weapon preference requires swarmer missiles technology. Preference application and visibility received bug fixes. | Check technology and current policy before suggesting a starbase loadout change. |
| Armor upkeep was reduced to match same-tier shield upkeep. | Recalculate ship-build trade-offs from installed 4.5.2 component data rather than older cost assumptions. |
| The Franchising civic can bypass Opinion, Trust, and Embassy requirements when proposing Subjugation. | Diplomatic eligibility needs civic-specific exceptions; do not apply a universal relation threshold. |
| Leveled technologies now retain their identity when saved, and a revolt backed by another empire can join that backer. | Recheck technology parsing and treat backing a revolt as a concrete diplomatic risk when the relevant information is visible to the player. |

The full patch contains many origin-specific and bugfix entries. The table selects only changes likely to affect Stellaris Guide's general recommendations.

## Diary-by-diary reading guide

| Source | Date | Useful finding | Status for recommendations |
| --- | --- | --- | --- |
| [#428: 4.5 Cygnus](https://forum.paradoxplaza.com/forum/developer-diary/stellaris-dev-diary-428-4-5-cygnus.1933872/) | 9 Jul 2026 | Introduced Pop Group/faction rework, military preference policies, and federation economic laws in beta. | Cross-check with 4.5 release. |
| [#429: Summer Experiments](https://forum.paradoxplaza.com/forum/developer-diary/stellaris-dev-diary-429-summer-experiments-2026.1938749/) | 20 Aug 2026 | Beta AI district/planet changes; separate experiments may or may not ship. | Use AI notes as advice-design ideas; do not encode experiments as game rules. |
| [#430: Development Continues](https://forum.paradoxplaza.com/forum/developer-diary/stellaris-dev-diary-430-4-5-cygnus-development-continues.1939491/) | 27 Aug 2026 | War-joining logic changed; beta introduced Exclusive Harvesting Rights. | War support affects advice; harvesting agreement was later withdrawn. |
| [#431: Development Continues to Continue](https://forum.paradoxplaza.com/forum/developer-diary/stellaris-dev-diary-431-4-5-cygnus-development-continues-to-continue.1940219/) | 3 Sep 2026 | Further ethics/faction behavior and displays; AI planet specialization fixes. | Validate against shipped UI/save before surfacing exact metrics. |
| [#432: Yet More About 4.5](https://forum.paradoxplaza.com/forum/developer-diary/stellaris-dev-diary-432-yet-more-about-4-5-cygnus.1941026/) | 10 Sep 2026 | AI economy planning, target buffers, shortage response, and colony designation revisions. | Good model for goal-to-action design, not a direct player rule. |
| [#433: Preliminary Release Notes](https://forum.paradoxplaza.com/forum/developer-diary/stellaris-dev-diary-433-4-5-cygnus-preliminary-release-notes.1941572/) | 17 Sep 2026 | Consolidated planned 4.5.0 changes and confirmed Exclusive Harvesting Rights had been pulled. | Prefer final release when details differ. |
| [4.5 release announcement](https://forum.paradoxplaza.com/forum/threads/dev-team-stellaris-4-5-released-checksum-8697.1942119/) | 22 Sep 2026 | Confirms 4.5 release, Pop Group save incompatibility, factions, preference policies, and federation laws. | Shipped 4.5.0 baseline. |
| [#434: Tentative 4.5.2 Notes](https://forum.paradoxplaza.com/forum/developer-diary/stellaris-dev-diary-434-4-5-2-cygnus-tentative-patch-notes.1943322/) | 1 Oct 2026 | Previewed 4.5.2 changes. | Superseded by final 4.5.2 hotfix notes of 6 Oct. |
| [4.5.2 final hotfix announcement](https://steamcommunity.com/app/281990/announcements/) | 6 Oct 2026 | Confirms policy splits and Nomad-specific preferences, along with fixes. | Shipped 4.5.2 baseline. |

The Paradox forum pages were not accessible through the research browser. The same developer announcements on the [official Stellaris Steam announcements page](https://steamcommunity.com/app/281990/announcements/) were used to verify the findings and final release status.
