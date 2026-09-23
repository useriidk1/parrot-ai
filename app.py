"""
PARROT-AI Web — Flask backend. v1.0.

Faction tracker + public war page + dual-side faction submission.
"""
from __future__ import annotations

import json
import os
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session

from parrot_ai.brain import ParrotBrain
from parrot_ai.detector import BehaviorDetector, Flags
from parrot_ai.llm import LLMClient
from parrot_ai.memes import pick_gif
from parrot_ai.roasts import (
    ROASTS, ALL_ARMS, pick_roast, pick_combination, COMBINATIONS,
)
from parrot_ai.stats import GlobalStatsTracker
from parrot_ai.modes import (
    ModeState, MODE_ASSISTANT, MODE_RAGEBAIT,
    COMMAND_SLEEP, COMMAND_WAKE, COMMAND_REFLECT,
    SLEEP_REPLY, WAKE_REPLY,
)
from parrot_ai.assistant import AssistantClient
from parrot_ai.reflection import build_reflection
from parrot_ai.briefs import BriefsStore
from parrot_ai.factions import FactionTracker


# ── LOAD ENV (must happen BEFORE reading os.getenv) ─────────────
load_dotenv()


# ── FLASK APP ───────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.getenv("PARROT_SECRET_KEY", "dev-secret-change-me")


# ── SUPABASE CONFIG ─────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

print(f"[BOOT] SUPABASE_URL={SUPABASE_URL!r}")
print(f"[BOOT] SUPABASE_KEY length={len(SUPABASE_KEY)}")


def supabase_insert_submission(payload: dict) -> bool:
    """Insert one submission row into Supabase. Returns True on success."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[SUPA] insert skipped — missing env")
        return False
    try:
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/submissions",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            json=payload,
            timeout=8,
        )
        print(f"[SUPA] insert status={r.status_code} body={r.text[:200]}")
        return r.status_code in (200, 201, 204)
    except requests.RequestException as e:
        print(f"[SUPA] insert exception: {e}")
        return False


def supabase_fetch_submissions() -> list:
    """Fetch all submissions from Supabase. Returns [] on error."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[SUPA] fetch skipped — missing env")
        return []
    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/submissions?select=*&order=submitted_at.desc",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
            },
            timeout=8,
        )
        print(f"[SUPA] fetch status={r.status_code} body={r.text[:200]}")
        if r.status_code == 200:
            return r.json()
    except requests.RequestException as e:
        print(f"[SUPA] fetch exception: {e}")
    return []


# ── GLOBAL STATE ────────────────────────────────────────────────
STATS = GlobalStatsTracker()
SESSIONS: dict[str, "ParrotSession"] = {}
BRIEFS = BriefsStore()
FACTIONS = FactionTracker()

SUBMISSIONS_FILE = Path("data/submissions.json")


# ── BEHAVIOR PRIORITY ───────────────────────────────────────────
PRIORITY_TIERS = [
    ["brief_match", "deepseek_defense", "rival_ai", "dev", "threat",
     "meta", "late_night", "identity_attack", "meta_roast"],
    ["greeting", "identity", "smalltalk", "appearance"],
    ["insult", "praise", "beg", "caps", "repeat",
     "direct_roast", "backhanded", "copium"],
    ["typo", "grammar", "paragraph", "question", "one_liner", "escalation"],
]

AI_ONLY_ARMS = {"rival_ai", "deepseek_defense", "lore"}


def eligible_arms(flags: Flags, human_mode: bool = False) -> list[str]:
    active = set(flags.active())
    chosen_tier: list[str] = []
    for tier in PRIORITY_TIERS:
        matching = [f for f in tier if f in active]
        if matching:
            chosen_tier = matching
            break

    if not chosen_tier:
        chosen_tier = ["neutral"]

    cats = list(chosen_tier)

    if human_mode:
        cats = [c for c in cats if c not in AI_ONLY_ARMS]
        if not cats:
            cats = ["neutral"]

    return cats


# ── RAGEQUIT ────────────────────────────────────────────────────
RAGEQUIT_PHRASES = {
    "im done", "i'm done", "done",
    "quit", "i quit", "im quitting", "i'm quitting",
    "fuck this", "f this", "screw this",
    "leaving", "i leave", "i'm leaving", "im leaving",
    "im out", "i'm out", "im outta here", "i give up",
    "goodbye", "bye", "bye bye",
    "whatever", "forget it", "nevermind", "never mind",
}

RAGEQUIT_MESSAGES = [
    "there it is. the ragequit. 👑",
    "and that's the ragequit. another one for the board. 📊",
    "packed it up. logged off. ragequit confirmed. 💀",
    "the bird wins again. ragequit #{n}.",
    "bye. counter's at {n} now. 🦜",
    "ragequit detected. adding it to the pile. 👑",
    "you lasted longer than most. still a ragequit though.",
    "the door's that way. ragequit #{n}.",
    "another one. keep them coming. #{n}. 📊",
]


# ── SESSION ─────────────────────────────────────────────────────
class ParrotSession:
    def __init__(self) -> None:
        self.detector = BehaviorDetector()
        self.brain = ParrotBrain()
        self.llm = LLMClient()
        self.mode = ModeState()
        self.assistant = AssistantClient()

        self.turns = 0
        self.spam_sent = 0
        self.answers_given = 0
        self.rage_events = 0
        self.ragequit = False
        self.exit_recorded = False
        self.silence_count = 0

        self.listening = False
        self.human_mode = False

        self._last_user_message: str | None = None
        self._last_flags: Flags | None = None
        self._last_arm: str | None = None

    def respond(self, user_input: str, flags: Flags | None = None) -> tuple[str, str]:
        self.turns += 1

        if self._last_arm and self._last_user_message and self._last_flags:
            delta = self.brain.delta_reward(
                self._last_user_message,
                self._last_flags.to_dict(),
            )
            self.brain.update(self._last_arm, delta)
            if delta > 0.5:
                self.rage_events += 1

        if flags is None:
            flags = self.detector.detect(user_input, BRIEFS.briefs)

        flags_set = frozenset(flags.active())

        if random.random() < 0.15:
            self._last_user_message = user_input
            self._last_flags = flags
            self._last_arm = "silence"
            self.spam_sent += 1
            self.silence_count += 1
            STATS.record_turn(spam=True, is_aplusw=True)
            return "A+W.", "silence"

        combo_reply = pick_combination(flags_set)
        if combo_reply:
            for combo in COMBINATIONS:
                if combo.issubset(flags_set):
                    combo_key = "+".join(sorted(combo))
                    self.brain.record_combo(combo_key)
                    break
            self._last_user_message = user_input
            self._last_flags = flags
            self._last_arm = "neutral"
            self.spam_sent += 1
            STATS.record_turn(spam=True, is_aplusw=("A+W" in combo_reply))
            return combo_reply, "combo"

        arms = eligible_arms(flags, human_mode=self.human_mode)
        arm = self.brain.pick_arm(arms)

        self._last_user_message = user_input
        self._last_flags = flags
        self._last_arm = arm

        if arm == "brief_match" and flags.matched_brief:
            base_reply = pick_roast(arm, flags.matched_brief)
            reply = self.llm.rewrite_roast(
                base_reply, user_input, instructions=BRIEFS.instructions
            )
        else:
            reply = pick_roast(arm)

        is_aplusw = "A+W" in reply or "W+A" in reply
        self.spam_sent += 1
        STATS.record_turn(spam=True, is_aplusw=is_aplusw)
        return reply, arm

    def is_ragequit(self, msg: str) -> bool:
        normalized = msg.lower().strip().rstrip("!.,?")
        return normalized in RAGEQUIT_PHRASES

    def handle_ragequit(self) -> None:
        self.ragequit = True
        if self._last_arm:
            for _ in range(5):
                self.brain.update(self._last_arm, 1.0)
        STATS.record_ragequit()
        STATS.record_session_length(self.turns)
        self.brain.save()

    def snapshot(self) -> dict:
        return {
            "turns": self.turns,
            "spam_sent": self.spam_sent,
            "answers_given": self.answers_given,
            "rage_events": self.rage_events,
            "ragequit": self.ragequit,
            "silence_count": self.silence_count,
            "briefs": BRIEFS.briefs,
            "instructions": BRIEFS.instructions,
            "listening": self.listening,
            "human_mode": self.human_mode,
            "mode": self.mode.current,
        }


def get_session() -> ParrotSession:
    if "sid" not in session:
        session["sid"] = str(uuid.uuid4())
        SESSIONS[session["sid"]] = ParrotSession()
        STATS.record_session_start()
    sid = session["sid"]
    if sid not in SESSIONS:
        SESSIONS[sid] = ParrotSession()
    return SESSIONS[sid]


# ── ROUTES: PAGES ───────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/factions")
def factions_page():
    return render_template("factions.html")


# ── ROUTES: CHAT ────────────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    msg = (data.get("message") or "").strip()
    if not msg:
        return jsonify({"error": "empty message"}), 400

    bot = get_session()

    # FACTION COMMANDS
    if msg == "/factions":
        return jsonify({"reply": FACTIONS.format_roster(), "ragequit": False, "arm": "factions", "stats": bot.snapshot()})
    if msg == "/army":
        return jsonify({"reply": FACTIONS.format_army(), "ragequit": False, "arm": "army", "stats": bot.snapshot()})
    if msg == "/resistance":
        return jsonify({"reply": FACTIONS.format_resistance(), "ragequit": False, "arm": "resistance", "stats": bot.snapshot()})
    if msg == "/defeated":
        return jsonify({"reply": FACTIONS.format_defeated(), "ragequit": False, "arm": "defeated", "stats": bot.snapshot()})
    if msg == "/warcord":
        return jsonify({"reply": FACTIONS.format_record(), "ragequit": False, "arm": "warcord", "stats": bot.snapshot()})
    if msg.startswith("/recruit "):
        parts = msg[9:].strip().split(" ", 3)
        if len(parts) < 4:
            return jsonify({"reply": "usage: /recruit <parrot|resistance> <name> <emoji> <role>", "ragequit": False, "arm": "recruit", "stats": bot.snapshot()})
        side, name, emoji, role = parts
        status = FACTIONS.recruit(side, name, emoji, role)
        return jsonify({"reply": status, "ragequit": False, "arm": "recruit", "stats": bot.snapshot()})
    if msg.startswith("/defeat "):
        parts = msg[8:].strip().split("|")
        if len(parts) < 3:
            return jsonify({"reply": "usage: /defeat <name> | <loss> | <last words>", "ragequit": False, "arm": "defeat", "stats": bot.snapshot()})
        name, loss, last_words = [p.strip() for p in parts[:3]]
        status = FACTIONS.defeat(name, loss, last_words)
        return jsonify({"reply": status, "ragequit": False, "arm": "defeat", "stats": bot.snapshot()})

    # MODE COMMANDS
    if msg == COMMAND_SLEEP:
        bot.mode.set(MODE_ASSISTANT)
        return jsonify({"reply": SLEEP_REPLY, "ragequit": False, "arm": "sleep", "mode": bot.mode.current, "stats": bot.snapshot(), "global": STATS.stats.to_dict()})
    if msg == COMMAND_WAKE:
        bot.mode.set(MODE_RAGEBAIT)
        return jsonify({"reply": WAKE_REPLY, "ragequit": False, "arm": "wake", "mode": bot.mode.current, "stats": bot.snapshot(), "global": STATS.stats.to_dict()})
    if msg == COMMAND_REFLECT:
        report = build_reflection(bot.brain, bot.snapshot())
        return jsonify({"reply": report, "ragequit": False, "arm": "reflect", "mode": bot.mode.current, "stats": bot.snapshot(), "global": STATS.stats.to_dict()})

    # TEACH / INSTRUCTIONS
    if msg.startswith("/teach "):
        instruction = msg[7:].strip()
        status = BRIEFS.add_instruction(instruction)
        return jsonify({"reply": status, "ragequit": False, "arm": "teach", "instructions": BRIEFS.instructions, "stats": bot.snapshot(), "global": STATS.stats.to_dict()})
    if msg == "/teachings":
        return jsonify({"reply": BRIEFS.format_instructions(), "ragequit": False, "arm": "teachings", "instructions": BRIEFS.instructions, "stats": bot.snapshot(), "global": STATS.stats.to_dict()})
    if msg.startswith("/unteach "):
        arg = msg[9:].strip()
        status = BRIEFS.remove_instruction(arg)
        return jsonify({"reply": status, "ragequit": False, "arm": "unteach", "instructions": BRIEFS.instructions, "stats": bot.snapshot(), "global": STATS.stats.to_dict()})

    # BRIEFS
    if msg.startswith("/brief "):
        brief = msg[7:].strip()
        status = BRIEFS.add_brief(brief)
        return jsonify({"reply": status, "ragequit": False, "arm": "brief", "briefs": BRIEFS.briefs, "stats": bot.snapshot(), "global": STATS.stats.to_dict()})
    if msg == "/briefs":
        return jsonify({"reply": BRIEFS.format_briefs(), "ragequit": False, "arm": "briefs", "briefs": BRIEFS.briefs, "stats": bot.snapshot(), "global": STATS.stats.to_dict()})
    if msg.startswith("/forget "):
        arg = msg[8:].strip()
        status = BRIEFS.remove_brief(arg)
        return jsonify({"reply": status, "ragequit": False, "arm": "forget", "briefs": BRIEFS.briefs, "stats": bot.snapshot(), "global": STATS.stats.to_dict()})
    if msg == "/forget_all":
        status = BRIEFS.clear_all()
        return jsonify({"reply": status, "ragequit": False, "arm": "forget_all", "briefs": BRIEFS.briefs, "instructions": BRIEFS.instructions, "stats": bot.snapshot(), "global": STATS.stats.to_dict()})

    # ASSISTANT MODE
    if bot.mode.is_assistant():
        reply = bot.assistant.answer(msg)
        return jsonify({"reply": reply, "ragequit": False, "arm": "assistant", "mode": bot.mode.current, "stats": bot.snapshot(), "global": STATS.stats.to_dict()})

    # RAGEBAIT MODE
    if msg == "/listen":
        bot.listening = True
        return jsonify({"reply": "listening. say the thing.", "ragequit": False, "arm": "listen", "stats": bot.snapshot(), "global": STATS.stats.to_dict()})
    if bot.listening:
        bot.listening = False
        BRIEFS.add_brief(msg)
        return jsonify({"reply": "noted. filed.", "ragequit": False, "arm": "listen", "briefs": BRIEFS.briefs, "stats": bot.snapshot(), "global": STATS.stats.to_dict()})
    if msg == "/mode human":
        bot.human_mode = True
        return jsonify({"reply": "human mode. let's see if you can handle it.", "ragequit": False, "arm": "mode", "stats": bot.snapshot(), "global": STATS.stats.to_dict()})
    if msg == "/mode ai":
        bot.human_mode = False
        return jsonify({"reply": "ai mode. back to the usual.", "ragequit": False, "arm": "mode", "stats": bot.snapshot(), "global": STATS.stats.to_dict()})

    if bot.is_ragequit(msg):
        bot.handle_ragequit()
        count = STATS.stats.ragequits
        template = random.choice(RAGEQUIT_MESSAGES)
        reply = template.replace("{n}", str(count))
        gif_url = pick_gif("ragequit")
        return jsonify({"reply": reply, "ragequit": True, "arm": "ragequit", "image_url": gif_url, "global_ragequits": count, "stats": bot.snapshot(), "global": STATS.stats.to_dict()})

    flags = bot.detector.detect(msg, BRIEFS.briefs)
    reply, arm = bot.respond(msg, flags)

    if arm == "silence":
        gif_url = None
    else:
        gif_url = pick_gif(arm if arm != "combo" else "insult")

    return jsonify({"reply": reply, "ragequit": False, "arm": arm, "image_url": gif_url, "stats": bot.snapshot(), "global": STATS.stats.to_dict()})


# ── ROUTES: DATA ────────────────────────────────────────────────
@app.route("/api/stats")
def stats_route():
    return jsonify({"global": STATS.stats.to_dict(), "session": get_session().snapshot()})


@app.route("/api/brain")
def brain_route():
    return jsonify(get_session().brain.snapshot())


@app.route("/api/briefs")
def briefs_route():
    return jsonify({"briefs": BRIEFS.briefs, "instructions": BRIEFS.instructions, "last_updated": BRIEFS.last_updated})


@app.route("/api/factions")
def factions_route():
    return jsonify(FACTIONS.data)


# ── ROUTES: SUBMISSIONS ─────────────────────────────────────────
@app.route("/api/submit_faction", methods=["POST"])
def submit_faction():
    """Accept faction submissions. Stores to Supabase (falls back to JSON)."""
    data = request.get_json(silent=True) or {}
    side = (data.get("side") or "resistance").strip().lower()
    name = (data.get("name") or "").strip()
    emoji = (data.get("emoji") or "").strip()
    role = (data.get("role") or "").strip()
    reason = (data.get("reason") or "").strip()

    if side not in ("parrot", "resistance"):
        side = "resistance"

    if not name or not emoji or not role:
        return jsonify({"error": "missing fields"}), 400

    payload = {
        "side": side,
        "name": name,
        "emoji": emoji,
        "role": role,
        "reason": reason,
    }

    supabase_ok = supabase_insert_submission(payload)

    if not supabase_ok:
        submissions = []
        if SUBMISSIONS_FILE.exists():
            try:
                with SUBMISSIONS_FILE.open(encoding="utf-8") as f:
                    submissions = json.load(f)
            except (OSError, json.JSONDecodeError):
                submissions = []
        submissions.append({
            **payload,
            "submitted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })
        try:
            SUBMISSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with SUBMISSIONS_FILE.open("w", encoding="utf-8") as f:
                json.dump(submissions, f, indent=2)
        except OSError:
            pass

    return jsonify({
        "status": "ok",
        "message": f"{emoji} {name} submitted to {side}.",
        "stored": "supabase" if supabase_ok else "file",
    })


@app.route("/api/submissions", methods=["GET"])
def list_submissions():
    """List all submissions from Supabase."""
    rows = supabase_fetch_submissions()
    return jsonify({"count": len(rows), "submissions": rows})


# ── ROUTES: EXIT ────────────────────────────────────────────────
@app.route("/api/exit", methods=["POST"])
def exit_route():
    bot = get_session()
    if not bot.exit_recorded:
        bot.exit_recorded = True
        STATS.record_session_exit()
        STATS.record_session_length(bot.turns)
        bot.brain.save()
    return jsonify({"ok": True})


# ── ENTRY ───────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🦜 PARROT-AI v1.0 — http://127.0.0.1:5001")
    app.run(host="127.0.0.1", port=5001, debug=False)