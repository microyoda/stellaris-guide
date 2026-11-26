"""Conservative, save-scoped routes through installed base-game technology rules."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re

from .dlcs import dlc_status_list, extract_script_dlc_requirements
from .saves import block, matching_brace, pretty_tech, scalar


TECH_ID = re.compile(r"tech_[a-z0-9_]{1,100}\Z")
TECH_ENTRY = re.compile(r"(?m)^(tech_[a-z0-9_]+)\s*=\s*\{")
HAS_TECH = re.compile(r'\bhas_technology\s*=\s*"?(tech_[a-z0-9_]+)"?')
LOC_ENTRY = re.compile(r'^\s*(tech_[a-z0-9_]+):\d+\s+"((?:[^"\\]|\\.)*)"', re.M)
LOC_DESC_ENTRY = re.compile(r'^\s*(tech_[a-z0-9_]+_desc):\d+\s+"((?:[^"\\]|\\.)*)"', re.M)


@lru_cache(maxsize=2)
def _technology_names(game_dir: str) -> dict[str, str]:
    """Read local game labels without shipping Paradox localisation in the package."""
    root = Path(game_dir).resolve()
    directory = (root / "localisation" / "english").resolve()
    if not directory.is_relative_to(root) or not directory.is_dir():
        return {}
    names: dict[str, str] = {}
    total = 0
    try:
        for path in sorted(directory.glob("*.yml")):
            if not path.resolve().is_relative_to(directory):
                return {}
            size = path.stat().st_size
            total += size
            if size > 2_000_000 or total > 20_000_000:
                return {}
            for key, value in LOC_ENTRY.findall(path.read_text(encoding="utf-8-sig")):
                cleaned = re.sub(r"§.", "", value).replace(r'\"', '"').strip()
                if cleaned and len(cleaned) <= 160 and "$" not in cleaned:
                    names[key] = cleaned
    except (OSError, UnicodeError):
        return {}
    return names


@lru_cache(maxsize=2)
def _technology_descriptions(game_dir: str) -> dict[str, str]:
    """Use bounded installed English descriptions, not generated gameplay claims."""
    root = Path(game_dir).resolve()
    directory = (root / "localisation" / "english").resolve()
    if not directory.is_relative_to(root) or not directory.is_dir():
        return {}
    descriptions: dict[str, str] = {}
    total = 0
    try:
        for path in sorted(directory.glob("*.yml")):
            if not path.resolve().is_relative_to(directory):
                return {}
            size = path.stat().st_size
            total += size
            if size > 2_000_000 or total > 20_000_000:
                return {}
            for key, raw in LOC_DESC_ENTRY.findall(path.read_text(encoding="utf-8-sig")):
                cleaned = re.sub(r"§.", "", raw).replace(r"\n", " ").replace(r'\"', '"').strip()
                if (0 < len(cleaned) <= 320 and not re.search(r"[$£{}]", cleaned) and
                        not re.search(r"\\[A-Za-z]", cleaned)):
                    descriptions[key[:-5]] = cleaned
    except (OSError, UnicodeError):
        return {}
    return descriptions


def _parse_prerequisites(content: str) -> tuple[list[str], list[list[str]], bool]:
    """Read only plain tech IDs and explicit OR groups; flag other syntax."""
    source = re.sub(r"(?m)#.*$", "", content)
    if source.strip().startswith("{") and source.strip().endswith("}"):
        source = source.strip()[1:-1]
    masked = list(source)
    groups: list[list[str]] = []
    uncertain = False
    for match in re.finditer(r"\bOR\s*=\s*\{", source):
        if _depth_at(source, match.start()) != 0:
            uncertain = True
            continue
        opening = source.find("{", match.start(), match.end())
        closing = matching_brace(source, opening)
        inner = source[opening + 1:closing - 1]
        tokens = re.findall(r'"?(tech_[a-z0-9_]+)"?', inner)
        if tokens and not re.sub(r'"?tech_[a-z0-9_]+"?', "", inner).strip():
            groups.append(list(dict.fromkeys(tokens)))
        else:
            uncertain = True
        masked[match.start():closing] = " " * (closing - match.start())
    remainder = "".join(masked)
    direct = re.findall(r'"?(tech_[a-z0-9_]+)"?', remainder)
    if re.sub(r'"?tech_[a-z0-9_]+"?', "", remainder).strip():
        uncertain = True
    return list(dict.fromkeys(direct)), groups, uncertain


def _depth_at(text: str, stop: int) -> int:
    """Brace depth outside comments and quoted strings."""
    depth, quoted, escaped, comment = 0, False, False, False
    for char in text[:stop]:
        if comment:
            if char == "\n":
                comment = False
            continue
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == "#":
            comment = True
        elif char == '"':
            quoted = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
    return depth


def _simple_tech_group(content: str) -> list[str]:
    """Accept only a group made entirely of has_technology fields."""
    without_comments = re.sub(r"(?m)#.*$", "", content)
    options = HAS_TECH.findall(without_comments)
    remainder = HAS_TECH.sub("", without_comments).strip()
    return list(dict.fromkeys(options)) if options and not remainder else []


def _one_of_groups(potential: str) -> list[list[str]]:
    if not potential:
        return []
    groups = []
    for match in re.finditer(r"\bOR\s*=\s*\{", potential):
        if _depth_at(potential, match.start()) != 1:
            continue
        opening = potential.find("{", match.start(), match.end())
        options = _simple_tech_group(potential[opening + 1:matching_brace(potential, opening) - 1])
        if options:
            groups.append(options)
    for match in HAS_TECH.finditer(potential):
        if _depth_at(potential, match.start()) == 1:
            groups.append([match.group(1)])
    return groups


@lru_cache(maxsize=2)
def installed_rules(game_dir: str, installed_version: str = "") -> tuple[dict, dict]:
    """Read bounded local base-game files; no save or mod content is imported."""
    root = Path(game_dir).resolve()
    directory = (root / "common" / "technology").resolve()
    if not directory.is_relative_to(root) or not directory.is_dir():
        return {}, {}
    files = sorted(directory.glob("*.txt"))
    tier_file = directory / "tier" / "00_tier.txt"
    if len(files) > 80:
        return {}, {}
    rules, total = {}, 0
    names = _technology_names(game_dir)
    descriptions = _technology_descriptions(game_dir)
    try:
        for path in files:
            if not path.resolve().is_relative_to(directory):
                return {}, {}
            size = path.stat().st_size
            total += size
            if size > 1_000_000 or total > 8_000_000:
                return {}, {}
            source = path.read_text(encoding="utf-8-sig")
            for match in TECH_ENTRY.finditer(source):
                opening = source.find("{", match.start(), match.end())
                body = source[opening:matching_brace(source, opening)]
                potential = block(body, "potential")
                direct = block(body, "prerequisites")
                prerequisites, prerequisite_choices, prerequisite_unknown = _parse_prerequisites(direct)
                weight = scalar(body, "weight")
                weight_modifiers = block(body, "weight_modifier")
                rules[match.group(1)] = {
                    "id": match.group(1), "name": names.get(match.group(1), pretty_tech(match.group(1))),
                    "localized": match.group(1) in names,
                    "area": scalar(body, "area", ""),
                    "tier": int(scalar(body, "tier")) if str(scalar(body, "tier", "")).isdigit() else None,
                    "prerequisites": prerequisites,
                    "one_of": prerequisite_choices + _one_of_groups(potential),
                    "prerequisite_unknown": prerequisite_unknown,
                    "required_dlc": extract_script_dlc_requirements(potential),
                    "conditional": bool(potential),
                    "draw_conditions_unverified": bool(
                        potential or re.search(r"\bfactor\s*=\s*0\b", weight_modifiers)),
                    "granted_candidate": weight == "0" and not re.search(
                        r"\badd\s*=", weight_modifiers),
                    "source": path.name,
                    "description": descriptions.get(match.group(1), ""),
                }
        gates = {}
        if tier_file.resolve().is_relative_to(directory) and tier_file.stat().st_size <= 100_000:
            source = tier_file.read_text(encoding="utf-8-sig")
            for match in re.finditer(r"(?m)^(\d+)\s*=\s*\{", source):
                opening = source.find("{", match.start(), match.end())
                body = source[opening:matching_brace(source, opening)]
                count = scalar(body, "previously_unlocked")
                if str(count).isdigit():
                    gates[int(match.group(1))] = int(count)
        direct_children: dict[str, list[str]] = {}
        alternative_children: dict[str, list[str]] = {}
        for key, rule in rules.items():
            for parent in rule["prerequisites"]:
                direct_children.setdefault(parent, []).append(key)
            for group in rule["one_of"]:
                for parent in group:
                    alternative_children.setdefault(parent, []).append(key)
        for key, rule in rules.items():
            direct = [rules[child]["name"] for child in direct_children.get(key, []) if child in rules]
            alternate = [rules[child]["name"] for child in alternative_children.get(key, []) if child in rules]
            if direct:
                benefit = "Required for later research: " + ", ".join(sorted(direct)[:3]) + "."
            elif alternate:
                benefit = "One possible prerequisite for: " + ", ".join(sorted(alternate)[:3]) + "."
            else:
                benefit = "A specific gameplay benefit could not be verified from these rules; check its in-game card."
            rule["benefit"] = benefit
        return rules, gates
    except (OSError, UnicodeError, ValueError):
        return {}, {}


def _dlc_status(required: list[str], saved: list[str] | None,
                save_version: str | None = None) -> list[dict]:
    return dlc_status_list(required, saved, save_version)


def route_for_target(snapshot: dict, game_dir: str, target: str) -> dict:
    """Return a cautious route from the *selected* campaign only."""
    campaign = snapshot.get("campaign", {})
    installed = campaign.get("installed", {})
    result = {"target_id": target, "status": "unknown", "reason": "Rules unavailable.",
              "campaign_id": campaign.get("id"), "date": snapshot.get("date"),
              "modified": snapshot.get("modified"), "empire": snapshot.get("empire"),
              "release": campaign.get("save_version"), "steps": [], "one_of": [],
              "next_unlocks": [], "future_opportunities": [],
              "tier_gate": {"status": "unknown"}, "dlc": [], "next_check": "Check Technology in game."}
    if not TECH_ID.fullmatch(target) or not campaign.get("id"):
        result["reason"] = "Target or campaign identity is unavailable."
        return result
    if installed.get("version_match") != "match":
        result["reason"] = "Saved and installed game releases do not match."
        return result
    technology = snapshot.get("technology", {})
    if technology.get("researched_status") != "complete":
        result["reason"] = "Completed research could not be read fully from this save."
        return result
    rules, gates = installed_rules(game_dir, str(installed.get("version") or ""))
    if target not in rules:
        result["reason"] = "This target has no verified installed base-game definition."
        return result
    researched = set(technology.get("researched", {}))
    branches = technology.get("branches", {})
    current = {branch.get("current_id") for branch in branches.values()}
    options = {key for branch in branches.values() for key in branch.get("alternative_ids", [])}
    steps, visited = [], set()
    route_issues: set[str] = set()

    def add_step(key: str, depth: int) -> None:
        if key in visited:
            return
        if len(steps) >= 48:
            route_issues.add("Dependency route exceeds 48 steps.")
            return
        visited.add(key)
        rule = rules.get(key)
        if not rule:
            route_issues.add("A prerequisite definition is missing from installed base-game rules.")
        elif key not in researched:
            if rule.get("prerequisite_unknown"):
                route_issues.add("A prerequisite uses syntax this route cannot verify.")
            if depth >= 8 and rule["prerequisites"]:
                route_issues.add("Dependency route exceeds eight levels.")
            else:
                for prerequisite in rule["prerequisites"]:
                    add_step(prerequisite, depth + 1)
        state = ("researched" if key in researched else "researching" if key in current
                 else "saved_option" if key in options else "unmet")
        steps.append({"id": key, "name": rule["name"] if rule else pretty_tech(key),
                      "state": state, "definition_known": bool(rule)})

    add_step(target, 0)
    rule = rules[target]
    one_of = []
    for step in steps:
        if step["id"] in researched:
            continue
        owner = rules.get(step["id"])
        if not owner:
            continue
        for group in owner["one_of"]:
            if any(key not in rules for key in group):
                route_issues.add("An alternative prerequisite definition is missing from installed base-game rules.")
            one_of.append({"for_id": step["id"], "for_name": owner["name"],
                           "options": [
                               {"id": key, "name": rules[key]["name"] if key in rules else pretty_tech(key),
                                "state": ("researched" if key in researched else "researching" if key in current
                                          else "saved_option" if key in options else "unmet")}
                               for key in group]})
    tier = rule["tier"]
    threshold = gates.get(tier) if tier is not None else None
    prior_count = sum(key in researched and item.get("area") == rule["area"]
                      and item.get("tier") == tier - 1 for key, item in rules.items()) if tier else 0
    mods = campaign.get("mods") or []
    required_dlc = list(dict.fromkeys(dlc for step in steps
                                      for dlc in (rules.get(step["id"]) or {}).get("required_dlc", [])))
    save_version = campaign.get("save_version") or snapshot.get("version")
    dlc = _dlc_status(required_dlc, campaign.get("required_dlcs"), save_version)
    dlc_uncertain = any(item["status"] != "present" for item in dlc)
    tier_status = ("unknown" if threshold is None or mods else
                   "met" if prior_count >= threshold else "not_met")
    result.update(status="limited" if mods or dlc_uncertain or route_issues else "verified_base_game",
                  reason=("Base-game route only; this save's mod definitions are unverified."
                          if mods else "Required DLC is missing or cannot be verified from this save."
                          if dlc_uncertain else "Matching installed base-game rules."),
                  name=rule["name"], area=rule["area"], steps=steps,
                  one_of=one_of, granted_candidate=rule["granted_candidate"],
                  conditional=rule["conditional"], source=rule["source"],
                  description=rule["description"], benefit=rule["benefit"],
                  tier_gate={"tier": tier, "required_previous_tier": threshold,
                             "researched_previous_tier": prior_count, "status": tier_status},
                  dlc=dlc)
    if dlc_uncertain:
        result["next_check"] = "Check the required DLC in game before following this route."
    elif rule["granted_candidate"] and target not in researched:
        result["next_check"] = "This tech may come from an event or grant; check its source in game."
    elif target in researched:
        result["next_check"] = "Already researched in this save; explore what it leads toward."
    elif target in current:
        result["next_check"] = "This is a current project. Check its progress in game."
    elif target in options:
        result["next_check"] = "This is a saved research choice. Compare its effect in game."
    elif any(step["state"] == "unmet" for step in steps[:-1]):
        result["next_check"] = "Check the first unmet prerequisite in game; future draws are not guaranteed."
    elif any(not any(item["state"] == "researched" for item in group["options"])
             for group in one_of):
        result["next_check"] = "Choose one technology from each unmet alternative group in game."
    else:
        result["next_check"] = "Prerequisites appear met. Check current research choices in game; a draw is not guaranteed."
    if route_issues:
        result["reason"] = " ".join(sorted(route_issues))
        result["next_check"] = "Route evidence is incomplete. Verify this target and its prerequisites in game."
    _present_route(result, rules, gates, researched, current, options, bool(mods))
    if target in researched:
        result["next_unlocks"] = _next_technologies(
            target, rules, gates, researched, current, options, bool(mods),
            campaign.get("required_dlcs"), save_version)
    result["future_opportunities"] = _future_opportunities(
        target, rules, gates, researched, current, options, bool(mods),
        campaign.get("required_dlcs"), save_version)
    return result


def _future_opportunities(target: str, rules: dict, gates: dict, researched: set[str],
                          current: set[str], options: set[str], mods_active: bool,
                          saved_dlcs: list[str] | None,
                          save_version: str | None = None) -> list[dict]:
    """Trace bounded downstream dependencies; they are possibilities, not research offers."""
    children: dict[str, list[tuple[str, str]]] = {}
    for key, rule in rules.items():
        for parent in rule["prerequisites"]:
            children.setdefault(parent, []).append((key, "direct"))
        for group in rule["one_of"]:
            for parent in group:
                children.setdefault(parent, []).append((key, "one_of"))
    found: dict[str, dict] = {}
    frontier = [(target, [target], "direct")]
    for distance in range(1, 6):
        following = []
        for parent, path, prior_relation in frontier:
            for child, relation in sorted(children.get(parent, [])):
                if child in path or child in found or child not in rules:
                    continue
                chain = path + [child]
                kind = "one_of" if "one_of" in (prior_relation, relation) else "direct"
                rule = rules[child]
                blockers = ["Other prerequisite: " + rules[key]["name"]
                            for key in rule["prerequisites"]
                            if key not in chain and key not in researched and key in rules]
                for group in rule["one_of"]:
                    if not any(key in researched or key in chain for key in group):
                        blockers.append("Choose one of: " + " or ".join(
                            rules[key]["name"] for key in group if key in rules))
                tier = rule["tier"]
                threshold = gates.get(tier) if isinstance(tier, int) and tier > 0 else None
                if threshold is not None and not mods_active:
                    count = sum(key in researched and item.get("area") == rule["area"] and
                                item.get("tier") == tier - 1 for key, item in rules.items())
                    if count < threshold:
                        blockers.append(f"Current Tier {tier} gate: {threshold - count} more previous-tier "
                                        f"{rule['area']} technologies")
                elif mods_active and isinstance(tier, int) and tier > 0:
                    blockers.append("Tier rule may differ with mods; check in game")
                state = ("researched" if child in researched else "researching" if child in current
                         else "saved_option" if child in options else "unmet")
                if state != "unmet":
                    blockers = []  # Observed save state takes precedence over base-game gate inference.
                found[child] = {
                    "id": child, "name": rule["name"], "distance": distance,
                    "path": [{"id": key, "name": rules[key]["name"]} for key in chain],
                    "relation": kind,
                    "blockers": blockers[:5],
                    "state": state,
                    "description": rule["description"], "benefit": rule["benefit"],
                    "dlc": _dlc_status(list(dict.fromkeys(
                        dlc for key in chain for dlc in rules[key]["required_dlc"])),
                        saved_dlcs, save_version),
                    "draw_conditions_unverified": (mods_active or any(
                        rules[key]["draw_conditions_unverified"] for key in chain)),
                }
                following.append((child, chain, kind))
                if len(found) >= 120:
                    break
            if len(found) >= 120:
                break
        frontier = following
        if not frontier or len(found) >= 120:
            break
    return sorted(found.values(), key=lambda item: (item["distance"], item["name"].casefold(), item["id"]))[:36]


def _next_technologies(target: str, rules: dict, gates: dict, researched: set[str],
                       current: set[str], options: set[str], mods_active: bool,
                       saved_dlcs: list[str] | None,
                       save_version: str | None = None) -> list[dict]:
    """Show two dependency links forward, without equating them with a research draw."""
    children: dict[str, list[tuple[str, str]]] = {}
    for key, rule in rules.items():
        for parent in rule["prerequisites"]:
            children.setdefault(parent, []).append((key, "direct"))
        for group in rule["one_of"]:
            for parent in group:
                children.setdefault(parent, []).append((key, "one_of"))

    links: dict[str, tuple[int, str]] = {}
    frontier = [target]
    for distance in (1, 2):
        following = []
        for parent in frontier:
            for child, relation in children.get(parent, []):
                if child == target:
                    continue
                path_relation = ("one_of" if relation == "one_of" or
                                 (distance == 2 and links.get(parent, (0, "direct"))[1] == "one_of")
                                 else "direct")
                previous = links.get(child)
                if previous is None or distance < previous[0] or (
                        distance == previous[0] and path_relation == "direct"):
                    links[child] = (distance, path_relation)
                if distance == 1:
                    following.append(child)
        frontier = following

    items = []
    for key, (distance, relation) in links.items():
        rule = rules[key]
        missing = [parent for parent in rule["prerequisites"] if parent not in researched]
        missing_groups = [group for group in rule["one_of"]
                          if not any(parent in researched for parent in group)]
        tier = rule["tier"]
        threshold = gates.get(tier) if isinstance(tier, int) and tier > 0 else (
            0 if tier == 0 else None)
        count = sum(parent in researched and candidate.get("area") == rule["area"]
                    and candidate.get("tier") == tier - 1
                    for parent, candidate in rules.items()) if isinstance(tier, int) and tier > 0 else 0
        gate = ("unverified" if threshold is None or mods_active else
                "open" if count >= threshold else "closed")
        state = ("researched" if key in researched else "researching" if key in current else
                 "saved_option" if key in options else "unmet")
        items.append({"id": key, "name": rule["name"], "area": rule["area"],
                      "tier": tier, "distance": distance, "relation": relation,
                      "state": state, "missing_prerequisites": missing,
                      "missing_alternative_groups": missing_groups, "tier_gate": gate,
                      "dlc": _dlc_status(rule["required_dlc"], saved_dlcs, save_version),
                      "draw_conditions_unverified": rule["draw_conditions_unverified"] or mods_active,
                      "localized": rule["localized"],
                      "description": rule["description"], "benefit": rule["benefit"]})
    return sorted(items, key=lambda item: (item["distance"], item["name"].casefold(), item["id"]))


def _present_route(result: dict, rules: dict, gates: dict, researched: set[str],
                   current: set[str], options: set[str], mods_active: bool) -> None:
    """Add map and next-step data without treating a possible draw as certain."""
    steps = result["steps"]
    included = {step["id"] for step in steps}
    choices_by_owner: dict[str, list[list[str]]] = {}
    for group in result.get("one_of", []):
        choices_by_owner.setdefault(group["for_id"], []).append(
            [option["id"] for option in group["options"]])
    depths: dict[str, int] = {}
    route_gates: dict[tuple[str, int], dict] = {}
    edges = []
    for step in steps:
        key = step["id"]
        rule = rules.get(key)
        if not rule:
            step.update(area="", tier=None, parents=[], column=0,
                        display_state="Rule not verified", eligibility="unverified")
            continue
        parents = [parent for parent in rule["prerequisites"] if parent in included]
        depths[key] = 1 + max((depths.get(parent, -1) for parent in parents), default=-1)
        for parent in parents:
            edges.append({"from": parent, "to": key})
        tier = rule["tier"]
        gate = None
        if isinstance(tier, int) and tier > 0:
            threshold = gates.get(tier)
            count = sum(candidate in researched and item.get("area") == rule["area"]
                        and item.get("tier") == tier - 1 for candidate, item in rules.items())
            gate = {"area": rule["area"], "tier": tier, "required": threshold,
                    "count": count, "display_count": min(count, threshold) if threshold is not None else count,
                    "state": ("unverified" if threshold is None or mods_active else
                              "open" if count >= threshold else "closed")}
            route_gates[(rule["area"], tier)] = gate
        if key in researched:
            display_state, eligibility = "Researched", "confirmed"
        elif key in current:
            display_state, eligibility = "Researching", "confirmed"
        elif key in options:
            display_state, eligibility = "On your cards", "confirmed"
        elif any(parent not in researched for parent in rule["prerequisites"]):
            display_state, eligibility = "Needs prerequisites", "blocked"
        elif any(not any(choice in researched for choice in group)
                 for group in choices_by_owner.get(key, [])):
            display_state, eligibility = "Choose one prerequisite", "blocked"
        elif gate and gate["state"] == "closed":
            display_state, eligibility = "Tier gate closed", "blocked"
        else:
            display_state, eligibility = "Prerequisites met", "unverified"
        direct_prerequisites = [
            {"id": parent, "name": rules[parent]["name"] if parent in rules else pretty_tech(parent),
             "state": ("researched" if parent in researched else "researching" if parent in current
                       else "saved_option" if parent in options else "unmet")}
            for parent in rule["prerequisites"]]
        step.update(area=rule["area"], tier=tier, parents=parents,
                    direct_prerequisites=direct_prerequisites,
                    column=depths[key], display_state=display_state, eligibility=eligibility,
                    gate=gate, localized=rule["localized"],
                    description=rule["description"], benefit=rule["benefit"],
                    draw_conditions_unverified=rule["draw_conditions_unverified"] or mods_active)
    actions = []
    if result["target_id"] in researched:
        actions.append("Already researched. Explore the next research paths below.")
    elif result["target_id"] in current:
        actions.append(f"Continue researching {result['name']}.")
    elif result["target_id"] in options:
        actions.append("Your goal is on a research card now. Check it in game and choose it when ready.")
    else:
        for step in steps:
            if step["id"] in researched:
                continue
            if step["id"] in options:
                actions.append(f"{step['name']} is on your research cards. Consider it for this route.")
            elif step["id"] in current:
                actions.append(f"Continue researching {step['name']}.")
            elif (step.get("gate") or {}).get("state") == "closed":
                gate = step["gate"]
                missing = gate["required"] - gate["count"]
                actions.append(f"Research {missing} more Tier {gate['tier'] - 1} {gate['area'].title()} technologies to open Tier {gate['tier']}.")
            elif step["display_state"] == "Choose one prerequisite":
                pending = next(group for group in result["one_of"]
                               if group["for_id"] == step["id"] and
                               not any(option["id"] in researched for option in group["options"]))
                names = " or ".join(option["name"] for option in pending["options"])
                actions.append(f"Research one of {names} before {step['name']}; check each option's own conditions in game.")
            else:
                actions.append(f"Work toward {step['name']}; check its availability on your next {step['area'].title()} research draw.")
            if len(actions) == 2:
                break
        if not actions:
            actions.append("All traced prerequisites are complete. Check the goal's in-game research conditions and next draw.")
    map_nodes = list(steps)
    map_edges = list(edges)
    for group in result.get("one_of", []):
        owner = next((step for step in steps if step["id"] == group["for_id"]), None)
        if owner is None:
            continue
        for option in group["options"]:
            key = option["id"]
            if key not in included:
                rule = rules.get(key)
                if rule:
                    state = option["state"]
                    map_nodes.append({"id": key, "name": option["name"], "state": state,
                                      "display_state": ("Researched" if state == "researched" else
                                                        "Researching" if state == "researching" else
                                                        "On your cards" if state == "saved_option" else
                                                        "Alternative to research"),
                                      "eligibility": "confirmed" if state != "unmet" else "unverified",
                                      "area": rule["area"], "tier": rule["tier"], "parents": [],
                                      "direct_prerequisites": [
                                          {"id": parent, "name": rules[parent]["name"] if parent in rules else pretty_tech(parent),
                                           "state": ("researched" if parent in researched else
                                                     "researching" if parent in current else
                                                     "saved_option" if parent in options else "unmet")}
                                          for parent in rule["prerequisites"]],
                                      "column": max(0, owner["column"] - 1), "gate": None,
                                      "localized": rule["localized"], "alternative_for": owner["id"],
                                      "draw_conditions_unverified": True})
                    included.add(key)
            map_edges.append({"from": key, "to": owner["id"], "type": "one_of"})
    result["edges"] = edges
    result["map_edges"] = map_edges
    result["map_nodes"] = map_nodes
    result["route_gates"] = sorted(route_gates.values(), key=lambda gate: (gate["area"], gate["tier"]))
    groups = result.get("one_of", [])
    result["progress"] = {
        "done": sum(step["id"] in researched for step in steps) +
                sum(any(option["id"] in researched for option in group["options"]) for group in groups),
        "total": len(steps) + len(groups)}
    result["next_actions"] = actions


def route_targets(snapshot: dict, game_dir: str) -> list[dict]:
    """Searchable base-game targets; no hidden galaxy or player save data."""
    campaign = snapshot.get("campaign", {})
    if not campaign.get("id") or campaign.get("installed", {}).get("version_match") != "match":
        return []
    rules, _ = installed_rules(game_dir, str(campaign.get("installed", {}).get("version") or ""))
    researched = set(snapshot.get("technology", {}).get("researched", {}))
    branches = snapshot.get("technology", {}).get("branches", {})
    current = {branch.get("current_id") for branch in branches.values()}
    options = {key for branch in branches.values() for key in branch.get("alternative_ids", [])}
    return [{"id": key, "name": rule["name"], "area": rule["area"],
             "tier": rule["tier"], "state": ("researched" if key in researched else
             "researching" if key in current else "saved_option" if key in options else "unmet")}
            for key, rule in sorted(rules.items(), key=lambda entry: (entry[1]["name"], entry[0]))]


def research_overview(snapshot: dict, game_dir: str) -> dict:
    """Labels and tier progress for the three research slots, scoped to one save."""
    campaign = snapshot.get("campaign", {})
    if campaign.get("installed", {}).get("version_match") != "match":
        return {"status": "unverified", "labels": {}, "gates": {}}
    technology = snapshot.get("technology", {})
    if technology.get("researched_status") != "complete":
        return {"status": "unverified", "labels": {}, "gates": {}}
    rules, thresholds = installed_rules(game_dir, str(campaign.get("installed", {}).get("version") or ""))
    if not rules:
        return {"status": "unverified", "labels": {}, "gates": {}}
    researched = set(technology.get("researched", {}))
    labels = {}
    gates = {}
    mods = bool(campaign.get("mods"))
    for area, branch in technology.get("branches", {}).items():
        relevant = [branch.get("current_id"), *(branch.get("alternative_ids") or [])]
        labels.update({key: rules[key]["name"] for key in relevant if key in rules})
        count = sum(key in researched and rule["area"] == area and rule["tier"] == 1
                    for key, rule in rules.items())
        required = thresholds.get(2)
        completed = [rules[key]["name"] for key in researched
                     if key in rules and rules[key]["area"] == area and rules[key]["tier"] == 1]
        candidates = [{"id": key, "name": rules[key]["name"]} for key in branch.get("alternative_ids", [])
                      if key in rules and rules[key]["tier"] == 1]
        gates[area] = {"tier": 2, "count": count, "required": required,
                       "display_count": count,
                       "status": ("unverified" if mods or required is None else
                                  "open" if count >= required else "closed"),
                       "completed": sorted(completed), "on_cards": candidates}
    return {"status": "limited" if mods else "verified_base_game", "labels": labels, "gates": gates}
