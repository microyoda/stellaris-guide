# Upcoming release notes — planning only

**Recorded October 22, 2026.** These are player requests and acceptance ideas, not a release tag or authorization to implement. Do not build, package, or assign a version until the player explicitly asks.

## Tech Tree: see where a suggested card leads

The current route window shows illustrated technologies one or two dependency steps after a researched card. The next version should let the player select a suggested card and understand the **larger research path**: what the card can lead toward, what remains between the current research state and a chosen target, and which later benefits the path may unlock.

- Show direct requirements separately from earlier chains and later opportunities. Trace only edges supported by the selected game's technology definitions; never light unrelated prerequisite branches.
- For each later card, show the route to it, the next actionable research step, known blockers (other prerequisites, alternative requirements, tier gates, DLC, mods), and a clearly labelled **possible next target**. Research draws and estimated timing must not be promised when the save cannot support them.
- Keep artwork on the suggested cards and route details, with a readable fallback only when the game's asset cannot be resolved.
- Let the player compare suggested targets by their verified outcomes so the next choice has context rather than showing only a technology name and dependency distance.

## Tech Tree: explain every technology card

Every technology card, including current, researched and suggested cards, should have a short plain-language explanation:

1. **What it is:** one or two sentences describing the technology.
2. **What it gives you:** concrete, verified effects or unlocks such as buildings, districts, components, edicts or other opportunities, when supported by the selected ruleset.
3. **Why consider it now:** a save-grounded reason tied to the player's economy, planets, fleet or chosen target; show “No specific recommendation yet” when evidence is insufficient.

Study the installed, versioned game definitions and localisation before writing benefits. Respect DLC and mod uncertainty. Distinguish an immediate benefit from a later technology that merely becomes reachable; mark effects **unverified** when they cannot be mapped reliably. Avoid universal “best technology” claims.

## Fleet design: ship-class suggestions and chosen enemies

Add practical design suggestions for each ship class the player has unlocked, starting with **Corvettes, Frigates and Destroyers**. Show each design's role, suggested components and defenses, approximate resource/upkeep implications where the save and installed rules support them, and the trade-offs against other available designs. Use artwork for ship classes and components when assets can be resolved.

Let the player choose **who or what they plan to fight**. A future fleet design calculator can compare a small number of candidate builds against enemy information the player can actually see, or against equipment the player enters after observing it in game. Explain *why* a build may counter the known threat and what information would change the recommendation. When the enemy loadout is unknown, give a general-purpose baseline and an in-game inspection checklist rather than claiming an exact counter or a guaranteed win.

Use the installed, versioned game definitions for hull slots, components, prerequisites, policies and costs. Treat community fleet builds and matchup tests as labelled strategy candidates with source date, game version, assumptions and review status. Respect the selected save's unlocked components, DLC and mods. Keep hidden enemy designs outside ordinary spoiler-off advice. Do not use fleet-power totals alone to predict combat outcomes.

The player-facing layout, recommendation records, candidate selection rules and acceptance cases are detailed in [FLEET-DESIGN-FINDER-PLAN.md](FLEET-DESIGN-FINDER-PLAN.md). The screenshot informs the layout; its ranking metric and “best” wording are not adopted as proven combat advice.

## Built-in guide: answer the question actually asked

The source review, question-understanding design, staged work packages and acceptance gates are in [Built-in Guide answer quality: research and action plan](BUILT-IN-GUIDE-ANSWER-QUALITY-RESEARCH.md). Use that document when this fix is authorized for implementation.

The screenshots from save **2301.10.01** show four relevance failures: an espionage question, an Alpha Centauri Prime policy question and an Alpha Centauri Prime population question all receive the same unrelated amenities goal; a Dangal Prime economy question receives empire-wide monthly totals instead of planet-specific help. The current built-in routing chooses broad keywords or the highest-priority campaign goal before identifying intent and named entity. These are answer relevance failures, not evidence that the underlying save figures are wrong. Fix them in the next release; do not change the running application as part of this note.

- Build a small, versioned knowledge base for common how-to questions, starting with espionage and diplomacy. Separate **game rules and prerequisites** from **save-specific facts** and **community strategy**. Prefer verified 4.5 game definitions and official guidance; cite the source/version in the expanded explanation and mark DLC or mod uncertainty.
- Identify the player's intent and named subject before choosing an answer: for example, *how to start spying*, *what is my intel on Empire X*, and *should I run an operation* are different questions. Recognize natural wording, plurals, common misspellings and `/ask` without requiring exact keywords. Reuse the existing lightweight routing pattern first; add an NLP dependency only if measured cases justify it.
- Retrieve only evidence relevant to that intent from the selected save. For a how-to question, give short in-game steps and distinguish what is generally possible from what the Guide can confirm for this empire. For an empire-specific question, use only player-visible intel while spoilers are off. Do not infer an available envoy, spy network, operation, influence cost or policy from missing save fields.
- If an intent or required fact is unsupported, answer that directly and offer the next in-game check or a clarifying question. Never substitute the top campaign goal as an answer to an unrelated question. The same relevance rule applies when Ollama, LM Studio or OpenRouter fails and the built-in guide takes over.
- Keep the answer compact: **direct answer → steps or relevant save evidence → uncertainty/next check**. Show the save date where a stale autosave might affect the answer. Do not turn a general mechanic question into advice about a different colony, technology or fleet.

**Acceptance cases:** All four screenshot questions receive answers about their stated topics and named entities or a candid information limit. Spy-network how-to, contact intel, colony growth, colony management and local economy questions route to distinct answers. An unknown question or optional-provider failure never receives unrelated next-move text. Tests include a mistyped or missing colony name, an empire-wide economy question for contrast, missing espionage or growth fields, spoiler-off hidden rival data, DLC/mod uncertainty and a named contact.

## Related next-release work

The reviewed strategy-playbook backlog, including Expansion and Discovery traditions, community suggestions, policy eligibility, AI chat checks and the open visual acceptance check, remains in [strategy-playbooks.md](strategy-playbooks.md#next-increments). Coordinate Tech Tree target explanations with those playbooks once both use verified save facts.

## Acceptance examples to prepare before implementation

- A suggested card can be opened to show a correctly traced larger path and a short explanation of what researching it provides.
- An already researched card can show its next one or two links without implying that those links are currently offered as research choices.
- Xeno Diplomacy II keeps Federation Code as its direct requirement; an upstream Societal Unification route appears only when it is genuinely needed for the selected save's target path.
- A technology with missing DLC, mod-altered definitions or an unknown unlock shows the uncertainty instead of a guaranteed benefit.
- For an unlocked Corvette, Frigate or Destroyer, the Guide can explain a feasible baseline design and why its components fit the intended role; locked or unaffordable parts are labelled rather than presented as ready to build.
- A selected enemy with visible or player-supplied equipment can produce a conditional counter suggestion and its assumptions. With unknown equipment, the Guide avoids an enemy-specific claim.
