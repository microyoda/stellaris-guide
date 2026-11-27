"""Small, deterministic question router shared by built-in and optional chat."""
from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import re

from .traditions_data import find_tradition_perk_mentions


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
    ("empire sprawl", "empire size"),
    ("dig site", "archaeological site"),
    ("dig sites", "archaeological site"),
    ("volatile motes", "strategic resources"),
    ("exotic gases", "strategic resources"),
    ("rare crystals", "strategic resources"),
    ("fallen empires", "fallen empire"),
    ("auto generate", "ship designer"),
    ("own ship designs", "ship designer"),
    ("custom ship designs", "ship designer"),
)

_TOKEN_SLANG: dict[str, str] = {
    "cg": "consumer goods", "cgs": "consumer goods",
    "ec": "energy", "creds": "energy", "credits": "energy", "money": "energy", "cash": "energy",
    "mins": "minerals", "ore": "minerals",
    "starving": "food", "starvation": "food", "farming": "food", "farms": "food",
    "foundry": "alloys", "foundries": "alloys",
    "eco": "economy", "econ": "economy", "budget": "economy",
    "broke": "deficit",
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
    "homeless": "housing",
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
    "envoy": "espionage", "envoys": "espionage", "infiltrate": "espionage",
    "fe": "fallen empire", "fes": "fallen empire", "isolist": "isolationist",
    "sprawl": "empire size",
    "religion": "ideologies", "religions": "ideologies", "directive": "ideologies",
    "directives": "ideologies", "instinct": "ideologies", "instincts": "ideologies",
    "world": "colony", "worlds": "colonies",
    "boost": "increase", "raise": "increase", "fix": "improve", "prevent": "stop",
}

# Canonical Stellaris vocabulary (>= 5 chars) eligible for safe typo correction.
_CANONICAL_VOCAB: tuple[str, ...] = (
    "espionage", "infiltration", "intelligence", "ideology", "ideologies", "willpower",
    "nomads", "arkship", "arkships", "waystation", "waystations",
    "trade", "storage", "influence", "dangerous", "ascension", "tradition", "traditions",
    "prosperity", "discovery", "expansion", "supremacy", "statecraft", "aptitude",
    "mercantile", "logistics", "harmony", "synchronicity", "unyielding", "domination",
    "diplomacy", "subterfuge", "adaptability", "enmity", "politics", "versatility",
    "archivism", "domestication", "genetics", "cybernetics", "synthetics", "psionics",
    "ascendancy", "prerogative", "transcendent", "voidborne", "arcology", "ecumenopolis",
    "cosmogenesis", "archaeoengineers",
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
    "planet", "planets", "colony", "colonies", "colonize", "colonizing", "colonization",
    "habitability", "housing", "amenities", "stability", "unstable",
    "construction", "constructor", "constructors",
    "crime", "revolt", "revolts", "rebellion", "uprising", "unrest", "secession",
    "attack", "invade", "rival", "threat", "worried", "priority", "prioritize",
    "increase", "improve",
)
_CANONICAL_SET = frozenset(_CANONICAL_VOCAB)

_TYPO_STOPWORDS = frozenset({
    "about", "action", "actions", "after", "again", "against", "altitude", "amplitude",
    "arbor", "archeology", "archaeology", "archives", "archivist", "attach", "attitude",
    "before", "being", "better", "between", "build", "building",
    "choose", "colonist", "colonists", "conquer", "conquest", "construct", "constructing",
    "constructive", "contractor", "contractors", "could", "diplomat", "diplomats", "discover", "discovered",
    "doing", "dominant", "dominating", "during",
    "early", "earlier", "empire", "empires", "enemy", "enough", "entire", "entity", "every",
    "explain", "first", "galaxy", "general", "genetic", "grade", "guide",
    "having", "helps", "known", "later", "level", "logistic", "looking", "making", "might",
    "needs", "never", "other", "others", "outpost", "outposts", "place", "plane",
    "plant", "plants", "player", "players", "point", "police", "political", "power", "prime",
    "property", "properly", "purple", "quick", "reader", "really", "right", "saved", "should", "since",
    "small", "space", "spend", "start", "starting", "still", "strong", "strongest",
    "synthetic", "system", "systems", "their", "there", "these", "thing", "think", "those",
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
    "my colony", "the colony", "a colony", "my new colony", "new colony", "a new colony",
    "my colonies", "colonies", "all colonies", "new colonies",
    "my planets", "planets", "all planets", "a planet", "my worlds", "worlds",
    "one star system", "a star system", "the star system", "star system", "same system",
    "same star system", "one system", "a system", "the system", "new system", "new systems",
    "another empire", "other empires",
    "minimal losses", "space invasions", "in game terms", "game terms",
    "the game", "stellaris", "general", "now", "early", "early game", "the early game",
    "earlier game", "ealier game", "mid game", "the mid game", "late game", "the late game",
    "endgame", "the endgame", "midgame", "the midgame", "this save",
    "beginners", "beginner", "starting out", "new players", "the crisis", "crises",
    "energy", "energy credits", "minerals", "food", "consumer goods", "alloys",
    "unity", "influence", "trade", "research", "science", "tech", "technology",
    "traditions", "claims", "edicts", "building ships", "my starbases", "starbases",
    "ships", "my ships", "fleet", "my fleet", "fleets", "my fleets", "navy",
    "my navy", "war", "defense", "offense", "economy", "my economy",
}


def _has_tp_context(words: str) -> bool:
    return _has(
        words,
        "tradition", "traditions", "perk", "perks", "ascension", "acension",
        "tree", "trees", "benefit", "benefits", "bonus", "bonuses",
        "worth", "adopt", "finish", "finisher", "opener",
    )


def _detect_focus(topic: str, words: str, tp_mentions: list[tuple[str, str]] | None = None, raw_words: str = "") -> str | None:
    if topic == "ascension_perks":
        if _has(words, "ascension path", "ascension paths", "which ascension path", "best ascension path"):
            return "ascension_paths"
        mentions = tp_mentions if tp_mentions is not None else find_tradition_perk_mentions(words, has_tp_context=_has_tp_context(words), raw_words=raw_words)
        if len(mentions) >= 2:
            return "compare:" + ",".join(f"{kind}:{key}" for kind, key in mentions[:2])
        if len(mentions) == 1:
            kind, key = mentions[0]
            return f"{kind}:{key}"
        if (_has(words, "tradition", "traditions")
                and not _has(words, "perk", "perks", "ascension", "acension")):
            return "traditions_overview"
        if _has(words, "early", "earlier", "ealier", "first", "opener", "starting", "start", "beginning"):
            return "early_game"
        return "general"
    if topic == "economy":
        if _has(words, "strategic resource", "strategic resources", "volatile mote", "exotic gas", "rare crystal"):
            return "strategic_resources"
        if _has(words, "shortage", "shortages", "bankrupt", "bankruptcy", "run out of", "running out of", "out of a resource"):
            return "shortage"
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
    elif topic == "exploration":
        if _has(words, "anomaly", "anomalies"):
            return "anomalies"
        if _has(words, "archaeological", "archaeology", "archeology", "dig site", "dig sites", "excavate", "excavation"):
            return "dig_sites"
        if _has(words, "astral rift", "astral rifts", "astral thread", "astral threads"):
            return "astral_rifts"
        if _has(words, "relic", "relics", "minor artifact", "minor artifacts"):
            return "relics"
        return "route"
    elif topic == "diplomacy_gc":
        if _has(words, "custodian", "galactic emperor", "galactic imperium", "emperor"):
            return "custodian"
        if _has(words, "federation", "federations", "trade league"):
            return "federations"
        if _has(words, "galactic community", "galactic council", "senate", "resolution", "resolutions"):
            return "galactic_community"
        if _has(words, "improve relation", "improve relations", "relations with", "opinion", "trust", "friendly"):
            return "relations"
        return "relations"
    elif topic == "government":
        if _has(words, "colony ascension", "planetary ascension"):
            return "planetary_ascension"
    elif topic == "population":
        if _has(words, "won t generate", "wont generate", "not growing", "not generating", "no pop growth",
                "stopped growing", "stalled growth", "zero growth", "bug where"):
            return "pop_not_growing"
        if _has(words, "resettle", "resettlement", "move pops", "relocate"):
            return "resettlement"
        if _has(words, "robot", "robots", "pop assembly", "assembly", "clone vat", "clone vats"):
            return "pop_assembly"
    elif topic == "technology":
        if _has(words, "mega engineering", "megaengineering"):
            return "mega_engineering"
        if _has(words, "tech tier", "tech tiers", "technology tier", "technology tiers", "tiers work"):
            return "tech_tiers"
        if _has(words, "early game expansion", "early expansion", "prioritize for early", "early tech"):
            return "early_expansion_tech"
        for branch in ("physics", "society", "engineering"):
            if _has(words, branch):
                return branch
        if _has(words, "which branch", "weakest branch", "lowest branch", "branch needs",
                "branch is weakest", "weakest research", "lowest research"):
            return "branch_compare"
        if _has(words, "increase", "boost", "more research", "more science", "faster research",
                "research output", "science output", "improve research", "improve science", "research speed"):
            return "research_output"
    elif topic == "ships":
        if _has(words, "fleet stuck", "stuck in a system", "ships stuck", "fleet is stuck"):
            return "fleet_stuck"
        if _has(words, "ship designer", "own ship", "custom ship", "design ships", "design my own"):
            return "ship_designer"
        if _has(words, "cloaking", "cloak", "cloaked", "stealth fleet"):
            return "cloaking"
        if _has(words, "chokepoint", "choke point", "bastion", "defensive starbase"):
            return "chokepoint_starbase"
        if _has(words, "science ship", "science ships", "survey ship", "survey ships"):
            return "science_ship"
        if _has(words, "construction ship", "construction ships", "constructor", "constructors"):
            return "construction_ship"
        if _has(words, "colony ship", "colony ships"):
            return "colony_ship"
        if _has(words, "titan", "titans", "titan cap", "titan aura", "titan build"):
            return "titan"
        if _has(words, "starbase cap", "starbase capacity", "more starbases", "starbases", "starbase"):
            return "starbase_capacity"
        if _has(words, "naval capacity", "naval cap", "fleet capacity", "fleet cap"):
            return "naval_capacity"
        if _has(words, "corvette", "corvettes") and _has(words, "build", "best", "loadout", "early", "early game", "setup"):
            return "hull_corvette"
        if _has(words, "battleship", "battleships") and _has(words, "build", "best", "loadout", "late", "late game", "setup"):
            return "hull_battleship"
        if _has(words, "cruiser", "cruisers") and _has(words, "build", "best", "loadout", "mid", "setup"):
            return "hull_cruiser"
        if _has(words, "armor", "shield", "shields", "weapon", "weapons", "loadout",
                "configuration", "configure", "config", "equip", "outfit", "fitting",
                "hull", "afterburner", "counter", "torpedoes", "missiles", "lasers",
                "plasma", "kinetic", "flak"):
            return "ship_config"
    elif topic == "war":
        if _has(words, "army", "armies", "planetary invasion", "space invasion", "space invasions",
                "orbital bombardment", "bombardment", "ground combat", "invade planet", "plan a fleet for"):
            return "ground_combat"
        if _has(words, "war exhaustion", "status quo", "win a war", "winning a war", "surrender"):
            return "war_exhaustion"
        if _has(words, "make claims", "make a claim", "claims and declare", "declare war", "war goal", "war goals", "casus belli"):
            return "claims_wargoals"
        if _has(words, "avoid war", "prevent war", "stay peaceful", "without war"):
            return "avoid_war"
        if _has(words, "minimal losses", "counter a", "war tactics", "win battles"):
            return "war_tactics"
    elif topic == "megastructures":
        if _has(words, "hyper relay", "hyper relays", "gateway", "gateways"):
            return "relays_gateways"
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
        if _has(words, "multiple colonies", "one star system", "same star system", "colonies in one"):
            return "multi_colony_system"
        if _has(words, "specialize", "specialization", "designation", "designations", "new colony"):
            return "specialization"
        if _has(words, "unemployed", "unemployment"):
            return "unemployment"
        if _has(words, "crime", "criminal"):
            return "crime"
        if _has(words, "terraform", "terraforming"):
            return "terraforming"
        if _has(words, "habitat", "habitats"):
            return "habitats"
        if _has(words, "colonize", "colonizing", "colonization", "habitability",
                "how many planet", "how many planets", "how many colony", "how many colonies"):
            return "colonize"
        if _has(words, "amenities", "amenity"):
            return "amenities"
        if _has(words, "housing", "overcrowded", "overcrowding"):
            return "housing"
        if _has(words, "stability", "unstable"):
            return "stability"
        if _has(words, "which planet", "which colony", "needs attention", "attention first",
                "worst planet", "worst colony", "fix first"):
            return "attention"
        if _has(words, "what should i build", "what to build", "build on", "districts", "buildings", "jobs"):
            return "build"
    elif topic == "roleplay":
        if _has(words, "ai personality", "ai personalities", "ethos combination", "ethos combinations"):
            return "ai_personalities"
        return "roleplay_starters"
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
    tp_mentions = find_tradition_perk_mentions(words, has_tp_context=_has_tp_context(words), raw_words=raw_words)

    # A named place takes precedence over broad words such as "economy".
    if (_has(words, "more ai personalities", "workshop mod")
            or (_has(words, "mod", "mods")
                and _has(words, "immersion", "improve", "worth", "recommend", "compatible", "good")
                and not _has(raw_words, "gene mod", "gene modding"))):
        topic = "mod_question"
    elif (_has(words, "known issue", "known bug", "bug report", "is this a bug")
          and not _has(words, "population", "pop", "pops", "fleet stuck")):
        topic = "bug_report"
    elif _has(words, "criminal branch", "criminal syndicate", "criminal heritage", "branch office", "branch offices"):
        topic = "criminal_branch"
    elif _has(words, "genocide", "purging", "purge", "slavery", "slaves", "enslave"):
        topic = "slavery_purge"
    elif _has(words, "fallen empire", "awakened empire", "holy world", "holy worlds", "militant isolationist"):
        topic = "fallen_empire"
    elif _has(words, "leviathan", "leviathans", "ether drake", "dimensional horror", "enigmatic fortress"):
        topic = "leviathans"
    elif ((_has(words, "continental", "gaia") or _has(raw_words, "tomb world", "relic world"))
          and _has(raw_words, "world", "worlds", "continental", "gaia", "difference")
          and not _has(words, "terraform", "terraforming")
          and not _has(raw_words, "world shaper")):
        topic = "planet_classes"
    elif _has(words, "empire size", "reduce sprawl", "lower sprawl"):
        topic = "empire_size"
    elif _has(words, "edict", "edicts", "edict fund"):
        topic = "edicts"
    elif _has(words, "spy", "spies", "spying", "espionage", "infiltration", "intel",
            "intelligence", "spy network", "spy networks", "covert", "operation", "operations",
            "steal technology", "steal tech"):
        topic = "espionage"
    elif _has(words, "cloaking", "cloak", "cloaked", "stealth fleet"):
        topic = "ships"
    elif (_has(words, "ideology", "ideologies", "willpower", "fanatic faction", "fanatic factions",
               "galactic hall", "galactic halls", "tenet", "tenets", "ideological momentum",
               "ideological reach")
          or (_has(words, "force of will") and not _has(words, "perk", "perks", "ascension", "benefit", "benefits", "effect", "effects", "give", "gives"))):
        topic = "ideologies"
    elif _has(words, "nomad", "nomads", "arkship", "arkships", "waystation", "waystations",
              "wayline", "waylines", "operational reserves"):
        topic = "nomads"
    elif _has(words, "roleplay", "rp a", "rp campaign", "ai personality", "ai personalities",
              "ethos combination", "ethos combinations"):
        topic = "roleplay"
    elif _has(words, "trade", "storage cap", "storage", "market fee", "overflow", "influence cap") and not _has(words, "trade league"):
        topic = "trade_storage"
    elif _has(words, "dangerous tech", "dangerous technology", "dangerous technologies",
              "red tech", "red techs", "machine uprising", "sapient combat", "research restrictions"):
        topic = "dangerous_tech"
    elif ((tp_mentions
           or _has(words, "ascension perk", "ascension perks", "ascension path", "ascension paths",
                   "ascension", "acension", "perk", "perks", "tradition slot",
                   "best tradition", "which tradition", "next tradition",
                   "my traditions", "what traditions", "tradition tree", "tradition trees",
                   "technological ascendancy", "imperial prerogative", "galactic force projection")
           or (_has(words, "tradition", "traditions") and not _has(words, "unity")))
          and not _has(words, "colony ascension", "planetary ascension")):
        topic = "ascension_perks"
    elif _has(words, "automation", "automate", "planetary automation", "automation building",
              "optimization building"):
        topic = "automation"
    elif _has(words, "benchmark", "benchmarks", "on track", "milestone", "milestones",
              "campaign stage", "decade target", "where should i be", "year target"):
        topic = "benchmark"
    elif _has(words, "crisis", "crises", "prethoryn", "scourge", "unbidden", "extradimensional",
              "contingency", "cetana", "synthetic queen", "great khan", "khan", "gray tempest",
              "tempest", "voidworm", "war in heaven", "defender of the galaxy"):
        topic = "crisis"
    elif _has(words, "latest patch", "patch notes", "new in the latest patch", "new in the patch",
              "nerfs to", "nerf to"):
        topic = "patch_notes"
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
    elif _has(words, "federation", "federations", "trade league", "galactic community", "galactic council",
              "custodian", "galactic emperor", "galactic imperium",
              "improve relations", "improve relation"):
        topic = "diplomacy_gc"
    elif _has(words, "anomaly", "anomalies", "archaeological", "archaeology", "archeology",
              "dig site", "dig sites", "astral rift", "astral rifts", "astral thread",
              "relic", "relics", "minor artifact", "minor artifacts",
              "route for exploration", "efficient route for exploration", "exploration route"):
        topic = "exploration"
    elif _has(words, "megastructure", "megastructures", "dyson swarm", "dyson sphere",
              "arc furnace", "matter decompressor", "ring world", "gateway", "gateways",
              "hyper relay", "hyper relays",
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
              "immigration", "assembly", "grow pops", "grow population",
              "resettle", "resettlement", "robot", "robots", "won t generate", "wont generate"):
        topic = "population"
    elif _has(words, "science ship", "science ships", "survey ship", "survey ships",
              "construction ship", "construction ships", "constructor", "constructors",
              "colony ship", "colony ships", "fleet stuck", "stuck in a system",
              "ship designer", "chokepoint", "choke point"):
        topic = "ships"
    elif _has(words, "army", "armies", "planetary invasion", "space invasion", "space invasions",
              "orbital bombardment", "bombardment", "war exhaustion", "status quo",
              "make claims", "declare war", "avoid war", "win a war", "xenos war"):
        topic = "war"
    elif _has(words, "mega engineering", "megaengineering", "tech tier", "tech tiers",
              "tech", "technology", "research", "science", "physics", "society", "engineering",
              "which branch", "research branch", "tech branch"):
        topic = "technology"
    elif (_has(words, "strategic resource", "strategic resources", "shortage", "shortages",
               "run out of", "running out of", "bankrupt", "bankruptcy")
          or (_has(words, "alloy", "alloys", "energy", "mineral", "minerals", "food",
                   "consumer goods", "consumer good", "unity", "influence")
              and _has(words, "increase", "improve", "boost", "raise", "output", "income", "deficit", "more", "fix")
              and not _has(words, "naval capacity", "naval cap", "fleet capacity", "fleet cap", "starbase", "starbases"))):
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
    elif _has(words, "attack", "war", "invade"):
        topic = "war"
    elif _has(words, "worry", "worried", "threat", "danger", "strongest", "rival"):
        topic = "threat"
    elif _has(words, "next move", "next moves", "what should i do", "goal", "goals",
              "prioritize", "priority"):
        topic = "next_move"
    elif _has(words, "planet", "planets", "colony", "colonies", "colonize", "colonizing",
              "colonization", "habitability", "housing", "amenities",
              "amenity", "stability", "unstable", "crime", "jobs",
              "unemployed", "unemployment", "specialize", "specialization",
              "designation", "designations", "terraform", "terraforming", "habitat", "habitats",
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
    focus = _detect_focus(topic, words, tp_mentions, raw_words)
    missing_name = None
    if not planet and not planet_ambiguous and topic in {"planet", "economy", "population", "policy"}:
        match = (re.search(r"\b(?:in|on|at|for)\s+([\w-]+(?:\s+[\w-]+){0,3})\s*[?.!]*$", text, re.I)
                 or re.search(r"\b(?:improve|fix|grow|develop)\s+([\w-]+(?:\s+[\w-]+){0,3}?)\s+(?:economy|population|colony)\b", text, re.I))
        if match:
            cand = _words(match.group(1))
            stripped = re.sub(r"^(?:a|an|the|one|my|our|your|this|that)\s+", "", cand)
            if cand not in _NON_COLONY_PHRASES and stripped not in _NON_COLONY_PHRASES:
                missing_name, scope = match.group(1), "planet"
    if not contact and not contact_ambiguous and topic == "espionage":
        match = re.search(r"\b(?:on|from|against)\s+([\w-]+(?:\s+[\w-]+){0,3})\s*[?.!]*$", text, re.I)
        if match and _words(match.group(1)) not in {"other empires", "another empire", "an empire", "the empire", "them"}:
            missing_name, scope = match.group(1), "contact"
    return QuestionContext(text, topic, mode, scope, planet, contact, missing_name,
                           planet_ambiguous or contact_ambiguous, focus)
