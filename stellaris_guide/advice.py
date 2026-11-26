"""Plain language recommendations that always work without an AI provider."""

from __future__ import annotations

from .dlcs import has_dlc, parse_release_tuple
from .guide_knowledge import rule_for
from .question_context import QuestionContext, classify_question


def signed(value: float) -> str:
    return f"{value:+.1f}"


def make_advice(snapshot: dict, history: list[dict], plan: dict | None = None) -> dict:
    from .strategy import make_plan
    return make_plan(snapshot, history, plan)


def economy_answer(snapshot: dict) -> str:
    from .strategy import resource_runway

    net = snapshot["player"]["net"]
    keys = ["energy", "minerals", "food", "consumer_goods", "alloys"]
    if "trade" in net and (snapshot["player"].get("net_known") or {}).get("trade", True) is not False:
        keys.append("trade")
    net_known = snapshot["player"].get("net_known") or {}
    unknown_rates = [key for key in keys if key not in net or net_known.get(key, True) is False]
    tracked = [f"{key.replace('_', ' ')} {signed(net[key])}/month" if key not in unknown_rates
               else f"{key.replace('_', ' ')} rate unknown" for key in keys]
    covers = snapshot.get("resource_runway", {})
    deficits = []
    for key in keys:
        if key in unknown_rates or net[key] >= 0:
            continue
        cover = covers.get(key) or resource_runway(snapshot, key)
        label = key.replace("_", " ")
        if cover["status"] == "depleting":
            deficits.append(f"{label}: {cover['stock']:,.1f} stock, about {cover['months']:g} months cover at the saved rate ({cover['urgency']} Guide warning)")
        else:
            deficits.append(f"{label}: stock runway unknown")
    ending = " Deficits: " + "; ".join(deficits) + ". Check the next autosave before spending." if deficits else " No confirmed tracked monthly deficit was recorded."
    if unknown_rates:
        ending += " Some resource rates are unavailable in this save; check them in game."
    return "Your latest monthly balance is " + ", ".join(tracked) + "." + ending


def planet_answer(question: str, snapshot: dict) -> str:
    planets = snapshot.get("planets", [])
    if not planets:
        return "I could not read colony details from this save. Make a new autosave and try again."
    lowered = question.lower()
    selected = next((planet for planet in planets if planet["name"].lower() in lowered), None)
    selected = selected or next((planet for planet in planets if planet["recommendation"]["level"] == "urgent"), None) or planets[0]
    rec = selected["recommendation"]
    return (f"{selected['name']} is a {selected['designation'].lower()} colony with {selected['pops']:.1f} pops, "
            f"{selected['stability']:.0f}% stability, {selected['free_housing']:+.1f} free housing and "
            f"{selected['free_amenities']:+.1f} free amenities. {rec['title']}: {rec['action']} {rec['reason']}")


def tech_answer(snapshot: dict) -> str:
    branches = snapshot.get("technology", {}).get("branches", {})
    if not branches:
        return "I could not read the research queues from this save."
    parts = []
    for name in ("physics", "society", "engineering"):
        branch = branches.get(name, {})
        parts.append(f"{name.title()}: researching {branch.get('current', 'unknown')}; suggested next pick {branch.get('recommendation', 'review options')}")
    return ". ".join(parts) + ". Check each technology's in-game effect before choosing."


def ship_answer(snapshot: dict) -> str:
    rec = snapshot.get("ship_builds", {}).get("recommendation", {})
    if not rec:
        return "I could not read your owned ship designs from this save."
    return f"{rec['title']}. {rec['quantity']}. {rec['reason']} {rec['caveat']}"


def threat_answer(snapshot: dict) -> str:
    contacts = snapshot.get("contacts", [])
    if not contacts:
        return "No contacted empires were readable. Check the in-game diplomacy screen."
    known = [item for item in contacts if item.get("opinion") is not None]
    if not known:
        return "Contacts exist, but their opinions were not readable. Check in-game intel before naming a threat."
    top = min(known, key=lambda item: item["opinion"])
    return (f"Review {top['name']} first: recorded opinion {top['opinion']:+d}. "
            "Check borders, visible naval strength, treaties and intentions in game. "
            "A save can contain foreign power your empire has not discovered.")


def _guide_steps(topic: str, snapshot: dict) -> str:
    card = rule_for(topic, snapshot)
    if not card:
        return "I do not have verified steps for this topic yet. Check the relevant screen in Stellaris."
    steps = " ".join(card["steps"])
    suffix = card["check"]
    if card["applicability"] != "version_checked":
        suffix += " Your game version, DLC or mod rules have not been confirmed against this guide."
    return f"{steps} {suffix}"


def _named_problem(context: QuestionContext) -> str | None:
    if context.ambiguous:
        return "I found more than one possible name in this save. Please choose the exact planet or empire name."
    if context.missing_name:
        kind = "empire" if context.scope == "contact" else "colony"
        article = "an" if kind == "empire" else "a"
        return (f"I could not match {context.missing_name} to {article} {kind} in this selected save. "
                f"Check the selected campaign and use the {kind}'s name as shown in Stellaris.")
    return None


def _population_answer(context: QuestionContext, snapshot: dict) -> str:
    if context.planet is None:
        return "To grow a colony's population: " + _guide_steps("population", snapshot)
    planet = context.planet
    name = planet["name"]
    facts = [f"{name} has {planet['pops']:g} recorded pops"] if isinstance(planet.get("pops"), (int, float)) else [f"{name}'s population was not readable"]
    housing = planet.get("free_housing")
    if isinstance(housing, (int, float)):
        facts.append(f"{housing:+g} free housing")
    return (", ".join(facts) + ". The save does not verify its growth, assembly or migration rate. " +
            _guide_steps("population", snapshot))


def _policy_answer(context: QuestionContext, snapshot: dict) -> str:
    subject = f"For {context.planet['name']}, " if context.planet else ""
    selected = snapshot.get("policies") or {}
    selected_note = (f"The save records {len(selected)} selected empire policies, but cannot prove that "
                     "an alternative is available for you now. ") if isinstance(selected, dict) and selected else ""
    return subject + selected_note + _guide_steps("policy", snapshot)


def _planet_economy_answer(planet: dict, snapshot: dict) -> str:
    def listed(values: object) -> str:
        if not isinstance(values, dict):
            return "not readable"
        shown = [(key.replace("_", " "), value) for key, value in values.items()
                 if isinstance(value, (int, float)) and value > 0]
        return ", ".join(f"{key} {value:g}" for key, value in shown[:5]) or "none recorded"

    name = planet["name"]
    return (f"{name}'s saved local production: {listed(planet.get('produces'))}; "
            f"upkeep: {listed(planet.get('upkeep'))}. This is the colony, not your empire-wide balance. "
            + _guide_steps("planet_economy", snapshot))


def _espionage_answer(context: QuestionContext, snapshot: dict) -> str:
    contact = context.contact
    if not contact and context.mode != "how_to":
        return "Which known empire do you mean? Enter its name from Contacts to check its recorded intel and spy network."
    if contact:
        facts = []
        if contact.get("intel") is not None:
            facts.append(f"recorded intel {contact['intel']:g}" if isinstance(contact["intel"], (int, float)) else "intel recorded")
        facts.append("a spy network is recorded" if contact.get("spy_network") is True else
                     "a spy network is not verified from this save")
        prefix = f"For {contact['name']}, the selected save shows " + "; ".join(facts) + ". "
        if context.mode == "recommendation":
            return (prefix + "Whether an espionage operation is available or worthwhile is not verified by this save. "
                    "Check the target's Espionage screen, operation cost and likely diplomatic consequences in game.")
        if context.mode == "status":
            return prefix + "Check the target's Espionage screen for current operation progress and availability."
    else:
        prefix = "To investigate another empire, "
    return prefix + _guide_steps("espionage", snapshot)


def _nomads_answer(snapshot: dict) -> str:
    nomads = has_dlc(snapshot, "nomads")
    if nomads is False:
        return ("Nomads DLC is not recorded in this save's required_dlcs. "
                "Standard settled-empire colony, starbase, and fleet guidance applies to this campaign.")
    profile = (snapshot.get("player") or {}).get("profile") or {}
    prefix = ("This save shows a Nomadic empire profile. " if profile.get("is_nomad")
              else "Nomads DLC is recorded (or unconfirmed) in this save, though this empire does not look actively Nomadic. ")
    return prefix + _guide_steps("nomads", snapshot)


def _ideologies_answer(snapshot: dict) -> str:
    version = (snapshot.get("campaign") or {}).get("save_version") or snapshot.get("version")
    release = parse_release_tuple(version)
    if release and release < (4, 6, 0):
        return (f"This save is {version}, which predates Stellaris 4.6 Corona Borealis and the Willpower expansion. "
                "Ideologies, Fanatic Factions, and Galactic Halls are not available in 4.5 Cygnus campaigns.")
    willpower = has_dlc(snapshot, "willpower")
    if willpower is False:
        return ("Willpower DLC is not recorded in this save's required_dlcs. "
                "Base-game faction approval and Unity/Stability mechanics apply instead of Willpower Ideologies.")
    return _guide_steps("ideologies", snapshot)


def _trade_storage_answer(snapshot: dict) -> str:
    player = snapshot.get("player") or {}
    net = player.get("net") or {}
    stock = player.get("stock") or {}
    facts = []
    if "trade" in net and (player.get("net_known") or {}).get("trade", True) is not False:
        facts.append(f"monthly trade {signed(net['trade'])}")
    if "trade" in stock and (player.get("stock_known") or {}).get("trade", True) is not False:
        facts.append(f"stored trade {stock['trade']:,.1f}")
    if "influence" in stock and (player.get("stock_known") or {}).get("influence", True) is not False:
        facts.append(f"stored influence {stock['influence']:,.0f}")
    prefix = ("From this save: " + ", ".join(facts) + ". ") if facts else ""
    return prefix + _guide_steps("trade_storage", snapshot)


def answer_question(question: str, snapshot: dict, advice: dict | None = None) -> str:
    context = classify_question(question, snapshot)
    if not context.text:
        return "Type a question about your campaign or a Stellaris mechanic."
    problem = _named_problem(context)
    if problem:
        return problem
    if context.topic == "espionage":
        return _espionage_answer(context, snapshot)
    if context.topic == "ideologies":
        return _ideologies_answer(snapshot)
    if context.topic == "nomads":
        return _nomads_answer(snapshot)
    if context.topic == "trade_storage":
        return _trade_storage_answer(snapshot)
    if context.topic == "policy":
        return _policy_answer(context, snapshot)
    if context.topic == "population":
        return _population_answer(context, snapshot)
    if context.topic == "planet" and context.planet:
        return planet_answer(context.planet["name"], snapshot)
    if context.topic == "planet":
        return "Which colony do you mean? Enter its name, or open Planets to compare your colonies."
    if context.topic == "technology":
        return tech_answer(snapshot)
    if context.topic == "ships":
        return ship_answer(snapshot)
    if context.topic == "economy" and context.planet:
        return _planet_economy_answer(context.planet, snapshot)
    if context.topic == "economy":
        return economy_answer(snapshot)
    if context.topic in ("threat", "contact"):
        return threat_answer(snapshot)
    if context.topic == "war":
        return ("Check visible fleet strength, allies, war goals, border position, reinforcements "
                "and the target's treaties in game. Hidden foreign power in a save and a friendly "
                "opinion cannot establish that an attack is safe.")
    if context.topic == "next_move":
        goals = (advice or {}).get("goals", [])
        if goals:
            return "Your clearest next move is: " + goals[0]["title"] + ". " + goals[0]["detail"]
        return "This selected save has no verified next move yet. Check the Main page after the next autosave."
    return ("I do not have a reliable answer to that question yet. Ask about a named planet, "
            "your economy, research, ships, diplomacy or spying; I will say when a detail is unknown.")
