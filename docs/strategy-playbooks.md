# Strategy playbooks: first implementation and review gate

The Guide's first playbooks annotate existing next moves for resource deficits and unstable colonies. They do not add goals, change ranking, alter saves, or claim that a policy is available. Expansion, Discovery, named-threat fleet advice and community submissions are later work because the required save facts or evidence are not yet available. See `references-claude/community-playbooks-review.md` for the critique that set this scope.

## Trust and display

- `stellaris_guide/playbooks.json` is bundled, reviewed application data. It is not loaded from a user-provided save or a remote feed. Each playbook has an ID, revision, game release, installed checksum, source references, conditions, trade-off and change-course signal.
- Conditions may use only a fixed list of facts the parser already produces. They evaluate to **matched**, **not matched**, or **investigate** when a fact is missing. A typo or unsupported fact fails validation before the app starts.
- `rules_status` describes the game-rule claim; `strategy_status` describes testing of the advice. They are separate. A different save release, installed release or installed checksum automatically changes the effective rule status to **needs recheck**. Missing version/checksum or any recorded mod makes the status **conditional**. A save does not independently prove which mods alter these mechanics.
- A playbook whose rule status needs recheck remains visible as a warning on its existing goal. Playbook metadata never replaces the goal's source rule, trade-off, steps or ranking. Retired playbooks are suppressed.
- The default playbook data marks rule claims **conditional** and strategies **untested** until an independent review checks the source details and test fixtures. The 50 stability threshold and runway urgency bands are Guide heuristics, not universal game-rule thresholds.
- UI copy says “Strategy playbook” because these initial records were authored for the Guide from installed rules and existing Guide heuristics. A community article may supply an idea later, but is not evidence that the game implements a mechanic.

## Review checklist for each playbook

1. Record the precise installed game file or final patch note behind every mechanics claim, and distinguish Guide thresholds from game rules. Record the date and game version of any community source. Summarize it without copying its text.
2. Confirm every condition is readable from the save. Test a fitting save, a non-fitting save and a save missing a required fact. Record the fixture names in the playbook before changing its strategy status to tested.
3. Test the validated save release and installed checksum, a later release, a different checksum, missing installed context and a save listing mods. Do not assume a recorded DLC label proves current ownership, or a mod name proves which files it overrides.
4. Inspect player-facing text for hidden enemy facts, policy eligibility claims, invented numeric progress and commands the player cannot carry out. Keep spoilers off unless the player's existing setting permits them.
5. Obtain an independent reviewer for code and evidence. Obtain a separate security review before adding remote contributions, user-editable rule data or cloud transmission. Keep local feedback opt-in and export-only until separately designed.

## Next increments

**Planning note, October 22, 2026:** These are candidates for a future release, not authorization to implement or create a new release tag. Wait for the player's explicit request before building or packaging the next release.

Tech Tree route and card-explanation requests are recorded separately in [UPCOMING-RELEASE-NOTES.md](UPCOMING-RELEASE-NOTES.md).

1. Finish the open visual acceptance check for the packaged 1.6.3 goal card when the player authorizes opening the isolated local dashboard. Keep the existing package and running older releases undisturbed until then.
2. Validate the two starter playbooks against fitting, non-fitting and missing-data saves plus the corresponding in-game screens. Keep game-rule accuracy and strategic usefulness as separate statuses. Recheck automatically when the save release or installed checksum changes, and show mod uncertainty honestly.
3. Parse traditions, ethics, civics, origin, authority/Nomad status, nearby unowned habitable worlds and survey progress. Add positive, negative and missing-data fixtures for each field. Define campaign stage from observed facts rather than the year alone.
4. Add Expansion and Discovery playbooks only when their conditions can match a real save. They should connect selected traditions to concrete 5–10 year development steps, possible later synergies and a reason to change course. Policy ideas must say an option exists in the installed rules and tell the player to check the Policies screen; call a policy “available” only after its eligibility rules and cooldown are evaluated and tested.
5. Keep versioned installed game definitions and official patch notes as the rules authority. Review community submissions as optional strategy ideas with author, link, update date, applicable release, conditions and trade-offs. Do not import rankings or fleet recipes as facts. Start with a small reviewed collection and let players submit suggestions for human review before considering a public feed.
6. Playbook metadata stays out of AI chat evidence for now. Before chat can recommend a playbook, require cited playbook IDs, validated match and status claims, spoiler boundaries, and a separate security review. The model may explain reviewed advice but must not invent eligibility or upgrade an “investigate” result into certainty.
7. Add player-named threat advice only from the player's stated observations or visible intel. Enemy loadouts remain outside spoiler-off automated matching. Consider opt-in local feedback and export after at least three playbooks are reviewed; do not transmit feedback automatically.

## Verification

Run from the repository root with `PYTHONPATH=.` and a writable `TEMP`/`TMP`:

`python -m unittest tests.test_playbooks tests.test_v16_goals`

The Windows package specs include `stellaris_guide/playbooks.json` so the same reviewed data is available in packaged builds. A packaged smoke test is required before a release; this source change does not replace the currently running release.

### 1.6.3 evidence — October 21, 2026

- Full Python suite: 116 tests passed, one skipped. JavaScript syntax check and browser pin test passed. Playbook tests cover fitting, non-fitting, missing-fact, version/checksum mismatch, mods, conflicting/retired status, invalid facts and chat exclusion.
- Independent code review found goal provenance replacement, retired/status precedence and hidden playbook source/trade-off details. These were corrected. Separate security review found the Windows batch build omitted the data file and chat could misstate an untested playbook; the build now bundles the file and playbook metadata remains outside AI chat evidence. Security recheck found no remaining blocker.
- Built `dist/StellarisGuide-Windows-1.6.3.zip` (SHA-256 `EBCB465D6B6143E526F8763A6A670C81CD75FFCF2CF3EA1030E06CC94985D827`). Archive has 13 allowlisted entries and no save, screenshot, log, clipboard or config entry. The earlier 1.6.2 ZIP remains present.
- Extracted ZIP ran in an isolated Windows profile with a synthetic 4.5.2 save. `/api/state` reported version 1.6.3, ready status, a matched resource-deficit playbook with separate conditional/untested statuses. The packaged `/app.js` served the final playbook wording. The isolated process exited after the Guide's Quit endpoint.
- A final browser visual inspection was attempted, but automatic approval review blocked opening the isolated `127.0.0.1` dashboard in the in-app browser. The stated reason was that authorization for a browser action after the user's prior interruption was unclear. No alternate browser path was attempted. Visual acceptance remains open; the package and API smoke evidence above are complete.
