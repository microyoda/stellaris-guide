# Stellaris Guide — product plan

**Baseline:** v1.5.2, documented October 18, 2026. The supported target for this baseline is the Stellaris 4.5.2 Cygnus save format. This document separates shipped behavior from ideas that need research and validation.

## Product promise

Give a player a short, trustworthy answer to three questions: **What changed? What should I do next? How can I check that the action worked?** The first screen should be useful within a few seconds, including when no AI model is configured.

Stellaris Guide reads the player's saves and optional local game art. It does not edit saves, click inside Stellaris, or promise that a suggested in-game action is legal or safe. Its role is to help the player decide, then let the player act in the game.

## Players and jobs

| Player | Job to be done | A good outcome |
| --- | --- | --- |
| Learning player | See the most urgent economy, colony, or fleet issue without learning another complex interface. | One understandable next move and a concrete check in Stellaris. |
| Returning player | Resume a campaign after a break. | Identify the current empire, save date, changes, and near-term priorities. |
| Strategy-focused player | Compare known rivals and inspect a proposed build or policy. | See evidence, uncertainty, trade-offs, and the exact screen to verify before acting. |
| Privacy-conscious player | Play offline or avoid spoilers. | Built-in advice works without AI; hidden foreign information stays off unless explicitly enabled. |

## Experience principles

1. **One main screen.** Put campaign identity, save freshness, urgent Watchlist item, four quick indicators, next moves, and compact comparisons where they can be scanned together. Keep detailed cards in the left-side Planets, Empires, Tech Tree, and Ship Builds views.
2. **Actions under goals.** Each five-to-ten-year target should have a first practical step, a reason, a progress measure when available, and a check the player can perform in game.
3. **Show the evidence.** Distinguish a measured value from a heuristic and from an AI explanation. Never turn an unavailable value into zero or a guess.
4. **Respect discovery.** Use only player-visible information for ordinary rival advice. The optional spoiler mode is separate, off by default, and visibly labelled.
5. **Remain useful offline.** Save parsing, goals, basic chat answers, and navigation work without Ollama, LM Studio, or OpenRouter.
6. **Make freshness obvious.** A recommendation belongs to a particular campaign and save date. A screenshot may be newer than the autosave; the answer should say when their dates differ.

## Shipped in v1.5.2

| Surface | Current behavior | Important limit |
| --- | --- | --- |
| Main | Energy, alloys, fleet and colony indicators; expandable empire health; up to five next moves with steps; rotating Watchlist; trends; known-galaxy strength and opinion tabs. | A save-recorded strength value is not guaranteed to match a number shown in the Contacts screen. |
| Planets | Colony status, selected job settings, warning and cautious build ideas. | The app does not fully verify building eligibility, costs, queues, or every modded job. |
| Empires | Player reference plus known contacts, category views, diplomacy and intel where parsed. | Low intel and unsupported fields remain Unknown; hidden exact foreign data requires spoiler consent. |
| Tech Tree | Current research and a focused prerequisite path from installed game definitions when available. | DLC, mod overrides, and all eligibility conditions are not resolved. |
| Ship Builds | Owned design information and a cautious reinforcement or review suggestion. | It is not yet a validated slot-by-slot design optimizer. |
| Campaign guide | Plain questions or `/ask`, quick questions, recent/frequent text history, and optional screenshot analysis through local or online models. | Model answers may be wrong; screenshot analysis needs a vision-capable model. |
| Windows shell | Portable ZIP, newest autosave scan every 15 seconds, manual refresh, tray reopen/refresh/quit, and version badge. | Closing the browser tab leaves the tray app running. |

The Watchlist in v1.5.2 runs across the campaign header and advances every seven seconds while the dashboard tab is visible. [Release notes](RELEASE-1.5.2.md) describe the exact change.

## Recommendation contract for future work

Every new recommendation should answer these fields, whether it is displayed as a card or spoken through chat:

| Field | Question it answers |
| --- | --- |
| Observation | Which save value, trend, or player-visible contact fact triggered this? |
| Goal | What outcome should improve, by when? |
| Suggested action | What can the player try in Stellaris? |
| Expected effect and trade-off | What may improve, and what resource or risk may worsen? |
| Confidence and visibility | Is the fact verified, inferred, unknown, or spoiler-only? |
| In-game check | Which eligibility, price, treaty, enemy strength, or result must the player confirm? |
| Source date | Which campaign and save date support this advice? |

The current planner produces goals, steps, and alerts but does **not** yet store all of these as a common structured record. That is a proposed product and technical change, not a shipped feature.

## Growth roadmap — proposals, not commitments

| Horizon | Focus | Release gate |
| --- | --- | --- |
| **v1.6: credibility** | Resource stockpile runway, explainable priority, evidence-backed recommendation records, honest research and policy explanations, and confirmed UI fixes. | Same-date fixture cases show different urgency for short versus long runway; ordinary API and chat remain spoiler-safe. |
| **v1.7 candidate: teaching** | Short “Why?” lessons, optional player intent and experience settings, and archetype-specific advice once those facts are validated. | New players understand the leading action and its trade-off; unsupported empire types do not receive inapplicable advice. |
| **Later research** | Deeper diplomacy and espionage, verified planet/ship eligibility, mod/DLC adapters, historical planning, and scenario comparisons. | Each new claim has game-version fixtures and an in-game check before it appears as actionable advice. |

The [v1.6 release plan](RELEASE-1.6-PLAN.md) is the active planning document. The [Claude review triage](CLAUDE-REVIEW-TRIAGE.md) records accepted, adjusted and unconfirmed suggestions. The older [next-release record](NEXT-RELEASE.md) remains historical context for v1.5.

## Success measures

- A new player can identify a first action and its in-game check from Main without opening another page.
- A returning player can tell which campaign and save date are being analyzed and whether the app is still waiting for an autosave.
- All ordinary rival and AI context obey the spoiler setting across refresh, restart and campaign switch.
- New recommendation types have save fixtures, same-date in-game comparisons, and a clear Unknown state.
- The portable Windows package starts, updates from autosaves, reopens from the tray, and quits cleanly.

## Decisions still needed

1. Should goals be automatically replaced after a major event, or should the player pin one until dismissed?
2. Should a future scenario planner use transparent deterministic assumptions only, or also show AI-generated alternatives as clearly labelled hypotheses?
3. Which mod and localization combinations should be officially supported first?

For implementation boundaries and extension steps, see [Technical guide](TECHNICAL.md) and [System architecture](SYSTEM-ARCHITECTURE.md). The older [next-release planning record](NEXT-RELEASE.md) remains historical context; its unchecked items are not shipped claims.
