# Claude product review — Stellaris Guide response

**Reviewed:** October 18, 2026 against the user-supplied `product-review-claude.md` and the v1.5.2 source. Claude reviewed documentation and screenshots, but explicitly did not review source code or tests. This document is our triage, not an instruction to implement every suggestion. The agreed release scope is in [v1.6 plan](RELEASE-1.6-PLAN.md).

## What we accept

| Review finding | Source check | Decision |
| --- | --- | --- |
| Advice treats monthly deficits alike despite different reserves. | `saves.py` already parses stockpiles; `strategy.py` mentions stock in step text but chooses goals primarily from monthly net values. | **v1.6:** calculate resource runway and rank urgency from it. Show both stock and monthly change. |
| Goals lack clear urgency and can overwhelm Main. | `make_plan()` appends goals in rule order and returns the first five; it has no severity field. | **v1.6:** add a structured evidence/priority record and show one leading action with remaining goals compactly. Preserve the trend and galaxy chart on Main. |
| Tech progress and policy labels need plain meaning. | Technology branches expose raw progress/start date, without a verified total cost; saved policy IDs are shown in a basic formatted form. | **v1.6:** show elapsed research and explain policies using validated 4.5.2 labels. Show percent/ETA only after a reliable denominator and current output are verified. |
| “First visible option” is weak research advice. | `choose_tech()` can choose an available option from a limited hint rather than a complete eligibility/benefit model. | **v1.6:** label options as candidates or withhold a recommendation when evidence is thin. |
| Players need to learn *why*. | Current goals have steps and reasons, but presentation repeats generic checks. | **v1.6:** present observation, action, effect/trade-off, confidence and in-game check in one consistent card. Put optional teaching text behind “Why?”. |
| Offline, read-only and spoiler-safe behavior are strengths. | The core rule path, loopback API and server-side spoiler projection are present. | Keep them as release gates. Lead product copy with “works offline; AI is optional.” |

## What we adjust before adopting

| Review proposal | Adjustment |
| --- | --- |
| “Buy food today” because energy is abundant and food income is negative. | **Food stockpile and time to depletion are decisive.** Energy reserves alone do not establish urgency or affordability. If runway is short, suggest checking the Market for an immediate bridge while production is fixed. Never promise a particular price or purchasable amount from the save alone. |
| Spend 13,049 alloys on ships now. | Large stock alone does not prove the fleet is underbuilt. Check current naval use/capacity, upkeep, war posture, and player-visible rival strength where known. Suggest a small order and re-evaluation only with supporting facts. |
| Call a five-year research project “stalled.” | Start date is parsed, but total cost and galaxy tech settings are not. Show the elapsed time as an observation; call it stalled only after cost, output and progress change across saves support that conclusion. |
| Compare fleet power against a fixed expected value for game year and difficulty. | Defer a numeric benchmark. The app does not currently parse all relevant galaxy settings or have a calibrated save corpus. Use naval capacity and known rival comparisons, with Unknown where intel is insufficient. |
| Use the game's AI market timing as a six-month player threshold. | It is a useful *candidate* heuristic, not proof of an optimal player decision. Calibrate 0–3 and 3–6 month warning bands on test saves; let the player see the underlying runway. |
| Collapse the rival graph whenever intel is low. | The user asked to keep the graph visible on the main screen. Retain the section and use an informative low-intel state plus an “improve intel” action instead of hiding it automatically. |
| Hide all in-game checks behind an icon. | Remove repetitive copy from the card face, but preserve a visible concise check and an accessible expanded explanation for uncertain actions. |
| Move rules straight into community-editable YAML. | First give Python rules a common record, predicates, and fixtures. A declarative rule language is useful only after the fact schema, validation, precedence and safety boundaries settle. Avoid introducing an unvalidated mini-language in v1.6. |

## Findings that need reproduction

- **Repeated Tech Tree/Ship Builds sidebar entries:** the v1.5.2 HTML has one button for each destination. Reproduce against the packaged v1.5.2 app before classifying this as a current bug; the review screenshots may show another build or browser state.
- **Watchlist overlap:** v1.5.2 moved the ticker to a full header row with truncation and seven-second rotation. Verify the exact reported window width and Tech Tree view; fix any remaining overlap if reproduced.
- **Auto-generated ship warning:** the current parser records per-slot components and an `auto_generated` flag. The generic design recommendation is still limited, but the review's description of a parser retaining *only* distinct components is outdated. Prefer a policy-first explanation for new players; keep slot-level design work as a later, validated project.
- **Cygnus-specific mechanics:** the user-supplied final 4.5.2 patch confirms policy splits and randomized starting preferences. Other suggested thresholds and archetype rules need same-date game/save evidence before becoming advice. See [Cygnus research](CYGNUS-4.5-STRATEGY.md).

## Priority decision

**v1.6 should improve the answer on the Main screen before adding more destinations.** The first release gate is: when a save has a deficit, the Guide explains whether the stockpile is at risk now, gives a safe bridge action if supported, and shows a longer-term fix. The second gate is that every prominent recommendation can say what evidence produced it and what remains unknown. Broader espionage, scenario planning, mod handling and public rule contributions stay outside v1.6.
