# Strategy and diplomacy research for the next release

Reference reviewed: [Dfintz/Stellaris_Overmind](https://github.com/Dfintz/Stellaris_Overmind). Its README and source describe a Stellaris **4.4.6** advisor/AI project that reads autosaves, extracts active policies and known empires, filters foreign information by intel, and periodically revises a strategic plan. Stellaris Guide remains a player-controlled, read-only dashboard for **4.5 Cygnus**.

## Features to adopt, in priority order

| Feature | What Stellaris Guide should recommend | Evidence required from the save |
| --- | --- | --- |
| **Policy check** | Show a specific current policy, a possible alternative, how it supports a current goal, and the trade-off. Example: consider an economy setting that supports fleet production only when the empire can actually select it and the resource balance permits it. | Player ethics, civics/government, active policy, available options or validated game rules, resource trend. |
| **Diplomacy and threat advice** | Recommend actions toward a *named contacted empire*: improve relations, seek a pact, prepare defenses, or delay a war. Explain the evidence and what remains unknown. | Contact, opinion/attitude, agreements, active wars, visible or relative strength, intel level. |
| **Plan refresh after meaningful change** | Keep the 5–10 year goal and its steps stable between saves, then re-evaluate when a war starts, a new neighbor appears, a deficit begins, a colony is founded, or a goal is met. Show what changed and why the recommendation changed. | Previous and latest snapshots with the same campaign identity and dates. |
| **Empire-aware advice** | Check ethics, civics, origin, and government before suggesting a policy, diplomatic action, or strategic path. | Player empire fields from the save and version-matched game rules. |

These recommendations belong directly below the relevant item in **Your next moves**, following [NEXT-RELEASE.md](NEXT-RELEASE.md). A policy or diplomacy suggestion should be an actionable step toward a goal, not a disconnected list of tips. The player always decides and acts in Stellaris.

## Guardrails and exclusions

- Use only knowledge the player could reasonably have from contact and intel. Do not reveal exact hidden enemy power because the save contains it internally. When confidence is low, say “strength unknown” and suggest scouting or improving intel.
- Verify a policy or diplomatic option against **4.5 Cygnus** and the player's empire before calling it available. Overmind's phase-based policy defaults and static 4.4.6 strategy tables are references, not rules to copy.
- Use deterministic checks for eligibility and save facts; the optional LLM may explain and prioritize valid candidates. If the LLM times out, retain the evidence-based guidance.
- Do not add Overmind's AI-empire control, mod bridge, automated policy changes, or multi-agent orchestration to this read-only player companion.

## First validation pass

On a representative 4.5 save, confirm where active policies, ethics/civics, contact, intel, opinion, agreements, and wars are stored. Compare a few generated suggestions with the game's available actions. Test one new-war and one new-deficit transition across consecutive autosaves. Only show advice for fields verified in that save format.
