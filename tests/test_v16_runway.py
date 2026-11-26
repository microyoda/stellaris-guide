"""Resource cover and job-capacity counterexamples for v1.6 Phase 2."""
import unittest

from stellaris_guide.advice import economy_answer
from stellaris_guide.saves import planet_job_advice, planet_recommendation
from stellaris_guide.strategy import make_plan, resource_runway, resource_steps


def snapshot(stock=11731.4, net=-57.2, date="2277.10.01"):
    return {
        "date": date, "path": "campaign/autosave.sav", "empire": "United Nations of Earth",
        "campaign": {"id": "one"},
        "player": {"net": {"food": net, "alloys": 30, "energy": 20},
                   "stock": {"food": stock, "alloys": 100, "energy": 100},
                   "military": 1000},
        "planets": [{"id": 1, "name": "Alpha Centauri Prime", "designation": "Farming",
                     "designation_key": "col_farming", "produces": {"food": 80},
                     "upkeep": {"energy": 4}, "free_amenities": 3,
                     "free_housing": 5, "stability": 70,
                     "jobs": [{"type": "farmer", "filled": 2.6, "capacity": 12.0,
                               "limit": 12.0, "disabled": False}],
                     "recommendation": {"level": "stable", "action": "Wait", "reason": "Stable"}}],
        "contacts": [], "ship_builds": {"recommendation": {}}, "policies": {},
    }


class RunwayTests(unittest.TestCase):
    def test_long_runway_and_open_farmer_jobs_do_not_trigger_market_or_farm(self):
        current = snapshot()
        plan = make_plan(current, [current], {})
        cover = current["resource_runway"]["food"]
        self.assertEqual(cover["urgency"], "planned")
        self.assertAlmostEqual(cover["months"], 205.1, places=1)
        self.assertEqual(cover["date"], "2277.10.01")
        food = next(g for g in plan["goals"] if g["key"] == "deficit:food")
        self.assertIn("205.1 months", food["detail"])
        actions = " ".join(item["action"] for item in food["steps"])
        self.assertIn("open farmer jobs", actions)
        self.assertNotIn("Agriculture District", actions)
        self.assertNotIn("Market", actions)
        answer = economy_answer(current)
        self.assertIn("205.1 months cover", answer)
        self.assertNotIn("urgent Guide warning", answer)

    def test_short_runway_and_zero_stock_are_urgent(self):
        current = snapshot(stock=20, net=-10)
        self.assertEqual(resource_runway(current, "food")["urgency"], "urgent")
        self.assertIn("Market", resource_steps(current, "food")[0]["action"])
        current["player"]["stock"]["food"] = 30
        self.assertEqual(resource_runway(current, "food")["urgency"], "watch")
        current["player"]["stock"]["food"] = 60
        self.assertEqual(resource_runway(current, "food")["urgency"], "planned")
        current["player"]["stock"]["food"] = 0
        cover = resource_runway(current, "food")
        self.assertEqual((cover["status"], cover["months"]), ("depleting", 0))

    def test_unknown_and_non_depleting_states(self):
        current = snapshot(stock=100, net=0)
        self.assertEqual(resource_runway(current, "food")["status"], "no_depletion")
        current["player"]["stock_known"] = {"food": False}
        self.assertEqual(resource_runway(current, "food")["status"], "unknown")
        del current["player"]["stock_known"]
        current["player"]["stock"]["food"] = float("nan")
        self.assertEqual(resource_runway(current, "food")["status"], "unknown")
        current["player"]["stock"]["food"] = 100
        current["player"]["net_known"] = {"food": False}
        self.assertEqual(resource_runway(current, "food")["status"], "unknown")
        del current["player"]["net_known"]
        current["player"]["net"]["food"] = "invalid"
        self.assertEqual(resource_runway(current, "food")["status"], "unknown")
        current["player"]["net"]["food"] = -10
        current["player"]["stock"]["food"] = -1
        self.assertEqual(resource_runway(current, "food")["status"], "unknown")

    def test_rising_stock_does_not_erase_current_deficit(self):
        previous = snapshot(stock=10881.3, date="2277.07.01")
        current = snapshot()
        plan = make_plan(current, [previous, current], {})
        food = next(g for g in plan["goals"] if g["key"] == "deficit:food")
        self.assertEqual(current["resource_runway"]["food"]["stock_change"], 850.1)
        self.assertIn("cause unknown", food["detail"])
        previous["campaign"]["id"] = "another-campaign"
        self.assertIsNone(resource_runway(current, "food", [previous, current])["stock_change"])
        future = snapshot(stock=1, date="2278.01.01")
        previous["campaign"]["id"] = "one"
        self.assertEqual(resource_runway(current, "food", [previous, future, current])["stock_change"], 850.1)

    def test_job_limit_and_stability_before_construction(self):
        current = snapshot()
        planet = current["planets"][0]
        planet["jobs"][0]["limit"] = 2.6
        actions = " ".join(item["action"] for item in resource_steps(current, "food"))
        self.assertIn("job limit", actions)
        self.assertNotIn("Agriculture District", actions)
        planet["jobs"][0]["limit"] = None
        actions = " ".join(item["action"] for item in resource_steps(current, "food"))
        self.assertIn("capacity is incomplete", " ".join(item["reason"] for item in resource_steps(current, "food")))
        planet["jobs"][0]["limit"] = 12.0
        planet["jobs"][0]["filled"] = 12.0
        actions = " ".join(item["action"] for item in resource_steps(current, "food"))
        self.assertIn("Agriculture District", actions)
        planet["jobs"][0]["filled"] = 2.6
        planet["free_amenities"] = -6
        planet["stability"] = 35
        advice = planet_job_advice(planet, {"food": -10})
        self.assertIn("2.6 of 12", advice[0]["observation"])
        self.assertIn("upkeep", advice[0]["tradeoff"])
        self.assertEqual(planet_recommendation(planet, {"food": -10})["level"], "urgent")


if __name__ == "__main__":
    unittest.main()
