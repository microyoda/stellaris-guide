import io
import json
import unittest
from unittest.mock import patch

from stellaris_guide import server


SNAPSHOT = {
    "date": "2259.07.01", "version": "Cygnus v4.5.2", "empire": "Test Union",
    "player": {"net": {"energy": 10}, "military": 1000}, "contacts": [],
}
ADVICE = {"goals": [{"title": "Build fleet", "detail": "Reach 2K"}]}


class ProviderTests(unittest.TestCase):
    def test_optional_provider_formats(self):
        old_config = dict(server.CONFIG)
        old_key = server.OPENROUTER_KEY
        try:
            server.OPENROUTER_KEY = "test-key"
            for provider in ("ollama", "lmstudio", "openrouter"):
                with self.subTest(provider=provider):
                    server.CONFIG.update(provider=provider, model="test-model")
                    reply = {"message": {"content": "Use diplomacy."}} if provider == "ollama" else {"choices": [{"message": {"content": "Use diplomacy."}}]}
                    with patch("urllib.request.urlopen", return_value=io.BytesIO(json.dumps(reply).encode())) as mocked:
                        answer, source = server.ai_answer("What next?", SNAPSHOT, ADVICE)
                    self.assertEqual(answer, "Use diplomacy.")
                    self.assertEqual(source, provider.title())
                    request = mocked.call_args.args[0]
                    payload = json.loads(request.data)
                    self.assertEqual(payload["model"], "test-model")
                    self.assertIn("Cygnus v4.5.2", payload["messages"][1]["content"])
        finally:
            server.CONFIG.update(old_config)
            server.OPENROUTER_KEY = old_key


if __name__ == "__main__":
    unittest.main()
