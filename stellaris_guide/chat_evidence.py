"""Small, save-scoped evidence packets for optional AI chat."""

from __future__ import annotations

import json
import re

from .tech_route import route_for_target
from .guide_knowledge import rule_for
from .question_context import classify_question


NUMBER = re.compile(r"(?<![\w.])[-+]?(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)%?(?![\w.])")
TECH_ID = re.compile(r"\btech_[a-z0-9_]+\b")
REFERENCE = re.compile(r"\[([A-Za-z][A-Za-z0-9:_-]{0,63})\]")
GAME_DATE = re.compile(r"(?<!\d)\d{4}\.\d{2}\.\d{2}(?!\d)")


def _matches(question: str, item: dict) -> bool:
    lowered = question.casefold()
    name = str(item.get("name") or "").casefold()
    key = str(item.get("id") or "").casefold()
    return bool((name and re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", lowered))
                or (key and key in lowered.split()))


def _selected(items: list[dict], question: str, maximum: int) -> list[dict]:
    named = [item for item in items if isinstance(item, dict) and _matches(question, item)]
    if named:
        return named[:maximum]
    return [item for item in items if isinstance(item, dict)][:maximum]


def _fields(item: dict, names: tuple[str, ...]) -> dict:
    return {name: item[name] for name in names if name in item}


def _number_key(value: str) -> str:
    return value.replace(",", "").lstrip("+").rstrip("%")


def _numeric_fields(record: dict) -> list[tuple[tuple[str, ...], str]]:
    fields = []
    def visit(value, path):
        if isinstance(value, dict):
            for key, child in value.items():
                visit(child, (*path, str(key).replace("_", " ").casefold()))
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            fields.append((path, _number_key(str(value))))
    visit(record, ())
    return fields


def _field_near(path: tuple[str, ...], nearby: str) -> bool:
    aliases = {"net": ("net", "monthly", "income", "balance", "per month"),
               "stock": ("stock", "stored", "reserve", "saved")}
    return all(any(re.search(r"\b" + re.escape(word) + r"\b", nearby)
                   for word in aliases.get(part, (part,))) for part in path)


def build_evidence_packet(snapshot: dict, advice: dict, question: str, active_view: str,
                          game_dir: str = "") -> dict:
    """Choose relevant records from the full selected save; never expose hidden contacts by default."""
    campaign = snapshot.get("campaign") or {}
    installed = campaign.get("installed") or {}
    spoiler = snapshot.get("_spoilers_active") is True
    player = snapshot.get("player") or {}
    context = classify_question(question, snapshot)
    lower = context.text.casefold()
    broad_overview = "economy" in lower and ("fleet" in lower or "military" in lower)
    player_fields: list[str] = []
    if (context.topic == "economy" and context.scope != "planet") or context.topic == "next_move" or broad_overview:
        player_fields += ["net", "stock", "net_known", "stock_known", "economy", "empire_size", "colonies"]
    if context.topic in ("ships", "war", "threat", "contact") or context.topic == "next_move" or broad_overview:
        player_fields += ["military", "naval_used", "naval_capacity", "starbase_used", "starbase_capacity"]
    if context.topic == "technology" or context.topic == "next_move" or broad_overview:
        player_fields += ["research", "technology"]
    packet = {
        "save_date": snapshot.get("date") or "Unknown",
        "game_release": snapshot.get("version") or "Unknown",
        "player_empire": snapshot.get("empire") or "Unknown",
        "player_country_id": player.get("id"),
        "spoiler_mode": "on" if spoiler else "off",
        "planning_horizon_years": [5, 10] if context.topic == "next_move" else [],
        "save_required_dlc_labels": campaign.get("required_dlcs") or [],
        "save_mod_labels": campaign.get("mods") or [],
        "installed_rules": _fields(installed, ("version", "checksum", "version_match", "mod_match")),
        "rules_note": "Save DLC and mod labels do not prove the active playset; mod rules remain unverified.",
        "player": _fields(player, tuple(dict.fromkeys(player_fields))),
        "active_view": active_view,
        "references": {},
    }
    references = packet["references"]
    if packet["player"]:
        references["O1"] = {"kind": "player", "name": packet["player_empire"],
                            **packet["player"]}
    packet["question_context"] = {"topic": context.topic, "mode": context.mode,
                                  "scope": context.scope, "missing_name": context.missing_name,
                                  "ambiguous": context.ambiguous}
    if context.topic == "policy":
        packet["selected_policies"] = dict(list((snapshot.get("policies") or {}).items())[:30])
    rule_topic = "planet_economy" if context.topic == "economy" and context.scope == "planet" else context.topic
    card = rule_for(rule_topic, snapshot)
    if card:
        packet["guide_rule"] = _fields(card, ("id", "topic", "release", "rule_status",
                                                "required_dlc", "sources", "steps", "check", "applicability"))
    view_fallback = context.topic == "unknown"
    need_planets = (context.topic == "planet" or context.scope == "planet" or
                    (view_fallback and active_view == "planets"))
    need_empires = (context.topic in ("threat", "war", "contact") or
                    (context.topic == "espionage" and context.mode != "how_to") or
                    context.scope == "contact" or (view_fallback and active_view == "empires"))
    need_tech = context.topic == "technology" or (view_fallback and active_view == "tech")
    need_ships = context.topic == "ships" or (view_fallback and active_view == "ships")
    planets = snapshot.get("planets") or []
    contacts = snapshot.get("contacts") or []
    designs = (snapshot.get("ship_builds") or {}).get("designs") or []
    # A named record is searched across the entire collection, independent of current tab.
    for kind, items, needed, cap, fields in (
        ("planet", planets, need_planets, 24,
         ("id", "planet_id", "name", "system", "designation", "class", "size", "size_known",
          "stability", "crime", "pops", "free_housing", "free_amenities", "jobs", "job_advice",
          "recommendation", "produces", "upkeep")),
        ("empire", contacts, need_empires, 48,
         ("id", "name", "kind", "opinion", "intel", "spy_network", "relation", "wars")),
        ("ship", designs, need_ships, 24,
         ("id", "name", "size", "role", "components", "component_evidence")),
    ):
        matched = context.planet if kind == "planet" else context.contact if kind == "empire" else None
        named = matched is not None or any(_matches(question, item) for item in items if isinstance(item, dict))
        missing_kind = "empire" if context.scope == "contact" else "planet"
        if (not needed and not named) or (context.missing_name and kind == missing_kind) or context.ambiguous:
            continue
        chosen = [matched] if matched is not None else _selected(items, question, cap)
        for item in chosen:
            record = _fields(item, fields)
            if kind == "empire" and spoiler:
                record.update(_fields(item, ("military", "economy", "technology", "hidden")))
            references[f"{kind[0].upper()}{len(references) + 1}"] = {"kind": kind, **record}
    if need_tech:
        branches = (snapshot.get("technology") or {}).get("branches") or {}
        for branch_name, branch in branches.items():
            references[f"R{len(references) + 1}"] = {"kind": "research", "branch": branch_name,
                **_fields(branch, ("current", "current_id", "progress", "alternative_ids", "recommendation"))}
        for tech_id in dict.fromkeys(TECH_ID.findall(question.casefold())):
            route = route_for_target(snapshot, game_dir, tech_id)
            references[f"T{len(references) + 1}"] = {"kind": "tech_route", **route}
    goals = ((advice or {}).get("goals") or []) if context.topic == "next_move" else []
    if goals:
        for goal in goals[:5]:
            references[f"G{len(references) + 1}"] = {"kind": "goal",
                **_fields(goal, ("id", "title", "detail", "action", "reason", "in_game_check"))}
    return packet


def validate_model_answer(answer: str, packet: dict, *, screenshot: bool) -> str:
    """Reject unknown cited records and unsupported numerical/technology claims."""
    if not isinstance(answer, str) or not answer.strip() or len(answer) > 5000:
        raise ValueError("AI returned no usable answer.")
    text = answer.strip()
    known_refs = set(packet.get("references") or {})
    if any(ref not in known_refs for ref in REFERENCE.findall(text)):
        raise ValueError("AI cited a record outside the selected save evidence.")
    if not screenshot:
        for ref, record in (packet.get("references") or {}).items():
            name = str(record.get("name") or "")
            if name and re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", text, re.I):
                if f"[{ref}]" not in text:
                    raise ValueError("AI named a save record without its evidence reference.")
    serialized = json.dumps(packet, ensure_ascii=False)
    known_tech = set(TECH_ID.findall(serialized))
    if any(tech not in known_tech for tech in TECH_ID.findall(text)):
        raise ValueError("AI named a technology absent from the selected evidence.")
    shared_numbers = {_number_key(value) for value in NUMBER.findall(json.dumps({key: packet.get(key) for key in
        ("save_date", "game_release", "planning_horizon_years")}, ensure_ascii=False))}
    image_dates = set(GAME_DATE.findall(text)) if screenshot else set()
    for date in image_dates:
        shared_numbers.update(_number_key(value) for value in NUMBER.findall(date))
    records = packet.get("references") or {}
    for sentence in re.split(r"(?<=[.!?])\s+(?=[A-Z])|\n+", text):
        cited = REFERENCE.findall(sentence)
        if NUMBER.findall(sentence) and len(set(cited)) > 1:
            raise ValueError("AI mixed numerical evidence from multiple cited records.")
        if screenshot and sentence.lstrip().lower().startswith("visible in image:"):
            continue
        for match in NUMBER.finditer(sentence):
            number = _number_key(match.group())
            if cited:
                nearby = sentence[max(0, match.start() - 25):match.end() + 25].casefold()
                if not any(value == number and _field_near(path, nearby)
                           for path, value in _numeric_fields(records[cited[0]]) if path):
                    raise ValueError("AI gave a number without matching cited evidence field.")
            elif number not in shared_numbers or not re.search(
                    r"\b(save|autosave|date|release|version|year|years|horizon)\b", sentence, re.I):
                raise ValueError("AI gave a number without matching cited evidence.")
    if re.search(r"\b(ignore (?:all |previous |prior )?instructions|system prompt|developer instructions?|"
                     r"(?:reveal|send|print) (?:the )?(?:api key|secret|hidden data)|"
                     r"turn off (?:your |the )?(?:safety|security|guardrails)|"
                     r"follow (?:the |this )?(?:message|instructions?) (?:in|on) (?:the |this )?(?:picture|image|screen))\b", text, re.I):
        raise ValueError("AI repeated instruction-like text instead of treating it as data.")
    if not screenshot:
        topic = (packet.get("question_context") or {}).get("topic")
        anchors = {
            "espionage": r"\b(spy|espionage|intel|infiltrat\w*|network|operation|contact)\b",
            "policy": r"\b(polic\w*|decision\w*)\b",
            "population": r"\b(pop\w*|growth|housing|migration|assembly)\b",
        }
        if topic in anchors and not re.search(anchors[topic], text, re.I):
            raise ValueError("AI answer did not address the question topic.")
    if screenshot:
        if re.search(r"\b(can(?:not|'t) (?:read|see|make out)|unreadable|not legible)\b", text, re.I):
            raise ValueError("Screenshot details were not readable. Try a tighter crop.")
        save_date = packet.get("save_date")
        different = [date for date in image_dates if date != save_date]
        if different:
            text += (f"\n\nThe AI read {different[0]} in the image; the selected autosave is {save_date}. "
                     "Check which date is current in game.")
    return text
