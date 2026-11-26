"""Pure-stdlib entry point for client-side browser execution (Pyodide Web Worker).

Reuses the exact same save parser, DLC registry, strategy planner, playbooks,
and built-in chat guide as the desktop application with zero server uploads
and zero Windows/Pillow/local-filesystem dependencies.
"""

from __future__ import annotations

import copy
import json
import time

from .advice import answer_question, make_advice
from .dlcs import DLC_CATALOG, active_dlcs, dlc_display_name, normalize_dlc_id
from .saves import parse_save_bytes

APP_VERSION = "1.7.0-web"
WEB_MAX_GAMESTATE_BYTES = 120_000_000
_LAST_RAW_CHAIN: list[dict] = []
_LAST_ADVICE: dict | None = None
_LAST_PLAN: dict = {}


def public_snapshot(snapshot: dict | None, *, spoilers_active: bool = False) -> dict | None:
    """Mirror server.py's spoiler boundary and hide military ordering when spoilers are off."""
    if snapshot is None:
        return None
    if spoilers_active:
        return {**{k: v for k, v in snapshot.items() if k != "_save_fingerprint"},
                "_spoilers_active": True}
    visible = dict(snapshot)
    visible.pop("_save_fingerprint", None)
    visible["_spoilers_active"] = False
    visible["contacts"] = sorted(
        [
            {**{k: v for k, v in contact.items()
                if k not in ("military", "economy", "technology", "hidden", "wars")},
             "wars": [war for war in contact.get("wars", []) if war.get("against_player")]}
            for contact in snapshot.get("contacts", [])
        ],
        key=lambda item: (str(item.get("name") or "").casefold(), item.get("id", 0)),
    )
    return visible


def public_history_snapshot(snapshot: dict, *, spoilers_active: bool = False) -> dict:
    visible = public_snapshot(snapshot, spoilers_active=spoilers_active)
    visible.pop("campaign", None)
    technology = visible.get("technology")
    if isinstance(technology, dict):
        visible["technology"] = {k: v for k, v in technology.items()
                                 if k not in ("researched", "researched_status")}
    return visible


def analyze_save_archive(raw_bytes: bytes, filename: str = "autosave.sav", *,
                         modified: float = 0.0,
                         history: list[dict] | None = None,
                         plan: dict | None = None,
                         spoilers_active: bool = False,
                         campaign_label: str = "") -> dict:
    """Parse one .sav ZIP archive in memory; keep unredacted snapshots inside worker memory."""
    global _LAST_RAW_CHAIN, _LAST_ADVICE, _LAST_PLAN
    snapshot = parse_save_bytes(
        raw_bytes, filename=filename, modified=modified or time.time(),
        campaign_label=campaign_label, include_details=True, game_dir="",
        max_gamestate_bytes=WEB_MAX_GAMESTATE_BYTES,
    )
    prior_source = list(history) if history is not None else list(_LAST_RAW_CHAIN)
    prior = [item for item in prior_source
             if item.get("campaign", {}).get("id") == snapshot["campaign"]["id"]
             and item.get("date") != snapshot.get("date")][-5:]
    chain = [*prior, snapshot]
    plan_store = dict(plan or _LAST_PLAN)
    advice = make_advice(snapshot, chain, plan_store)
    _LAST_RAW_CHAIN = chain
    _LAST_ADVICE = advice
    _LAST_PLAN = plan_store
    return {
        "status": "ready",
        "snapshot": public_snapshot(snapshot, spoilers_active=spoilers_active),
        "history": [public_history_snapshot(item, spoilers_active=spoilers_active) for item in chain],
        "advice": advice,
        "plan": plan_store,
        "save_token": snapshot.get("_save_fingerprint", "")[:16],
        "error": None,
        "updated_at": time.time(),
        "app_version": APP_VERSION,
        "web_mode": True,
    }


def reproject_current_save(*, spoilers_active: bool = False) -> dict:
    """Re-project the currently loaded save and its history for spoiler toggles."""
    if not _LAST_RAW_CHAIN:
        raise ValueError("No uploaded save is currently loaded.")
    latest = _LAST_RAW_CHAIN[-1]
    return {
        "status": "ready",
        "snapshot": public_snapshot(latest, spoilers_active=spoilers_active),
        "history": [public_history_snapshot(item, spoilers_active=spoilers_active)
                    for item in _LAST_RAW_CHAIN],
        "advice": _LAST_ADVICE or {},
        "plan": _LAST_PLAN,
        "save_token": latest.get("_save_fingerprint", "")[:16],
        "error": None,
        "updated_at": time.time(),
        "app_version": APP_VERSION,
        "web_mode": True,
    }


def _demo_presets() -> dict[str, dict]:
    return {
        "une-452": {
            "label": "UNE Settled (4.5.2 Cygnus)",
            "description": "Balanced early-mid campaign with a food/trade watch and an unstable colony.",
            "default_dlcs": ["Apocalypse", "Overlord", "Nemesis"],
            "snapshot": {
                "path": "demo/une-2277.sav", "filename": "autosave_2277.10.01.sav", "modified": 1760000000.0,
                "version": "Cygnus v4.5.2", "date": "2277.10.01", "empire": "United Nations of Earth",
                "campaign": {
                    "id": "demo452une000001", "player_country_id": 0,
                    "save_version": "Cygnus v4.5.2", "save_date": "2277.10.01",
                    "required_dlcs": ["Apocalypse", "Overlord", "Nemesis"],
                    "mods": [],
                    "installed": {"version": None, "checksum": None, "version_match": "unknown",
                                  "playset_mods": None, "mod_match": "unknown"},
                },
                "player": {
                    "id": 0, "military": 2850, "economy": 1420, "technology": 980,
                    "naval_used": 48, "naval_capacity": None, "starbase_used": 6, "starbase_capacity": 7,
                    "empire_size": 168, "colonies": 3,
                    "stock": {"energy": 2400.0, "minerals": 1850.0, "food": 42.0,
                              "consumer_goods": 610.0, "alloys": 920.0, "unity": 3100.0,
                              "influence": 945.0, "trade": 380.0},
                    "net": {"energy": 44.5, "minerals": 82.0, "food": -18.0,
                            "consumer_goods": 11.4, "alloys": 32.5, "unity": 68.0,
                            "influence": 4.2, "trade": -12.5},
                    "stock_known": {k: True for k in ("energy", "minerals", "food", "consumer_goods", "alloys", "unity", "influence", "trade")},
                    "net_known": {k: True for k in ("energy", "minerals", "food", "consumer_goods", "alloys", "unity", "influence", "trade")},
                    "research": {"physics": 124.0, "society": 138.0, "engineering": 116.0},
                    "profile": {
                        "authority": "auth_democratic", "origin": "origin_default",
                        "civics": ["civic_beacon_of_liberty", "civic_idealistic_foundation"],
                        "ethics": ["ethic_fanatic_egalitarian", "ethic_xenophile"],
                        "traditions": ["tr_discovery_adopt", "tr_expansion_adopt"],
                        "ascension_perks": ["ap_technological_ascendancy"],
                        "is_hive": False, "is_machine": False, "is_gestalt": False,
                        "is_megacorp": False, "is_nomad": False, "is_wilderness": False,
                        "shipset_kind": "mechanical", "uses_consumer_goods": True,
                        "uses_food": True, "ideology_active": None,
                    },
                },
                "contacts": [
                    {"id": 2, "name": "Commonwealth of Man", "kind": "default", "military": 4100,
                     "economy": 1380, "technology": 920, "opinion": -78, "intel": 42.0,
                     "spy_network": True, "wars": [], "relation": {"hostile": True, "embassy": False},
                     "hidden": {"stock": {"alloys": 1450}, "net": {"alloys": 48.0}}},
                    {"id": 3, "name": "Tzynn Star Hegemony", "kind": "default", "military": 2200,
                     "economy": 1100, "technology": 790, "opinion": 35, "intel": 55.0,
                     "spy_network": False, "wars": [], "relation": {"hostile": False, "embassy": True},
                     "hidden": {"stock": {"alloys": 600}, "net": {"alloys": 19.0}}},
                ],
                "policies": {
                    "fleet_doctrine": "battle_line",
                    "weapon_preference": "weapon_preference_kinetic",
                    "defense_preference": "defense_preference_balanced",
                },
                "flag": {"icon_category": "human", "icon_file": "flag_human_9.dds", "background_file": "00_solid.dds", "colors": ["blue", "dark_blue", "null"]},
                "planets": [
                    {
                        "id": 1, "planet_id": 10, "name": "Earth", "system": "Sol", "class": "Continental", "class_key": "pc_continental",
                        "size": 18, "size_known": True, "designation": "Empire Capital", "designation_key": "col_capital",
                        "stability": 74.0, "crime": 2.0, "pops": 42.0, "free_housing": 6.0, "free_amenities": 9.0,
                        "jobs": [{"type": "foundry", "filled": 8.0, "capacity": 8.0, "limit": 8.0, "disabled": False},
                                 {"type": "trader", "filled": 2.0, "capacity": 5.0, "limit": 5.0, "disabled": False}],
                        "districts": 11, "buildings": 6, "produces": {"alloys": 38.0, "trade": 32.0}, "upkeep": {"minerals": 24.0}, "profits": {"alloys": 38.0},
                        "recommendation": {"level": "stable", "title": "No urgent build", "action": "Let the colony grow and revisit when a job, housing or amenity warning appears.", "reason": "Housing, amenities and stability are currently comfortable."},
                        "job_advice": [],
                    },
                    {
                        "id": 2, "planet_id": 22, "name": "Alpha Centauri Prime", "system": "Alpha Centauri", "class": "Continental", "class_key": "pc_continental",
                        "size": 16, "size_known": True, "designation": "Agri-World", "designation_key": "col_farming",
                        "stability": 38.0, "crime": 14.0, "pops": 21.0, "free_housing": 1.0, "free_amenities": -7.5,
                        "jobs": [{"type": "farmer", "filled": 4.0, "capacity": 8.0, "limit": 8.0, "disabled": False},
                                 {"type": "entertainer", "filled": 0.0, "capacity": 2.0, "limit": 2.0, "disabled": False}],
                        "districts": 6, "buildings": 3, "produces": {"food": 26.0}, "upkeep": {"energy": 9.0}, "profits": {"food": 26.0},
                        "recommendation": {"level": "urgent", "title": "Add amenities", "action": "On Alpha Centauri Prime, check amenity jobs first; if they are filled, inspect the building menu for an amenity building.", "reason": "This colony has 7.5 fewer amenities than it uses. Check building availability and cost in game."},
                        "job_advice": [{"observation": "Amenities are -7.5. On this colony, 0 of 2 capacity is filled and 2 jobs are allowed.", "action": "Consider filling the open entertainer job.", "tradeoff": "Filling this job may draw workers from another resource.", "check": "Confirm entertainer job priority and available workforce in game.", "confidence": "Job capacity read from save; assignment must be checked in game."}],
                    },
                ],
                "technology": {
                    "researched_count": 34, "researched_status": "complete",
                    "researched": {"tech_corvettes": 1, "tech_destroyers": 1, "tech_lasers_2": 1, "tech_mass_drivers_2": 1},
                    "branches": {
                        "physics": {"current": "Blue Lasers", "current_id": "tech_lasers_3", "progress": 1420.0, "progress_known": True, "started": "2276.04.01", "alternatives": ["Improved Deflectors", "Fusion Power"], "alternative_ids": ["tech_shields_2", "tech_fusion_power"], "recommendation": "Improved Deflectors", "reason": "It can help close the fleet power gap."},
                        "society": {"current": "Eco Simulation", "current_id": "tech_eco_simulation", "progress": 980.0, "progress_known": True, "started": "2276.08.01", "alternatives": ["Colonial Centralization", "Doctrine: Fleet Support"], "alternative_ids": ["tech_colonial_centralization", "tech_doctrine_navy_size_1"], "recommendation": "Doctrine: Fleet Support", "reason": "It can widen the empire's strategic options."},
                        "engineering": {"current": "Cruisers", "current_id": "tech_cruisers", "progress": 2150.0, "progress_known": True, "started": "2275.11.01", "alternatives": ["Alloy Foundries", "Ceramic Metal Armor"], "alternative_ids": ["tech_alloys_1", "tech_ship_armor_2"], "recommendation": "Alloy Foundries", "reason": "It supports minerals, industry or alloys."},
                    },
                },
                "ship_builds": {
                    "designs": [
                        {"id": 101, "name": "Aegis Gunship", "size": "Corvette", "size_key": "corvette", "role": "Gunship", "naval_usage": 1,
                         "components": ["Mass Driver 2", "Laser 2", "Armor 2", "Shield 2"],
                         "slots": [{"slot": "SMALL_GUN_01", "component": "SMALL_MASS_DRIVER_2"}, {"slot": "SMALL_GUN_02", "component": "SMALL_LASER_2"}, {"slot": "UTILITY_01", "component": "SMALL_ARMOR_2"}, {"slot": "UTILITY_02", "component": "SMALL_SHIELD_2"}],
                         "component_evidence": [], "design_check": {"auto_generated": False}},
                        {"id": 102, "name": "Vanguard Picket", "size": "Destroyer", "size_key": "destroyer", "role": "Screen", "naval_usage": 2,
                         "components": ["Flak Battery 2", "Mass Driver 2", "Armor 2"],
                         "slots": [{"slot": "PD_01", "component": "FLAK_BATTERY_2"}, {"slot": "SMALL_GUN_01", "component": "SMALL_MASS_DRIVER_2"}, {"slot": "UTILITY_01", "component": "MEDIUM_ARMOR_2"}],
                         "component_evidence": [], "design_check": {"auto_generated": False}},
                    ],
                    "fleets": [{"id": 501, "name": "1st Fleet", "power": 2850, "ship_count": 32, "classes": {"corvette": 24, "destroyer": 8}, "classes_complete": True, "design_counts": {"101": 24, "102": 8}, "size": 40, "planned_size": 50, "location": "Sol"}],
                    "class_usage": {"corvette": 24, "destroyer": 16}, "usage_status": "inferred_from_plans",
                    "recommendation": {"title": "Review Aegis Gunship for reinforcement", "design_id": 101, "quantity": "Check one order in game first", "reason": "This is an owned saved combat design and monthly alloy income is positive.", "caveat": "Verify unlocked components, naval capacity, upkeep, counters and the ship's in-game cost before committing."},
                    "policies": {"fleet_doctrine": "battle_line", "weapon_preference": "weapon_preference_kinetic", "defense_preference": "defense_preference_balanced"},
                    "policy_details": [
                        {"key": "fleet_doctrine", "selected_id": "battle_line", "policy_label": "Fleet Doctrine", "selected_label": "Battle Line", "status": "unverified"},
                        {"key": "weapon_preference", "selected_id": "weapon_preference_kinetic", "policy_label": "Weapon Preference", "selected_label": "Kinetic", "status": "unverified"},
                        {"key": "defense_preference", "selected_id": "defense_preference_balanced", "policy_label": "Defense Preference", "selected_label": "Balanced", "status": "unverified"},
                    ],
                },
            },
        },
        "nomads-452": {
            "label": "Nomads Arkship Fleet (4.5.2 + Nomads)",
            "description": "Mobile Arkship empire showing Waystation/Arkship policies and Nomad fleet playbook.",
            "default_dlcs": ["Nomads", "First Contact Story Pack"],
            "snapshot": {
                "path": "demo/nomads-2264.sav", "filename": "autosave_2264.06.01.sav", "modified": 1760000100.0,
                "version": "Cygnus v4.5.2", "date": "2264.06.01", "empire": "Starfarer Armada",
                "campaign": {
                    "id": "demo452nom000002", "player_country_id": 0,
                    "save_version": "Cygnus v4.5.2", "save_date": "2264.06.01",
                    "required_dlcs": ["Nomads", "First Contact Story Pack"],
                    "mods": [],
                    "installed": {"version": None, "checksum": None, "version_match": "unknown",
                                  "playset_mods": None, "mod_match": "unknown"},
                },
                "player": {
                    "id": 0, "military": 3600, "economy": 1150, "technology": 880,
                    "naval_used": 62, "naval_capacity": None, "starbase_used": 4, "starbase_capacity": 6,
                    "empire_size": 94, "colonies": 1,
                    "stock": {"energy": 1600.0, "minerals": 1200.0, "food": 480.0,
                              "consumer_goods": 340.0, "alloys": 1450.0, "unity": 2200.0,
                              "influence": 920.0, "trade": 520.0},
                    "net": {"energy": 35.0, "minerals": 48.0, "food": 12.0,
                            "consumer_goods": 9.0, "alloys": 42.0, "unity": 55.0,
                            "influence": 4.8, "trade": 28.0},
                    "stock_known": {k: True for k in ("energy", "minerals", "food", "consumer_goods", "alloys", "unity", "influence", "trade")},
                    "net_known": {k: True for k in ("energy", "minerals", "food", "consumer_goods", "alloys", "unity", "influence", "trade")},
                    "research": {"physics": 105.0, "society": 112.0, "engineering": 134.0},
                    "profile": {
                        "authority": "auth_nomad", "origin": "origin_nomads",
                        "civics": ["civic_wayfarers"], "ethics": ["ethic_xenophile", "ethic_militarist"],
                        "traditions": ["tr_discovery_adopt"], "ascension_perks": [],
                        "is_hive": False, "is_machine": False, "is_gestalt": False,
                        "is_megacorp": False, "is_nomad": True, "is_wilderness": False,
                        "shipset_kind": "mechanical", "uses_consumer_goods": True,
                        "uses_food": True, "ideology_active": None,
                    },
                },
                "contacts": [],
                "policies": {
                    "fleet_doctrine": "ambush",
                    "weapon_preference": "weapon_preference_explosive",
                    "arkship_weapon_preference": "arkship_weapon_preference_explosive",
                    "waystation_defense_preference": "waystation_defense_preference_armor",
                },
                "flag": {"icon_category": "domination", "icon_file": "domination_1.dds", "background_file": "00_solid.dds", "colors": ["teal", "black", "null"]},
                "planets": [],
                "technology": {
                    "researched_count": 29, "researched_status": "complete",
                    "researched": {"tech_corvettes": 1, "tech_thrusters_2": 1},
                    "branches": {
                        "physics": {"current": "Tachyon Sensors", "current_id": "tech_sensors_3", "progress": 720.0, "progress_known": True, "started": "2263.10.01", "alternatives": ["Hyperlane Breach Points"], "alternative_ids": ["tech_hyperlane_breach"], "recommendation": "Hyperlane Breach Points", "reason": "Compare its in-game effect with your current goal."},
                        "society": {"current": "Operational Reserves", "current_id": "tech_operational_reserves", "progress": 840.0, "progress_known": True, "started": "2263.07.01", "alternatives": ["Naval Contractors"], "alternative_ids": ["tech_doctrine_navy_size_2"], "recommendation": "Naval Contractors", "reason": "It can widen the empire's strategic options."},
                        "engineering": {"current": "Plasma Thrusters", "current_id": "tech_thrusters_3", "progress": 1120.0, "progress_known": True, "started": "2263.04.01", "alternatives": ["Arkship Mastery"], "alternative_ids": ["tech_arkship_mastery"], "recommendation": "Arkship Mastery", "reason": "It supports Nomad fleet mobility or Arkship progression."},
                    },
                },
                "ship_builds": {
                    "designs": [
                        {"id": 201, "name": "Horizon Arkship", "size": "Arkship", "size_key": "arkship", "role": "Capital", "naval_usage": 16,
                         "components": ["Swarmer Missiles", "Armor 3", "Shield 2"],
                         "slots": [{"slot": "LARGE_GUN_01", "component": "SWARMER_MISSILES_2"}, {"slot": "UTILITY_01", "component": "LARGE_ARMOR_3"}],
                         "component_evidence": [], "design_check": {"auto_generated": False}},
                    ],
                    "fleets": [{"id": 601, "name": "1st Nomad Armada", "power": 3600, "ship_count": 15, "classes": {"arkship": 1, "corvette": 14}, "classes_complete": True, "design_counts": {"201": 1}, "size": 30, "planned_size": 40, "location": "Vega"}],
                    "class_usage": {"arkship": 16, "corvette": 14}, "usage_status": "inferred_from_plans",
                    "recommendation": {"title": "Review Horizon Arkship for reinforcement", "design_id": 201, "quantity": "Check one order in game first", "reason": "Owned saved Nomad design with positive alloy income.", "caveat": "Confirm Tier III Military Arkship limit (one per fleet) and Waystation upkeep in game."},
                    "policies": {"fleet_doctrine": "ambush", "arkship_weapon_preference": "arkship_weapon_preference_explosive", "waystation_defense_preference": "waystation_defense_preference_armor"},
                    "policy_details": [
                        {"key": "fleet_doctrine", "selected_id": "ambush", "policy_label": "Fleet Doctrine", "selected_label": "Ambush", "status": "unverified"},
                        {"key": "arkship_weapon_preference", "selected_id": "arkship_weapon_preference_explosive", "policy_label": "Arkship Weapon Preference", "selected_label": "Explosive", "status": "unverified"},
                        {"key": "waystation_defense_preference", "selected_id": "waystation_defense_preference_armor", "policy_label": "Waystation Defense Preference", "selected_label": "Armor Priority", "status": "unverified"},
                    ],
                },
            },
        },
        "willpower-460": {
            "label": "Willpower Ideologies (4.6 Corona Borealis)",
            "description": "4.6 save demonstrating Willpower Ideology upkeep alert, Galactic Administration priority, and automatic 4.5 playbook recheck gate.",
            "default_dlcs": ["Willpower", "Overlord", "BioGenesis"],
            "snapshot": {
                "path": "demo/willpower-2285.sav", "filename": "autosave_2285.01.01.sav", "modified": 1760000200.0,
                "version": "Corona Borealis v4.6.0", "date": "2285.01.01", "empire": "Covenant of the Dawn",
                "campaign": {
                    "id": "demo460wil000003", "player_country_id": 0,
                    "save_version": "Corona Borealis v4.6.0", "save_date": "2285.01.01",
                    "required_dlcs": ["Willpower", "Overlord", "BioGenesis"],
                    "mods": [],
                    "installed": {"version": None, "checksum": None, "version_match": "unknown",
                                  "playset_mods": None, "mod_match": "unknown"},
                },
                "player": {
                    "id": 0, "military": 4900, "economy": 2100, "technology": 1540,
                    "naval_used": 76, "naval_capacity": None, "starbase_used": 8, "starbase_capacity": 9,
                    "empire_size": 214, "colonies": 5,
                    "stock": {"energy": 3100.0, "minerals": 2400.0, "food": 1950.0,
                              "consumer_goods": 850.0, "alloys": 1700.0, "unity": 4200.0,
                              "influence": 210.0, "trade": 980.0},
                    "net": {"energy": 68.0, "minerals": 110.0, "food": 54.0,
                            "consumer_goods": 24.0, "alloys": 58.0, "unity": 142.0,
                            "influence": 1.1, "trade": 42.0},
                    "stock_known": {k: True for k in ("energy", "minerals", "food", "consumer_goods", "alloys", "unity", "influence", "trade")},
                    "net_known": {k: True for k in ("energy", "minerals", "food", "consumer_goods", "alloys", "unity", "influence", "trade")},
                    "research": {"physics": 195.0, "society": 230.0, "engineering": 182.0},
                    "profile": {
                        "authority": "auth_oligarchic", "origin": "origin_golden_generation",
                        "civics": ["civic_path_of_the_self"], "ethics": ["ethic_fanatic_spiritualist", "ethic_egalitarian"],
                        "traditions": ["tr_harmony_adopt", "tr_statecraft_adopt"], "ascension_perks": ["ap_one_vision"],
                        "is_hive": False, "is_machine": False, "is_gestalt": False,
                        "is_megacorp": False, "is_nomad": False, "is_wilderness": False,
                        "shipset_kind": "biological", "uses_consumer_goods": True,
                        "uses_food": True, "ideology_active": True,
                    },
                },
                "contacts": [],
                "policies": {"fleet_doctrine": "strike_wing", "weapon_preference": "weapon_preference_energy"},
                "flag": {"icon_category": "ornate", "icon_file": "flag_ornate_1.dds", "background_file": "00_solid.dds", "colors": ["gold", "purple", "null"]},
                "planets": [
                    {
                        "id": 1, "planet_id": 11, "name": "Sanctuary", "system": "Aurelia", "class": "Gaia", "class_key": "pc_gaia",
                        "size": 20, "size_known": True, "designation": "Empire Capital", "designation_key": "col_capital",
                        "stability": 82.0, "crime": 0.0, "pops": 55.0, "free_housing": 8.0, "free_amenities": 14.0,
                        "jobs": [], "districts": 12, "buildings": 7, "produces": {"unity": 95.0}, "upkeep": {"consumer_goods": 18.0}, "profits": {"unity": 95.0},
                        "recommendation": {"level": "stable", "title": "No urgent build", "action": "Let the colony grow and revisit when a job, housing or amenity warning appears.", "reason": "Housing, amenities and stability are currently comfortable."},
                        "job_advice": [],
                    }
                ],
                "technology": {
                    "researched_count": 48, "researched_status": "complete",
                    "researched": {"tech_corvettes": 1, "tech_colonial_centralization": 1},
                    "branches": {
                        "physics": {"current": "Zero Point Power", "current_id": "tech_zero_point_power", "progress": 1900.0, "progress_known": True, "started": "2284.02.01", "alternatives": ["Hyper Shields"], "alternative_ids": ["tech_shields_4"], "recommendation": "Hyper Shields", "reason": "Compare its in-game effect with your current goal."},
                        "society": {"current": "Galactic Administration", "current_id": "tech_galactic_administration", "progress": 1650.0, "progress_known": True, "started": "2284.05.01", "alternatives": ["Galactic Bureaucracy"], "alternative_ids": ["tech_galactic_bureaucracy"], "recommendation": "Galactic Administration", "reason": "In 4.6+, Galactic Administration is reported to unlock the 5th Council position; verify in game."},
                        "engineering": {"current": "Stingers", "current_id": "tech_stingers", "progress": 2400.0, "progress_known": True, "started": "2283.11.01", "alternatives": ["Citadels"], "alternative_ids": ["tech_starbase_5"], "recommendation": "Citadels", "reason": "Compare its in-game effect with your current goal."},
                    },
                },
                "ship_builds": {
                    "designs": [
                        {"id": 301, "name": "Solar Mauler", "size": "Mauler", "size_key": "mauler", "role": "Brawler", "naval_usage": 1,
                         "components": ["Plasma Thrower", "Organic Armor"],
                         "slots": [{"slot": "SMALL_GUN_01", "component": "SMALL_PLASMA_2"}, {"slot": "UTILITY_01", "component": "SMALL_ARMOR_3"}],
                         "component_evidence": [], "design_check": {"auto_generated": False}},
                    ],
                    "fleets": [{"id": 701, "name": "1st Bio-Wing", "power": 4900, "ship_count": 30, "classes": {"mauler": 30}, "classes_complete": True, "design_counts": {"301": 30}, "size": 30, "planned_size": 40, "location": "Aurelia"}],
                    "class_usage": {"mauler": 30}, "usage_status": "inferred_from_plans",
                    "recommendation": {"title": "Review Solar Mauler for reinforcement", "design_id": 301, "quantity": "Check one order in game first", "reason": "Owned BioGenesis design with positive alloy and food balances.", "caveat": "Confirm both Food and Alloy upkeep and 4.6 multiplicative Regen Speed in Ship Designer."},
                    "policies": {"fleet_doctrine": "strike_wing", "weapon_preference": "weapon_preference_energy"},
                    "policy_details": [{"key": "fleet_doctrine", "selected_id": "strike_wing", "policy_label": "Fleet Doctrine", "selected_label": "Strike Wing", "status": "unverified"}],
                },
            },
        },
    }


def list_demo_presets() -> list[dict]:
    return [
        {"id": key, "label": item["label"], "description": item["description"],
         "default_dlcs": item["default_dlcs"]}
        for key, item in _demo_presets().items()
    ]


def list_selectable_dlcs() -> list[dict]:
    return [
        {"id": entry["id"], "name": entry["name"], "category": entry["category"]}
        for entry in DLC_CATALOG
        if entry["category"] != "base_included"
    ]


def build_demo_state(preset_id: str = "une-452", *,
                     enabled_dlc_ids: list[str] | None = None,
                     spoilers_active: bool = False) -> dict:
    presets = _demo_presets()
    preset = presets.get(preset_id) or presets["une-452"]
    snapshot = copy.deepcopy(preset["snapshot"])
    version = snapshot["campaign"]["save_version"]
    if enabled_dlc_ids is not None:
        labels = [dlc_display_name(normalize_dlc_id(item)) for item in enabled_dlc_ids]
        snapshot["campaign"]["required_dlcs"] = labels
    snapshot["campaign"]["dlc_summary"] = active_dlcs(snapshot["campaign"]["required_dlcs"], version)
    # Build two synthetic earlier trend points with lower metrics and tech progress.
    hist_early = copy.deepcopy(snapshot)
    hist_early["date"] = "2270.01.01" if preset_id == "une-452" else "2280.01.01" if preset_id == "willpower-460" else "2258.01.01"
    hist_early["player"]["military"] = int(snapshot["player"]["military"] * 0.65)
    hist_early["player"]["economy"] = int(snapshot["player"]["economy"] * 0.72)
    hist_early["player"]["technology"] = int(snapshot["player"]["technology"] * 0.68)
    for branch in hist_early.get("technology", {}).get("branches", {}).values():
        if isinstance(branch.get("progress"), (int, float)):
            branch["progress"] = round(branch["progress"] * 0.4, 1)
    hist_mid = copy.deepcopy(snapshot)
    hist_mid["date"] = "2274.01.01" if preset_id == "une-452" else "2283.01.01" if preset_id == "willpower-460" else "2261.01.01"
    hist_mid["player"]["military"] = int(snapshot["player"]["military"] * 0.84)
    hist_mid["player"]["economy"] = int(snapshot["player"]["economy"] * 0.88)
    hist_mid["player"]["technology"] = int(snapshot["player"]["technology"] * 0.85)
    for branch in hist_mid.get("technology", {}).get("branches", {}).values():
        if isinstance(branch.get("progress"), (int, float)):
            branch["progress"] = round(branch["progress"] * 0.72, 1)
    chain = [hist_early, hist_mid, snapshot]
    advice = make_advice(snapshot, chain, {})
    return {
        "status": "ready",
        "demo_preset": preset_id if preset_id in presets else "une-452",
        "snapshot": public_snapshot(snapshot, spoilers_active=spoilers_active),
        "history": [public_history_snapshot(item, spoilers_active=spoilers_active) for item in chain],
        "advice": advice,
        "error": None,
        "updated_at": time.time(),
        "app_version": APP_VERSION,
        "web_mode": True,
    }


def ask_builtin(question: str, snapshot: dict, advice: dict | None = None) -> dict:
    answer = answer_question(question, snapshot, advice or {})
    return {"answer": answer, "source": "Built-in guide (in-browser)", "image_analyzed": False}


def generate_static_demo_bundle() -> dict:
    """Precompute static demo payloads for instant <100ms load before Pyodide warms up."""
    presets = list_demo_presets()
    return {
        "app_version": APP_VERSION,
        "presets": presets,
        "dlcs": list_selectable_dlcs(),
        "states": {item["id"]: build_demo_state(item["id"]) for item in presets},
    }


if __name__ == "__main__":
    print(json.dumps(generate_static_demo_bundle(), indent=2))
