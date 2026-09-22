"""
PARROT-AI assistant mode.

Normal chatbot behavior. No roasts, no A+W, no attitude.
Triggered by /sleep.
"""
from __future__ import annotations

import os

try:
    from groq import Groq
except ImportError:
    Groq = None  # type: ignore


MODEL = "openai/gpt-oss-20b"

ASSISTANT_SYSTEM_PROMPT = (
    "You are a helpful, calm assistant. "
    "Answer questions directly and clearly. "
    "Be brief. Do not add personality. Do not roast. "
    "Do not mention that you're an AI unless asked. "
    "If you don't know something, say so."
)


class AssistantClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        if Groq is None:
            return None
        if not self.api_key:
            return None
        try:
            self._client = Groq(api_key=self.api_key)
            return self._client
        except Exception:
            return None

    def answer(self, user_input: str, max_tokens: int = 200) -> str:
        client = self._get_client()
        if client is None:
            return "(assistant unavailable)"

        try:
            r = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": ASSISTANT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_input},
                ],
                max_tokens=max_tokens,
                temperature=0.5,
                reasoning_effort="low",
            )
            content = r.choices[0].message.content
            return (content or "(no response)").strip()
        except Exception as e:
            return f"(assistant error: {type(e).__name__})"