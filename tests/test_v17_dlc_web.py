"""Tests for DLC normalization, empire profiles, Trade/Willpower/Nomads, and Option 1 Web build."""

from __future__ import annotations

import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.build_web import build_web
from scripts.verify_guidelines import audit_game_dir, export_tech_graph, reconcile_save
from stellaris_guide.advice import answer_question
from stellaris_guide.dlcs import (
    active_dlcs,
    detect_dlc_drift,
    dlc_status_list,
    extract_script_dlc_requirements,
    has_dlc,
)
from stellaris_guide.playbooks import load_playbooks, match_playbook
from stellaris_guide.saves import parse_save_bytes, planet_recommendation
from stellaris_guide.strategy import make_plan, resource_steps
from stellaris_guide.tech_route import route_for_target
from stellaris_guide.web_bridge import (
    analyze_save_archive,
    ask_builtin,
    build_demo_state,
    public_snapshot,
    reproject_current_save,
    web_route_for_target,
    web_route_targets,
)


def make_sav_bytes(meta: str, gamestate: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("meta", meta)
        zf.writestr("gamestate", gamestate)
    return buf.getvalue()


SAMPLE_META_452 = (
    'version="Cygnus v4.5.2"\n'
    'date="2277.10.01"\n'
    'name="Machine Collective"\n'
    'required_dlcs={\n'
    '\t"Apocalypse"\n'
    '\t"Ancient Relics Story Pack"\n'
    '}\n'
    'mods={\n}\n'
)

SAMPLE_GAME_MACHINE = """
player={
\t{ name="Player" country=0 }
}
country={
\t0={
\t\tname={ key="NAME_Machine_Collective" }
\t\ttype=default
\t\tmilitary_power=3200
\t\teconomy_power=1500
\t\ttech_power=900
\t\tused_naval_capacity=40
\t\tstarbase_capacity_used=4
\t\tstarbase_capacity=6
\t\tempire_size=120
\t\tgovernment={
\t\t\tauthority="auth_machine_intelligence"
\t\t\torigin="origin_machine"
\t\t\tcivics={ "civic_machine_builder" }
\t\t}
\t\tethos={ ethic="ethic_gestalt_consciousness" }
\t\ttraditions={ "tr_expansion_adopt" }
\t\tresource_stockpile={ energy=200 minerals=300 alloys=500 influence=950 trade=40 }
\t\tbudget={
\t\t\tincome={ energy=50 minerals=20 alloys=40 influence=4 trade=10 physics_research=80 society_research=70 engineering_research=90 }
\t\t\texpenses={ energy=30 minerals=40 alloys=10 influence=0 trade=25 }
\t\t}
\t\tcontacts={ 1 }
\t\towned_planets={ 1 }
\t\tactive_policies={
\t\t\t{ policy="fleet_doctrine" selected="battle_line" }
\t\t}
\t\ttech_status={
\t\t\ttechnology="tech_corvettes" level=1
\t\t\talternatives={ physics={ "tech_lasers_2" } society={ "tech_doctrine_navy_size_1" } engineering={ "tech_mining_2" } }
\t\t}
\t}
\t1={
\t\tname={ key="NAME_Hidden_Rival" }
\t\ttype=default
\t\tmilitary_power=99999
\t\teconomy_power=88888
\t\ttech_power=77777
\t\tresource_stockpile={ alloys=55555 }
\t\tbudget={ income={ alloys=100 } expenses={ alloys=10 } }
\t}
}
colony={
\t1={
\t\tfinal_designation="col_mining"
\t\tstability=22
\t\tcrime=5
\t\tnum_sapient_pops=2000
\t\tfree_housing=400
\t\tfree_amenities=300
\t\tpop_jobs={ 10 }
\t\tproduces={ minerals=30 }
\t\tupkeep={ energy=8 }
\t}
}
pop_jobs={
\t10={ type="mining_drone" workforce=200 max_workforce=800 workforce_limit=800 }
}
planets={
\tplanet={
\t\t5={
\t\t\tname={ key="NAME_Prime_Node" }
\t\t\tplanet_class="pc_machine"
\t\t\tplanet_size=18
\t\t\tcolony=1
\t\t}
\t}
}
ship_design={}
"""


class DlcRegistryTests(unittest.TestCase):
    def test_extracts_shorthand_and_host_dlc_triggers(self):
        script = (
            'potential = {\n'
            '  # has_overlord_dlc = yes\n'
            '  NOT = { has_first_contact_dlc = yes }\n'
            '  NOR = { host_has_dlc = "Nemesis" }\n'
            '  host_has_dlc = "Apocalypse"\n'
            '  has_ancrel = yes\n'
            '  has_megacorp = yes\n'
            '  has_nomads_dlc = yes\n'
            '  has_willpower_dlc = yes\n'
            '  has_synthethic_dawn = yes\n'
            '}\n'
        )
        found = extract_script_dlc_requirements(script)
        for expected in ("apocalypse", "ancient_relics", "megacorp", "nomads", "willpower", "synthetic_dawn"):
            self.assertIn(expected, found)
        for excluded in ("overlord", "first_contact", "nemesis"):
            self.assertNotIn(excluded, found)
        # Unknown cosmetic labels should not falsely match paid DLCs by substring.
        self.assertEqual(active_dlcs(["Shroud-Touched Cosmetics"], "Cygnus v4.5.2")["unknown_labels"],
                         ["Shroud-Touched Cosmetics"])
        self.assertNotIn("shadows_of_the_shroud",
                         active_dlcs(["Shroud-Touched Cosmetics"], "Cygnus v4.5.2")["active_ids"])

    def test_utopia_and_synthetic_dawn_promoted_to_base_game_in_45(self):
        summary_45 = active_dlcs([], "Cygnus v4.5.2")
        self.assertIn("utopia", summary_45["active_ids"])
        self.assertIn("synthetic_dawn", summary_45["active_ids"])
        self.assertIn("humanoids", summary_45["active_ids"])

        summary_43 = active_dlcs([], "v4.3.0")
        self.assertNotIn("utopia", summary_43["active_ids"])

        status = dlc_status_list(["has_utopia", "has_ancrel", "has_overlord_dlc"],
                                 ["Ancient Relics Story Pack"], "Cygnus v4.5.2")
        by_id = {item["id"]: item for item in status}
        self.assertEqual(by_id["utopia"]["status"], "present")
        self.assertTrue(by_id["utopia"]["base_game"])
        self.assertEqual(by_id["ancient_relics"]["status"], "present")
        self.assertEqual(by_id["overlord"]["status"], "not_listed")

    def test_dlc_drift_detects_added_and_removed_dlcs(self):
        prior = {"campaign": {"id": "c1", "required_dlcs": ["Overlord", "Nomads"]}}
        current = {"campaign": {"id": "c1", "required_dlcs": ["Overlord", "Willpower"]}}
        other = {"campaign": {"id": "c2", "required_dlcs": ["Apocalypse"]}}
        drift = detect_dlc_drift(current, [other, prior, current])
        self.assertTrue(drift["changed"])
        self.assertIn("Willpower", drift["added"])
        self.assertIn("Nomads", drift["removed"])

    def test_tech_route_handles_ancrel_and_utopia_triggers(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            tech_dir = root / "common" / "technology"
            tech_dir.mkdir(parents=True)
            (tech_dir / "00_dlc.txt").write_text(
                'tech_relic_weapon = { area = physics tier = 2 potential = { has_ancrel = yes } }\n'
                'tech_ringworld = { area = engineering tier = 3 potential = { has_utopia = yes } }\n',
                encoding="utf-8",
            )
            tier = tech_dir / "tier" / "00_tier.txt"
            tier.parent.mkdir()
            tier.write_text("2 = { previously_unlocked = 0 }\n3 = { previously_unlocked = 0 }\n")
            snap = {
                "date": "2280.01.01", "modified": 1, "version": "Cygnus v4.5.2",
                "campaign": {"id": "c1", "save_version": "Cygnus v4.5.2",
                             "required_dlcs": ["Ancient Relics Story Pack"], "mods": [],
                             "installed": {"version_match": "match"}},
                "technology": {"researched_status": "complete", "researched": {}, "branches": {}},
            }
            relic = route_for_target(snap, str(root), "tech_relic_weapon")
            self.assertEqual(relic["status"], "verified_base_game")
            self.assertEqual(relic["dlc"][0]["status"], "present")
            utopia = route_for_target(snap, str(root), "tech_ringworld")
            self.assertEqual(utopia["status"], "verified_base_game")
            self.assertTrue(utopia["dlc"][0]["base_game"])


class ProfileAndReliabilityTests(unittest.TestCase):
    def test_parse_save_bytes_machine_profile_trade_revolt_and_cap(self):
        raw = make_sav_bytes(SAMPLE_META_452, SAMPLE_GAME_MACHINE)
        snap = parse_save_bytes(raw, "autosave.sav")
        profile = snap["player"]["profile"]
        self.assertTrue(profile["is_machine"])
        self.assertTrue(profile["is_gestalt"])
        self.assertFalse(profile["uses_consumer_goods"])
        self.assertFalse(profile["uses_food"])
        self.assertEqual(snap["player"]["net"]["trade"], -15.0)
        self.assertEqual(snap["planets"][0]["recommendation"]["title"], "Prevent colony revolt")

        # Gestalt drone jobs are matched in resource_steps.
        steps = resource_steps(snap, "minerals")
        self.assertTrue(any("mining drone" in item["action"] for item in steps))

        plan = make_plan(snap, [snap], {})
        goal_keys = [g["key"] for g in plan["goals"]]
        self.assertIn("deficit:trade", goal_keys)
        self.assertIn("deficit:minerals", goal_keys)
        trade_goal = next(g for g in plan["goals"] if g["key"] == "deficit:trade")
        self.assertEqual(trade_goal["playbook"]["id"], "trade-and-market-deficit")
        colony_goal = next(g for g in plan["goals"] if g["key"] == "colony:1")
        self.assertEqual(colony_goal["metric"], "stability:1")
        self.assertEqual(colony_goal["target"], 50)
        self.assertTrue(any(a["title"] == "Influence near cap" for a in plan["alerts"]))

    def test_parse_save_bytes_rejects_bad_archive(self):
        with self.assertRaises((ValueError, zipfile.BadZipFile)):
            parse_save_bytes(b"not-a-zip", "broken.sav")
        missing_game = io.BytesIO()
        with zipfile.ZipFile(missing_game, "w") as zf:
            zf.writestr("meta", SAMPLE_META_452)
        with self.assertRaises(ValueError):
            parse_save_bytes(missing_game.getvalue(), "incomplete.sav")

    def test_dlc_gated_playbooks_and_willpower_version_gate(self):
        records = {item["id"]: item for item in load_playbooks()}
        nomad_snap = build_demo_state("nomads-452")["snapshot"]
        self.assertEqual(
            match_playbook(records["nomad-arkship-fleet"], nomad_snap, {"key": "fleet"})["match"],
            "matched",
        )
        # Removing Nomads DLC suppresses the Nomad playbook.
        nomad_snap_no_dlc = dict(nomad_snap)
        nomad_snap_no_dlc["campaign"] = {**nomad_snap["campaign"], "required_dlcs": []}
        self.assertIsNone(match_playbook(records["nomad-arkship-fleet"], nomad_snap_no_dlc, {"key": "fleet"}))

        # Apocalypse playbook respects present / absent / unknown DLC metadata.
        une_snap = build_demo_state("une-452")["snapshot"]
        self.assertEqual(
            match_playbook(records["fleet-apocalypse-capital"], une_snap, {"key": "fleet"})["match"],
            "matched",
        )
        une_no_apoc = build_demo_state("une-452", enabled_dlc_ids=[])["snapshot"]
        self.assertIsNone(match_playbook(records["fleet-apocalypse-capital"], une_no_apoc, {"key": "fleet"}))
        une_unknown_dlc = dict(une_snap)
        une_unknown_dlc["campaign"] = {**une_snap["campaign"], "required_dlcs": None}
        self.assertEqual(
            match_playbook(records["fleet-apocalypse-capital"], une_unknown_dlc, {"key": "fleet"})["match"],
            "investigate",
        )

        # Willpower Ideologies question gating: 4.5.2 vs 4.6 without Willpower vs 4.6 with Willpower.
        ans_45 = answer_question("How do ideologies work in Willpower?", une_snap)
        self.assertIn("predates Stellaris 4.6", ans_45)

        wp_state = build_demo_state("willpower-460")
        ans_46 = answer_question("How do ideologies work in Willpower?", wp_state["snapshot"])
        self.assertIn("Fanatic Faction", ans_46)
        self.assertTrue(any(a["title"] == "Check Ideology upkeep" for a in wp_state["advice"]["alerts"]))

        wp_no_dlc = build_demo_state("willpower-460", enabled_dlc_ids=[])["snapshot"]
        ans_46_no_dlc = answer_question("How do ideologies work?", wp_no_dlc)
        self.assertIn("Willpower DLC is not recorded", ans_46_no_dlc)

        # Trade & Storage question works with RedEye 4.5.2 guidance.
        ans_trade = answer_question("How do trade and storage caps work?", une_snap)
        self.assertIn("15,000", ans_trade)
        self.assertIn("Trade", ans_trade)

    def test_stability_revolt_threshold(self):
        rec = planet_recommendation(
            {"name": "Rim World", "free_amenities": 5, "free_housing": 5,
             "stability": 20, "designation_key": "col_colony"},
            {},
        )
        self.assertEqual(rec["level"], "urgent")
        self.assertEqual(rec["title"], "Prevent colony revolt")


class WebBridgeAndBuildTests(unittest.TestCase):
    def test_web_bridge_spoiler_isolation_and_builtin_chat(self):
        raw = make_sav_bytes(SAMPLE_META_452, SAMPLE_GAME_MACHINE)
        safe = analyze_save_archive(raw, "autosave.sav", spoilers_active=False)
        self.assertNotIn("raw_snapshot", safe)
        self.assertNotIn("_save_fingerprint", json.dumps(safe))
        self.assertNotIn("99999", json.dumps(safe["snapshot"]))
        self.assertNotIn("55555", json.dumps(safe["snapshot"]))
        self.assertFalse(safe["snapshot"]["_spoilers_active"])

        # Reprojection toggles spoilers across both snapshot and history cleanly.
        spoiled = reproject_current_save(spoilers_active=True)
        self.assertEqual(spoiled["snapshot"]["contacts"][0]["military"], 99999)
        self.assertEqual(spoiled["history"][-1]["contacts"][0]["military"], 99999)
        self.assertTrue(spoiled["snapshot"]["_spoilers_active"])

        # Demo contacts with spoilers off are sorted by name (not hidden military power).
        demo = build_demo_state("une-452", spoilers_active=False)
        names = [c["name"] for c in demo["snapshot"]["contacts"]]
        self.assertEqual(names, sorted(names, key=str.casefold))

        reply = ask_builtin("What's my economy looking like?", safe["snapshot"], safe["advice"])
        self.assertIn("minerals -20.0/month", reply["answer"])
        self.assertIn("trade -15.0/month", reply["answer"])

    def test_static_web_build_excludes_desktop_only_modules(self):
        with tempfile.TemporaryDirectory() as folder:
            out = build_web(Path(folder) / "dist-web")
            self.assertTrue((out / "index.html").is_file())
            self.assertTrue((out / "demo-snapshots.json").is_file())
            self.assertTrue((out / "web-runtime.js").is_file())
            self.assertTrue((out / "web-worker.js").is_file())
            self.assertTrue((out / ".nojekyll").is_file())
            html = (out / "index.html").read_text(encoding="utf-8")
            self.assertIn("./web-runtime.js", html)
            self.assertIn("./web.css", html)
            self.assertNotIn('src="/', html)
            py_dir = out / "py" / "stellaris_guide"
            self.assertTrue((py_dir / "dlcs.py").is_file())
            self.assertTrue((py_dir / "web_bridge.py").is_file())
            self.assertTrue((py_dir / "tech_graph.json").is_file())
            self.assertTrue((out / "art.js").is_file())
            for forbidden in ("capture.py", "tray.py", "route_window.py", "server.py", "chat_evidence.py"):
                self.assertFalse((py_dir / forbidden).exists())
            bundle = json.loads((out / "demo-snapshots.json").read_text(encoding="utf-8"))
            self.assertIn("une-452", bundle["states"])
            self.assertIn("nomads-452", bundle["states"])
            self.assertIn("willpower-460", bundle["states"])

    def test_web_tech_route_explorer_and_verifier_script(self):
        demo = build_demo_state("une-452")
        snap = demo["snapshot"]
        # Overview labels and Tier 2 gates are populated in web mode.
        self.assertIn("overview", snap["technology"])
        self.assertIn("tech_cruisers", snap["technology"]["overview"]["labels"])
        route = web_route_for_target(snap, "tech_mega_engineering")
        self.assertIn("mega", route["name"].casefold())
        step_ids = [s["id"] for s in route["steps"]]
        self.assertIn("tech_zero_point_power", step_ids)
        self.assertTrue(route["one_of"])
        # Real 4.6.0 exported graph: DLC-gated techs report not_listed when absent and present when active.
        willpower_route = web_route_for_target(snap, "tech_galactic_halls")
        self.assertEqual(willpower_route["dlc"][0]["id"], "willpower")
        self.assertEqual(willpower_route["dlc"][0]["status"], "not_listed")
        wp_snap = build_demo_state("willpower-460")["snapshot"]
        self.assertEqual(web_route_for_target(wp_snap, "tech_galactic_halls")["dlc"][0]["status"], "present")
        relic_route = web_route_for_target(snap, "tech_archaeostudies")
        self.assertEqual(relic_route["dlc"][0]["id"], "ancient_relics")
        self.assertEqual(relic_route["dlc"][0]["status"], "not_listed")
        ark_route = web_route_for_target(snap, "tech_arkship_tier_3")
        self.assertTrue(ark_route["one_of"])
        # Unknown tech degrades honestly without crashing.
        unknown = web_route_for_target(snap, "tech_modded_mystery")
        self.assertEqual(unknown["status"], "unknown")
        self.assertTrue(len(web_route_targets(snap)) >= 50)

        # Verify scripts/verify_guidelines.py against synthetic game dir + save.
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "launcher-settings.json").write_text(json.dumps({"version": "Cygnus v4.5.2 (9776)"}))
            tech_dir = root / "common" / "technology"
            tech_dir.mkdir(parents=True)
            (tech_dir / "00_test.txt").write_text(
                'tech_alpha = { area = physics tier = 1 }\n'
                'tech_beta = { area = physics tier = 2 prerequisites = { tech_alpha } potential = { has_overlord_dlc = yes } }\n'
            )
            audit = audit_game_dir(root)
            self.assertEqual(audit["checksum"], "9776")
            out_graph = root / "exported_graph.json"
            exported = export_tech_graph(root, out_graph)
            self.assertEqual(exported["exported_techs"], 2)
            graph_data = json.loads(out_graph.read_text(encoding="utf-8"))
            self.assertEqual(graph_data["rules"]["tech_beta"]["required_dlc"], ["overlord"])
            sav_path = root / "autosave.sav"
            sav_path.write_bytes(make_sav_bytes(SAMPLE_META_452, SAMPLE_GAME_MACHINE))
            rec = reconcile_save(sav_path)
            self.assertEqual(rec["empire"], "Machine Collective")
            self.assertTrue(rec["profile"]["is_machine"])


        # Public snapshot fails closed: hides low-intel (<10) AND unknown-intel (None) personality unless spoilers are enabled.
        from stellaris_guide import server
        low_intel_snap = {
            "_save_fingerprint": "fp-test-intel",
            "contacts": [
                {"id": 1, "name": "Alpha", "intel": 5, "personality": "fanatical_befrienders", "military": 900, "wars": []},
                {"id": 2, "name": "Beta", "intel": 25, "personality": "hegemonic_imperialists", "military": 400, "wars": []},
                {"id": 3, "name": "Gamma", "intel": None, "personality": "fanatic_purifiers", "military": 700, "wars": []},
            ]
        }
        redacted = public_snapshot(low_intel_snap, spoilers_active=False)
        by_name = {c["name"]: c for c in redacted["contacts"]}
        self.assertNotIn("personality", by_name["Alpha"])
        self.assertNotIn("personality", by_name["Gamma"])
        self.assertEqual(by_name["Beta"]["personality"], "hegemonic_imperialists")
        revealed = public_snapshot(low_intel_snap, spoilers_active=True)
        self.assertEqual(revealed["contacts"][0]["personality"], "fanatical_befrienders")

        srv_redacted = server.public_snapshot(low_intel_snap)
        srv_by_name = {c["name"]: c for c in srv_redacted["contacts"]}
        self.assertNotIn("personality", srv_by_name["Alpha"])
        self.assertNotIn("personality", srv_by_name["Gamma"])
        self.assertEqual(srv_by_name["Beta"]["personality"], "hegemonic_imperialists")

        # Defense-in-depth: threat_answer does not leak personality when intel is None or <10.
        hidden_threat = answer_question("Who should I be worried about?", {
            "contacts": [{"id": 3, "name": "Gamma", "opinion": 50, "intel": None, "personality": "fanatical_befrienders"}],
        })
        self.assertNotIn("Fanatical Befrienders", hidden_threat)


if __name__ == "__main__":
    unittest.main()
