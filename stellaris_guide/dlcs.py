"""Canonical Stellaris DLC registry, trigger normalization, and base-game rules.

Normalizes save `required_dlcs` labels and Clausewitz script triggers into stable
IDs, recognizes base-game-promoted packs (Utopia, Synthetic Dawn, Humanoids on
4.5+), and detects DLC drift across saves of the same campaign.
"""

from __future__ import annotations

import re


def parse_release_tuple(value: str | None) -> tuple[int, int, int] | None:
    match = re.search(r"(?<!\d)(\d+)\.(\d+)\.(\d+)\b", str(value or ""))
    if not match:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").casefold())


DLC_CATALOG: tuple[dict, ...] = (
    # Promoted to PC base game on 11 May 2026 (4.5 Cygnus baseline).
    {
        "id": "utopia",
        "name": "Utopia",
        "category": "base_included",
        "base_game_since": (4, 5, 0),
        "aliases": ("Utopia",),
        "triggers": ("has_utopia", "has_utopia_dlc"),
    },
    {
        "id": "synthetic_dawn",
        "name": "Synthetic Dawn",
        "category": "base_included",
        "base_game_since": (4, 5, 0),
        "aliases": ("Synthetic Dawn", "Synthetic Dawn Story Pack"),
        "triggers": ("has_synthetic_dawn", "has_synthethic_dawn", "has_synthetic_dawn_dlc"),
    },
    {
        "id": "humanoids",
        "name": "Humanoids Species Pack",
        "category": "base_included",
        "base_game_since": (4, 5, 0),
        "aliases": ("Humanoids Species Pack", "Humanoids"),
        "triggers": ("has_humanoids", "has_humanoids_dlc"),
    },
    # Expansions, Story Packs, and Species Packs.
    {
        "id": "plantoids",
        "name": "Plantoids Species Pack",
        "category": "species_pack",
        "base_game_since": None,
        "aliases": ("Plantoids Species Pack", "Plantoids"),
        "triggers": ("has_plantoids", "has_plantoids_dlc"),
    },
    {
        "id": "leviathans",
        "name": "Leviathans Story Pack",
        "category": "story_pack",
        "base_game_since": None,
        "aliases": ("Leviathans Story Pack", "Leviathans"),
        "triggers": ("has_leviathans", "has_leviathans_dlc"),
    },
    {
        "id": "apocalypse",
        "name": "Apocalypse",
        "category": "expansion",
        "base_game_since": None,
        "aliases": ("Apocalypse",),
        "triggers": ("has_apocalypse", "has_apocalypse_dlc"),
    },
    {
        "id": "distant_stars",
        "name": "Distant Stars Story Pack",
        "category": "story_pack",
        "base_game_since": None,
        "aliases": ("Distant Stars Story Pack", "Distant Stars"),
        "triggers": ("has_distar", "has_distant_stars", "has_distant_stars_dlc"),
    },
    {
        "id": "megacorp",
        "name": "MegaCorp",
        "category": "expansion",
        "base_game_since": None,
        "aliases": ("MegaCorp", "Megacorp"),
        "triggers": ("has_megacorp", "has_megacorp_dlc"),
    },
    {
        "id": "ancient_relics",
        "name": "Ancient Relics Story Pack",
        "category": "story_pack",
        "base_game_since": None,
        "aliases": ("Ancient Relics Story Pack", "Ancient Relics"),
        "triggers": ("has_ancrel", "has_ancient_relics", "has_ancient_relics_dlc"),
    },
    {
        "id": "lithoids",
        "name": "Lithoids Species Pack",
        "category": "species_pack",
        "base_game_since": None,
        "aliases": ("Lithoids Species Pack", "Lithoids"),
        "triggers": ("has_lithoids", "has_lithoids_dlc"),
    },
    {
        "id": "federations",
        "name": "Federations",
        "category": "expansion",
        "base_game_since": None,
        "aliases": ("Federations",),
        "triggers": ("has_federations", "has_federations_dlc"),
    },
    {
        "id": "necroids",
        "name": "Necroids Species Pack",
        "category": "species_pack",
        "base_game_since": None,
        "aliases": ("Necroids Species Pack", "Necroids"),
        "triggers": ("has_necroids", "has_necroids_dlc"),
    },
    {
        "id": "nemesis",
        "name": "Nemesis",
        "category": "expansion",
        "base_game_since": None,
        "aliases": ("Nemesis",),
        "triggers": ("has_nemesis", "has_nemesis_dlc"),
    },
    {
        "id": "aquatics",
        "name": "Aquatics Species Pack",
        "category": "species_pack",
        "base_game_since": None,
        "aliases": ("Aquatics Species Pack", "Aquatics"),
        "triggers": ("has_aquatics", "has_aquatics_dlc"),
    },
    {
        "id": "overlord",
        "name": "Overlord",
        "category": "expansion",
        "base_game_since": None,
        "aliases": ("Overlord",),
        "triggers": ("has_overlord", "has_overlord_dlc"),
    },
    {
        "id": "toxoids",
        "name": "Toxoids Species Pack",
        "category": "species_pack",
        "base_game_since": None,
        "aliases": ("Toxoids Species Pack", "Toxoids"),
        "triggers": ("has_toxoids", "has_toxoids_dlc"),
    },
    {
        "id": "first_contact",
        "name": "First Contact Story Pack",
        "category": "story_pack",
        "base_game_since": None,
        "aliases": ("First Contact Story Pack", "First Contact"),
        "triggers": ("has_first_contact", "has_first_contact_dlc"),
    },
    {
        "id": "galactic_paragons",
        "name": "Galactic Paragons",
        "category": "expansion",
        "base_game_since": None,
        "aliases": ("Galactic Paragons", "Paragons"),
        "triggers": ("has_paragons", "has_galactic_paragons", "has_paragons_dlc", "has_galactic_paragons_dlc"),
    },
    {
        "id": "astral_planes",
        "name": "Astral Planes",
        "category": "expansion",
        "base_game_since": None,
        "aliases": ("Astral Planes",),
        "triggers": ("has_astral_planes", "has_astral_planes_dlc"),
    },
    {
        "id": "machine_age",
        "name": "The Machine Age",
        "category": "expansion",
        "base_game_since": None,
        "aliases": ("The Machine Age", "Machine Age"),
        "triggers": ("has_machine_age", "has_machine_age_dlc"),
    },
    {
        "id": "cosmic_storms",
        "name": "Cosmic Storms",
        "category": "expansion",
        "base_game_since": None,
        "aliases": ("Cosmic Storms",),
        "triggers": ("has_cosmic_storms", "has_cosmic_storms_dlc"),
    },
    {
        "id": "grand_archive",
        "name": "Grand Archive",
        "category": "story_pack",
        "base_game_since": None,
        "aliases": ("Grand Archive", "Grand Archive Story Pack"),
        "triggers": ("has_grand_archive", "has_grand_archive_dlc"),
    },
    {
        "id": "biogenesis",
        "name": "BioGenesis",
        "category": "expansion",
        "base_game_since": None,
        "aliases": ("BioGenesis", "Biogenesis"),
        "triggers": ("has_biogenesis", "has_biogenesis_dlc"),
    },
    {
        "id": "shadows_of_the_shroud",
        "name": "Shadows of the Shroud",
        "category": "story_pack",
        "base_game_since": None,
        "aliases": ("Shadows of the Shroud",),
        "triggers": ("has_shroud_dlc", "has_shadows_of_the_shroud", "has_shadows_of_the_shroud_dlc"),
    },
    {
        "id": "infernals",
        "name": "Infernals Species Pack",
        "category": "species_pack",
        "base_game_since": None,
        "aliases": ("Infernals Species Pack", "Infernals"),
        "triggers": ("has_infernals", "has_infernals_dlc"),
    },
    {
        "id": "nomads",
        "name": "Nomads",
        "category": "expansion",
        "base_game_since": None,
        "aliases": ("Nomads", "Stellaris: Nomads"),
        "triggers": ("has_nomads", "has_nomads_dlc"),
    },
    {
        "id": "willpower",
        "name": "Willpower",
        "category": "expansion",
        "base_game_since": None,
        "aliases": ("Willpower", "Stellaris: Willpower"),
        "triggers": ("has_willpower", "has_willpower_dlc"),
    },
)

DLC_BY_ID: dict[str, dict] = {entry["id"]: entry for entry in DLC_CATALOG}
_ALIAS_TO_ID: dict[str, str] = {}
_TRIGGER_TO_ID: dict[str, str] = {}

for _entry in DLC_CATALOG:
    _ALIAS_TO_ID[_norm(_entry["id"])] = _entry["id"]
    _ALIAS_TO_ID[_norm(_entry["name"])] = _entry["id"]
    for _alias in _entry["aliases"]:
        _ALIAS_TO_ID[_norm(_alias)] = _entry["id"]
    for _trigger in _entry["triggers"]:
        _TRIGGER_TO_ID[_trigger.casefold()] = _entry["id"]
        _ALIAS_TO_ID[_norm(_trigger.removeprefix("has_").removesuffix("_dlc"))] = _entry["id"]

_HOST_DLC_RE = re.compile(r'\b(?:host_has_dlc|local_has_dlc)\s*=\s*"([^"\n]{1,120})"')
_HAS_DLC_SUFFIX_RE = re.compile(r"\b(has_[a-z0-9_]+_dlc)\s*=\s*yes\b")
_KNOWN_TRIGGER_RE = re.compile(
    r"\b(" + "|".join(sorted(_TRIGGER_TO_ID, key=len, reverse=True)) + r")\s*=\s*yes\b"
)


def normalize_dlc_id(value: str) -> str:
    """Resolve a save DLC name, script trigger, or slug to a canonical ID."""
    text = str(value or "").strip()
    lower = text.casefold()
    if lower in _TRIGGER_TO_ID:
        return _TRIGGER_TO_ID[lower]
    key = _norm(text)
    if key in _ALIAS_TO_ID:
        return _ALIAS_TO_ID[key]
    cleaned = re.sub(r"[^a-z0-9]+", "_", lower.removeprefix("has_").removesuffix("_dlc")).strip("_")
    return cleaned or "unknown"


def _strip_comments_and_negated_blocks(script_block: str) -> str:
    """Remove Clausewitz comments and NOT/NOR blocks so excluded DLCs aren't marked required."""
    no_comments = re.sub(r"(?m)#.*$", "", script_block)
    out = []
    pos = 0
    pattern = re.compile(r"\b(?:NOT|NOR)\s*=\s*\{", re.IGNORECASE)
    while pos < len(no_comments):
        match = pattern.search(no_comments, pos)
        if not match:
            out.append(no_comments[pos:])
            break
        out.append(no_comments[pos:match.start()])
        depth = 0
        idx = no_comments.find("{", match.start(), match.end())
        quoted = False
        escaped = False
        while idx < len(no_comments):
            ch = no_comments[idx]
            if quoted:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    quoted = False
            elif ch == '"':
                quoted = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    idx += 1
                    break
            idx += 1
        pos = idx
    return "".join(out)


def dlc_display_name(dlc_id: str) -> str:
    entry = DLC_BY_ID.get(dlc_id)
    if entry:
        return entry["name"]
    return dlc_id.replace("_", " ").strip().title() or "Unknown DLC"


def is_base_game_included(dlc_id: str, save_version: str | None = None) -> bool:
    entry = DLC_BY_ID.get(dlc_id)
    since = entry.get("base_game_since") if entry else None
    if not since:
        return False
    release = parse_release_tuple(save_version)
    # When version is absent, do not assume older pre-4.5 rules; only promote
    # when the release is known to be 4.5.0+.
    return bool(release and release >= since)


def extract_script_dlc_requirements(script_block: str) -> list[str]:
    """Extract canonical DLC IDs from Clausewitz potential/possible blocks."""
    if not script_block:
        return []
    cleaned = _strip_comments_and_negated_blocks(script_block)
    found: list[str] = []
    for raw_name in _HOST_DLC_RE.findall(cleaned):
        found.append(normalize_dlc_id(raw_name))
    for trigger in _KNOWN_TRIGGER_RE.findall(cleaned.casefold()):
        found.append(_TRIGGER_TO_ID[trigger])
    for trigger in _HAS_DLC_SUFFIX_RE.findall(cleaned.casefold()):
        found.append(normalize_dlc_id(trigger))
    return list(dict.fromkeys(item for item in found if item and item != "unknown"))


def active_dlcs(saved_labels: list[str] | None, save_version: str | None = None) -> dict:
    """Summarize active DLCs from a save's `required_dlcs` and version baseline."""
    base_ids = [entry["id"] for entry in DLC_CATALOG
                if is_base_game_included(entry["id"], save_version)]
    if saved_labels is None:
        return {
            "known": False,
            "active_ids": list(base_ids),
            "saved_ids": [],
            "base_included_ids": base_ids,
            "unknown_labels": [],
            "display": [{"id": key, "name": dlc_display_name(key), "source": "base_game"}
                        for key in base_ids],
        }
    saved_ids: list[str] = []
    unknown_labels: list[str] = []
    for raw in saved_labels:
        canonical = normalize_dlc_id(raw)
        if canonical not in DLC_BY_ID:
            unknown_labels.append(str(raw))
        if canonical not in saved_ids:
            saved_ids.append(canonical)
    active_ids = list(dict.fromkeys([*base_ids, *saved_ids]))
    display = []
    for key in active_ids:
        source = "base_game" if key in base_ids and key not in saved_ids else "save"
        display.append({"id": key, "name": dlc_display_name(key), "source": source})
    return {
        "known": True,
        "active_ids": active_ids,
        "saved_ids": saved_ids,
        "base_included_ids": base_ids,
        "unknown_labels": unknown_labels,
        "display": display,
    }


def dlc_status_list(required: list[str], saved_labels: list[str] | None,
                    save_version: str | None = None) -> list[dict]:
    """Evaluate required DLC triggers/IDs against save metadata and base game."""
    summary = active_dlcs(saved_labels, save_version)
    active = set(summary["active_ids"])
    base = set(summary["base_included_ids"])
    result = []
    for raw in required:
        canonical = normalize_dlc_id(raw)
        if canonical in base:
            status = "present"
        elif not summary["known"]:
            status = "unknown"
        elif canonical in active:
            status = "present"
        else:
            status = "not_listed"
        result.append({
            "id": canonical,
            "name": dlc_display_name(canonical),
            "status": status,
            "base_game": canonical in base,
        })
    return result


def has_dlc(snapshot: dict, dlc_id: str) -> bool | None:
    """Return True if active/base-game, False if absent from known save list, else None."""
    canonical = normalize_dlc_id(dlc_id)
    campaign = snapshot.get("campaign") or {}
    version = campaign.get("save_version") or snapshot.get("version")
    if is_base_game_included(canonical, version):
        return True
    saved = campaign.get("required_dlcs")
    if saved is None:
        return None
    summary = active_dlcs(saved, version)
    return canonical in set(summary["active_ids"])


def detect_dlc_drift(snapshot: dict, history: list[dict]) -> dict:
    """Detect whether recorded required_dlcs changed across saves in one campaign."""
    campaign = snapshot.get("campaign") or {}
    campaign_id = campaign.get("id")
    current_labels = campaign.get("required_dlcs")
    if not campaign_id or current_labels is None:
        return {"changed": False, "added": [], "removed": []}
    current_set = {normalize_dlc_id(label) for label in current_labels}
    for previous in reversed(history):
        if previous is snapshot:
            continue
        prior_campaign = previous.get("campaign") or {}
        if prior_campaign.get("id") != campaign_id:
            continue
        prior_labels = prior_campaign.get("required_dlcs")
        if prior_labels is None:
            continue
        prior_set = {normalize_dlc_id(label) for label in prior_labels}
        added = sorted(dlc_display_name(key) for key in current_set - prior_set)
        removed = sorted(dlc_display_name(key) for key in prior_set - current_set)
        return {"changed": bool(added or removed), "added": added, "removed": removed}
    return {"changed": False, "added": [], "removed": []}
