import tempfile
import unittest
import zipfile
from pathlib import Path

from stellaris_guide.advice import answer_question, make_advice
from stellaris_guide.saves import parse_save, player_empire_name, recent_saves


GAME = '''player={ { name="Player" country=0 } }
country={
\t0={
\t\tname={ key="NAME_Human_Union" }
\t\tbudget={ current_month={ income={ base={ energy=30 alloys=12 } } expenses={ upkeep={ energy=10 alloys=5 } } } }
\t\tmilitary_power=1000
\t\teconomy_power=600
\t\ttech_power=500
\t\tused_naval_capacity=20
\t\tempire_size=60
\t\towned_planets={ 1 2 }
\t\ttype="default"
\t\tmodules={ standard_economy_module={ resources={ energy=1000 alloys=300 } } }
\t\trelations_manager={ relation={ owner=0 country=1 contact=yes relation_current=-80 hostile=yes } relation={ owner=0 country=2 contact=no } }
\t}
\t1={
\t\tname={ key="NAME_Rival_Empire" }
\t\tmilitary_power=2000
\t\teconomy_power=500
\t\ttech_power=400
\t\ttype="default"
\t}
\t2={
\t\tname={ key="NAME_Unknown_Empire" }
\t\tmilitary_power=9000
\t\teconomy_power=9000
\t\ttech_power=9000
\t\ttype="default"
\t}
}
'''


class SaveTests(unittest.TestCase):
    def test_preset_empire_uses_game_name_without_campaign_suffix(self):
        player = 'name={ key="EMPIRE_DESIGN_humans1" }'
        self.assertEqual(player_empire_name('United Nations of Earth 3', player), 'United Nations of Earth')

    def test_read_save_and_hide_unknown_empire(self):
        with tempfile.TemporaryDirectory() as folder:
            campaign = Path(folder) / 'campaign'
            campaign.mkdir()
            path = campaign / 'autosave_2230.01.01.sav'
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('meta', 'version="Cygnus v4.5.2"\nname="Human Union"\ndate="2230.01.01"')
                archive.writestr('gamestate', GAME)
            saves = recent_saves(Path(folder))
            self.assertEqual(saves, [path])
            result = parse_save(path)
            self.assertEqual(len(result["_save_fingerprint"]), 64)
            self.assertEqual(result['player']['net']['energy'], 20)
            self.assertEqual(result['player']['net']['alloys'], 7)
            self.assertEqual(result['player']['colonies'], 2)
            self.assertEqual(len(result['contacts']), 1)
            self.assertEqual(result['contacts'][0]['military'], 2000)
            advice = make_advice(result, [result])
            self.assertTrue(advice['goals'])
            self.assertIn('energy +20', answer_question('/ask economy?', result, advice))

    def test_bad_save_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'broken.sav'
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('meta', 'date="2200.01.01"')
            with self.assertRaises(ValueError):
                parse_save(path)


if __name__ == '__main__':
    unittest.main()
