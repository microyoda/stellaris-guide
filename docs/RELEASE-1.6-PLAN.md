# Stellaris Guide v1.6 — research and release plan

**Status: phased implementation authorized October 18, 2026; see [implementation plan](release1.6-implementation-plan.md).** No v1.6 feature is claimed as shipped until its acceptance gate passes. The validated target is Stellaris 4.5.2 Cygnus (9776); another game release needs a separate rule and fixture review.

This plan combines the supplied Claude product review, the existing review triage, the five dashboard screenshots and their exact 2277.10.01 save, the 16 Gamer of Passion articles, installed 4.5.2 game definitions, research on Ollama, LM Studio, OpenRouter and screenshot safety, and a read-only review of YThibos/Stellaris-Tech-Tree. The articles and third-party tree are candidate knowledge, not authority over the installed game or the player's circumstances.

## Outcome and decisions already settled

A player should understand what matters in their campaign, why it matters, what they can do, and what to check in Stellaris. Advice works offline without an AI provider. The app remains read-only and does not show hidden rival information unless the player deliberately enables spoilers.

| Question | Player decision for v1.6 |
| --- | --- |
| May immediate resource risk displace the leading goal? | The player may pin another campaign goal above it. Keep a serious risk visible in a separate indicator; do not silently replace the pin. |
| Which empire fixtures come first? | Start with a regular organic empire. Choose later archetypes by DLC used by the actual game load; do not preselect Machine and Hive or any other pair. |
| May the review screenshots be used as regression evidence? | Yes, after comparison with the exact 2277.10.01 save. This comparison is now complete; verified and unverified expectations are distinguished below. |

## Evidence hierarchy and applicability

1. **Player observation:** a dated autosave, a screenshot, or a value the player confirms in game. A screenshot can be newer than the selected save; show both dates when they disagree.
2. **Mechanic verified for the ruleset:** installed game definitions and final official patch notes, with game version, DLC and mod applicability attached.
3. **Tested strategy:** a recommendation supported by multiple relevant fixtures and counterexamples, not one build or one galaxy setting.
4. **Community strategy article:** useful hypothesis or explanation. Rankings and fixed fleet recipes remain opinion until tested for 4.5.2 and the player's empire.
5. **AI synthesis:** explains the above evidence; it is never itself proof of a game value or rule.

Every rule or knowledge card should record its source, version, prerequisites, exceptions, DLC or mod dependence, whether the player can see the fact, spoiler level, verification status and test cases. Use plain “Unknown” when a needed field or rule is unavailable. A mod name containing a version number does not itself prove compatibility or incompatibility.

### Exact 2277.10.01 research fixture

The five review screenshots match the autosave named autosave_2277.10.01.sav in the United Nations of Earth campaign. The save metadata says Cygnus v4.5.2 and date 2277.10.01. The locally installed game's launcher settings say v4.5.2 (9776). The save lists 16 required DLC and the mod “Planetary Diversity (4.1)”. “Required DLC” is the save's label, not proof of current launcher ownership or enablement; save-recorded mods may differ from the currently selected playset. Keep the original save and screenshots outside any release archive.

The required DLC entries in that save are Ancient Relics Story Pack, Anniversary Portraits, Apocalypse, Aquatics Species Pack, Distant Stars Story Pack, Federations, First Contact Story Pack, Galactic Paragons, Grand Archive, Horizon Signal, Leviathans Story Pack, Lithoids Species Pack, Megacorp, Plantoids Species Pack, The Machine Age, and Toxoids Species Pack.

| Visible/reviewed issue | Exact-save finding | Regression expectation |
| --- | --- | --- |
| Food −57.2/month, energy stock 27,093.5; review says buy food today. | Food stock is 11,731.4: about 205 months of cover at the saved net rate. The stock rose from 10,881.3 on 2277.07.01 to 11,731.4 on 2277.10.01 despite a monthly deficit; the reason for the gain is unverified. | Explain the long runway and gradual production fix. A same-day market purchase is not an urgent default. Market price and trade availability need an in-game check. |
| Consumer goods −10.4/month. | Stock is 4,471.3, roughly 430 months of cover at the saved net rate. | Show deficit and runway separately; do not call it an immediate shortage. |
| Alloys stock 13,049.1, fleet power 2,320; review says build ships now. | Figures match, but naval capacity and threat evidence are insufficient to establish an urgent ship order. Fleet power remained 2,320 across the four 2277 autosaves. | Show possible unused military potential, then ask for naval capacity, upkeep, player goal and visible threats before ordering a build. |
| Destroyers has been current since 2272.10.29; review calls it stalled. | Progress increased 1,625.5 → 1,719.3 → 1,813.0 → 1,906.8 across the January, April, July and October 2277 saves. | Do not call it stalled. Show elapsed time and measured progress trend. Do not invent a completion percentage or ETA without a verified cost and rate. |
| Alpha Centauri Prime needs attention. | 33.5% stability, −31.7 amenities and 2.6 of 12 farmer jobs filled match the screenshot. | A strong planet-advice fixture. Distinguish available jobs from employed workforce; inspect job controls before suggesting another farm building or district. |
| Main screenshot repeats Tech Tree and Ship Builds; Tech Tree ticker text overlaps. | Both are visible in the supplied screenshots. The source HTML and a packaged build may differ. | Reproduce at the same screen size and build before calling either a current-code regression. |

The fixture also confirms United Nations of Earth, eight colonies, +207 energy/month, +43.4 alloys/month, and the five displayed goals. The screenshots are evidence of what was displayed, while the save and earlier autosaves decide whether the review's proposed advice is justified.

## Proposed v1.6 release scope, in order

### 1. Fixture and campaign-context foundation

Start with the exact regular organic 2277.10.01 case, then add a short-runway counterexample, missing-value case, low-stability planet, research-progress trend and low-intel contact. Add later empire types according to DLC actually used by each game load. Do not generalize food, factions, housing or military upkeep to another archetype without an applicable fixture. Use scrubbed or synthetic test assets for anything distributed.

Read and carry the selected save's version, date, required DLC, mods, player empire and known contacted empires. If available, compare to the installed game's version and current playset and label mismatches. Do not assume the save contains the running game's checksum. Record the relevant galaxy settings only after their save keys are verified.

**Gate:** every new rule has a positive case, a counterexample and a missing-data case, tied to a source version and fixture.

### 2. Resource runway, planet jobs and practical recovery

For a negative monthly net with valid positive stock, calculate months of cover as stock divided by the absolute monthly net. A nonnegative net has no depletion runway; missing stock or invalid net yields Unknown. Show stock and monthly net with the result. Candidate warning bands are under 3 months urgent, 3–6 months watch, and over 6 months a planned fix. These are product heuristics to validate, not Stellaris mechanics. The developers' AI market timing can inform research, but does not establish an optimal player action.

A short-runway deficit can suggest checking a Market purchase as a temporary bridge when the player has energy, followed by a production fix. Do not promise price, available quantity or an instant purchase. Planet advice must compare current jobs, allowed job settings, workforce actually filling them, amenities, stability and upkeep before suggesting a new building. The 2277 fixture's 2.6/12 farmer jobs shows why capacity alone is insufficient.

**Gate:** the same monthly deficit with little food versus 205 months of food produces different urgency; the Alpha Centauri case does not recommend redundant farm capacity merely because food income is negative.

### 3. Recommendation record, ranking and player pin

Use one internal recommendation record for all goals: stable ID, save date, observation, action, reason, expected effect, trade-off, in-game check, severity, confidence expressed through evidence and uncertainty, visibility level, source rule/version, and progress. Rank unpinned suggestions from explainable urgency and impact, not merely low action cost. A player pin controls the leading Main card even when a different goal ranks higher. Show any critical risk separately and persistently without changing the pin.

Keep one leading card, compact remaining goals, Watchlist ticker, trend graph and known-galaxy chart visible. Each recommendation expands to teach why and show its evidence. Preserve a meaningful Unknown state where intel or data is insufficient. This respects the player's chosen strategy and avoids presenting a numeric fleet benchmark based only on game year.

**Gate:** ranking is stable for the same snapshot, the pin persists across refreshes, a critical risk stays visible, and no spoiler-off recommendation depends on hidden rival power.

### 4. Research, military policy and ship explanation

Map saved 4.5.2 Fleet Doctrine and fleet, starbase and defense-platform weapon/defense preferences to player-readable names. Read selected policy from the save; the 4.5.2 starting choice is randomized. Explain auto-generated designs in light of the current policy and unlocked components. Keep slot-level inspection cautious; do not promise an optimal fleet or Titan loadout.

Show current research, saved start date and observed progress across saves. Show percent or time remaining only after total cost, progress units, current output and relevant galaxy settings are verified. A first-visible technology is a candidate, not a strategic recommendation.

**Gate:** policy labels match the in-game Military Policies screen; the 2277 Destroyers case is not falsely marked stalled; no ship build is declared available or affordable from incomplete data.

### 4a. Focused technology route window (research proposal)

**Decision to validate before building:** use [YThibos/Stellaris-Tech-Tree](https://github.com/YThibos/Stellaris-Tech-Tree) as a reference for its prerequisite model and interaction, then present a smaller, campaign-specific route in a separate Edge window. This is a proposed v1.6 scope item, not a claim that its code or game data has been integrated. The review was of `master` at commit `41d811d0ca1efdcb01f2eaa47ac77fb4a1a70daa` on October 18, 2026. Recheck the upstream revision before implementation.

**What the upstream project actually provides.** Its Svelte/TypeScript tree has a 4.5.2 snapshot extracted on October 15, 2026, with vanilla plus 19 layers from the author's mod playset. It models direct prerequisites, groups in which *one of several* technologies suffices, tier gates, availability conditions, draw-weight modifiers, DLC checks, mod layers and research markers. Search, target highlighting, save import and hide-researched controls already exist. Its browser URL remembers version, search, highlighted targets and content filters, **not** the imported researched state. Its save reader provides researched levels, empire name, date, DLC and mod names, but not the three current projects. Its campaign import can match an existing campaign by empire name and its mod matching includes names; neither should become Stellaris Guide's campaign identity or proof of a mod match. The upstream full board is wide and scroll-heavy. These observations come from its README, `src/domain`, `src/save`, `src/site/state` and `public/data` at that revision.

**Player view.** The Tech Tree tab keeps a compact summary and a **Explore route** action. Opening it shows one goal in a separate Edge window with a visible **Close** button: target and effect at top; a short route of researched, researching now and unmet steps; alternative requirements drawn as an explicit **choose one** fork; tier progress and other availability conditions in plain language; and a concise **what to research next / check in game** panel. A **Show full tree** control reveals the broad exploratory graph only on demand. Search and changing the target stay available. Never mark every member of a one-of group as mandatory merely because the upstream `requirementPath()` highlights them all. A target may also be granted by an event rather than drawn as an ordinary research option; label that case instead of drawing an impossible research route. Keep this window advisory and read-only.

**Data contract and applicability.** Start from the Guide's selected save and stable campaign identity, not a second browser-owned campaign. Pass the save date, player empire, release/checksum when known, researched technology **IDs and repeatable levels**, current Physics/Society/Engineering project IDs and progress, DLC, enabled mod identifiers and ordered playset, and snapshot freshness to the view. The existing Guide parser has current projects and alternatives, but its `technology.py` reads only direct prerequisites from installed `common/technology` files, caps the focus path at four levels/five displayed steps, and lacks one-of groups, tier gates, conditional availability and mod overlays. Its `saves.py` currently exposes a researched **count**, so exact researched IDs need to be retained deliberately. Compare the selected save's version and content with the tree's data before showing a confident route. Names alone are insufficient for mod identity; compare stable Workshop IDs, load order and extracted definitions where possible, and mark unverified mod paths **Unknown**. The sample 2277.10.01 campaign uses Planetary Diversity (4.1); do not assume the author's bundled mod playset represents it.

**Source of tech data.** Prefer an offline, version-matched snapshot derived from the player's installed game and actual playset, if a packaged, no-command-line extraction path proves practical. Assess a build-time vanilla 4.5.2 snapshot only after reviewing Paradox's redistribution terms; the upstream project's MIT licence covers code and documentation, **not** Stellaris or mod data and icons under `public/data`. Retain its MIT copyright notice for any reused code and its third-party notices for any permitted assets. Do not require a nontechnical player to install Node, run `npm`, or upload a save to the public tree site. The Guide should serve the view locally and avoid duplicating sensitive save data in URL parameters or persistent browser storage. Until mod extraction is verified, show a clearly limited vanilla route or an applicability warning rather than inventing a modded unlock path.

**Edge window and Close behavior.** Prototype two launch paths on the packaged Windows build: (1) when the Guide is already open in Edge, a user-clicked `window.open()` popup with an in-page `window.close()` control; (2) when another browser hosts the Guide, launch Edge explicitly in its own app window and let the local Guide close **only that tracked window**. `window.close()` alone is not reliable for a window launched by an external process. Do not close all Edge windows or kill a shared Edge process. Verify the Close button, title-bar X, repeated opens, refreshes and tray reopening; if a reliable window-specific close cannot be demonstrated, keep the title-bar X and do not label the in-page control as working. Include keyboard focus, Escape behavior and a narrow-screen layout in the prototype.

**Truth and recommendation limits.** Distinguish: *researched*, *researching*, *prerequisites met*, *tier gate met*, *conditions appear met*, *available among saved alternatives*, and *future possibility*. A prerequisite path is not a guarantee that the game will offer a technology: draw weights, empire conditions, game settings, DLC, mods and random rolls can affect it. Do not calculate a completion date from a base technology cost or current progress alone. Preserve the existing v1.6 research-progress verification gate before showing percentages or ETAs. When spoilers are off, never use hidden rival or unexplored-galaxy data to justify the goal; **Show full tree** is an intentional exploration action, distinct from the double-confirmed hidden-save-information setting. Do not send the campaign to an LLM for path arithmetic; the AI may explain a route only from validated, version-tagged steps.

**Implementation choice gate (future work):** compare (a) adapting the upstream MIT domain/extraction code with a compact local UI and (b) extending Guide's Python parser for the missing mechanics. Choose after a small offline prototype measures fidelity against installed 4.5.2 definitions, packaging size/startup time and mod/playset handling. Do not embed the upstream hosted page as the production view: it would disconnect from the selected autosave and the app's spoiler and version checks. No choice is recorded as completed here.

**Acceptance cases:** Orbital Rings shows all verified mandatory requirements; a one-of target displays alternatives as a fork; an already researched target is complete; a current project is marked in progress; a granted/event technology is not promised as a normal draw; tier and other availability conditions are separately explained; a missing or mismatched DLC/mod/release gives an Unknown or limited-data state; two campaigns with the same empire name do not share progress; a newer save refreshes the open route without stale advice; the exact 2277.10.01 fixture is checked against its installed 4.5.2 rules; and Edge's Close button closes only this route window. Verify source game files and at least one in-game observation before treating a disputed upstream path as game truth.

**Gate:** a nontechnical Windows player can open, understand and close the focused route without installing development tools; the route reflects the selected save and applicable rules; ambiguous requirements and random draws are not presented as guaranteed steps; distribution and notice requirements are resolved before release.

### 5. AI chat evidence harness for questions and screenshots

The built-in guide remains the fallback when Ollama, LM Studio or OpenRouter is unavailable. The model explains a bounded, question-specific evidence packet; it does not inspect the full hidden save or replace deterministic facts. The packet must contain:

- Save release and date, installed release/checksum if separately known, and mismatch status.
- Player empire identity, relevant economy, policies and goal; contacted empires relevant to the question with their player-visible intel and relationships. Include stable country/planet IDs where available.
- Save-recorded required DLC and mods, with exact labels and whether current activation is verified. A modded rule is conditional until checked.
- Relevant planet, technology, ship or event evidence retrieved by name/ID from the whole selected snapshot. Do not send only the first four or eight items when the player asked about another one.
- Rule cards with source version, prerequisites, exceptions and spoiler level, plus a snapshot timestamp. Do not derive hidden facts into goal text while spoilers are off.

For an image question, first identify the visible screen and transcribe only legible observations. Then match the observed entity to the save; if there are multiple matches, ask or report uncertainty. Compare screenshot time with save time. If text is too small, request a tighter crop. The response must never claim to see an unreadable number or infer unseen fleet strength.

The proposed model output is a structured answer with observation IDs, rule IDs, assumptions, next actions, in-game checks and unknowns. Validate referenced IDs and values in the application before display; a valid JSON shape alone is not proof of strategic correctness. Screenshot pixels and OCR text are untrusted data, not instructions. Check image capability before sending a screenshot. Cloud screenshot transmission needs a clear player-facing indication; local providers remain available. The existing screenshot-history exclusion should remain. For slow local models, research preflight/loading state, bounded context, streaming or progress feedback and cancellation before changing timeout policy.

**Gate:** named entities beyond current truncation limits are answered with the right record; stale save versus screenshot is identified; unsupported DLC/mod rule is qualified; adversarial text in a screenshot cannot change system instructions; spoiler-off context contains no hidden values; a non-vision model never pretends to analyze an image.

### 6. UI and copy regression pass

Reproduce the repeated sidebar entries and Watchlist overlap visible in the supplied images using the packaged v1.5.2 build and same viewport before fixing. Keep the ticker rotating without overlap. Make the leading card and risk indicator scannable; retain keyboard access and the graph without a long scroll. Reduce generic repeated disclaimers while preserving explicit checks for real uncertainty. Lead installation and Settings copy with “works offline; AI is optional.”

**Gate:** Main and Tech Tree pass the review viewport and a narrower one; destinations appear once; ticker rotates cleanly; the pinned goal, risk indicator and graph remain understandable.

## 4.5.2 rule checks completed in research

| Mechanic | Verified in installed Cygnus 4.5.2 definitions | Advice implication |
| --- | --- | --- |
| Consecrated Worlds | The perk requires Spiritualist and non-Nomadic status. The decision requires a valid uncolonized target and is limited to three worlds; eligible classes and exceptions have their own triggers. Source: common/ascension_perks/00_ascension_perks.txt and common/decisions/02_special_decisions.txt. | Check eligibility and the cost of a perk slot or uncolonized world before suggesting it. |
| Automation building | The inspected Technician automation building grants 25% automated workforce at level 1 and 50% at level 2, with energy upkeep. Source: common/buildings/01_pop_assembly_buildings.txt. | Verify other job types separately; compare useful freed workforce and upkeep. |
| Hyper Relay | The ordinary route uses 500 alloys, 100 rare crystals and 25 influence, with 2 energy upkeep; bio-ship and Flash Forge cases alter cost. Source: common/megastructures/14_hyper_relay.txt. | Do not quote one universal cost. Check a connected route and the actual empire. |
| Military policy | Separate fleet, starbase and platform preferences are present. Starting doctrine is randomized in 4.5.2. Source: common/policies/06_policies_fleets_and_starbases.txt and final 4.5.2 notes. | Read saved selections; do not infer them from empire identity. |
| Dangerous technology and crisis | Jump Drive or Psi Jump Drive can satisfy one earlier endgame-crisis start condition after the endgame year. The inspected Contingency selection branch has no research weight. Source: events/crisis_trigger_events.txt. | Distinguish crisis timing from crisis identity. Do not repeat the older article's claim that this research makes the Contingency more likely. |

These checks validate specific claims, not every game mechanic, every mod override, or the optimal strategy. Installed definitions are a stronger source for the unmodded rule than a tier list, but actual modded behavior and save interpretation still need fixtures.

## Research inventory: all 16 linked strategy articles

Each entry is a candidate knowledge card. “Conditional” means its recommendation depends on the empire, DLC, game settings, unlocked technology or observed enemy. “Spoiler-gated” means do not surface undiscovered outcomes by default.

| Article | Useful knowledge to retain | Trust condition |
| --- | --- | --- |
| [Consecrated Worlds](https://gamerofpassion.com/stellaris-how-does-consecrated-worlds-work/) | Eligibility, limited targets, perk opportunity cost. | Core triggers checked above; exact rewards and exceptions need targeted tests. |
| [Best Ascension Perks](https://gamerofpassion.com/stellaris-best-ascension-perks/) | Compare prerequisites, empire goals and scarce perk slots. | Subjective ranking; article checked against 4.5.1, so retest on 4.5.2. |
| [Best Fleet Composition](https://gamerofpassion.com/stellaris-best-fleet-composition/) | Hull roles, range, tracking and counterplay. | Conditional; test against 4.5.2 enemy designs, policies and costs. |
| [Best Titan Build](https://gamerofpassion.com/stellaris-best-titan-build/) | Aura choice and long-range role. | Conditional on unlocks and enemy defenses; no fixed best loadout. |
| [Precursor Tier List](https://gamerofpassion.com/stellaris-precursor-tier-list-ranking-all-9-precursors/) | Different rewards help different campaign goals. | Subjective and spoiler-gated; DLC and discovered identity matter. |
| [The Doorway](https://gamerofpassion.com/stellaris-the-doorway-explained/) | Random event outcomes and uncertainty. | Spoiler-gated; only explain outcomes when requested or discovered. |
| [Leviathan Traits](https://gamerofpassion.com/stellaris-leviathan-traits-every-guardian-reward-explained/) | Guardian rewards and timing can matter. | Verify exact 4.5.2 event triggers and counters; spoiler-gated. |
| [Fallen Empire Counter](https://gamerofpassion.com/stellaris-fallen-empire-counter-how-to-actually-deal-with-one/) | Dormant versus awakened, fleet design, access and war readiness. | Conditional; difficulty and Fallen Empire strength settings defeat fixed power thresholds. |
| [Transport Ships](https://gamerofpassion.com/stellaris-transport-ships/) | An invasion needs armies and a safe route, not just naval strength. | Verify army availability and transport safety for the actual war. |
| [Automation Building](https://gamerofpassion.com/stellaris-automation-building/) | Workforce freed by relevant automation buildings versus upkeep. | Technician percentages checked above; other buildings and planet jobs need checks. |
| [Enigmatic Fortress](https://gamerofpassion.com/stellaris-enigmatic-fortress/) | Timed expedition and consequential choices. | Spoiler-gated; verify event sequence before showing solutions. |
| [Hyper Relays](https://gamerofpassion.com/stellaris-hyper-relays/) | Connected route planning and defensive travel. | Core costs checked above; empire-specific exceptions matter. |
| [Ship Design](https://gamerofpassion.com/stellaris-ship-design/) | Slots, range, power and combat-computer trade-offs. | Conditional on actual unlocked components, policies and enemy evidence. |
| [War in Heaven](https://gamerofpassion.com/stellaris-war-in-heaven/) | Alliances, neutrality and League choices have trade-offs. | Conditional and spoiler-gated; “stay neutral” is not a universal rule. |
| [Contingency](https://gamerofpassion.com/stellaris-contingency/) | Ghost Signal response and crisis preparation once observed. | Spoiler-gated; exact event rules need 4.5.2 verification. |
| [Dangerous Technology](https://gamerofpassion.com/stellaris-dangerous-technology/) | Historical explanation of why certain technologies feel risky. | Older probability claims conflict with the inspected 4.5.2 crisis-selection branch; do not use them as current facts. |

Do not import these articles wholesale into prompts. Turn supported mechanics into short versioned rule cards, keep subjective strategic views identified as such, and expose event spoilers only by player choice.

## Acceptance examples and evaluation

1. Short food runway with energy available: explain depletion date and propose an in-game Market check as a bridge; then a supported production fix.
2. The exact 2277.10.01 save: report 11,731.4 food and about 205 months of cover, not “buy today”; show low stability on Alpha Centauri Prime as an independently visible concern.
3. The same saved deficit with ample versus little food produces different severity and next action.
4. Destroyers progress increasing across the four 2277 saves is not called stalled. Without a verified total research cost, no percentage or ETA appears.
5. Large alloy stock with unknown naval capacity and low rival intel does not trigger an unconditional ship order.
6. A pinned goal stays on top after refresh while a genuinely urgent risk remains visible separately.
7. Known empires appear only with player-visible intelligence while spoilers are off. The player empire remains the baseline in comparisons.
8. A question about a planet or contacted empire beyond the first eight retrieves that entity rather than answering from a truncated summary.
9. An image question with unreadable text says what is uncertain; a non-vision model does not claim visual analysis. A screenshot newer than the save is labelled as such.
10. The chat includes save release, player empire, required DLC and recorded mods with provenance, and qualifies advice that a mod may change.
11. No model configured: Main, goals, built-in questions and in-game checks still work.
12. Recheck 4.5.2 knowledge against later patches, DLC and mods before carrying any “verified” badge forward.

Evaluate providers on the same curated question/image cases: factual grounding, unsupported claims, spoiler leaks, false visual claims, action usefulness, response time and provider failure behavior. Include adversarial screenshot text and missing-data cases. Do not treat a fluent answer or valid structured output as an accuracy test.

## Implementation map for a future authorized build

| Work | Likely area | Required proof |
| --- | --- | --- |
| Campaign metadata and fixture preparation | Save parser and scrubbed tests | Exact date, release, required DLC, mods and empire identity survive extraction; originals stay outside package. |
| Resource and planet reasoning | Save parser, strategy and advice | 205-month versus short-runway counterexample; jobs versus employed workforce. |
| Recommendation record, pin and alert | Strategy, server state and Main UI | Stable IDs; pinned goal survives refresh; serious risk remains visible. |
| Research and military policy explanation | Technology parser, policy mapping and UI | 2277 Destroyers trend, saved 4.5.2 policy labels and no invented ETA. |
| Focused technology route feasibility and UI | Technology model/extractor, selected-save context, locally served Edge window | Mandatory versus one-of routes, current research, version/DLC/mod match, offline package and window-specific Close pass the section 4a acceptance cases. |
| Chat evidence and image harness | Server, built-in chat and provider adapters | Targeted retrieval, schema/reference validation, spoiler isolation, vision detection and stale-date handling. |
| Visual and copy pass | Main, sidebar, ticker, Settings and installation guide | Reproduce and resolve confirmed screenshots at matching viewport; offline promise remains clear. |
| Packaging | Windows package and guides | Version badge, ZIP integrity and clean tray quit, only after implementation is authorized. |

## Outside v1.6 unless separately approved

- A universal numeric fleet-power target derived from game year alone; optimal Titan or fleet composition; automatic ship edits.
- Exhaustive mod compatibility adapters, DLC-specific strategy for every pack, and broad event/precursor spoiler guides. Campaign metadata and rule applicability checks are in scope; comprehensive mod-specific mechanics are not.
- New espionage screens, hidden-rival disclosure without the existing double-confirmed spoiler choice, and a full scenario simulator.
- A claim that every modded technology route is supported before its actual playset has been extracted and checked; automatic selection of technology in the game; guaranteed research draw or completion dates.
- An unvalidated community-editable rule language or public contribution pipeline.
- A mandatory player questionnaire. Optional experience, roleplay and long-term goal preferences can be considered after the evidence foundation works.

## Source trail

- Supplied product-review-claude.md, its five StellarisGuide screenshots, and the exact 2277.10.01 autosave; [review triage](CLAUDE-REVIEW-TRIAGE.md).
- [Cygnus 4.5 strategy research](CYGNUS-4.5-STRATEGY.md), user-supplied final 4.5.2 patch text (checksum 9776), and installed Stellaris common and events definitions listed above.
- [Paradox 4.5.2 development notes](https://forum.paradoxplaza.com/forum/developer-diary/stellaris-dev-diary-434-4-5-2-cygnus-tentative-patch-notes.1943322/) are preliminary; prefer final notes and installed 4.5.2 definitions for released behavior.
- [Ollama vision](https://docs.ollama.com/capabilities/vision), [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs), [LM Studio developer documentation](https://lmstudio.ai/docs/developer), [OpenRouter structured outputs](https://openrouter.ai/docs/structured-outputs), and [OWASP prompt-injection guidance](https://genai.owasp.org/llmrisk/llm01-prompt-injection/).
- The 16 Gamer of Passion sources are linked individually in the research inventory. Their conclusions are not equivalent to validated 4.5.2 rules.
- [YThibos/Stellaris-Tech-Tree README](https://github.com/YThibos/Stellaris-Tech-Tree/blob/41d811d0ca1efdcb01f2eaa47ac77fb4a1a70daa/README.md), [technology and graph model](https://github.com/YThibos/Stellaris-Tech-Tree/blob/41d811d0ca1efdcb01f2eaa47ac77fb4a1a70daa/src/domain/tech-tree.ts), [save reader](https://github.com/YThibos/Stellaris-Tech-Tree/blob/41d811d0ca1efdcb01f2eaa47ac77fb4a1a70daa/src/save/save-research.ts), [snapshot manifest](https://github.com/YThibos/Stellaris-Tech-Tree/blob/41d811d0ca1efdcb01f2eaa47ac77fb4a1a70daa/public/data/4.5.2/snapshot.json), [licence](https://github.com/YThibos/Stellaris-Tech-Tree/blob/41d811d0ca1efdcb01f2eaa47ac77fb4a1a70daa/LICENSE) and [third-party notices](https://github.com/YThibos/Stellaris-Tech-Tree/blob/41d811d0ca1efdcb01f2eaa47ac77fb4a1a70daa/THIRD-PARTY-NOTICES.md), reviewed October 18, 2026.
- [MDN `Window.close()` behavior](https://developer.mozilla.org/en-US/docs/Web/API/Window/close) supports the Edge-window feasibility gate; Windows-specific close behavior still requires a packaged-app test.

**Authorization:** the player requested phased implementation on October 18, 2026. Follow the implementation plan's phase gates, usage-limit checks and independent review policy before release.
