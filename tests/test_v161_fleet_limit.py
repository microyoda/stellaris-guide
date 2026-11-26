"""Campaign-scoped manual fleet limit storage."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from stellaris_guide import server


class FleetLimitTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(dir=Path.cwd())
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "fleet-limits.json"
        patcher = patch.object(server, "FLEET_LIMIT_PATH", self.path)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.campaign = {"campaign": {"id": "a" * 16}}
        self.other = {"campaign": {"id": "b" * 16}}

    def test_persists_per_campaign_and_can_clear(self):
        self.assertIsNone(server.fleet_limit_for(self.campaign))
        self.assertEqual(server.update_fleet_limit(self.campaign, "a" * 16, 140), 140)
        self.assertEqual(server.fleet_limit_for(self.campaign), 140)
        self.assertIsNone(server.fleet_limit_for(self.other))
        server.update_fleet_limit(self.other, "b" * 16, 200)
        server.update_fleet_limit(self.campaign, "a" * 16, None)
        self.assertIsNone(server.fleet_limit_for(self.campaign))
        self.assertEqual(server.fleet_limit_for(self.other), 200)

    def test_rejects_stale_campaign_and_invalid_value(self):
        for campaign_id, limit in (("b" * 16, 140), ("a" * 16, True),
                                   ("a" * 16, 0), ("a" * 16, 100001),
                                   ("a" * 16, "140")):
            with self.subTest(campaign_id=campaign_id, limit=limit):
                with self.assertRaises(ValueError):
                    server.update_fleet_limit(self.campaign, campaign_id, limit)
        self.assertFalse(self.path.exists())

    def test_failed_replace_keeps_previous_limits(self):
        server.update_fleet_limit(self.campaign, "a" * 16, 140)
        previous = self.path.read_bytes()
        with patch.object(server.os, "replace", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                server.update_fleet_limit(self.campaign, "a" * 16, 150)
        self.assertEqual(self.path.read_bytes(), previous)
        self.assertEqual(server.fleet_limit_for(self.campaign), 140)
        self.assertEqual(list(self.path.parent.glob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
