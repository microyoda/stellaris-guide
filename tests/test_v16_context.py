"""Synthetic Cygnus saves for the v1.6 campaign-context boundary."""

import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from stellaris_guide import saves, server
from stellaris_guide.saves import parse_save
from stellaris_guide.advice import economy_answer
from stellaris_guide.strategy import resource_runway


GAME = '''player={
	{
		country=0
	}
}
country={
	0={
		name={ key="NAME_Human_Union" }
		type="default"
		tech_status={
			technology="tech_starbase_1"
			level=1
			technology="tech_repeatable"
			level=3
			physics_queue={
				technology="tech_current"
				progress=25
				date="2200.01.01"
			}
			society_queue={ }
			engineering_queue={ }
			alternatives={ physics={ "tech_future" } }
		}
		military_power=100
		budget={ current_month={ income={ base={ energy=20 } } expenses={ upkeep={ energy=5 } } } }
		modules={ standard_economy_module={ resources={ energy=100 } } }
	}
}'''


def write_save(root: Path, campaign: str = "campaign-one", meta: str | None = None,
               game: str = GAME) -> Path:
    folder = root / "save games" / campaign
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "autosave_2200.01.01.sav"
    if meta is None:
        meta = ('version="Cygnus v4.5.2"\nname="Human Union"\n'
                'date="2200.01.01"\nrequired_dlcs={ "Apocalypse" }\n'
                'mods={ "Example Mod (1.0)" }\n')
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("meta", meta)
        archive.writestr("gamestate", game)
    return path


class CampaignContextTests(unittest.TestCase):
    def test_missing_budget_rate_is_unknown_not_zero_income(self):
        with tempfile.TemporaryDirectory() as folder:
            game = GAME.replace("energy=20", "").replace("energy=5", "")
            snapshot = parse_save(write_save(Path(folder), game=game), include_details=False)
        self.assertFalse(snapshot["player"]["net_known"]["energy"])
        self.assertEqual(resource_runway(snapshot, "energy")["status"], "unknown")
        self.assertIn("energy rate unknown", economy_answer(snapshot))
        self.assertIn("unavailable", economy_answer(snapshot))

    def test_save_context_keeps_exact_research_and_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            snapshot = parse_save(write_save(Path(folder)), include_details=False)
        context = snapshot["campaign"]
        self.assertEqual(context["save_version"], "Cygnus v4.5.2")
        self.assertEqual(context["required_dlcs"], ["Apocalypse"])
        self.assertEqual(context["mods"], ["Example Mod (1.0)"])
        self.assertEqual(context["player_country_id"], 0)
        self.assertEqual(snapshot["technology"]["researched"],
                         {"tech_starbase_1": 1, "tech_repeatable": 3})
        self.assertEqual(snapshot["technology"]["researched_count"], 2)
        self.assertEqual(snapshot["technology"]["researched_status"], "complete")
        self.assertEqual(snapshot["technology"]["branches"]["physics"]["current_id"],
                         "tech_current")
        self.assertEqual(snapshot["technology"]["branches"]["physics"]["alternative_ids"],
                         ["tech_future"])
        self.assertTrue(snapshot["technology"]["branches"]["physics"]["progress_known"])

    def test_same_empire_name_in_two_campaign_folders_has_distinct_ids(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            first = parse_save(write_save(root, "first"), include_details=False)
            second = parse_save(write_save(root, "second"), include_details=False)
        self.assertEqual(first["empire"], second["empire"])
        self.assertNotEqual(first["campaign"]["id"], second["campaign"]["id"])

    def test_installed_version_and_mod_labels_are_qualified(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            save = write_save(root)
            game_dir = root / "installed-game"
            game_dir.mkdir()
            (game_dir / "launcher-settings.json").write_text(
                json.dumps({"version": "Cygnus v4.5.2 (9776)"}), encoding="utf-8")
            (root / "dlc_load.json").write_text(
                json.dumps({"enabled_mods": ["mod/example.mod"]}), encoding="utf-8")
            (root / "mod").mkdir()
            (root / "mod" / "example.mod").write_text('name="Example Mod (1.0)"',
                                                       encoding="utf-8")
            context = parse_save(save, include_details=False,
                                 game_dir=str(game_dir))["campaign"]["installed"]
            self.assertEqual(context["version_match"], "match")
            self.assertEqual(context["checksum"], "9776")
            self.assertEqual(context["mod_match"], "names_only")
            (game_dir / "launcher-settings.json").write_text(
                json.dumps({"version": "Cygnus v4.5.1 (1234)"}), encoding="utf-8")
            (root / "mod" / "example.mod").write_text('name="Different Mod"',
                                                       encoding="utf-8")
            mismatch = parse_save(save, include_details=False,
                                  game_dir=str(game_dir))["campaign"]["installed"]
            self.assertEqual(mismatch["version_match"], "mismatch")
            self.assertEqual(mismatch["mod_match"], "mismatch")

    def test_missing_metadata_and_bad_research_level_are_unknown(self):
        with tempfile.TemporaryDirectory() as folder:
            bad_game = GAME.replace('level=3', 'level=broken')
            save = write_save(Path(folder), meta='version="unknown"\nname="Human Union"\n',
                              game=bad_game)
            snapshot = parse_save(save, include_details=False)
        self.assertIsNone(snapshot["campaign"]["required_dlcs"])
        self.assertIsNone(snapshot["campaign"]["mods"])
        self.assertEqual(snapshot["campaign"]["installed"]["version_match"], "unknown")
        self.assertEqual(snapshot["technology"]["researched"], {"tech_starbase_1": 1})
        self.assertEqual(snapshot["technology"]["researched_status"], "partial")

    def test_compact_and_intervening_research_fields_are_recognized(self):
        with tempfile.TemporaryDirectory() as folder:
            game = GAME.replace('technology="tech_repeatable"\n\t\t\tlevel=3',
                                'technology="tech_repeatable" flag=yes level=3')
            result = parse_save(write_save(Path(folder), game=game), include_details=False)
        self.assertEqual(result["technology"]["researched"]["tech_repeatable"], 3)
        self.assertEqual(result["technology"]["researched_status"], "complete")

    def test_malformed_progress_and_missing_player_reference(self):
        with tempfile.TemporaryDirectory() as folder:
            game = GAME.replace('progress=25', 'progress=broken')
            save = write_save(Path(folder), game=game)
            result = parse_save(save, include_details=False)
            self.assertFalse(result["technology"]["branches"]["physics"]["progress_known"])
            game = GAME.replace('\t\tcountry=0', '\t\tcountry=broken', 1)
            save = write_save(Path(folder), game=game)
            with self.assertRaisesRegex(ValueError, "player country reference"):
                parse_save(save, include_details=False)

    def test_incomplete_research_never_builds_a_confident_focus_path(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            partial = write_save(root, game=GAME.replace('level=3', 'level=broken'))
            with mock.patch("stellaris_guide.technology.focus_path",
                            side_effect=AssertionError("incomplete research reached focus_path")):
                result = parse_save(partial, game_dir=str(root / "game"))
            self.assertEqual(result["technology"]["researched_status"], "partial")
            self.assertNotIn("focus_path", result["technology"]["branches"]["physics"])
            unknown = write_save(root, game=GAME.replace("tech_status=", "missing_status="))
            with mock.patch("stellaris_guide.technology.focus_path",
                            side_effect=AssertionError("unknown research reached focus_path")):
                result = parse_save(unknown, game_dir=str(root / "game"))
            self.assertEqual(result["technology"]["researched_status"], "unknown")

    def test_oversized_meta_version_and_name_are_not_exposed(self):
        with tempfile.TemporaryDirectory() as folder:
            meta = f'version="{"v" * 161}"\nname="{"N" * 161}"\n'
            result = parse_save(write_save(Path(folder), meta=meta), include_details=False)
        self.assertEqual(result["version"], "Unknown")
        self.assertEqual(result["empire"], "Human Union")

    def test_missing_enabled_mods_does_not_claim_mismatch(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            save = write_save(root)
            (root / "dlc_load.json").write_text('{}', encoding="utf-8")
            installed = parse_save(save, include_details=False)["campaign"]["installed"]
        self.assertEqual(installed["mod_match"], "unknown")
        self.assertIsNone(installed["playset_mods"])

    def test_oversized_archive_members_and_labels_are_bounded(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            save = write_save(root)
            with mock.patch.object(saves, "MAX_META_BYTES", 50):
                with self.assertRaisesRegex(ValueError, "meta is too large"):
                    parse_save(save, include_details=False)
            with mock.patch.object(saves, "MAX_GAMESTATE_BYTES", 100):
                with self.assertRaisesRegex(ValueError, "gamestate is too large"):
                    parse_save(save, include_details=False)
            large_meta = ('version="Cygnus v4.5.2"\nname="Human Union"\n'
                          f'mods={{ "{"X" * 161}" }}\n')
            result = parse_save(write_save(root, meta=large_meta), include_details=False)
            self.assertIsNone(result["campaign"]["mods"])

    def test_history_response_omits_new_campaign_fields(self):
        with tempfile.TemporaryDirectory() as folder:
            snapshot = parse_save(write_save(Path(folder)), include_details=False)
        history = server.public_history_snapshot(snapshot)
        self.assertNotIn("campaign", history)
        self.assertNotIn("researched", history["technology"])
        self.assertIn("campaign", server.public_snapshot(snapshot))

    def test_unreadable_latest_save_is_not_replaced_by_older_one(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            old = write_save(root, campaign="old")
            newest = root / "save games" / "new" / "autosave_2200.04.01.sav"
            newest.parent.mkdir()
            with zipfile.ZipFile(newest, "w") as archive:
                archive.writestr("meta", 'version="Cygnus v4.5.2"')
            os.utime(old, (1000, 1000))
            os.utime(newest, (2000, 2000))
            with mock.patch.dict(server.CONFIG, {"save_folder": str(root / "save games"),
                                               "game_folder": ""}):
                with mock.patch.dict(server.STATE, {"status": "loading", "snapshot": None,
                                                    "history": [], "advice": None,
                                                    "error": None, "updated_at": None}, clear=True):
                    server.scan_once()
                    self.assertEqual(server.STATE["status"], "error")
                    self.assertIsNone(server.STATE["snapshot"])
                    self.assertEqual(server.STATE["history"], [])
                    self.assertIn(newest.name, server.STATE["error"])

    def test_playset_descriptor_cannot_escape_user_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            save = write_save(root)
            (root / "dlc_load.json").write_text(
                json.dumps({"enabled_mods": ["../outside.mod"]}), encoding="utf-8")
            result = parse_save(save, include_details=False)["campaign"]["installed"]
        self.assertIsNone(result["playset_mods"])
        self.assertEqual(result["mod_match"], "unknown")

    def test_playset_symlink_outside_user_folder_is_unknown(self):
        with tempfile.TemporaryDirectory() as folder, tempfile.TemporaryDirectory() as elsewhere:
            root = Path(folder)
            save = write_save(root)
            (root / "mod").mkdir()
            outside = Path(elsewhere) / "external.mod"
            outside.write_text('name="Example Mod (1.0)"', encoding="utf-8")
            try:
                (root / "mod" / "linked.mod").symlink_to(outside)
            except OSError:
                self.skipTest("This Windows setup does not permit symlink creation")
            (root / "dlc_load.json").write_text(
                json.dumps({"enabled_mods": ["mod/linked.mod"]}), encoding="utf-8")
            result = parse_save(save, include_details=False)["campaign"]["installed"]
        self.assertIsNone(result["playset_mods"])
        self.assertEqual(result["mod_match"], "unknown")


if __name__ == "__main__":
    unittest.main()
