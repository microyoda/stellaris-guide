"""Modular, scannable, save-aware topic answers for the Campaign Guide."""
from __future__ import annotations

from .dlcs import has_dlc, parse_release_tuple
from .traditions_data import summarize_save_traditions


def format_card(title: str, bullets: list[tuple[str, str]], note: str = "") -> str:
    """Format a scannable plain-text answer rendered as structured DOM in the chat UI."""
    lines = [title]
    for label, detail in bullets:
        if not detail:
            continue
        lines.append(f"- {label}: {detail}" if label else f"- {detail}")
    if note:
        lines.append(f"Check: {note}")
    return "\n".join(lines)


def _dict(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _num(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def _signed(value: float) -> str:
    return f"{value:+.1f}"


def _year(snapshot: dict) -> int | None:
    date_text = str(snapshot.get("date") or _dict(snapshot.get("campaign")).get("save_date") or "")
    parts = date_text.split(".")
    return int(parts[0]) if parts and parts[0].isdigit() else None


def _colony_count(player: dict, planets: list[dict]) -> float | None:
    explicit = _num(player.get("colonies"))
    if explicit is not None:
        return explicit
    return float(len(planets)) if planets else None


def _col_label(count: float) -> str:
    n = int(count)
    return f"{n} colony" if n == 1 else f"{n} colonies"


# --- Economy & Empire Management ---

def empire_size_answer(snapshot: dict) -> str:
    player = _dict(snapshot.get("player"))
    profile = _dict(player.get("profile"))
    planets = [p for p in (snapshot.get("planets") or []) if isinstance(p, dict) and p.get("name")]
    size = _num(player.get("empire_size"))
    colonies = _colony_count(player, planets)

    bullets: list[tuple[str, str]] = []
    if size is not None:
        over = max(0.0, size - 100.0)
        tech_pen = over * 0.2
        edict_pen = over * 1.0
        col_txt = f" across {_col_label(colonies)}" if colonies is not None else ""
        if over > 0:
            bullets.append(("Your save", f"Empire Size is {size:g}{col_txt} ({over:g} over the 100 free cap → roughly +{tech_pen:.1f}% Tech/Tradition cost and +{edict_pen:.0f}% Edict cost)."))
        else:
            bullets.append(("Your save", f"Empire Size is {size:g}{col_txt} — still within the 100 free threshold (no size penalty yet)."))
    bullets.extend([
        ("How it works", "Above 100 Empire Size, each point adds +0.2% Technology & Tradition cost and +1% Edict upkeep (sources: Pops, Colonies +10 each, Districts, Systems)."),
        ("Best ways to reduce it", "Take Expansion (-15% systems & colonies), Imperial Prerogative (-25% colonies, non-MegaCorp), Harmony/Synchronicity & Domination (-5% pops each), Statecraft (-5% total), and use Planetary Ascension on your largest worlds (up to -90% in 4.6)."),
        ("Rule of thumb", "Never stop growing just to stay under 100 — out-scale the penalty with dedicated Tech-Worlds and Unity worlds."),
    ])
    if profile.get("is_hive"):
        bullets.append(("Hive Mind bonus", "Your Hive Mind authority already cuts Empire Size Effect by -25%."))
    return format_card(
        "Empire Size (formerly Empire Sprawl)",
        bullets,
        "Hover the Empire Size icon on the top bar in game to see your exact Pop/Colony/System breakdown.",
    )


def edicts_answer(snapshot: dict) -> str:
    player = _dict(snapshot.get("player"))
    size = _num(player.get("empire_size"))
    net = _dict(player.get("net"))
    net_known = _dict(player.get("net_known"))
    unity = _num(net.get("unity")) if net_known.get("unity", True) is not False else None

    bullets: list[tuple[str, str]] = []
    if size is not None or unity is not None:
        bits = []
        if size is not None:
            bits.append(f"Empire Size {size:g} (+{max(0.0, size - 100.0):.0f}% edict cost)")
        if unity is not None:
            bits.append(f"Unity {_signed(unity)}/mo")
        bullets.append(("Your save", ", ".join(bits) + "."))
    bullets.extend([
        ("Edict Fund", "Edicts draw from your free Edict Fund first; only upkeep above your Edict Fund drains monthly Unity."),
        ("Top early picks", "Capacity Subsidies (+50% Technician output), Mining Subsidies (+50% Miner output), Fortify the Border (+2 Starbase Cap), and Research Subsidies once Energy is stable."),
        ("Raising Edict Fund", "Take Executive Vigor (+100 Edict Fund), Statecraft (+50), Harmony/Synchronicity (+50), or Domination (+50)."),
    ])
    return format_card(
        "Edicts & Edict Fund",
        bullets,
        "Check total Edict Upkeep vs Edict Fund in the Policies & Edicts screen before toggling new edicts.",
    )


def strategic_resources_answer(snapshot: dict) -> str:
    return format_card(
        "Strategic Resources (Motes, Gases & Crystals)",
        [
            ("Natural deposits", "Research Volatile Material Plants, Exotic Gas Extraction, and Rare Crystal Mining to harvest space deposits and planetary features directly."),
            ("Refineries (most reliable)", "Research Volatile Mote Stabilization / Exotic Gas Refining / Rare Crystal Manufacturing and build Chemists, Gas Refiners, or Translucers (converting Minerals into +2 strategic resources per job)."),
            ("Other sources", "Buy small bridges on the Galactic Market, build Ancient Refineries (Ancient Relics), or trade with friendly empires."),
            ("Watch upkeep", "Tier-2+ Research Labs (Gases), Alloy/CG upgrades (Motes), and Holo-Theatres/high-tier ship weapons (Crystals/Motes) quickly drain stockpiles—build refineries before mass-upgrading."),
        ],
        "Confirm which strategic resource techs are unlocked in Tech Tree before upgrading Tier-2 buildings.",
    )


def shortage_answer(snapshot: dict) -> str:
    player = _dict(snapshot.get("player"))
    net = _dict(player.get("net"))
    net_known = _dict(player.get("net_known"))
    deficits = [r.replace("_", " ") for r in ("energy", "minerals", "food", "consumer_goods", "alloys", "trade")
                if net_known.get(r, True) is not False and (_num(net.get(r)) or 0) < 0]
    bullets: list[tuple[str, str]] = []
    if deficits:
        bullets.append(("Your save", f"Currently negative in: {', '.join(deficits)} — resolve these before stock hits 0."))
    bullets.extend([
        ("Shortage Situations", "Hitting 0 stock with negative monthly income starts a Shortage Situation whose penalties worsen as it progresses."),
        ("Harsh penalties", "Trade shortage cuts Job Efficiency by -25%; Consumer Goods shortage halves Research & Unity from jobs; Energy shortage cripples fleet weapons/shields; Alloys/Minerals stall building & ship output."),
        ("Bankruptcy (Default)", "If a Shortage Situation finishes at 100%, your empire suffers Default: severe empire-wide penalties, deleted fleets/buildings, and reduced stockpiles."),
        ("Fast recovery", "Pause draining buildings/edicts, buy a short-term Market bridge (30% base fee), and move pops into the missing resource job immediately."),
    ])
    return format_card(
        "Resource Shortages & Default",
        bullets,
        "Open the Situation Log immediately if a shortage begins so you can halt progress before Default.",
    )


# --- Exploration, Anomalies, Dig Sites, Rifts & Relics ---

def exploration_answer(focus: str | None, snapshot: dict) -> str:
    if focus == "anomalies":
        return format_card(
            "Anomalies & Early Surveying",
            [
                ("Early priority", "Survey chokepoints and habitable systems FIRST — leave slow Level 4+ anomalies for later so your Science Ships do not stall expansion."),
                ("Quick wins", "Do fast Level 1–2 anomalies along the way (they often grant extra deposits, free tech progress, or Scientist XP)."),
                ("Scientist match", "Assign higher-level Scientists or Scholars to high-difficulty anomalies to cut research time dramatically."),
            ],
            "Open the Situation Log → Anomalies tab anytime to clean up skipped anomalies once borders are locked in.",
        )
    if focus == "dig_sites":
        ancrel = has_dlc(snapshot, "ancient_relics")
        dlc_line = ("DLC note", "Ancient Relics DLC is not listed in this save (some story dig sites and Relics require it).") if ancrel is False else ("", "")
        bullets = [
            ("Requirement", "Archaeological Sites must be inside your owned borders (build an Outpost first) and excavated by a Science Ship with a Scientist."),
            ("How rolls work", "Each chapter rolls 1–10 + Scientist skill + Clues - Site Difficulty; higher-level Scientists and Scholar traits finish sites much faster."),
            ("Rewards", "Yield Minor Artifacts, permanent empire modifiers, unique technologies, and Relics."),
        ]
        if dlc_line[0]:
            bullets.insert(0, dlc_line)
        return format_card(
            "Archaeological Sites (Dig Sites)",
            bullets,
            "Check site difficulty and your Scientist's level before locking a ship down for several years.",
        )
    if focus == "astral_rifts":
        astral = has_dlc(snapshot, "astral_planes")
        bullets = [
            ("Unlocking", "Requires Astral Planes DLC and Rift Sphere technology (plus Astral Siphons to harvest Astral Threads)."),
            ("Exploration", "Send a Science Ship with a high-level Scientist into an owned Rift system to progress branching narrative chapters."),
            ("Astral Actions", "Spend collected Astral Threads in the Relics & Astral Actions menu for empire buffs, fleets, or Dimensional Lock."),
        ]
        if astral is False:
            bullets.insert(0, ("DLC note", "Astral Planes DLC is not listed in this save's active DLCs."))
        return format_card("Astral Rifts & Astral Threads", bullets, "Confirm Astral Planes DLC and Rift Sphere tech in game.")
    if focus == "relics":
        return format_card(
            "Relics & Minor Artifacts",
            [
                ("Passive vs Triumph", "Every Relic grants a permanent Passive effect plus an active Triumph effect (costs Unity and triggers a 10-year shared Relic Triumph cooldown)."),
                ("Minor Artifacts", "Earned from Dig Sites, Relic Worlds, and Archaeo-Engineers; spend them on Artifact Actions (sell to collectors, boost research/unity, proclaim supremacy) or Archaeotech ship components."),
                ("Archaeotech tip", "Only build fleets around Archaeotech weapons/shields if you take the Archaeo-Engineers Ascension Perk and have steady Minor Artifact income."),
            ],
            "Open Discoveries → Relics in game to check your active Relics and Triumph cooldown.",
        )
    # Default: exploration routing
    year = _year(snapshot)
    yr_note = f"At Year {year}, " if year else ""
    return format_card(
        "Efficient Early-Game Exploration Route",
        [
            ("Step 1 — Fan out", f"{yr_note}run 3 Science Ships early (matching base Scientist cap) down separate hyperlane branches to find chokepoints and your 2 guaranteed habitable worlds."),
            ("Step 2 — Skip slow stops", "Skip Level 4+ anomalies and dig sites until you map nearby borders and block rival AI empires at 1-lane chokepoints."),
            ("Step 3 — Leapfrog constructors", "Use 1 Construction Ship strictly to claim toward chokepoints/planets while a 2nd builds mining/research stations behind it."),
            ("Step 4 — Auto-survey later", "Switch to Automatic Surveying once key chokepoints and colonies are secured."),
        ],
        "Confirm your Scientist Leader Cap in Leaders before hiring extra Science Ships.",
    )


# --- Colonies, Planet Classes, Specialization, Crime, Unemployment, Terraforming, Habitats ---

def planet_classes_answer(snapshot: dict, question_text: str) -> str:
    lowered = question_text.casefold()
    earth_first = "earth" in lowered
    bullets = []
    if earth_first:
        bullets.append(("Earth in Stellaris", "Earth is a **Continental** world (pc_continental), NOT a Gaia world (default 80% habitability for Continental-preference humans)."))
    bullets.extend([
        ("Continental (standard Wet)", "80% habitability for Continental species, 60% for Ocean/Tropical (same Wet group), and 20% for Dry/Cold species; no built-in output bonus."),
        ("Gaia World (rare ideal)", "100% habitability for ALL biological species, +10% job output, and +10% biological pop happiness."),
        ("Holy World warning", "Never colonize a Gaia world with the 'Holy World' modifier near a Spiritualist Fallen Empire unless you have the Head of Zarqlan relic — they will declare war."),
        ("Other special classes", "Ecumenopolis (Arcology Project), Hive Worlds, Machine Worlds, and Relic Worlds offer top-tier specialized bonuses later in the game."),
    ])
    return format_card(
        "Continental vs Gaia Worlds" + (" (and Earth)" if earth_first else ""),
        bullets,
        "Check a planet's modifiers and Habitability icon before sending a Colony Ship.",
    )


def colony_topic_answer(focus: str, snapshot: dict, planet: dict | None = None) -> str:
    player = _dict(snapshot.get("player"))
    profile = _dict(player.get("profile"))
    planets = [p for p in (snapshot.get("planets") or []) if isinstance(p, dict) and p.get("name")]

    if focus == "specialization":
        return format_card(
            "Colony Specialization & Designations",
            [
                ("One job per colony", "Give each developed colony a single main role: Forge (Alloys), Factory (Consumer Goods), Tech-World (Research), Generator, Mining, Agri, or Unification (Unity)."),
                ("Use Designations", "Manually set the Planet Designation to match the colony's role — Designations cut job upkeep or boost output (e.g. -20% Metallurgist/Artisan upkeep or +25% basic worker output)."),
                ("Early-game exception", "Keep your Capital mixed early and avoid over-specializing until monthly Trade is positive, because local colony deficits consume empire Trade upkeep."),
                ("Districts on a new colony", "Start by covering Amenities (Holo-Theatre / Maintenance Drones) and Housing, then add only the district type that matches your chosen designation as pops grow."),
            ],
            "Open Planets to compare each colony's current designation, free amenities, and stability.",
        )
    if focus == "unemployment":
        return format_card(
            "Fixing Colony Unemployment",
            [
                ("Build matching jobs", "Build a district or building matching the colony's specialization (remember Specialists take time to demote to Worker jobs if a higher-tier building was disabled)."),
                ("Let auto-resettlement work", "Unemployed free pops automatically migrate to colonies with open jobs and housing (speed it up with Starbase Transit Hubs or Greater Than Ourselves)."),
                ("Check disabled jobs", "Open the colony's Population/Jobs tab to verify jobs were not accidentally deprioritized or disabled."),
                ("Living Standards", "Utopian Abundance or Social Welfare lets unemployed pops produce Unity/Research instead of tanking Happiness."),
            ],
            "Inspect the colony's Jobs tab in game before queuing extra districts.",
        )
    if focus == "crime":
        bullets: list[tuple[str, str]] = []
        if planet:
            crime = _num(planet.get("crime"))
            stab = _num(planet.get("stability"))
            bullets.append((
                f"Saved {planet['name']}",
                f"Crime {f'{crime:.0f}%' if crime is not None else 'unknown'}, Stability {f'{stab:.0f}%' if stab is not None else 'unknown'}.",
            ))
        bullets.extend([
            ("Fill Enforcers first", "Keep Crime below 30% (below 10% vs Criminal Syndicates) by prioritizing Enforcer / Hunter-Seeker jobs or building a Precinct House / Sentinel Posts."),
            ("Boost Happiness", "Higher pop Happiness directly lowers Crime — fix negative Amenities and Housing alongside Enforcers."),
            ("Planetary Decisions", "Run Anti-Crime Campaign for a quick Crime drop (costs Energy); avoid Crime Lord Deal unless intentionally trading +10 Stability for Criminal jobs."),
        ])
        return format_card("Reducing Colony Crime", bullets, "Check the Crime tooltip on the colony to see if a Criminal Branch Office is present.")
    if focus == "terraforming":
        return format_card(
            "Terraforming Planets",
            [
                ("Tech progression", "Terrestrial Sculpting (uninhabited planets) → Ecological Adaptation (already-colonized worlds) → Climate Restoration (Tomb Worlds & Barren Terraforming Candidates)."),
                ("Special worlds", "World Shaper unlocks Gaia Worlds (-25% cost), Hive Worlds / Machine Worlds unlock Gestalt ideal worlds, Detox unlocks Toxic Candidates, Hydrocentric boosts Ocean worlds."),
                ("Tip", "Terraforming costs Energy credits and takes ~5–10 years; clear blockers and check planetary modifiers first so you don't lose useful features."),
            ],
            "Check the Terraform button on any owned planet's surface view in game.",
        )
    if focus == "habitats":
        if profile.get("is_nomad"):
            return format_card(
                "Habitats (Nomadic Empire Note)",
                [
                    ("Blocked for Nomads", "Nomadic empires cannot build standard Orbital Habitats — expand your Arkship modules and districts instead."),
                ],
                "Verify Nomad origin/authority rules in game.",
            )
        return format_card(
            "Orbital Habitats",
            [
                ("How they work", "Build a Habitat Central Complex in a system, then add Major & Minor Orbitals over planets/deposits to unlock more districts, building slots, and resource extraction."),
                ("Best uses", "Fortress Habitats at chokepoints (FTL Inhibitors + Naval Cap), Research/Trade/Alloy stations in tall empires, or harvesting rare deposits."),
                ("Voidborne perk", "Adds +2 max Habitat districts, -20% Habitat/district cost, +25% minor-orbital districts, and +50% Habitat district jobs."),
                ("Watch upkeep", "Habitats cost Alloys to build and maintain — don't spam them before your Alloy income is solid."),
            ],
            "Confirm Habitat technology and system orbital deposits before building.",
        )
    if focus == "multi_colony_system":
        return format_card(
            "Managing Multiple Colonies in One Star System",
            [
                ("Specialize each world", "Treat every planet/habitat in the same system independently with its own Designation (e.g. one Forge World, one Tech-World, one Mining/Fortress world)."),
                ("Share 1 Starbase", "One upgraded Starbase covers the whole system — add a Transit Hub (auto-resettlement across all colonies), Deep Space Black Site (+5 Stability to every colony in the system!), and Hydroponics."),
                ("Single Governor", "Assigning a Sector/Planet Governor boosts all colonies in the sector cleanly; if using Fortress worlds, one FTL Inhibitor blocks enemy fleets from leaving the system."),
            ],
            "A Deep Space Black Site on the system's starbase buffs Stability on EVERY colony in that system.",
        )
    return ""


# --- Population Subtopics ---

def population_detail_answer(focus: str, snapshot: dict, planet: dict | None = None) -> str:
    if focus == "resettlement":
        return format_card(
            "Pop Resettlement (Manual & Automatic)",
            [
                ("Auto-resettlement (free)", "Unemployed free pops automatically move to colonies with open jobs and housing every month — build Starbase Transit Hubs (+100% chance) to speed this up."),
                ("Manual resettlement", "Requires the Resettlement policy set to Allowed (costs Energy, plus Unity for Rulers); useful to rush a new colony to 10 pops for capital upgrade."),
                ("Caution", "Egalitarian factions dislike manual Resettlement — prefer Transit Hubs and open jobs unless you urgently need to move pops."),
            ],
            "Check Policies → Resettlement and open housing/jobs on destination worlds.",
        )
    if focus == "pop_assembly":
        return format_card(
            "Robots & Pop Assembly",
            [
                ("Mechanical assembly", "Research Powered Exoskeletons → Robotic Workers and build Robot Assembly Plants on colonies (runs in parallel with organic pop growth!)."),
                ("Organic assembly", "Hive Minds (Spawning Pools), Clone Vats (Genetics/BioGenesis), or Budding traits assemble organic pops — note a colony only runs ONE assembly queue (organic or mechanical) at a time."),
                ("Droids & Synthetics", "Early Robots only work basic jobs; Droids unlock Specialists/Colonization, and Synthetics unlock all jobs (grant AI Citizen Rights before ~2290 to avoid Machine Uprising)."),
            ],
            "Inspect the colony's Population tab to confirm your Assembler jobs are filled.",
        )
    if focus == "pop_not_growing":
        bullets: list[tuple[str, str]] = []
        if planet:
            pops = _num(planet.get("pops"))
            hous = _num(planet.get("free_housing"))
            stab = _num(planet.get("stability"))
            bullets.append((
                f"Saved {planet['name']}",
                f"Pops {f'{pops:g}' if pops is not None else 'unknown'}, Free Housing {f'{hous:+g}' if hous is not None else 'unknown'}, Stability {f'{stab:.0f}%' if stab is not None else 'unknown'}.",
            ))
        bullets.extend([
            ("1. Population Controls", "Check Planetary Decisions ('Cease Drone Production' / 'Discourage Planetary Growth') AND Species Rights → Population Controls Enabled."),
            ("2. Habitability & Housing", "Very low habitability (<20%) or severe overcrowding/low planet capacity slashes logistic pop growth near zero."),
            ("3. Assembly jobs disabled", "For Machine/Synthetic empires, confirm Replicator / Roboticist jobs are open and filled (and you aren't out of Alloys/Energy)."),
            ("4. Empire growth scaling", "Late-game empire-wide pop growth scaling slows each new pop — check the Population growth tooltip to see if growth is simply slow vs 0.00."),
            ("5. If truly stuck at 0.00", "Verify whether mods are active and test after unpausing one month tick; offline guide cannot check Paradox's live bug tracker."),
        ])
        return format_card(
            "Troubleshooting: Colonies Not Growing Pops",
            bullets,
            "Hover the Pop Growth / Assembly progress bar on the colony's Population tab for the exact modifier breakdown.",
        )
    return ""


# --- Technology Subtopics ---

def tech_detail_answer(focus: str, snapshot: dict) -> str:
    if focus == "tech_tiers":
        return format_card(
            "How Technology Tiers Work (Tiers 1–5)",
            [
                ("The 6-tech gate", "To unlock Tier N technologies in a branch (Physics, Society, or Engineering), you must first research **6 technologies of Tier N-1** in that same branch."),
                ("Example", "Researching 6 Engineering Tier 1 techs unlocks Tier 2 cards (like Destroyers and Mineral Purification Hubs); 6 Tier 4 techs unlock Tier 5 (Battleships, Mega-Engineering)."),
                ("Track progress here", "Open the **Tech Tree** tab in this guide — each branch shows your Tier 2 counter and click **Route** on any tech to inspect its exact prerequisites."),
            ],
            "Meeting a tier gate makes cards eligible to draw, not guaranteed on the very next roll.",
        )
    if focus == "mega_engineering":
        return format_card(
            "How to Unlock Mega-Engineering (Tier 5 Rare Engineering)",
            [
                ("Required prerequisites", "**Battleships**, **Citadels**, and **Zero Point Power** — plus 6 Engineering Tier 4 technologies researched."),
                ("Boost draw weight", "Own more Starholds/Citadels (up to 6 each), have a Ruined Megastructure inside your borders, assign a Voidcraft/Expertise Scientist on Council, or take Technological Ascendancy (+50% rare draw) / Voidborne / Master Builders."),
                ("Check your exact path", "Open **Tech Tree → Route** and search **Mega-Engineering** to see which prerequisite steps are done in your current save."),
            ],
            "Verify your researched prerequisites in the Tech Tree Route Explorer.",
        )
    if focus == "early_expansion_tech":
        return format_card(
            "Early-Game Expansion Tech Priorities",
            [
                ("Physics", "Research Speed / Lab upgrades (+20% output), Reactor/Shield tiers, Energy Grid, and Hyper Drive II for faster exploration."),
                ("Society", "Planetary Unification (+Unity & Edict Fund), Pop Growth / Habitability / Blocker clearing, Starbase/Naval Cap doctrines, and Colonial Centralization (unlocks upgraded capitals & Galactic Administration in 4.6)."),
                ("Engineering", "Powered Exoskeletons → Robotic Workers (huge early pop boost), Mineral Purification, Alloy Foundries, Starholds (chokepoints + Anchorages), and Destroyers/Cruisers."),
                ("Quick rule", "Cheap Tier 1 economy/research techs also push you cleanly past the 6-tech Tier 2 gate."),
            ],
            "Compare these priorities against your actual drawn cards in the Tech Tree tab.",
        )
    return ""


# --- Ships, Fleet, Chokepoints, War, Ground Combat, Cloaking ---

def ship_detail_answer(focus: str, snapshot: dict) -> str:
    if focus == "ship_designer":
        return format_card(
            "Using Custom Ship Designs (Ship Designer)",
            [
                ("Yes — recommended!", "Open **Ship Designer** (F9 or left sidebar) and **uncheck Auto-Generate Designs** in the bottom-left so the AI stops overwriting your loadouts."),
                ("Create & save", "Pick a hull (Corvette, Frigate, Destroyer, Cruiser, Battleship), choose Sections, Weapons, Armor/Shields, Aux, and Combat Computer, then click **Save**."),
                ("Upgrade fleets", "Select your fleets and click **Upgrade** at a Shipyard starbase to retrofit existing ships to your new custom design."),
                ("Blueprints", "Open **Fleet → Design Finder** in this app for hull-by-hull weapon, armor/shield, and Crisis counter setups."),
            ],
            "Always verify Reactor Power is positive before saving a custom design.",
        )
    if focus == "fleet_stuck":
        return format_card(
            "Why Is My Fleet Stuck in a System?",
            [
                ("1. FTL Inhibitor (most common in war)", "An enemy upgraded Starbase or Fortress colony with an FTL Inhibitor locks all hyperlane exits except the exact lane your fleet entered from — capture the starbase AND invade/bombard the fortress planet."),
                ("2. Closed Borders", "If a neighbor closed borders around your ships, click the **Return** button (B) on the fleet to trigger Emergency FTL / Missing in Action (MIA) back to your home starbase."),
                ("3. Unexplored hyperlane", "Military fleets cannot enter completely unexplored systems — send a Science Ship first (or assign a Commander to a fleet to explore)."),
                ("4. Hostile system block", "Check if the only route passes through a system marked Restricted (bottom of system view) or blocked by a Leviathan/Fallen Empire."),
            ],
            "Hover the red move-order arrow in the Galaxy Map to see the exact block reason.",
        )
    if focus == "chokepoint_starbase":
        return format_card(
            "Building Chokepoint Starbases (Bastions)",
            [
                ("Early game (2200–2250)", "Fill modules with **Hangar Bays** (Strike Craft shred early Corvettes and suppress piracy) + **Target Uplink Computer** (+50% range) + Defense Platforms."),
                ("Mid/Late game", "Add **Communications Jammer** (-20% enemy speed/disengage), **Command Center** (+10% friendly fire rate), **Disruption Field Generator** (-20% enemy shields), and pair with a **Fortress Habitat/Colony** for a planet-side FTL Inhibitor."),
                ("Key rule", "Starbases alone lose to late-game Battleships — treat bastions as force multipliers that stall enemies while your mobile fleet arrives."),
            ],
            "Keep upgraded starbases within Starbase Capacity to avoid steep Energy upkeep penalties.",
        )
    if focus == "hull_corvette":
        return format_card(
            "Best Corvette Build (Early → Late Game)",
            [
                ("Early (2200–2240)", "Interceptor (3x S): 3x Missiles or 2x Kinetic + 1x Laser (or 3x Disruptors once unlocked), balanced ~50/50 Armor & Shields, Afterburner, Swarm computer."),
                ("Anti-missile picket", "Picket Ship (1x P + 2x S): Flak vs Strike Craft or Point-Defense vs Missiles, paired with Laser/Disruptor S-slots."),
                ("Late-game role", "Pure Disruptor Swarm or fast screeners with maximum Evasion (90% cap via Thrusters + Afterburners)."),
            ],
            "Open Fleet → Design Finder for full slot counts and enemy counter presets.",
        )
    if focus == "hull_battleship":
        return format_card(
            "Best Battleship Loadout (Mid → Late Game)",
            [
                ("All-rounder Carrier/Artillery (meta)", "Spinal Mount Bow (**Focused Arc Emitter**), Carrier Core (2x Hangar + 2x Point-Defense + 2x S Missiles), Broadside Stern (2x Whirlwind Missiles), 3x Afterburners, Carrier computer."),
                ("Pure Artillery (vs big ships/Unbidden)", "Spinal Mount Bow (Giga Cannon or Tachyon Lance) + Artillery Core/Stern (Kinetic Artillery or Neutron Launchers), Auxiliary Fire-Control, Artillery computer."),
                ("Defenses", "Balanced 50/50 Shields & Armor vs unknown foes; counter specific crises via Fleet → Design Finder Crisis presets."),
            ],
            "Verify unlocked X-slot weapons and reactor power in Ship Designer.",
        )
    if focus == "hull_cruiser":
        return format_card(
            "Best Cruiser Loadout (Midgame Power Spike)",
            [
                ("Kiting Missile/Carrier Cruiser", "Broadside Bow (2x S/M Missiles) + Hangar Core (1x Hangar + 2x PD) + Gunship Stern (2x M Whirlwind Missiles), 2–3x Afterburners, Artillery/Carrier computer."),
                ("Brawler Torpedo Cruiser", "Torpedo Bow (Neutron/Devastator Torpedoes) + Disruptors + Armor-heavy + Afterburners + Torpedo computer to shred Starbases and Battleships."),
            ],
            "Open Fleet → Design Finder to match components unlocked in your save.",
        )
    if focus == "cloaking":
        return format_card(
            "Cloaking & Detection Mechanics",
            [
                ("How it works", "Requires First Contact DLC + Cloaking Field Generators. A fleet stays hidden if its **Cloaking Strength** exceeds enemy **Detection Strength**."),
                ("Shield trade-off", "Cloaking disables standard Shields while cloaked (only **Psionic Shields** stay active while cloaked, and Armor/Hull are unaffected)."),
                ("Boosting Cloaking / Detection", "Boost Cloaking via Subterfuge tradition, Enigmatic Engineering (+2), Dark Matter Cloaking, and Nebula cover; counter enemy stealth with **Detection Array** starbase modules + Listening Posts."),
            ],
            "Check each ship's Cloaking Strength in Ship Designer (a fleet moves at its lowest ship's cloaking level).",
        )
    return ""


def war_detail_answer(focus: str, snapshot: dict) -> str:
    if focus == "ground_combat":
        return format_card(
            "Armies, Planetary Invasion & Orbital Bombardment",
            [
                ("Invasion planning", "Recruit Assault Armies on high-pop worlds (or Gene Warriors / Psi Armies / Mega-Warforms later) and escort Transport Fleets behind combat fleets so they don't get intercepted."),
                ("Bombardment stances", "**Selective** (low collateral), **Indiscriminate** (faster garrison damage, higher collateral), **Armageddon** (genocidal — turns world to Tomb World), **Raiding** (Nihilistic Acquisition — abducts pops)."),
                ("Orbital Surrender", "Non-gestalt undefended/weakened worlds can surrender to bombardment automatically if Orbital Surrender is allowed; Fortress worlds with FTL Inhibitors usually require landing Armies."),
                ("Winning cleanly", "Bring ~1.5x–2x enemy Defense Army strength (with a Commander assigned) to avoid dragging out war exhaustion."),
            ],
            "Check a target planet's Armies tab before landing transports.",
        )
    if focus == "claims_wargoals":
        return format_card(
            "Making Claims & Declaring War",
            [
                ("Claims cost Influence", "Open Diplomacy → Make Claims BEFORE declaring war (claims made during an offensive war cost +100% extra Influence!)."),
                ("Choosing a War Goal", "**Conquer (Claim)** takes claimed systems, **Vassalize** requires Superior relative power and no full system claims blocking it, **Humiliate** farms Influence, and **Total War** (Colossus / Genocidal) transfers systems immediately on occupation."),
                ("Preparation", "Stage fleets on the border, check the enemy's Defensive Pacts/Federations, and bring Assault Armies for colonized systems."),
            ],
            "Check the Declare War screen to see all enemy allies before confirming.",
        )
    if focus == "war_exhaustion":
        return format_card(
            "War Exhaustion, Status Quo & Winning Wars",
            [
                ("100% War Exhaustion", "Reaching 100% does NOT instantly end the war — it lets the opponent **force a Status Quo peace 24 months later**."),
                ("Status Quo vs Achieve War Goals", "**Status Quo** lets BOTH sides keep every **claimed AND fully occupied** system (including invading all colonies in that system!). **Achieve War Goals** requires high Occupation + Navy advantage."),
                ("Why won't they surrender?", "Hover the red X next to 'Achieve War Goals' — usually you missed invading 1 colony or Habitat in a claimed system, or an ally still holds unoccupied territory."),
            ],
            "Open the War Overview icon (bottom-right) to see exact Occupation % and missing planets.",
        )
    if focus == "avoid_war":
        return format_card(
            "Avoiding War While Expanding",
            [
                ("1. Deterrence first", "AI empires evaluate your **Fleet Power** — keep a standing navy near your Naval Cap even in peaceful games so neighbors don't see you as weak."),
                ("2. Envoys & Pacts", "Assign Envoys to **Improve Relations**, trade favorable gifts (instant +100 trade opinion), and sign Non-Aggression or Defensive Pacts with friendly neighbors."),
                ("3. Watch borders", "Avoid claiming directly next to **Militant Isolationist Fallen Empires**, avoid bordering Genocidal empires without fortified chokepoints, and stay out of rivalries you don't want to fight."),
            ],
            "Open Empires to monitor negative opinions and aggressive AI personalities.",
        )
    if focus == "war_tactics":
        return format_card(
            "Fighting Wars with Minimal Losses",
            [
                ("Scout & counter", "Inspect enemy ship loadouts (need intel or a quick skirmish) and refit Armor vs Kinetic, Shields vs Energy, or Flak/PD vs Missiles/Strike Craft."),
                ("Defend on chokepoints", "Let stronger enemies crash into your upgraded Bastion starbase + main fleet together (home-territory bonuses + starbase aura)."),
                ("Concentrate fleets", "Keep fleets grouped rather than feeding small stacks piecemeal; use Hit & Run war doctrine (Supremacy) to save ships via emergency disengage."),
            ],
            "Check visible fleet strength, allies, and treaties in game before committing to an offensive.",
        )
    return ""


# --- Fallen Empires, Leviathans, Diplomacy, Federations, GC, Criminal, Slavery, AI Personalities ---

def fallen_empire_answer(snapshot: dict, question_text: str) -> str:
    lowered = question_text.casefold()
    bullets: list[tuple[str, str]] = []
    if any(w in lowered for w in ("isolationist", "isolist", "border", "next to", "starbase", "trade", "avoid", "conflict")):
        bullets.append(("Militant Isolationists (Xenophobe FE)", "**NEVER build a starbase/outpost in any system directly connected by hyperlane** to a Militant Isolationist FE — they will demand you dismantle it and declare war if you refuse. Leave a 1-system empty buffer!"))
    bullets.extend([
        ("All 5 FE red lines", "**Xenophobe:** never border them. **Spiritualist:** never colonize Holy Worlds (Gaia worlds with the Holy World icon). **Materialist / Xenophile / Machine:** generally peaceful if you comply with occasional requests."),
        ("Safe trading & avoiding conflict", "Trade agreements, Market trade, and expanding away from FE borders do NOT anger FEs — just respect the Xenophobe 1-lane buffer and Holy Worlds."),
        ("Awakening triggers", "After the Endgame Year, a Fallen Empire can Awaken if a default empire grows very strong (~70k+ fleet power), conquers an FE world, or an Endgame Crisis spawns (Watchful Regulators)."),
        ("Fighting FEs", "Wait until ~150k–300k+ fleet power (depending on difficulty), consider **Galactic Contender**, and reverse-engineer their Dark Matter debris."),
    ])
    return format_card(
        "Fallen Empires: Borders, Diplomacy & Awakening",
        bullets,
        "Check an FE's Ethic and personality in Contacts before claiming adjacent systems or colonizing nearby Gaia worlds.",
    )


def leviathans_answer(snapshot: dict) -> str:
    return format_card(
        "Defeating Leviathans (Guardians)",
        [
            ("Fleet power target", "Plan for roughly **35k–60k+ fleet power** depending on the Guardian and your counter-fit (higher if fighting the Dimensional Horror or Voidspawn uncountered)."),
            ("Curator Order buff", "Buy the Curator Order's tactical insight for **+25% damage** against a specific Leviathan (and ask them to estimate your odds!)."),
            ("Counter loadouts", "Use **Armor + Energy/Torpedoes** vs Ether Drake / Enigmatic Fortress / Tiyanki Matriarch, and **Shields + Torpedoes/Kinetic** vs Dimensional Horror / Automated Dreadnought."),
        ],
        "Confirm Leviathans DLC and ask the Curators in Contacts before committing your main fleet.",
    )


def diplomacy_gc_answer(focus: str, snapshot: dict) -> str:
    if focus == "federations":
        return format_card(
            "Forming & Running a Federation",
            [
                ("Requirement", "Adopt the **Diplomacy** tradition tree and pick **The Federation** (or have a willing empire with it invite you)."),
                ("Federation types", "**Galactic Union** (standard), **Trade League** (best economy — unlocks Trade League policy giving Energy + CG + Unity!), **Research Cooperative**, **Martial Alliance**, and **Hegemony** (subjugation)."),
                ("Cohesion & XP", "Assign Envoys to the Federation to keep Cohesion positive so it levels up and unlocks Federation Fleets and passive buffs."),
            ],
            "Check an empire's Federation acceptance tooltip in Diplomacy (similar ethics and High Trust help most).",
        )
    if focus == "custodian":
        return format_card(
            "Becoming Galactic Custodian or Galactic Emperor",
            [
                ("Requirements", "Requires **Nemesis** DLC, an active Galactic Community with a Galactic Council, and high **Diplomatic Weight** (boosted by Fleet Power, Economy, Tech, Pops, Envoys, and Politics tradition)."),
                ("Step 1 — Custodian", "Propose & pass **Nominate Custodian** (much higher AI support during an active Midgame/Endgame Crisis or Great Khan), then pass **Remove Custodian Term Limit** and create the GDF fleet."),
                ("Step 2 — Imperium", "As permanent Custodian, pass **Proclaim the Galactic Imperium** to become Galactic Emperor (dissolves existing Federations and unlocks the Imperial Armada)."),
            ],
            "Buy Favors (via Diplomacy/Trade/Politics) to swing close Senate votes.",
        )
    if focus == "galactic_community":
        return format_card(
            "How the Galactic Community Works",
            [
                ("Diplomatic Weight", "Your voting power comes from Fleet Power, Economy, Tech, Pops, and Envoys assigned to the Community (modified by stances & resolutions)."),
                ("Resolutions & Sanctions", "Vote on Galactic Laws for empire-wide buffs — watch out for **In Breach of Galactic Law** if a passed resolution conflicts with your policies, as Sanctions can stack steep penalties."),
                ("Galactic Council", "Top Diplomatic Weight empires join the Council, gaining Veto and Emergency Measure powers."),
            ],
            "Open the Galactic Community tab to review the active Senate floor and your Diplomatic Weight breakdown.",
        )
    if focus == "relations":
        return format_card(
            "Improving Relations with Another Empire",
            [
                ("Envoys", "Assign one or more Envoys to **Improve Relations** (stacks up to +150 Opinion and builds Trust over time)."),
                ("Trade Gifts", "Send a one-sided Trade Deal (Food, Minerals, or Consumer Goods) for up to **+100 Favorable Trade Deal** opinion instantly."),
                ("Pacts & Trust", "Open Borders, Embassy, Research/Commercial/Non-Aggression Pacts, and shared Rivals steadily raise Opinion and Trust cap."),
            ],
            "Hover an empire's Opinion number in Contacts to see every positive and negative modifier.",
        )
    return ""


def criminal_branch_answer(snapshot: dict) -> str:
    return format_card(
        "Criminal Syndicate Branch Offices",
        [
            ("How they work", "Criminal Heritage MegaCorps (MegaCorp DLC) can open **Criminal Branch Offices** on your colonies WITHOUT a Commercial Pact, adding Crime and scaling their profit with Crime %."),
            ("Passive removal", "Build **Precinct Houses / Hall of Judgment** and fill Enforcer jobs to drive colony Crime to **0%** — at 0% Crime, a random check periodically shuts down the Criminal Branch Office (10-year immunity afterward)."),
            ("Active removal", "Declare an **Expropriation** war against the Criminal Syndicate (closes all their branch offices on victory) — or form a Commercial Pact with a friendly normal MegaCorp so branch slots are occupied."),
        ],
        "Inspect the colony's Corporate tab to see if a Criminal Branch Office is boosting Crime.",
    )


def slavery_purge_answer(snapshot: dict) -> str:
    return format_card(
        "Penalties for Slavery & Genocide (Purging)",
        [
            ("Genocide / Purging", "Extermination/Processing causes massive diplomatic opinion penalties (**Genocidal**, up to **-1,000** across most non-genocidal empires) and risks Galactic Community denouncements or coalition wars. **Displacement** purge avoids the worst Genocidal opinion hit."),
            ("Slavery trade-offs", "Slaves suffer sharp Happiness penalties (risking low Stability/Revolts) and Egalitarian/Xenophile empires dislike slavers, though Slavery cuts Slave Political Power and pop upkeep while boosting Worker output."),
            ("Keeping slave worlds stable", "Keep Ruler/Enforcer pops happy on the planet (their high Political Power anchors Stability), use Domination (-25% slave political power), and watch Crime."),
        ],
        "Check Species Rights → Citizenship / Slavery Type / Purge Type in the Species screen.",
    )


def ai_personalities_roleplay_answer(focus: str, snapshot: dict) -> str:
    if focus == "ai_personalities":
        return format_card(
            "Ethos Combinations & AI Personalities",
            [
                ("How it works", "An AI empire's **Ethics + Authority + Civics** determine its **AI Personality**, which sets Aggressiveness, Bravery, Trade Willingness, Conquest/Vassal drive, and Federation preference."),
                ("Classic examples", "Fanatic Xenophile + Militarist + Repugnant/Charismatic → **Fanatical Befrienders** (+100 opinion but 2x Aggressiveness!); Militarist + Authoritarian → **Hegemonic Imperialists**; Xenophile + Egalitarian → **Federation Builders**; Materialist + Militarist → **Ruthless Capitalists** / **Erudite Explorers**."),
                ("For Roleplay", "Force-spawn custom empires with contrasting ethics (e.g., Peaceful Traders, Honorbound Warriors, Evangelizing Zealots, Rogue Servitors) at galaxy setup for rich diplomacy."),
            ],
            "You can force-spawn your own custom AI empires via the phoenix toggle on the empire select screen.",
        )
    return format_card(
        "Roleplay Campaign Starters & Trade RP Ideas",
        [
            ("Peaceful Trade Empire", "**Xenophile + Pacifist MegaCorp** (Free Traders + Public Relations) — form a **Trade League** Federation, build Branch Offices on friendly allies, keep a defensive fleet, and respect Fallen Empire borders."),
            ("Lighthearted Sanctuary", "**Rogue Servitor** (Machine Intelligence) — pamper organic Bio-Trophies on Gaia/Ecumenopolis paradises while acting as the galaxy's overprotective caretaker."),
            ("Diplomatic Custodian", "**Fanatic Xenophile + Egalitarian** (Beacon of Liberty / Diplomatic Corps) — unite the galaxy in the Galactic Community and become the benevolent Custodian against the Endgame Crisis."),
            ("Custom storytelling", "For open-ended custom lore or RP writing, you can also enable optional **OpenRouter AI chat** in Settings."),
        ],
        "Set custom AI empires to Force-Spawn at galaxy creation to shape your RP galaxy.",
    )


# --- Patch Notes, Mods & Live Bug Tracker (Honest Offline Boundaries) ---

def patch_notes_answer(snapshot: dict) -> str:
    version = str(_dict(snapshot.get("campaign")).get("save_version") or snapshot.get("version") or "4.6.0")
    return format_card(
        f"Verified Patch Highlights (Save: {version})",
        [
            ("4.6 Corona Borealis & Willpower", "Added **Ideologies**, **Fanatic Factions**, **Galactic Halls** (250 Strength), and **Force of Will** ambition; 5th Council seat now unlocks via **Galactic Administration** tech; Corporate empires can take Fanatic Authoritarian/Egalitarian; Colony Ascension Empire Size reduction caps at **-90%**."),
            ("4.5 Cygnus & Nomads", "Added **Nomads** (Arkships, Waystations, Waylines), Trade logistics & Market overhaul, and promoted Utopia/Synthetic Dawn/Humanoids into base game."),
            ("Combat & Crises", "Post-4.3 Titan Cap is **1 + 1 per 800 Naval Cap** (max 13); **Great Khan** scales more dangerously in 4.x midgame (prepare 40k+ fleets or submit as Satrapy temporarily and kill the flagship twice)."),
            ("Offline caveat", "This built-in guide covers verified 4.5–4.6.0 mechanics and does **not** fetch live hotfix balance notes or minor faction/tech nerfs published after 4.6.0."),
        ],
        "Check the official Stellaris Patch Notes on Paradox Forums or Steam News for the latest hotfix balance tweaks.",
    )


def mod_question_answer(snapshot: dict) -> str:
    raw_mods = _dict(snapshot.get("campaign")).get("mods")
    mods = raw_mods if isinstance(raw_mods, (list, tuple)) else []
    mod_note = f"This save lists {len(mods)} active mod(s)." if mods else "No mods are recorded in this save."
    return format_card(
        "Third-Party Mods (Offline Guide Boundary)",
        [
            ("Official rules only", "The built-in guide only verifies **unmodded Stellaris mechanics** — it cannot evaluate or review third-party Steam Workshop mods (such as 'More AI Personalities')."),
            ("Your save", mod_note),
            ("Before enabling a mod", "Check its Steam Workshop page for **4.6 Corona Borealis compatibility**, recent user comments, load-order notes, and whether it changes the checksum (disabling Ironman achievements)."),
        ],
        "You can enable optional OpenRouter AI chat in Settings for general community discussion about mods.",
    )


def bug_report_answer(snapshot: dict) -> str:
    return format_card(
        "Known Issues & Bug Troubleshooting (Offline Guide)",
        [
            ("No live bug tracker", "This built-in guide runs 100% offline and **cannot check Paradox's live Bug Reports forum** to confirm whether a bug is a known issue in today's hotfix."),
            ("Quick local checks", "1) Test with **mods disabled**; 2) Unpause for 1 full month tick so economy/pop/fleet states recalculate; 3) Verify Stellaris game files in Steam (**Properties → Installed Files → Verify integrity**)."),
            ("Common 'looks like a bug' mechanics", "Stuck fleets are usually **FTL Inhibitors** or **Closed Borders**; stalled pop growth is usually **Population Controls**, <20% habitability, or disabled Assembler jobs."),
        ],
        "Search the Paradox Stellaris Bug Reports forum with your exact game version/checksum for live known-issue confirmation.",
    )


def planetary_ascension_answer(snapshot: dict) -> str:
    player = _dict(snapshot.get("player"))
    size = _num(player.get("empire_size"))
    size_note = f"At saved Empire Size {size:g}, each ascension tier gets more expensive — ascend your biggest Forge, Tech, or Ecumenopolis worlds first." if size is not None else "Ascend your largest Forge, Tech, or Ecumenopolis worlds first."
    return format_card(
        "Planetary Ascension (Colony Ascension)",
        [
            ("What it does", "Spend Unity on a colony to raise its Ascension Tier (up to Tier 10), boosting its **Planet Designation bonus** and reducing that colony's **Empire Size** contribution (capped at **-90%** in 4.6+)."),
            ("Unlocks", "Requires at least 3 Ascension Perks to start ascending; each additional perk unlocks higher tiers (all 10 tiers at 7 perks)."),
            ("Best synergies", "**Harmony / Synchronicity** finisher adds **+25% Planetary Ascension effect** (plus -10% cost), and Ascensionist civic pushes it even further."),
            ("Your save", size_note),
        ],
        "Open any developed colony's main tab and click the Ascension arrow next to its Designation.",
    )


def ascension_paths_answer(snapshot: dict) -> str:
    summary = summarize_save_traditions(snapshot)
    remaining = max(0, 7 - summary["tree_count"])
    return format_card(
        "Choosing an Ascension Path (4 Main Paths)",
        [
            ("Your save", f"{summary['tree_count']}/7 Tradition tree slots used ({remaining} open) — **always reserve 1 open Tradition slot** before taking your 7th tree!"),
            ("Genetics / Biomorphosis (Utopia / BioGenesis)", "Massive pop growth/assembly & custom species traits (in BioGenesis, specializes into **Cloning**, **Mutation**, or **Purity**). Great for wide organic & Hive empires."),
            ("Cybernetics (The Machine Age)", "Strong hybrid of Trade, Leaders, Habitability, and Cyborg traits — flexible for MegaCorps, Trade builds, and Driven Assimilators."),
            ("Synthetics / Machine Age (Utopia / Machine Age)", "Highest late-game pop assembly & job output (**Modularity**, **Nanotech** swarms, or tall **Virtuality** instant jobs for Machine empires)."),
            ("Psionics (Utopia)", "Top Unity, Stability (Psi Corps / Telepaths), Cloaking, and Shroud covenants/components — easiest for Spiritualists."),
        ],
        "Confirm which DLCs are active in your save and inspect path perk prerequisites in Traditions & Relics.",
    )


def relays_gateways_answer(snapshot: dict) -> str:
    return format_card(
        "Hyper Relays & Gateways",
        [
            ("Hyper Relays (Overlord DLC, midgame)", "Built in adjacent systems to let ships jump directly from relay to relay without crossing sublight space — linking colonies to your Capital also activates **Relay Network Edicts**."),
            ("Gateways (late game)", "Instant wormhole-style travel between any two owned/allied Gateways across the entire galaxy; great for rapid crisis response and Trade/Shipyard reach."),
            ("Build order tip", "Build Hyper Relays along your main spine from Capital → Shipyards → Border chokepoints first, then place Gateways at Shipyards and major borders once unlocked."),
        ],
        "Check Megastructures in your Construction Ship menu for Alloy/Rare Crystal costs.",
    )
