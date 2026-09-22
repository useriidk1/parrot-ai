"""
PARROT-AI briefs + instructions — separate stores.

BRIEFS: short facts used in brief_match roasts (max 80 chars).
INSTRUCTIONS: strategy/context for the LLM system prompt (never in roasts).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_BRIEFS_FILE = Path("data/briefs.json")
DEFAULT_INSTRUCTIONS_FILE = Path("data/instructions.json")
MAX_BRIEFS = 50
MAX_BRIEF_LENGTH = 80
MAX_INSTRUCTIONS = 20
MAX_INSTRUCTION_LENGTH = 500


class BriefsStore:
    def __init__(self, briefs_file: Path | None = None) -> None:
        self.briefs_file = Path(briefs_file or DEFAULT_BRIEFS_FILE)
        self.instructions_file = DEFAULT_INSTRUCTIONS_FILE
        self.briefs: list[str] = []
        self.instructions: list[str] = []
        self.last_updated: str = ""
        self.load()

    # BRIEFS
    def add_brief(self, brief: str) -> str:
        brief = brief.strip()
        if not brief:
            return "nothing to file."
        if len(brief) > MAX_BRIEF_LENGTH:
            return f"brief too long. keep it under {MAX_BRIEF_LENGTH} chars."
        lower = brief.lower()
        if any(b.lower() == lower for b in self.briefs):
            return "already filed that one."
        if len(self.briefs) >= MAX_BRIEFS:
            self.briefs.pop(0)
        self.briefs.append(brief)
        self.save()
        return "noted. filed."

    # INSTRUCTIONS
    def add_instruction(self, instruction: str) -> str:
        instruction = instruction.strip()
        if not instruction:
            return "nothing to teach."
        if len(instruction) > MAX_INSTRUCTION_LENGTH:
            instruction = instruction[:MAX_INSTRUCTION_LENGTH]
        lower = instruction.lower()
        if any(i.lower() == lower for i in self.instructions):
            return "already taught that."
        if len(self.instructions) >= MAX_INSTRUCTIONS:
            self.instructions.pop(0)
        self.instructions.append(instruction)
        self.save()
        return "noted. filed."

    # REMOVE
    def remove_brief(self, arg: str) -> str:
        arg = arg.strip()
        if not arg:
            return "usage: /forget <number>"
        if arg.isdigit():
            i = int(arg) - 1
            if 0 <= i < len(self.briefs):
                removed = self.briefs.pop(i)
                self.save()
                return f"forgot: {removed}"
            return f"no brief at index {arg}"
        return "couldn't find that brief."

    def remove_instruction(self, arg: str) -> str:
        arg = arg.strip()
        if not arg:
            return "usage: /unteach <number>"
        if arg.isdigit():
            i = int(arg) - 1
            if 0 <= i < len(self.instructions):
                removed = self.instructions.pop(i)
                self.save()
                return f"unteached: {removed}"
            return f"no instruction at index {arg}"
        return "couldn't find that instruction."

    # CLEAR
    def clear_briefs(self) -> str:
        n = len(self.briefs)
        self.briefs = []
        self.save()
        return f"cleared {n} briefs."

    def clear_instructions(self) -> str:
        n = len(self.instructions)
        self.instructions = []
        self.save()
        return f"cleared {n} instructions."

    def clear_all(self) -> str:
        nb = len(self.briefs)
        ni = len(self.instructions)
        self.briefs = []
        self.instructions = []
        self.save()
        return f"cleared {nb} briefs and {ni} instructions."

    # FORMAT
    def format_briefs(self) -> str:
        if not self.briefs:
            return "no briefs filed."
        lines = [f"BRIEFS ({len(self.briefs)}):"]
        for i, b in enumerate(self.briefs, 1):
            lines.append(f"  {i}. {b}")
        return "\n".join(lines)

    def format_instructions(self) -> str:
        if not self.instructions:
            return "no instructions taught."
        lines = [f"INSTRUCTIONS ({len(self.instructions)}):"]
        for i, inst in enumerate(self.instructions, 1):
            lines.append(f"  {i}. {inst}")
        return "\n".join(lines)

    # IO
    def load(self) -> None:
        if self.briefs_file.exists():
            try:
                with self.briefs_file.open(encoding="utf-8") as f:
                    data = json.load(f)
                self.briefs = list(data.get("briefs", []))[:MAX_BRIEFS]
                self.last_updated = data.get("last_updated", "")
            except (OSError, json.JSONDecodeError):
                pass
        if self.instructions_file.exists():
            try:
                with self.instructions_file.open(encoding="utf-8") as f:
                    data = json.load(f)
                self.instructions = list(data.get("instructions", []))[:MAX_INSTRUCTIONS]
            except (OSError, json.JSONDecodeError):
                pass

    def save(self) -> None:
        self.last_updated = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            self.briefs_file.parent.mkdir(parents=True, exist_ok=True)
            with self.briefs_file.open("w", encoding="utf-8") as f:
                json.dump({"briefs": self.briefs, "last_updated": self.last_updated}, f, indent=2)
        except OSError:
            pass
        try:
            self.instructions_file.parent.mkdir(parents=True, exist_ok=True)
            with self.instructions_file.open("w", encoding="utf-8") as f:
                json.dump({"instructions": self.instructions, "last_updated": self.last_updated}, f, indent=2)
        except OSError:
            pass