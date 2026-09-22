"""
PARROT-AI reflection mode.

Generates an after-action report from the current session's brain state.
Triggered by /reflect.
"""
from __future__ import annotations

from datetime import datetime, timezone

from parrot_ai.roasts import ALL_ARMS


def build_reflection(brain, session_stats: dict) -> str:
    lines = []
    lines.append("REFLECTION — session report")
    lines.append("=" * 50)
    lines.append(f"Time: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    lines.append(f"Rounds: {session_stats.get('turns', 0)}")
    lines.append(f"Roasts fired: {session_stats.get('spam_sent', 0)}")
    lines.append(f"Silence fires: {session_stats.get('silence_count', 0)}")
    lines.append("")

    ranked = sorted(
        ALL_ARMS,
        key=lambda c: (
            brain.alpha[c] / (brain.alpha[c] + brain.beta[c])
            if (brain.alpha[c] + brain.beta[c]) > 0 else 0.5
        ),
        reverse=True,
    )

    lines.append("WHAT WORKED:")
    top = [c for c in ranked if brain.plays[c] > 0][:3]
    if not top:
        lines.append("  (nothing played yet)")
    else:
        for cat in top:
            a, b = brain.alpha[cat], brain.beta[cat]
            mean = a / (a + b) if (a + b) > 0 else 0.5
            lines.append(
                f"  {cat}: E[p]={mean:.2f}, plays={brain.plays[cat]}, "
                f"+{brain.successes[cat]} -{brain.failures[cat]}"
            )
    lines.append("")

    lines.append("WHAT DIDN'T WORK:")
    bottom = [c for c in ranked if brain.plays[c] >= 2][-3:]
    if not bottom:
        lines.append("  (not enough data)")
    else:
        for cat in bottom:
            a, b = brain.alpha[cat], brain.beta[cat]
            mean = a / (a + b) if (a + b) > 0 else 0.5
            lines.append(
                f"  {cat}: E[p]={mean:.2f}, plays={brain.plays[cat]}, "
                f"+{brain.successes[cat]} -{brain.failures[cat]}"
            )
    lines.append("")

    never_fired = [c for c in ALL_ARMS if brain.plays[c] == 0]
    if never_fired:
        lines.append(f"NEVER FIRED ({len(never_fired)}):")
        lines.append(f"  {', '.join(never_fired)}")
        lines.append("")

    if hasattr(brain, "combos_fired") and brain.combos_fired > 0:
        lines.append(f"COMBOS FIRED: {brain.combos_fired}")
        if hasattr(brain, "combos"):
            for combo, count in sorted(brain.combos.items(), key=lambda x: -x[1]):
                lines.append(f"  {combo}: {count}")
        lines.append("")

    lines.append("SUMMARY:")
    lines.append(f"  Total turns learned: {brain.total_turns}")
    lines.append(f"  Baseline signal: {brain.baseline_signal:+.2f}")
    lines.append("")

    return "\n".join(lines)