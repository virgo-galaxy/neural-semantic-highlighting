"""Plain-text training reports; formatting never changes metric selection or data."""
from __future__ import annotations

from collections.abc import Mapping



def duration(seconds: float) -> str:
    minutes, seconds = divmod(max(0, int(seconds)), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def training_line(main: int, main_total: int, focus: int, focus_total: int,
                  losses: Mapping[str, float], windows: int, elapsed: float) -> str:
    completed, total = main + focus, main_total + focus_total
    eta = elapsed / max(1, completed) * (total - completed)
    rate = windows / max(elapsed, 1e-9)
    return (f"  main {main:>4}/{main_total} focus {focus:>3}/{focus_total} "
            f"loss={losses['total']:.4f} boundary_loss={losses['boundary']:.4f} "
            f"type_loss={losses['token_type']:.4f} modifier_loss={losses['modifier']:.4f} "
            f"{rate:.1f} win/s ETA={duration(eta)}")


def validation_line(split: str, step: int, total: int, windows: int, elapsed: float) -> str:
    eta = elapsed / max(1, step) * (total - step)
    return (f"  {split} {step:>4}/{total} batches "
            f"{windows / max(elapsed, 1e-9):.1f} win/s "
            f"elapsed={duration(elapsed)} ETA={duration(eta)}")

