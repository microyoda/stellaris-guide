import tempfile
import unittest
import zipfile
from pathlib import Path

from stellaris_guide.saves import parse_save


GAME = '''player={ country=0 }
country={
\t0={
\t\tname={ key="NAME_Test_Empire" }
\t\ttype="default"
\t\tmilitary_power=900
\t\teconomy_power=600
\t\ttech_power=500
\t\tused_naval_capacity=12
\t\tempire_size=44
\t\towned_planets={ 1 }
\t\tbudget={ income={ energy=40 alloys=20 } expenses={ energy=10 alloys=5 } }
\t\tship_design_collection={ ship_design={ 100 } }
\t\ttech_status={
\t\t\ttechnology="tech_old"
\t\t\tphysics_queue={ { technology="tech_power_plant_4" progress=250 date="2250.01.01" } }
\t\t\tsociety_queue={ { technology="tech_cloning" progress=100 date="2250.01.01" } }
\t\t\tengineering_queue={ { technology="tech_mining_2" progress=80 date="2250.01.01" } }
\t\t\talternatives={ physics={ "tech_power_plant_4" "tech_lasers_2" } society={ "tech_cloning" "tech_growth_2" } engineering={ "tech_mining_2" "tech_armor_2" } }
\t\t}
\t}
}
planets={
\tplanet={
\t\t1={ name={ key="ASTEROID_NAME_FORMAT" } planet_class="pc_asteroid" planet_size=5 }
\t\t99={
\t\t\tname={ key="NEW_COLONY_NAME_1" variables={ { key="NAME" value={ key="NAME_Alpha_Centauri" } } } }
\t\t\tplanet_class="pc_continental"
\t\t\tplanet_size=18
\t\t\tcolony=1
\t\t\tcoordinate={ origin=12 }
\t\t}
\t\t98={ name={ key="NAME_Alpha_Centauri_A" } planet_class="pc_g_star" coordinate={ origin=12 } }
\t}
}
colony={
\t1={
\t\tfinal_designation="col_generator"
\t\tstability=42
\t\tcrime=3
\t\tnum_sapient_pops=2500
\t\tfree_housing=350
\t\tfree_amenities=-620
\t\tdistricts={ 1 2 3 }
\t\tbuildings_cache={ 10 11 }
\t}
}
ship_design={
\t100={ name={ key="HUMAN1_SHIP_Vanguard" } ship_size="corvette" ship_role="gunship" component={ template="SMALL_RED_LASER" } }
}
'''


class CygnusFeatureTests(unittest.TestCase):
    def test_planet_research_and_ship_details(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "autosave_2250.01.01.sav"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("meta", 'version="Cygnus v4.5.2"\ndate="2250.01.01"\nname="Test Empire"')
                archive.writestr("gamestate", GAME)
            result = parse_save(path)

        planet = result["planets"][0]
        self.assertEqual(result["empire"], "Test Empire")
        self.assertEqual(planet["name"], "Alpha Centauri Prime")
        self.assertEqual(planet["planet_id"], 99)
        self.assertEqual(planet["size"], 18)
        self.assertEqual(planet["system"], "Alpha Centauri")
        self.assertEqual(planet["pops"], 25.0)
        self.assertEqual(planet["free_amenities"], -6.2)
        self.assertEqual(planet["recommendation"]["title"], "Add amenities")
        self.assertEqual(result["technology"]["branches"]["physics"]["current"], "Power Plant 4")
        self.assertNotIn("Power Plant 4", result["technology"]["branches"]["physics"]["alternatives"])
        self.assertEqual(result["ship_builds"]["designs"][0]["name"], "Vanguard")
        self.assertEqual(result["ship_builds"]["designs"][0]["role"], "Gunship")
        self.assertEqual(result["ship_builds"]["designs"][0]["component_access_status"], "unverified")
        self.assertIn("does not establish build eligibility", result["ship_builds"]["recommendation"]["reason"])


if __name__ == "__main__":
    unittest.main()
