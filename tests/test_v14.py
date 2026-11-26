import tempfile
import unittest
from pathlib import Path

from PIL import Image

from stellaris_guide.assets import render_flag
from stellaris_guide.saves import parse_flag, parse_policies
from stellaris_guide.server import compact_ai_context
from stellaris_guide.strategy import make_plan
from stellaris_guide.technology import focus_path


def snapshot(food=-10, military=1000):
    return {
        "path": "campaign/autosave_2250.sav", "date": "2250.01.01", "empire": "Test",
        "player": {"net": {"food": food, "energy": 10, "alloys": 30},
                   "stock": {"food": 100, "alloys": 300}, "military": military},
        "planets": [{"id": 1, "name": "Farm Prime", "designation": "Farming",
                     "produces": {"food": 25}, "free_amenities": 3, "stability": 70,
                     "recommendation": {"level": "stable", "action": "Wait", "reason": "Stable"}}],
        "contacts": [{"id": 4, "name": "Neighbor", "opinion": -100, "military": 99999}],
        "ship_builds": {"recommendation": {"design_id": 1, "title": "Reinforce Corvette"}},
        "policies": {"fleet_doctrine": "phalanx_fleet_doctrine"},
    }


class V14Tests(unittest.TestCase):
    def test_goal_steps_progress_and_stable_target(self):
        first = snapshot()
        stored = {}
        initial = make_plan(first, [first], stored)
        food = next(g for g in initial["goals"] if g["key"] == "deficit:food")
        self.assertIn("Farm Prime", food["steps"][0]["action"])
        self.assertEqual(food["progress"]["percent"], 0)
        later = snapshot(food=-2, military=1100)
        later["date"] = "2251.01.01"
        updated = make_plan(later, [first, later], stored)
        food = next(g for g in updated["goals"] if g["key"] == "deficit:food")
        self.assertEqual(food["target"], 5)
        self.assertEqual(food["due"], 2253)
        self.assertGreater(food["progress"]["percent"], 0)
        self.assertTrue(any(g["key"] == "diplomacy:4" for g in updated["goals"]))

    def test_policy_and_flag_are_read_from_save(self):
        raw = '''flag={ icon={ category="human" file="flag_human_9.dds" }
                   background={ category="backgrounds" file="00_solid.dds" }
                   colors={ "blue" "black" "null" } }
                 policies={ { policy="fleet_doctrine" selected="phalanx_fleet_doctrine" }
                            { policy="platform_weapon_preference" selected="platform_weapon_2" } }'''
        self.assertEqual(parse_policies(raw)["platform_weapon_preference"], "platform_weapon_2")
        self.assertEqual(parse_flag(raw)["icon_file"], "flag_human_9.dds")

    def test_ai_context_does_not_send_hidden_foreign_power(self):
        context = compact_ai_context(snapshot(), {"goals": []}, "main")
        self.assertEqual(context["contacted_empires"][0]["name"], "Neighbor")
        self.assertNotIn("military", context["contacted_empires"][0])

    def test_installed_definition_path(self):
        with tempfile.TemporaryDirectory() as folder:
            technology = Path(folder) / "common" / "technology"
            technology.mkdir(parents=True)
            (technology / "test.txt").write_text(
                'tech_destroyers = { prerequisites = { "tech_corvettes" } }\n'
                'tech_cruisers = { prerequisites = { "tech_destroyers" } }\n'
                'tech_battleships = { prerequisites = { "tech_cruisers" } }\n')
            path = focus_path(folder, "engineering", {"tech_corvettes"},
                              "tech_destroyers", [], {})
            self.assertEqual(path["target_id"], "tech_cruisers")
            self.assertEqual([s["id"] for s in path["steps"]], ["tech_destroyers", "tech_cruisers"])

    def test_local_flag_composition(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "flags"
            (root / "human").mkdir(parents=True)
            (root / "backgrounds").mkdir()
            (root / "colors.txt").write_text(
                "colors={\nblue={ flag=rgb { 10 20 200 } }\n}\n")
            Image.new("RGB", (8, 8), (255, 0, 0)).save(root / "backgrounds" / "solid.dds")
            Image.new("RGBA", (8, 8), (255, 255, 255, 0)).save(root / "human" / "icon.dds")
            data = render_flag(folder, "human", "icon.dds", "solid.dds", ("blue",))
            self.assertIsNotNone(data)
            self.assertTrue(data.startswith(b"\x89PNG"))
            self.assertIsNone(render_flag(folder, "../human", "icon.dds", "solid.dds", ("blue",)))


if __name__ == "__main__":
    unittest.main()
