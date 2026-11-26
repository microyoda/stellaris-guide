"""Serve source dashboard on loopback without browser or tray for visual QA."""
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from stellaris_guide import server

server.CONFIG.update(provider="off")
server.CONFIG_PATH = Path(".test-temp/config-preview.json")
server.PLAN_PATH = Path(".test-temp/plan-preview.json")
server.scan_once()
http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
Path(".test-temp/preview.port").write_text(str(http.server_port))
try:
    http.serve_forever()
finally:
    http.server_close()
