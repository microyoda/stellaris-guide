# Built-in Guide answer quality: research and action plan

**Planning only — October 23, 2026.** This document does not authorize application changes, a package, or a release tag. It expands the built-in Guide item in [Upcoming release notes](UPCOMING-RELEASE-NOTES.md).

## Observed failures across the screenshots

On save **2301.10.01**, four different questions expose the same underlying problem: the Guide chooses a broad keyword or the top campaign goal before it understands **what the player asked about** and **which place or empire they named**. The colony goal may be useful elsewhere, but it does not answer these questions.

| Player question in screenshots | Current answer | Answer type the player needs |
| --- | --- | --- |
| “how to spy others empires?” | Alpha Centauri Prime amenities goal | Espionage how-to, with DLC and visibility limits. |
| “what policies shall i do in Alpha Centauri Prime?” | Same amenities goal | Clarify whether they mean empire-wide Policies, a planetary decision, designation or job settings; then explain only verified options relevant to that colony. |
| “how to increase population in Alpha Centauri Prime?” | Same amenities goal | Planet-specific growth/assembly/migration explanation and a check of actual blockers; say when those drivers are not readable. |
| “how to improve dangal prime economy?” | Empire-wide monthly balance | Resolve Dangal Prime as a planet first, then explain its recorded output, upkeep, jobs and constraints. If that planet is not found, ask for clarification rather than switching to the empire economy. |

Code inspection identifies two separate paths to repair:

| Current path | Observed limit | Planned correction |
| --- | --- | --- |
| `stellaris_guide/advice.py` → `answer_question` | A few keyword groups cover planets, technology, ships, economy and threats. Espionage has no route. Unmatched text falls through to the first next-move goal. | Classify the question first. Return an on-topic how-to, a relevant status answer, a clarification, or an explicit knowledge limit. Reserve next-move advice for an actual “what should I do next?” question. |
| `stellaris_guide/advice.py` → planet/economy answers | `planet_answer` gives one generic planet status and its existing recommendation; a missed name silently selects an urgent or first colony. `economy_answer` always reports empire totals, even when a planet is named. | Separate planet growth, policy/management and local economy intents. Resolve the requested planet before composing an answer; do not substitute a different colony or empire scope. |
| `stellaris_guide/chat_evidence.py` → evidence packet | Empire retrieval recognizes terms such as `empire`, `threat`, `war` and `diplom`, but not `spy`, `espionage`, `infiltration` or `intel`. An optional AI provider may therefore lack the relevant contact record too. | Use the same intent/entity result for built-in and optional AI retrieval. Include only relevant, player-visible records. |
| `stellaris_guide/saves.py` → planet and contact projections | Planet records include population, housing, amenities, jobs, production and upkeep; policy parsing records selected empire policies. Contact records include an intel value when parsed and a boolean indication that a spy network was found. The Guide does not yet verify each planet's growth drivers, planetary-action eligibility, infiltration, envoy assignment, operation eligibility or costs. | Audit fields against same-date 4.5.2 game screens before giving specific instructions. Missing fields mean **unknown**, never a fabricated blocker, zero or available action. |

This is a routing, scope and grounding defect first. A large language model or broad web scrape is not needed to prevent these mismatches. More knowledge is useful only after the Guide can select the right topic and entity and distinguish general rules from selected-save facts.

The screenshot's word **“empires”** happens to trigger empire retrieval for an optional AI provider. The missing `spy`/`intel` triggers affect other phrasings such as “How do I spy?” or “What is my infiltration?” The screenshot's actual failure occurs in the built-in answer route.

## What the versioned sources support

1. The basic espionage and Intel systems were introduced with the free 3.0 update; **Gather Intelligence** was part of that base system, while other operations were associated with **Nemesis**. This distinction matters when explaining DLC-dependent actions. [Paradox's 3.0 developer update](https://steamcommunity.com/games/281990/announcements/detail/3008940762696483706) and the [Nemesis product description](https://www.paradoxinteractive.com/games/stellaris/add-ons/stellaris-nemesis) are historical sources, not proof of every current 4.5.2 eligibility rule.
2. The official **4.5.2 Cygnus** announcement confirms checksum **9776**. It does not provide a complete current operation eligibility map. An espionage item in the preceding *tentative* patch notes must not be treated as a shipped 4.5.2 change. The installed game's definitions and a same-version in-game check must settle exact steps, prerequisites and costs. See **“Stellaris 4.5.2 released [checksum 9776]”** in the [official October 2026 announcements](https://steamcommunity.com/app/281990/announcements/?l=english).
3. Dev Diary **#429** explicitly places its vigilance, upgraded assets and other espionage ideas under **Summer Experiments** with no guarantee of shipping. Dev Diary **#435** describes ideological diplomacy and espionage updates with **Willpower/4.6**, not as current 4.5.2 rules. These are research leads, never 4.5.2 Guide instructions. [Experiment diary](https://steamcommunity.com/games/281990/announcements/detail/713410320354246996) · [Willpower diary](https://steamcommunity.com/games/281990/announcements/detail/668378128507208706).
4. The official 4.5 Cygnus release describes a **Pop Group storage rework** and warns that saves from 4.4 and earlier are incompatible with 4.5. This does **not** by itself establish a planet's population growth rate or that a particular policy can be selected. Do not confuse faction share changes inside Pop Groups with adding population to Alpha Centauri Prime. [Official Cygnus release announcement](https://steamcommunity.com/app/281990/announcements/?l=english).

**Source order for a rule card:** installed version-matched base-game and DLC/mod definitions plus localisation and in-game screen → final official patch notes → older official explanations as context → reviewed community tactics as separately labelled strategy. A preview, beta experiment or future expansion cannot override a current installed rule. Every rule card needs a game-version range, DLC condition, source, last validation date and recheck status. The planned loader should compare the saved game version with each card and mark mismatches “needs recheck”; on an unverified mod, downgrade to “check in game.” This loader behavior does not exist yet.

## Answer contract and compact knowledge schema

The Guide should answer in this order: **direct answer**, **two or three actionable steps or relevant saved facts**, then **what it cannot verify and where to check**. It should not print an unrelated next move. For a general question, game knowledge is enough; for a question about a named empire, save evidence and spoiler visibility also matter. Show the selected save date when making a current-status claim.

The current chat endpoint requires a selected readable save. Keep that behavior in this fix: if no save is selected, prompt the player to select one before answering, including for a general mechanics question. Offline mechanics-only chat without a save would be a separate product decision.

Proposed curated rule-card fields (a design, not an implemented API):

| Field | Purpose |
| --- | --- |
| `id`, `topic`, `question_intents`, `aliases` | Stable topic and natural-language triggers, including common plurals and misspellings. |
| `release_range`, `dlc_requirements`, `mod_status` | Prevent an answer from silently crossing game-rule versions. |
| `rule_claims`, `steps`, `required_save_fields` | Keep general how-to text separate from claims about the player's campaign. |
| `source_refs`, `validated_on`, `rule_status` | Let reviewers trace a rule to installed data or official notes; mark it for recheck on version change. |
| `strategy_status`, `strategy_conditions`, `tradeoffs` | Keep optional community tactics distinct from verified mechanics. |
| `unknown_response` | On-topic wording when eligibility or save facts cannot be verified. |

The first knowledge set should cover **basic espionage**, **planetary population growth**, **planetary economy**, and **policies versus planetary management**. Each card should be short and explicitly versioned. For espionage, explain how to find a contacted empire's controls and inspect whether a network can be established; confirm exact 4.5.2 UI labels and eligibility in game before publication. For planet questions, distinguish current planet facts from the causes of growth or output, which the parser may not know. For policies, distinguish selected empire-wide settings from a planet's designation, decisions and jobs; never call a currently selected policy an available alternative. A question about **how spying works** must not require a readable network in the save. A question about **my network against Empire X** must not invent its infiltration, envoy, assets or available operations.

## Question understanding and retrieval

1. **Normalize** `/ask`, case, punctuation, simple plural/verb variants and common typos. Preserve named empire and planet text for entity matching. Start with a small maintained English alias set; do not add an NLP package before a measured failure requires one.
2. **Classify intent, scope and answer mode** independently: mechanic how-to, current campaign status, recommendation/decision, comparison, screenshot interpretation, or unsupported/ambiguous; planet, empire, contact or general-rule scope. Topics include espionage, economy, population growth, planetary management, research, fleet, diplomacy and threat. “How do I spy?”, “Do I have a network?”, and “Should I steal technology?” are separate intents despite shared vocabulary. “Dangal Prime economy” is planet-scoped even though it contains the word `economy`. Use word boundaries and phrase evidence to avoid accidental substring matches.
3. **Resolve entities** against the full selected snapshot before choosing an answer function. Support safe spelling variations, but require clarification when a fuzzy match is ambiguous or weak. If two names collide, clarify which planet or contact is meant. A named colony must not override an espionage intent merely because its name appears in the question. For unknown contacts, ask the player to identify the empire in Contacts rather than selecting the first rival. Never silently replace an unmatched named colony with the most urgent colony.
4. **Retrieve facts** required by that intent. A how-to can use a version-matched rule card without foreign save data. A status answer needs the named, visible contact and verified fields. The optional AI packet should receive the same intent, rule card and relevant records, with source IDs. With spoilers off, hidden rival fields never enter the packet or built-in answer.
5. **Compose and check**: each sentence must answer the selected intent or explain a missing prerequisite. Reject unsupported numeric or availability claims. If no suitable rule card exists, say what is unknown and suggest the in-game screen to inspect. Provider errors use this same on-topic built-in path; a screenshot without a vision model must still say the image was not analyzed.

Do not use a model-generated classification as the only authority for spoiler disclosure, rule eligibility or a claimed save fact. A future statistical classifier can suggest an intent, but deterministic visibility and evidence checks remain final.

## Work packages for a later authorized implementation

| Order | Action | Evidence required before proceeding |
| --- | --- | --- |
| 1 | Capture **all four screenshot questions** as regression fixtures. Build a labelled set of real and paraphrased questions across supported and unsupported topics. Include general how-to, named-planet and named-contact status, DLC variants and provider fallback. | Each item has expected intent, entity, scope, allowed evidence and an acceptable answer/abstention; independently review labels. |
| 2 | Audit espionage and planet facts against one or more same-date 4.5.2 saves, installed definitions and in-game screenshots. Verify planet growth drivers, local resource figures, available planetary actions and policy eligibility separately from currently selected values. Record which fields are player-visible and which cannot be parsed reliably. | A field map with save path/key, UI location, version, DLC/mod conditions and missing-value behavior. Do not expand `saves.py` from guesses. |
| 3 | Add a small reviewed knowledge-card collection, starting with basic espionage, population growth, planet economy, and policies versus planetary actions. Keep mechanics and strategy statuses separate. | Each public claim has a source, version gate, DLC gate and reviewer; the planned loader marks stale cards “needs recheck.” |
| 4 | Replace keyword fall-through with intent/entity routing in `advice.py`. Share the routing result with `chat_evidence.py` and `server.py` so both built-in and optional-provider fallback retrieve the same relevant evidence. | Success and failure tests for every intent; unrelated goal never appears for an unknown question. No new dependency unless the labelled set shows a concrete gap. |
| 5 | Add answer relevance and grounding checks plus a small local evaluation report. Review confusing cases before expanding topics. | The screenshot case passes; no spoiler leaks; unsupported facts are marked unknown; latency and offline behavior stay acceptable. Independent code review and separate security review for visibility/provider-boundary changes. |

## Acceptance gates and measurement

- **Exact screenshot regressions:** On the 2301.10.01 fixture, spying yields an espionage answer; the Alpha Centauri Prime policy and population questions get distinct, planet-relevant answers or clearly stated missing-data limits; the Dangal Prime economy question gets local evidence or asks which planet was meant. None returns the same generic amenities goal or empire balance as a substitute.
- **Entity mismatch:** A slight spelling variation can be matched only when one saved name is unambiguous; an unknown or ambiguous name triggers clarification and never substitutes the most urgent colony.
- **Scope:** “What is my economy looking like?” remains empire-wide. “How is Dangal Prime's economy?” is planet-scoped. A selected empire policy is not presented as a verified eligible alternative or as a planet-specific switch.
- **Intent separation:** “How do I build a spy network?”, “Do I have a network on [contact]?”, “What intel do I have on [contact]?” and “Should I run an operation against [contact]?” each take distinct paths. If a contact name is absent or ambiguous, the answer asks for the missing target.
- **No invented state:** no readable network, missing intel, no Nemesis, modded operations, stale save and older game release each produce appropriately limited answers. A missing parse result is not a negative game-state claim.
- **Provider failure:** the built-in fallback stays on topic when Ollama, LM Studio or OpenRouter times out; image failures never imply the image was seen.
- **Privacy and scope:** spoiler-off tests include hidden enemy network/operation data in the raw save and verify it never reaches answer text or model packet. No chat question or screenshot is added to telemetry by this feature.
- **Evaluation:** record topic accuracy, answer relevance, unsupported-claim count, correct abstentions and response time on a held-out labelled set. Release gate: **zero unrelated-goal fallbacks and zero known spoiler leaks**; review every failure before broadening the knowledge base. Report sample size and coverage instead of claiming universal NLP accuracy.

The first implementation should solve the visible mistake with a small, reviewed system. Broader strategy and community advice can be added only after the question classifier and rule provenance have passed these gates.
