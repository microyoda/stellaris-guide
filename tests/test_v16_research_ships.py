"""Saved research observations and cautious Cygnus military advice."""
import unittest
import tempfile
from pathlib import Path

from stellaris_guide.saves import (component_prerequisite_evidence,
                                  military_policy_details, ship_design_check)
from stellaris_guide.strategy import research_trend


def research_save(date, project="tech_destroyers", progress=0, known=True, campaign="one"):
    return {"date": date, "campaign": {"id": campaign},
            "technology": {"branches": {"engineering": {
                "current_id": project, "progress": progress, "progress_known": known}}}}


class ResearchTrendTests(unittest.TestCase):
    def test_destroyers_progress_in_four_saves_is_observed_without_eta(self):
        history = [research_save("2277.01.01", progress=1625.5),
                   research_save("2277.04.01", progress=1719.3),
                   research_save("2277.07.01", progress=1813.0),
                   research_save("2277.10.01", progress=1906.8)]
        trend = research_trend(history[-1], history, "engineering")
        self.assertEqual(trend["progress_delta"], 93.8)
        self.assertEqual(trend["elapsed_months"], 3)
        self.assertEqual(trend["from_date"], "2277.07.01")
        self.assertIn("No completion time", trend["observation"])
        self.assertNotIn("stalled", trend["observation"])

    def test_missing_previous_changed_project_zero_and_declining_progress(self):
        first = research_save("2277.01.01", progress=100)
        current = research_save("2277.04.01", progress=100)
        self.assertEqual(research_trend(current, [first, current], "engineering")["progress_delta"], 0)
        current["technology"]["branches"]["engineering"]["progress"] = 90
        self.assertEqual(research_trend(current, [first, current], "engineering")["progress_delta"], -10)
        current["technology"]["branches"]["engineering"]["current_id"] = "tech_other"
        self.assertEqual(research_trend(current, [first, current], "engineering")["status"], "no_comparable_save")
        current["technology"]["branches"]["engineering"]["progress_known"] = False
        self.assertEqual(research_trend(current, [first, current], "engineering")["status"], "unknown")
        current["technology"]["branches"]["engineering"]["current_id"] = ""
        self.assertEqual(research_trend(current, [first, current], "engineering")["status"], "no_project")

    def test_same_project_in_another_campaign_is_not_compared(self):
        first = research_save("2277.01.01", progress=100, campaign="other")
        current = research_save("2277.04.01", progress=200)
        self.assertEqual(research_trend(current, [first, current], "engineering")["status"], "no_comparable_save")

    def test_missing_campaign_identity_does_not_compare_research(self):
        first = research_save("2277.01.01", progress=100, campaign="other")
        current = research_save("2277.04.01", progress=200)
        current["campaign"].pop("id")
        trend = research_trend(current, [first, current], "engineering")
        self.assertEqual(trend["status"], "no_comparable_save")
        self.assertIsNone(trend["progress_delta"])


class MilitaryPolicyTests(unittest.TestCase):
    def test_saved_randomized_doctrine_uses_installed_definition_and_label(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            definitions = root / "common" / "policies" / "06_policies_fleets_and_starbases.txt"
            labels = root / "localisation" / "english" / "main_3_l_english.yml"
            extra = labels.parent / "defense_platform_policies_l_english.yml"
            definitions.parent.mkdir(parents=True)
            labels.parent.mkdir(parents=True)
            definitions.write_text('fleet_doctrine = {\n option = {\n name = "phalanx_fleet_doctrine"\n }\n option = {\n name = "battleline_fleet_doctrine"\n }\n}\n')
            labels.write_text('l_english:\n policy_fleet_doctrine: "Fleet Doctrine"\n phalanx_fleet_doctrine: "Phalanx Doctrine"\n battleline_fleet_doctrine: "Battle Line Doctrine"\n')
            extra.write_text('l_english:\n')
            selected = military_policy_details({"fleet_doctrine": "battleline_fleet_doctrine"}, str(root), "match")
            self.assertEqual(selected[0]["selected_label"], "Battle Line Doctrine")
            self.assertEqual(selected[0]["status"], "verified_base_game")
            unknown = military_policy_details({"fleet_doctrine": "modded_doctrine"}, str(root), "match")
            self.assertNotEqual(unknown[0]["status"], "verified_base_game")
            mismatch = military_policy_details({"fleet_doctrine": "phalanx_fleet_doctrine"}, str(root), "mismatch")
            self.assertEqual(mismatch[0]["selected_label"], "phalanx_fleet_doctrine")
            self.assertEqual(mismatch[0]["status"], "unverified")
            custom = military_policy_details({"fleet_custom_policy": "custom_option"}, str(root), "match")
            self.assertEqual(custom[0]["selected_id"], "custom_option")
            self.assertEqual(custom[0]["status"], "missing_definition")

    def test_starbase_and_platform_preferences_use_selected_options(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            definitions = root / "common" / "policies" / "06_policies_fleets_and_starbases.txt"
            labels = root / "localisation" / "english" / "main_3_l_english.yml"
            extra = labels.parent / "defense_platform_policies_l_english.yml"
            definitions.parent.mkdir(parents=True)
            labels.parent.mkdir(parents=True)
            definitions.write_text(
                'starbase_weapon_preference = {\n option = {\n name = "starbase_laser"\n }\n}\n'
                'platform_defense_preference = {\n option = {\n name = "platform_armor"\n }\n}\n')
            labels.write_text(
                'l_english:\n policy_starbase_weapon_preference: "Starbase Weapons"\n'
                ' starbase_laser: "Laser Focus"\n')
            extra.write_text(
                'l_english:\n policy_platform_defense_preference: "Platform Defenses"\n'
                ' platform_armor: "Armor Focus"\n')
            selected = military_policy_details({"starbase_weapon_preference": "starbase_laser",
                                                "platform_defense_preference": "platform_armor"},
                                               str(root), "match")
            self.assertEqual([item["selected_label"] for item in selected],
                             ["Laser Focus", "Armor Focus"])
            self.assertTrue(all(item["status"] == "verified_base_game" for item in selected))

    def test_missing_ship_slots_do_not_prove_a_build(self):
        check = ship_design_check("gunship", [], True)
        self.assertIn("No weapon", check["why"])
        self.assertIn("unverified", check["confidence"])

    def test_visible_weapon_slot_does_not_endorse_loadout(self):
        check = ship_design_check("gunship", [{"slot": "GUN_01", "component": "SMALL_RED_LASER"}], False)
        self.assertIn("Review this loadout", check["suggestion"])
        self.assertNotIn("Keep this loadout", check["suggestion"])


class ComponentEvidenceTests(unittest.TestCase):
    def test_researched_and_missing_prerequisites_are_distinguished(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            definitions = root / "common" / "component_templates" / "00_weapons_energy.txt"
            definitions.parent.mkdir(parents=True)
            definitions.write_text(
                'weapon_component_template = {\n key = "SMALL_RED_LASER"\n'
                ' prerequisites = { "tech_lasers_1" }\n}\n'
                'weapon_component_template = {\n key = "SMALL_BLUE_LASER"\n'
                ' prerequisites = { "tech_lasers_2" }\n}\n')
            designs = [{"slots": [{"component": "SMALL_RED_LASER"},
                                  {"component": "SMALL_BLUE_LASER"},
                                  {"component": "MODDED_WEAPON"}]}]
            technology = {"researched_status": "complete", "researched": {"tech_lasers_1": 1}}
            component_prerequisite_evidence(designs, technology, str(root), "match")
            evidence = designs[0]["component_evidence"]
            self.assertEqual([item["status"] for item in evidence],
                             ["listed_tech_researched", "tech_not_recorded", "unverified"])
            self.assertEqual(evidence[1]["unresearched_tech"], ["tech_lasers_2"])
            self.assertEqual(designs[0]["component_access_status"], "unverified")

    def test_version_mismatch_and_partial_research_never_verify_components(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            definitions = root / "common" / "component_templates" / "00_weapons_energy.txt"
            definitions.parent.mkdir(parents=True)
            definitions.write_text('weapon_component_template = {\n key = "SMALL_RED_LASER"\n'
                                   ' prerequisites = { "tech_lasers_1" }\n}\n')
            technology = {"researched_status": "complete", "researched": {"tech_lasers_1": 1}}
            for version, status in (("mismatch", "complete"), ("match", "partial")):
                designs = [{"slots": [{"component": "SMALL_RED_LASER"}]}]
                component_prerequisite_evidence(designs, {**technology, "researched_status": status},
                                                str(root), version)
                self.assertEqual(designs[0]["component_evidence"][0]["status"], "unverified")


if __name__ == "__main__":
    unittest.main()
