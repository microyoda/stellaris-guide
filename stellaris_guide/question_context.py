"""Small, deterministic question router shared by built-in and optional chat."""
from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import re


def _words(value: str) -> str:
    return " ".join(re.findall(r"\w+", value.casefold()))


def _has(text: str, *phrases: str) -> bool:
    return any(re.search(r"(?<!\w)" + re.escape(_words(phrase)).replace(r"\ ", r"\s+") +
                         r"(?!\w)", text) for phrase in phrases)


def _entity(text: str, items: list[dict]) -> tuple[dict | None, bool]:
    """Prefer full-name matches; allow one clear multiword spelling correction."""
    normalized = _words(text)
    records = [(item, _words(str(item.get("name") or ""))) for item in items
               if isinstance(item, dict) and item.get("name")]
    exact = [(item, name) for item, name in records if name and _has(normalized, name)]
    if exact:
        longest = max(len(name) for _, name in exact)
        winners = [item for item, name in exact if len(name) == longest]
        return (winners[0], False) if len(winners) == 1 else (None, True)

    tokens = normalized.split()
    scored: list[tuple[float, dict]] = []
    for item, name in records:
        parts = name.split()
        if len(parts) < 2 or len(tokens) < len(parts):
            continue
        score = max(SequenceMatcher(None, name, " ".join(tokens[i:i + len(parts)])).ratio()
                    for i in range(len(tokens) - len(parts) + 1))
        if score >= 0.87:
            scored.append((score, item))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    if not scored:
        return None, False
    if len(scored) > 1 and scored[0][0] - scored[1][0] < 0.08:
        return None, True
    return scored[0][1], False


@dataclass(frozen=True)
class QuestionContext:
    text: str
    topic: str
    mode: str
    scope: str
    planet: dict | None = None
    contact: dict | None = None
    missing_name: str | None = None
    ambiguous: bool = False
    focus: str | None = None


_NON_COLONY_PHRASES = {
    "my", "the", "our", "this", "that", "a", "an", "your", "overall", "whole", "entire",
    "my overall", "overall economy", "my empire", "the empire", "empire",
    "my colony", "the colony", "my new colony", "new colony", "my colonies",
    "colonies", "all colonies", "my planets", "planets", "all planets", "my worlds", "worlds",
    "the game", "stellaris", "general", "now", "early game", "mid game", "late game", "this save",
    "energy", "energy credits", "minerals", "food", "consumer goods", "alloys",
    "unity", "influence", "trade", "research", "science", "tech", "technology",
    "traditions", "claims", "edicts", "building ships", "my starbases", "starbases",
    "ships", "my ships", "fleet", "my fleet", "fleets", "my fleets", "navy",
    "my navy", "war", "defense", "offense", "economy", "my economy",
}


def _detect_focus(topic: str, words: str) -> str | None:
    if topic == "economy":
        for key, phrases in (
            ("consumer_goods", ("consumer good", "consumer goods")),
            ("alloys", ("alloy", "alloys")),
            ("energy", ("energy", "energy credit", "energy credits")),
            ("minerals", ("mineral", "minerals")),
            ("food", ("food",)),
            ("unity", ("unity",)),
            ("influence", ("influence",)),
        ):
            if _has(words, *phrases):
                return key
    elif topic == "technology":
        for branch in ("physics", "society", "engineering"):
            if _has(words, branch):
                return branch
        if _has(words, "which branch", "weakest branch", "lowest branch", "branch needs"):
            return "branch_compare"
        if _has(words, "increase", "boost", "more research", "more science", "faster research",
                "research output", "science output", "improve research", "improve science"):
            return "research_output"
    elif topic == "ships":
        if _has(words, "starbase cap", "starbase capacity", "more starbases", "starbases", "starbase"):
            return "starbase_capacity"
        if _has(words, "naval capacity", "naval cap", "fleet capacity", "fleet cap"):
            return "naval_capacity"
        if _has(words, "armor", "shield", "shields", "weapon", "weapons", "loadout",
                "configuration", "configure", "config", "equip", "outfit", "fitting",
                "hull", "afterburner", "counter"):
            return "ship_config"
    elif topic == "planet":
        if _has(words, "amenities", "amenity"):
            return "amenities"
        if _has(words, "housing", "overcrowded", "overcrowding"):
            return "housing"
        if _has(words, "stability", "unstable", "revolt", "crime"):
            return "stability"
        if _has(words, "which planet", "which colony", "needs attention", "attention first",
                "worst planet", "worst colony", "fix first"):
            return "attention"
        if _has(words, "what should i build", "what to build", "build on", "districts", "buildings", "jobs"):
            return "build"
    return None


def classify_question(question: str, snapshot: dict) -> QuestionContext:
    text = question.strip()
    if re.match(r"(?i)^/ask(?:\s|$)", text):
        text = re.sub(r"(?i)^/ask\s*", "", text, count=1).strip()
    words = _words(text)
    planet, planet_ambiguous = _entity(text, snapshot.get("planets") or [])
    contact, contact_ambiguous = _entity(text, snapshot.get("contacts") or [])

    # A named place takes precedence over broad words such as "economy".
    if _has(words, "spy", "spies", "spying", "espionage", "infiltration", "intel",
            "intelligence", "spy network", "spy networks", "covert", "operation", "operations",
            "steal technology", "steal tech"):
        topic = "espionage"
    elif _has(words, "ideology", "ideologies", "willpower", "fanatic faction", "fanatic factions",
              "galactic hall", "galactic halls", "tenet", "tenets", "ideological momentum",
              "ideological reach", "force of will"):
        topic = "ideologies"
    elif _has(words, "nomad", "nomads", "arkship", "arkships", "waystation", "waystations",
              "wayline", "waylines", "operational reserves"):
        topic = "nomads"
    elif _has(words, "trade", "storage cap", "storage", "market fee", "overflow", "influence cap"):
        topic = "trade_storage"
    elif _has(words, "policy", "policies", "planetary decision", "planetary decisions"):
        topic = "policy"
    elif _has(words, "population", "populations", "pop growth", "pops", "migration",
              "immigration", "assembly", "grow pops", "grow population"):
        topic = "population"
    elif _has(words, "tech", "technology", "research", "science", "physics", "society", "engineering",
              "which branch", "research branch", "tech branch"):
        topic = "technology"
    elif (_has(words, "alloy", "alloys", "energy", "mineral", "minerals", "food",
               "consumer goods", "consumer good", "unity", "influence")
          and _has(words, "increase", "improve", "boost", "raise", "output", "income", "deficit", "more", "fix")
          and not _has(words, "naval capacity", "naval cap", "fleet capacity", "fleet cap", "starbase", "starbases")):
        topic = "economy"
    elif _has(words, "ship", "ships", "design", "fleet", "fleets", "corvette", "frigate",
              "destroyer", "cruiser", "battleship", "naval capacity", "naval cap",
              "fleet capacity", "fleet cap", "starbase", "starbases",
              "armor", "shield", "shields", "loadout"):
        topic = "ships"
    elif _has(words, "economy", "economic", "resource", "resources", "alloy", "alloys",
              "energy", "mineral", "minerals", "food", "consumer goods", "consumer good",
              "unity", "influence", "income", "deficit", "output", "upkeep"):
        topic = "economy"
    elif _has(words, "attack", "war", "fallen empire", "invade"):
        topic = "war"
    elif _has(words, "worry", "worried", "threat", "danger", "strongest", "rival"):
        topic = "threat"
    elif _has(words, "next move", "next moves", "what should i do", "goal", "goals",
              "prioritize", "priority"):
        topic = "next_move"
    elif _has(words, "planet", "planets", "colony", "colonies", "housing", "amenities",
              "amenity", "stability", "crime", "jobs") or planet:
        topic = "planet"
    elif contact:
        topic = "contact"
    else:
        topic = "unknown"

    mode = "how_to" if _has(words, "how to", "how do i", "how can i", "how do you",
                            "where do i", "steps", "ways to") else (
        "recommendation" if _has(words, "should", "recommend", "best", "improve", "increase",
                                 "boost", "raise", "fix", "more", "which policy", "which policies",
                                 "which branch", "which planet", "which colony", "shall i") else "status")
    scope = "planet" if planet or planet_ambiguous else "contact" if contact or contact_ambiguous else "general"
    focus = _detect_focus(topic, words)
    missing_name = None
    if not planet and not planet_ambiguous and topic in {"planet", "economy", "population", "policy"}:
        match = (re.search(r"\b(?:in|on|at|for)\s+([\w-]+(?:\s+[\w-]+){0,3})\s*[?.!]*$", text, re.I)
                 or re.search(r"\b(?:improve|fix|grow|develop)\s+([\w-]+(?:\s+[\w-]+){0,3}?)\s+(?:economy|population|colony)\b", text, re.I))
        if match and _words(match.group(1)) not in _NON_COLONY_PHRASES:
            missing_name, scope = match.group(1), "planet"
    if not contact and not contact_ambiguous and topic == "espionage":
        match = re.search(r"\b(?:on|from|against)\s+([\w-]+(?:\s+[\w-]+){0,3})\s*[?.!]*$", text, re.I)
        if match and _words(match.group(1)) not in {"other empires", "another empire", "an empire", "the empire", "them"}:
            missing_name, scope = match.group(1), "contact"
    return QuestionContext(text, topic, mode, scope, planet, contact, missing_name,
                           planet_ambiguous or contact_ambiguous, focus)
