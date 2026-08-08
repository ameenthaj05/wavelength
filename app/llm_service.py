import os
import json
from typing import List, Dict, Optional
import httpx
import anthropic

class LLMService:
    def __init__(self, provider: Optional[str] = None, api_key: Optional[str] = None):
        # Auto-detect provider if not explicitly passed
        self.anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        self.gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

        if provider:
            self.provider = provider.lower()
        elif os.environ.get("LLM_PROVIDER"):
            self.provider = os.environ.get("LLM_PROVIDER").lower()
        elif self.gemini_key:
            self.provider = "gemini"
        elif self.anthropic_key:
            self.provider = "anthropic"
        else:
            self.provider = "anthropic"  # Default fallback, will raise error on call if key missing

        # Select model based on provider
        if self.provider == "gemini":
            self.model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
            self.api_key = api_key or self.gemini_key
        else:
            self.model = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
            self.api_key = api_key or self.anthropic_key

        self.anthropic_client = None
        if self.provider == "anthropic" and self.api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=self.api_key)

    def generate_reply(self, system_prompt: str, history: List[Dict[str, str]]) -> str:
        """
        Sends system_prompt and conversation history to the LLM and returns the raw text response.
        """
        if not self.api_key:
            raise ValueError(
                f"Missing API key for LLM provider '{self.provider}'. "
                f"Please set {'GEMINI_API_KEY' if self.provider == 'gemini' else 'ANTHROPIC_API_KEY'}."
            )

        if self.provider == "gemini":
            return self._call_gemini(system_prompt, history)
        else:
            return self._call_anthropic(system_prompt, history)

    def _call_anthropic(self, system_prompt: str, history: List[Dict[str, str]]) -> str:
        if not self.anthropic_client:
            self.anthropic_client = anthropic.Anthropic(api_key=self.api_key)
        
        # Ensure we don't send empty history
        messages = list(history)
        if not messages:
            messages.append({"role": "user", "content": "Please begin the interview."})

        response = self.anthropic_client.messages.create(
            model=self.model,
            max_tokens=1000,
            system=system_prompt,
            messages=messages
        )
        return "".join(block.text for block in response.content if block.type == "text")

    def _call_gemini(self, system_prompt: str, history: List[Dict[str, str]]) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        # Map conversation history to Gemini roles ('user' and 'model')
        contents = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })
            
        if not contents:
            contents.append({
                "role": "user",
                "parts": [{"text": "Please begin the interview."}]
            })

        payload = {
            "contents": contents,
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }
        
        headers = {"Content-Type": "application/json"}
        
        with httpx.Client(timeout=30.0) as http_client:
            response = http_client.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                raise RuntimeError(
                    f"Gemini API request failed with status code {response.status_code}: {response.text}"
                )
            
            resp_data = response.json()
            try:
                text = resp_data["candidates"][0]["content"]["parts"][0]["text"]
                return text
            except (KeyError, IndexError) as e:
                raise RuntimeError(f"Unexpected response structure from Gemini API: {resp_data}") from e
