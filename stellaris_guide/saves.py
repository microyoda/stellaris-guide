"""Defensive extractor for the Cygnus fields used by Stellaris Guide.

Stellaris saves are ZIP files containing Clausewitz text. This extracts only
dashboard data and tolerates missing fields so mods do not block the whole UI.
"""

from __future__ import annotations

import io
import os
import hashlib
import json
import math
import re
import zipfile
from collections import defaultdict
from pathlib import Path

from .dlcs import active_dlcs, parse_release_tuple

SAVE_ROOT = Path.home() / "Documents" / "Paradox Interactive" / "Stellaris" / "save games"
RESOURCES = ("energy", "minerals", "food", "consumer_goods", "alloys", "unity", "influence", "trade")
NUMBER = re.compile(r"(?<![A-Za-z_])([a-z_]+)=(-?\d+(?:\.\d+)?)")
MAX_META_BYTES = 1_000_000
MAX_GAMESTATE_BYTES = 350_000_000
MAX_LABEL_COUNT = 128
MAX_LABEL_LENGTH = 160
MAX_LABEL_TOTAL = 8_000


def save_list(meta: str, key: str) -> list[str] | None:
    """Return quoted save labels; None means the metadata omitted the list."""
    section = block(meta, key)
    if not section:
        return None
    labels = re.findall(r'"([^"\n]+)"', section)
    if (len(labels) > MAX_LABEL_COUNT or any(len(label) > MAX_LABEL_LENGTH for label in labels)
            or sum(map(len, labels)) > MAX_LABEL_TOTAL):
        return None
    return labels


def game_release(value: str | None) -> str | None:
    match = re.search(r"(?<!\d)(\d+\.\d+\.\d+)\b", value or "")
    return match.group(1) if match else None


def installed_context(game_dir: str, save_path: Path, save_version: str,
                      save_mods: list[str] | None) -> dict:
    """Report local ruleset evidence without treating a name match as mod verification."""
    result = {"version": None, "checksum": None, "version_match": "unknown",
              "playset_mods": None, "mod_match": "unknown"}
    if game_dir:
        settings = Path(game_dir) / "launcher-settings.json"
        try:
            if (settings.resolve().is_relative_to(Path(game_dir).resolve())
                    and settings.stat().st_size <= 1_000_000):
                data = json.loads(settings.read_text(encoding="utf-8-sig"))
                installed = str(data.get("version", ""))
                result["version"] = installed or None
                checksum = re.search(r"\(([A-Za-z0-9]{4})\)\s*$", installed)
                result["checksum"] = checksum.group(1) if checksum else None
                saved_release, installed_release = game_release(save_version), game_release(installed)
                if saved_release and installed_release:
                    result["version_match"] = "match" if saved_release == installed_release else "mismatch"
        except (OSError, ValueError, TypeError, AttributeError):
            pass

    # Custom save folders do not prove which launcher playset produced the save.
    if save_path.parent.parent.name.lower() != "save games":
        return result
    user_dir = save_path.parent.parent.parent
    try:
        load_path = user_dir / "dlc_load.json"
        if (not load_path.resolve().is_relative_to(user_dir.resolve())
                or load_path.stat().st_size > 1_000_000):
            return result
        load = json.loads(load_path.read_text(encoding="utf-8-sig"))
        if not isinstance(load, dict) or "enabled_mods" not in load:
            return result
        descriptors = load["enabled_mods"]
        if not isinstance(descriptors, list) or len(descriptors) > 200:
            return result
        names = []
        for descriptor in descriptors:
            if not isinstance(descriptor, str):
                return result
            candidate = (user_dir / descriptor).resolve()
            if not candidate.is_relative_to(user_dir.resolve()) or candidate.stat().st_size > 128_000:
                return result
            name = scalar(candidate.read_text(encoding="utf-8-sig"), "name")
            if not name or len(name) > MAX_LABEL_LENGTH:
                return result
            names.append(name)
            if sum(map(len, names)) > MAX_LABEL_TOTAL:
                return result
        result["playset_mods"] = names
        if save_mods is not None:
            result["mod_match"] = ("names_only" if names == save_mods else "mismatch")
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    return result


def researched_technologies(status: str) -> tuple[dict[str, int], str]:
    """Read completed techs; flag incomplete records rather than treating them as unmet."""
    if not status:
        return {}, "unknown"
    first_nested = re.search(r"(?m)^\s*[A-Za-z_]+\s*=\s*\{", status[1:])
    completed = status[1:1 + first_nested.start()] if first_nested else status
    levels = {}
    status_label = "complete"
    entries = list(re.finditer(r'(?<![A-Za-z_])technology\s*=\s*"([^"\n]+)"', completed))
    for index, entry in enumerate(entries):
        following = completed[entry.end():entries[index + 1].start() if index + 1 < len(entries)
                              else len(completed)]
        level = re.search(r'(?<![A-Za-z_])level\s*=\s*([^\s{}]+)', following)
        if not level or not level.group(1).isdigit() or int(level.group(1)) <= 0:
            status_label = "partial"
            continue
        key, value = entry.group(1), int(level.group(1))
        levels[key] = max(levels.get(key, 0), value)
    return levels, status_label


def matching_brace(text: str, opening: int) -> int:
    depth, quoted, escaped = 0, False, False
    for pos in range(opening, len(text)):
        char = text[pos]
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return pos + 1
    raise ValueError("An incomplete save section was found")


def block(text: str, key: str, *, top_level: bool = False) -> str:
    prefix = r"(?m)^" if top_level else r"(?<![A-Za-z_])"
    match = re.search(prefix + re.escape(key) + r"\s*=\s*\{", text)
    if not match:
        return ""
    opening = text.find("{", match.start(), match.end())
    return text[opening:matching_brace(text, opening)]


def scalar(text: str, key: str, default=None):
    match = re.search(r"(?<![A-Za-z_])" + re.escape(key) + r"\s*=\s*(\"[^\"]*\"|[^\s{}]+)", text)
    return match.group(1).strip('"') if match else default


def direct_scalar(text: str, key: str, tabs: int = 2, default=None):
    match = re.search(r"(?m)^\t{" + str(tabs) + r"}" + re.escape(key) + r"\s*=\s*(\"[^\"]*\"|[^\s{}]+)", text)
    return match.group(1).strip('"') if match else default


def numeric(text: str, key: str, default: float = 0.0) -> float:
    try:
        return float(scalar(text, key, default))
    except (TypeError, ValueError):
        return float(default)


def indexed_entries(section: str, tabs: int = 1):
    pattern = re.compile(r"(?m)^\t{" + str(tabs) + r"}(\d+)\s*=\s*\{")
    for match in pattern.finditer(section):
        opening = section.find("{", match.start(), match.end())
        yield int(match.group(1)), section[opening:matching_brace(section, opening)]


def country_entries(section: str):
    yield from indexed_entries(section, 1)


def resource_totals(text: str) -> dict[str, float]:
    totals: defaultdict[str, float] = defaultdict(float)
    for key, value in NUMBER.findall(text):
        if key in RESOURCES or key.endswith("_research"):
            totals[key] += float(value)
    return {key: round(value, 1) for key, value in totals.items()}


def display_token(value: str, *prefixes: str) -> str:
    token = value or ""
    for prefix in prefixes:
        token = token.removeprefix(prefix)
    return token.replace("_", " ").strip().title() or "Unknown"


def display_name(name: str, country_id: int | None = None) -> str:
    keys = re.findall(r'key="([^"]+)"', name or "")
    if keys:
        first = keys[0]
        if first == "NEW_COLONY_NAME_1":
            values = [key for key in keys[1:] if key.upper() != "NAME"]
            if values:
                base = display_token(values[-1], "NAME_")
                return f"{base} Prime"
        if first.startswith("STAR_NAME_"):
            values = [key for key in keys[1:] if key.upper() != "NAME"]
            if values:
                return display_token(values[-1], "NAME_")
        if first.endswith("_FORMAT"):
            values = [key for key in keys[1:] if key.lower() not in ("prefix", "suffix", "name", "adjective")]
            if values:
                joined = ""
                for value in values:
                    joined += value if not joined or joined.endswith(("-", "'")) else " " + value
                return joined.replace("_", " ").strip().title()
        for marker in ("_PLANET_", "_SHIP_"):
            if marker in first:
                return first.split(marker, 1)[1].replace("_", " ").title()
        if first.startswith("NAME_"):
            return first.removeprefix("NAME_").replace("_", " ").title()
    useful = [key for key in keys if key.lower() not in
              ("1", "2", "%adj%", "%adjective%", "adjective", "name", "prefix", "suffix")]
    if useful:
        parts = [re.sub(r"(?<=[a-z])(?=[A-Z])", " ", part.removeprefix("SPEC_"))
                 .replace("_planet", "").replace("_", " ") for part in useful[:3]]
        return " ".join(parts).title()
    key = scalar(name or "", "key", "")
    if key:
        return display_token(key, "EMPIRE_DESIGN_", "NAME_")
    return f"Empire {country_id}" if country_id is not None else "Unknown"


def parse_name(container: str, fallback: str) -> str:
    name_block = block(container, "name")
    if name_block:
        result = display_name(name_block)
        if result != "Unknown":
            return result
    raw = scalar(container, "name", "")
    return display_token(raw, "NAME_") if raw and raw != "name" else fallback


def player_empire_name(meta_name: str, player: str) -> str:
    """Prefer the actual country name over the campaign/save display name."""
    name_block = block(player, "name")
    key = scalar(name_block, "key", "")
    if key.startswith("EMPIRE_DESIGN_"):
        # Stellaris appends a number when another campaign uses the same preset
        # name (for example "United Nations of Earth 3"). That number identifies
        # the campaign folder, not the in-game nation.
        cleaned = re.sub(r"\s+\d+$", "", meta_name).strip()
        return cleaned or meta_name
    parsed = display_name(name_block)
    return parsed if parsed != "Unknown" else meta_name


def scaled_colony_value(value: float) -> float:
    return round(value / 100.0 if abs(value) >= 100 else value, 1)


def parse_job_summary(colony: str, job_records: dict[int, str]) -> list[dict]:
    """Read Cygnus workforce groups without treating each group as one pop."""
    summary: dict[str, dict] = {}
    for job_id in (int(value) for value in re.findall(r"\b\d+\b", block(colony, "pop_jobs"))):
        record = job_records.get(job_id, "")
        if not record:
            continue
        kind = scalar(record, "type", "unknown")
        filled_raw = numeric(record, "workforce", -1)
        maximum_raw = numeric(record, "max_workforce", -1)
        limit_raw = numeric(record, "workforce_limit", -1)
        if filled_raw < 0 and maximum_raw < 0:
            continue  # An unused special job placeholder.
        item = summary.setdefault(kind, {"type": kind, "filled": 0.0, "capacity": 0.0,
                                         "limit": 0.0, "capacity_known": False,
                                         "limit_known": False, "disabled": False})
        if filled_raw >= 0:
            item["filled"] += filled_raw / 100
        if maximum_raw >= 0:
            item["capacity"] += maximum_raw / 100
            item["capacity_known"] = True
        if limit_raw >= 0:
            item["limit"] += limit_raw / 100
            item["limit_known"] = True
    for item in summary.values():
        for key in ("filled", "capacity", "limit"):
            item[key] = round(item[key], 1)
        if not item["capacity_known"]:
            item["capacity"] = None
        if not item["limit_known"]:
            item["limit"] = None
        item["disabled"] = item["limit"] == 0 and (item["capacity"] or 0) > 0
    return sorted(summary.values(), key=lambda item: (-item["filled"], item["type"]))


def parse_known_intel(player: str) -> dict[int, float]:
    """Intel recorded for the player; exact foreign power still needs separate consent."""
    manager = block(player, "intel_manager")
    entries = block(manager, "intel")
    return {int(country_id): round(float(value), 1)
            for country_id, value in re.findall(
                r"\{\s*(\d+)\s*\{\s*intel=([-+]?\d+(?:\.\d+)?)", entries)}


def parse_policies(player: str) -> dict[str, str]:
    """Read the selected options, not the empire's assumed starting defaults."""
    return dict(re.findall(r'policy="([a-z0-9_]+)"\s+selected="([a-z0-9_]+)"', player))


MILITARY_POLICY_KEYS = (
    "fleet_doctrine", "weapon_preference", "defense_preference",
    "starbase_weapon_preference", "starbase_defense_preference",
    "platform_weapon_preference", "platform_defense_preference",
    "defense_platform_protocols",
    "arkship_weapon_preference", "waystation_defense_preference",
)


def is_military_policy_key(key: str) -> bool:
    return key in MILITARY_POLICY_KEYS or key.startswith(
        ("fleet_", "starbase_", "platform_", "weapon_preference_", "defense_preference_",
         "defense_platform_", "arkship_", "waystation_"))


def military_policy_details(policies: dict[str, str], game_dir: str,
                            version_match: str) -> list[dict]:
    """Resolve saved 4.5.2 IDs only against the verified installed base game."""
    keys = [key for key in MILITARY_POLICY_KEYS if key in policies]
    keys.extend(sorted(key for key in policies if is_military_policy_key(key) and key not in keys))
    selected = [(key, policies[key]) for key in keys]
    if not selected:
        return []
    output = [{"key": key, "selected_id": value, "policy_label": key,
               "selected_label": value, "status": "unverified"} for key, value in selected]
    if version_match != "match" or not game_dir:
        return output
    root = Path(game_dir).resolve()
    paths = [root / "common" / "policies" / "06_policies_fleets_and_starbases.txt",
             root / "localisation" / "english" / "main_3_l_english.yml",
             root / "localisation" / "english" / "defense_platform_policies_l_english.yml"]
    try:
        if any(not path.resolve().is_relative_to(root) or path.stat().st_size > 1_000_000
               for path in paths):
            return output
        definitions = paths[0].read_text(encoding="utf-8-sig")
        localization = "\n".join(path.read_text(encoding="utf-8-sig") for path in paths[1:])
    except (OSError, ValueError):
        return output
    labels = dict(re.findall(r'^\s*([a-zA-Z0-9_]+):\s*(?:\d+\s*)?"([^"\n]{1,160})"',
                             localization, re.MULTILINE))
    for item in output:
        option_ids = set(re.findall(r'(?m)^\s*name\s*=\s*"([a-z0-9_]+)"',
                                    block(definitions, item["key"], top_level=True)))
        policy_label = labels.get(f"policy_{item['key']}")
        option_label = labels.get(item["selected_id"])
        if (item["selected_id"] in option_ids and policy_label and option_label
                and "$" not in policy_label + option_label):
            item.update(policy_label=policy_label, selected_label=option_label,
                        status="verified_base_game")
        elif not option_ids:
            item["status"] = "missing_definition"
        elif item["selected_id"] not in option_ids:
            item["status"] = "unknown_option"
        else:
            item["status"] = "missing_label"
    return output


def parse_flag(player: str) -> dict:
    raw = block(player, "flag")
    icon, background = block(raw, "icon"), block(raw, "background")
    colors = re.findall(r'"([a-z_]+)"', block(raw, "colors"))
    return {
        "icon_category": scalar(icon, "category", ""),
        "icon_file": scalar(icon, "file", ""),
        "background_file": scalar(background, "file", ""),
        "colors": colors[:3],
    }


def parse_empire_profile(player: str, policies: dict[str, str],
                         designs: list[dict] | None = None) -> dict:
    """Read empire authority, ethics, civics, origin, traditions, and shipset cues."""
    government = block(player, "government")
    authority = scalar(government, "authority", "") or ""
    origin = scalar(government, "origin", "") or ""
    civics = re.findall(r'"([a-z0-9_]+)"', block(government, "civics"))[:16]
    ethics = re.findall(r'\bethic\s*=\s*"([a-z0-9_]+)"', block(player, "ethos"))[:8]
    traditions = re.findall(r'"(tr_[a-z0-9_]+)"', block(player, "traditions"))[:80]
    ascension_perks = re.findall(r'"(ap_[a-z0-9_]+)"', block(player, "ascension_perks"))[:16]
    is_hive = authority == "auth_hive_mind"
    is_machine = authority == "auth_machine_intelligence"
    is_gestalt = is_hive or is_machine or "ethic_gestalt_consciousness" in ethics
    is_megacorp = authority == "auth_corporate"
    design_sizes = {str(item.get("size_key") or "").casefold() for item in (designs or [])}
    is_nomad = bool(
        "nomad" in authority.casefold()
        or "nomad" in origin.casefold()
        or direct_scalar(player, "is_nomadic", default="") == "yes"
        or any(key.startswith(("arkship_", "waystation_")) for key in policies)
        or any("arkship" in size for size in design_sizes)
    )
    is_wilderness = "wilderness" in origin.casefold()
    graphical_culture = (direct_scalar(player, "graphical_culture", default="") or "").casefold()
    bio_hulls = {"mauler", "weaver", "harbinger", "stinger"}
    if design_sizes & bio_hulls or "bio" in graphical_culture:
        shipset_kind = "biological"
    elif any("fauna" in size or "amoeba" in size or "tiyanki" in size for size in design_sizes):
        shipset_kind = "fauna"
    else:
        shipset_kind = "mechanical"
    civic_set = set(civics)
    uses_consumer_goods = (not is_gestalt) or bool(
        civic_set & {"civic_machine_servitor", "civic_machine_obsessional_directive"}
    )
    uses_food = (not is_machine) or shipset_kind == "biological" or bool(
        civic_set & {"civic_machine_servitor", "civic_machine_assimilator", "civic_machine_catalytic"}
    )
    ideology_block = block(player, "ideology")
    ideology_has_body = bool(ideology_block and ideology_block.strip("{} \t\r\n"))
    ideology_scalar = direct_scalar(player, "ideology", default=None)
    ideology_active = True if (
        ideology_has_body
        or (ideology_scalar is not None and ideology_scalar.casefold() not in ("", "0", "none", "no", "null"))
    ) else None
    return {
        "authority": authority or None,
        "origin": origin or None,
        "civics": civics,
        "ethics": ethics,
        "traditions": traditions,
        "ascension_perks": ascension_perks,
        "is_hive": is_hive,
        "is_machine": is_machine,
        "is_gestalt": is_gestalt,
        "is_megacorp": is_megacorp,
        "is_nomad": is_nomad,
        "is_wilderness": is_wilderness,
        "shipset_kind": shipset_kind,
        "uses_consumer_goods": uses_consumer_goods,
        "uses_food": uses_food,
        "ideology_active": ideology_active,
    }


def planet_recommendation(planet: dict, empire_net: dict) -> dict:
    amenities, housing, stability = planet["free_amenities"], planet["free_housing"], planet["stability"]
    designation = planet["designation_key"]
    if stability < 25:
        return {"level": "urgent", "title": "Prevent colony revolt", "action": f"On {planet['name']}, raise stability immediately: inspect amenities, housing, crime, faction approval, and martial/enforcer options in game.", "reason": f"Stability is {stability:.0f}%, below 25%, which risks a planetary revolt if left unaddressed."}
    if amenities < 0:
        return {"level": "urgent" if amenities < -5 or stability < 40 else "watch", "title": "Add amenities", "action": f"On {planet['name']}, check amenity jobs first; if they are filled, inspect the building menu for an amenity building.", "reason": f"This colony has {abs(amenities):.1f} fewer amenities than it uses. Check building availability and cost in game."}
    if stability < 50:
        return {"level": "urgent" if stability < 40 else "watch", "title": "Improve stability", "action": "Check jobs, crime, faction approval and the governor before expanding.", "reason": f"Stability is {stability:.0f}%, which can reduce colony output."}
    if housing < 2:
        return {"level": "watch", "title": "Prepare more housing", "action": f"Check whether {planet['name']} can add a City District before its next growth completes.", "reason": f"Only {housing:.1f} housing remains. Check for an open district slot in game."}
    if "generator" in designation and empire_net.get("energy", 0) < 20:
        return {"level": "growth", "title": "Review energy jobs", "action": "Check technician jobs and available workers before considering another Generator District.", "reason": "The designation fits energy production, but unused job capacity will not benefit from another district."}
    if "industrial" in designation and empire_net.get("alloys", 0) < 40:
        return {"level": "growth", "title": "Review industrial jobs", "action": "Check foundry and artisan job settings, workers and mineral upkeep before considering another Industrial District.", "reason": "Existing industrial capacity should be checked before adding more."}
    return {"level": "stable", "title": "No urgent build", "action": "Let the colony grow and revisit when a job, housing or amenity warning appears.", "reason": "Housing, amenities and stability are currently comfortable."}


def planet_job_advice(planet: dict, empire_net: dict) -> list[dict]:
    jobs = {item["type"]: item for item in planet.get("jobs", [])}
    advice = []
    priorities = []
    if planet["free_amenities"] < 0:
        priorities.append((("entertainer", "maintenance_drone"),
                           f"Amenities are {planet['free_amenities']:+.1f}.",
                           "Filling this job may draw workers from another resource."))
    for resource, kinds in (("minerals", ("miner", "mining_drone")),
                            ("energy", ("technician", "technician_drone")),
                            ("food", ("farmer", "agri_drone")),
                            ("alloys", ("foundry", "fabricator", "alloy_drone")),
                            ("consumer_goods", ("artisan", "artisan_drone")),
                            ("trade", ("trader", "clerk", "logistics_drone"))):
        if empire_net.get(resource, 0) < 0:
            priorities.append((kinds, f"Empire {resource.replace('_', ' ')} is {empire_net[resource]:+.1f}/month.",
                               "Compare worker availability and upkeep before changing job priority."))
    for kinds, observation, tradeoff in priorities:
        for kind in kinds:
            job = jobs.get(kind)
            if not job or job["capacity"] is None:
                continue
            if job["disabled"]:
                action = f"Review the disabled {kind.replace('_', ' ')} job setting."
            elif job["capacity"] > job["filled"] and (job["limit"] is None or job["limit"] > job["filled"]):
                action = f"Consider filling the open {kind.replace('_', ' ')} job."
            else:
                continue
            allowed = min(job["capacity"], job["limit"]) if job["limit"] is not None else job["capacity"]
            upkeep = ", ".join(f"{name.replace('_', ' ')} {amount:g}"
                               for name, amount in planet.get("upkeep", {}).items() if amount > 0)
            advice.append({"observation": f"{observation} On this colony, {job['filled']:g} of {job['capacity']:g} capacity is filled and {allowed:g} jobs are allowed.",
                           "action": action,
                           "tradeoff": tradeoff + (f" Colony upkeep recorded: {upkeep}." if upkeep else " Check colony upkeep in game."),
                           "check": f"Confirm {kind.replace('_', ' ')} job priority and available workforce in game.",
                           "confidence": "Job capacity read from save; assignment must be checked in game."})
            break
    return advice[:2]


def parse_planets(game: str, player: str, empire_net: dict) -> list[dict]:
    owned = [int(value) for value in re.findall(r"\b\d+\b", block(player, "owned_planets"))]
    colonies = dict(indexed_entries(block(game, "colony", top_level=True), 1))
    job_records = dict(indexed_entries(block(game, "pop_jobs", top_level=True), 1))
    planet_records = dict(indexed_entries(block(block(game, "planets", top_level=True), "planet"), 2))
    # `owned_planets` contains colony IDs in Cygnus. The actual celestial-body
    # record points back to that ID through its direct `colony=` field. Looking
    # up a planet by the colony ID instead returns an unrelated star, moon or
    # asteroid that happens to share the same numeric index.
    colony_to_planet = {}
    for planet_id, record in planet_records.items():
        colony_id = direct_scalar(record, "colony", tabs=3, default=None)
        if colony_id is not None:
            colony_to_planet[int(colony_id)] = (planet_id, record)
    owned_origins = {
        scalar(block(record, "coordinate"), "origin", "")
        for _, record in colony_to_planet.values()
    }
    system_names = {}
    for record in planet_records.values():
        planet_class = scalar(record, "planet_class", "")
        if "_star" not in planet_class:
            continue
        origin = scalar(block(record, "coordinate"), "origin", "")
        if origin not in owned_origins or origin in system_names:
            continue
        star_name = re.sub(r"\s+[A-Z]$", "", parse_name(record, "Unknown system"))
        system_names[origin] = star_name
    result = []
    for colony_id in owned:
        actual_planet_id, record = colony_to_planet.get(colony_id, (colony_id, planet_records.get(colony_id, "")))
        colony = colonies.get(colony_id, "")
        origin = scalar(block(record, "coordinate"), "origin", "")
        designation_key = scalar(colony, "final_designation", "col_colony")
        planet = {
            "id": colony_id, "planet_id": actual_planet_id, "name": parse_name(record, f"Colony {colony_id}"),
            "system": system_names.get(origin, ""),
            "class": display_token(scalar(record, "planet_class", "unknown"), "pc_"),
            "class_key": scalar(record, "planet_class", ""),
            "size": round(numeric(record, "planet_size")),
            "size_known": scalar(record, "planet_size", None) is not None,
            "designation": display_token(designation_key, "col_"), "designation_key": designation_key,
            "stability": round(numeric(colony, "stability"), 1), "crime": round(numeric(colony, "crime"), 1),
            "pops": scaled_colony_value(numeric(colony, "num_sapient_pops")),
            "free_housing": scaled_colony_value(numeric(colony, "free_housing")),
            "free_amenities": scaled_colony_value(numeric(colony, "free_amenities")),
            "jobs": parse_job_summary(colony, job_records),
            "districts": len(re.findall(r"\b\d+\b", block(colony, "districts"))),
            "buildings": len(re.findall(r"\b\d+\b", block(colony, "buildings_cache"))),
            "produces": resource_totals(block(colony, "produces")), "upkeep": resource_totals(block(colony, "upkeep")),
            "profits": resource_totals(block(colony, "profits")),
        }
        planet["recommendation"] = planet_recommendation(planet, empire_net)
        planet["job_advice"] = planet_job_advice(planet, empire_net)
        result.append(planet)
    order = {"urgent": 0, "watch": 1, "growth": 2, "stable": 3}
    result.sort(key=lambda item: (order[item["recommendation"]["level"]], item["name"]))
    return result


def pretty_tech(value: str) -> str:
    return display_token(value, "tech_")


def choose_tech(branch: str, alternatives: list[str], hint: dict) -> tuple[str, str]:
    if not alternatives:
        return "No alternative visible", "Open the research picker in game to see the available choices."
    profile = hint.get("profile") or {}
    version = str(hint.get("version") or "")
    uses_food = profile.get("uses_food", True)
    release = parse_release_tuple(version)
    is_46_plus = bool(release and release >= (4, 6, 0))
    society_rules = []
    if is_46_plus and not profile.get("is_gestalt"):
        society_rules.append((("galactic_administration",), True,
                              "In 4.6+, Galactic Administration is reported to unlock the 5th Council position; verify in game."))
    if uses_food:
        society_rules.append((("food", "farm", "growth", "health"), hint["net"].get("food", 0) < 10, "It supports food or population growth."))
    society_rules.append((("diplom", "federation", "naval"), True, "It can widen the empire's strategic options."))
    rules = {
        "physics": [(("power", "energy", "reactor"), hint["net"].get("energy", 0) < 20, "It supports the empire's energy margin."), (("shield", "laser", "weapon", "combat"), hint["military"] < 3000, "It can help close the fleet power gap.")],
        "society": society_rules,
        "engineering": [(("alloy", "industry", "mining"), hint["net"].get("alloys", 0) < 40, "It supports minerals, industry or alloys."), (("arkship", "waystation", "thruster"), bool(profile.get("is_nomad")), "It supports Nomad fleet mobility or Arkship progression."), (("armor", "hull", "weapon", "ship"), hint["military"] < 3000, "It can support the next fleet upgrade.")],
    }
    for keywords, enabled, reason in rules[branch]:
        if enabled:
            found = next((tech for tech in alternatives if any(word in tech.lower() for word in keywords)), None)
            if found:
                return pretty_tech(found), reason
    return pretty_tech(alternatives[0]), "It is the first visible option; compare its in-game effect with your current goal."


def parse_technology(player: str, hint: dict, game_dir: str = "") -> dict:
    status = block(player, "tech_status")
    researched, researched_status = researched_technologies(status)
    alternatives_root = block(status, "alternatives")
    branches = {}
    for branch in ("physics", "society", "engineering"):
        queue, available_block = block(status, f"{branch}_queue"), block(alternatives_root, branch)
        current_id = scalar(queue, "technology", "")
        alternatives = [value for value in re.findall(r'"([^"]+)"', available_block) if value != current_id]
        recommendation, reason = choose_tech(branch, alternatives, hint)
        raw_progress = scalar(queue, "progress")
        try:
            progress_value = float(raw_progress)
            progress_known = math.isfinite(progress_value) and progress_value >= 0
        except (TypeError, ValueError):
            progress_value, progress_known = 0.0, False
        branches[branch] = {"current": pretty_tech(current_id) if current_id else "Choose research", "current_id": current_id, "progress": round(progress_value, 1) if progress_known else 0.0, "progress_known": progress_known, "started": scalar(queue, "date", ""), "alternatives": [pretty_tech(value) for value in alternatives[:6]], "alternative_ids": alternatives, "recommendation": recommendation, "reason": reason}
    if game_dir and researched_status == "complete":
        from .technology import focus_path
        completed = set(researched)
        for name, branch in branches.items():
            options = [key for key in re.findall(r'"([^"]+)"', block(alternatives_root, name))
                       if key != branch["current_id"]]
            branch["focus_path"] = focus_path(game_dir, name, completed,
                                                branch["current_id"], options, hint["net"],
                                                profile=hint.get("profile"),
                                                save_version=hint.get("version", ""))
    return {"researched_count": len(researched), "researched": researched,
            "researched_status": researched_status, "branches": branches}


def repeated_blocks(text: str, key: str):
    for match in re.finditer(r"(?<![A-Za-z_])" + re.escape(key) + r"\s*=\s*\{", text):
        opening = text.find("{", match.start(), match.end())
        yield text[opening:matching_brace(text, opening)]


def ship_design_check(role: str, slots: list[dict], auto_generated: bool) -> dict:
    weapons = [item for item in slots if any(part in item["slot"] for part in ("GUN", "TORPEDO", "MISSILE", "HANGAR"))]
    torpedoes = [item for item in weapons if "TORPEDO" in item["component"]]
    if "explosive" in role.lower() and not torpedoes:
        suggestion = "Review the torpedo-capable slot for this explosive role."
        why = "The saved role is explosive, but no torpedo component was found in its slots."
    elif not weapons:
        suggestion = "Check this design's weapon sections in Ship Designer."
        why = "No weapon slot could be verified from the save."
    else:
        suggestion = "Review this loadout in Ship Designer before changing weapons."
        why = f"The save shows {len(weapons)} weapon slot(s), including {len(torpedoes)} torpedo slot(s)."
    return {"suggestion": suggestion, "why": why,
            "tradeoff": "A weapon change can alter range, damage profile, power use, and cost.",
            "check": "Confirm unlocked alternatives, final stats, cost and upkeep in the in-game Ship Designer.",
            "confidence": "Slot-level save check; build eligibility and enemy counters are unverified.",
            "auto_generated": auto_generated}


def component_prerequisite_evidence(designs: list[dict], technology: dict,
                                    game_dir: str, version_match: str) -> None:
    """Compare owned components with matching installed base-game tech requirements.

    This never establishes full build eligibility: events, empire type, DLC, mods,
    and slot rules can add conditions outside a component's listed prerequisites.
    """
    wanted = {slot.get("component", "") for design in designs
              for slot in design.get("slots", [])}
    wanted = {key for key in wanted if re.fullmatch(r"[A-Za-z0-9_]{1,100}", key)}
    definitions = {}
    available = (bool(game_dir) and version_match == "match"
                 and technology.get("researched_status") == "complete")
    if available and wanted:
        try:
            root = Path(game_dir).resolve()
            directory = (root / "common" / "component_templates").resolve()
            if not directory.is_relative_to(root) or not directory.is_dir():
                raise ValueError("Component directory unavailable")
            files = sorted(directory.glob("*.txt"))
            if len(files) > 128:
                raise ValueError("Too many component definition files")
            total = 0
            for path in files:
                if not path.resolve().is_relative_to(directory):
                    raise ValueError("Component definition outside game directory")
                size = path.stat().st_size
                total += size
                if size > 1_000_000 or total > 8_000_000:
                    raise ValueError("Component definitions too large")
                source = path.read_text(encoding="utf-8-sig")
                for match in re.finditer(
                        r"(?m)^(?:weapon|utility|strike_craft)_component_template\s*=\s*\{", source):
                    opening = source.find("{", match.start(), match.end())
                    entry = source[opening:matching_brace(source, opening)]
                    key = scalar(entry, "key", "")
                    if key not in wanted:
                        continue
                    requirements = block(entry, "prerequisites")
                    tech_ids = re.findall(r'"(tech_[A-Za-z0-9_]+)"', requirements)
                    definitions[key] = tech_ids if requirements and tech_ids else None
        except (OSError, ValueError, UnicodeError):
            available = False
            definitions = {}
    researched = technology.get("researched", {}) if available else {}
    for design in designs:
        evidence = []
        for component in dict.fromkeys(slot.get("component", "")
                                       for slot in design.get("slots", [])):
            requirements = definitions.get(component)
            if requirements:
                missing = [tech for tech in requirements if tech not in researched]
                status = "tech_not_recorded" if missing else "listed_tech_researched"
            else:
                missing, status = [], "unverified"
            evidence.append({"component": component, "status": status,
                             "required_tech": requirements or [], "unresearched_tech": missing})
        design["component_evidence"] = evidence
        design["component_access_status"] = "unverified"


def parse_ship_builds(game: str, player: str, empire_net: dict, military: float) -> dict:
    owned_ids = [int(value) for value in re.findall(r"\b\d+\b", block(block(player, "ship_design_collection"), "ship_design"))]
    all_designs = dict(indexed_entries(block(game, "ship_design", top_level=True), 1))
    combat_sizes = {
        "corvette": 1, "frigate": 1, "destroyer": 2, "cruiser": 3,
        "battleship": 4, "titan": 5, "juggernaut": 6, "colossus": 6,
        "mauler": 1, "weaver": 2, "harbinger": 3, "stinger": 4,
        "arkship": 5, "military_arkship": 6,
    }
    designs = []
    for design_id in owned_ids:
        raw = all_designs.get(design_id, "")
        size_key = str(scalar(raw, "ship_size", "")).lower()
        if size_key not in combat_sizes:
            continue
        components = []
        slots = []
        for component in repeated_blocks(raw, "component"):
            template = scalar(component, "template", "")
            slot = scalar(component, "slot", "")
            if template:
                slots.append({"slot": slot, "component": template})
            if template and template not in components:
                components.append(template)
        role = scalar(raw, "ship_role", scalar(raw, "role", "general"))
        designs.append({"id": design_id, "name": parse_name(raw, f"{display_token(size_key)} design"), "size": display_token(size_key), "size_key": size_key, "role": display_token(role, "ship_role_", "role_"), "components": [display_token(value, "SMALL_", "MEDIUM_", "LARGE_", "EXTRA_LARGE_") for value in components[:10]]})
        designs[-1]["slots"] = slots
        designs[-1]["required_components"] = re.findall(r'required_component="([^"]+)"', raw)
        designs[-1]["component_access_status"] = "unverified"
        designs[-1]["design_check"] = ship_design_check(role, slots, scalar(raw, "auto_gen_design", "no") == "yes")
    designs.sort(key=lambda item: (-combat_sizes[item["size_key"]], item["name"]))
    candidate = next((item for item in designs if any(word in item["role"].lower() for word in ("gun", "artillery", "brawler", "screen"))), None) or (designs[0] if designs else None)
    if empire_net.get("alloys", 0) <= 0:
        recommendation = {"title": "Stabilize alloys before ordering ships", "design_id": candidate["id"] if candidate else None, "quantity": "Pause major orders", "reason": "Monthly alloy income is not positive, so a ship order may delay recovery.", "caveat": "Verify naval capacity, upkeep and the ship's in-game cost before committing."}
    elif candidate:
        recommendation = {"title": f"Review {candidate['name']} for reinforcement", "design_id": candidate["id"], "quantity": "Check one order in game first", "reason": "This is an owned saved combat design and monthly alloy income is positive. The save does not establish build eligibility or affordability." + (" Fleet power is still modest." if military < 3000 else ""), "caveat": "Verify unlocked components, naval capacity, upkeep, counters and the ship's in-game cost before committing."}
    else:
        recommendation = {"title": "Create or upgrade a combat design", "design_id": None, "quantity": "Review Ship Designer", "reason": "No owned combat design could be read from this save.", "caveat": "The guide will use the new design after the next autosave."}
    return {"designs": designs, "recommendation": recommendation}


def parse_player_fleets(game: str, player: str, designs: list[dict]) -> dict:
    """Read owned military fleets and infer class usage from saved fleet plans.

    The save records naval capacity used but not its maximum. A plan's fleet_size
    is a planned composition, not the fleet command limit.
    """
    owned = block(block(player, "fleets_manager"), "owned_fleets")
    owned_ids = {int(value) for value in re.findall(r"\bfleet\s*=\s*(\d+)", owned)}
    if not owned_ids:
        return {"fleets": [], "class_usage": {}, "usage_status": "unavailable"}

    fleet_blocks = {key: raw for key, raw in indexed_entries(block(game, "fleet", top_level=True))
                    if key in owned_ids and scalar(raw, "ship_class") == "shipclass_military"}
    if not fleet_blocks:
        return {"fleets": [], "class_usage": {}, "usage_status": "unavailable"}
    ship_ids = {int(value) for raw in fleet_blocks.values()
                for value in re.findall(r"\b\d+\b", block(raw, "ships"))}
    ships = {key: raw for key, raw in indexed_entries(block(game, "ships", top_level=True))
             if key in ship_ids}
    template_ids = {int(value) for raw in fleet_blocks.values()
                    if (value := scalar(raw, "fleet_template", "")).isdigit()}
    templates = {key: raw for key, raw in indexed_entries(block(game, "fleet_template", top_level=True))
                 if key in template_ids}
    design_classes = {key: str(scalar(raw, "ship_size", "")).lower()
                      for key, raw in indexed_entries(block(game, "ship_design", top_level=True))}

    plans = {}
    for template_id, raw in templates.items():
        planned = scalar(raw, "fleet_size", "")
        counts = {}
        for design_id, quantity in re.findall(
                r"\{\s*ship_design_implementation\s*=\s*\{([^{}]*)\}"
                r"\s*(?:count\s*=\s*(\d+))?\s*\}", raw):
            design_match = re.search(r"\bdesign\s*=\s*(\d+)", design_id)
            size = design_classes.get(int(design_match.group(1))) if design_match else None
            if size:
                counts[size] = counts.get(size, 0) + int(quantity or 1)
        plans[template_id] = {"size": int(planned) if planned.isdigit() else None,
                              "classes": counts}

    # A single-class plan gives a direct saved ratio. Mixed plans can then
    # determine one remaining class. Conflicting or fractional evidence is omitted.
    weights = {}
    conflicts = set()
    for plan in plans.values():
        if plan["size"] is None or len(plan["classes"]) != 1:
            continue
        size, quantity = next(iter(plan["classes"].items()))
        if quantity <= 0 or plan["size"] % quantity:
            continue
        candidate = plan["size"] // quantity
        if candidate <= 0 or (size in weights and weights[size] != candidate):
            conflicts.add(size)
        else:
            weights[size] = candidate
    for size in conflicts:
        weights.pop(size, None)
    for _ in range(4):
        changed = False
        for plan in plans.values():
            if plan["size"] is None:
                continue
            unknown = [(size, count) for size, count in plan["classes"].items()
                       if size not in weights and size not in conflicts]
            if len(unknown) != 1 or any(size in conflicts for size in plan["classes"]):
                continue
            size, quantity = unknown[0]
            remainder = plan["size"] - sum(count * weights[known]
                                             for known, count in plan["classes"].items()
                                             if known in weights)
            if quantity > 0 and remainder > 0 and remainder % quantity == 0:
                weights[size] = remainder // quantity
                changed = True
        if not changed:
            break

    systems = {key: parse_name(raw, "Unknown system")
               for key, raw in indexed_entries(block(game, "galactic_object", top_level=True))}
    fleets = []
    class_usage = {}
    for fleet_id, raw in fleet_blocks.items():
        name_data = block(raw, "name")
        sequence = re.search(r'key="num"\s+value\s*=\s*\{\s*key="(\d+)"', name_data)
        if scalar(name_data, "key") == "%SEQ%" and sequence:
            n = int(sequence.group(1))
            suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
            name = f"{n}{suffix} Fleet"
        else:
            name = parse_name(raw, f"Fleet {fleet_id}")
        by_class = {}
        design_counts = {}
        ship_ids = re.findall(r"\b\d+\b", block(raw, "ships"))
        for ship_id in ship_ids:
            ship = ships.get(int(ship_id), "")
            design_id = scalar(block(ship, "ship_design_implementation"), "design", "")
            size = design_classes.get(int(design_id)) if design_id.isdigit() else None
            if size:
                by_class[size] = by_class.get(size, 0) + 1
                design_counts[design_id] = design_counts.get(design_id, 0) + 1
        classes_complete = len(ship_ids) == sum(by_class.values())
        actual = sum(count * weights[size] for size, count in by_class.items()) if (
            classes_complete and by_class and all(size in weights for size in by_class)) else None
        if actual is not None:
            for size, count in by_class.items():
                class_usage[size] = class_usage.get(size, 0) + count * weights[size]
        template_id = scalar(raw, "fleet_template", "")
        plan = plans.get(int(template_id), {}) if template_id.isdigit() else {}
        coordinate = block(block(raw, "combat"), "coordinate")
        origin = scalar(coordinate, "origin", "")
        location = systems.get(int(origin)) if origin.isdigit() else None
        fleets.append({"id": fleet_id, "name": name[:MAX_LABEL_LENGTH],
                       "power": round(numeric(raw, "military_power")),
                       "ship_count": len(ship_ids), "classes": by_class,
                       "classes_complete": classes_complete,
                       "design_counts": design_counts, "size": actual,
                       "planned_size": plan.get("size"),
                       "location": location if location != "Unknown system" else None})
    fleets.sort(key=lambda item: (int(re.match(r"\d+", item["name"]).group())
                                  if re.match(r"\d+", item["name"]) else 10**9, item["id"]))
    used = scalar(player, "used_naval_capacity", "")
    known_total = sum(item["size"] for item in fleets if item["size"] is not None)
    usage_status = ("matches_saved_total" if used.isdigit() and
                    all(item["size"] is not None for item in fleets) and
                    known_total == int(used) else "inferred_from_plans")
    for design in designs:
        design["naval_usage"] = weights.get(design["size_key"])
    return {"fleets": fleets, "class_usage": class_usage, "usage_status": usage_status}


def bounded_zip_text(archive: zipfile.ZipFile, name: str, limit: int) -> str:
    if archive.getinfo(name).file_size > limit:
        raise ValueError(f"The save {name} is too large to read safely")
    with archive.open(name) as entry:
        data = entry.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"The save {name} is too large to read safely")
    return data.decode("utf-8-sig", "replace")


def _parse_save_texts(meta: str, game: str, *, path: Path | None, filename: str,
                      modified: float, fingerprint: str, campaign_seed: str,
                      include_details: bool = True, game_dir: str = "") -> dict:
    version, date, campaign_name = scalar(meta, "version", "Unknown"), scalar(meta, "date", "Unknown"), scalar(meta, "name", "Your empire")
    version = version if len(version) <= MAX_LABEL_LENGTH else "Unknown"
    date = date if len(date) <= 32 else "Unknown"
    campaign_name = campaign_name if len(campaign_name) <= MAX_LABEL_LENGTH else "Your empire"
    required_dlcs, save_mods = save_list(meta, "required_dlcs"), save_list(meta, "mods")
    dlc_summary = active_dlcs(required_dlcs, version)
    player_block = block(game, "player", top_level=True)
    player_ref = scalar(player_block, "country") if player_block else None
    if player_ref is None or not player_ref.isdigit():
        raise ValueError("The player country reference was not found")
    player_id = int(player_ref)
    countries = block(game, "country", top_level=True)
    if not countries:
        raise ValueError("The country section was not found")
    entries = {}
    for country_id, country in country_entries(countries):
        kind = direct_scalar(country, "type", default="")
        if kind in ("default", "fallen_empire", "awakened_fallen_empire") or country_id == player_id:
            entries[country_id] = country
    if player_id not in entries:
        raise ValueError("The player empire was not found")
    player = entries[player_id]
    empire_name = player_empire_name(campaign_name, player)
    empire_name = empire_name if len(empire_name) <= MAX_LABEL_LENGTH else "Your empire"
    campaign_id = hashlib.sha256(
        f"{campaign_seed}:{player_id}".encode("utf-8")
    ).hexdigest()[:16]
    stock = resource_totals(block(player, "resource_stockpile"))
    if not stock:
        stock = resource_totals(block(block(player, "standard_economy_module"), "resources"))
    budget = block(player, "budget")
    income, expenses = resource_totals(block(budget, "income")), resource_totals(block(budget, "expenses"))
    net = {key: round(income.get(key, 0) - abs(expenses.get(key, 0)), 1) for key in RESOURCES}
    contacts_block = block(player, "contacts")
    known_ids = {int(value) for value in re.findall(r"\b\d+\b", contacts_block)}
    opinions = {}
    relations = {}
    for relation in repeated_blocks(block(player, "diplomacy"), "relation"):
        opinions[int(scalar(relation, "country", "-1"))] = round(numeric(relation, "value"))
    # Older and synthetic saves expose contacts through relations_manager.
    for relation in repeated_blocks(block(player, "relations_manager"), "relation"):
        target = int(scalar(relation, "country", "-1"))
        if scalar(relation, "contact", "no") == "yes":
            known_ids.add(target)
        opinions[target] = round(numeric(relation, "relation_current"))
        relations[target] = {
            "hostile": scalar(relation, "hostile", "no") == "yes",
            "embassy": scalar(relation, "embassy", "no") == "yes",
        }
    known_intel = parse_known_intel(player)
    network_ids = {int(value) for value in re.findall(r"\b\d+\b", block(player, "spy_networks"))}
    networks = dict(indexed_entries(block(game, "spy_networks", top_level=True), 1))
    network_targets = {int(scalar(networks[network_id], "target", "-1"))
                       for network_id in network_ids if network_id in networks}
    wars_by_country: dict[int, list[dict]] = {}
    for war_id, war in indexed_entries(block(game, "war", top_level=True), 1):
        attackers = {int(value) for value in re.findall(r"\bcountry=(\d+)", block(war, "attackers"))}
        defenders = {int(value) for value in re.findall(r"\bcountry=(\d+)", block(war, "defenders"))}
        for side, members, opposition in (("attacker", attackers, defenders),
                                           ("defender", defenders, attackers)):
            raw = direct_scalar(war, f"{side}_war_exhaustion", default=None)
            exhaustion = round(float(raw) * 100, 1) if raw is not None else None
            for member in members:
                wars_by_country.setdefault(member, []).append({
                    "id": war_id, "side": side, "exhaustion": exhaustion,
                    "against_player": player_id in opposition,
                })
    contacts = []
    for country_id in known_ids:
        other = entries.get(country_id)
        if not other or country_id == player_id:
            continue
        other_budget = block(other, "budget")
        other_income = resource_totals(block(other_budget, "income"))
        other_expenses = resource_totals(block(other_budget, "expenses"))
        contacts.append({"id": country_id, "name": display_name(block(other, "name"), country_id),
                         "kind": direct_scalar(other, "type", default="default"),
                         "personality": direct_scalar(other, "personality", default=None),
                         "military": round(float(direct_scalar(other, "military_power", default=0) or 0)),
                         "economy": round(float(direct_scalar(other, "economy_power", default=0) or 0)),
                         "technology": round(float(direct_scalar(other, "tech_power", default=0) or 0)),
                         "opinion": opinions.get(country_id), "intel": known_intel.get(country_id),
                         "spy_network": country_id in network_targets,
                         "wars": wars_by_country.get(country_id, []),
                         "relation": relations.get(country_id, {}),
                         "hidden": {
                             "stock": resource_totals(block(other, "resource_stockpile")),
                             "net": {key: round(other_income.get(key, 0)
                                               - abs(other_expenses.get(key, 0)), 1)
                                     for key in RESOURCES},
                         }})
    contacts.sort(key=lambda item: item["military"], reverse=True)
    military = round(float(direct_scalar(player, "military_power", default=0) or 0))
    owned_planets = [int(value) for value in re.findall(r"\b\d+\b", block(player, "owned_planets"))]
    policies = parse_policies(player)
    ship_builds = (parse_ship_builds(game, player, net, military)
                   if include_details else {"designs": [], "recommendation": {}})
    profile = parse_empire_profile(player, policies, ship_builds.get("designs"))
    installed = (installed_context(game_dir, path, version, save_mods)
                 if path is not None else {"version": None, "checksum": None,
                                           "version_match": "unknown",
                                           "playset_mods": None, "mod_match": "unknown"})
    snapshot = {
        "path": str(path) if path is not None else filename, "filename": filename, "modified": modified,
        "version": version, "date": date, "empire": empire_name,
        "campaign": {"id": campaign_id, "player_country_id": player_id,
                     "save_version": version, "save_date": date,
                     "required_dlcs": required_dlcs, "dlc_summary": dlc_summary,
                     "mods": save_mods, "installed": installed},
        "player": {
            "id": player_id, "military": military,
            "economy": round(float(direct_scalar(player, "economy_power", default=0) or 0)),
            "technology": round(float(direct_scalar(player, "tech_power", default=0) or 0)),
            "naval_used": round(float(direct_scalar(player, "used_naval_capacity", default=0) or 0)),
            "naval_capacity": None,
            "starbase_used": round(float(direct_scalar(player, "starbase_capacity_used", default=0) or 0)),
            "starbase_capacity": round(float(direct_scalar(player, "starbase_capacity", default=0) or 0)),
            "empire_size": round(float(direct_scalar(player, "empire_size", default=0) or 0)),
            "colonies": len(owned_planets), "stock": stock, "net": net,
            "stock_known": {key: key in stock for key in RESOURCES},
            "net_known": {key: key in income or key in expenses for key in RESOURCES},
            "research": {branch: round(income.get(f"{branch}_research", 0), 1)
                         for branch in ("physics", "society", "engineering")},
            "profile": profile,
        },
        "contacts": contacts, "policies": policies, "flag": parse_flag(player),
    }
    snapshot["technology"] = parse_technology(
        player, {"net": net, "military": military, "profile": profile, "version": version},
        game_dir if include_details else "",
    )
    if include_details:
        snapshot["planets"] = parse_planets(game, player, net)
        snapshot["ship_builds"] = ship_builds
        snapshot["ship_builds"].update(parse_player_fleets(
            game, player, snapshot["ship_builds"]["designs"]))
        component_prerequisite_evidence(
            snapshot["ship_builds"]["designs"], snapshot["technology"], game_dir,
            snapshot["campaign"]["installed"]["version_match"])
        military_policies = {key: value for key, value in snapshot["policies"].items()
                             if is_military_policy_key(key)}
        snapshot["ship_builds"]["policies"] = military_policies
        snapshot["ship_builds"]["policy_details"] = military_policy_details(
            military_policies, game_dir, snapshot["campaign"]["installed"]["version_match"])
        rec = snapshot["ship_builds"].get("recommendation", {})
        if rec and military_policies:
            rec["caveat"] += " Compare this design with the saved military policies shown below."
    else:
        snapshot["planets"] = []
        snapshot["ship_builds"] = ship_builds
    snapshot["_save_fingerprint"] = fingerprint
    return snapshot


def parse_save_bytes(raw_bytes: bytes, filename: str = "uploaded.sav", *,
                     modified: float = 0.0, campaign_label: str = "",
                     include_details: bool = True, game_dir: str = "",
                     max_gamestate_bytes: int = MAX_GAMESTATE_BYTES) -> dict:
    """Parse an in-memory .sav ZIP archive safely (used by browser/web mode)."""
    if len(raw_bytes) > max_gamestate_bytes:
        raise ValueError("The save archive is too large to read safely in this mode")
    with zipfile.ZipFile(io.BytesIO(raw_bytes)) as archive:
        if not {"meta", "gamestate"}.issubset(archive.namelist()):
            raise ValueError("The file has no Stellaris meta or gamestate")
        meta = bounded_zip_text(archive, "meta", MAX_META_BYTES)
        game = bounded_zip_text(archive, "gamestate", max_gamestate_bytes)
    fingerprint = hashlib.sha256(raw_bytes).hexdigest()
    seed = (campaign_label or scalar(meta, "name", "") or filename).strip().casefold()
    return _parse_save_texts(
        meta, game, path=None, filename=Path(filename).name or "uploaded.sav",
        modified=modified, fingerprint=fingerprint, campaign_seed=f"web:{seed}",
        include_details=include_details, game_dir=game_dir,
    )


def parse_save(path: Path, include_details: bool = True, game_dir: str = "") -> dict:
    with zipfile.ZipFile(path) as archive:
        if not {"meta", "gamestate"}.issubset(archive.namelist()):
            raise ValueError("The file has no Stellaris meta or gamestate")
        meta = bounded_zip_text(archive, "meta", MAX_META_BYTES)
        game = bounded_zip_text(archive, "gamestate", MAX_GAMESTATE_BYTES)
    # Spoiler consent is bound to this exact save. Folder/player IDs can be reused
    # by a new campaign and must never carry consent across that boundary.
    with path.open("rb") as save_stream:
        fingerprint = hashlib.file_digest(save_stream, "sha256").hexdigest()
    return _parse_save_texts(
        meta, game, path=path, filename=path.name, modified=path.stat().st_mtime,
        fingerprint=fingerprint, campaign_seed=path.parent.resolve().as_posix().casefold(),
        include_details=include_details, game_dir=game_dir,
    )


def recent_saves(root: Path, limit: int = 6) -> list[Path]:
    if not root.is_dir():
        return []
    paths = []
    for folder, _, files in os.walk(root):
        for filename in files:
            if filename.lower().endswith(".sav"):
                path = Path(folder) / filename
                try:
                    paths.append((path.stat().st_mtime, path))
                except OSError:
                    continue
    if not paths:
        return []
    autosaves = [item for item in paths if item[1].name.lower().startswith("autosave")]
    if autosaves:
        paths = autosaves
    newest = max(paths)[1]
    campaign_paths = [item for item in paths if item[1].parent == newest.parent]
    return [path for _, path in sorted(campaign_paths, reverse=True)[:limit]]
