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


def _num(value: object) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def _fmt_metric(value: object, fmt: str, suffix: str = "") -> str:
    parsed = _num(value)
    return f"{format(parsed, fmt)}{suffix}" if parsed is not None else "unknown"


def _planet_resource_summary(snapshot: dict, resource: str) -> str:
    planets = snapshot.get("planets") or []
    producers = []
    drains = []
    for p in planets:
        if not isinstance(p, dict) or not p.get("name"):
            continue
        prod = _num((p.get("produces") or {}).get(resource)) if isinstance(p.get("produces"), dict) else None
        if prod is not None and prod > 0:
            producers.append((prod, p["name"]))
        upkeep = _num((p.get("upkeep") or {}).get(resource)) if isinstance(p.get("upkeep"), dict) else None
        if upkeep is not None and upkeep > 0:
            drains.append((upkeep, p["name"]))
    parts = []
    if producers:
        producers.sort(reverse=True)
        top = ", ".join(f"{name} ({val:g})" for val, name in producers[:2])
        parts.append(f"Top saved colony output: {top}")
    if drains:
        drains.sort(reverse=True)
        top = ", ".join(f"{name} ({val:g})" for val, name in drains[:2])
        parts.append(f"largest colony upkeep: {top}")
    return (". ".join(parts) + ". ") if parts else ""


def _resource_levers(resource: str, snapshot: dict) -> str:
    player = snapshot.get("player") or {}
    profile = player.get("profile") or {}
    policies = snapshot.get("policies") or {}
    is_gestalt = bool(profile.get("is_gestalt"))
    is_machine = bool(profile.get("is_machine"))
    is_nomad = bool(profile.get("is_nomad"))
    net = player.get("net") or {}
    net_known = player.get("net_known") or {}

    if resource == "energy":
        notes = []
        sb_used = _num(player.get("starbase_used"))
        sb_cap = _num(player.get("starbase_capacity"))
        if sb_used is not None and sb_cap is not None and sb_cap > 0 and sb_used > sb_cap:
            notes.append(f"You are over starbase capacity ({sb_used:g}/{sb_cap:g}), which adds a steep Energy upkeep penalty—downgrade excess starbases first.")
        if is_nomad:
            notes.append("Expand Arkship energy modules and Wayline/Waystation coverage, and trim idle fleet/module upkeep.")
        elif is_gestalt:
            notes.append("Build Generator Districts (Technician Drones) on a Generator-designated world with open housing, add Energy Grids when researched, and prioritize Technician jobs before adding more districts.")
        else:
            notes.append("Build Generator Districts (Technician jobs) on a Generator-designated colony with available pops, add an Energy Grid when unlocked, and check whether Trade surplus or excess Market fees are distorting your monthly flow.")
        notes.append("Also check Energy upkeep drains (undocked fleets away from Crew Quarters starbases, unused districts/buildings, active edicts) and consider Capacity Subsidies or energy-output techs.")
        return " ".join(notes)

    if resource == "minerals":
        if is_nomad:
            return ("Prioritize rich mineral systems along your Waylines and Waystations, and check Arkship alloy/industrial upkeep before expanding.")
        worker = "Mining Drones" if is_gestalt else "Miner jobs"
        return (f"Build Mining Districts ({worker}) on a Mining-designated world with pops ready to fill them, build orbital mining stations in owned systems, "
                "and add a Mineral Purification Plant when unlocked. Watch Forge and Factory mineral upkeep before queueing more industrial districts.")

    if resource == "food":
        if profile.get("uses_food") is False:
            return ("This Machine empire profile normally has little or no Food demand unless feeding bio-trophies, livestock, catalytic jobs, or biological ships. "
                    "Verify actual Food upkeep in game before building Agriculture districts.")
        if is_nomad:
            return ("Add Arkship food/hydroponics modules or harvest food-rich systems along your Waylines, and check crew or biological ship upkeep in game.")
        worker = "Agri-Drones" if is_gestalt else "Farmer jobs"
        return (f"Add Hydroponics Bays to starbases for pop-free Food, or build Agriculture Districts ({worker}) on an Agri-World with open pops. "
                "Check pop, catalytic, or biological ship upkeep if Food is dropping quickly.")

    if resource == "consumer_goods":
        if is_gestalt and profile.get("uses_consumer_goods") is not True:
            return ("Most Gestalt empires do not normally use Consumer Goods (exceptions include Rogue Servitors or Obsessional Directive). "
                    "Verify in game whether this empire actually has Consumer Goods upkeep before building industrial jobs.")
        worker = "Artisan Drones" if is_gestalt else "Artisan jobs"
        econ_policy = policies.get("economic_policy")
        policy_note = f" Saved economic policy is {str(econ_policy).replace('_', ' ')}." if econ_policy else ""
        return (f"Designate a Factory World and fill {worker} (Industrial/Factory districts and Civilian Industries), or pause new Research Labs/Unity buildings until your monthly balance is positive.{policy_note} "
                "You can also review your Economic Policy (Civilian vs Mixed vs Militarized Economy) and Trade Policy in game.")

    if resource == "alloys":
        mineral_val = _num(net.get("minerals")) if net_known.get("minerals", True) is not False else None
        mineral_note = (f" Saved Minerals net is {signed(mineral_val)}/month—make sure Mineral income stays positive to feed new foundries."
                        if mineral_val is not None else "")
        if is_nomad:
            return (f"Upgrade Arkship alloy/foundry modules and connect mineral-rich Waystations before queueing more ships.{mineral_note} "
                    "Check fleet upkeep and Nomad policies in game.")
        worker = "Fabricators" if is_machine else ("Foundry Drones" if is_gestalt else "Metallurgist jobs")
        econ_policy = policies.get("economic_policy")
        policy_note = f" Saved economic policy is {str(econ_policy).replace('_', ' ')}." if econ_policy else ""
        return (f"Specialize a Forge World with Industrial/Forge districts and Alloy Foundries ({worker}) where pops are available.{mineral_note}{policy_note} "
                "Check Economic Policy (Militarized vs Mixed Economy) and ship upkeep in game before expanding.")

    if resource == "trade":
        if is_nomad:
            return ("Connect Waystations along active Waylines, cut unnecessary recurring Market purchases (base 30% Market fee), and watch logistics upkeep across Arkships.")
        worker = "Logistics Drones" if is_gestalt else "Trader / Commercial jobs"
        return (f"Add {worker} on a Trade-focused colony, reduce local planet resource deficits that consume logistics Trade, "
                "and pause recurring Market purchases (base Market fee starts at 30%) until monthly Trade is positive.")

    if resource == "unity":
        size = _num(player.get("empire_size"))
        size_note = f" Saved Empire Size is {size:g}, which increases Tradition and Edict costs." if size is not None else ""
        worker = "Coordinator or Synapse Drone jobs" if is_gestalt else "Bureaucrat or Priest jobs"
        return (f"Build a dedicated Unification colony with {worker} and keep Faction approval (or Gestalt Directives / Willpower Ideologies if active) healthy.{size_note} "
                "Review active Edicts if Unity upkeep is eating your surplus.")

    if resource == "influence":
        return ("Influence mainly comes from Power Projection (fleet size relative to naval cap), Rivals, Protectorates/Vassals, and certain councilor/event bonuses—and is drained by diplomatic pacts, claims, expansion, and Ideology upkeep. "
                "Cancel unnecessary diplomatic pacts, keep a standing fleet for Power Projection, and watch the 1,000 base storage cap so surplus Influence is not wasted.")

    return "Check your largest deficits, open jobs, and colony designations in game before queueing new districts."


def _resource_answer(resource: str, snapshot: dict, mode: str) -> str:
    from .strategy import resource_runway

    player = snapshot.get("player") or {}
    net = player.get("net") or {}
    stock = player.get("stock") or {}
    net_known = player.get("net_known") or {}
    stock_known = player.get("stock_known") or {}
    label = resource.replace("_", " ")

    facts = []
    net_val = _num(net.get(resource)) if net_known.get(resource, True) is not False else None
    stock_val = _num(stock.get(resource)) if stock_known.get(resource, True) is not False else None
    if net_val is not None:
        facts.append(f"{signed(net_val)}/month")
    else:
        facts.append("monthly rate unknown in this save")
    if stock_val is not None:
        facts.append(f"{stock_val:,.1f} stored")
    if net_val is not None and net_val < 0:
        cover = (snapshot.get("resource_runway") or {}).get(resource) or resource_runway(snapshot, resource)
        if cover.get("status") == "depleting":
            facts.append(f"about {cover['months']:g} months cover ({cover['urgency']} Guide warning)")
    header = f"Saved {label}: " + ", ".join(facts) + ". "
    colony_note = _planet_resource_summary(snapshot, resource)
    if mode == "status":
        return header + colony_note + "Ask how to increase it for specific levers, or check the Economy tooltip in game for modifier breakdowns."
    return header + colony_note + _resource_levers(resource, snapshot) + " Confirm available district slots, open jobs, and active policies in game before building."


def economy_answer(snapshot: dict, context: QuestionContext | None = None) -> str:
    from .strategy import resource_runway

    if context and context.focus:
        return _resource_answer(context.focus, snapshot, context.mode)

    net = snapshot["player"]["net"]
    keys = ["energy", "minerals", "food", "consumer_goods", "alloys"]
    if "trade" in net and (snapshot["player"].get("net_known") or {}).get("trade", True) is not False:
        keys.append("trade")
    net_known = snapshot["player"].get("net_known") or {}
    unknown_rates = [key for key in keys if _num(net.get(key)) is None or net_known.get(key, True) is False]

    if context and context.mode in ("how_to", "recommendation"):
        deficits = [key for key in keys if key not in unknown_rates and net[key] < 0]
        if deficits:
            worst = min(deficits, key=lambda key: net[key])
            return (f"Start by fixing your biggest saved deficit ({worst.replace('_', ' ')} {signed(net[worst])}/month). "
                    + _resource_answer(worst, snapshot, "how_to"))
        urgent = [p for p in snapshot.get("planets", []) if (p.get("recommendation") or {}).get("level") == "urgent"]
        if urgent:
            col = urgent[0]
            stab = _fmt_metric(col.get("stability"), ".0f", "%")
            amen = _fmt_metric(col.get("free_amenities"), "+.1f")
            min_note = (f" ({signed(net['minerals'])}/month)"
                        if "minerals" not in unknown_rates else "")
            return (f"No tracked monthly deficit is recorded, so stabilize {col['name']} first ({stab} stability, "
                    f"{amen} free amenities) to protect colony output, then convert surplus Minerals{min_note} "
                    "into Alloys or Research. Ask about a specific resource (e.g. energy or alloys) for targeted steps.")
        return ("No tracked monthly deficit is recorded. Specialize colonies by designation (Generator, Mining, Forge, Factory, Tech-World), "
                "avoid building districts ahead of available pops, and keep Trade positive. Ask about a specific resource (e.g. energy, minerals, alloys, consumer goods, unity) for targeted steps.")

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
    return (f"{selected['name']} is a {str(selected.get('designation') or 'colony').lower()} colony with "
            f"{_fmt_metric(selected.get('pops'), '.1f')} pops, {_fmt_metric(selected.get('stability'), '.0f', '%')} stability, "
            f"{_fmt_metric(selected.get('free_housing'), '+.1f')} free housing and "
            f"{_fmt_metric(selected.get('free_amenities'), '+.1f')} free amenities. {rec['title']}: {rec['action']} {rec['reason']}")


def _general_planet_answer(context: QuestionContext, snapshot: dict) -> str:
    planets = [p for p in (snapshot.get("planets") or []) if isinstance(p, dict) and p.get("name")]
    if not planets:
        return "I could not read colony details from this save. Make a new autosave and try again."
    focus = context.focus
    if focus == "amenities":
        low = sorted([p for p in planets if (_num(p.get("free_amenities")) or 0) < 0],
                     key=lambda p: _num(p.get("free_amenities")) or 0)
        if not low:
            return "No saved colony currently shows negative free amenities. Check in-game colony tooltips after the next autosave if stability drops."
        listed = "; ".join(
            f"{p['name']} ({_fmt_metric(p.get('free_amenities'), '+.1f')} amenities, {_fmt_metric(p.get('stability'), '.0f', '%')} stability)"
            for p in low[:3]
        )
        return (f"Saved colonies with an amenities deficit: {listed}. "
                "Check open Entertainer or Maintenance Drone jobs first, or add a Holo-Theatre / amenities source before expanding further.")
    if focus == "housing":
        low = sorted([p for p in planets if (_num(p.get("free_housing")) or 0) < 0],
                     key=lambda p: _num(p.get("free_housing")) or 0)
        if not low:
            return "No saved colony currently shows negative free housing. Check individual colony tabs before resettling more pops."
        listed = "; ".join(f"{p['name']} ({_fmt_metric(p.get('free_housing'), '+.1f')} free housing)" for p in low[:3])
        return f"Saved colonies with overcrowding: {listed}. Build City/Housing districts or resettle excess pops, and confirm open jobs in game."
    if focus == "stability":
        with_stab = [(stab, p) for p in planets if (stab := _num(p.get("stability"))) is not None]
        if not with_stab:
            return "Colony stability values were not readable in this save. Check your Colonies screen in game."
        low = sorted([(stab, p) for stab, p in with_stab if stab < 55], key=lambda item: item[0])
        if not low:
            lowest_stab, lowest = min(with_stab, key=lambda item: item[0])
            return (f"No saved colony is below 55% stability (lowest is {lowest['name']} at {lowest_stab:.0f}%). "
                    "Keep amenities positive, crime low, and factions happy to sustain output bonuses.")
        listed = "; ".join(
            f"{p['name']} ({stab:.0f}% stability, {_fmt_metric(p.get('free_amenities'), '+.1f')} amenities)"
            for stab, p in low[:3]
        )
        return (f"Lowest-stability saved colonies: {listed}. Fix negative amenities and high crime first (below 25% risks revolt), "
                "then check faction approval, housing, and martial/anti-crime decisions in game.")
    if focus in ("attention", "build") or context.mode in ("recommendation", "how_to"):
        urgent = [p for p in planets if (p.get("recommendation") or {}).get("level") == "urgent"]
        if urgent:
            first = urgent[0]
            rec = first["recommendation"]
            extra = f" Also watch: {', '.join(p['name'] for p in urgent[1:3])}." if len(urgent) > 1 else ""
            return (f"Start with {first['name']} ({str(first.get('designation') or 'colony').lower()}, "
                    f"{_fmt_metric(first.get('stability'), '.0f', '%')} stability, "
                    f"{_fmt_metric(first.get('free_amenities'), '+.1f')} free amenities, "
                    f"{_fmt_metric(first.get('free_housing'), '+.1f')} free housing). "
                    f"{rec['title']}: {rec['action']} {rec['reason']}{extra}")
        return planet_answer("", snapshot)
    return "Which colony do you mean? Enter its name, or open Planets to compare your colonies."


def tech_answer(snapshot: dict, context: QuestionContext | None = None) -> str:
    branches = snapshot.get("technology", {}).get("branches", {})
    if not branches:
        return "I could not read the research queues from this save."
    player = snapshot.get("player") or {}
    research = player.get("research") or {}
    focus = context.focus if context else None
    mode = context.mode if context else "status"

    if focus in ("physics", "society", "engineering"):
        branch = branches.get(focus, {})
        rate = _num(research.get(focus))
        rate_str = f" ({rate:.1f}/month)" if rate is not None else ""
        return (f"{focus.title()}{rate_str}: currently researching {branch.get('current', 'unknown')}; "
                f"suggested next pick is {branch.get('recommendation', 'review options')}. "
                "Open Tech Tree and click Route to inspect exact prerequisites before picking.")

    if focus == "branch_compare":
        rates = [(val, name) for name in ("physics", "society", "engineering")
                 if (val := _num(research.get(name))) is not None]
        if rates:
            rates.sort()
            low_val, low_name = rates[0]
            summary = ", ".join(f"{name.title()} {_num(research.get(name)):.1f}/mo" for name in ("physics", "society", "engineering") if _num(research.get(name)) is not None)
            branch = branches.get(low_name, {})
            return (f"Saved research output: {summary}. {low_name.title()} is your lowest branch at {low_val:.1f}/month "
                    f"(researching {branch.get('current', 'unknown')}; suggested next pick: {branch.get('recommendation', 'review options')}). "
                    "Check orbital stations, scientist traits, and specialty labs in game.")

    if focus == "research_output" or mode == "how_to":
        rate_parts = [f"{name.title()} {val:.1f}/mo" for name in ("physics", "society", "engineering")
                      if (val := _num(research.get(name))) is not None]
        size = _num(player.get("empire_size"))
        net = player.get("net") or {}
        net_known = player.get("net_known") or {}
        cg_val = _num(net.get("consumer_goods")) if net_known.get("consumer_goods", True) is not False else None
        header = ("Saved research output: " + ", ".join(rate_parts) + ". ") if rate_parts else ""
        size_note = f"Saved Empire Size is {size:g} (higher Empire Size increases tech costs). " if size is not None else ""
        cg_note = (f"Watch Consumer Goods ({signed(cg_val)}/mo) before adding more labs. "
                   if cg_val is not None and cg_val < 0 else "")
        return (header + size_note + cg_note +
                "To increase research: specialize a Tech-World with Research Labs and Researchers (or Calculators/Brain Drones for Gestalt), "
                "build orbital research stations, assign research-focused Councilors/scientists, and keep Empire Size under control. Confirm upkeep and open jobs in game.")

    if mode == "recommendation":
        picks = [f"{name.title()}: {branches.get(name, {}).get('recommendation', 'review options')}"
                 for name in ("physics", "society", "engineering")]
        return ("Suggested next research picks — " + "; ".join(picks) +
                ". Open Tech Tree and click Route to verify prerequisites and check each tech's in-game effect before choosing.")

    parts = []
    for name in ("physics", "society", "engineering"):
        branch = branches.get(name, {})
        rate = _num(research.get(name))
        rate_str = f" ({rate:.1f}/mo)" if rate is not None else ""
        parts.append(f"{name.title()}{rate_str}: researching {branch.get('current', 'unknown')}; suggested next pick {branch.get('recommendation', 'review options')}")
    return ". ".join(parts) + ". Check each technology's in-game effect before choosing."


def ship_answer(snapshot: dict, context: QuestionContext | None = None) -> str:
    player = snapshot.get("player") or {}
    focus = context.focus if context else None
    mode = context.mode if context else "status"

    if focus == "starbase_capacity":
        sb_used = _num(player.get("starbase_used"))
        sb_cap = _num(player.get("starbase_capacity"))
        sb_text = (f"Saved starbases: {sb_used:g} / {sb_cap:g}."
                   if sb_used is not None and sb_cap is not None else "Saved starbase capacity is unavailable in this save.")
        over_note = (" You are currently over cap, which adds a steep Energy upkeep penalty—downgrade low-value starbases first."
                     if sb_used is not None and sb_cap is not None and sb_cap > 0 and sb_used > sb_cap else "")
        profile = player.get("profile") or {}
        if profile.get("is_nomad"):
            levers = "Expand Waystation/Wayline capacity through Nomad technologies and traditions rather than standard settled starbases."
        else:
            levers = ("Increase Starbase Capacity by owning more systems, researching Starbase Capacity technologies (such as Interstellar Economics / Doctrine techs), "
                      "picking Unyielding or Supremacy traditions, using the Fortify the Border edict, or taking Grasp the Void. "
                      "You can also downgrade unneeded starbases back to Outposts.")
        return f"{sb_text}{over_note} {levers} Confirm exact bonuses and eligibility in game."

    if focus == "naval_capacity":
        naval_used = _num(player.get("naval_used"))
        naval_cap = _num(player.get("naval_capacity"))
        sb_used = _num(player.get("starbase_used"))
        sb_cap = _num(player.get("starbase_capacity"))
        used_text = f"{naval_used:g}" if naval_used is not None else "unknown"
        cap_text = f"{naval_cap:g}" if naval_cap is not None else "unknown in save"
        sb_text = (f" Starbases: {sb_used:g}/{sb_cap:g}."
                   if sb_used is not None and sb_cap is not None else "")
        profile = player.get("profile") or {}
        if profile.get("is_nomad"):
            levers = "Expand Arkship naval modules, Waystation support, and naval-capacity technologies/traditions."
        else:
            levers = ("Build Anchorage starbases with Naval Logistics Offices (staying within Starbase Capacity), "
                      "add Strongholds/Fortresses (Soldier jobs) on border worlds, and prioritize Naval Capacity technologies and Supremacy traditions.")
        return f"Saved naval usage: {used_text} / {cap_text}.{sb_text} {levers} Confirm your exact naval cap and alloy upkeep in game."

    rec = snapshot.get("ship_builds", {}).get("recommendation", {})
    if focus == "ship_config" or mode == "how_to":
        lead = (f"Current saved build focus: {rec['title']} ({rec['quantity']}). "
                if isinstance(rec, dict) and rec.get("title") and rec.get("quantity") else "")
        return (lead +
                "General Ship Designer configuration: start with ~50% Armor / ~50% Shields and mixed Kinetic + Energy (or Disruptors/Missiles) when enemy gear is unknown. "
                "Counter visible enemies: use Armor-heavy (~70-80%) vs Kinetic weapons, Shield-heavy (~70-80%) vs Energy weapons, Armor + Point-Defense/Flak vs Missiles/Torpedoes; "
                "use Kinetic or bypass weapons vs Shield-heavy enemies and Energy/Torpedoes vs Armor-heavy enemies. Add Afterburners on Corvettes/Frigates/Cruisers and open Fleet → Design Finder for hull-by-hull blueprints. "
                "Confirm unlocked tiers, reactor power, and alloy upkeep in Ship Designer.")

    if not rec:
        return "I could not read your owned ship designs from this save."
    return f"{rec['title']}. {rec['quantity']}. {rec['reason']} {rec['caveat']}"


AI_PERSONALITY_WARNINGS = {
    "fanatical_befrienders": "Fanatical Befrienders (+100 base opinion masks 2x Aggressiveness and 1.5x Bravery—willing to attack Superior empires)",
    "fanatic_purifiers": "Fanatic Purifiers (total-war genocidal AI; diplomacy is disabled)",
    "devouring_swarm": "Devouring Swarm (total-war Hive Mind; diplomacy is disabled)",
    "exterminators": "Determined Exterminators (total-war Machine Intelligence toward organics)",
    "metalhead": "Metalheads (extreme aggression and bravery; hostile toward almost everyone)",
    "hegemonic_imperialists": "Hegemonic Imperialists (aggressive conqueror/subjugator)",
    "democratic_crusaders": "Democratic Crusaders (aggressive toward non-democratic empires)",
    "slaving_despots": "Slaving Despots (expansionist conqueror/raider)",
    "honorbound_warriors": "Honorbound Warriors (high bravery; willing to challenge stronger fleets)",
}


def threat_answer(snapshot: dict) -> str:
    contacts = snapshot.get("contacts", [])
    if not contacts:
        return "No contacted empires were readable. Check the in-game diplomacy screen."
    spoilers = snapshot.get("_spoilers_active") is True
    risky = []
    for item in contacts:
        intel = _num(item.get("intel"))
        if not spoilers and (intel is None or intel < 10):
            continue
        pers = str(item.get("personality") or "").lower()
        if pers in AI_PERSONALITY_WARNINGS:
            risky.append((item["name"], AI_PERSONALITY_WARNINGS[pers]))
    known = [item for item in contacts if item.get("opinion") is not None]
    if not known and not risky:
        return "Contacts exist, but their opinions were not readable. Check in-game intel before naming a threat."
    parts = []
    if known:
        top = min(known, key=lambda item: item["opinion"])
        parts.append(f"Review {top['name']} first: recorded opinion {top['opinion']:+d}.")
    if risky:
        flagged = "; ".join(f"{name}: {note}" for name, note in risky[:2])
        parts.append(f"High-risk AI personalities recorded: {flagged}.")
    parts.append("Check borders, visible naval strength, treaties and intentions in game. "
                 "A save can contain foreign power your empire has not discovered.")
    return " ".join(parts)


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


def _crisis_answer(context: QuestionContext, snapshot: dict) -> str:
    counters = {
        "prethoryn": (
            "Prethoryn Scourge counter: Prethoryn use zero shields (all armor + huge hull) with biological missiles and strike craft. "
            "Fit 100% Armor (skip shields) + Flak/Point-Defense escorts, and arm fleets with Energy weapons (Tachyon Lances, Plasma, Lasers) and Strike Craft. "
        ),
        "unbidden": (
            "The Unbidden (Extradimensional Invaders) counter: Unbidden use massive shields and zero armor, with anti-armor weapons and slow sublight speed. "
            "Fit Maximum Shields + Shield Capacitors (skip armor) and pure long-range Kinetic weapons (Giga Cannons, Kinetic Artillery) to kite them; "
            "avoid pure bypass weapons inside Dimensional Anchor systems where shield hardening spikes. "
        ),
        "contingency": (
            "The Contingency counter: Contingency ships use balanced 1:4:4 Hull/Armor/Shields with low hardening and heavy mixed weapons. "
            "Fit balanced Shields + Armor with Shield Capacitors/Afterburners, and use shield/armor bypass weapons (Focused Arc Emitters, Disruptors, Missiles, Strike Craft). "
        ),
        "cetana": (
            "Cetana (The Synthetic Queen, The Machine Age DLC) counter: her flagship structures have huge health pools and resist penetration/bypass builds. "
            "Field massed Devastator Torpedo Frigates with Afterburners for raw DPS against the flagship, supported by artillery/carrier fleets to clear patrols. "
        ),
        "midgame": (
            "Midgame crises include the Great Khan (Apocalypse — can surrender as Satrapy or kill the flagship twice), Gray Tempest (Distant Stars — destroy Central Factory in the L-Cluster), "
            "Voidworm Plague (Grand Archive — clear Nests before population surges), Crystal Rift / The Formless (Astral Planes), and War in Heaven (Leviathans). "
        ),
    }
    prefix = counters.get(context.focus or "", "")
    profile = (snapshot.get("player") or {}).get("profile") or {}
    nomad_note = "Nomad warning: crisis fleets destroy Arkships outright rather than disabling them. " if profile.get("is_nomad") else ""
    return prefix + nomad_note + _guide_steps("crisis", snapshot)


def _council_answer(snapshot: dict) -> str:
    version = (snapshot.get("campaign") or {}).get("save_version") or snapshot.get("version")
    release = parse_release_tuple(version)
    size = _num((snapshot.get("player") or {}).get("empire_size"))
    parts = []
    if size is not None:
        agenda_cost = round(7000 * (1 + max(0.0, size - 100) * 0.001))
        parts.append(f"At saved Empire Size {size:g}, estimated base Agenda progress cost is ~{agenda_cost:,}.")
    if release and release < (4, 6, 0):
        parts.append(f"This save is {version} (pre-4.6): the 5th Council seat still follows 4.5 civic unlock rules rather than 4.6's Galactic Administration tech.")
    elif release and release >= (4, 6, 0):
        parts.append("In 4.6 Corona Borealis, the 5th Council seat unlocks via Galactic Administration tech rather than a 3rd civic.")
    prefix = (" ".join(parts) + " ") if parts else ""
    return prefix + _guide_steps("council", snapshot)


def _leaders_answer(snapshot: dict) -> str:
    paragons = has_dlc(snapshot, "galactic_paragons")
    prefix = ("With Galactic Paragons active, you manually pick traits, Veteran classes unlock at level 4 (Tier 3 cap), and Destiny traits at level 8. "
              if paragons is True else
              "Without Galactic Paragons listed, traits auto-roll and Veteran traits cap at Tier 2. "
              if paragons is False else "")
    return prefix + _guide_steps("leaders", snapshot)


def _subjects_answer(snapshot: dict) -> str:
    overlord = has_dlc(snapshot, "overlord")
    prefix = ("Overlord DLC is active, enabling negotiable Agreement terms, Specialist Subjects (Bulwark/Scholarium/Prospectorium), and Overlord Holdings. "
              if overlord is True else
              "Overlord DLC is not recorded in this save, so specialized subject types and custom holdings are unavailable. "
              if overlord is False else "")
    return prefix + _guide_steps("subjects", snapshot)


def _megastructures_answer(snapshot: dict) -> str:
    profile = (snapshot.get("player") or {}).get("profile") or {}
    parts = []
    if profile.get("is_nomad"):
        parts.append("This empire has a Nomadic profile: Habitats, Deep Space Citadels, Orbital Rings, and most multi-stage megastructures are blocked (only Quantum Catapult, Arc Furnace, and Ambition megastructures).")
    if has_dlc(snapshot, "biogenesis") is True:
        parts.append("BioGenesis DLC enables Deep Space Citadels (1/system cap, +1 with Eternal Vigilance or Starlit Citadel).")
    prefix = (" ".join(parts) + " ") if parts else ""
    return prefix + _guide_steps("megastructures", snapshot)


def _government_answer(snapshot: dict) -> str:
    player = snapshot.get("player") or {}
    profile = player.get("profile") or {}
    version = (snapshot.get("campaign") or {}).get("save_version") or snapshot.get("version")
    release = parse_release_tuple(version)
    parts = []
    if profile.get("authority"):
        auth_label = str(profile["authority"]).removeprefix("auth_").replace("_", " ")
        parts.append(f"Saved authority: {auth_label}.")
    size = _num(player.get("empire_size"))
    if size is not None:
        parts.append(f"At saved Empire Size {size:g}, reforming government costs about {int(round(size * 10)):,} Unity (20-year cooldown).")
    if release and release < (4, 6, 0):
        parts.append(f"Note: this save is {version} (4.5 rules), where Corporate empires still cannot take Fanatic Authoritarian/Egalitarian.")
    prefix = (" ".join(parts) + " ") if parts else ""
    return prefix + _guide_steps("government", snapshot)


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
    if context.topic == "crisis":
        return _crisis_answer(context, snapshot)
    if context.topic == "council":
        return _council_answer(snapshot)
    if context.topic == "leaders":
        return _leaders_answer(snapshot)
    if context.topic == "subjects":
        return _subjects_answer(snapshot)
    if context.topic == "megastructures":
        return _megastructures_answer(snapshot)
    if context.topic == "government":
        return _government_answer(snapshot)
    if context.topic == "policy":
        return _policy_answer(context, snapshot)
    if context.topic == "population":
        return _population_answer(context, snapshot)
    if context.topic == "planet" and context.planet:
        return planet_answer(context.planet["name"], snapshot)
    if context.topic == "planet":
        return _general_planet_answer(context, snapshot)
    if context.topic == "technology":
        return tech_answer(snapshot, context)
    if context.topic == "ships":
        return ship_answer(snapshot, context)
    if context.topic == "economy" and context.planet:
        return _planet_economy_answer(context.planet, snapshot)
    if context.topic == "economy":
        return economy_answer(snapshot, context)
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
