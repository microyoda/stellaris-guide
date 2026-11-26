# Fleet Design Finder — planning schema

**Status:** Next-release design note, October 23, 2026. No implementation, package or release tag is authorized by this note. The supplied screenshot is a layout reference, not a specification for rankings or numeric scores.

## Player question and primary screen

The page should answer: **“What should I build with the parts I have, for the fight I expect?”** Keep the useful shape of the reference: hull tabs, objective choices, a short ranked list, a recommendation panel and comparison. Show artwork for hulls and components wherever the selected game's assets can be resolved.

| Area | What the player sees | Required honesty |
| --- | --- | --- |
| Context strip | Save date and game version; selected Fleet Doctrine and weapon/defense preferences; target enemy or “Unknown opponent”; intel/source badge | Selected policies are known from the save; available alternatives and enemy equipment may not be. |
| Hull tabs | Corvette, Frigate, Destroyer and later unlocked hulls; number of saved designs; locked or uncertain state with reason | A saved design count is not a count of buildable designs. Do not label a hull locked from a missing save field alone. |
| Goal chips | Balanced, damage, survival, screening, low cost and mobility; anti-shield/anti-armor only as known-enemy or explicit “what if” scenarios | “Best” means best *for the stated goal and assumptions*, never a universal winner. |
| Candidate list | Up to five relevant designs, each labelled **Saved**, **Auto-design**, **Guide concept**, or **Reviewed community idea**; one-line role, buildability, main trade-off and evidence status | Avoid precise overall scores until the combat and cost model is validated. Do not rank solely by fleet power or “power per 100 alloys.” |
| Recommendation pane | **Use existing design**, **Consider a new design**, or **Need more information**; component artwork, why it fits, resource/capacity implications, and what to check in the in-game Ship Designer | Never claim the Guide has built or equipped a ship; the player acts in game. |
| Compare drawer | Up to three choices side by side: offensive profile, defenses, range/role, speed, alloy cost, upkeep, naval use, missing parts, policy fit and uncertainty | Collapse by default so the next section remains visible on one screen. |

Suggested flow: choose a hull → choose a goal → optionally choose an enemy or enter observed equipment → inspect recommendation → compare alternatives → follow a short in-game checklist. The page should work without selecting an enemy: show a general-purpose baseline and say which facts would enable a more specific counter.

## Recommendation data schema

Keep **facts**, **assumptions**, **candidate designs** and **advice** separate. A calculator must not convert an unknown enemy loadout into an invented value.

| Record | Minimum fields |
| --- | --- |
| `context` | Save ID/date/release; recorded DLC and mods; selected doctrine/preferences; unlocked hulls and components where verified; alloy balance/stock, naval use/capacity; chosen goal. |
| `enemy` | Target name or player-named scenario; source `visible_intel`, `player_supplied`, or `unknown`; observed hull mix, weapons, defenses and confidence per field; no hidden design data while spoilers are off. |
| `candidate` | Stable ID; source and revision; hull, role, sections/slots/components; status `saved`, `generated_concept`, or `community_idea`; build status `verified`, `conditional`, `blocked`, or `unknown`, with reasons. |
| `assessment` | Goal-specific strengths and weaknesses; known cost/upkeep/naval usage; policy fit; mismatch against observed threat; model assumptions, source version and unknowns. Keep each dimension visible instead of hiding it in one power number. |
| `recommendation` | Decision `reuse`, `review_new_design`, or `inspect_first`; reason; two or three in-game steps; trade-off; what would change the advice; separate rule and strategy review statuses. |

### Selection method

1. Filter impossible hulls and components using the selected save and installed versioned definitions. Unknown eligibility stays **conditional**; do not silently discard or declare buildable.
2. Look at existing saved designs first. If one fits the selected goal, recommend using or checking it before proposing a duplicate custom design.
3. Compare feasible alternatives on the selected objective. For a known enemy, use only visible or player-supplied equipment; for an unknown enemy, show broad roles and a checklist. Present attack, survival, range, screening, mobility and cost as separate dimensions. If a future numeric calculator is introduced, show its assumptions and validation limits.
4. Use reviewed community builds as hypotheses or templates. Verify parts and mechanics against installed rules, then test the tactic against fitting and counterexample fixtures before treating it as a tested strategy. Show source author, date, game version and conditions in expanded details.
5. Give a plain-language action: **keep current**, **change a specific part in Ship Designer**, or **scout/check the enemy first**. A recommendation must explain why a change matters and when to reconsider it.

### Buildability and policy gates

**Verified buildable** is reserved for a candidate whose hull is researched, whose section layout and slot sizes are valid, whose every component is unlocked and permitted, and whose reactor supplies enough power. The check must use the player's game version, DLC and mod rules and a verified construction cost. A saved design is not automatically buildable: it can contain obsolete or unavailable parts. If any check is missing, label the candidate **conditional** and list what the player should verify in Ship Designer. Use **blocked** only when a known requirement fails; use **unknown** when the source data itself cannot be read. The present parser does not supply all these checks, so newly generated designs will normally start as conditional concepts.

Show the **selected** Fleet Doctrine and weapon/defense preferences from the save as facts. An alternative policy is only a suggestion to inspect in the Policies screen until eligibility is evaluated from the installed rules. In 4.5, these settings can affect automatic designs and technology offers; policy fit must explain that connection without promising the player can switch. Check Nomad-specific policy families separately instead of applying regular-empire options to them.

### Candidate ordering

Filter candidates with confirmed impossible requirements from the recommended list, but keep them discoverable with their blocking reason. Put a fitting, verified saved design ahead of an equivalent new concept. Within each goal, compare only known dimensions relevant to that goal and explain the trade-off. Unknown cost or combat behavior never becomes zero or an estimated win rate. Put candidates with missing decisive metrics in an **insufficient data** group after candidates that can be compared; do not assign a precise rank to that group. If candidates remain tied, show them as equally suitable and sort by stable name for display only. Community ideas remain explicitly conditional until their rule claims and combat strategy have separate reviews.

## Evidence and safeguards

The existing Ship Builds page already reads saved design slots, some component evidence, fleet composition and selected military policies. It does not yet prove every candidate's exact build eligibility, final in-game cost, or enemy-specific combat outcome. Review these gaps before generating or ranking new designs.

Use installed game definitions and official final patch notes as the rule layer. The local military research notes in [`references-claude/04-military-ships-fleets.md`](../references-claude/04-military-ships-fleets.md) identify policy and role questions to verify; [`11-conflicts-and-stale-content.md`](../references-claude/11-conflicts-and-stale-content.md) flags older fleet claims that should not become 4.5 rules. Community guides remain optional, source-labelled tactics. Follow the reviewed-playbook trust and status model in [`strategy-playbooks.md`](strategy-playbooks.md). Preserve the player's spoiler setting and never use hidden enemy components in normal advice.

## Acceptance cases before implementation is called complete

- An unlocked Corvette, Frigate or Destroyer with a suitable saved design produces a **reuse** recommendation with a reason; an unsuitable design is not called best because of fleet power alone.
- A locked component, missing DLC, mod uncertainty, or unknown exact cost visibly limits a generated concept instead of making it “ready to build.”
- A visible or player-supplied enemy loadout can change the recommended offensive/defensive profile. An unknown or low-intel opponent does not receive a fabricated counter.
- Switching doctrine or preference changes the policy-fit explanation, while the page does not claim that an unselected policy is available without eligibility checks.
- A stale-version save or changed installed checksum downgrades rule confidence. Community tactics retain an independent strategy-testing status.
- A candidate becomes **verified buildable** only when the hull, sections, slot sizes, component access, power, version/DLC/mod rules and cost checks all pass. Each failed check makes it blocked; each unavailable check makes it conditional or unknown with a visible reason.
- Ranking fixtures include two tied candidates, an unknown-cost candidate and an unknown-combat candidate. Ties remain tied; missing decisive metrics appear under **insufficient data**, never as zero or an invented score.
- With spoilers off, enemy recommendations use only visible intel or details the player entered. A save containing hidden enemy equipment does not leak that equipment into the list, comparison or chat explanation.
- A mod that changes a hull, slot, component or policy rule prevents an unverified vanilla build from receiving a verified badge. A Nomad fixture uses its own policy family.
- The default desktop viewport shows hull tabs, goal, top recommendation and candidate list without page scrolling; comparison opens as a drawer. Keyboard users can select hulls and goals, open and close the drawer, move between candidates and read the recommendation.
- Every hull and component has artwork when a matching asset is available. When an asset is missing, a readable labelled fallback occupies the same space without a broken-image icon or layout jump.
