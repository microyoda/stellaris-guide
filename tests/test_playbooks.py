"""Reviewed playbook matching, version gating and goal integration."""

import json
import tempfile
import unittest
from pathlib import Path

from stellaris_guide.chat_evidence import build_evidence_packet
from stellaris_guide.playbooks import load_playbooks, match_playbook
from stellaris_guide.strategy import make_plan


def snapshot():
    return {
        "date": "2277.10.01", "path": "campaign/autosave.sav",
        "campaign": {"id": "playbook-test", "save_version": "Cygnus v4.5.2",
                     "mods": [], "installed": {"version": "4.5.2 (9776)", "checksum": "9776"}},
        "player": {"net": {"food": -10, "energy": 10, "alloys": 30},
                   "stock": {"food": 20, "energy": 100, "alloys": 200}, "military": 1000},
        "planets": [{"id": 2, "name": "Colony", "free_amenities": -4,
                     "stability": 40, "designation": "Farming", "produces": {"food": 3},
                     "recommendation": {"level": "urgent", "action": "Check amenities",
                                        "reason": "Amenities are low."}}],
        "contacts": [], "ship_builds": {"recommendation": {}}, "policies": {},
    }


class PlaybookTests(unittest.TestCase):
    def setUp(self):
        self.records = {item["id"]: item for item in load_playbooks()}

    def test_matching_goal_keeps_existing_rank_and_shows_separate_statuses(self):
        current = snapshot()
        result = make_plan(current, [current], {})
        self.assertEqual([goal["key"] for goal in result["goals"][:2]],
                         ["deficit:food", "colony:2"])
        self.assertEqual(result["goals"][0]["playbook"]["id"], "resource-deficit-recovery")
        self.assertEqual(result["goals"][0]["playbook"]["match"], "matched")
        self.assertEqual(result["goals"][0]["playbook"]["rules_status"], "conditional")
        self.assertEqual(result["goals"][0]["playbook"]["strategy_status"], "untested")
        self.assertEqual(result["goals"][1]["playbook"]["id"], "unstable-colony")
        self.assertEqual(result["goals"][0]["source_rule"], "Guide v1.6 heuristic")

    def test_nonfitting_and_missing_data_are_distinct(self):
        current = snapshot()
        make_plan(current, [current], {})
        record = self.records["resource-deficit-recovery"]
        self.assertIsNone(match_playbook(record, current, {"key": "deficit:energy"}))
        self.assertIsNone(match_playbook(record, current, {"key": "fleet"}))
        current["resource_runway"]["food"].pop("status")
        self.assertEqual(match_playbook(record, current, {"key": "deficit:food"})["match"],
                         "investigate")
        colony = self.records["unstable-colony"]
        current["planets"][0]["stability"] = 70
        current["planets"][0]["free_amenities"] = 3
        self.assertIsNone(match_playbook(colony, current, {"key": "colony:2"}))
        current["planets"][0].pop("stability")
        self.assertEqual(match_playbook(colony, current, {"key": "colony:2"})["match"],
                         "investigate")

    def test_version_checksum_and_mod_gate_are_automatic(self):
        current = snapshot()
        make_plan(current, [current], {})
        record = self.records["resource-deficit-recovery"]
        goal = {"key": "deficit:food"}
        current["campaign"]["save_version"] = "Corona Borealis v4.6.0"
        self.assertEqual(match_playbook(record, current, goal)["rules_status"], "needs recheck")
        current["campaign"]["save_version"] = "Cygnus v4.5.2"
        current["campaign"]["installed"]["checksum"] = "ABCD"
        self.assertEqual(match_playbook(record, current, goal)["rules_status"], "needs recheck")
        current["campaign"]["installed"]["checksum"] = "9776"
        current["campaign"]["mods"] = ["Unknown balance mod"]
        self.assertEqual(match_playbook(record, current, goal)["rules_status"], "conditional")
        for authored in ("conflict", "needs recheck"):
            changed = dict(record, rules_status=authored)
            self.assertEqual(match_playbook(changed, current, goal)["rules_status"], authored)

    def test_retired_playbook_is_suppressed(self):
        current = snapshot()
        make_plan(current, [current], {})
        record = dict(self.records["resource-deficit-recovery"])
        record["strategy_status"] = "retired"
        self.assertIsNone(match_playbook(record, current, {"key": "deficit:food"}))

    def test_chat_does_not_send_playbooks_to_model(self):
        current = snapshot()
        advice = make_plan(current, [current], {})
        packet = build_evidence_packet(current, advice, "How is my food?", "main")
        records = [item for item in packet["references"].values() if item.get("kind") == "goal"]
        self.assertFalse(any("playbook" in item for item in records))
        advice["goals"][0]["playbook"] = dict(advice["goals"][0]["playbook"],
                                               rules_status="verified", strategy_status="tested")
        qualified = build_evidence_packet(current, advice, "How is my food?", "main")
        records = [item for item in qualified["references"].values() if item.get("kind") == "goal"]
        self.assertFalse(any("playbook" in item for item in records))

    def test_unknown_fact_or_operator_fails_validation(self):
        record = self.records["resource-deficit-recovery"]
        for condition in ({"fact": "player.ethics", "op": "eq", "value": "x"},
                          {"fact": "player.net.{resource}", "op": "exec", "value": 0}):
            changed = dict(record)
            changed["conditions"] = [condition]
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "playbooks.json"
                path.write_text(json.dumps([changed]), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_playbooks(path)


if __name__ == "__main__":
    unittest.main()
