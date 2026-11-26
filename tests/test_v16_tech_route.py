"""Focused route tests use synthetic game definitions and save context only."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from stellaris_guide import route_window, server
from stellaris_guide.tech_route import research_overview, route_for_target


def snapshot(campaign="campaign-1", date="2277.10.01", researched=None,
             current="", options=None, dlcs=None, mods=None, version="match"):
    return {"date": date, "modified": 123,
            "campaign": {"id": campaign, "required_dlcs": dlcs, "mods": mods or [],
                         "installed": {"version_match": version}},
            "technology": {"researched_status": "complete", "researched": researched or {},
                           "branches": {"engineering": {"current_id": current,
                                                        "alternative_ids": options or []}}}}


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        folder = self.root / "common" / "technology"
        folder.mkdir(parents=True)
        (folder / "00_fixture.txt").write_text(
            'tech_base = {\n area = engineering\n tier = 2\n weight = 100\n}\n'
            'tech_a = {\n area = engineering\n tier = 2\n weight = 100\n}\n'
            'tech_b = {\n area = engineering\n tier = 2\n weight = 100\n}\n'
            'tech_orbital_ring_tier_1 = {\n area = engineering\n tier = 3\n weight = 100\n'
            ' prerequisites = { "tech_base" }\n potential = {\n has_overlord_dlc = yes\n'
            ' OR = {\n has_technology = "tech_a"\n has_technology = "tech_b"\n }\n'
            ' is_nomadic = no\n }\n}\n'
            'tech_event = {\n area = physics\n tier = 1\n weight = 0\n}\n')
        tier = folder / "tier" / "00_tier.txt"
        tier.parent.mkdir()
        tier.write_text('3 = {\n previously_unlocked = 1\n}\n')

    def route(self, save, target="tech_orbital_ring_tier_1"):
        return route_for_target(save, str(self.root), target)

    def test_one_of_is_choice_not_two_mandatory_steps(self):
        result = self.route(snapshot(researched={"tech_base": 1, "tech_b": 1},
                                     dlcs=["Overlord"]))
        self.assertEqual(result["status"], "verified_base_game")
        self.assertEqual([step["id"] for step in result["steps"]],
                         ["tech_base", "tech_orbital_ring_tier_1"])
        self.assertEqual([item["id"] for item in result["one_of"][0]["options"]],
                         ["tech_a", "tech_b"])
        self.assertEqual(result["one_of"][0]["options"][1]["state"], "researched")
        self.assertEqual(result["tier_gate"]["status"], "met")
        self.assertNotIn("completion", result["next_check"].lower())

    def test_dlc_mod_and_release_uncertainty_limit_route(self):
        missing = self.route(snapshot(dlcs=[]))
        self.assertEqual(missing["status"], "limited")
        self.assertEqual(missing["dlc"][0]["status"], "not_listed")
        self.assertIn("DLC", missing["next_check"])
        modded = self.route(snapshot(dlcs=["Overlord"], mods=["Example Mod"]))
        self.assertEqual(modded["status"], "limited")
        self.assertEqual(modded["tier_gate"]["status"], "unknown")
        mismatch = self.route(snapshot(version="mismatch", dlcs=["Overlord"]))
        self.assertEqual(mismatch["status"], "unknown")
        self.assertEqual(mismatch["steps"], [])

    def test_event_current_researched_and_selected_save_date(self):
        event = self.route(snapshot(dlcs=[]), "tech_event")
        self.assertTrue(event["granted_candidate"])
        self.assertIn("event or grant", event["next_check"])
        current = self.route(snapshot(current="tech_orbital_ring_tier_1", dlcs=["Overlord"]))
        self.assertEqual(current["steps"][-1]["state"], "researching")
        self.assertIn("current project", current["next_check"])
        done = self.route(snapshot(researched={"tech_orbital_ring_tier_1": 1},
                                        dlcs=["Overlord"]))
        self.assertEqual(done["steps"][-1]["state"], "researched")
        self.assertIn("Already researched", done["next_check"])
        newer = self.route(snapshot(campaign="campaign-2", date="2278.01.01", dlcs=["Overlord"]))
        self.assertEqual(newer["campaign_id"], "campaign-2")
        self.assertEqual(newer["date"], "2278.01.01")

    def test_missing_identity_or_incomplete_research_is_unknown(self):
        no_identity = self.route(snapshot(campaign=""))
        self.assertEqual(no_identity["status"], "unknown")
        incomplete = snapshot(dlcs=["Overlord"])
        incomplete["technology"]["researched_status"] = "partial"
        self.assertEqual(self.route(incomplete)["status"], "unknown")
        self.assertEqual(self.route(snapshot(), "not_a_tech")["status"], "unknown")


    def test_route_map_preserves_branch_edges_and_confirmed_card(self):
        save = snapshot(researched={"tech_base": 1}, options=["tech_orbital_ring_tier_1"],
                        dlcs=["Overlord"])
        result = self.route(save)
        self.assertEqual(result["edges"], [{"from": "tech_base", "to": "tech_orbital_ring_tier_1"}])
        self.assertEqual(result["steps"][-1]["display_state"], "On your cards")
        self.assertEqual(result["steps"][-1]["parents"], ["tech_base"])
        self.assertEqual(result["next_actions"],
                         ["Your goal is on a research card now. Check it in game and choose it when ready."])
        self.assertEqual(next(gate for gate in result["route_gates"] if gate["tier"] == 3)["state"], "open")

    def test_localized_name_and_unverified_draw_are_not_claimed_available(self):
        folder = self.root / "localisation" / "english"
        folder.mkdir(parents=True)
        (folder / "technology_l_english.yml").write_text(
            'l_english:\n tech_orbital_ring_tier_1:0 "Orbital Rings"\n', encoding="utf-8-sig")
        result = self.route(snapshot(researched={"tech_base": 1}, dlcs=["Overlord"]))
        self.assertEqual(result["name"], "Orbital Rings")
        self.assertEqual(result["steps"][-1]["display_state"], "Choose one prerequisite")
        self.assertEqual(result["steps"][-1]["eligibility"], "blocked")
        self.assertTrue(any(edge.get("type") == "one_of" for edge in result["map_edges"]))
        self.assertIn("Research one of", " ".join(result["next_actions"]))
        satisfied = self.route(snapshot(researched={"tech_base": 1, "tech_a": 1}, dlcs=["Overlord"]))
        self.assertEqual(satisfied["steps"][-1]["display_state"], "Prerequisites met")
        self.assertEqual(satisfied["steps"][-1]["eligibility"], "unverified")
        self.assertNotIn("Ready to appear", str(result))

    def test_two_prerequisite_branches_merge_at_goal(self):
        folder = self.root / "common" / "technology"
        (folder / "01_branches.txt").write_text(
            'tech_left_root = { area = physics tier = 0 weight = 100 }\n'
            'tech_left_mid = { area = physics tier = 1 prerequisites = { "tech_left_root" } weight = 100 }\n'
            'tech_left_tip = { area = physics tier = 1 prerequisites = { "tech_left_mid" } weight = 100 }\n'
            'tech_right_root = { area = society tier = 0 weight = 100 }\n'
            'tech_right_mid = { area = society tier = 1 prerequisites = { "tech_right_root" } weight = 100 }\n'
            'tech_right_tip = { area = society tier = 2 prerequisites = { "tech_right_mid" } weight = 100 }\n'
            'tech_goal = { area = physics tier = 2 prerequisites = { "tech_left_tip" "tech_right_tip" } weight = 100 }\n')
        result = self.route(snapshot(), "tech_goal")
        self.assertEqual(len(result["steps"]), 7)
        self.assertEqual({(edge["from"], edge["to"]) for edge in result["edges"] if edge["to"] == "tech_goal"},
                         {("tech_left_tip", "tech_goal"), ("tech_right_tip", "tech_goal")})
        self.assertEqual(result["steps"][-1]["column"], 3)


class RouteLookaheadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        folder = self.root / "common" / "technology"
        folder.mkdir(parents=True)
        (folder / "00_soc_tech.txt").write_text(
            'tech_planetary_government = { area = society tier = 0 }\n'
            'tech_planetary_unification = { area = society tier = 1 prerequisites = { tech_planetary_government } }\n'
            'tech_colonial_centralization = { area = society tier = 2 prerequisites = { tech_planetary_unification } }\n'
            'tech_federation_code = { area = society tier = 1 prerequisites = { tech_colonial_centralization } }\n'
            'tech_xeno_diplomacy = { area = society tier = 2 prerequisites = { tech_federation_code } }\n'
            'tech_galactic_administration = { area = society tier = 3 }\n'
            'tech_xeno_relations = { area = society tier = 3 prerequisites = { tech_xeno_diplomacy tech_galactic_administration } }\n'
            'tech_future = { area = society tier = 4 prerequisites = { tech_xeno_relations } }\n'
            'tech_other_parent = { area = society tier = 0 }\n'
            'tech_other = { area = society tier = 1 prerequisites = { tech_other_parent } }\n'
            'tech_choice = { area = society tier = 3 prerequisites = { OR = { tech_xeno_diplomacy tech_other } } }\n'
            'tech_choice_child = { area = society tier = 4 prerequisites = { tech_choice } }\n'
            'tech_dlc_child = { area = society tier = 3 prerequisites = { tech_xeno_diplomacy } '
            'potential = { has_overlord_dlc = yes } }\n')
        tier = folder / "tier" / "00_tier.txt"
        tier.parent.mkdir()
        tier.write_text('1 = { previously_unlocked = 0 }\n2 = { previously_unlocked = 1 }\n'
                        '3 = { previously_unlocked = 1 }\n4 = { previously_unlocked = 1 }\n')

    def route(self, researched=None, target="tech_xeno_diplomacy", **kwargs):
        return route_for_target(snapshot(researched=researched, **kwargs), str(self.root), target)

    def test_direct_prerequisite_and_full_unresearched_path_are_distinct(self):
        result = self.route()
        self.assertEqual([step["id"] for step in result["steps"]], [
            "tech_planetary_government", "tech_planetary_unification",
            "tech_colonial_centralization", "tech_federation_code", "tech_xeno_diplomacy"])
        self.assertEqual([item["id"] for item in result["steps"][-1]["direct_prerequisites"]],
                         ["tech_federation_code"])
        self.assertEqual(result["next_unlocks"], [])

    def test_researched_intermediate_stops_remaining_route(self):
        result = self.route(researched={"tech_federation_code": 1})
        self.assertEqual([step["id"] for step in result["steps"]],
                         ["tech_federation_code", "tech_xeno_diplomacy"])
        self.assertEqual(result["edges"], [{"from": "tech_federation_code", "to": "tech_xeno_diplomacy"}])
        self.assertNotIn("tech_colonial_centralization", [step["id"] for step in result["map_nodes"]])

    def test_researched_target_shows_two_dependency_steps_not_claimed_draw(self):
        result = self.route(researched={"tech_xeno_diplomacy": 1})
        self.assertEqual([step["id"] for step in result["steps"]], ["tech_xeno_diplomacy"])
        direct = {item["id"]: item for item in result["next_unlocks"] if item["distance"] == 1}
        later = {item["id"]: item for item in result["next_unlocks"] if item["distance"] == 2}
        self.assertIn("tech_xeno_relations", direct)
        self.assertEqual(direct["tech_xeno_relations"]["missing_prerequisites"],
                         ["tech_galactic_administration"])
        self.assertIn("tech_future", later)
        self.assertEqual(result["steps"][0]["direct_prerequisites"][0]["id"], "tech_federation_code")

    def test_one_of_descendants_remain_possible_paths(self):
        result = self.route(researched={"tech_xeno_diplomacy": 1})
        by_id = {item["id"]: item for item in result["next_unlocks"]}
        self.assertEqual(by_id["tech_choice"]["relation"], "one_of")
        self.assertEqual(by_id["tech_choice_child"]["relation"], "one_of")

    def test_alternative_detail_preserves_live_prerequisite_state(self):
        for expected, kwargs in (("researching", {"current": "tech_other_parent"}),
                                 ("saved_option", {"options": ["tech_other_parent"]})):
            with self.subTest(expected=expected):
                result = self.route(target="tech_choice", **kwargs)
                alternative = next(item for item in result["map_nodes"] if item["id"] == "tech_other")
                self.assertEqual(alternative["direct_prerequisites"][0]["state"], expected)

    def test_downstream_dlc_is_reported_for_each_card(self):
        missing = self.route(researched={"tech_xeno_diplomacy": 1}, dlcs=[])
        child = next(item for item in missing["next_unlocks"] if item["id"] == "tech_dlc_child")
        self.assertEqual(child["dlc"][0]["status"], "not_listed")
        present = self.route(researched={"tech_xeno_diplomacy": 1}, dlcs=["Overlord"])
        child = next(item for item in present["next_unlocks"] if item["id"] == "tech_dlc_child")
        self.assertEqual(child["dlc"][0]["status"], "present")

    def test_mismatch_has_no_lookahead_and_mods_remain_unverified(self):
        self.assertEqual(self.route(version="mismatch")["next_unlocks"], [])
        modded = self.route(researched={"tech_xeno_diplomacy": 1}, mods=["Example mod"])
        self.assertEqual(modded["status"], "limited")
        self.assertTrue(all(item["draw_conditions_unverified"] for item in modded["next_unlocks"]))


class RouteIntegrityTests(unittest.TestCase):
    def test_comments_and_or_branches_do_not_become_mandatory(self):
        from stellaris_guide.tech_route import _parse_prerequisites
        direct, groups, unknown = _parse_prerequisites(
            'tech_base # tech_commented\n OR = { tech_a tech_b }'
        )
        self.assertEqual(direct, ["tech_base"])
        self.assertEqual(groups, [["tech_a", "tech_b"]])
        self.assertFalse(unknown)
        self.assertTrue(_parse_prerequisites('AND = { tech_a }')[2])

    def test_missing_definition_and_depth_limit_stay_limited(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            technology = root / "common" / "technology"
            technology.mkdir(parents=True)
            tier = technology / "tier" / "00_tier.txt"
            tier.parent.mkdir()
            tier.write_text('1 = { previously_unlocked = 0 }\n')
            (technology / "rules.txt").write_text(
                'tech_missing_target = { prerequisites = { tech_not_installed } }\n'
                + ''.join(f'tech_chain_{i} = {{ prerequisites = {{ tech_chain_{i + 1} }} }}\n'
                          for i in range(10))
                + 'tech_chain_10 = { }\n'
            )
            missing = route_for_target(snapshot(), str(root), "tech_missing_target")
            self.assertEqual(missing["status"], "limited")
            self.assertIn("missing", missing["reason"])
            deep = route_for_target(snapshot(), str(root), "tech_chain_0")
            self.assertEqual(deep["status"], "limited")
            self.assertIn("eight levels", deep["reason"])
            self.assertNotIn("appear met", deep["next_check"])

    def test_edge_title_rejects_suffix(self):
        token = "route-token"
        exact = route_window.TITLE_PREFIX + token
        self.assertTrue(route_window._route_title_matches(exact, token))
        self.assertFalse(route_window._route_title_matches(exact + " another page", token))

    @unittest.skipUnless(__import__("sys").platform == "win32", "Windows window enumeration")
    def test_edge_window_enumeration_requires_exact_title_and_edge_process(self):
        import ctypes
        token = "route-token"
        title = [route_window.TITLE_PREFIX + token]
        user32 = SimpleNamespace()
        user32.GetWindowTextLengthW = lambda hwnd: len(title[0])
        user32.GetWindowTextW = lambda hwnd, buffer, count: setattr(buffer, "value", title[0])
        user32.GetWindowThreadProcessId = lambda hwnd, pid: setattr(pid._obj, "value", 42)
        user32.EnumWindows = lambda callback, data: callback(101, data)
        kernel32 = SimpleNamespace()
        kernel32.OpenProcess = mock.Mock(return_value=1)
        def image_name(process, flags, name, size):
            name.value = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
            return True
        kernel32.QueryFullProcessImageNameW = mock.Mock(side_effect=image_name)
        kernel32.GetProcessTimes = mock.Mock(return_value=True)
        kernel32.CloseHandle = mock.Mock()
        with mock.patch.object(ctypes, "windll", SimpleNamespace(user32=user32, kernel32=kernel32)):
            self.assertIsNone(route_window._matching_edge_window(token))
            route_window.ACTIVE_ROUTES[token] = {"created": 100, "profile": Path("route-profile")}
            try:
                with mock.patch.object(route_window, "_new_process", return_value=False):
                    self.assertIsNone(route_window._matching_edge_window(token))
                with (mock.patch.object(route_window, "_new_process", return_value=True),
                      mock.patch.object(route_window, "_edge_uses_profile", return_value=False)):
                    self.assertIsNone(route_window._matching_edge_window(token))
                with (mock.patch.object(route_window, "_new_process", return_value=True),
                      mock.patch.object(route_window, "_edge_uses_profile", return_value=True)):
                    self.assertEqual(route_window._matching_edge_window(token), 101)
            finally:
                route_window.ACTIVE_ROUTES.pop(token, None)
            title[0] += " unrelated"
            self.assertIsNone(route_window._matching_edge_window(token))

    def test_step_cap_does_not_claim_verified_route(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            technology = root / "common" / "technology"
            technology.mkdir(parents=True)
            tier = technology / "tier" / "00_tier.txt"
            tier.parent.mkdir()
            tier.write_text('1 = { previously_unlocked = 0 }\n')
            prerequisites = ' '.join(f'tech_dependency_{i}' for i in range(50))
            (technology / "rules.txt").write_text(
                f'tech_wide = {{ prerequisites = {{ {prerequisites} }} }}\n'
                + ''.join(f'tech_dependency_{i} = {{ }}\n' for i in range(50))
            )
            route = route_for_target(snapshot(), str(root), "tech_wide")
            self.assertEqual(route["status"], "limited")
            self.assertIn("48 steps", route["reason"])


class RouteEndpointTests(unittest.TestCase):
    def request(self, path, origin=None):
        replies = []
        headers = {"Host": "127.0.0.1:1234"}
        if origin:
            headers["Origin"] = origin
        request = SimpleNamespace(path=path, headers=headers, host_is_local=lambda: True,
                                  send_json=lambda body, status=200: replies.append((status, body)),
                                  send_error=lambda status: replies.append((status, {})))
        server.Handler.do_GET(request)
        return replies[-1]

    def test_selected_campaign_and_origin_gate(self):
        selected = snapshot(campaign="campaign-2")
        selected["empire"] = "Same Empire Name"
        with mock.patch.dict(server.STATE, {"snapshot": selected}), \
             mock.patch.dict(server.CONFIG, {"game_folder": "synthetic"}), \
             mock.patch.object(server, "route_for_target", return_value={"status": "limited"}) as route:
            stale = self.request("/api/tech-route?campaign=campaign-1&target=tech_base")
            self.assertEqual(stale[0], 409)
            self.assertFalse(route.called)
            rejected = self.request("/api/tech-route?campaign=campaign-2&target=tech_base",
                                    origin="https://foreign.example")
            self.assertEqual(rejected[0], 403)
            valid = self.request("/api/tech-route?campaign=campaign-2&target=tech_base")
            self.assertEqual(valid[0], 200)
            route.assert_called_once_with(selected, "synthetic", "tech_base")

    def test_target_index_uses_selected_campaign(self):
        selected = snapshot(campaign="campaign-2", date="2278.01.01")
        with mock.patch.dict(server.STATE, {"snapshot": selected}), \
             mock.patch.object(server, "route_targets", return_value=[{"id": "tech_base"}]):
            response = self.request("/api/tech-route/targets?campaign=campaign-2")
            self.assertEqual(response[0], 200)
            self.assertEqual(response[1]["date"], "2278.01.01")
            self.assertEqual(response[1]["targets"][0]["id"], "tech_base")

    def post(self, path, body, origin=None, token=None):
        replies = []
        headers = {"Host": "127.0.0.1:1234", "X-Guide-Token": token or ""}
        if origin:
            headers["Origin"] = origin
        request = SimpleNamespace(path=path, headers=headers, host_is_local=lambda: True,
                                  read_body=lambda: body, server=SimpleNamespace(server_port=1234),
                                  send_json=lambda payload, status=200: replies.append((status, payload)))
        server.Handler.do_POST(request)
        return replies[-1]

    def test_edge_open_requires_current_campaign_and_token(self):
        selected = snapshot(campaign="campaign-2")
        with mock.patch.dict(server.STATE, {"snapshot": selected}), \
             mock.patch.dict(server.CONFIG, {"game_folder": "synthetic"}), \
             mock.patch.object(server, "route_for_target", return_value={"status": "limited"}), \
             mock.patch.object(server, "launch_edge_route", return_value="instance-token") as launch:
            body = {"campaign_id": "campaign-2", "target": "tech_base"}
            self.assertEqual(self.post("/api/tech-route/open", body)[0], 403)
            self.assertEqual(self.post("/api/tech-route/open", {**body, "campaign_id": "campaign-1"},
                                       token=server.TOKEN)[0], 400)
            valid = self.post("/api/tech-route/open", body, token=server.TOKEN)
            self.assertEqual(valid[0], 200)
            launch.assert_called_once_with("http://127.0.0.1:1234", "campaign-2", "tech_base")

    def test_edge_close_requires_same_origin_and_tracked_instance(self):
        with mock.patch.object(server, "close_edge_route", return_value=True) as close:
            self.assertEqual(self.post("/api/tech-route/close", {"instance": "secret"})[0], 403)
            self.assertEqual(self.post("/api/tech-route/close", {"instance": "secret"},
                                       origin="https://foreign.example")[0], 403)
            self.assertEqual(self.post("/api/tech-route/close", {"instance": "secret"},
                                       origin="http://127.0.0.1:1234")[0], 200)
            close.assert_called_once_with("secret")

    def test_edge_close_rejects_non_string_instance(self):
        with mock.patch.object(server, "close_edge_route") as close:
            for value in ([], {}, 123, None):
                self.assertEqual(self.post("/api/tech-route/close", {"instance": value},
                                           origin="http://127.0.0.1:1234")[0], 400)
            close.assert_not_called()


class EdgeWindowTests(unittest.TestCase):
    @unittest.skipUnless(__import__("sys").platform == "win32", "Windows profile verification")
    def test_profile_check_requires_exact_process_argument(self):
        profile = Path("C:/Users/Player/AppData/Local/StellarisGuide/route-windows/owned")
        good = SimpleNamespace(returncode=0, stdout=f'"C:\\Edge\\msedge.exe" "--user-data-dir={profile}"')
        with mock.patch.object(route_window.subprocess, "run", return_value=good) as run:
            self.assertTrue(route_window._edge_uses_profile(42, profile))
            self.assertIn("ProcessId=42", run.call_args.args[0][-1])
            self.assertEqual(run.call_args.kwargs["timeout"], 4)
        bad = SimpleNamespace(returncode=0, stdout=good.stdout + "-copied")
        with mock.patch.object(route_window.subprocess, "run", return_value=bad):
            self.assertFalse(route_window._edge_uses_profile(42, profile))
        with mock.patch.object(route_window.subprocess, "run", side_effect=OSError):
            self.assertFalse(route_window._edge_uses_profile(42, profile))
        self.assertFalse(route_window._edge_uses_profile(0, profile))

    def test_old_open_route_remains_tracked(self):
        route_window.ACTIVE_ROUTES.clear()
        self.addCleanup(route_window.ACTIVE_ROUTES.clear)
        with (tempfile.TemporaryDirectory(dir=Path.cwd()) as folder,
              mock.patch.object(route_window, "ROUTE_PROFILES", Path(folder)),
              mock.patch.object(route_window, "edge_executable", return_value=Path("C:/Edge/msedge.exe")),
              mock.patch.object(route_window.subprocess, "Popen"),
              mock.patch.object(route_window, "_route_title_present", return_value=True),
              mock.patch.object(route_window, "_profile_has_live_edge", return_value=True),
              mock.patch.object(route_window.time, "time", return_value=7200)):
            route_window.ACTIVE_ROUTES["old"] = {"created": 1, "profile": Path(folder) / "old"}
            route_window.launch_edge_route("http://127.0.0.1:1234", "campaign-1", "tech_base")
            self.assertIn("old", route_window.ACTIVE_ROUTES)

    def test_old_closed_route_releases_capacity(self):
        route_window.ACTIVE_ROUTES.clear()
        self.addCleanup(route_window.ACTIVE_ROUTES.clear)
        with (tempfile.TemporaryDirectory(dir=Path.cwd()) as folder,
              mock.patch.object(route_window, "ROUTE_PROFILES", Path(folder)),
              mock.patch.object(route_window, "edge_executable", return_value=Path("C:/Edge/msedge.exe")),
              mock.patch.object(route_window.subprocess, "Popen"),
              mock.patch.object(route_window, "_route_title_present", return_value=False),
              mock.patch.object(route_window, "_profile_has_live_edge", return_value=False),
              mock.patch.object(route_window, "_cleanup_profile"),
              mock.patch.object(route_window.time, "time", return_value=7200)):
            for i in range(4):
                route_window.ACTIVE_ROUTES[str(i)] = {"created": 1, "profile": Path(folder) / str(i)}
            instance = route_window.launch_edge_route("http://127.0.0.1:1234", "campaign-1", "tech_base")
            self.assertEqual(list(route_window.ACTIVE_ROUTES), [instance])

    def test_missing_title_releases_capacity_even_with_background_edge(self):
        route_window.ACTIVE_ROUTES.clear()
        self.addCleanup(route_window.ACTIVE_ROUTES.clear)
        with (tempfile.TemporaryDirectory(dir=Path.cwd()) as folder,
              mock.patch.object(route_window, "ROUTE_PROFILES", Path(folder)),
              mock.patch.object(route_window, "edge_executable", return_value=Path("C:/Edge/msedge.exe")),
              mock.patch.object(route_window.subprocess, "Popen"),
              mock.patch.object(route_window, "_route_title_present", return_value=False),
              mock.patch.object(route_window.time, "time", return_value=7200)):
            route_window.ACTIVE_ROUTES["old"] = {"created": 1, "profile": Path(folder) / "old"}
            with mock.patch.object(route_window, "_cleanup_profile"):
                route_window.launch_edge_route("http://127.0.0.1:1234", "campaign-1", "tech_base")
            self.assertNotIn("old", route_window.ACTIVE_ROUTES)

    def test_cleanup_waits_until_edge_releases_profile(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            profile = Path(folder) / "owned"
            profile.mkdir()
            with (mock.patch.object(route_window, "ROUTE_PROFILES", Path(folder)),
                  mock.patch.object(route_window.time, "sleep"),
                  mock.patch.object(route_window, "_profile_has_live_edge", side_effect=[True, None, False]),
                  mock.patch.object(route_window.shutil, "rmtree") as remove):
                route_window._cleanup_profile(profile)
                remove.assert_called_once_with(profile)
    def test_launch_is_argument_array_and_close_only_tracked_window(self):
        route_window.ACTIVE_ROUTES.clear()
        self.addCleanup(route_window.ACTIVE_ROUTES.clear)
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder, \
             mock.patch.object(route_window, "ROUTE_PROFILES", Path(folder)), \
             mock.patch.object(route_window, "edge_executable", return_value=Path("C:/Edge/msedge.exe")), \
             mock.patch.object(route_window.subprocess, "Popen") as launch:
            instance = route_window.launch_edge_route("http://127.0.0.1:1234", "campaign-1", "tech_base")
            args = launch.call_args.args[0]
            self.assertEqual(args[0].replace("\\", "/"), "C:/Edge/msedge.exe")
            self.assertIn("--app=http://127.0.0.1:1234/tech-route.html?", args[2])
            self.assertIn(instance, args[2])
            self.assertEqual(args[3], f"--user-data-dir={Path(folder) / instance}")
            self.assertTrue((Path(folder) / instance).is_dir())
        with mock.patch.object(route_window, "_matching_edge_window", return_value=None):
            self.assertFalse(route_window.close_edge_route(instance))
            self.assertIn(instance, route_window.ACTIVE_ROUTES)
            self.assertFalse(route_window.close_edge_route("untracked"))


class ResearchOverviewTests(unittest.TestCase):
    def test_tier_gate_and_saved_card_labels(self):
        save = snapshot(researched={"tech_one": 1}, current="tech_now",
                        options=["tech_next"])
        rules = {
            "tech_one": {"name": "First Step", "area": "engineering", "tier": 1},
            "tech_now": {"name": "Current Project", "area": "engineering", "tier": 1},
            "tech_next": {"name": "Next Choice", "area": "engineering", "tier": 1},
        }
        with mock.patch("stellaris_guide.tech_route.installed_rules", return_value=(rules, {2: 2})):
            result = research_overview(save, "synthetic")
        self.assertEqual(result["labels"]["tech_now"], "Current Project")
        self.assertEqual(result["gates"]["engineering"]["status"], "closed")
        self.assertEqual(result["gates"]["engineering"]["count"], 1)
        self.assertEqual(result["gates"]["engineering"]["on_cards"][0]["id"], "tech_next")

    def test_mismatch_or_mod_does_not_claim_verified_gate(self):
        save = snapshot(researched={"tech_one": 1}, options=["tech_next"])
        rules = {"tech_one": {"name": "First Step", "area": "engineering", "tier": 1}}
        with mock.patch("stellaris_guide.tech_route.installed_rules", return_value=(rules, {2: 0})):
            self.assertEqual(research_overview(save, "synthetic")["gates"]["engineering"]["status"], "open")
            save["campaign"]["mods"] = ["changed_technology"]
            self.assertEqual(research_overview(save, "synthetic")["gates"]["engineering"]["status"], "unverified")
            save["campaign"]["installed"]["version_match"] = "mismatch"
            self.assertEqual(research_overview(save, "synthetic")["status"], "unverified")


if __name__ == "__main__":
    unittest.main()
