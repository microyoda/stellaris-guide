# Tools, repositories and data resources

All READMEs below were read in full from GitHub; the `github.io` sites were opened in the second pass.

## R1 – Stellaris Overmind (Dfintz)

- LLM advisor + AI override mod for **Stellaris 4.4.6 "Pegasus"** (checksum fdde). Player mode watches autosaves and prints a suggestion; AI mode steers native AI with personality overrides. [R1 README]
- Its meta is **version-locked JSON** in `docs/meta/`. Only `4.4.6.json` exists; `4.5.0.json` and `4.5.2.json` return 404, so **Overmind has no 4.5 rules yet**. [R1, checked 20 Oct 2026]
- Its 4.4.6 baseline is deliberately thin: official patch mechanics only, `weapon_verdicts` and `fleet_templates` are empty, and community weapon tiers are "not asserted as 4.4.6 truth" without a recorded game test. [R1 `META_4.4.6.md`]
- **Worth adopting:** (a) the version-locked meta file pattern with a scaffold script; (b) an explicit evidence policy per version; (c) fog-of-war filtering before anything reaches the LLM; (d) Nomad-specific rules.
- **Do not copy:** its 4.4.6 rules into 4.5 advice, its personality/weapon meta, or AI-control features (the Guide is read-only). [R1, L1 STRATEGY-RESEARCH]

## R2 – Stellaris LLM Companion (gitmaan)

- Electron app with a Rust save parser; precomputes a **complete briefing JSON** and sends it to the chosen LLM, so chat needs no tool loop. SQLite snapshots track change between saves. Advisor tone adapts to ethics, government and civics. Optional MCP relay. [R2]
- Its README admits the current "Strategic Perspective" can surface galaxy-wide information the player shouldn't know; a fog-of-war mode is only planned. [R2]
- **Lesson for the Guide:** a precomputed briefing is fast and cheap, but it must be **intel-filtered** first. Copy the briefing idea, not the spoiler risk.

## R3 – Stellaris Dashboard (eliasdoehne)

- Graph dashboard, galaxy history map and event ledger from autosaves; Rust parser via maturin (jomini-based); Ironman-compatible in-game browser mod at `localhost:28053`. [R3]
- By default it hides countries you haven't met; "Show information for all countries" is called "essentially a cheat". Pseudo-countries track only territory, wars and diplomacy. [R3]
- **Lesson:** the default visibility rules are a good model for the Guide's intel policy.

## R4 – AgentMystia Stellaris Tech Tree

- Static site of **662 techs** (physics 162 / society 311 / engineering 189), **582 edges**, **13 any-of (OR) prerequisite groups**, ELK layout. Built from `common/technology`, tiers/categories, `scripted_variables` (cost macros resolved, e.g. `@tier5cost3 → 24000`), localisation and DDS icons. The README says it was built entirely by an AI model as a coding test. [R4]
- **Game version is not stated.** Use as a design reference only; build the Guide's catalog from the player's installed files. (The builder's own TECH-TREE-RESEARCH.md reaches the same conclusion.) [R4, L1]

## R5 – YThibos Stellaris Tech Tree

- Draws **every** prerequisite, plus hidden requirements tucked into a tech's availability conditions (example: Synaptic Cogitator also needs Scalable Reservoir Computing). Techs sit in columns by **real tier T0–T5** with each tier's "techs of the previous tier needed". Lists availability conditions and draw-weight modifiers in plain English. Supports campaign import from a `.sav` (in-browser), DLC filtering and mods. In public testing. [R5]
- **Lesson for the Guide (high value):** a tech "path" must include `potential`/availability conditions and **tier gates**, not only `prerequisites`. Otherwise the Guide will recommend techs the game can't offer yet. This is the single most useful precision fix from these tools.

## R6 – Stellaris Assets (tuttu.github.io, by Michaël De Bona)

- A Hugo static site giving quick access to Stellaris graphics and audio by category: Crisis, DLC, Events (pictures, sounds), Governments (authorities, civics), Messages, Modifiers, Modules, Mutations, Origins, Planets (buildings, decisions, deposits, districts, jobs, modifiers), Relics, Rooms, Runes, Ship Parts, Situations, Specimens and Traits. [R6, read 20 Oct 2026]
- **Coverage stops at Shadows of the Shroud (4.3);** the footer is © 2016–2025. **Nomads (4.4) and 4.5 icons are missing**, e.g. Arkship, Waystation, Fleet Doctrine and preference policy icons.
- Content is Paradox's copyrighted game art. Use it only to **look up asset names and paths**, then load the image from the player's own install (as ARTWORK-RESEARCH.md already plans).

## Guidelines

1. **Install-derived data beats any website snapshot.** Read `common/`, `localisation/` and `gfx/` from the player's install for the exact version and DLC set. [R4, R5, L1]
2. **Model tech availability = prerequisites + potential conditions + tier gate + DLC + weight > 0.** [R5]
3. **Keep a version-locked rule file per patch** (4.5.0, 4.5.2) with an evidence label on every rule, like Overmind's meta JSON. This knowledge base's labels map directly onto that. [R1]
4. **Filter by intel before advice.** All three advisors (R1, R2, R3) treat hidden information as a risk. [R1, R2, R3]
