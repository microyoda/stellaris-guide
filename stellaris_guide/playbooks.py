"""Reviewed, version-bound playbook metadata for existing evidence-based goals."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .dlcs import has_dlc, normalize_dlc_id


PLAYBOOK_FILE = Path(__file__).with_name("playbooks.json")
FACTS = {
    "player.net.{resource}",
    "resource_runway.{resource}.status",
    "planet.recommendation.level",
    "planet.stability",
    "planet.free_amenities",
    "player.profile.is_nomad",
    "player.profile.is_gestalt",
    "player.profile.shipset_kind",
    "player.profile.ideology_active",
}
OPS = {"eq", "lt"}
RULE_STATUSES = {"verified", "conditional", "needs recheck", "conflict"}
STRATEGY_STATUSES = {"untested", "tested", "retired"}
DEFICIT_RESOURCES = {"food", "energy", "consumer_goods", "minerals", "alloys", "trade"}


def _validate_condition(condition):
    if not isinstance(condition, dict):
        raise ValueError("Playbook condition must be an object")
    if "any" in condition:
        if set(condition) != {"any"} or not isinstance(condition["any"], list) or not condition["any"]:
            raise ValueError("Invalid playbook alternative conditions")
        for child in condition["any"]:
            _validate_condition(child)
    elif (set(condition) != {"fact", "op", "value"}
          or condition["fact"] not in FACTS or condition["op"] not in OPS):
        raise ValueError("Unsupported playbook fact or operator")


def load_playbooks(path=PLAYBOOK_FILE):
    records = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("Playbooks must be a list")
    seen = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Playbook must be an object")
        required = {"id", "revision", "title", "applies_to", "conditions",
                    "validated_release", "validated_checksum", "rules_status",
                    "strategy_status", "sources", "trade_off", "change_course_if"}
        if not required <= set(record) or record["id"] in seen:
            raise ValueError("Incomplete or duplicate playbook")
        seen.add(record["id"])
        if (not re.fullmatch(r"[a-z][a-z0-9-]+", record["id"])
                or not isinstance(record["revision"], int) or record["revision"] < 1
                or record["applies_to"] not in {"deficit", "colony", "fleet"}
                or not re.fullmatch(r"\d+\.\d+\.\d+", record["validated_release"])
                or not re.fullmatch(r"[A-Za-z0-9]{4}", record["validated_checksum"])
                or record["rules_status"] not in RULE_STATUSES
                or record["strategy_status"] not in STRATEGY_STATUSES
                or not isinstance(record["conditions"], list) or not record["conditions"]
                or not isinstance(record["sources"], list) or not record["sources"]):
            raise ValueError("Invalid playbook metadata")
        if "required_dlcs" in record and (
                not isinstance(record["required_dlcs"], list)
                or not all(isinstance(item, str) for item in record["required_dlcs"])):
            raise ValueError("Invalid playbook DLC requirements")
        if record["applies_to"] == "deficit" and (
                not isinstance(record.get("resources"), list)
                or not set(record["resources"]) <= DEFICIT_RESOURCES):
            raise ValueError("Unsupported playbook resource")
        for condition in record["conditions"]:
            _validate_condition(condition)
    return records


def _read_fact(snapshot, planet, fact, resource):
    parts = fact.replace("{resource}", resource or "").split(".")
    value = planet if parts[0] == "planet" else snapshot.get(parts[0])
    for part in parts[1:]:
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def _condition_state(condition, snapshot, planet, resource):
    if "any" in condition:
        states = [_condition_state(item, snapshot, planet, resource) for item in condition["any"]]
        return True if True in states else None if None in states else False
    value = _read_fact(snapshot, planet, condition["fact"], resource)
    if value is None:
        return None
    if condition["op"] == "eq":
        return value == condition["value"]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value < condition["value"]


def _rules_status(record, snapshot):
    if record["rules_status"] in {"conflict", "needs recheck"}:
        return record["rules_status"]
    campaign = snapshot.get("campaign") or {}
    installed = campaign.get("installed") or {}
    save_release = re.search(r"\d+\.\d+\.\d+", str(campaign.get("save_version") or ""))
    local_release = re.search(r"\d+\.\d+\.\d+", str(installed.get("version") or ""))
    if ((save_release and save_release.group() != record["validated_release"])
            or (local_release and local_release.group() != record["validated_release"])
            or (installed.get("checksum") and installed["checksum"].upper() != record["validated_checksum"].upper())):
        return "needs recheck"
    if (not save_release or not local_release or not installed.get("checksum")
            or campaign.get("mods")):
        return "conditional"
    return record["rules_status"]


def match_playbook(record, snapshot, goal):
    """Return a display record or None; missing facts remain an investigation."""
    if record["strategy_status"] == "retired":
        return None
    prefix, _, subject = goal["key"].partition(":")
    if prefix != record["applies_to"]:
        return None
    if prefix == "deficit" and subject not in record["resources"]:
        return None
    dlc_unknown = False
    required_dlcs = [normalize_dlc_id(item) for item in record.get("required_dlcs") or []]
    for dlc_id in required_dlcs:
        state = has_dlc(snapshot, dlc_id)
        if state is False:
            return None
        if state is None:
            dlc_unknown = True
    planet = None
    if prefix == "colony":
        planet = next((item for item in snapshot.get("planets", [])
                       if str(item.get("id")) == subject), None)
    states = [_condition_state(item, snapshot, planet, subject if prefix == "deficit" else None)
              for item in record["conditions"]]
    if False in states:
        return None
    match = "investigate" if (None in states or dlc_unknown) else "matched"
    result = {
        "id": record["id"], "revision": record["revision"],
        "title": record["title"], "match": match,
        "rules_status": _rules_status(record, snapshot),
        "strategy_status": record["strategy_status"],
        "validated_release": record["validated_release"],
        "sources": record["sources"],
        "trade_off": record["trade_off"],
        "change_course_if": record["change_course_if"],
    }
    if required_dlcs:
        result["required_dlcs"] = required_dlcs
    if record.get("base_game_alternative"):
        result["base_game_alternative"] = record["base_game_alternative"]
    return result
