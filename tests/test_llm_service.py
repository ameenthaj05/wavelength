import unittest
from unittest.mock import patch, MagicMock
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.llm_service import LLMService

class TestLLMService(unittest.TestCase):
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fake-anthropic-key"})
    def test_provider_auto_detect_anthropic(self):
        service = LLMService()
        self.assertEqual(service.provider, "anthropic")
        self.assertEqual(service.api_key, "fake-anthropic-key")
        self.assertEqual(service.model, "claude-3-5-sonnet-20241022")

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-gemini-key"})
    def test_provider_auto_detect_gemini(self):
        service = LLMService()
        self.assertEqual(service.provider, "gemini")
        self.assertEqual(service.api_key, "fake-gemini-key")
        self.assertEqual(service.model, "gemini-2.5-flash")

    @patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "fake-anthropic-key",
        "GEMINI_API_KEY": "fake-gemini-key",
        "LLM_PROVIDER": "gemini"
    })
    def test_provider_override_env(self):
        service = LLMService()
        self.assertEqual(service.provider, "gemini")

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-gemini-key"}, clear=True)
    @patch("httpx.Client")
    def test_call_gemini_formatting(self, mock_httpx_client):
        # Setup mock HTTP client to return a mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": '{"reply": "Hello there", "done": false, "meta": {"day": 7, "is_new_question": true}}'}]
                    }
                }
            ]
        }
        
        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client_instance

        service = LLMService()
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "How can I help you?"}
        ]
        
        reply = service.generate_reply("You are an interviewer", history)
        
        # Verify the response is correctly returned
        self.assertIn("Hello there", reply)
        
        # Verify post payload was constructed with correct Gemini roles ("user" and "model")
        call_args = mock_client_instance.post.call_args
        self.assertIsNotNone(call_args)
        
        posted_json = call_args[1]["json"]
        self.assertEqual(posted_json["contents"][0]["role"], "user")
        self.assertEqual(posted_json["contents"][1]["role"], "model")
        self.assertEqual(posted_json["systemInstruction"]["parts"][0]["text"], "You are an interviewer")

if __name__ == "__main__":
    unittest.main()
