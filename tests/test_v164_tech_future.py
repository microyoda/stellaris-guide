"""v1.6.4 downstream Tech Tree and explanation checks."""
import tempfile
import unittest
from pathlib import Path

from stellaris_guide.tech_route import route_for_target


class FutureRouteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        folder = self.root / "common" / "technology"
        folder.mkdir(parents=True)
        (folder / "00_fixture.txt").write_text(
            'tech_root = { area = society tier = 0 }\n'
            'tech_next = { area = society tier = 1 prerequisites = { tech_root } }\n'
            'tech_later = { area = society tier = 2 prerequisites = { tech_next } }\n'
            'tech_distant = { area = society tier = 3 prerequisites = { tech_later } }\n'
            'tech_side = { area = society tier = 1 }\n'
            'tech_far = { area = society tier = 4 prerequisites = { tech_distant tech_side } '
            'potential = { has_overlord_dlc = yes } }\n'
            'tech_beyond = { area = society tier = 4 prerequisites = { tech_far } }\n',
            encoding="utf-8")
        tier = folder / "tier" / "00_tier.txt"
        tier.parent.mkdir()
        tier.write_text('1 = { previously_unlocked = 0 }\n2 = { previously_unlocked = 0 }\n'
                        '3 = { previously_unlocked = 0 }\n4 = { previously_unlocked = 0 }\n',
                        encoding="utf-8")
        localisation = self.root / "localisation" / "english"
        localisation.mkdir(parents=True)
        (localisation / "tech_l_english.yml").write_text(
            'l_english:\n tech_root:0 "Root Discovery"\n'
            ' tech_root_desc:0 "Improves the starting research path."\n'
            ' tech_next_desc:0 "Needs $UNKNOWN$ substitution."\n', encoding="utf-8")

    def save(self, *, mods=None, release="match"):
        return {"date": "2301.01.01", "campaign": {"id": "c1", "mods": mods or [],
                "required_dlcs": [], "installed": {"version_match": release}},
                "technology": {"researched_status": "complete", "researched": {},
                               "branches": {"society": {"current_id": "", "alternative_ids": []}}}}

    def test_future_path_and_explanation_are_conditional(self):
        result = route_for_target(self.save(), str(self.root), "tech_root")
        self.assertEqual(result["description"], "Improves the starting research path.")
        self.assertIn("tech_next", [item["id"] for item in result["future_opportunities"]])
        far = next(item for item in result["future_opportunities"] if item["id"] == "tech_far")
        self.assertEqual(far["distance"], 4)
        self.assertEqual([step["id"] for step in far["path"]],
                         ["tech_root", "tech_next", "tech_later", "tech_distant", "tech_far"])
        self.assertEqual(far["dlc"][0]["status"], "not_listed")
        self.assertIn("Other prerequisite: Side", far["blockers"])
        beyond = next(item for item in result["future_opportunities"] if item["id"] == "tech_beyond")
        self.assertEqual(beyond["dlc"][0]["status"], "not_listed")
        self.assertEqual(result["steps"][-1]["direct_prerequisites"], [])
        self.assertIn("Required for later research", result["benefit"])
        self.assertEqual(next(item for item in result["future_opportunities"]
                              if item["id"] == "tech_next")["description"], "")

    def test_mismatch_has_no_future_and_mods_limit_certainty(self):
        self.assertEqual(route_for_target(self.save(release="mismatch"), str(self.root),
                                          "tech_root")["future_opportunities"], [])
        result = route_for_target(self.save(mods=["Example Mod"]), str(self.root), "tech_root")
        self.assertEqual(result["status"], "limited")
        self.assertTrue(all(item["draw_conditions_unverified"]
                            for item in result["future_opportunities"]))
        self.assertTrue(any("Tier rule may differ with mods" in blocker
                            for item in result["future_opportunities"]
                            for blocker in item["blockers"]))
        self.assertFalse(any("more previous-tier" in blocker
                             for item in result["future_opportunities"]
                             for blocker in item["blockers"]))

    def test_nearest_children_survive_wide_future_list(self):
        folder = self.root / "common" / "technology"
        (folder / "01_wide.txt").write_text(
            "".join(f'tech_child_{index:02d} = {{ area = society tier = 1 '
                    f'prerequisites = {{ tech_root }} }}\n' for index in range(40)) +
            "".join(f'tech_early_name_{index:02d} = {{ area = society tier = 2 '
                    f'prerequisites = {{ tech_child_00 }} }}\n' for index in range(20)),
            encoding="utf-8")
        result = route_for_target(self.save(), str(self.root), "tech_root")
        shown = result["future_opportunities"][:18]
        self.assertEqual(len(shown), 18)
        self.assertTrue(all(item["distance"] == 1 for item in shown))

    def test_observed_research_card_has_no_inferred_blocker(self):
        save = self.save()
        save["technology"]["branches"]["society"]["alternative_ids"] = ["tech_far"]
        result = route_for_target(save, str(self.root), "tech_root")
        far = next(item for item in result["future_opportunities"] if item["id"] == "tech_far")
        self.assertEqual(far["state"], "saved_option")
        self.assertEqual(far["blockers"], [])


if __name__ == "__main__":
    unittest.main()
