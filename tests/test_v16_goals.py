"""Goal record, rank and spoiler boundaries for v1.6 Phase 3."""
import json
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from stellaris_guide import server
from stellaris_guide.strategy import make_plan


def snapshot():
    return {
        "date": "2277.10.01", "path": "campaign/autosave.sav", "empire": "Player",
        "campaign": {"id": "aaaaaaaaaaaaaaaa", "save_version": "Cygnus v4.5.2"},
        "player": {"net": {"food": -10, "energy": 20, "alloys": 30},
                   "stock": {"food": 0, "energy": 100, "alloys": 200},
                   "military": 1000},
        "planets": [{"id": 2, "name": "Colony", "designation": "Farming",
                     "produces": {"food": 3}, "free_amenities": -8, "stability": 35,
                     "recommendation": {"level": "urgent", "action": "Check amenities", "reason": "Amenities are low."}}],
        "contacts": [{"id": 9, "name": "Visible Rival", "opinion": -100,
                      "military": 99999, "hidden": {"stock": 88888}}],
        "ship_builds": {"recommendation": {}}, "policies": {},
    }


class GoalTests(unittest.TestCase):
    def test_rank_and_traceable_record(self):
        current = snapshot()
        result = make_plan(current, [current], {})
        self.assertEqual(result["goals"][0]["key"], "deficit:food")
        self.assertEqual(result["goals"][1]["key"], "colony:2")
        record = result["goals"][0]
        for field in ("id", "snapshot_date", "observation", "action", "reason",
                      "expected_effect", "trade_off", "in_game_check", "severity",
                      "source_rule", "source_game_version", "visibility", "rank_reason", "progress"):
            self.assertIn(field, record)
        self.assertEqual(record["severity"], "urgent")
        self.assertEqual(record["snapshot_date"], current["date"])
        self.assertEqual(record["source_game_version"], "Cygnus v4.5.2")
        self.assertTrue(any(a["title"] == "Food stock risk" for a in result["alerts"]))
        self.assertEqual([g["key"] for g in result["goals"]],
                         [g["key"] for g in make_plan(current, [current], {})["goals"]])

    def test_no_hidden_rival_values_enter_goal_or_catalog(self):
        current = snapshot()
        result = make_plan(current, [current], {})
        text = json.dumps({"goals": result["goals"], "catalog": result["goal_catalog"]})
        self.assertNotIn("99999", text)
        self.assertNotIn("88888", text)
        self.assertIn("Visible Rival", text)

    def test_reused_save_folder_does_not_inherit_other_campaign_progress(self):
        first = snapshot()
        stored = {}
        first_goal = next(g for g in make_plan(first, [first], stored)["goals"] if g["key"] == "deficit:food")
        second = snapshot()
        second["campaign"]["id"] = "bbbbbbbbbbbbbbbb"
        second["date"] = "2300.01.01"
        second["player"]["net"]["food"] = -2
        second_goal = next(g for g in make_plan(second, [second], stored)["goals"] if g["key"] == "deficit:food")
        self.assertEqual(first_goal["due"], 2280)
        self.assertEqual(second_goal["due"], 2303)
        self.assertEqual(second_goal["progress"]["baseline"], -2)
        self.assertIn("aaaaaaaaaaaaaaaa|deficit:food", stored)
        self.assertIn("bbbbbbbbbbbbbbbb|deficit:food", stored)

    def test_pin_persists_by_campaign_and_rejects_stale_or_unknown_goals(self):
        current = snapshot()
        advice = make_plan(current, [current], {})
        old_pins = dict(server.PINS)
        try:
            with tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                with mock.patch.object(server, "CONFIG_DIR", root), mock.patch.object(server, "PINS_PATH", root / "pins-v1.6.json"):
                    server.PINS.clear()
                    selected = server.update_pin(current, advice, "aaaaaaaaaaaaaaaa", "deficit:food")
                    self.assertEqual(selected["key"], "deficit:food")
                    self.assertNotIn("campaign/autosave.sav", server.PINS_PATH.read_text())
                    server.PINS.clear()
                    server.load_pins()  # app restart on a new random local port
                    self.assertEqual(server.pin_for(current)["key"], "deficit:food")
                    other = snapshot()
                    other["campaign"]["id"] = "bbbbbbbbbbbbbbbb"
                    self.assertIsNone(server.pin_for(other))
                    with self.assertRaises(ValueError):
                        server.update_pin(other, advice, "aaaaaaaaaaaaaaaa", "deficit:food")
                    with self.assertRaises(ValueError):
                        server.update_pin(current, advice, "aaaaaaaaaaaaaaaa", "not-a-goal")
                    # A disappearing goal remains dormant until the player clears it.
                    self.assertEqual(server.pin_for(current)["key"], "deficit:food")
                    self.assertIsNone(server.update_pin(current, {"goals": []}, "aaaaaaaaaaaaaaaa", None))
                    self.assertIsNone(server.pin_for(current))
        finally:
            server.PINS.clear()
            server.PINS.update(old_pins)

    def test_failed_pin_write_restores_prior_record(self):
        current = snapshot()
        advice = make_plan(current, [current], {})
        old_pins = dict(server.PINS)
        try:
            server.PINS.clear()
            server.PINS["aaaaaaaaaaaaaaaa"] = {"key": "old", "title": "Old goal"}
            with mock.patch.object(server, "save_pins", side_effect=OSError("denied")):
                with self.assertRaises(OSError):
                    server.update_pin(current, advice, "aaaaaaaaaaaaaaaa", "deficit:food")
            self.assertEqual(server.pin_for(current)["key"], "old")
        finally:
            server.PINS.clear()
            server.PINS.update(old_pins)

    def test_post_body_requires_object(self):
        request = SimpleNamespace(headers={"Content-Length": "2"}, rfile=io.BytesIO(b"[]"))
        with self.assertRaises(ValueError):
            server.Handler.read_body(request)
        request = SimpleNamespace(headers={"Content-Length": "2"}, rfile=io.BytesIO(b"{}"))
        self.assertEqual(server.Handler.read_body(request), {})

    def test_pin_file_remains_within_reload_limit(self):
        old_pins = dict(server.PINS)
        try:
            with tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                with mock.patch.object(server, "CONFIG_DIR", root), mock.patch.object(server, "PINS_PATH", root / "pins-v1.6.json"):
                    server.PINS.clear()
                    for value in range(160):
                        server.PINS[f"{value:016x}"] = {"key": "k" * 100, "title": "t" * 160}
                    server.save_pins()
                    self.assertLess(server.PINS_PATH.stat().st_size, 64_000)
                    server.PINS.clear()
                    server.load_pins()
                    self.assertEqual(len(server.PINS), 150)
                    self.assertIn(f"{159:016x}", server.PINS)
        finally:
            server.PINS.clear()
            server.PINS.update(old_pins)

    def test_pin_route_needs_token_and_selected_campaign(self):
        current = snapshot()
        advice = make_plan(current, [current], {})
        responses = []
        request = SimpleNamespace(
            path="/api/pin", headers={"X-Guide-Token": "wrong"},
            host_is_local=lambda: True,
            read_body=lambda: {"campaign_id": "aaaaaaaaaaaaaaaa", "goal_key": "deficit:food"},
            send_json=lambda payload, status=200: responses.append((status, payload)),
        )
        server.Handler.do_POST(request)
        self.assertEqual(responses[-1][0], 403)
        old_pins = dict(server.PINS)
        try:
            with tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                with mock.patch.object(server, "CONFIG_DIR", root), mock.patch.object(server, "PINS_PATH", root / "pins-v1.6.json"), mock.patch.dict(server.STATE, {"snapshot": current, "advice": advice}):
                    server.PINS.clear()
                    request.headers["X-Guide-Token"] = server.TOKEN
                    request.read_body = lambda: {"campaign_id": "bbbbbbbbbbbbbbbb", "goal_key": "deficit:food"}
                    server.Handler.do_POST(request)
                    self.assertEqual(responses[-1][0], 400)
                    self.assertFalse(server.PINS)
                    request.read_body = lambda: {"campaign_id": "aaaaaaaaaaaaaaaa", "goal_key": "deficit:food"}
                    server.Handler.do_POST(request)
                    self.assertEqual(responses[-1][0], 200)
                    self.assertEqual(responses[-1][1]["pin"]["key"], "deficit:food")
        finally:
            server.PINS.clear()
            server.PINS.update(old_pins)


if __name__ == "__main__":
    unittest.main()
