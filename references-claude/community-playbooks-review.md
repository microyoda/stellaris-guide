# Review: reviewed community playbooks

Reviewed 21 October 2026 by the Claude advisor thread. Target game: Stellaris 4.5.2 "Cygnus" (checksum 9776).

What I read: the proposal (Yoda, 21 Oct 2026); the advisor knowledge base in `claude-advisor/knowledge-base/` (README, files 01, 06, 07, 11, 12, 13 and 14); `Stellaris-Dashboard/stellaris_guide/strategy.py` (all 388 lines, focus on `make_plan` at line 272); `stellaris_guide/saves.py` (what the save parser actually reads); and `docs/RELEASE-1.6-PLAN.md`. Nothing in `Stellaris-Dashboard/` was changed.

## Verdict

**Go ahead, with five corrections.** The idea is sound and fits the 1.6 plan: playbooks are tier 4 ("community strategy article") in the plan's evidence hierarchy (RELEASE-1.6-PLAN.md, line 18), and starting with a small reviewed set instead of an open feed matches the plan's exclusion of "an unvalidated community-editable rule language or public contribution pipeline" (section "Outside v1.6"). Both cited lines are correct: `make_plan` starts at strategy.py line 272, and the evidence hierarchy starts at line 18.

The proposal assumes the Guide can already see more of the save than it does, and it assumes a pool of current community advice that mostly doesn't exist yet. Fix those two things and the plan holds.

## Corrections

### C1. Most of the "conditions" in step 2 can't be read from the save today

I checked `saves.py` for every fact the proposal lists:

| Fact the proposal checks | Read today? | Evidence | What it would take |
| --- | --- | --- | --- |
| Selected traditions | **No** | No `tradition` parsing anywhere in `saves.py` | New parser field plus a fixture |
| Available policies | **No, only selected ones** | `parse_policies` (line 306) reads `policy=… selected=…` pairs | Evaluating each option's `potential`/`allow` triggers; see C3 |
| Resources (incl. influence, unity) | Yes | `RESOURCES` (line 19) includes unity and influence | — |
| Planets | **Owned colonies only** | Colony loop around lines 435–483 | Unowned, surveyed, habitable worlds near borders are not parsed |
| Technology | Yes (current projects, researched) | `technology.py`, plan section 4/4a | — |
| Campaign stage | **No such field** | Only `year` is derived in `make_plan` | A definition built from observed facts, not the year (the plan already rejects year-only fleet targets) |
| Known rivals | Partly | Contacts with opinion and intel (lines 841–898) | Must respect the spoiler-off rule |
| Ethics, civics, origin, authority, Nomad status | **No** | Not parsed | Needed for almost every "suitable empire type" check |
| Exploration left (surveyed vs unsurveyed systems) | **No** | Not parsed | Needed for the Discovery example |

So the two worked examples in the proposal (Expansion: "nearby worlds, influence and supporting economy"; Discovery: "changes when exploration opportunities run out") each depend on at least two facts the Guide doesn't have. Under the proposal's own rule ("if a required fact is missing, show it as something to investigate"), both would always show as "investigate". **Recommendation:** list the parser fields each starter playbook needs, and schedule that parser work (with fixtures) before or with the first playbooks. Pick starter playbooks partly by how many of their conditions are already readable.

### C2. There is very little current community advice to review

From the Steam crawl (knowledge-base file 14): **only 1 of 280 Steam guides was updated after 4.5.0 shipped (22 Sep 2026) and covers gameplay**, and it is a Russian fleet-build guide (SG1). The popular "4.5" ship guide (SG2) was last edited before release. Gamer of Passion articles are a mix of 4.5-rewritten and pre-4.5 (file 11, X9–X11). The knowledge base has **no 4.5 source at all for the Expansion or Discovery tradition trees**. Player reports in Steam discussions are useful as warnings but contradictory (file 12).

That changes what "community playbook" means in practice:

- For 4.5.2, most playbooks will be **written by us from installed game files and official notes**, with community sources cited as the idea or explanation, not as the evidence.
- Every community source needs its `time_updated` checked (the Steam file-details API gives it), and anything not updated since 22 Sep 2026 is pre-4.5. A title saying "4.5" proves nothing (file 14, guideline 1).
- Consider naming the feature **"reviewed playbooks"** or **"strategy playbooks"** in the UI. "Community" suggests the content came from players and was only lightly checked, which is the opposite of the trust you want.

### C3. "A policy recommendation must use a choice actually available to that player" is not checkable as written

The save stores the selected option, not which options are offered. Whether an option is offered depends on `potential` and `allow` triggers in `common/policies/*.txt` (ethics, civics, technology, DLC), plus cooldowns. The Guide doesn't evaluate those triggers, and partial evaluation would be worse than none because it would look authoritative.

**Recommendation:** have the Guide say "this option exists in your installed 4.5.2 rules and you don't have it selected; open Policies to check you can pick it and its cooldown." Only call an option "available" for policies whose triggers have been checked by hand and tested on fixtures. The existing `fleet_steps` already phrases it this way ("Check available choices, cooldown…"), so stay consistent with it.

### C4. Split "verified for this version" into two separate statuses

"Verified" is ambiguous. A playbook can have every mechanic correct for 4.5.2 and still be a poor strategy for most empires. The plan already separates "mechanic verified for the ruleset" (tier 2) from "tested strategy" (tier 3). Each playbook should carry both:

| Field | Values | Meaning |
| --- | --- | --- |
| `rules_status` | verified / conditional / needs recheck / conflict | Are the game-rule claims true for this version and DLC? Checked against installed files. |
| `strategy_status` | untested / tested on N fixtures / retired | Did it give sensible advice on the fitting and non-fitting fixtures? |

Make "needs recheck" **automatic**: when the save version or installed checksum differs from the playbook's validated checksum, the Guide should downgrade the playbook itself instead of waiting for someone to relabel it. This matters soon. 4.6 "Corona Borealis" with Willpower and Ideologies is announced (knowledge-base file 01; `docs/WILLPOWER-4.6-IDEOLOGIES.md`), and every 4.5.2 playbook should flip to "needs recheck" the day it lands.

### C5. Fleet matchups shouldn't be in the first set

Fleet matchups need the enemy's weapons, defenses and hull mix. With spoilers off, the Guide can only use what the player's intel reveals (plan section 3 gate), and most saves won't have enemy designs at all. File 14 also notes that fleet power doesn't predict fights and that the strongest current claims (flak over point defense, torpedo size bonus, Ancient Bastion) are player tests or open conflicts (C4, C5 in file 11). The plan also excludes "optimal fleet composition" from 1.6.

**Recommendation:** replace fleet matchups in the first set with a playbook the player starts by naming the threat ("I'm fighting strike-craft carriers" or "Prethoryn are coming"). That keeps hidden information out and makes the condition a player observation, which is tier 1 evidence.

## Additional recommendations

### R1. Choose a starter set the knowledge base can already support

Ranked by how much is already verified and readable:

1. **Resource deficit recovery** (food, energy, consumer goods). The runway logic and job-limit checks already exist in `resource_runway` and `resource_steps`; the 2277.10.01 fixture and its short-runway counterexample are planned. Player reports add useful warnings (job priorities resetting after a reload, pops avoiding surplus jobs; file 12).
2. **Unstable colony** (amenities, stability, unfilled jobs). Covered by the Alpha Centauri Prime fixture and the planet recommendation code.
3. **Expansion**, after C1's parser fields exist. **Exclude Nomads**: file 07 says not to give normal claim and colony-ship advice to Nomadic empires. Also respect file 12's "don't colonize every planet at once" and "build only when you have pops to fill jobs".
4. **Discovery**, after survey data is parsed, and with exploration outcomes spoiler-gated (the plan already marks precursors, The Doorway and the Enigmatic Fortress as spoiler-gated).
5. **Named-threat defense** (from C5), using the file 14 guidelines only as labelled player tests.

Ascension-path planning would make a good sixth: file 06 already has strict, checkable rules (take the path before the 7th tradition tree; colony ascension is +10% per tier, not +25%), but it also needs tradition parsing.

### R2. Fit playbooks into `make_plan` without breaking the current ranking

Things the builder will hit in `strategy.py`:

- `describe_priority` has no branch for new keys, so a playbook goal falls through to score 20, "Routine preparation", and sorts last. Give playbooks their own key prefix (e.g. `playbook:<id>`) and a score from the playbook's own urgency, capped below resource and colony emergencies.
- `enrich_goal` hard-codes `source_rule="Guide v1.6 heuristic"`. Playbook goals need the playbook ID, its revision and its `rules_status`, so the chat evidence packet and the UI can show where advice came from.
- `make_plan` returns `goals[:5]`. Limit playbook goals to one or two so they don't push out an urgent deficit. The player pin from plan section 3 should be able to hold a playbook goal on top.
- Progress baselines only understand `net:`, `opinion:` and top-level player fields. A 5–10 year target such as "colonies" or "surveyed systems" needs a metric the save actually records, or the progress bar will be wrong. Only give a numeric target when the metric is read from the save; otherwise show "check in game".
- Evaluate conditions as **true / false / unknown**, never as true/false only. "Unknown" is how the proposal's "something to investigate" state should be reached.

### R3. Store playbooks as data, not code, and validate them

Keep each playbook as a small JSON or YAML file with a fixed schema, loaded at startup and checked by a test. Conditions should reference only fact keys from a fixed list that the parser produces (so a typo or a fact the parser can't read fails the test, instead of silently becoming "unknown" for every player). This is not a community rule language, so it stays inside the plan's limits.

Example sketch:

```yaml
id: deficit-recovery-food
revision: 3
title: Recover a food deficit without wasting jobs
sources:
  - {tag: KB-03, kind: game-files, version: "4.5.2"}
  - {tag: KB-12, kind: player-reported, note: "job priorities may reset after reload"}
game_version: {validated_checksum: "9776"}
requires: {dlc: [], not_mods_touching: ["common/jobs", "common/pop_jobs"]}
empire_fit: {exclude: [machine_authority]}   # needs authority parsing (C1); machine empires don't use food
conditions:
  - {fact: player.net.food, op: lt, value: 0}
  - {fact: resource_runway.food.months, op: lt, value: 24}
actions: [...]        # 2–3 steps, each with action, reason, in-game check
target: {metric: "net:food", value: 5, years: 5}
change_course_if:
  - "Food stock rises for two saves in a row while net stays negative (cause unknown in the 2277 fixture)"
rules_status: verified
strategy_status: {tested_fixtures: [fx-2277-10-01, fx-short-runway, fx-missing-food]}
reviewers: [author, second-reviewer]
```

### R4. Make the review step concrete

Step 4 is right; make it a checklist the builder agent can run:

1. Every number in the playbook is traced to an installed 4.5.2 file path or a final patch note. A community number with no game-file match is removed or marked "players report".
2. Each playbook has **a fitting fixture, a non-fitting fixture and a missing-data fixture**. This is the plan's existing gate for every new rule ("positive case, counterexample, missing-data case").
3. The DLC check uses the save's `required_dlcs`, labelled as "recorded in the save", not ownership (file 13). A playbook naming a DLC feature is hidden or marked conditional when that DLC isn't recorded.
4. Mods: if the save lists mods that override the files a playbook depends on, mark the playbook "conditional". The current fixture already has one ("Planetary Diversity (4.1)").
5. The second reviewer is not the author (AGENTS.md rule 9) and reviews the evidence trail, not the prose.

### R5. Keep player feedback local and opt-in

The Guide works offline and is read-only, so "helpful / didn't apply / game rule changed" has nowhere to go by default. Store it locally with the playbook ID, revision, save version and date, and let the player export it as a file to share if they want to. Don't send it anywhere automatically. "Game rule changed" should also flag that playbook in the player's own Guide until the next playbook update.

### R6. Give the AI chat the playbooks, not the authority

Add the matched playbooks to the chat evidence packet as rule cards with IDs, status and unknown conditions (plan section 5). The model may explain and compare them but should not invent a new playbook or upgrade an "investigate" to an instruction. The app should check that every playbook ID the model cites exists and was matched for this save before showing the answer.

## Suggested order of work

1. Write the playbook schema and the review checklist (R3, R4). No parser change needed.
2. Ship the two playbooks that need no new parsing: resource deficit recovery and unstable colony (R1, items 1–2). This tests the whole pipeline on facts we already trust.
3. Add parser fields for traditions, ethics/civics/origin, Nomad status, nearby habitable worlds and survey state, each with a fixture (C1).
4. Then Expansion and Discovery, then named-threat defense.
5. Local feedback (R5) once at least three playbooks exist.
6. Recheck everything when 4.6 ships (C4).

## Sources

- Knowledge base: `claude-advisor/knowledge-base/` files 01, 06, 07, 11, 12, 13, 14.
- `Stellaris-Dashboard/stellaris_guide/strategy.py` lines 152–230 (`resource_steps`, `fleet_steps`), 236–388 (`describe_priority`, `enrich_goal`, `make_plan`).
- `Stellaris-Dashboard/stellaris_guide/saves.py` lines 19, 306–360, 435–483, 841–923.
- `Stellaris-Dashboard/docs/RELEASE-1.6-PLAN.md`: evidence hierarchy (line 18), sections 1, 3, 5, "Outside v1.6".
- `Stellaris-Dashboard/AGENTS.md` rule 9.
