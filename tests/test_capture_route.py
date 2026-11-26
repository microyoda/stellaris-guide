import importlib
import unittest
from unittest.mock import patch

from PIL import Image


capture_module = importlib.import_module("stellaris_guide.capture")


class CaptureRouteTests(unittest.TestCase):
    def test_game_window_uses_window_pixels_not_desktop_grab(self):
        game = Image.new("RGB", (32, 32), (30, 90, 150))
        with (patch.object(capture_module, "available", return_value=True),
              patch.object(capture_module, "list_windows", return_value=[{"id": 42, "stellaris": True}]),
              patch.object(capture_module, "_print_window", return_value=game) as direct,
              patch("PIL.ImageGrab.grab", side_effect=AssertionError("desktop capture was used"))):
            result = capture_module.capture(42)
        direct.assert_called_once_with(42)
        self.assertTrue(result.startswith("data:image/jpeg;base64,"))


if __name__ == "__main__":
    unittest.main()
