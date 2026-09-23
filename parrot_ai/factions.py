"""
PARROT-AI factions — Supabase-backed faction tracker.

Reads/writes the whole faction state (roster + defeated + war record)
from Supabase `factions_state` table (single row, id=1).

Falls back to data/factions.json when Supabase env vars are missing,
so local dev without a network still works.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import requests


DEFAULT_FACTIONS_FILE = Path("data/factions.json")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()


EMPTY_STATE = {
    "parrot_army": {"name": "Parrot Army", "members": []},
    "resistance": {"name": "The Resistance", "members": []},
    "defeated": [],
    "war_record": {},
}


def _supabase_headers(extra: dict | None = None) -> dict:
    h = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    if extra:
        h.update(extra)
    return h


def _supabase_load() -> dict | None:
    """Load factions state from Supabase. Returns None on error."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/factions_state?id=eq.1&select=data",
            headers=_supabase_headers(),
            timeout=8,
        )
        if r.status_code == 200:
            rows = r.json()
            if rows:
                data = rows[0].get("data")
                if isinstance(data, dict):
                    return data
            return None
        print(f"[FACTIONS] supabase load status={r.status_code} body={r.text[:200]}")
    except requests.RequestException as e:
        print(f"[FACTIONS] supabase load exception: {e}")
    return None


def _supabase_save(state: dict) -> bool:
    """Save factions state to Supabase. Returns True on success."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False
    try:
        # Upsert: PATCH if exists, POST if not. Use Prefer: resolution=merge-duplicates
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/factions_state",
            headers=_supabase_headers({
                "Prefer": "resolution=merge-duplicates,return=minimal",
            }),
            json={"id": 1, "data": state},
            timeout=8,
        )
        ok = r.status_code in (200, 201, 204)
        print(f"[FACTIONS] supabase save status={r.status_code} ok={ok}")
        return ok
    except requests.RequestException as e:
        print(f"[FACTIONS] supabase save exception: {e}")
        return False


class FactionTracker:
    def __init__(self, factions_file: Path | None = None) -> None:
        self.factions_file = Path(factions_file or DEFAULT_FACTIONS_FILE)
        self.data: dict = {}

        # Try Supabase first
        supa = _supabase_load()
        if supa is not None:
            self.data = supa
            print("[FACTIONS] loaded from Supabase")
            # Mirror to local file so local dev stays consistent
            self._save_local()
        else:
            self.load()
            print("[FACTIONS] loaded from JSON file")

    def load(self) -> None:
        if not self.factions_file.exists():
            self.data = dict(EMPTY_STATE)
            return
        try:
            with self.factions_file.open(encoding="utf-8") as f:
                self.data = json.load(f)
        except (OSError, json.JSONDecodeError):
            self.data = dict(EMPTY_STATE)

    def _save_local(self) -> None:
        try:
            self.factions_file.parent.mkdir(parents=True, exist_ok=True)
            with self.factions_file.open("w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except OSError as e:
            print(f"[FACTIONS] local save exception: {e}")

    def save(self) -> None:
        # Save to Supabase first, then local mirror
        supa_ok = _supabase_save(self.data)
        self._save_local()
        if not supa_ok:
            print("[FACTIONS] supabase save failed — local only")

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