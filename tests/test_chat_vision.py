"""Check screenshot routing and local question-history privacy without live AI calls."""

import base64
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image

from stellaris_guide import server


SNAPSHOT = {
    "date": "2277.07.01",
    "version": "Cygnus v4.5.2",
    "empire": "United Nations of Earth",
    "player": {"net": {"energy": 10}, "military": 2320},
    "contacts": [],
}


class ChatVisionTests(unittest.TestCase):
    def test_screenshot_reaches_each_provider_in_its_expected_format(self):
        picture = Image.new("RGB", (120, 120), "white")
        for x in range(30, 90):
            for y in range(30, 90):
                picture.putpixel((x, y), (20, 30, 90))
        encoded = io.BytesIO()
        picture.save(encoded, format="JPEG")
        screenshot = server.validate_screenshot(
            "data:image/jpeg;base64," + base64.b64encode(encoded.getvalue()).decode("ascii")
        )
        previous_config = dict(server.CONFIG)
        previous_key = server.OPENROUTER_KEY
        try:
            server.OPENROUTER_KEY = "test-key"
            for provider in ("ollama", "lmstudio", "openrouter"):
                with self.subTest(provider=provider):
                    server.CONFIG.update(provider=provider, model="vision-test")
                    reply = ({"message": {"content": "Visible in image: a fleet is shown."}} if provider == "ollama"
                             else {"choices": [{"message": {"content": "Visible in image: a fleet is shown."}}]})
                    with patch.object(server, "_provider_can_read_images", return_value=True), \
                         patch("urllib.request.urlopen", return_value=io.BytesIO(json.dumps(reply).encode())) as mocked:
                        answer, _ = server.ai_answer("What should I do?", SNAPSHOT, {}, screenshot=screenshot)
                    self.assertEqual(answer, "Visible in image: a fleet is shown.")
                    payload = json.loads(mocked.call_args.args[0].data)
                    user = payload["messages"][-1]
                    if provider == "ollama":
                        self.assertEqual(user["images"], [screenshot[1]])
                        self.assertIsInstance(user["content"], str)
                    else:
                        self.assertEqual(user["content"][1]["image_url"]["url"], screenshot[0])
                        self.assertIn("2277.07.01", user["content"][0]["text"])
        finally:
            server.CONFIG.update(previous_config)
            server.OPENROUTER_KEY = previous_key

    def test_empty_provider_content_has_a_clear_error(self):
        previous_config = dict(server.CONFIG)
        try:
            server.CONFIG.update(provider="lmstudio", model="vision-test")
            reply = {"choices": [{"message": {"content": None}}]}
            with patch("urllib.request.urlopen", return_value=io.BytesIO(json.dumps(reply).encode())):
                with self.assertRaisesRegex(ValueError, "returned no text"):
                    server.ai_answer("What next?", SNAPSHOT, {})
        finally:
            server.CONFIG.update(previous_config)

    def test_question_history_persists_only_text_and_frequency(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(server, "QUESTION_HISTORY_PATH", Path(directory) / "history.json"):
                server.remember_question("What ships should I build?", has_image=True)
                history = server.remember_question("What ships should I build?", has_image=True)
                self.assertEqual(history["frequent"][0]["count"], 2)
                self.assertTrue(history["recent"][0]["has_image"])
                saved = server.QUESTION_HISTORY_PATH.read_text(encoding="utf-8")
                self.assertNotIn("data:image", saved)
                self.assertEqual(len(server.read_question_history()), 1)

    def test_invalid_screenshot_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "valid JPEG"):
            server.validate_screenshot("data:image/jpeg;base64," + base64.b64encode(b"not a JPEG").decode("ascii"))


if __name__ == "__main__":
    unittest.main()
