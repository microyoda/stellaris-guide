import unittest

from stellaris_guide import server
from stellaris_guide.saves import parse_job_summary, parse_known_intel, ship_design_check


class V15SaveAndPrivacyTests(unittest.TestCase):
    def test_cygnus_job_capacity_and_disabled_setting(self):
        colony = "{ pop_jobs={ 10 11 } }"
        records = {
            10: '{ type="miner" workforce=250 max_workforce=500 workforce_limit=500 }',
            11: '{ type="entertainer" workforce=0 max_workforce=200 workforce_limit=0 }',
        }
        jobs = {item["type"]: item for item in parse_job_summary(colony, records)}
        self.assertEqual(jobs["miner"]["filled"], 2.5)
        self.assertEqual(jobs["miner"]["capacity"], 5)
        self.assertTrue(jobs["entertainer"]["disabled"])

    def test_player_intel_is_separate_from_foreign_power(self):
        player = "{ intel_manager={ intel={ { 19 { intel=36.5 stale_intel={} } } } }"
        self.assertEqual(parse_known_intel(player), {19: 36.5})
        snapshot = {
            "path": "C:/campaign/autosave.sav", "_save_fingerprint": "a" * 64,
            "player": {"military": 100},
            "contacts": [{"id": 19, "name": "Neighbor", "intel": 36.5,
                          "military": 99999, "economy": 2222, "technology": 3333,
                          "hidden": {"stock": {"alloys": 9000}}, "opinion": -10}],
        }
        old = server.CONFIG.get("spoiler_campaign", "")
        try:
            server.CONFIG["spoiler_campaign"] = ""
            normal = server.public_snapshot(snapshot)
            self.assertNotIn("military", normal["contacts"][0])
            self.assertNotIn("hidden", normal["contacts"][0])
            self.assertEqual(normal["contacts"][0]["intel"], 36.5)
            self.assertEqual(normal["player"]["military"], 100)
            context = server.compact_ai_context(normal, {}, "empires")
            self.assertNotIn("military", context["contacted_empires"][0])
            server.CONFIG["spoiler_campaign"] = server.campaign_key(snapshot)
            spoiler = server.public_snapshot(snapshot)
            self.assertEqual(spoiler["contacts"][0]["military"], 99999)
            self.assertEqual(server.compact_ai_context(spoiler, {}, "empires")
                             ["contacted_empires"][0]["military"], 99999)
            self.assertFalse(server.spoilers_active({"path": "C:/different/autosave.sav"}))
        finally:
            server.CONFIG["spoiler_campaign"] = old

    def test_ship_role_mismatch_is_review_only(self):
        result = ship_design_check("explosive", [{"slot": "SMALL_GUN_01", "component": "SMALL_LASER_1"}], True)
        self.assertIn("Review", result["suggestion"])
        self.assertIn("in-game Ship Designer", result["check"])
        self.assertTrue(result["auto_generated"])


if __name__ == "__main__":
    unittest.main()
