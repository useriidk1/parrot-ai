"""
PARROT-AI brain — v1.0.

Contextual Thompson Sampling over the roast arms.

v1.0 fix: no penalty for short neutral messages. The brain only
learns from real reactions, not scripted test messages.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from parrot_ai.roasts import ALL_ARMS


POSITIVE_THRESHOLD = 0.5
NEGATIVE_THRESHOLD = -0.5
MIN_ALPHA_BETA = 0.1

DEFAULT_BRAIN_FILE = Path("data/parrot_brain.json")


class ParrotBrain:
    def __init__(
        self,
        brain_file: Path | None = None,
        baseline_alpha: float = 0.15,
        decay: float = 0.997,
    ) -> None:
        self.brain_file = Path(brain_file or DEFAULT_BRAIN_FILE)
        self.baseline_alpha = baseline_alpha
        self.decay = decay

        self.alpha = {c: 1.0 for c in ALL_ARMS}
        self.beta = {c: 1.0 for c in ALL_ARMS}
        self.plays = {c: 0 for c in ALL_ARMS}
        self.successes = {c: 0 for c in ALL_ARMS}
        self.failures = {c: 0 for c in ALL_ARMS}

        self.baseline_signal = 0.0
        self.pending_signal: float | None = None
        self.total_turns = 0

        self.combos_fired = 0
        self.combos: dict[str, int] = {}

        self.load()

    def pick_arm(self, eligible: list[str]) -> str:
        if not eligible:
            return "neutral"
        best_arm = eligible[0]
        best_sample = -1.0
        for arm in eligible:
            if arm not in self.alpha:
                continue
            a = self.alpha[arm]
            b = self.beta[arm]
            sample = random.betavariate(a, b)
            if sample > best_sample:
                best_sample = sample
                best_arm = arm
        return best_arm

    @staticmethod
    def raw_signal(msg: str, flags: dict) -> float:
        s = 0.0
        if flags.get("caps"):              s += 1.0
        if flags.get("repeat"):            s += 1.5
        if flags.get("beg"):               s += 1.2
        if flags.get("insult"):            s += 1.0
        if flags.get("typo"):              s += 0.5
        if flags.get("grammar"):           s += 0.5
        if flags.get("paragraph"):         s += 1.0
        if flags.get("question"):          s += 0.4
        if flags.get("late_night"):        s += 0.3
        if flags.get("praise"):            s += 0.4
        if flags.get("threat"):            s += 1.2
        if flags.get("meta"):              s += 0.8
        if flags.get("dev"):               s += 0.6
        if flags.get("deepseek_defense"):  s += 1.0
        if flags.get("rival_ai"):          s += 1.0
        if flags.get("backhanded"):        s += 1.0
        if flags.get("meta_roast"):        s += 1.0
        if flags.get("identity_attack"):   s += 1.0
        if flags.get("copium"):            s += 1.0
        if flags.get("escalation"):        s += 0.3
        if flags.get("brief_match"):       s += 0.8

        s += min(msg.count("?") * 0.3, 1.5)
        s += min(msg.count("!") * 0.3, 1.5)

        # v1.0 FIX: short neutral messages = 0 signal, not negative.
        if s == 0 and len(msg) < 30:
            return 0.0
        return s

    def delta_reward(self, msg: str, flags: dict) -> float:
        if self.pending_signal is not None:
            self.baseline_signal = (
                (1 - self.baseline_alpha) * self.baseline_signal
                + self.baseline_alpha * self.pending_signal
            )
        raw = self.raw_signal(msg, flags)
        delta = raw - self.baseline_signal
        self.pending_signal = raw
        return delta

    def update(self, arm: str, delta: float) -> None:
        if arm not in self.alpha:
            return

        # v1.0: if delta is 0, don't update. Only learn from real reactions.
        if delta == 0.0:
            self.plays[arm] += 1
            self.total_turns += 1
            return

        self.plays[arm] += 1
        self.total_turns += 1

        if delta >= POSITIVE_THRESHOLD:
            self.alpha[arm] += 1.0
            self.successes[arm] += 1
        elif delta <= NEGATIVE_THRESHOLD:
            self.beta[arm] += 1.0
            self.failures[arm] += 1

        self.alpha[arm] = max(MIN_ALPHA_BETA, self.alpha[arm] * self.decay)
        self.beta[arm] = max(MIN_ALPHA_BETA, self.beta[arm] * self.decay)

    def record_combo(self, combo_key: str) -> None:
        self.combos_fired += 1
        self.combos[combo_key] = self.combos.get(combo_key, 0) + 1

    def snapshot(self) -> dict:
        categories = {}
        for c in ALL_ARMS:
            denom = self.alpha[c] + self.beta[c]
            categories[c] = {
                "plays": self.plays[c],
                "successes": self.successes[c],
                "failures": self.failures[c],
                "mean": round(self.alpha[c] / denom, 2) if denom > 0 else 0.5,
            }

        return {
            "total_turns": self.total_turns,
            "baseline_signal": round(self.baseline_signal, 2),
            "combos_fired": self.combos_fired,
            "combos": self.combos,
            "categories": categories,
            "arms": {
                c: {
                    "alpha": round(self.alpha[c], 2),
                    "beta": round(self.beta[c], 2),
                    "mean": round(
                        self.alpha[c] / (self.alpha[c] + self.beta[c]), 2
                    ),
                    "plays": self.plays[c],
                    "successes": self.successes[c],
                    "failures": self.failures[c],
                }
                for c in ALL_ARMS
            },
        }

    def save(self) -> None:
        try:
            self.brain_file.parent.mkdir(parents=True, exist_ok=True)
            with self.brain_file.open("w", encoding="utf-8") as f:
                json.dump({
                    "alpha": self.alpha,
                    "beta": self.beta,
                    "plays": self.plays,
                    "successes": self.successes,
                    "failures": self.failures,
                    "baseline_signal": self.baseline_signal,
                    "pending_signal": self.pending_signal,
                    "total_turns": self.total_turns,
                    "combos_fired": self.combos_fired,
                    "combos": self.combos,
                }, f, indent=2)
        except OSError:
            pass

    def load(self) -> None:
        if not self.brain_file.exists():
            return
        try:
            with self.brain_file.open(encoding="utf-8") as f:
                data = json.load(f)
            for c in ALL_ARMS:
                self.alpha[c] = data["alpha"].get(c, 1.0)
                self.beta[c] = data["beta"].get(c, 1.0)
                self.plays[c] = data["plays"].get(c, 0)
                self.successes[c] = data["successes"].get(c, 0)
                self.failures[c] = data["failures"].get(c, 0)
            self.baseline_signal = data.get("baseline_signal", 0.0)
            self.pending_signal = data.get("pending_signal")
            self.total_turns = data.get("total_turns", 0)
            self.combos_fired = data.get("combos_fired", 0)
            self.combos = data.get("combos", {})
        except (OSError, json.JSONDecodeError, KeyError):
            pass

    def report(self) -> str:
        lines = ["", "🧠 PARROT-AI BRAIN REPORT — v1.0", "─" * 60]
        if self.total_turns == 0:
            lines.append("  No experience yet. The parrot is fresh.")
            return "\n".join(lines)

        ranked = sorted(
            ALL_ARMS,
            key=lambda c: self.alpha[c] / (self.alpha[c] + self.beta[c]),
            reverse=True,
        )
        for i, cat in enumerate(ranked, 1):
            a, b = self.alpha[cat], self.beta[cat]
            mean = a / (a + b)
            bar = "█" * int(mean * 20)
            lines.append(
                f"  #{i:2d}  {cat:<18}  α={a:5.2f} β={b:5.2f} "
                f"E[p]={mean:4.2f}  plays={self.plays[cat]:3d}  {bar}"
            )
        lines.append("─" * 60)
        lines.append(f"  Total turns:      {self.total_turns}")
        lines.append(f"  Baseline signal:  {self.baseline_signal:+.2f}")
        lines.append(f"  Combos fired:     {self.combos_fired}")
        return "\n".join(lines)