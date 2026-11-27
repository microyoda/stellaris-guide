"""Version-tagged, reviewed guidance for the small built-in question set."""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import re

from .dlcs import active_dlcs, normalize_dlc_id, parse_release_tuple


KNOWLEDGE_FILE = Path(__file__).with_name("guide_knowledge.json")
TOPICS = {
    "espionage", "population", "policy", "planet_economy",
    "trade_storage", "nomads", "ideologies",
    "crisis", "council", "leaders", "subjects", "megastructures", "government",
    "revolt", "automation", "dangerous_tech", "ascension_perks",
}


@lru_cache(maxsize=2)
def load_knowledge(path: Path = KNOWLEDGE_FILE) -> dict[str, dict]:
    cards = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(cards, list) or len(cards) > 100:
        raise ValueError("Guide knowledge must be a bounded list")
    result: dict[str, dict] = {}
    for card in cards:
        if not isinstance(card, dict) or not {"id", "topic", "release", "rule_status", "required_dlc",
                                                  "sources", "steps", "check"} <= card.keys():
            raise ValueError("Incomplete guide knowledge card")
        if (not isinstance(card["topic"], str) or not isinstance(card["id"], str) or
                not isinstance(card["release"], str) or
                card["topic"] not in TOPICS or card["topic"] in result or
                not re.fullmatch(r"[a-z][a-z0-9-]{1,63}", card["id"]) or
                not re.fullmatch(r"\d+\.\d+\.\d+", card["release"]) or
                not isinstance(card["rule_status"], str) or
                card["rule_status"] not in {"verified", "conditional"} or
                not isinstance(card["required_dlc"], list) or
                not all(isinstance(item, str) for item in card["required_dlc"]) or
                not isinstance(card["sources"], list) or not card["sources"] or
                not all(isinstance(item, str) for item in card["sources"]) or
                not isinstance(card["steps"], list) or not 1 <= len(card["steps"]) <= 5 or
                not all(isinstance(step, str) and 1 <= len(step) <= 240 for step in card["steps"]) or
                not isinstance(card["check"], str) or len(card["check"]) > 300):
            raise ValueError("Invalid guide knowledge card")
        result[card["topic"]] = card
    return result


def rule_for(topic: str, snapshot: dict) -> dict | None:
    try:
        card = load_knowledge().get(topic)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None
    if not card:
        return None
    campaign = snapshot.get("campaign") or {}
    installed = campaign.get("installed") or {}
    version_text = str(campaign.get("save_version") or snapshot.get("version") or "")
    release = re.search(r"\d+\.\d+\.\d+", version_text)
    required = {normalize_dlc_id(item) for item in card["required_dlc"]}
    dlc_summary = active_dlcs(campaign.get("required_dlcs"), version_text)
    saved_dlc = set(dlc_summary["active_ids"])
    missing_dlc = sorted(required - saved_dlc)
    min_release = parse_release_tuple(card.get("min_release"))
    save_tuple = parse_release_tuple(version_text)
    release_ok = bool(
        (release and release.group() == card["release"])
        or (min_release and save_tuple and save_tuple >= min_release and save_tuple[:2] == min_release[:2])
    )
    version_matches = bool(
        release_ok
        and installed.get("version_match") == "match"
        and not campaign.get("mods")
        and not missing_dlc
    )
    return {
        **card,
        "missing_dlc": missing_dlc,
        "applicability": "version_checked" if version_matches else "check_in_game",
    }
