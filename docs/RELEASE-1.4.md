# Stellaris Guide 1.4

**Date:** 17 October 2026  
**Game baseline:** Stellaris 4.5.2 Cygnus (checksum 9776)

## What changed

- Each **Your next moves** card now includes save-based **How to achieve this** actions directly below the goal. The card shows a target, deadline, and progress against the first observed autosave. Progress persists in the user's local app-data folder across Guide restarts.
- Resource goals name a colony from the save, explain its current output and problems, and tell the player what district, building, jobs, upkeep, and eligibility to check. The app does not claim an unverified district or system is buildable.
- Fleet steps name a saved combat design and show the empire's selected military policies, including the Cygnus preference families present in that save.
- Hostile-contact advice uses recorded opinion and asks the player to verify borders, treaties, and actual intel. The **Other empires** graph now plots contacted empires' opinions; hidden foreign military power is not sent to an AI provider or presented as player intel.
- The **Tech Tree** tab shows a focused prerequisite path from the installed game's technology definitions when they are found. Visible research choices are marked. Eligibility still depends on game draws, DLC, special triggers, and enabled mods.
- The Guide reads the player's installed game files for the empire flag layers, research icons, and planet-class icons. Images fall back to the existing interface when unavailable. A custom game folder can be set in Settings.
- LM Studio and Ollama receive a shorter save summary and allow up to five minutes for a response. Chat still falls back to the built-in guide when an optional provider fails.
- Planet names continue to use the Cygnus colony-to-celestial-body mapping; unknown planet size is shown as unknown instead of zero. Structured foreign empire names are formatted more clearly.

## Operation and privacy

The app polls the latest autosave every 15 seconds; **↻** checks immediately. It reads saves and installed game files without changing either. The tray icon opens, refreshes, or quits the app. OpenRouter receives the compact save summary only when the player asks a question; its API key remains in memory for the current run.

## Limits to keep visible

- Planet build eligibility, job assignment, policy cooldown, diplomatic acceptance, and war support must be checked in game. The save fields used here do not prove those outcomes.
- Technology paths come from the configured base game installation. Enabled mod overrides are not yet indexed.
- Flag composition is a best-effort rendering of local DDS layers and may differ from the in-game shader.
- Stellaris 4.6 Ideologies from developer diary #436 is a future feature and is **not** encoded as 4.5.2 strategy.

## Verification

Ten automated tests cover the original save parsing and the new goal, policy, flag, technology-path, and AI-context behavior. Source JavaScript passes syntax checking. The installed 4.5.2 save was parsed and produced five goals, 27 selected policies, prerequisite paths, and local artwork. An isolated loopback test checked source UI, state, flag and icon routes, and built-in chat. The packaged executable also served its UI, save state, and flag on a separate port, then exited through its own Quit endpoint. The Windows portable ZIP is at `dist/StellarisGuide-Windows-1.4.zip`.
