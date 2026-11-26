"""Test a running packaged app on an explicitly supplied loopback port."""
import json
import sys
import urllib.error
import urllib.request


port = int(sys.argv[1])
expected_version = sys.argv[2] if len(sys.argv) > 2 else None
base = f"http://127.0.0.1:{port}"
for route in ("/", "/app.js", "/fleet.js", "/api/state"):
    with urllib.request.urlopen(base + route, timeout=20) as response:
        data = response.read()
        assert response.status == 200 and data
        if route == "/app.js":
            assert b"fetchState" in data
        if route == "/fleet.js":
            assert b"function renderFleet" in data
        if route == "/api/state":
            state = json.loads(data)
            assert state["status"] == "ready", state.get("error")
            if expected_version:
                assert state["app_version"] == expected_version
            assert state["advice"]["goals"]
            assert state["snapshot"]["campaign"]["id"]
            token = state["token"]
            print("packaged save", state["snapshot"]["date"], len(state["advice"]["goals"]), "goals")
        print(route, response.status, len(data))
if expected_version in ("1.6.1", "1.6.2"):
    campaign_id = state["snapshot"]["campaign"]["id"]
    def limit_request(campaign, limit):
        return urllib.request.Request(base + "/api/fleet-limit",
                                      data=json.dumps({"campaign_id": campaign, "limit": limit}).encode(),
                                      headers={"Content-Type": "application/json", "X-Guide-Token": token},
                                      method="POST")
    try:
        urllib.request.urlopen(limit_request("0" * 16, 140), timeout=20)
        raise AssertionError("Stale campaign was accepted")
    except urllib.error.HTTPError as error:
        assert error.code == 400
    with urllib.request.urlopen(limit_request(campaign_id, 140), timeout=20) as response:
        assert json.load(response)["fleet_limit"] == 140
    with urllib.request.urlopen(base + "/api/state", timeout=20) as response:
        assert json.load(response)["config"]["fleet_limit"] == 140
    with urllib.request.urlopen(limit_request(campaign_id, None), timeout=20) as response:
        assert json.load(response)["fleet_limit"] is None
    print("/api/fleet-limit stale, save, reload and clear passed")
request = urllib.request.Request(base + "/api/quit", data=b"{}",
                                 headers={"Content-Type": "application/json",
                                          "X-Guide-Token": token}, method="POST")
with urllib.request.urlopen(request, timeout=20) as response:
    assert json.load(response)["ok"]
    print("/api/quit", response.status)
