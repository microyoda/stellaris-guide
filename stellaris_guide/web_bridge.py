"""Pure-stdlib entry point for client-side browser execution (Pyodide Web Worker).

Reuses the exact same save parser, DLC registry, strategy planner, playbooks,
and built-in chat guide as the desktop application with zero server uploads
and zero Windows/Pillow/local-filesystem dependencies.
"""

from __future__ import annotations

import copy
from functools import lru_cache
import json
from pathlib import Path
import time

from .advice import answer_question, make_advice
from .dlcs import DLC_CATALOG, active_dlcs, dlc_display_name, dlc_status_list, normalize_dlc_id
from .saves import parse_save_bytes, pretty_tech

APP_VERSION = "1.7.0-web"
TECH_GRAPH_FILE = Path(__file__).with_name("tech_graph.json")
WEB_MAX_GAMESTATE_BYTES = 120_000_000
_LAST_RAW_CHAIN: list[dict] = []
_LAST_ADVICE: dict | None = None
_LAST_PLAN: dict = {}


@lru_cache(maxsize=2)
def load_tech_graph(path: Path = TECH_GRAPH_FILE) -> tuple[dict, dict[int, int], bool, str]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}, {}, True, "unknown"
    raw_rules = data.get("rules") if isinstance(data, dict) else {}
    raw_gates = data.get("gates") if isinstance(data, dict) else {}
    partial = bool(data.get("partial", True)) if isinstance(data, dict) else True
    release = str(data.get("baseline_release") or "unknown") if isinstance(data, dict) else "unknown"
    rules = {k: v for k, v in raw_rules.items() if isinstance(k, str) and isinstance(v, dict)}
    gates = {int(k): int(v) for k, v in raw_gates.items() if str(k).isdigit() and isinstance(v, int)}
    return rules, gates, partial, release


def web_research_overview(snapshot: dict) -> dict:
    """Provide research labels and Tier 2 gate counts from the bundled web tech graph."""
    rules, thresholds, partial, _ = load_tech_graph()
    technology = snapshot.get("technology") or {}
    if not rules or technology.get("researched_status") != "complete":
        return {"status": "unverified", "labels": {}, "gates": {}}
    researched = set(technology.get("researched") or {})
    mods = bool((snapshot.get("campaign") or {}).get("mods"))
    labels: dict[str, str] = {}
    gates: dict[str, dict] = {}
    for area, branch in (technology.get("branches") or {}).items():
        relevant = [branch.get("current_id"), *(branch.get("alternative_ids") or [])]
        labels.update({key: rules[key]["name"] for key in relevant if key in rules})
        count = sum(key in researched and rule.get("area") == area and rule.get("tier") == 1
                    for key, rule in rules.items())
        required = thresholds.get(2)
        completed = sorted(rules[key]["name"] for key in researched
                           if key in rules and rules[key].get("area") == area and rules[key].get("tier") == 1)
        on_cards = [{"id": key, "name": rules[key]["name"]}
                    for key in branch.get("alternative_ids", [])
                    if key in rules and rules[key].get("tier") == 1]
        gate_status = (
            "unverified" if mods or required is None else
            "open" if count >= required else
            "unverified" if partial else "closed"
        )
        gates[area] = {
            "tier": 2, "count": count, "required": required,
            "display_count": count,
            "status": gate_status,
            "completed": completed, "on_cards": on_cards,
        }
    return {"status": "limited", "labels": labels, "gates": gates}


def web_route_targets(snapshot: dict) -> list[dict]:
    rules, _, _, _ = load_tech_graph()
    technology = snapshot.get("technology") or {}
    researched = set(technology.get("researched") or {})
    branches = technology.get("branches") or {}
    current = {b.get("current_id") for b in branches.values()}
    options = {k for b in branches.values() for k in (b.get("alternative_ids") or [])}
    return [
        {
            "id": key, "name": rule["name"], "area": rule.get("area", ""),
            "tier": rule.get("tier"),
            "state": ("researched" if key in researched else "researching" if key in current
                      else "saved_option" if key in options else "unmet"),
            "required_dlc": rule.get("required_dlc") or [],
        }
        for key, rule in sorted(rules.items(), key=lambda entry: (entry[1]["name"], entry[0]))
    ]


def web_route_for_target(snapshot: dict, target: str) -> dict:
    """Compute a cautious, DLC-aware technology route from the bundled web graph."""
    rules, gates, partial, graph_release = load_tech_graph()
    campaign = snapshot.get("campaign") or {}
    technology = snapshot.get("technology") or {}
    researched = set(technology.get("researched") or {})
    branches = technology.get("branches") or {}
    current = {b.get("current_id") for b in branches.values()}
    options = {k for b in branches.values() for k in (b.get("alternative_ids") or [])}
    save_version = campaign.get("save_version") or snapshot.get("version")
    saved_dlcs = campaign.get("required_dlcs")
    mods = bool(campaign.get("mods"))

    def state_of(key: str) -> str:
        return ("researched" if key in researched else "researching" if key in current
                else "saved_option" if key in options else "unmet")

    if target not in rules:
        return {
            "target_id": target, "name": pretty_tech(target), "status": "unknown",
            "reason": "This technology is not in the bundled web core graph. Verify its prerequisites in game or use the desktop app with your installed Stellaris folder.",
            "area": "", "tier": None, "state": state_of(target),
            "steps": [{"id": target, "name": pretty_tech(target), "state": state_of(target), "area": "", "tier": None}],
            "one_of": [], "next_unlocks": [], "dlc": [],
            "tier_gate": {"status": "unknown"},
            "next_check": "Search another milestone below or verify this technology in game.",
        }

    steps, visited = [], set()

    def walk(key: str, depth: int = 0) -> None:
        if key in visited or depth > 8 or len(steps) >= 40:
            return
        visited.add(key)
        rule = rules.get(key)
        if rule and key not in researched:
            for parent in rule.get("prerequisites") or []:
                walk(parent, depth + 1)
        steps.append({
            "id": key,
            "name": rule["name"] if rule else pretty_tech(key),
            "area": rule.get("area", "") if rule else "",
            "tier": rule.get("tier") if rule else None,
            "state": state_of(key),
            "dlc": dlc_status_list(rule.get("required_dlc") or [], saved_dlcs, save_version) if rule else [],
        })

    walk(target)
    rule = rules[target]
    one_of = []
    for item in steps:
        if item["id"] in researched:
            continue
        owner = rules.get(item["id"]) or {}
        for group in owner.get("one_of") or []:
            one_of.append({
                "for_id": item["id"], "for_name": owner.get("name", pretty_tech(item["id"])),
                "options": [
                    {
                        "id": opt, "name": rules[opt]["name"] if opt in rules else pretty_tech(opt),
                        "state": state_of(opt),
                        "dlc": dlc_status_list((rules.get(opt) or {}).get("required_dlc") or [], saved_dlcs, save_version),
                    }
                    for opt in group
                ],
            })

    next_unlocks = []
    for key, candidate in sorted(rules.items(), key=lambda e: (e[1].get("tier") or 0, e[1]["name"])):
        direct = target in (candidate.get("prerequisites") or [])
        alt = any(target in group for group in (candidate.get("one_of") or []))
        if direct or alt:
            next_unlocks.append({
                "id": key, "name": candidate["name"], "area": candidate.get("area", ""),
                "tier": candidate.get("tier"), "relation": "direct" if direct else "one_of",
                "state": state_of(key),
                "dlc": dlc_status_list(candidate.get("required_dlc") or [], saved_dlcs, save_version),
            })

    req_dlc = list(dict.fromkeys(
        d for step in steps for d in (rules.get(step["id"]) or {}).get("required_dlc", [])
    ))
    dlc_info = dlc_status_list(req_dlc, saved_dlcs, save_version)
    dlc_missing = any(item["status"] != "present" for item in dlc_info)

    tier = rule.get("tier")
    threshold = gates.get(tier) if isinstance(tier, int) and tier > 0 else None
    prior_count = sum(
        k in researched and r.get("area") == rule.get("area") and r.get("tier") == tier - 1
        for k, r in rules.items()
    ) if isinstance(tier, int) and tier > 0 else 0
    tier_status = ("unknown" if threshold is None or mods else
                   "met" if prior_count >= threshold else
                   "unknown" if partial else "not_met")
    has_unmet_one_of = any(
        not any(opt["state"] == "researched" for opt in group["options"])
        for group in one_of
    )

    if dlc_missing:
        next_check = "A required DLC is missing or unverified in this save; check DLC requirements in game."
    elif target in researched:
        next_check = "Already researched in this save. Explore downstream technologies below."
    elif target in current:
        next_check = "Currently being researched in this save."
    elif target in options:
        next_check = "Available on your saved research cards right now."
    elif any(s["state"] == "unmet" for s in steps[:-1]):
        next_check = "Work through the unmet prerequisite(s) above first; card draws are not guaranteed."
    elif has_unmet_one_of:
        next_check = "Research one option from each unmet alternative prerequisite group below; card draws are not guaranteed."
    else:
        next_check = "Core prerequisites appear met in this save. Check tier gate and research draws in game."

    return {
        "target_id": target, "name": rule["name"], "area": rule.get("area", ""),
        "tier": tier, "state": state_of(target),
        "status": "limited",
        "reason": ("Save lists mods; exported base-game graph may differ." if mods
                   else f"Derived from exported {graph_release} structural tech graph ({len(rules)} techs); verify draw weights and mod changes in game."
                   if not partial
                   else f"Derived from bundled core {graph_release} graph; verify exact draw weights and mod/patch changes in game."),
        "steps": steps, "one_of": one_of, "next_unlocks": next_unlocks,
        "dlc": dlc_info,
        "tier_gate": {"tier": tier, "required_previous_tier": threshold,
                      "researched_previous_tier": prior_count, "status": tier_status},
        "next_check": next_check,
    }


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
    snapshot.setdefault("technology", {})["overview"] = web_research_overview(snapshot)
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
                        "physics": {"current": "Tachyon Sensors", "current_id": "tech_sensors_4", "progress": 720.0, "progress_known": True, "started": "2263.10.01", "alternatives": ["Hyperlane Breach Points"], "alternative_ids": ["tech_hyper_drive_2"], "recommendation": "Hyperlane Breach Points", "reason": "Compare its in-game effect with your current goal."},
                        "society": {"current": "Operational Reserves", "current_id": "tech_doctrine_navy_size_1", "progress": 840.0, "progress_known": True, "started": "2263.07.01", "alternatives": ["Naval Contractors"], "alternative_ids": ["tech_doctrine_navy_size_2"], "recommendation": "Naval Contractors", "reason": "It can widen the empire's strategic options."},
                        "engineering": {"current": "Plasma Thrusters", "current_id": "tech_thrusters_3", "progress": 1120.0, "progress_known": True, "started": "2263.04.01", "alternatives": ["Arkship Tier 3"], "alternative_ids": ["tech_arkship_tier_3"], "recommendation": "Arkship Tier 3", "reason": "It supports Nomad fleet mobility or Arkship progression."},
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
    snapshot.setdefault("technology", {})["overview"] = web_research_overview(snapshot)
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
