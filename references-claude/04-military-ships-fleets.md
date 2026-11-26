# Military: policies, ship design, fleets (4.5)

## New military policies — *OFFICIAL-FINAL* [DD433, R450, R452]

- **Fleet Doctrine** (six doctrines) sets the tactical role of each hull in automated designs and designer auto-complete. Switching rebuilds auto designs immediately. [DD433, G13]
- **Weapon Preferences (Fleets):** Energy, Kinetic, Explosive or Strike Craft. **Defense Preferences (Fleets):** Shield Priority, Balanced or Armor Priority. Both steer auto designs **and which weapon/defense techs you are offered**. [DD433, G13]
- **Starbase** weapon/defense preferences (Explosive needs swarmer missile tech). **4.5.2:** defense platforms got their own pair; the starbase Strike Craft preference was removed; Nomads instead get **Weapon Preferences (Arkships)** (sets Arkship point defense and Military Arkship armaments) and **Defense Preferences (Waystations)**. [R452]
- **4.5.2 fixes:** starbase preferences now take priority over higher-scoring weapons; preferences no longer hidden until 2200; starbase policies now work with the auto-designer off, and turning it back on refreshes existing starbases. [R452]
- Starting Doctrine and preferences are **randomized** toward empire defaults (4.5.2). Military policies can be changed from the Fleet Manager, research policies from the Technology view. [R452, DD433]
- **AI fleets now follow their own Doctrine and Weapon Preference** instead of fixed personality ratios, so enemy compositions vary more. [DD433]

### Doctrine → hull roles (from 4.5.2 game files) — *COMMUNITY-4.5* [G13]

| Doctrine | Corvette | Frigate | Destroyer | Cruiser | Battleship | Titan |
| --- | --- | --- | --- | --- | --- | --- |
| Spearhead | Brawler 70 / Gunship 30 | Siege | Brawler 70 / Gunship 30 | Gunship | Gunship | Gunship |
| Battle Line | Gunship 70 / Screen 30 | Siege | Gunship 70 / Screen 30 | Gunship | Gunship | Gunship |
| Barrage | Artillery | Energy Torpedo 70 / Siege 30 | Artillery 70 / Screen 30 | Artillery | Artillery | Artillery |
| Strike Wing | Screen | Energy Torpedo | Screen | Carrier | Carrier | Artillery |
| Ambush | Brawler | Siege | Artillery | Energy Torpedo | Artillery | Artillery |
| Phalanx | Screen 70 / Gunship 30 | Siege | Screen 70 / Brawler 30 | Gunship 70 / Artillery 30 | Gunship 70 / Artillery 30 | Gunship 70 / Artillery 30 |

## Balance and combat changes

| Change | Patch | Label | Source |
| --- | --- | --- | --- |
| Armor energy/alloy upkeep = same-tier shield (was double) | **4.5.2** | OFFICIAL-FINAL | R452 |
| Maulers "slightly slower" (no number published) | **4.5.2** | OFFICIAL-FINAL | R452 |
| Short-range weapons (autocannons, disruptors…) removed from Starbases, Orbital Rings, Deep Space Citadels; auto platform designs avoid them too | 4.5.0 | OFFICIAL-FINAL | DD433 |
| Station weapon modules are weapon-type-specific, tech-gated, auto-upgrade | 4.5.0 | OFFICIAL-FINAL | DD433 |
| Strike craft and missile defensive modifiers apply to station-launched craft and missiles | 4.5.0 | OFFICIAL-FINAL | DD433 |
| **Missile/torpedo armor and shields now apply in combat**, so point defense no longer ignores them | 4.5.0 | OFFICIAL-FINAL | DD433 |
| Auto designs regenerate the day after new tech; no more empty slots after upgrades; low-power designs cut strike craft instead of stripping defenses | 4.5.0 | OFFICIAL-FINAL | DD433, W1 |
| Auto station designs use armor where shields are negated (pulsars, X-ray binaries, turbulent nebulae, cloaking) | 4.5.0 | OFFICIAL-FINAL | DD433 |
| Carrier computer uses the longer of weapon or strike craft range | 4.5.0 | COMMUNITY-4.5 | G13 |
| Destroyed titan's aura no longer lingers | 4.5.0 | OFFICIAL-FINAL | DD431, G4 |
| Fleets no longer locked in battle when a ship drifts out of range | **4.5.2** | OFFICIAL-FINAL | R452 |
| Auto-disengage after 15 idle days **disabled** | **4.5.1** | OFFICIAL-FINAL | R451 |
| Stellar Cannon is a tier 3 tech needing Wormhole Stabilization and UV Lasers | 4.5.0 | OFFICIAL-FINAL | DD433 |

## Community combat guidance

- **Fleet composition** — *COMMUNITY-OLD* (page first written 2021; compositions from 4.3/4.4 testing) [G3]: early corvettes with 1 autocannon + 2 plasma throwers (armor + shields); mid-game kinetic artillery + neutron launcher cruisers; late artillery battleships plus as many titans as allowed; start around 50:50 cruiser:battleship until you scout; point defense only against missiles, torpedoes or strike craft. Note the guide says "4.5 did not change weapon or hull stats", which predates or ignores the 4.5.2 armor upkeep change.
- **Titan** (**needs Apocalypse**; without it, use flak/PD screens or more cruisers against corvette swarms) — *COMMUNITY-4.5 (4.5.1 files)* [G4, 13-dlc]: Perdition Beam (250 range, collateral 500 damage to every ship within 40 of the target since 4.3), 6× Kinetic Artillery, 3× Auxiliary Fire-Control, Sapient/Autonomous Artillery computer (titans only take Artillery computers). Hostile auras in the main stack, support auras elsewhere. Armor vs shields by the enemy's weapons. "One titan per 200 naval capacity" is a pre-4.3 rule.
- **Ship design** — *COMMUNITY-4.5 (4.5.2 files)* [G13]: shields in utility slots as far as reactor power allows, armor fills the rest; hardening per plate/shield from tier 2 (1%) to tier 5 (4%) since 4.3. Design by hand once at war with a known enemy; untick Auto-upgrade on custom designs.
- **Transports** — *COMMUNITY-4.5 (4.5.2 files)* [G9]: come only from recruited armies (Assault Army 100 minerals, 90 days, 1 energy/month); hull 100 / armor 100 / evasion 70, speed 160; can't be designed or refit. Land with clearly more strength than the defenders (about 2× to be safe); landing takes 10 days. Since 4.5 a system is only fully occupied once its **starbase** is taken.

## Guidelines for the Guide

1. **Read Doctrine and preferences from the save** before suggesting designs or weapon research; never infer them from empire type. [R452]
2. **Explain that a preference policy also changes tech offers.** Suggest one only when it serves a stated goal. [DD433]
3. **Show only the policy family that applies** (settled: fleet/starbase/platform; Nomad: fleet/Arkship/Waystation). [R452]
4. **Recompute armor vs shield value from 4.5.2 files.** Armor is now as cheap to maintain as shields. [R452]
5. **Point defense is worth more vs missile users in 4.5** because missiles now have real defenses PD can strip. Recommend PD/flak only when visible enemies use missiles, torpedoes or strike craft. [DD433, G3]
6. **Counter what the player can see.** Use intel on enemy shields/armor before suggesting anti-shield or anti-armor weapons. [G3, G4, R1]
7. **Don't promise auto-retreat from idle battles;** it's disabled since 4.5.1. [R451]
8. **Invasion advice must include taking the starbase.** [W1, G9]
