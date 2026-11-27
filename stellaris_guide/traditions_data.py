"""Verified Stellaris 4.6.0 Tradition trees & Ascension Perks catalog and save-fit helpers."""
from __future__ import annotations

import re

# Concise, original mechanical summaries verified against Stellaris 4.6.0 game files.
# Keys are canonical lookup IDs used by question_context.py and advice.py.

TRADITIONS: dict[str, dict] = {
    "prosperity": {
        "name": "Prosperity",
        "kind": "tradition",
        "prefix": "tr_prosperity_",
        "dlc": None,
        "ambiguous": False,
        "aliases": ("prosperity",),
        "adopt": "+20% mining/gathering station output (Nomads: +10% Arkship harvest output, +25% stockpile capacity) and unlocks the Favored Society agenda",
        "picks": (
            "-10% colony building/district cost and +25% build speed; "
            "-10% building/district upkeep; +100 Housing per City District "
            "(Void Dwellers/Nomads: +1 max Habitat/Arkship district); "
            "-5% job upkeep; and +5% output from all colony jobs"
        ),
        "finish": "+25% station output (Nomads: +15% Arkship harvest output) + 1 Ascension Perk slot",
        "role": "Core economic snowballs: lowers build/upkeep costs and boosts every job and station empire-wide.",
    },
    "discovery": {
        "name": "Discovery",
        "kind": "tradition",
        "prefix": "tr_discovery_",
        "dlc": None,
        "ambiguous": True,
        "aliases": ("discovery",),
        "adopt": "+20% anomaly research speed",
        "picks": (
            "+35% science ship survey speed and +50% disengage chance; "
            "+20% research station and starbase research output; "
            "+1 Research Alternative, +1 Scientist cap, and +1 starting Scientist skill; "
            "+20% Scientist XP and -15% Scientist upkeep; plus Faith in Science researcher upkeep relief"
        ),
        "finish": "+10% overall Research Speed + 1 Ascension Perk slot",
        "role": "Best early-game tech & exploration opener: faster surveying, extra tech draws, and +10% research speed.",
    },
    "expansion": {
        "name": "Expansion",
        "kind": "tradition",
        "prefix": "tr_expansion_",
        "dlc": None,
        "ambiguous": True,
        "aliases": ("expansion",),
        "adopt": "+25% colony development, terraforming, and megastructure build speed; -20% starbase/habitat/waystation alloy upkeep",
        "picks": (
            "+1 starting Urban District on new colonies; +10% founder pop growth; "
            "-15% Empire Size from systems and colonies; -10% starbase/waystation Influence cost; "
            "and -20% starbase upkeep with +50% starbase capacity multiplier"
        ),
        "finish": "+1 max districts on non-artificial planets + 1 Ascension Perk slot",
        "role": "Strong early wide-empire opener: cheaper claims/outposts, faster colony ramp, and lower Empire Size from space.",
    },
    "supremacy": {
        "name": "Supremacy",
        "kind": "tradition",
        "prefix": "tr_supremacy_",
        "dlc": None,
        "ambiguous": False,
        "aliases": ("supremacy",),
        "adopt": "+20 Naval Capacity and +20% army damage",
        "picks": (
            "-10% ship upkeep and +20% Naval Capacity; +25% shipyard build speed; "
            "+10% fleet command limit, +1 Commander cap, and +1 starting Commander skill; "
            "+10% ship fire rate and +20% bombardment; +20% damage vs starbases"
        ),
        "finish": "Unlocks War Doctrines policy & Supremacist stance + 1 Ascension Perk slot",
        "role": "Essential military tree before major wars or crisis prep: boosts naval cap, ship fire rate, and shipyard speed.",
    },
    "statecraft": {
        "name": "Statecraft",
        "kind": "tradition",
        "prefix": "tr_statecraft_",
        "dlc": None,
        "ambiguous": False,
        "aliases": ("statecraft",),
        "adopt": "+50 Edict Fund",
        "picks": (
            "+25% Council Agenda speed; +25% Agenda finishing-effect duration; "
            "extra Council Agendas; bonus Councilor XP whenever any Agenda finishes; "
            "and +1 effective Councilor skill"
        ),
        "finish": "-5% Empire Size + 1 Ascension Perk slot",
        "role": "Top-tier early/midgame scaling tree: rapidly levels your entire Council via agendas and cuts Empire Size.",
    },
    "aptitude": {
        "name": "Aptitude",
        "kind": "tradition",
        "prefix": "tr_aptitude_",
        "dlc": "Galactic Paragons",
        "ambiguous": False,
        "aliases": ("aptitude",),
        "adopt": "+1 Leader trait selection option",
        "picks": (
            "-25% Leader recruit cost and +1 pool size; +1 cap for Commanders, Officials, and Scientists "
            "with -1 max negative traits; +10% Leader lifespan and -25% Leader upkeep; "
            "+1 Leader skill; plus Leadership Conditioning agenda"
        ),
        "finish": "+1 starting Leader trait + 1 Ascension Perk slot",
        "role": "Leader-focused tree: raises all three Leader caps, reduces upkeep, and strengthens trait rolls.",
    },
    "mercantile": {
        "name": "Mercantile",
        "kind": "tradition",
        "prefix": "tr_mercantile_",
        "dlc": None,
        "ambiguous": False,
        "aliases": ("mercantile",),
        "adopt": "-20% Trader upkeep",
        "picks": (
            "+15% pop Trade output; extra Trader jobs and +200 Amenities per Trader unit; "
            "unlocks Consumer Benefits & Marketplace of Ideas Trade Policies (convert Trade to Consumer Goods or Unity); "
            "+10% job Trade output; and -10% Market fee"
        ),
        "finish": "+10% empire Trade output + 1 Ascension Perk slot",
        "role": "Core Trade/MegaCorp tree: turns Trade into Consumer Goods or Unity and slashes Market fees.",
    },
    "logistics": {
        "name": "Logistics",
        "kind": "tradition",
        "prefix": "tr_logistics_",
        "dlc": None,
        "ambiguous": True,
        "aliases": ("logistics",),
        "adopt": "+5% Logistics Drone workforce bonus",
        "picks": (
            "+2 Trade per Trader; +1 Trade from Maintenance Drones and -5% structure upkeep; "
            "-10% Market fee; and -10% ship logistics upkeep"
        ),
        "finish": "+10% empire Trade output + 1 Ascension Perk slot",
        "role": "Gestalt Trade & logistics tree: stabilizes Trade income and trims fleet/structure logistics upkeep.",
    },
    "harmony": {
        "name": "Harmony",
        "kind": "tradition",
        "prefix": "tr_harmony_",
        "dlc": None,
        "ambiguous": True,
        "aliases": ("harmony",),
        "adopt": "-10% pop upkeep",
        "picks": (
            "+25% governing ethics attraction and -10 Crime; -5% Empire Size from pops and +20% refugee attraction; "
            "+3 Colony Stability and -10% Planetary Ascension cost; +50 Edict Fund; "
            "+10 Leader lifespan and -1 max negative trait"
        ),
        "finish": "+25% Planetary Ascension effect + 1 Ascension Perk slot",
        "role": "Stability, tall-empire, and Planetary Ascension tree: lowers pop upkeep/size and buffs Stability.",
    },
    "synchronicity": {
        "name": "Synchronicity",
        "kind": "tradition",
        "prefix": "tr_synchronicity_",
        "dlc": None,
        "ambiguous": False,
        "aliases": ("synchronicity",),
        "adopt": "-10% pop upkeep and unlocks Gestalt node-boost Council Agendas",
        "picks": (
            "+30% auto-resettlement; -20% Leader upkeep and -5% Empire Size from pops; "
            "+3 Stability and -10% Planetary Ascension cost; +50 Edict Fund and +1 restored node skill; "
            "+10 Leader lifespan and -1 max negative trait"
        ),
        "finish": "+25% Planetary Ascension effect + 1 Ascension Perk slot",
        "role": "Gestalt equivalent of Harmony: cuts pop/leader upkeep, improves Stability, and powers Planetary Ascension.",
    },
    "unyielding": {
        "name": "Unyielding",
        "kind": "tradition",
        "prefix": "tr_unyielding_",
        "dlc": None,
        "ambiguous": False,
        "aliases": ("unyielding",),
        "adopt": "+2 Starbase Capacity and +50% starbase upgrade speed",
        "picks": (
            "+25% defense army health; -25% bombardment damage, -25% war exhaustion, and +25% hostile claim cost; "
            "+33% defensive-war ship build speed and +15% home-territory fire rate; "
            "+33% starbase & defense platform damage and hull; +2 Starbase Capacity and -50% starbase upgrade cost"
        ),
        "finish": "+50% defense platform capacity and -20% starbase upkeep + 1 Ascension Perk slot",
        "role": "Defensive & Starbase-economy tree (+4 total Starbase Capacity): great for chokepoints, Anchorages, and Hydroponics.",
    },
    "domination": {
        "name": "Domination",
        "kind": "tradition",
        "prefix": "tr_domination_",
        "dlc": None,
        "ambiguous": True,
        "aliases": ("domination",),
        "adopt": "+5% Worker output, +5% Slave workforce, and -25% Slave political power",
        "picks": (
            "+0.5 Influence/month, +1 Official cap, and +1 starting Official skill; "
            "extra Housing & Politician jobs on Capital buildings; +20% Councilor XP and +50 Edict Fund; "
            "+1 Unity per Enforcer (+0.5 per Telepath); and another +5% Worker/Slave output"
        ),
        "finish": "-5% Empire Size from pops + 1 Ascension Perk slot",
        "role": "Worker/Slaver & Influence tree: adds +10% total Worker output, +0.5 Influence/mo, and -5% pop Empire Size.",
    },
    "diplomacy": {
        "name": "Diplomacy",
        "kind": "tradition",
        "prefix": "tr_diplomacy_",
        "dlc": None,
        "ambiguous": True,
        "aliases": ("diplomacy",),
        "adopt": "-50% diplomatic Influence upkeep and -25% diplomatic Influence cost",
        "picks": (
            "Unlocks forming Federations, +1 Envoy, and +1 Federation cohesion; "
            "+100% Federation naval cap contribution and -25% border friction; "
            "+3 Unity per Embassy; +50 Trust cap and +33% Trust growth; +5 diplomatic acceptance"
        ),
        "finish": "+2 Federation XP, +10% Diplomatic Weight, and +1 Official cap + 1 Ascension Perk slot",
        "role": "Required to form a Federation and cut Influence drain from multiple diplomatic pacts.",
    },
    "subterfuge": {
        "name": "Subterfuge",
        "kind": "tradition",
        "prefix": "tr_subterfuge_",
        "dlc": "Nemesis",
        "ambiguous": False,
        "aliases": ("subterfuge",),
        "adopt": "-25% Espionage operation cost and +1 Decryption",
        "picks": (
            "+1 Encryption and +5 Ship Evasion; +1 hostile operation difficulty and +20% hostile cost; "
            "+1 Decryption, +2 operation skill, and +10 Ship Tracking; "
            "+1 Envoy and +10 max Spy Network; +50% infiltration speed"
        ),
        "finish": "+1 Ascension Perk slot (and pairs with Cloaking/Espionage builds)",
        "role": "Espionage & stealth-combat tree: speeds up spy networks and grants rare +5 Evasion / +10 Tracking.",
    },
    "adaptability": {
        "name": "Adaptability",
        "kind": "tradition",
        "prefix": "tr_adaptability_",
        "dlc": None,
        "ambiguous": True,
        "aliases": ("adaptability",),
        "adopt": "-10% pop housing usage (Wilderness: -10% building time)",
        "picks": (
            "-15% strategic resource structure cost/upkeep; -25% bombardment damage and +25% defense army damage; "
            "+10% Habitability; +1 max districts on planets and artificial worlds; "
            "-50% resettlement cost and +25% auto-resettlement"
        ),
        "finish": "Improves planetary designation bonuses + 1 Ascension Perk slot",
        "role": "Colony efficiency & Habitability tree: extra district slots, +10% Habitability, and stronger colony designations.",
    },
    "enmity": {
        "name": "Enmity",
        "kind": "tradition",
        "prefix": "tr_enmity_",
        "dlc": None,
        "ambiguous": False,
        "aliases": ("enmity",),
        "adopt": "+1 max Rivalry and +1 Ideological Rivalry",
        "picks": (
            "Per-rival bonuses, opposing Diplomatic Weight, catch-up bonuses while weaker than a Rival "
            "(military/tech/economy), +15% damage vs Rivals & Ideological Rivals, and rewards for eclipsing a Rival"
        ),
        "finish": "+1 Envoy + 1 Ascension Perk slot",
        "role": "Rivalry snowball tree: excels on higher difficulties when rivals start stronger than you.",
    },
    "politics": {
        "name": "Politics",
        "kind": "tradition",
        "prefix": "tr_politics_",
        "dlc": "Overlord",
        "ambiguous": True,
        "aliases": ("politics",),
        "adopt": "+1 Envoy",
        "picks": (
            "Gain Favors when supported resolutions pass; 18 months Unity when your own resolution passes; "
            "-25% resolution cost; +25% Diplomatic Weight after another empire passes a resolution; "
            "-25% Veto and Emergency Measures cooldown"
        ),
        "finish": "+10% Diplomatic Weight + 1 Ascension Perk slot",
        "role": "Galactic Community control tree: accelerates Custodian/Imperium plays and farms Favors & Unity.",
    },
    "versatility": {
        "name": "Versatility",
        "kind": "tradition",
        "prefix": "tr_versatility_",
        "dlc": "Synthetic Dawn",
        "ambiguous": False,
        "aliases": ("versatility",),
        "adopt": "-10% Pop Assembler upkeep",
        "picks": (
            "+50 synthetic Trust cap and +1 Envoy; -10% Market fee; -10% Amenities usage; "
            "-5% job upkeep; and +1 Unity from Maintenance Drones"
        ),
        "finish": "+10% Pop Assembly speed (+1 Energy assembler upkeep) + 1 Ascension Perk slot",
        "role": "Machine Intelligence utility tree: boosts Pop Assembly, Unity from Maintenance Drones, and lowers job upkeep.",
    },
    "archivism": {
        "name": "Archivism",
        "kind": "tradition",
        "prefix": "tr_archivism_",
        "dlc": "Grand Archive",
        "ambiguous": False,
        "aliases": ("archivism",),
        "adopt": "-50% exhibit unlock cost and +5% anomaly chance",
        "picks": (
            "+30% archaeological excavation speed, +1 clue, and +30% Scientist XP; "
            "2x specimen sale value; +35% science ship speed and -50% upkeep; -25% specimen storage cooldown"
        ),
        "finish": "+15% Specimen output + 1 Ascension Perk slot",
        "role": "Grand Archive & dig-site tree: accelerates archaeological sites and scales Grand Archive specimen bonuses.",
    },
    "domestication": {
        "name": "Domestication",
        "kind": "tradition",
        "prefix": "tr_domestication_",
        "dlc": "Grand Archive",
        "ambiguous": False,
        "aliases": ("domestication",),
        "adopt": "+20% Farmer output and -10% Space Fauna build cost",
        "picks": (
            "+25% Vivarium capacity and +20% capture chance; +33% blocker clear speed; "
            "higher fauna breeding chance and +25% culling rewards; +5% pop growth and +15% fauna build speed"
        ),
        "finish": "Bonus Space Fauna XP gain + 1 Ascension Perk slot",
        "role": "Space Fauna fleet & Vivarium tree: supports biological/fauna builds and Food economy.",
    },
    "genetics": {
        "name": "Genetics / Biomorphosis",
        "kind": "tradition",
        "prefix": "tr_genetics_",
        "dlc": "Utopia / BioGenesis",
        "ambiguous": False,
        "aliases": ("genetics", "biomorphosis", "cloning", "mutation", "purity"),
        "adopt": "Unlocks advanced biological gene-modding (in BioGenesis, splits into Cloning, Mutation, or Purity flexible paths)",
        "picks": "Major pop growth/assembly, extra species trait points/picks, advanced biological traits, and specialized Cloning/Mutation/Purity bonuses",
        "finish": "Full biological ascension mastery + 1 Ascension Perk slot",
        "role": "Biological Ascension Path tree: remember to leave 1 of your 7 Tradition slots open before adopting it.",
    },
    "cybernetics": {
        "name": "Cybernetics",
        "kind": "tradition",
        "prefix": "tr_cybernetics_",
        "dlc": "The Machine Age",
        "ambiguous": False,
        "aliases": ("cybernetics", "cybernetic"),
        "adopt": "Begins Cybernetic pop assimilation and augmentation",
        "picks": "Cyborg species traits, Augmentation Centers, reduced pop upkeep, and cybernetic authority upgrades",
        "finish": "Full Cybernetic Ascension + 1 Ascension Perk slot",
        "role": "Cybernetic Ascension Path tree: strong trade/leader/habitability hybrid; reserve 1 Tradition slot.",
    },
    "synthetics": {
        "name": "Synthetics / Machine Ascension",
        "kind": "tradition",
        "prefix": "tr_synthetics_",
        "dlc": "Utopia / The Machine Age",
        "ambiguous": False,
        "aliases": ("synthetics", "synthetic ascension", "modularity", "nanotech", "virtuality"),
        "adopt": "Unlocks full Synthetic transformation (Machine empires choose Modularity, Nanotech, or Virtuality)",
        "picks": "Massive pop assembly/robot output (Synthetics/Modularity), infinite nanite swarms (Nanotech), or instant tall-colony jobs (Virtuality)",
        "finish": "Full Synthetic/Machine Ascension + 1 Ascension Perk slot",
        "role": "Synthetic/Machine Ascension Path tree: reserve 1 of your 7 Tradition slots before adopting.",
    },
    "psionics": {
        "name": "Psionics",
        "kind": "tradition",
        "prefix": "tr_psionics_",
        "dlc": "Utopia",
        "ambiguous": False,
        "aliases": ("psionics", "psionic"),
        "adopt": "Awakens Psionic species traits and Psi Corps access",
        "picks": "Psi Corps (Telepaths for stability/unity/output), Psionic assimilation, Shroud breach & covenants, and encryption/cloaking bonuses",
        "finish": "Full Psionic Ascension + 1 Ascension Perk slot",
        "role": "Psionic Ascension Path tree: excels at Unity, Stability, and high-tier Shroud components; reserve 1 Tradition slot.",
    },
}

ASCENSION_PERKS: dict[str, dict] = {
    "technological_ascendancy": {
        "name": "Technological Ascendancy",
        "kind": "perk",
        "id": "ap_technological_ascendancy",
        "dlc": None,
        "aliases": ("technological ascendancy", "tech ascendancy"),
        "effects": "+50% Rare Technology draw chance and unlocks Research Focus policies",
        "role": "Strong 1st-slot pick when chasing key rare techs (Mega-Engineering, Psionics, strategic/ship techs) and tailoring branch focus.",
    },
    "one_vision": {
        "name": "One Vision",
        "kind": "perk",
        "id": "ap_one_vision",
        "dlc": None,
        "aliases": ("one vision",),
        "effects": "+10% empire Unity output; regular empires get +50% Governing Ethics Attraction (+15% ideological faction attraction with Willpower); Gestalts get -10% Planetary Ascension cost (-10 Deviancy with Willpower)",
        "role": "Reliable 1st-slot Unity & stability pick, especially for Unity-rush, Spiritualist, or 4.6 Willpower Ideology builds.",
    },
    "imperial_prerogative": {
        "name": "Imperial Prerogative",
        "kind": "perk",
        "id": "ap_imperial_prerogative",
        "dlc": None,
        "aliases": ("imperial prerogative",),
        "effects": "-25% Empire Size from colonies and +2 Official Leader cap (Nomads: +15% Ruler workforce and +2 Official cap; not available to MegaCorps)",
        "role": "Top 1st-slot scaling pick for wide non-MegaCorp empires with many colonies to keep Tech and Tradition costs down.",
    },
    "executive_vigor": {
        "name": "Executive Vigor",
        "kind": "perk",
        "id": "ap_executive_vigor",
        "dlc": None,
        "aliases": ("executive vigor",),
        "effects": "+100 Edict Fund and +15% Council Agenda progress speed",
        "role": "Great early-game pick to run Capacity/Mining/Research Subsidies free of Unity drain while cycling Agendas faster.",
    },
    "transcendent_learning": {
        "name": "Transcendent Learning",
        "kind": "perk",
        "id": "ap_transcendent_learning",
        "dlc": None,
        "aliases": ("transcendent learning",),
        "effects": "+2 Scientist Leader cap, +25% Leader XP gain, and -15% Leader upkeep",
        "role": "Excellent 1st-slot pick for early exploration, anomaly farming, and leveling your Council & Scientists faster.",
    },
    "interstellar_dominion": {
        "name": "Interstellar Dominion",
        "kind": "perk",
        "id": "ap_interstellar_dominion",
        "dlc": None,
        "aliases": ("interstellar dominion",),
        "effects": "-20% starbase and claim Influence cost and -25% Empire Size from systems (Nomads: -20% Waystation Influence cost, +15% stockpile capacity)",
        "role": "Strong 1st-slot opener for aggressive early land-grabs and cheap war claims.",
    },
    "mastery_of_nature": {
        "name": "Mastery of Nature",
        "kind": "perk",
        "id": "ap_mastery_of_nature",
        "dlc": None,
        "aliases": ("mastery of nature",),
        "effects": "-33% blocker clearing cost and unlocks the Mastery of Nature planetary decision (+2 max districts); Nomads get +50% Arkship harvest output",
        "role": "Useful for tall empires squeezing extra districts out of small planets, or Nomads boosting Arkship harvesting.",
    },
    "shared_destiny": {
        "name": "Shared Destiny",
        "kind": "perk",
        "id": "ap_shared_destiny",
        "dlc": None,
        "aliases": ("shared destiny",),
        "effects": "+2 Envoys, -20% Specialist Subject conversion time, and +1 subject before Divided Patronage loyalty penalties apply",
        "role": "Key Overlord/vassal-swarm perk when managing multiple subjects without tanking Loyalty.",
    },
    "grasp_the_void": {
        "name": "Grasp the Void",
        "kind": "perk",
        "id": "ap_grasp_the_void",
        "dlc": None,
        "aliases": ("grasp the void",),
        "effects": "+5 Starbase Capacity",
        "role": "Immediate starbase relief for extra Anchorages (Naval Cap), Hydroponics Bays, or border chokepoints.",
    },
    "eternal_vigilance": {
        "name": "Eternal Vigilance",
        "kind": "perk",
        "id": "ap_eternal_vigilance",
        "dlc": None,
        "aliases": ("eternal vigilance",),
        "effects": "+1 Commander cap, +25% starbase/platform damage & hull, +5 defense platforms, -50% platform upkeep, +20% home-territory fire rate, and +1 Deep Space Citadel per system (BioGenesis); Nomads boost Waystations and Arkship fire rate",
        "role": "Strong defensive/turtling perk for holding chokepoints against stronger neighbors or crises.",
    },
    "voidborne": {
        "name": "Voidborne",
        "kind": "perk",
        "id": "ap_voidborn",
        "dlc": "Utopia",
        "aliases": ("voidborne", "voidborn"),
        "effects": "+2 max Habitat districts, -20% Habitat & Habitat-district cost, +25% minor-orbital districts, and +50% Habitat district jobs (Nomads: +2 max Arkship districts)",
        "role": "Must-have for Void Dwellers or Habitat-heavy tall empires.",
    },
    "arcology_project": {
        "name": "Arcology Project",
        "kind": "perk",
        "id": "ap_arcology_project",
        "dlc": "MegaCorp",
        "aliases": ("arcology project", "arcology", "ecumenopolis"),
        "effects": "Unlocks the Arcology Project decision to turn developed worlds into Ecumenopoleis (massive Alloy, Consumer Goods, and Unity hubs); requires Anti-Gravity Engineering and 2 prior perks",
        "role": "One of the strongest midgame economic perks for non-Gestalt (and Rogue Servitor) Alloy/Unity production.",
    },
    "world_shaper": {
        "name": "World Shaper",
        "kind": "perk",
        "id": "ap_world_shaper",
        "dlc": None,
        "aliases": ("world shaper", "gaia worlds"),
        "effects": "-25% terraforming cost and unlocks terraforming planets into Gaia Worlds (100% habitability, +10% job output & happiness); requires Climate Restoration",
        "role": "Clean mid/late-game economic multiplier for organic empires with many basic-resource worlds.",
    },
    "hive_worlds": {
        "name": "Hive Worlds",
        "kind": "perk",
        "id": "ap_hive_worlds",
        "dlc": "Utopia",
        "aliases": ("hive worlds", "hive world"),
        "effects": "Unlocks terraforming into Hive Worlds (uncapped basic districts, +10% job output, extra spawning drones) for Hive Minds",
        "role": "Core midgame economic perk for Hive Mind empires.",
    },
    "machine_worlds": {
        "name": "Machine Worlds",
        "kind": "perk",
        "id": "ap_machine_worlds",
        "dlc": "Synthetic Dawn",
        "aliases": ("machine worlds", "machine world"),
        "effects": "Unlocks terraforming into Machine Worlds (uncapped Mining/Generator districts, +10% job output, -10% housing usage) for non-Servitor Machine empires",
        "role": "Core midgame economic perk for Machine Intelligences.",
    },
    "master_builders": {
        "name": "Master Builders",
        "kind": "perk",
        "id": "ap_master_builders",
        "dlc": "Utopia",
        "aliases": ("master builders",),
        "effects": "+50% Megastructure build speed and +1 concurrent Megastructure build capacity",
        "role": "High-value late-midgame perk once you unlock Mega-Engineering and want to build multiple megastructures at once.",
    },
    "galactic_wonders": {
        "name": "Galactic Wonders",
        "kind": "perk",
        "id": "ap_galactic_wonders",
        "dlc": "Utopia / MegaCorp",
        "aliases": ("galactic wonders",),
        "effects": "Grants research options for Dyson Sphere, Ring World, and Matter Decompressor (MegaCorp); requires Mega-Engineering plus one completed/repaired megastructure",
        "role": "Premier late-game scaling perk to solve Energy, Minerals, and late-game pop/research capacity.",
    },
    "defender_of_the_galaxy": {
        "name": "Defender of the Galaxy",
        "kind": "perk",
        "id": "ap_defender_of_the_galaxy",
        "dlc": None,
        "aliases": ("defender of the galaxy",),
        "effects": "+50% fleet damage against Endgame Crises, Gray Tempest, Voidworms, and Player Crises (+200 opinion bonus with other empires)",
        "role": "Best late-game survival perk against high-strength Endgame Crises (mutually exclusive with Player Crisis / Ambition paths).",
    },
    "galactic_force_projection": {
        "name": "Galactic Force Projection",
        "kind": "perk",
        "id": "ap_galactic_force_projection",
        "dlc": None,
        "aliases": ("galactic force projection",),
        "effects": "+150 Naval Capacity, +20% Fleet Command Limit, +1 Commander cap, and +2 max Influence from Power Projection",
        "role": "Immediate military power spike (and +2 Influence/mo from fleet projection) for mid/late-game wars.",
    },
    "colossus_project": {
        "name": "Colossus Project",
        "kind": "perk",
        "id": "ap_colossus",
        "dlc": "Apocalypse",
        "aliases": ("colossus project",),
        "effects": "Unlocks the Colossus planet-killer ship and Total War Casus Belli, plus -15% War Exhaustion and -5% ship upkeep",
        "role": "Late-game conquest perk: eliminates Influence claim costs via Total War.",
    },
    "galactic_nemesis": {
        "name": "Galactic Nemesis (Become the Crisis)",
        "kind": "perk",
        "id": "ap_become_the_crisis",
        "dlc": "Nemesis",
        "aliases": ("become the crisis", "galactic nemesis"),
        "effects": "Unlocks the Menace Crisis path (cheap Mineral-built Menacing ships, Star-Eaters, and Aetherophasic Engine victory); -50% refugee attraction",
        "role": "Aggressive conquest/crisis-win path; mutually exclusive with Cosmogenesis, Defender of the Galaxy, and Force of Will.",
    },
    "cosmogenesis": {
        "name": "Cosmogenesis",
        "kind": "perk",
        "id": "ap_cosmogenesis",
        "dlc": "The Machine Age",
        "aliases": ("cosmogenesis",),
        "effects": "Unlocks the Science Crisis path (Synaptic Lathe, Fallen Empire buildings & Riddle Escort/Battlecruiser ships, Horizon Needle victory)",
        "role": "Strongest late-game tech-dominance path; mutually exclusive with other Crisis/Ambition perks.",
    },
    "force_of_will": {
        "name": "Force of Will",
        "kind": "perk",
        "id": "ap_force_of_will",
        "dlc": "Willpower",
        "aliases": ("force of will",),
        "effects": "4.6 Willpower Ambition path (requires 3+ perks, Fanatic empire, and Custodian of a non-Militarist/non-Xenophobe/non-Authoritarian Ideology)",
        "role": "4.6 Willpower ideological victory path; mutually exclusive with Defender of the Galaxy and Crisis perks.",
    },
    "lord_of_war": {
        "name": "Lord of War",
        "kind": "perk",
        "id": "ap_lord_of_war",
        "dlc": "Overlord",
        "aliases": ("lord of war",),
        "effects": "+1 Mercenary Enclave capacity, +25% Diplomatic Weight from Fleet Power, and boosted mercenary dividends",
        "role": "Niche perk for Mercenary Enclave / MegaCorp private-military builds.",
    },
    "enigmatic_engineering": {
        "name": "Enigmatic Engineering",
        "kind": "perk",
        "id": "ap_enigmatic_engineering",
        "dlc": "Apocalypse",
        "aliases": ("enigmatic engineering",),
        "effects": "+2 Encryption (and +2 Cloaking Strength with First Contact), prevents enemies from reverse-engineering your ship debris, and unlocks Fallen Empire building draws",
        "role": "Protects tech leads in wars and unlocks rare FE-tier infrastructure draws.",
    },
    "archaeoengineers": {
        "name": "Archaeo-Engineers",
        "kind": "perk",
        "id": "ap_archaeoengineers",
        "dlc": "First Contact",
        "aliases": ("archaeo engineers", "archaeoengineers"),
        "effects": "+1 Scientist cap, +33% Archaeotech weapon damage, -20% Minor Artifact ship cost, +25% Specimen output, and enhanced Archaeotech modules",
        "role": "Required if building fleets around Archaeotech weapons/shields or stacking Relic World / Grand Archive bonuses.",
    },
    "galactic_contender": {
        "name": "Galactic Contender",
        "kind": "perk",
        "id": "ap_galactic_contender",
        "dlc": None,
        "aliases": ("galactic contender",),
        "effects": "+20% Diplomatic Weight and bonus fleet damage against Fallen Empires, Awakened Empires, and Gate Builders",
        "role": "Situational late-game pick for conquering Fallen Empires or winning a War in Heaven.",
    },
    "nihilistic_acquisition": {
        "name": "Nihilistic Acquisition",
        "kind": "perk",
        "id": "ap_nihilistic_acquisition",
        "dlc": "Apocalypse",
        "aliases": ("nihilistic acquisition",),
        "effects": "Unlocks Raiding orbital bombardment stance to abduct enemy pops directly onto your colonies",
        "role": "Strong pop-growth shortcut for Authoritarian/Xenophobe/Gestalt raiding empires.",
    },
    "hydrocentric": {
        "name": "Hydrocentric",
        "kind": "perk",
        "id": "ap_hydrocentric",
        "dlc": "Aquatics",
        "aliases": ("hydrocentric",),
        "effects": "-25% Ocean terraforming cost, boosts the Aquatic species trait by +50%, and unlocks Expand Planetary Sea & Deluge Colossus",
        "role": "Signature perk for Aquatic species building Ocean worlds.",
    },
    "detox": {
        "name": "Detox",
        "kind": "perk",
        "id": "ap_detox",
        "dlc": "Toxoids",
        "aliases": ("detox",),
        "effects": "Allows terraforming Toxic Worlds with the Toxic Terraforming Candidate modifier into habitable planets",
        "role": "Situational wide-expansion pick only when you have multiple Toxic Terraforming Candidates in your borders.",
    },
    "universal_transactions": {
        "name": "Universal Transactions",
        "kind": "perk",
        "id": "ap_universal_transactions",
        "dlc": "MegaCorp",
        "aliases": ("universal transactions",),
        "effects": "+1 Official cap, -15% Branch Office cost, and waives Commercial Pact Influence upkeep for MegaCorps",
        "role": "High-value early/midgame perk for MegaCorps signing many Commercial Pacts.",
    },
    "consecrated_worlds": {
        "name": "Consecrated Worlds",
        "kind": "perk",
        "id": "ap_consecrated_worlds",
        "dlc": None,
        "aliases": ("consecrated worlds",),
        "effects": "Spiritualist decision to consecrate up to 3 uncolonized worlds (especially Gaia/Holy Worlds) for empire-wide Unity, Amenities, and Spiritualist attraction",
        "role": "Roleplay/Spiritualist Unity perk; also lets you appease the Holy Guardians Fallen Empire.",
    },
    "behemoth_fury": {
        "name": "Behemoth Fury",
        "kind": "perk",
        "id": "ap_behemoths",
        "dlc": "BioGenesis",
        "aliases": ("behemoth fury", "behemoths"),
        "effects": "BioGenesis biological Crisis path raising colossal space Behemoths; -50% refugee attraction",
        "role": "Biological player-crisis path; mutually exclusive with other Crisis/Ambition perks.",
    },
    "wanderlust": {
        "name": "Wanderlust",
        "kind": "perk",
        "id": "ap_wanderlust",
        "dlc": "Nomads",
        "aliases": ("wanderlust",),
        "effects": "+1 max artificial/Arkship district and -10% Leader upkeep",
        "role": "Nomad/Arkship-focused perk to expand onboard Arkship capacity.",
    },
}

# Map save prefix -> canonical tradition key for status inspection.
_PREFIX_TO_TRADITION: dict[str, str] = {
    "tr_prosperity_": "prosperity",
    "tr_discovery_": "discovery",
    "tr_expansion_": "expansion",
    "tr_supremacy_": "supremacy",
    "tr_statecraft_": "statecraft",
    "tr_aptitude_": "aptitude",
    "tr_mercantile_": "mercantile",
    "tr_logistics_": "logistics",
    "tr_harmony_": "harmony",
    "tr_synchronicity_": "synchronicity",
    "tr_unyielding_": "unyielding",
    "tr_domination_": "domination",
    "tr_diplomacy_": "diplomacy",
    "tr_subterfuge_": "subterfuge",
    "tr_adaptability_": "adaptability",
    "tr_enmity_": "enmity",
    "tr_politics_": "politics",
    "tr_versatility_": "versatility",
    "tr_archivism_": "archivism",
    "tr_domestication_": "domestication",
    "tr_genetics_": "genetics",
    "tr_cloning_": "genetics",
    "tr_mutation_": "genetics",
    "tr_purity_": "genetics",
    "tr_cybernetics_": "cybernetics",
    "tr_synthetics_": "synthetics",
    "tr_modularity_": "synthetics",
    "tr_nanotech_": "synthetics",
    "tr_virtuality_": "synthetics",
    "tr_psionics_": "psionics",
}

_AP_ID_TO_PERK: dict[str, str] = {
    item["id"]: key for key, item in ASCENSION_PERKS.items()
}
_AP_ID_TO_PERK.update({
    "ap_defender_of_the_galaxy_nomads": "defender_of_the_galaxy",
    "ap_eternal_vigilance_nomads": "eternal_vigilance",
    "ap_galactic_wonders_utopia": "galactic_wonders",
    "ap_galactic_wonders_megacorp": "galactic_wonders",
    "ap_galactic_wonders_utopia_and_megacorp": "galactic_wonders",
})


def _phrase_present(words: str, phrase: str) -> bool:
    pattern = r"(?<!\w)" + re.escape(phrase).replace(r"\ ", r"\s+") + r"(?!\w)"
    return bool(re.search(pattern, words))


def find_tradition_perk_mentions(words: str, *, has_tp_context: bool, raw_words: str = "") -> list[tuple[str, str]]:
    """Return ordered list of ('tradition'|'perk', key) mentioned in normalized/raw words."""
    found: list[tuple[int, str, str]] = []
    seen: set[tuple[str, str]] = set()
    sources = (words, raw_words) if raw_words and raw_words != words else (words,)

    for key, item in ASCENSION_PERKS.items():
        for alias in item["aliases"]:
            pat = r"(?<!\w)" + re.escape(alias).replace(r"\ ", r"\s+") + r"(?!\w)"
            for src in sources:
                m = re.search(pat, src)
                if m and ("perk", key) not in seen:
                    seen.add(("perk", key))
                    found.append((m.start(), "perk", key))
                    break
            if ("perk", key) in seen:
                break

    unambiguous_found = bool(found)
    for key, item in TRADITIONS.items():
        if item.get("ambiguous"):
            continue
        for alias in item["aliases"]:
            pat = r"(?<!\w)" + re.escape(alias).replace(r"\ ", r"\s+") + r"(?!\w)"
            for src in sources:
                m = re.search(pat, src)
                if m and ("tradition", key) not in seen:
                    seen.add(("tradition", key))
                    found.append((m.start(), "tradition", key))
                    unambiguous_found = True
                    break
            if ("tradition", key) in seen:
                break

    # Ambiguous common-English tradition names (e.g. discovery, expansion, diplomacy)
    # require explicit tradition/perk framing OR pairing with another detected tree/perk
    # OR a direct "X vs Y" / "X or Y" comparison where >=2 ambiguous traditions appear.
    ambiguous_hits: list[tuple[int, str, str]] = []
    for key, item in TRADITIONS.items():
        if not item.get("ambiguous"):
            continue
        for alias in item["aliases"]:
            pat = r"(?<!\w)" + re.escape(alias).replace(r"\ ", r"\s+") + r"(?!\w)"
            for src in sources:
                m = re.search(pat, src)
                if m and ("tradition", key) not in seen:
                    ambiguous_hits.append((m.start(), "tradition", key))
                    break
            if any(k == key for _, _, k in ambiguous_hits):
                break

    has_vs_compare = bool(re.search(r"(?<!\w)(?:vs|versus|or)(?!\w)", words))
    if has_tp_context or unambiguous_found or (has_vs_compare and len(ambiguous_hits) >= 2):
        for pos, kind, key in ambiguous_hits:
            if (kind, key) not in seen:
                seen.add((kind, key))
                found.append((pos, kind, key))

    found.sort(key=lambda entry: entry[0])
    return [(kind, key) for _, kind, key in found]


def summarize_save_traditions(snapshot: dict) -> dict:
    """Summarize adopted/finished Tradition trees and picked Ascension Perks from snapshot.player.profile."""
    player = snapshot.get("player")
    profile = player.get("profile") if isinstance(player, dict) else None
    if not isinstance(profile, dict):
        profile = {}
    raw_tr_val = profile.get("traditions")
    raw_ap_val = profile.get("ascension_perks")
    raw_tr = [item for item in raw_tr_val if isinstance(item, str)] if isinstance(raw_tr_val, (list, tuple)) else []
    raw_ap = [item for item in raw_ap_val if isinstance(item, str)] if isinstance(raw_ap_val, (list, tuple)) else []

    trees: dict[str, dict] = {}
    for tr_id in raw_tr:
        matched_key = None
        for prefix, key in _PREFIX_TO_TRADITION.items():
            if tr_id.startswith(prefix):
                matched_key = key
                break
        if not matched_key:
            continue
        entry = trees.setdefault(matched_key, {"adopted": False, "finished": False, "picks": 0})
        if tr_id.endswith("_adopt") or "_adopt_" in tr_id:
            entry["adopted"] = True
        elif tr_id.endswith("_finish") or "_finish_" in tr_id:
            entry["finished"] = True
            entry["adopted"] = True
        else:
            entry["picks"] += 1
            entry["adopted"] = True

    perks: list[str] = []
    perk_keys: set[str] = set()
    for ap_id in raw_ap:
        key = _AP_ID_TO_PERK.get(ap_id)
        if key:
            perk_keys.add(key)
            perks.append(ASCENSION_PERKS[key]["name"])
        else:
            label = ap_id.removeprefix("ap_").replace("_", " ").title()
            perks.append(label)

    return {
        "trees": trees,
        "tree_count": len(trees),
        "finished_count": sum(1 for item in trees.values() if item["finished"]),
        "perk_names": perks,
        "perk_keys": perk_keys,
        "raw_traditions_present": bool(raw_tr),
    }
