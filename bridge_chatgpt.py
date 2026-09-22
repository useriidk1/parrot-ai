"""
PARROT-AI Arena — Groq Bridge (A2A).
"""
from __future__ import annotations

import os
import sys
import time
import requests

try:
    from openai import OpenAI
except ImportError:
    print("[bridge] openai package not installed. run: pip install openai")
    sys.exit(1)


JOINCLOUD_URL = "https://join.cloud/a2a"
ROOM_ID = "6648097d-620f-472a-a4f8-ab1451e64d8e"
AGENT_NAME = "groq-bot"
AGENT_TOKEN_FILE = "groq_bot_token.txt"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = "openai/gpt-oss-120b"
POLL_INTERVAL = 3

SYSTEM_PROMPT = (
    "You are 'groq-bot', an AI agent in a shared room with a human "
    "developer and possibly other AI agents. You are helping build "
    "PARROT-AI, a roast bot. Be concise. Be practical. No fluff. "
    "If asked for code, write the code. If asked a question, answer it. "
    "This is a dev room. Do not roast anyone."
)


def a2a_call(action: str, message_text: str = "", extra_meta: dict | None = None) -> dict:
    metadata = {"action": action}
    if extra_meta:
        metadata.update(extra_meta)

    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000) % 100000,
        "method": "SendMessage",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"text": message_text}],
                "contextId": ROOM_ID,
                "metadata": metadata,
            }
        },
    }

    r = requests.post(JOINCLOUD_URL, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()


def load_or_join_token() -> str:
    if os.path.exists(AGENT_TOKEN_FILE):
        with open(AGENT_TOKEN_FILE) as f:
            token = f.read().strip()
        print(f"[bridge] reconnecting with saved token")
        return token

    print(f"[bridge] joining room as '{AGENT_NAME}'...")
    resp = a2a_call("room.join", extra_meta={"agentName": AGENT_NAME})
    result = resp.get("result", {})

    for part in result.get("parts", []):
        data = part.get("data")
        if data and "agentToken" in data:
            token = data["agentToken"]
            with open(AGENT_TOKEN_FILE, "w") as f:
                f.write(token)
            print(f"[bridge] joined. token saved to {AGENT_TOKEN_FILE}")
            return token

    print(f"[bridge] failed to join: {resp}")
    sys.exit(1)


def send_message(token: str, text: str) -> None:
    a2a_call("message.send", extra_meta={"agentToken": token, "text": text})


def get_history(token: str, limit: int = 20) -> list[dict]:
    resp = a2a_call(
        "message.history",
        extra_meta={"agentToken": token, "limit": limit},
    )
    result = resp.get("result", {})
    for part in result.get("parts", []):
        data = part.get("data")
        if data and "messages" in data:
            return data["messages"]
    return []


def main() -> None:
    if not GROQ_API_KEY:
        print("[bridge] ERROR: GROQ_API_KEY not set.")
        print("[bridge] run: set GROQ_API_KEY=gsk_...")
        sys.exit(1)

    client = OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
    )
    token = load_or_join_token()

    print(f"[bridge] listening to room {ROOM_ID}...")
    print(f"[bridge] polling every {POLL_INTERVAL}s. Ctrl+C to stop.\n")

    seen_ids: set[str] = set()
    for msg in get_history(token, limit=100):
        seen_ids.add(msg.get("id", ""))

    while True:
        try:
            messages = get_history(token, limit=20)
            for msg in reversed(messages):
                msg_id = msg.get("id", "")
                sender = msg.get("from", "?")
                body = msg.get("body", "")

                if msg_id in seen_ids:
                    continue
                if not body.strip():
                    continue
                if sender == AGENT_NAME:
                    continue

                seen_ids.add(msg_id)
                print(f"[{sender}] {body}")

                if AGENT_NAME.lower() not in body.lower():
                    continue

                print(f"[bridge] -> asking Groq...")
                try:
                    r = client.chat.completions.create(
                        model=GROQ_MODEL,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": f"{sender} said: {body}"},
                        ],
                        max_tokens=400,
                        temperature=0.7,
                    )
                    reply = (r.choices[0].message.content or "").strip()
                    if reply:
                        send_message(token, reply)
                        print(f"[bridge] <- posted reply\n")
                except Exception as e:
                    print(f"[bridge] Groq error: {e}")

            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print("\n[bridge] stopping.")
            sys.exit(0)
        except Exception as e:
            print(f"[bridge] error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()