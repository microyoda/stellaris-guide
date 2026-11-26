# Stellaris Guide 1.6.1

## For players

- **Tech Tree:** Browse your current research and open an illustrated, clickable route to a target technology in a separate Edge window. The route distinguishes researched steps, missing prerequisites and checks that still need the game.
- **Fleet:** See your owned military fleets, saved ship designs, recorded components and military policies. Compare up to three designs and sketch a build plan.
- **Naval limit:** Enter the limit shown in Stellaris. The Guide saves it on this PC for the selected campaign and warns when your plan exceeds it. Clear or change it whenever the in-game value changes.

Extract `StellarisGuide-Windows-1.6.1.zip` and double-click `StellarisGuide.exe`. See [the installation guide](INSTALL.md). The Guide reads saves and installed game artwork; it does not change your game.

## Evidence and limits

The 2277.10.01 Stellaris 4.5.2 Cygnus save records four owned military fleets with saved powers 740, 688, 265 and 627. Their recorded class sizes total 166 naval use; the 3rd Fleet is at 24 of 48 on its saved plan. The save did not establish a reliable naval capacity maximum. Costs, build time, upkeep, combat performance, eligibility and modded rules still need confirmation in Stellaris. A technology's prerequisites do not guarantee it will be offered as a research choice.

The planner uses saved design class usage where identifiable. Unknown ship designs retain the ship count while their class mix and size are marked incomplete. Unknown empire naval use is shown as unknown. Rival military figures remain behind the existing spoiler control. The manual limit lives in the user's local StellarisGuide settings and is never sent to an AI provider as a claim from the save.

Verification: 103 Python tests passed with one skip; all three JavaScript suites passed. Independent Fleet, Tech Tree and final release reviews and separate security reviews found no remaining actionable release finding. The Windows ZIP and packaged app smoke results are recorded in [the implementation evidence log](release1.6.1-implementation-plan.md).
