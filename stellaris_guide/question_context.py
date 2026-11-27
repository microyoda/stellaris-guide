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


def _damerau_distance(a: str, b: str, limit: int = 2) -> int:
    """Bounded optimal string alignment distance (handles adjacent transpositions as 1 edit)."""
    la, lb = len(a), len(b)
    if abs(la - lb) > limit:
        return limit + 1
    prev2 = list(range(lb + 1))
    prev1 = list(range(lb + 1))
    for i in range(1, la + 1):
        curr = [i] + [0] * lb
        row_min = i
        ai = a[i - 1]
        for j in range(1, lb + 1):
            cost = 0 if ai == b[j - 1] else 1
            best = min(prev1[j] + 1, curr[j - 1] + 1, prev1[j - 1] + cost)
            if i > 1 and j > 1 and ai == b[j - 2] and a[i - 2] == b[j - 1]:
                best = min(best, prev2[j - 2] + 1)
            curr[j] = best
            if best < row_min:
                row_min = best
        if row_min > limit:
            return limit + 1
        prev2, prev1 = prev1, curr
    return prev1[lb]


# Everyday Stellaris player slang and shorthand normalized to canonical routing terms.
_MULTIWORD_SLANG: tuple[tuple[str, str], ...] = (
    ("ring world", "megastructures"),
    ("ascend colony", "colony ascension"),
    ("ascend my colony", "colony ascension"),
    ("ascend planet", "colony ascension"),
    ("ascend my planet", "colony ascension"),
    ("army general", "leaders"),
    ("nav cap", "naval capacity"),
    ("fleet cap", "fleet capacity"),
    ("auto build", "automation"),
    ("civil war", "revolt"),
    ("l gate", "gray tempest"),
    ("ghost signal", "contingency"),
    ("synth queen", "cetana"),
    ("sentry array", "megastructures"),
    ("mega shipyard", "megastructures"),
    ("how am i doing", "benchmark"),
    ("am i behind", "benchmark"),
    ("am i ahead", "benchmark"),
    ("strike craft", "ship loadout"),
    ("galactic market", "trade"),
)

_TOKEN_SLANG: dict[str, str] = {
    "cg": "consumer goods", "cgs": "consumer goods",
    "ec": "energy", "creds": "energy", "credits": "energy", "money": "energy", "cash": "energy",
    "mins": "minerals", "ore": "minerals",
    "starving": "food", "starvation": "food", "farming": "food", "farms": "food",
    "foundry": "alloys", "foundries": "alloys",
    "eco": "economy", "econ": "economy", "budget": "economy",
    "broke": "deficit", "bankrupt": "deficit", "shortage": "deficit", "shortages": "deficit",
    "navcap": "naval capacity", "fleetcap": "fleet capacity",
    "sb": "starbase", "starhold": "starbase", "starfortress": "starbase",
    "anchorage": "naval capacity", "anchorages": "naval capacity",
    "vet": "corvette", "vettes": "corvette", "corvs": "corvette",
    "frig": "frigate", "frigs": "frigate",
    "dd": "destroyer", "dds": "destroyer",
    "bb": "battleship", "bbs": "battleship",
    "torp": "torpedoes", "torps": "torpedoes",
    "warships": "ships", "armada": "fleet", "navy": "fleet",
    "refit": "configure", "loadouts": "loadout", "pd": "flak",
    "ap": "ascension perk", "aps": "ascension perks",
    "autobuild": "automation",
    "riots": "revolt", "rioting": "revolt", "rebel": "revolt", "rebels": "revolt",
    "rebelling": "revolt", "mutiny": "revolt", "separatist": "revolt", "separatists": "revolt",
    "unhappy": "stability", "happiness": "stability", "criminals": "crime", "deviancy": "crime",
    "homeless": "housing", "unemployed": "jobs", "unemployment": "jobs",
    "horde": "great khan", "marauders": "great khan", "lgate": "gray tempest",
    "nanites": "gray tempest",
    "pretorian": "prethoryn", "praetorian": "prethoryn", "prethorin": "prethoryn",
    "subjugate": "vassal", "subjugation": "vassal", "vassalize": "vassal", "vassalise": "vassal",
    "protectorate": "vassal", "subsidiary": "vassal", "feudatory": "vassal",
    "admiral": "leaders", "admirals": "leaders", "generals": "leaders",
    "governor": "leaders", "governors": "leaders",
    "megas": "megastructures", "dyson": "megastructures", "decompressor": "megastructures",
    "catapult": "megastructures", "ringworld": "megastructures",
    "ark": "arkship", "arks": "arkships", "nomadic": "nomads",
    "pacing": "benchmark",
    "sci": "research", "techtree": "technology", "researching": "research", "labs": "research",
    "envoy": "espionage", "envoys": "espionage", "cloaking": "espionage", "infiltrate": "espionage",
    "religion": "ideologies", "religions": "ideologies", "directive": "ideologies",
    "directives": "ideologies", "instinct": "ideologies", "instincts": "ideologies",
    "world": "colony", "worlds": "colonies",
    "boost": "increase", "raise": "increase", "fix": "improve", "prevent": "stop",
}

# Canonical Stellaris vocabulary (>= 5 chars) eligible for safe typo correction.
_CANONICAL_VOCAB: tuple[str, ...] = (
    "espionage", "infiltration", "intelligence", "ideology", "ideologies", "willpower",
    "nomads", "arkship", "arkships", "waystation", "waystations",
    "trade", "storage", "influence", "dangerous", "ascension", "tradition",
    "automation", "automate", "benchmark", "milestone", "milestones",
    "crisis", "crises", "prethoryn", "scourge", "unbidden", "extradimensional",
    "contingency", "cetana", "tempest", "voidworm",
    "council", "councilor", "councilors", "agenda", "agendas", "legitimacy",
    "leader", "leaders", "scientist", "scientists", "commander", "paragon", "paragons",
    "subject", "subjects", "vassal", "vassals", "overlord", "loyalty", "tributary", "bulwark", "scholarium",
    "megastructure", "megastructures", "gateway", "citadel",
    "government", "authority", "reform", "faction", "factions",
    "policy", "policies", "population", "migration", "assembly",
    "technology", "research", "science", "physics", "society", "engineering",
    "corvette", "frigate", "destroyer", "cruiser", "battleship", "titan", "titans",
    "fleet", "fleets", "starbase", "starbases", "naval", "capacity",
    "armor", "shield", "shields", "weapon", "weapons", "loadout", "configuration", "configure",
    "afterburner", "counter", "torpedoes", "missiles", "lasers", "plasma", "kinetic",
    "economy", "economic", "resource", "resources", "energy", "mineral", "minerals",
    "consumer", "goods", "alloy", "alloys", "unity", "deficit", "income", "output", "upkeep",
    "planet", "planets", "colony", "colonies", "housing", "amenities", "stability", "unstable",
    "crime", "revolt", "revolts", "rebellion", "uprising", "unrest", "secession",
    "attack", "invade", "rival", "threat", "worried", "priority", "prioritize",
    "increase", "improve",
)
_CANONICAL_SET = frozenset(_CANONICAL_VOCAB)

_TYPO_STOPWORDS = frozenset({
    "about", "action", "actions", "after", "again", "against", "arbor", "attach",
    "before", "being", "better", "between", "build", "building", "choose", "conquer",
    "conquest", "could", "doing", "during", "early", "earlier", "empire", "empires",
    "enough", "every", "explain", "first", "galaxy", "general", "grade", "guide",
    "having", "helps", "known", "later", "level", "looking", "making", "might",
    "needs", "never", "other", "others", "outpost", "outposts", "place", "plane",
    "plant", "plants", "player", "players", "point", "police", "power", "prime",
    "purple", "quick", "reader", "really", "right", "saved", "should", "since",
    "small", "space", "spend", "start", "starting", "still", "strong", "strongest",
    "system", "systems", "their", "there", "these", "thing", "think", "those",
    "today", "treat", "under", "using", "value", "version", "wants", "where",
    "which", "while", "whose", "worth", "would", "wrong", "years", "yours",
})


def _normalize_player_words(raw_words: str, protected_tokens: set[str]) -> str:
    """Expand player slang and safely correct single-word typos without altering entity names."""
    text = raw_words
    for phrase, replacement in _MULTIWORD_SLANG:
        if phrase in text:
            text = re.sub(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", replacement, text)
    out: list[str] = []
    fuzzy_checks = 0
    for tok in text.split():
        if tok in protected_tokens:
            out.append(tok)
            continue
        if tok in _TOKEN_SLANG:
            out.append(_TOKEN_SLANG[tok])
            continue
        if (len(tok) < 5 or len(tok) > 20 or fuzzy_checks >= 60
                or tok in _CANONICAL_SET or tok in _TYPO_STOPWORDS or tok.isdigit()):
            out.append(tok)
            continue
        fuzzy_checks += 1
        max_edits = 1 if len(tok) <= 7 else 2
        best_dist = max_edits + 1
        best_ratio = 0.0
        best_word = None
        tied = False
        for cand in _CANONICAL_VOCAB:
            if abs(len(tok) - len(cand)) > max_edits:
                continue
            same_first = tok[0] == cand[0]
            first_swapped = tok[0] == cand[1] and tok[1] == cand[0]
            if not same_first and not first_swapped:
                continue
            dist = _damerau_distance(tok, cand, max_edits)
            if dist > max_edits:
                continue
            if dist == 2 and not same_first:
                continue
            ratio = SequenceMatcher(None, tok, cand).ratio()
            min_ratio = 0.78 if dist == 1 else 0.82
            if ratio < min_ratio:
                continue
            if dist < best_dist or (dist == best_dist and ratio > best_ratio + 0.04):
                best_dist = dist
                best_ratio = ratio
                best_word = cand
                tied = False
            elif dist == best_dist and abs(ratio - best_ratio) <= 0.04 and cand != best_word:
                tied = True
        out.append(best_word if best_word and not tied else tok)
    return " ".join(out)


_COLONY_SUFFIX_RE = re.compile(r"\s+(?:prime|ii|iii|iv|v|vi|habitat|station)$", re.I)


def _entity(text: str, items: list[dict], *, allow_suffix_strip: bool = False) -> tuple[dict | None, bool]:
    """Prefer full-name matches; allow suffix-stripped colony names and clear multiword typo corrections."""
    normalized = _words(text)
    records = [(item, _words(str(item.get("name") or ""))) for item in items
               if isinstance(item, dict) and item.get("name")]
    exact = [(item, name) for item, name in records if name and _has(normalized, name)]
    if exact:
        longest = max(len(name) for _, name in exact)
        winners = [item for item, name in exact if len(name) == longest]
        return (winners[0], False) if len(winners) == 1 else (None, True)

    if allow_suffix_strip:
        stripped_exact = []
        for item, name in records:
            base = _COLONY_SUFFIX_RE.sub("", name).strip()
            if base and base != name and len(base.split()) >= 2 and base not in _NON_COLONY_PHRASES and _has(normalized, base):
                stripped_exact.append((item, base))
        if stripped_exact:
            longest = max(len(base) for _, base in stripped_exact)
            winners = [item for item, base in stripped_exact if len(base) == longest]
            return (winners[0], False) if len(winners) == 1 else (None, True)

    tokens = normalized.split()
    scored: list[tuple[float, dict]] = []
    for item, name in records:
        candidates = [name]
        if allow_suffix_strip:
            base = _COLONY_SUFFIX_RE.sub("", name).strip()
            if base and base != name and len(base.split()) >= 2 and base not in _NON_COLONY_PHRASES:
                candidates.append(base)
        best_for_item = 0.0
        for cand in candidates:
            parts = cand.split()
            if len(parts) < 2 or len(tokens) < len(parts):
                continue
            score = max(SequenceMatcher(None, cand, " ".join(tokens[i:i + len(parts)])).ratio()
                        for i in range(len(tokens) - len(parts) + 1))
            if score >= 0.87 and score > best_for_item:
                best_for_item = score
        if best_for_item > 0.0:
            scored.append((best_for_item, item))
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
    "the game", "stellaris", "general", "now", "early", "early game", "earlier game",
    "ealier game", "mid game", "late game", "endgame", "midgame", "this save",
    "beginners", "beginner", "starting out", "new players", "the crisis", "crises",
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
        if _has(words, "titan", "titans", "titan cap", "titan aura", "titan build"):
            return "titan"
        if _has(words, "starbase cap", "starbase capacity", "more starbases", "starbases", "starbase"):
            return "starbase_capacity"
        if _has(words, "naval capacity", "naval cap", "fleet capacity", "fleet cap"):
            return "naval_capacity"
        if _has(words, "armor", "shield", "shields", "weapon", "weapons", "loadout",
                "configuration", "configure", "config", "equip", "outfit", "fitting",
                "hull", "afterburner", "counter", "torpedoes", "missiles", "lasers",
                "plasma", "kinetic", "flak"):
            return "ship_config"
    elif topic == "crisis":
        for key, phrases in (
            ("prethoryn", ("prethoryn", "scourge")),
            ("unbidden", ("unbidden", "extradimensional", "aberrant", "vehement")),
            ("contingency", ("contingency", "sterilization hub")),
            ("cetana", ("cetana", "synthetic queen")),
            ("midgame", ("great khan", "khan", "gray tempest", "tempest", "voidworm", "crystal rift", "formless", "war in heaven")),
        ):
            if _has(words, *phrases):
                return key
    elif topic == "planet":
        if _has(words, "revolt", "revolts", "rebellion", "uprising", "unrest", "secession"):
            return "revolt"
        if _has(words, "amenities", "amenity"):
            return "amenities"
        if _has(words, "housing", "overcrowded", "overcrowding"):
            return "housing"
        if _has(words, "stability", "unstable", "crime"):
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
    raw_words = _words(text)
    planet, planet_ambiguous = _entity(text, snapshot.get("planets") or [], allow_suffix_strip=True)
    contact, contact_ambiguous = _entity(text, snapshot.get("contacts") or [])
    protected_tokens = {
        tok
        for coll in (snapshot.get("planets") or [], snapshot.get("contacts") or [])
        for item in coll if isinstance(item, dict) and item.get("name")
        for tok in _words(str(item["name"])).split()
    }
    words = _normalize_player_words(raw_words, protected_tokens)

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
    elif _has(words, "dangerous tech", "dangerous technology", "dangerous technologies",
              "red tech", "red techs", "machine uprising", "sapient combat", "research restrictions"):
        topic = "dangerous_tech"
    elif (_has(words, "ascension perk", "ascension perks", "ascension path", "ascension", "acension",
               "perk", "perks", "tradition slot", "best tradition", "which tradition",
               "technological ascendancy", "imperial prerogative", "galactic force projection")
          and not _has(words, "colony ascension", "planetary ascension")):
        topic = "ascension_perks"
    elif _has(words, "automation", "automate", "planetary automation", "automation building",
              "optimization building"):
        topic = "automation"
    elif _has(words, "benchmark", "benchmarks", "on track", "milestone", "milestones",
              "campaign stage", "decade target", "where should i be", "year target"):
        topic = "benchmark"
    elif _has(words, "crisis", "crises", "prethoryn", "scourge", "unbidden", "extradimensional",
              "contingency", "cetana", "synthetic queen", "great khan", "gray tempest",
              "voidworm", "war in heaven", "defender of the galaxy"):
        topic = "crisis"
    elif _has(words, "council", "councilor", "councilors", "agenda", "agendas",
              "expand the council", "legitimacy", "minister of defense", "head of research"):
        topic = "council"
    elif _has(words, "leader", "leaders", "leader cap", "leader capacity", "scientist", "scientists",
              "commander", "commanders", "official leader", "officials",
              "statistician", "analyst", "scholar", "paragon", "paragons"):
        topic = "leaders"
    elif _has(words, "subject", "subjects", "vassal", "vassals", "overlord", "loyalty",
              "divided patronage", "tributary", "bulwark", "scholarium", "prospectorium", "satrapy"):
        topic = "subjects"
    elif _has(words, "megastructure", "megastructures", "dyson swarm", "dyson sphere",
              "arc furnace", "matter decompressor", "ring world", "gateway", "gateways",
              "deep space citadel", "deep space citadels", "orbital ring", "quantum catapult"):
        topic = "megastructures"
    elif _has(words, "government", "reform government", "reform my government", "government reform",
              "authority", "change authority", "democratic authority", "oligarchic authority",
              "dictatorial authority", "imperial authority", "corporate authority",
              "faction", "factions", "suppress faction", "promote faction",
              "colony ascension", "planetary ascension"):
        topic = "government"
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
              "destroyer", "cruiser", "battleship", "titan", "titans", "naval capacity", "naval cap",
              "fleet capacity", "fleet cap", "starbase", "starbases",
              "armor", "shield", "shields", "loadout", "torpedoes", "flak", "ship loadout"):
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
              "amenity", "stability", "unstable", "crime", "jobs",
              "revolt", "revolts", "rebellion", "uprising", "unrest", "secession") or planet:
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
