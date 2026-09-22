"""
PARROT-AI global stats tracker.

Tracks aggregate events across all sessions on this machine:
  - ragequits          (confirmed: user typed a ragequit phrase)
  - session_exits      (detected: tab closed / navigated away)
  - sessions           (total starts)
  - total_turns        (all messages sent)
  - total_spam         (A+W + roasts)
  - total_answers      (LLM answers, when wired up)
  - aplusw_responses   (responses that literally contained A+W)
  - longest_session    (turns in the longest single session)

Persisted to data/global_stats.json with a thread lock so it
can't corrupt under concurrent writes.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

DEFAULT_STATS_FILE = Path("data/global_stats.json")

_lock = Lock()


@dataclass
class GlobalStats:
    ragequits: int = 0
    ragequit_rate_numerator: int = 0
    ragequit_rate_denominator: int = 0
    session_exits: int = 0
    sessions: int = 0
    total_turns: int = 0
    total_spam: int = 0
    total_answers: int = 0
    aplusw_responses: int = 0
    longest_session_turns: int = 0
    first_seen: str = ""
    last_seen: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        denom = self.ragequit_rate_denominator or 1
        d["ragequit_rate"] = round(
            100.0 * self.ragequit_rate_numerator / denom, 2
        )
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "GlobalStats":
        allowed = set(cls.__dataclass_fields__)
        return cls(**{k: v for k, v in d.items() if k in allowed})


class GlobalStatsTracker:
    def __init__(self, stats_file: Path | None = None) -> None:
        self.stats_file = Path(stats_file or DEFAULT_STATS_FILE)
        self.stats = self._load()

    # ── IO ────────────────────────────────────────────────────
    def _load(self) -> GlobalStats:
        if not self.stats_file.exists():
            return GlobalStats()
        try:
            with self.stats_file.open(encoding="utf-8") as f:
                return GlobalStats.from_dict(json.load(f))
        except (OSError, json.JSONDecodeError):
            return GlobalStats()

    def save(self) -> None:
        with _lock:
            try:
                self.stats_file.parent.mkdir(parents=True, exist_ok=True)
                with self.stats_file.open("w", encoding="utf-8") as f:
                    json.dump(self.stats.to_dict(), f, indent=2)
            except OSError:
                pass

    def _touch(self) -> None:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        if not self.stats.first_seen:
            self.stats.first_seen = now
        self.stats.last_seen = now

    # ── RECORDERS ─────────────────────────────────────────────
    def record_session_start(self) -> None:
        self.stats.sessions += 1
        self._touch()
        self.save()

    def record_turn(
        self,
        spam: bool = False,
        answer: bool = False,
        is_aplusw: bool = False,
    ) -> None:
        self.stats.total_turns += 1
        if spam:
            self.stats.total_spam += 1
        if answer:
            self.stats.total_answers += 1
        if is_aplusw:
            self.stats.aplusw_responses += 1
        self._touch()

    def record_ragequit(self) -> None:
        self.stats.ragequits += 1
        self.stats.ragequit_rate_numerator += 1
        self.stats.ragequit_rate_denominator += 1
        self._touch()
        self.save()

    def record_session_with_turns(self) -> None:
        self.stats.ragequit_rate_denominator += 1

    def record_session_exit(self) -> None:
        self.stats.session_exits += 1
        self._touch()
        self.save()

    def record_session_length(self, turns: int) -> None:
        if turns > self.stats.longest_session_turns:
            self.stats.longest_session_turns = turns
        self.save()