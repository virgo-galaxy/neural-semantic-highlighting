"""Size-aware assignment of intact source groups before any training windows."""
from __future__ import annotations

import hashlib
from typing import Mapping

SPLITS = ("train", "validation", "test")
RATIOS = (0.8, 0.1, 0.1)


def assign_groups(weights: Mapping[str, int], seed: int) -> dict[str, str]:
    """Deterministic largest-first allocation plus local balancing.

    Weights are character-safe fixed-window counts, independent of Gold cuts.
    A module/subsystem is never split to hit a target. Near-copy exclusions are
    resolved before this function; each input key is an independent source group.
    """
    if not weights:
        return {}
    if any(type(weight) is not int or weight <= 0 for weight in weights.values()):
        raise ValueError("Source group weights must be positive integers")
    if len(weights) < 3:
        raise ValueError("Natural evaluation needs at least three independent source groups")
    total = sum(weights.values())
    targets = [total * ratio for ratio in RATIOS]
    loads = [0, 0, 0]
    counts = [0, 0, 0]
    tie = lambda group: hashlib.sha256(f"{seed}:{group}".encode()).hexdigest()
    ordered = sorted(weights, key=lambda group: (-weights[group], tie(group)))
    assignments = {}
    for offset, group in enumerate(ordered):
        weight = weights[group]
        empty = [i for i in range(3) if counts[i] == 0]
        remaining = len(ordered) - offset
        candidates = empty if len(empty) == remaining else range(3)
        # The loss change is weighted by each target size; this avoids assigning
        # a large indivisible module to a small holdout just to fill a document quota.
        best = min(candidates, key=lambda i: (
            ((loads[i] + weight - targets[i]) ** 2 - (loads[i] - targets[i]) ** 2) / targets[i], i))
        assignments[group] = best
        loads[best] += weight
        counts[best] += 1
    # Reassign only complete groups and only when the weighted error decreases.
    # The bound keeps runtime predictable on large inventories.
    for _ in range(32):
        changed = False
        for group in ordered:
            old, weight = assignments[group], weights[group]
            if counts[old] <= 1:
                continue
            best, best_delta = old, -1e-9
            for new in range(3):
                if new == old:
                    continue
                delta = (((loads[old] - weight - targets[old]) ** 2 - (loads[old] - targets[old]) ** 2) / targets[old]
                         + ((loads[new] + weight - targets[new]) ** 2 - (loads[new] - targets[new]) ** 2) / targets[new])
                if delta < best_delta:
                    best, best_delta = new, delta
            if best != old:
                loads[old] -= weight
                loads[best] += weight
                counts[old] -= 1
                counts[best] += 1
                assignments[group] = best
                changed = True
        if not changed:
            break
    return {group: SPLITS[index] for group, index in assignments.items()}


def natural_balance(window_counts: Mapping[str, int]) -> dict:
    """Reject unusable natural holdouts instead of counting focused cases as coverage."""
    total = sum(window_counts.values())
    if not total:
        return {"applicable": False, "reason": "no-natural-documents"}
    actual = {split: window_counts[split] / total for split in SPLITS}
    bounds = {"train": [0.70, 0.90], "validation": [0.05, 0.20], "test": [0.05, 0.20]}
    passed = all(lo <= actual[split] <= hi for split, (lo, hi) in bounds.items())
    result = {"applicable": True, "passed": passed, "metric": "naturalWindows", "ratios": actual,
              "bounds": bounds, "targetRatios": dict(zip(SPLITS, RATIOS))}
    if not passed:
        detail = ", ".join(f"{split}={actual[split]:.1%}" for split in SPLITS)
        raise ValueError(f"Natural split balance gate failed ({detail}); keep groups intact and review the source group weights; no snapshot published")
    return result
