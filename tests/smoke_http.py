"""Manual loopback smoke test; run from the repository root."""
import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from stellaris_guide import server


server.CONFIG.update(provider="off")
server.PLAN_PATH = Path(".test-temp/plan-smoke.json")
server.scan_once()
assert server.STATE["status"] == "ready", server.STATE["error"]
http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
thread = threading.Thread(target=http.serve_forever, daemon=True)
thread.start()
base = f"http://127.0.0.1:{http.server_port}"
try:
    for route, expected in (
        ("/", "text/html"), ("/app.js", "javascript"),
        ("/api/state", "application/json"), ("/api/flag", "image/png"),
        ("/api/tech-icon?id=tech_destroyers", "image/png"),
        ("/api/planet-icon?id=pc_continental", "image/png"),
    ):
        with urllib.request.urlopen(base + route, timeout=20) as response:
            data = response.read()
            assert response.status == 200
            assert expected in response.headers["Content-Type"]
            assert data
            print(route, response.status, len(data))
    request = urllib.request.Request(
        base + "/api/ask", data=json.dumps({"question": "/ask economy?"}).encode(),
        headers={"Content-Type": "application/json", "X-Guide-Token": server.TOKEN},
        method="POST")
    with urllib.request.urlopen(request, timeout=20) as response:
        answer = json.load(response)
        assert answer["source"] == "Built-in guide"
        assert "energy" in answer["answer"]
        print("/api/ask", response.status, answer["source"])
finally:
    http.shutdown()
    http.server_close()
