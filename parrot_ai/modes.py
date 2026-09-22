"""
PARROT-AI mode system.

Three modes:
  - RAGEBAIT (default) — full parrot roasts
  - ASSISTANT (hidden) — normal chatbot behavior
  - REFLECT (temporary) — after-action report
"""
from __future__ import annotations

from dataclasses import dataclass


MODE_RAGEBAIT = "ragebait"
MODE_ASSISTANT = "assistant"
MODE_REFLECT = "reflect"

VALID_MODES = {MODE_RAGEBAIT, MODE_ASSISTANT, MODE_REFLECT}

COMMAND_SLEEP = "/sleep"
COMMAND_WAKE = "/wake"
COMMAND_REFLECT = "/reflect"

SLEEP_REPLY = "ok. what's up."
WAKE_REPLY = "A+W."


@dataclass
class ModeState:
    """Tracks the current mode for a session."""
    current: str = MODE_RAGEBAIT
    previous: str = MODE_RAGEBAIT

    def set(self, mode: str) -> None:
        if mode not in VALID_MODES:
            raise ValueError(f"invalid mode: {mode}")
        if mode != MODE_REFLECT:
            self.previous = self.current
        self.current = mode

    def back(self) -> None:
        """Return to previous non-reflect mode."""
        self.current = self.previous if self.previous != MODE_REFLECT else MODE_RAGEBAIT

    def is_ragebait(self) -> bool:
        return self.current == MODE_RAGEBAIT

    def is_assistant(self) -> bool:
        return self.current == MODE_ASSISTANT

    def is_reflect(self) -> bool:
        return self.current == MODE_REFLECT