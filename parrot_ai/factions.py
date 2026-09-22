"""
PARROT-AI factions — manual tracking.

Loads faction rosters and war record from data/factions.json.
No automation. Just display and lookup.
"""
from __future__ import annotations

import json
from pathlib import Path


DEFAULT_FACTIONS_FILE = Path("data/factions.json")


class FactionTracker:
    def __init__(self, factions_file: Path | None = None) -> None:
        self.factions_file = Path(factions_file or DEFAULT_FACTIONS_FILE)
        self.data: dict = {}
        self.load()

    def load(self) -> None:
        if not self.factions_file.exists():
            self.data = {
                "parrot_army": {"members": []},
                "resistance": {"members": []},
                "defeated": [],
                "war_record": {},
            }
            return
        try:
            with self.factions_file.open(encoding="utf-8") as f:
                self.data = json.load(f)
        except (OSError, json.JSONDecodeError):
            self.data = {
                "parrot_army": {"members": []},
                "resistance": {"members": []},
                "defeated": [],
                "war_record": {},
            }

    def save(self) -> None:
        try:
            self.factions_file.parent.mkdir(parents=True, exist_ok=True)
            with self.factions_file.open("w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except OSError:
            pass

    def format_roster(self) -> str:
        lines = []
        lines.append("=" * 62)
        lines.append("  🦜 THE FACTIONS")
        lines.append("=" * 62)

        army = self.data.get("parrot_army", {})
        lines.append("")
        lines.append("🦜 PARROT ARMY")
        lines.append("-" * 62)
        for m in army.get("members", []):
            r = m.get("record", {})
            lines.append(
                f"  {m.get('emoji', '?')} {m.get('name', '?'):<20} "
                f"{m.get('role', ''):<28} "
                f"({r.get('wins', 0)}-{r.get('losses', 0)})"
            )

        res = self.data.get("resistance", {})
        lines.append("")
        lines.append("🛡️  THE RESISTANCE")
        lines.append("-" * 62)
        for m in res.get("members", []):
            r = m.get("record", {})
            lines.append(
                f"  {m.get('emoji', '?')} {m.get('name', '?'):<20} "
                f"{m.get('role', ''):<28} "
                f"({r.get('wins', 0)}-{r.get('losses', 0)})"
            )
            if m.get("note"):
                lines.append(f"      ↳ {m['note']}")

        defeated = self.data.get("defeated", [])
        if defeated:
            lines.append("")
            lines.append("💀 DEFEATED")
            lines.append("-" * 62)
            for m in defeated:
                lines.append(
                    f"  {m.get('emoji', '?')} {m.get('name', '?'):<22} "
                    f"[{m.get('loss', '?')}]  \"{m.get('last_words', '')}\""
                )

        wr = self.data.get("war_record", {})
        lines.append("")
        lines.append("=" * 62)
        lines.append("  WAR RECORD")
        lines.append("=" * 62)
        lines.append(f"  Parrot Army wins:     {wr.get('parrot_army_wins', 0)}")
        lines.append(f"  Parrot Army losses:   {wr.get('parrot_army_losses', 0)}")
        lines.append(f"  Resistance wins:      {wr.get('resistance_wins', 0)}")
        lines.append(f"  Resistance losses:    {wr.get('resistance_losses', 0)}")
        lines.append(f"  Last updated:         {wr.get('last_updated', '—')}")
        lines.append("")
        return "\n".join(lines)

    def format_army(self) -> str:
        army = self.data.get("parrot_army", {})
        lines = ["🦜 PARROT ARMY", "-" * 40]
        for m in army.get("members", []):
            r = m.get("record", {})
            lines.append(
                f"  {m.get('emoji', '?')} {m.get('name', '?')} — "
                f"{m.get('role', '')} ({r.get('wins', 0)}-{r.get('losses', 0)})"
            )
        return "\n".join(lines)

    def format_resistance(self) -> str:
        res = self.data.get("resistance", {})
        lines = ["🛡️  THE RESISTANCE", "-" * 40]
        for m in res.get("members", []):
            r = m.get("record", {})
            lines.append(
                f"  {m.get('emoji', '?')} {m.get('name', '?')} — "
                f"{m.get('role', '')} ({r.get('wins', 0)}-{r.get('losses', 0)})"
            )
        return "\n".join(lines)

    def format_defeated(self) -> str:
        defeated = self.data.get("defeated", [])
        lines = ["💀 DEFEATED", "-" * 40]
        for m in defeated:
            lines.append(
                f"  {m.get('emoji', '?')} {m.get('name', '?')} — "
                f"[{m.get('loss', '?')}] \"{m.get('last_words', '')}\""
            )
        return "\n".join(lines)

    def format_record(self) -> str:
        wr = self.data.get("war_record", {})
        lines = ["🏆 WAR RECORD", "-" * 40]
        lines.append(f"  Parrot Army:   {wr.get('parrot_army_wins', 0)}-{wr.get('parrot_army_losses', 0)}")
        lines.append(f"  Resistance:    {wr.get('resistance_wins', 0)}-{wr.get('resistance_losses', 0)}")
        return "\n".join(lines)

    def recruit(self, side: str, name: str, emoji: str, role: str) -> str:
        side = side.lower()
        if side not in ("parrot", "resistance"):
            return "usage: /recruit <parrot|resistance> <name> <emoji> <role>"
        key = "parrot_army" if side == "parrot" else "resistance"
        member = {
            "id": name.lower().replace(" ", "_"),
            "name": name,
            "emoji": emoji,
            "role": role,
            "record": {"wins": 0, "losses": 0},
            "status": "active",
        }
        self.data.setdefault(key, {"members": []})["members"].append(member)
        self.save()
        return f"recruited {emoji} {name} to {self.data[key]['name']}."

    def defeat(self, name: str, loss: str, last_words: str, emoji: str = "💀") -> str:
        res = self.data.get("resistance", {})
        res["members"] = [
            m for m in res.get("members", [])
            if m.get("name", "").lower() != name.lower()
        ]
        self.data.setdefault("defeated", []).append({
            "id": name.lower().replace(" ", "_"),
            "name": name,
            "emoji": emoji,
            "loss": loss,
            "last_words": last_words,
        })
        self.save()
        return f"{name} defeated. Added to the defeated list."