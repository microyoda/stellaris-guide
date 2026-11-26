# Tech tree mapping research

Reference reviewed: [AgentMystia's Stellaris Technology Tree](https://agentmystia.github.io/StellarisTechTree/) and its [source repository](https://github.com/AgentMystia/StellarisTechTree). Its README describes a searchable graph organized by physics, society, and engineering; technology tiers and categories; prerequisite links including **any-of** groups; and a detail panel with cost, effects, and DLC source. Its build pipeline reads technology definitions, localization, macros, and icon files from a local Stellaris installation.

## What to use in Stellaris Guide

- Build our own technology catalog from the player's installed game: `common/technology/*.txt`, related tier/category and scripted-variable files, `localisation/english/*.yml`, and `gfx/interface/icons/technologies/*.dds`. This keeps the catalog aligned with the actual installed game rather than a fixed website snapshot.
- Represent each technology with its ID, branch, tier, category, prerequisites (including any-of groups), cost, icon, and human-readable effects where these can be resolved. Keep conditions such as DLC, empire eligibility, and research weight; a prerequisite path alone does not promise that a technology will be offered.
- Join the catalog to the autosave's researched IDs, current research, and offered alternatives. Mark graph nodes **researched**, **available now**, or **locked/conditional**; do not infer an offer from prerequisites alone.
- In the default Tech tab, show the three current research choices and one short path toward a player goal, such as a fleet upgrade. Let the player open a focused prerequisite chain, search for a technology, or expand the full graph. Put cost, unlocks, and “why this helps your current plan” in the selected node's detail panel.
- Refresh the catalog when the installed game version or active mods change. Resolve mod overrides in load order where possible; show a clear fallback when definitions or icons cannot be found.

## Version and reuse checks

The reference project's README reports 662 technologies in its generated dataset, but does not establish that the hosted data matches this player's **Stellaris 4.5 Cygnus** installation. Do not import its generated catalog as the source of truth. Compare parsed IDs and selected prerequisites against the installed 4.5 game files and the player's save before release. The graph design and data workflow are useful references; review code and asset permissions before reusing any of the project's files.

The current Guide reads researched, active, and offered technology IDs from the save. It does not yet parse game technology definitions or render prerequisite paths.
