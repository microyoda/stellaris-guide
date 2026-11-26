"""Read-only accuracy verifier and tech-graph exporter for Stellaris Guide.

Usage examples:
  python scripts/verify_guidelines.py --save "path/to/autosave.sav"
  python scripts/verify_guidelines.py --game-dir "C:/Program Files (x86)/Steam/steamapps/common/Stellaris"
  python scripts/verify_guidelines.py --game-dir "..." --save "..." --export-tech-graph
"""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stellaris_guide.advice import make_advice
from stellaris_guide.dlcs import extract_script_dlc_requirements
from stellaris_guide.playbooks import load_playbooks
from stellaris_guide.saves import block, game_release, matching_brace, parse_save, pretty_tech, scalar
from stellaris_guide.tech_route import TECH_ENTRY, _one_of_groups, _parse_prerequisites

MAX_TECH_FILE_BYTES = 2_000_000
MAX_TECH_TOTAL_BYTES = 16_000_000


def _read_bounded_text(path: Path, root: Path, limit: int = 2_000_000) -> str | None:
    try:
        resolved = path.resolve()
        if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
            return None
        if resolved.stat().st_size > limit:
            return None
        return resolved.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return None


def audit_game_dir(game_dir: Path) -> dict:
    """Verify installed Stellaris version, checksum, playbook file refs, and key defines."""
    root = game_dir.resolve()
    result: dict = {
        "game_dir": str(root),
        "version": None,
        "checksum": None,
        "playbooks": [],
        "defines_checked": {},
    }
    settings_text = _read_bounded_text(root / "launcher-settings.json", root, 1_000_000)
    if settings_text:
        try:
            data = json.loads(settings_text)
            if isinstance(data, dict):
                installed = str(data.get("version") or "")
                result["version"] = installed or None
                m = re.search(r"\(([A-Za-z0-9]{4})\)\s*$", installed)
                result["checksum"] = m.group(1) if m else None
        except (ValueError, TypeError):
            pass

    installed_release = game_release(result["version"])
    for record in load_playbooks():
        missing_files = []
        for src in record.get("sources") or []:
            if src.get("kind") == "installed-game":
                for part in str(src.get("ref") or "").split(";"):
                    rel = part.strip()
                    if not rel:
                        continue
                    candidate = (root / rel).resolve()
                    if not candidate.is_relative_to(root) or not candidate.is_file():
                        missing_files.append(rel)
        release_match = bool(installed_release and installed_release == record["validated_release"])
        checksum_match = bool(result["checksum"] and result["checksum"].upper() == record["validated_checksum"].upper())
        result["playbooks"].append({
            "id": record["id"],
            "validated_release": record["validated_release"],
            "validated_checksum": record["validated_checksum"],
            "release_match": release_match,
            "checksum_match": checksum_match,
            "missing_game_files": missing_files,
            "rules_status": record["rules_status"],
            "strategy_status": record["strategy_status"],
        })

    defines_text = _read_bounded_text(root / "common" / "defines" / "00_defines.txt", root, 4_000_000)
    if defines_text:
        for key in (
            "MARKET_FEE", "MIN_MARKET_FEE", "MAX_MARKET_FEE",
            "BASE_RESOURCE_STORAGE_CAP", "INFLUENCE_STORAGE_CAP",
            "STABILITY_REVOLT_THRESHOLD",
        ):
            m = re.search(r"(?m)^\s*" + re.escape(key) + r"\s*=\s*([^\s#]+)", defines_text)
            if m:
                result["defines_checked"][key] = m.group(1)
    return result


def reconcile_save(save_path: Path, game_dir: str = "") -> dict:
    """Parse one save read-only and produce a screen-by-screen reconciliation checklist."""
    snap = parse_save(save_path, include_details=True, game_dir=game_dir)
    advice = make_advice(snap, [snap], {})
    player = snap.get("player") or {}
    return {
        "file": save_path.name,
        "empire": snap.get("empire"),
        "date": snap.get("date"),
        "version": snap.get("version"),
        "active_dlcs": (snap.get("campaign", {}).get("dlc_summary") or {}).get("active_ids", []),
        "mods": snap.get("campaign", {}).get("mods") or [],
        "profile": player.get("profile") or {},
        "top_bar_check": {
            "net": player.get("net"),
            "stock": player.get("stock"),
            "military": player.get("military"),
            "naval_used": player.get("naval_used"),
            "starbases": f"{player.get('starbase_used')}/{player.get('starbase_capacity')}",
            "empire_size": player.get("empire_size"),
            "colonies": player.get("colonies"),
        },
        "colonies": [
            {
                "name": p["name"], "designation": p["designation"],
                "stability": p["stability"], "free_amenities": p["free_amenities"],
                "free_housing": p["free_housing"], "pops": p["pops"],
                "recommendation": p["recommendation"]["title"],
            }
            for p in snap.get("planets", [])
        ],
        "goals": [
            {
                "key": g["key"], "title": g["title"], "severity": g["severity"],
                "playbook": (g.get("playbook") or {}).get("id"),
                "rules_status": (g.get("playbook") or {}).get("rules_status"),
                "strategy_status": (g.get("playbook") or {}).get("strategy_status"),
            }
            for g in advice.get("goals", [])
        ],
        "alerts": advice.get("alerts", []),
    }


def export_tech_graph(game_dir: Path, output_path: Path) -> dict:
    """Extract structural-only tech graph (no copyrighted localization prose/art)."""
    root = game_dir.resolve()
    tech_dir = (root / "common" / "technology").resolve()
    if not tech_dir.is_relative_to(root) or not tech_dir.is_dir():
        raise FileNotFoundError(f"Technology directory not found: {tech_dir}")
    rules: dict[str, dict] = {}
    total_bytes = 0
    for path in sorted(tech_dir.glob("*.txt"))[:200]:
        resolved = path.resolve()
        if not resolved.is_relative_to(tech_dir) or not resolved.is_file():
            continue
        size = resolved.stat().st_size
        total_bytes += size
        if size > MAX_TECH_FILE_BYTES or total_bytes > MAX_TECH_TOTAL_BYTES:
            continue
        source = resolved.read_text(encoding="utf-8-sig", errors="replace")
        for match in TECH_ENTRY.finditer(source):
            tech_id = match.group(1)
            opening = source.find("{", match.start(), match.end())
            try:
                body = source[opening:matching_brace(source, opening)]
            except ValueError:
                continue
            potential = block(body, "potential")
            direct = block(body, "prerequisites")
            prereqs, prereq_or, _ = _parse_prerequisites(direct)
            tier_raw = scalar(body, "tier", "")
            rules[tech_id] = {
                "name": pretty_tech(tech_id),
                "area": scalar(body, "area", ""),
                "tier": int(tier_raw) if str(tier_raw).isdigit() else None,
                "prerequisites": prereqs,
                "one_of": prereq_or + _one_of_groups(potential),
                "required_dlc": extract_script_dlc_requirements(potential),
            }
    if not rules:
        raise ValueError("No technologies were parsed; existing tech_graph.json was left unchanged.")
    gates: dict[str, int] = {}
    tier_text = _read_bounded_text(tech_dir / "tier" / "00_tier.txt", tech_dir, 200_000)
    if tier_text:
        for match in re.finditer(r"(?m)^(\d+)\s*=\s*\{", tier_text):
            opening = tier_text.find("{", match.start(), match.end())
            try:
                body = tier_text[opening:matching_brace(tier_text, opening)]
            except ValueError:
                continue
            count = scalar(body, "previously_unlocked")
            if str(count).isdigit():
                gates[match.group(1)] = int(count)
    release = "unknown"
    settings_text = _read_bounded_text(root / "launcher-settings.json", root, 1_000_000)
    if settings_text:
        try:
            release = str(json.loads(settings_text).get("version") or "unknown")
        except (ValueError, TypeError, AttributeError):
            pass
    payload = {
        "schema": 1,
        "baseline_release": release,
        "partial": False,
        "source_note": "Derived structural tech graph (IDs, tiers, prerequisites, DLC triggers). No copyrighted game text or art.",
        "gates": gates or {"1": 0, "2": 6, "3": 6, "4": 6, "5": 6},
        "rules": rules,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_name(f"{output_path.name}.{secrets.token_hex(6)}.tmp")
    try:
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, output_path)
    finally:
        tmp.unlink(missing_ok=True)
    return {"exported_techs": len(rules), "release": release, "output": str(output_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify Stellaris Guide rules against installed files and saves.")
    parser.add_argument("--game-dir", type=str, default="", help="Path to local Stellaris installation folder")
    parser.add_argument("--save", type=str, default="", help="Path to a .sav file to reconcile read-only")
    parser.add_argument("--export-tech-graph", action="store_true",
                        help="Export full structural tech graph to stellaris_guide/tech_graph.json")
    args = parser.parse_args()

    report: dict = {}
    if args.game_dir:
        game_path = Path(args.game_dir)
        report["game_audit"] = audit_game_dir(game_path)
        if args.export_tech_graph:
            report["tech_graph_export"] = export_tech_graph(
                game_path, ROOT / "stellaris_guide" / "tech_graph.json"
            )
    if args.save:
        report["save_reconciliation"] = reconcile_save(Path(args.save), args.game_dir)
    if not report:
        parser.print_help()
        return
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
