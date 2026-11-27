"""Evidence-based goals for a Cygnus save."""
from __future__ import annotations

import math
import re
from pathlib import Path

from .dlcs import detect_dlc_drift, has_dlc, parse_release_tuple
from .playbooks import load_playbooks, match_playbook


PLAYBOOKS = load_playbooks()


def signed(value):
    return f"{value:+.1f}"


def step(action, reason, check):
    return {"action": action, "reason": reason, "check": check}


def finite_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) else None


def game_date(value):
    value = str(value or "")
    return tuple(map(int, value.split("."))) if re.fullmatch(r"\d{4,}\.\d{2}\.\d{2}", value) else None


def resource_runway(snapshot, resource, history=()):
    """Estimate cover at the saved monthly rate; bands are Guide heuristics."""
    player = snapshot.get("player", {})
    stock = finite_number((player.get("stock") or {}).get(resource))
    net = finite_number((player.get("net") or {}).get(resource))
    if (player.get("stock_known") or {}).get(resource, True) is False:
        stock = None
    if (player.get("net_known") or {}).get(resource, True) is False:
        net = None
    result = {"date": snapshot.get("date"), "stock": stock, "net": net,
              "status": "unknown", "months": None, "urgency": "unknown",
              "stock_change": None}
    if stock is None or stock < 0 or net is None:
        return result
    if net >= 0:
        result.update(status="no_depletion", urgency="none")
    else:
        months = stock / abs(net)
        result.update(status="depleting", months=round(months, 1),
                      urgency="urgent" if months < 3 else "watch" if months < 6 else "planned")
    current_date = game_date(snapshot.get("date"))
    previous_options = []
    for previous in history:
        prior_date = game_date(previous.get("date"))
        if previous is snapshot or current_date is None or prior_date is None or prior_date >= current_date:
            continue
        if (previous.get("campaign", {}).get("id") and snapshot.get("campaign", {}).get("id")
                and previous["campaign"]["id"] != snapshot["campaign"]["id"]):
            continue
        prior_player = previous.get("player") or {}
        if (prior_player.get("stock_known") or {}).get(resource, True) is False:
            continue
        prior = finite_number((prior_player.get("stock") or {}).get(resource))
        if prior is not None and prior >= 0:
            previous_options.append((prior_date, prior))
    if previous_options:
        result["stock_change"] = round(stock - max(previous_options)[1], 1)
    return result


def research_trend(snapshot, history, branch):
    current = snapshot.get("technology", {}).get("branches", {}).get(branch, {})
    project = current.get("current_id")
    result = {"project_id": project, "status": "unknown", "from_date": None,
              "to_date": snapshot.get("date"), "elapsed_months": None,
              "progress_delta": None, "observation": "Research progress could not be compared."}
    if not project:
        result.update(status="no_project", observation="No current project is recorded for this branch.")
        return result
    current_progress = finite_number(current.get("progress")) if current.get("progress_known") else None
    if current_progress is None or current_progress < 0:
        result.update(status="unknown", observation="Current saved research progress is unavailable.")
        return result
    current_date = game_date(snapshot.get("date"))
    campaign_id = snapshot.get("campaign", {}).get("id")
    if not campaign_id:
        result.update(status="no_comparable_save",
                      observation="Campaign identity is unavailable, so earlier research cannot be compared safely.")
        return result
    earlier = []
    for previous in history:
        date = game_date(previous.get("date"))
        if previous is snapshot or not current_date or not date or date >= current_date:
            continue
        if previous.get("campaign", {}).get("id") != campaign_id:
            continue
        prior = previous.get("technology", {}).get("branches", {}).get(branch, {})
        if prior.get("current_id") != project or not prior.get("progress_known"):
            continue
        value = finite_number(prior.get("progress"))
        if value is not None and value >= 0:
            earlier.append((date, value, previous.get("date")))
    if not earlier:
        result.update(status="no_comparable_save",
                      observation="No earlier save in this campaign records the same project with valid progress.")
        return result
    date, prior_progress, from_date = max(earlier)
    delta = round(current_progress - prior_progress, 1)
    months = ((current_date[0] - date[0]) * 12 + current_date[1] - date[1]
              if current_date[2] == date[2] else None)
    elapsed = f" over {months} game months" if months is not None else " between saved dates"
    if delta > 0:
        wording = f"Saved progress rose by {delta:g}{elapsed}."
    elif delta == 0:
        wording = f"No progress change was recorded{elapsed}; check the project in game."
    else:
        wording = f"Saved progress fell by {abs(delta):g}{elapsed}; the cause is unverified."
    result.update(status="observed", from_date=from_date, elapsed_months=months,
                  progress_delta=delta, observation=wording + " No completion time can be inferred.")
    return result


JOB_FOR_RESOURCE = {
    "food": ("farmer", "agri_drone"),
    "energy": ("technician", "technician_drone"),
    "minerals": ("miner", "mining_drone"),
    "alloys": ("foundry", "fabricator", "alloy_drone"),
    "consumer_goods": ("artisan", "artisan_drone"),
    "trade": ("trader", "clerk", "logistics_drone"),
}


def _matching_job(planet, resource):
    kinds = JOB_FOR_RESOURCE.get(resource, ())
    for kind in kinds:
        for job in planet.get("jobs", []):
            if job.get("type") == kind:
                return job, kind
    return None, (kinds[0] if kinds else resource)


def open_job_count(planet, resource):
    """Return usable unfilled capacity, or None when the save omits job limits."""
    job, _ = _matching_job(planet, resource)
    if not job:
        return None
    filled = finite_number(job.get("filled"))
    capacity = finite_number(job.get("capacity"))
    limit = finite_number(job.get("limit"))
    if filled is None or capacity is None or limit is None:
        return None
    allowed = min(capacity, limit)
    return max(0, round(allowed - filled, 1))


def colony_for(snapshot, resource):
    planets = snapshot.get("planets", [])
    if not planets:
        return None
    preferred = {"food": "farm", "energy": "generator", "minerals": "mining",
                 "alloys": "industrial", "consumer_goods": "industrial",
                 "trade": "trade"}[resource]
    return max(planets, key=lambda p: (
        (open_job_count(p, resource) or 0) > 0,
        preferred in p.get("designation", "").lower(),
        p.get("produces", {}).get(resource, 0)))


def resource_steps(snapshot, resource):
    planet = colony_for(snapshot, resource)
    profile = (snapshot.get("player") or {}).get("profile") or {}
    is_nomad = bool(profile.get("is_nomad"))
    label = resource.replace("_", " ")
    district = {"food": "Agriculture", "energy": "Generator", "minerals": "Mining",
                "alloys": "Industrial", "consumer_goods": "Industrial",
                "trade": "Trade / Commercial"}[resource]
    actions = []
    runway = snapshot.get("resource_runway", {}).get(resource) or resource_runway(snapshot, resource)
    if planet:
        matched_job, job_kind = _matching_job(planet, resource)
        job_label = job_kind.replace("_", " ")
        if planet.get("free_amenities", 0) < -5 or planet.get("stability", 100) < 50:
            actions.append(step(
                planet["recommendation"]["action"],
                f"{planet['name']} has {signed(planet['free_amenities'])} amenities and {planet['stability']:.0f}% stability.",
                "Confirm jobs, building eligibility and costs in the colony screen."))
        open_jobs = open_job_count(planet, resource)
        if open_jobs is not None and open_jobs > 0:
            actions.append(step(
                f"Check whether {planet['name']} can fill its open {job_label} jobs.",
                f"The save records {open_jobs:g} allowed but unfilled job capacity; new capacity alone will not produce more {label}.",
                "Check available workforce, job priority, stability and upkeep on this colony; workers cannot move between planets instantly."))
        elif open_jobs == 0:
            job = matched_job or {}
            if job.get("limit", 0) < job.get("capacity", 0) and job.get("filled", 0) < job.get("capacity", 0):
                actions.append(step(
                    f"Review {planet['name']}'s {job_label} job limit before adding capacity.",
                    f"The save records {job['filled']:g} filled, {job['limit']:g} allowed and {job['capacity']:g} capacity.",
                    "Check why the jobs are limited and whether workers and upkeep can support enabling them."))
            else:
                target_unit = "Arkship modules/districts or Waystation network" if is_nomad else f"{district} District or suitable building"
                actions.append(step(
                    f"Inspect {planet['name']} for a {target_unit}.",
                    f"No usable open {job_label} jobs were recorded. This colony produces {planet.get('produces', {}).get(resource, 0):.1f} {label}.",
                    "Confirm build slot, unlocked option, available workers, stability, construction cost and upkeep in game."))
        else:
            target_unit = "Arkship or Waystation" if is_nomad else f"{district} District"
            actions.append(step(
                f"Inspect {planet['name']}'s jobs before adding {target_unit} capacity.",
                f"The saved job capacity is incomplete; this colony produces {planet.get('produces', {}).get(resource, 0):.1f} {label}.",
                "Confirm filled and allowed jobs, workforce, build eligibility and upkeep in game."))
    elif is_nomad:
        actions.append(step(
            f"Check your Arkship onboard jobs, Waylines, and Operational Reserves for {label}.",
            "Nomadic empires gather and route resources through Arkships, Waystations, and Waylines rather than fixed colonies.",
            "Confirm Waystation protection, Logistics Ships, and Arkship modules in game."))
    if runway["status"] == "depleting" and runway["urgency"] == "urgent":
        actions.insert(0, step(
            f"Check a temporary {label} buffer in the in-game Market.",
            f"Saved stock {runway['stock']:,.1f}, net {signed(runway['net'])}/month: about {runway['months']:g} months at this rate.",
            "Check current Market price, Trade balance and market fee (30% base); a purchase does not repair the monthly deficit."))
    elif runway["status"] == "depleting":
        actions.append(step(
            f"Plan a gradual {label} production or upkeep fix.",
            f"Saved stock {runway['stock']:,.1f}, net {signed(runway['net'])}/month: about {runway['months']:g} months at this rate.",
            "Check the next autosave and in-game resource breakdown; saved rates can change."))
    return actions[:3] or [step(f"Inspect the {label} breakdown in game.",
                              "No suitable colony details were readable.",
                              "Do not order a build until eligibility is confirmed.")]


def fleet_steps(snapshot):
    player = snapshot["player"]
    profile = player.get("profile") or {}
    rec = snapshot.get("ship_builds", {}).get("recommendation", {})
    policies = snapshot.get("policies", {})
    actions = []
    if player["net"].get("alloys", 0) <= 0:
        actions.extend(resource_steps(snapshot, "alloys")[:1])
    elif rec.get("design_id"):
        upkeep_note = (" (and food if using a biological shipset)"
                       if profile.get("shipset_kind") == "biological" else "")
        actions.append(step(
            f"Check a small batch of the saved {rec['title'].removeprefix('Reinforce with ').removeprefix('Reinforce ')} design.",
            f"Alloys are {signed(player['net'].get('alloys', 0))}/month with {player.get('stock', {}).get('alloys', 0):,.0f} stored{upkeep_note}.",
            "Verify cost, naval capacity, upkeep, fleet composition and counters."))
    else:
        actions.append(step("Review saved combat designs in Ship Builds.",
                            "No suitable reinforcement design was identified.",
                            "Check the ship designer and fleet capacity in game."))
    policy_keys = (
        ("fleet_doctrine", "weapon_preference", "defense_preference",
         "arkship_weapon_preference", "waystation_defense_preference")
        if profile.get("is_nomad")
        else ("fleet_doctrine", "weapon_preference", "defense_preference")
    )
    details = [f"{key.replace('_', ' ')}: {policies[key]}" for key in policy_keys if policies.get(key)]
    if details:
        actions.append(step(
            "Compare your current military policies with that ship design.",
            "Selected in this save: " + "; ".join(details) + ". Weapon/defense preferences also steer tech draws.",
            "Check available choices, cooldown and the ship's actual loadout in game."))
    return actions[:2]


def goal(key, title, detail, due, metric, value, target, steps):
    return {"key": key, "title": title, "detail": detail, "due": due,
            "metric": metric, "current": value, "target": target, "steps": steps}


def describe_priority(item, snapshot):
    key = item["key"]
    if key.startswith("deficit:"):
        urgency = snapshot["resource_runway"][key.split(":", 1)[1]]["urgency"]
        return {"urgent": (100, "Less than three months of saved stock cover"),
                "watch": (75, "Three to six months of saved stock cover"),
                "planned": (35, "Deficit with over six months of saved stock cover"),
                "unknown": (45, "Deficit with unknown stock cover")}[urgency]
    if key.startswith("colony:"):
        return 90, "Urgent saved colony condition"
    if key == "grow:alloys":
        return 55, "Alloy income below the Guide's fleet preparation target"
    if key == "fleet":
        return 40, "Fleet preparation while monthly alloy income is positive"
    if key.startswith("diplomacy:"):
        return 30, "Contacted empire has strongly negative recorded opinion"
    return 20, "Routine preparation"


def enrich_goal(item, snapshot):
    """Keep the v1.5 goal fields while exposing one traceable advice record."""
    score, rank_reason = describe_priority(item, snapshot)
    first = item["steps"][0] if item["steps"] else {}
    item.update(id=item["key"], snapshot_date=snapshot.get("date"),
                observation=item["detail"], action=first.get("action", "Review in game."),
                reason=first.get("reason", item["detail"]),
                expected_effect=f"Move {item['metric']} toward {item['target']} if the in-game action works.",
                trade_off="Check construction cost, upkeep and competing priorities before committing.",
                in_game_check=first.get("check", "Verify in game."),
                severity="urgent" if score >= 90 else "watch" if score >= 55 else "planned",
                priority_score=score, rank_reason=rank_reason,
                visibility="player-visible", source_rule="Guide v1.6 heuristic",
                source_game_version=snapshot.get("campaign", {}).get("save_version"),
                confidence="Based on the selected save; check current conditions in game.")
    return item


CONTACTED_CRISIS_KINDS = {
    "swarm": ("prethoryn", "Prethoryn Scourge"),
    "extradimensional": ("unbidden", "The Unbidden"),
    "extradimensional_2": ("unbidden", "The Aberrant"),
    "extradimensional_3": ("unbidden", "The Vehement"),
    "ai_empire": ("contingency", "The Contingency"),
    "synth_queen": ("cetana", "Cetana (Synthetic Queen)"),
    "awakened_marauders": ("midgame", "The Great Khan"),
    "gray_goo": ("midgame", "Gray Tempest"),
}

CAMPAIGN_CHECKPOINTS = (
    {
        "year": 2210, "stage": 1, "stage_name": "Early Expansion",
        "focus": "Survey systems, claim chokepoints, and settle guaranteed colonies without overbuilding empty districts.",
        "targets": {"colonies": (2, 3), "alloys": (15, 30), "research": (40, 80)},
        "checklist": ["Keep Trade positive and avoid unaddressed deficits", "Settle initial habitable worlds and lock down hyperlane chokepoints"],
    },
    {
        "year": 2220, "stage": 1, "stage_name": "Early Expansion",
        "focus": "Start specializing your first Tech and Forge/Factory colonies while keeping stability above 50%.",
        "targets": {"colonies": (3, 5), "alloys": (25, 50), "research": (80, 150), "fleet": (1000, 2500)},
        "checklist": ["Keep all colonies >= 50% stability (below 25% risks revolt)", "Finish your first Tradition tree and scout neighbor AI personalities"],
    },
    {
        "year": 2230, "stage": 1, "stage_name": "Early Expansion",
        "focus": "Stabilize Consumer Goods and Trade, and build a standing deterrent fleet.",
        "targets": {"colonies": (4, 7), "alloys": (40, 80), "research": (150, 250), "fleet": (2500, 6000)},
        "checklist": ["Keep Consumer Goods and Trade positive (shortages cut Research/Unity and Job Efficiency)", "Build a standing fleet for deterrence and Power Projection"],
    },
    {
        "year": 2250, "stage": 2, "stage_name": "Specialization & Scaling",
        "focus": "Run dedicated worlds (Forge, Factory, Tech, Basic), unlock Cruisers, and choose an Ascension Path.",
        "targets": {"colonies": (6, 10), "alloys": (80, 150), "research": (300, 500), "fleet": (8000, 20000)},
        "checklist": ["Reserve an open Tradition slot for your Ascension Path", "Keep Starbases and Leaders within capacity caps"],
    },
    {
        "year": 2275, "stage": 2, "stage_name": "Specialization & Scaling",
        "focus": "Transition to Battleships and Kilostructures (Dyson Swarm / Arc Furnace) and prep for Dangerous Techs.",
        "targets": {"colonies": (8, 14), "alloys": (150, 300), "research": (600, 1000), "fleet": (20000, 50000)},
        "checklist": ["Set AI Citizen Rights (or outlaw robots) before ~2290 if researching Synthetics", "Establish Vassals, Federations, or defensive pacts"],
    },
    {
        "year": 2300, "stage": 3, "stage_name": "Midgame & Power Projection",
        "focus": "Be ready for Midgame Crises (Great Khan, Gray Tempest, Voidworm Plague) and War in Heaven.",
        "targets": {"alloys": (250, 500), "research": (1000, 1800), "fleet": (40000, 100000)},
        "checklist": ["Scale Naval Capacity with Anchorage starbases or Fortresses", "Ensure zero colonies are below 50% stability"],
    },
    {
        "year": 2350, "stage": 3, "stage_name": "Midgame & Power Projection",
        "focus": "Push Mega-Engineering, Titans, and Galactic Community / 4.6 Ideologies leverage.",
        "targets": {"alloys": (500, 900), "research": (2000, 3500), "fleet": (100000, 250000)},
        "checklist": ["Start your first Megastructure or Galactic Hall (4.6 Willpower)", "Save counter-fitted ship designs in Fleet Designer"],
    },
    {
        "year": 2400, "stage": 4, "stage_name": "Endgame & Crisis",
        "focus": "Build full Endgame Crisis readiness across alloys, naval capacity, gateways, and shipyards.",
        "targets": {"alloys": (800, 1500), "research": (3500, 6000), "fleet": (250000, 500000)},
        "checklist": ["Link Mega Shipyards and Gateways for fast reinforcement", "Consider Defender of the Galaxy (+50% crisis damage)"],
    },
    {
        "year": 2450, "stage": 4, "stage_name": "Endgame & Crisis",
        "focus": "Counter-refit fleets for the active Endgame Crisis and sustain wartime Alloys, Energy, and Trade.",
        "targets": {"alloys": (1200, 2000), "research": (5000, 8000), "fleet": (400000, 800000)},
        "checklist": ["Use Fleet -> Design Finder Crisis presets for the active crisis", "Swap off Sapient Combat Computers if facing the Contingency"],
    },
)


def detect_contacted_crises(snapshot: dict) -> list[dict]:
    """Return contacted active crisis factions from visible contacts (sorted deterministically, never by military power)."""
    found = []
    seen = set()
    for contact in snapshot.get("contacts") or []:
        if not isinstance(contact, dict):
            continue
        kind = str(contact.get("kind") or "").lower()
        if kind in CONTACTED_CRISIS_KINDS and kind not in seen:
            seen.add(kind)
            preset, label = CONTACTED_CRISIS_KINDS[kind]
            found.append({"kind": kind, "preset": preset, "label": label, "name": contact.get("name") or label})
    found.sort(key=lambda item: (item["label"].casefold(), item["kind"]))
    return found


def build_campaign_benchmark(snapshot: dict) -> dict:
    """Compare saved empire metrics against 4-stage decade checkpoints (post-4.3 1x-settings baseline)."""
    player = snapshot.get("player") or {}
    profile = player.get("profile") or {}
    net = player.get("net") or {}
    net_known = player.get("net_known") or {}
    research_map = player.get("research") or {}
    try:
        year = int(str(snapshot.get("date") or "").split(".")[0])
    except (ValueError, TypeError):
        year = 0

    current_cp = CAMPAIGN_CHECKPOINTS[0]
    for cp in CAMPAIGN_CHECKPOINTS:
        if year >= cp["year"]:
            current_cp = cp
    next_cp = next((cp for cp in CAMPAIGN_CHECKPOINTS if cp["year"] > year), None)
    before_first = year > 0 and year < CAMPAIGN_CHECKPOINTS[0]["year"]
    eval_cp = next_cp if before_first and next_cp else current_cp

    def rate_metric(label: str, key: str, value: float | None, bounds: tuple[int, int] | None, unit: str = "") -> dict | None:
        if bounds is None:
            return None
        low, high = bounds
        if value is None:
            status = "unknown"
        elif value >= low:
            status = "on_track"
        elif value >= low * 0.5:
            status = "building"
        else:
            status = "behind"
        return {
            "key": key, "label": label, "current": value,
            "target_low": low, "target_high": high, "unit": unit, "status": status,
        }

    is_nomad = bool(profile.get("is_nomad"))
    alloys_val = finite_number(net.get("alloys")) if net_known.get("alloys", True) is not False else None
    research_vals = [val for b in ("physics", "society", "engineering")
                     if (val := finite_number(research_map.get(b))) is not None]
    research_total = round(sum(research_vals), 1) if len(research_vals) == 3 else None
    colonies_val = finite_number(player.get("colonies"))
    fleet_val = finite_number(player.get("military"))

    targets = eval_cp["targets"]
    metrics = []
    if not is_nomad and "colonies" in targets:
        metrics.append(rate_metric("Colonies", "colonies", colonies_val, targets.get("colonies")))
    metrics.append(rate_metric("Alloys / mo", "alloys", alloys_val, targets.get("alloys"), "/mo"))
    metrics.append(rate_metric("Total research / mo", "research", research_total, targets.get("research"), "/mo"))
    if "fleet" in targets:
        metrics.append(rate_metric("Fleet power", "fleet", fleet_val, targets.get("fleet")))
    metrics = [m for m in metrics if m is not None]

    # Universal readiness checks (valid regardless of difficulty or galaxy sliders).
    checks = []
    deficits = [k.replace("_", " ") for k in ("energy", "minerals", "food", "consumer_goods", "alloys", "trade")
                if net_known.get(k, True) is not False and (v := finite_number(net.get(k))) is not None and v < 0]
    checks.append({
        "label": "Economy flow",
        "ok": not deficits,
        "detail": "No tracked monthly resource deficits." if not deficits else f"Active deficit(s): {', '.join(deficits)}.",
    })
    planets = [p for p in (snapshot.get("planets") or []) if isinstance(p, dict)]
    unstable = [(stab, p) for p in planets if (stab := finite_number(p.get("stability"))) is not None and stab < 50]
    revolt_risk = [(stab, p) for stab, p in unstable if stab < 25]
    if revolt_risk:
        worst_stab, worst = min(revolt_risk, key=lambda item: item[0])
        worst_name = worst.get("name") or "an unnamed colony"
        checks.append({"label": "Colony stability", "ok": False,
                       "detail": f"Revolt risk on {worst_name} ({worst_stab:.0f}% stability — below 25%)."})
    elif unstable:
        worst_stab, worst = min(unstable, key=lambda item: item[0])
        worst_name = worst.get("name") or "an unnamed colony"
        checks.append({"label": "Colony stability", "ok": False,
                       "detail": f"{len(unstable)} colony(ies) below 50% stability (lowest: {worst_name} at {worst_stab:.0f}%)."})
    elif planets:
        checks.append({"label": "Colony stability", "ok": True, "detail": "All saved colonies are at >= 50% stability."})

    sb_used = finite_number(player.get("starbase_used"))
    sb_cap = finite_number(player.get("starbase_capacity"))
    if sb_used is not None and sb_cap is not None and sb_cap > 0:
        over_sb = sb_used > sb_cap
        checks.append({
            "label": "Starbase capacity",
            "ok": not over_sb,
            "detail": (f"Over cap ({sb_used:g}/{sb_cap:g}) — steep Energy upkeep penalty."
                       if over_sb else f"Within cap ({sb_used:g}/{sb_cap:g})."),
        })

    return {
        "year": year,
        "stage": eval_cp["stage"],
        "stage_name": eval_cp["stage_name"],
        "before_first": before_first,
        "current_year": eval_cp["year"],
        "focus": eval_cp["focus"],
        "checklist": list(eval_cp["checklist"]),
        "metrics": metrics,
        "checks": checks,
        "next": ({
            "year": next_cp["year"],
            "stage": next_cp["stage"],
            "stage_name": next_cp["stage_name"],
            "focus": next_cp["focus"],
            "targets": {k: list(v) for k, v in next_cp["targets"].items() if not (is_nomad and k == "colonies")},
        } if next_cp and next_cp["year"] != eval_cp["year"] else None),
        "is_nomad": is_nomad,
        "contacted_crises": detect_contacted_crises(snapshot),
        "caveat": "Conditional post-4.3 baseline for standard 1x settings; adjust for difficulty, tech cost, habitable worlds, and empire origin.",
    }


def make_plan(snapshot, history, stored=None):
    player = snapshot["player"]
    profile = player.get("profile") or {}
    net = player["net"]
    stock = player.get("stock") or {}
    net_known = player.get("net_known") or {}
    try:
        year = int(str(snapshot["date"]).split(".")[0])
    except (ValueError, TypeError, KeyError):
        year = 0
    goals, alerts = [], []
    tracked_runway = ["food", "energy", "consumer_goods", "minerals", "alloys"]
    if "trade" in net or "trade" in stock:
        tracked_runway.append("trade")
    snapshot["resource_runway"] = {key: resource_runway(snapshot, key, history)
                                   for key in tracked_runway}
    for branch in ("physics", "society", "engineering"):
        current_branch = snapshot.get("technology", {}).get("branches", {}).get(branch)
        if current_branch is not None:
            current_branch["trend"] = research_trend(snapshot, history, branch)
    deficit_checks = [("food", 5), ("energy", 10), ("consumer_goods", 5), ("minerals", 10)]
    if "trade" in net and net_known.get("trade", True) is not False:
        deficit_checks.append(("trade", 5))
    for resource, minimum in deficit_checks:
        value = net.get(resource, 0)
        if value < 0:
            label = resource.replace("_", " ")
            runway = snapshot["resource_runway"][resource]
            if runway["status"] == "depleting":
                cover = f"Stock {runway['stock']:,.1f} covers about {runway['months']:g} months at the saved rate"
                if runway["stock_change"] is not None and runway["stock_change"] > 0:
                    cover += f"; stock rose {runway['stock_change']:,.1f} since the previous save (cause unknown)"
                detail = f"{cover}. Raise {label} from {signed(value)} to at least +{minimum}/month."
            else:
                detail = f"Runway unknown from this save. Raise {label} from {signed(value)} to at least +{minimum}/month."
            title = (f"Address {label} shortage" if runway["urgency"] == "urgent"
                     else f"Plan {label} recovery")
            goals.append(goal(f"deficit:{resource}", title, detail,
                              year + 3, f"net:{resource}", value, minimum,
                              resource_steps(snapshot, resource)))
            if runway["urgency"] == "urgent":
                alerts.append({"title": f"{label.title()} stock risk", "detail": detail})
    drift = detect_dlc_drift(snapshot, history)
    if drift["changed"]:
        parts = []
        if drift["added"]:
            parts.append("added: " + ", ".join(drift["added"]))
        if drift["removed"]:
            parts.append("removed: " + ", ".join(drift["removed"]))
        alerts.append({"title": "DLC set changed",
                       "detail": "Recorded save DLCs changed (" + "; ".join(parts) + "); verify DLC-gated rules in game."})
    release_tuple = parse_release_tuple(
        (snapshot.get("campaign") or {}).get("save_version") or snapshot.get("version")
    )
    if finite_number(stock.get("influence")) is not None and stock["influence"] >= 900 and net.get("influence", 0) > 0:
        spend_hint = ("Waystations, Arkships, or claims" if profile.get("is_nomad")
                      else "claims, megastructures, diplomacy, or Ideologies"
                      if has_dlc(snapshot, "willpower") is True and bool(release_tuple and release_tuple >= (4, 6, 0))
                      else "claims, megastructures, or diplomacy")
        alerts.append({"title": "Influence near cap",
                       "detail": f"Saved Influence is {stock['influence']:,.0f} ({signed(net['influence'])}/mo); excess over the 1,000 base cap is lost. Review {spend_hint} in game."})
    if (release_tuple and release_tuple >= (4, 6, 0)
            and has_dlc(snapshot, "willpower") is True
            and profile.get("ideology_active") is True
            and net.get("influence", 0) < 2):
        alerts.append({"title": "Check Ideology upkeep",
                       "detail": "Willpower Ideology is active while monthly Influence is low; check Ideological Momentum and upkeep in game."})
    alloys = net.get("alloys", 0)
    if alloys < 25:
        goals.append(goal("grow:alloys", "Grow alloy income",
                          f"Raise monthly alloys from {signed(alloys)} toward +25 before major fleet orders.",
                          year + 5, "net:alloys", alloys, 25, resource_steps(snapshot, "alloys")))
    else:
        power = player.get("military", 0)
        target = max(3000, int(power * 1.5))
        goals.append(goal("fleet", "Build a credible fleet",
                          f"Use {signed(alloys)} monthly alloys to work toward roughly {target:,} fleet power.",
                          year + 5, "military", power, target, fleet_steps(snapshot)))
    urgent = [p for p in snapshot.get("planets", [])
              if p.get("recommendation", {}).get("level") == "urgent"]
    if urgent:
        planet = urgent[0]
        use_stability = planet.get("free_amenities", 0) >= 0 and planet.get("stability", 100) < 50
        metric_name = f"stability:{planet['id']}" if use_stability else f"amenities:{planet['id']}"
        metric_current = planet["stability"] if use_stability else planet["free_amenities"]
        metric_target = 50 if use_stability else 0
        goals.append(goal(f"colony:{planet['id']}", f"Stabilize {planet['name']}",
                          f"Address its {signed(planet['free_amenities'])} amenities and {planet['stability']:.0f}% stability.",
                          year + 3, metric_name, metric_current, metric_target,
                          [step(planet["recommendation"]["action"],
                                planet["recommendation"]["reason"],
                                "Confirm jobs and building eligibility in game.")]))
        for item in urgent[:2]:
            alerts.append({"title": item["name"], "detail": item["recommendation"]["reason"]})
    tense = sorted((c for c in snapshot.get("contacts", [])
                    if c.get("opinion") is not None and c["opinion"] < -50),
                   key=lambda c: c["opinion"])
    if tense:
        contact = tense[0]
        name = contact["name"]
        goals.append(goal(f"diplomacy:{contact['id']}", f"Prepare for {name}",
                          f"Review this contacted empire at opinion {contact['opinion']:+d}.",
                          year + 5, f"opinion:{contact['id']}", contact["opinion"], 0, [
                              step(f"Review {name}'s borders, treaties and opinion.",
                                   f"The save records opinion {contact['opinion']:+d}.",
                                   "Check what your current intel actually reveals in game."),
                              step("Secure a defensible border and ask partners before relying on support.",
                                   "War support varies by conflict.",
                                   "Check chokepoints, acceptance, truce and war goals in game.")]))
        alerts.append({"title": f"Check {name}",
                       "detail": f"Recorded opinion {contact['opinion']:+d}; verify border risk and intel in game."})
    if not goals:
        goals.append(goal("prepare", "Prepare the next decade",
                          "Maintain reserves, review research and watch nearby diplomacy.",
                          year + 10, "readiness", 0, 1, [
                              step("Review the latest research choices and colony warnings.",
                                   "No urgent deficit was read.", "Verify unlocked options in game.")]))
    goals = [enrich_goal(item, snapshot) for item in goals]
    for item in goals:
        for record in PLAYBOOKS:
            matched = match_playbook(record, snapshot, item)
            if matched:
                item["playbook"] = matched
                break
    goals.sort(key=lambda item: (-item["priority_score"], item["key"]))
    anchor = (history[0] if history else snapshot).get("player", {})
    # Old v1.4 path-only progress cannot be safely migrated: a different
    # campaign may reuse that folder. Keep it on disk, but start ID-scoped
    # progress for Cygnus snapshots that provide a stable campaign identity.
    campaign = (snapshot.get("campaign", {}).get("id") or
                (str(Path(snapshot["path"]).parent) if snapshot.get("path") else ""))
    for item in goals:
        store_key = f"{campaign}|{item['key']}"
        old = stored.get(store_key) if stored is not None else None
        if old and old.get("campaign") == campaign and old.get("target", 0) > old.get("baseline", 0):
            item["target"], item["due"], baseline = old["target"], old["due"], old["baseline"]
        else:
            metric = item["metric"]
            if metric.startswith("net:"):
                baseline = anchor.get("net", {}).get(metric[4:], item["current"])
            elif metric.startswith("opinion:"):
                contact_id = int(metric.split(":", 1)[1])
                old_contact = next((c for c in (history[0] if history else snapshot).get("contacts", [])
                                    if c.get("id") == contact_id), None)
                baseline = old_contact.get("opinion", item["current"]) if old_contact else item["current"]
            else:
                baseline = anchor.get(metric, item["current"])
            if baseline >= item["target"]:
                baseline = item["current"]
            if stored is not None:
                stored[store_key] = {"campaign": campaign, "baseline": baseline,
                                     "target": item["target"], "due": item["due"]}
        gap = item["target"] - baseline
        percent = max(0, min(100, round(100 * (item["current"] - baseline) / gap))) if gap > 0 else 0
        item["progress"] = {"baseline": baseline, "current": item["current"],
                            "target": item["target"], "percent": percent,
                            "label": (f"{signed(item['current'])} / {signed(item['target'])}"
                                      if item["metric"].startswith("net:") else
                                      f"{item['current']:,.0f} / {item['target']:,.0f}")}
    return {"goals": goals[:5], "goal_catalog": goals, "alerts": alerts[:4],
            "window": f"{year + 5}–{year + 10}" if year else "Next 5–10 years",
            "benchmark": build_campaign_benchmark(snapshot)}
