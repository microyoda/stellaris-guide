"""Saved Fleet page observations; no installed game or user save required."""
import unittest

from stellaris_guide.saves import parse_player_fleets


def indexed(name, entries):
    return f"{name}=\n{{\n" + "".join(f"\t{key}=\n\t{raw}\n" for key, raw in entries.items()) + "}\n"


class FleetReadTests(unittest.TestCase):
    def test_own_fleets_and_class_usage_match_saved_total(self):
        game = "".join((
            indexed("ship_design", {10: "{ ship_size=frigate }", 11: "{ ship_size=corvette }"}),
            indexed("ships", {
                100: "{ ship_design_implementation={ design=10 } }",
                101: "{ ship_design_implementation={ design=10 } }",
                102: "{ ship_design_implementation={ design=11 } }",
                103: "{ ship_design_implementation={ design=11 } }",
            }),
            indexed("fleet_template", {
                20: "{ fleet_template_design={ { ship_design_implementation={ design=10 } count=2 } } fleet_size=16 }",
                21: "{ fleet_template_design={ { ship_design_implementation={ design=10 } } { ship_design_implementation={ design=11 } count=2 } } fleet_size=18 }",
            }),
            indexed("galactic_object", {7: '{ name="Sol" }'}),
            indexed("fleet", {
                1: '{ name="First Fleet" ship_class=shipclass_military fleet_template=20 ships={ 100 101 } combat={ coordinate={ origin=7 } } military_power=400 }',
                2: '{ name="Second Fleet" ship_class=shipclass_military fleet_template=21 ships={ 100 102 103 } military_power=300 }',
                3: '{ name="Rival Fleet" ship_class=shipclass_military ships={ 101 } military_power=900 }',
            }),
        ))
        player = '{ fleets_manager={ owned_fleets={ { fleet=1 } { fleet=2 } } } used_naval_capacity=34 }'
        designs = [{"id": 10, "size_key": "frigate"}, {"id": 11, "size_key": "corvette"}]
        result = parse_player_fleets(game, player, designs)
        self.assertEqual(result["usage_status"], "matches_saved_total")
        self.assertEqual([fleet["size"] for fleet in result["fleets"]], [16, 18])
        self.assertEqual(result["fleets"][0]["location"], "Sol")
        self.assertEqual(result["class_usage"], {"frigate": 24, "corvette": 10})
        self.assertEqual([design["naval_usage"] for design in designs], [8, 5])

    def test_missing_plan_or_unowned_fleet_does_not_invent_size(self):
        game = indexed("fleet", {
            4: '{ name="Unknown Plan" ship_class=shipclass_military ships={ 99 } military_power=40 }',
            5: '{ name="Foreign" ship_class=shipclass_military military_power=400 }',
        })
        player = '{ fleets_manager={ owned_fleets={ { fleet=4 } } } used_naval_capacity=12 }'
        result = parse_player_fleets(game, player, [{"id": 8, "size_key": "frigate"}])
        self.assertEqual(len(result["fleets"]), 1)
        self.assertEqual(result["fleets"][0]["ship_count"], 1)
        self.assertFalse(result["fleets"][0]["classes_complete"])
        self.assertIsNone(result["fleets"][0]["size"])
        self.assertEqual(result["usage_status"], "inferred_from_plans")
        self.assertEqual(parse_player_fleets(game, '{}', [] )["usage_status"], "unavailable")

    def test_unknown_design_keeps_ship_count_but_marks_mix_partial(self):
        game = "".join((
            indexed("ship_design", {10: "{ ship_size=frigate }"}),
            indexed("ships", {100: "{ ship_design_implementation={ design=10 } }",
                              101: "{ ship_design_implementation={ design=999 } }"}),
            indexed("fleet", {1: '{ name="First" ship_class=shipclass_military ships={ 100 101 } }'}),
        ))
        player = '{ fleets_manager={ owned_fleets={ { fleet=1 } } } }'
        result = parse_player_fleets(game, player, [{"id": 10, "size_key": "frigate"}])
        fleet = result["fleets"][0]
        self.assertEqual(fleet["ship_count"], 2)
        self.assertEqual(fleet["classes"], {"frigate": 1})
        self.assertFalse(fleet["classes_complete"])
        self.assertIsNone(fleet["size"])


if __name__ == "__main__":
    unittest.main()
