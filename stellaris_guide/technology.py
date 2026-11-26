"""Small prerequisite index from the installed game's version-matched files."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re

from .dlcs import parse_release_tuple
from .saves import block, matching_brace, pretty_tech


@lru_cache(maxsize=3)
def definitions(game_dir: str) -> dict[str, tuple[str, ...]]:
    folder = Path(game_dir) / "common" / "technology"
    tree = {}
    if not folder.is_dir():
        return tree
    for path in folder.glob("*.txt"):
        try:
            source = path.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        for match in re.finditer(r"(?m)^(tech_[a-z0-9_]+)\s*=\s*\{", source):
            opening = source.find("{", match.start(), match.end())
            try:
                body = source[opening:matching_brace(source, opening)]
            except ValueError:
                continue
            direct = block(body, "prerequisites")
            tree[match.group(1)] = tuple(dict.fromkeys(re.findall(r"tech_[a-z0-9_]+", direct)))
    return tree


def focus_path(game_dir: str, branch: str, researched: set[str],
               current: str, alternatives: list[str], net: dict,
               profile: dict | None = None, save_version: str = "") -> dict | None:
    tree = definitions(game_dir)
    if not tree:
        return None
    profile = profile or {}
    release = parse_release_tuple(save_version)
    if branch == "engineering":
        if profile.get("is_nomad"):
            candidates = ("tech_arkship_tier_2", "tech_arkship_tier_3", "tech_military_arkship", "tech_destroyers", "tech_cruisers", "tech_battleships")
        elif profile.get("shipset_kind") == "biological":
            candidates = ("tech_stingers", "tech_harbingers", "tech_weavers", "tech_destroyers", "tech_cruisers", "tech_battleships")
        else:
            candidates = ("tech_destroyers", "tech_cruisers", "tech_battleships")
    elif branch == "physics" and net.get("energy", 0) < 20:
        candidates = ("tech_power_plant_2", "tech_power_plant_3", "tech_power_plant_4")
    elif branch == "society":
        soc_candidates: list[str] = []
        if release and release >= (4, 6, 0):
            soc_candidates.append("tech_galactic_administration")
        if profile.get("uses_food", True) and net.get("food", 0) < 10:
            soc_candidates.extend(("tech_hydroponics", "tech_food_processing_1", "tech_food_processing_2"))
        candidates = tuple(soc_candidates) if soc_candidates else tuple(alternatives)
    else:
        candidates = tuple(alternatives)
    target = next((key for key in candidates if key in tree and key not in researched and key != current), None)
    if not target:
        target = next((key for key in alternatives if key in tree and key != current), None)
    if not target:
        return None
    visiting, ordered = set(), []

    def visit(key: str, depth: int) -> None:
        if depth > 4 or key in visiting or key in researched or key not in tree:
            return
        visiting.add(key)
        for previous in tree[key]:
            visit(previous, depth + 1)
        if key not in ordered:
            ordered.append(key)

    visit(target, 0)
    return {"target": pretty_tech(target), "target_id": target,
            "steps": [{"id": key, "name": pretty_tech(key),
                       "visible": key in alternatives or key == current} for key in ordered[-5:]],
            "caveat": "Prerequisites come from installed game files. Research draws, special triggers, DLC and mods may change availability."}
