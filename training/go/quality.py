"""Acceptance-oriented role gates for focused Go capabilities."""
from __future__ import annotations

TARGET_F1 = 0.90
TARGETED_ROLES = {
    "self-reference": "interface",
    "function-range": "method",
    "generic-method": "method",
    "generic-alias": "type-parameter",
    "struct-tags": "string",
}


def targeted_scores(report: dict) -> list[dict]:
    features = report.get("focusFeatures", {})
    rows = []
    for feature, role in TARGETED_ROLES.items():
        metrics = features.get(feature, {}).get("byTokenType", {}).get(role)
        if not metrics:
            rows.append({"feature": feature, "role": role, "support": 0, "f1": None, "passed": False})
            continue
        support = int(metrics.get("support", 0))
        f1 = float(metrics.get("f1", 0.0))
        rows.append({"feature": feature, "role": role, "support": support, "f1": f1,
                     "passed": support > 0 and f1 >= TARGET_F1})
    return rows


def targeted_gate_passed(report: dict) -> bool:
    rows = targeted_scores(report)
    return bool(rows) and all(row["passed"] for row in rows)


def targeted_gate_summary(report: dict) -> dict:
    rows = targeted_scores(report)
    return {"threshold": TARGET_F1, "passed": bool(rows) and all(row["passed"] for row in rows), "roles": rows}
