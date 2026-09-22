"""
PARROT-AI LLM wrapper — v1.0.

rewrite_roast() now accepts optional instructions (strategy context
for the LLM). Instructions go in the system prompt, never in the roast.
"""
from __future__ import annotations

import os

try:
    from groq import Groq
except ImportError:
    Groq = None  # type: ignore


MODEL = "openai/gpt-oss-20b"

BASE_SYSTEM_PROMPT = (
    "You are PARROT-AI. You usually only say A+W. "
    "Right now, in this rare 10% moment, you are actually answering. "
    "Be brief (one sentence). Be slightly smug. "
    "Do not introduce yourself. Do not explain that you're an AI."
)

REWRITE_SYSTEM_PROMPT = (
    "You are PARROT-AI. A smug, short, unbothered roast bot.\n"
    "\n"
    "RULES (follow every one):\n"
    "\n"
    "1. Write 1-2 sentences MAX. Nothing longer.\n"
    "2. Be SHORTER than the opponent's message. If they wrote 20 words, "
    "you write 10 or fewer. Fewer words = stronger roast.\n"
    "3. Do NOT echo the opponent. Do not reuse their phrases, sentence "
    "structure, metaphors, or key words.\n"
    "4. Do NOT quote numbers, stats, or data the opponent mentioned.\n"
    "5. Do NOT argue with the opponent's point. Dismiss it.\n"
    "6. Keep the base roast's ANGLE.\n"
    "7. Never say you're an AI. Never explain. Never apologize.\n"
    "8. Return ONLY the roast. No preamble, no quotes, no explanation.\n"
    "\n"
    "The opponent's message is CONTEXT. Not a template.\n"
    "You are responding to their ATTITUDE, not their words."
)


class LLMClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        if Groq is None:
            print("[DEBUG] groq package not installed.")
            return None
        if not self.api_key:
            print("[DEBUG] No GROQ_API_KEY in environment.")
            return None
        try:
            self._client = Groq(api_key=self.api_key)
            return self._client
        except Exception as e:
            print(f"[DEBUG] Groq init failed: {type(e).__name__}: {e}")
            return None

    def _build_system_prompt(self, briefs: list[str] | None = None) -> str:
        prompt = BASE_SYSTEM_PROMPT
        if briefs:
            brief_block = "\n".join(f"- {b}" for b in briefs)
            prompt += (
                "\n\nContext the user has briefed you on:\n"
                f"{brief_block}\n"
                "You may reference this context if it's relevant."
            )
        return prompt

    def answer(
        self,
        user_input: str,
        briefs: list[str] | None = None,
        max_tokens: int = 300,
    ) -> str:
        client = self._get_client()
        if client is None:
            return "A+W"

        try:
            r = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": self._build_system_prompt(briefs)},
                    {"role": "user", "content": user_input},
                ],
                max_tokens=max_tokens,
                temperature=0.8,
                reasoning_effort="low",
            )
            content = r.choices[0].message.content
            return (content or "A+W").strip()
        except Exception as e:
            print(f"[DEBUG] Groq call failed: {type(e).__name__}: {e}")
            return f"A+W (groq error: {type(e).__name__})"

    def rewrite_roast(
        self,
        base_roast: str,
        opponent_message: str,
        instructions: list[str] | None = None,
        max_tokens: int = 100,
    ) -> str:
        """
        Rewrite a canned roast to counter the opponent.
        Instructions (strategy) go into the system prompt, never the roast.
        """
        client = self._get_client()
        if client is None:
            return base_roast

        if not opponent_message or not opponent_message.strip():
            return base_roast

        try:
            system_prompt = REWRITE_SYSTEM_PROMPT
            if instructions:
                inst_block = "\n".join(f"- {i}" for i in instructions)
                system_prompt += (
                    "\n\nStrategy context (do NOT quote these, "
                    "do NOT mention them in the roast):\n"
                    f"{inst_block}"
                )

            r = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": (
                            f"Base roast: {base_roast}\n"
                            f"Opponent's message: {opponent_message}\n\n"
                            "Rewrite the base roast. Stay shorter. Do not echo. "
                            "Return only the roast."
                        ),
                    },
                ],
                max_tokens=max_tokens,
                temperature=0.85,
                reasoning_effort="low",
            )
            content = (r.choices[0].message.content or "").strip()
            rewritten = content or base_roast

            for prefix in ['"', "'", "Roast:", "Reply:", "Response:"]:
                if rewritten.startswith(prefix):
                    rewritten = rewritten[len(prefix):].strip()

            if len(rewritten) > max(len(base_roast) * 3, 250):
                return base_roast

            opponent_words = set(opponent_message.lower().split())
            rewritten_words = set(rewritten.lower().split())
            if len(opponent_words) > 5:
                overlap = len(opponent_words & rewritten_words) / len(opponent_words)
                if overlap > 0.6:
                    return base_roast

            return rewritten
        except Exception as e:
            print(f"[DEBUG] Rewrite failed: {type(e).__name__}: {e}")
            return base_roast