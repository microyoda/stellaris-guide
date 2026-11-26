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
    elif _has(words, "tech", "technology", "research", "physics", "society", "engineering"):
        topic = "technology"
    elif _has(words, "ship", "ships", "design", "fleet", "fleets", "corvette", "frigate",
              "destroyer", "cruiser", "battleship"):
        topic = "ships"
    elif _has(words, "economy", "economic", "resource", "resources", "alloy", "alloys",
              "energy", "mineral", "minerals", "food", "consumer goods", "income", "deficit"):
        topic = "economy"
    elif _has(words, "attack", "war", "fallen empire", "invade"):
        topic = "war"
    elif _has(words, "worry", "worried", "threat", "danger", "strongest", "rival"):
        topic = "threat"
    elif _has(words, "next move", "next moves", "what should i do", "goal", "goals",
              "prioritize", "priority"):
        topic = "next_move"
    elif _has(words, "planet", "colony", "housing", "amenities", "amenity", "stability", "jobs") or planet:
        topic = "planet"
    elif contact:
        topic = "contact"
    else:
        topic = "unknown"

    mode = "recommendation" if _has(words, "should", "recommend", "best", "improve", "increase",
                                     "which policy", "which policies", "shall i") else (
        "how_to" if _has(words, "how to", "how do i", "where do i", "steps") else "status")
    scope = "planet" if planet or planet_ambiguous else "contact" if contact or contact_ambiguous else "general"
    missing_name = None
    if not planet and not planet_ambiguous and topic in {"planet", "economy", "population", "policy"}:
        match = (re.search(r"\b(?:in|on|at|for)\s+([\w-]+(?:\s+[\w-]+){0,3})\s*[?.!]*$", text, re.I)
                 or re.search(r"\b(?:improve|fix|grow|develop)\s+([\w-]+(?:\s+[\w-]+){0,3}?)\s+(?:economy|population|colony)\b", text, re.I))
        if match and _words(match.group(1)) not in {"my empire", "the empire", "my colony", "the game", "stellaris"}:
            missing_name, scope = match.group(1), "planet"
    if not contact and not contact_ambiguous and topic == "espionage":
        match = re.search(r"\b(?:on|from|against)\s+([\w-]+(?:\s+[\w-]+){0,3})\s*[?.!]*$", text, re.I)
        if match and _words(match.group(1)) not in {"other empires", "another empire", "an empire", "the empire", "them"}:
            missing_name, scope = match.group(1), "contact"
    return QuestionContext(text, topic, mode, scope, planet, contact, missing_name,
                           planet_ambiguous or contact_ambiguous)
