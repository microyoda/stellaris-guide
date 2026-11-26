# Stellaris Guide 1.6.2

This update corrects Tech Tree route interpretation for Stellaris 4.5.2 Cygnus. The detail panel names a technology's **direct prerequisites**. The route map shows the earlier chain only when those technologies still need to be researched in the selected save. For example, Xeno Diplomacy directly requires Federation Code; an already researched Federation Code stops the displayed upstream route there.

When the selected technology is already researched, illustrated cards show technologies linked one or two dependency steps forward. These are possible research paths, not promises that a card is currently drawable. The cards identify alternative links, missing prerequisites, tier gates, and DLC that the selected save does not confirm.

## Install

Extract `StellarisGuide-Windows-1.6.2.zip` and double-click `StellarisGuide.exe`. See [the installation guide](INSTALL.md). The app reads saves and installed game artwork without changing the game. The previous v1.6.1 ZIP is kept separately.

## Verification

The installed 4.5.2 base-game data contains 677 technologies. The route audit checked all 677 direct prerequisite sets and all 677 routes after marking their direct parents researched; it found no mismatch or unexpected upstream node. The 121 routes marked limited in the empty-DLC audit require DLC not confirmed by that synthetic save. Focused success and failure tests, full suite results, visual checks, independent review, and package smoke evidence are recorded in [the implementation evidence log](release1.6.2-implementation-evidence.md).
