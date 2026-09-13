"""Validation quality gates for Go model selection and focused capabilities."""
from __future__ import annotations

TARGET_F1 = 0.90
MIN_ROLE_SUPPORT = 32

# Canonical focused capabilities that must generalize before a checkpoint can
# become the selected Go model. Whole-document string quality is already covered
# by the natural-role gate; pathological literals longer than the 512-byte context
# remain diagnostics rather than a hard model-selection target.
TARGETED_ROLES = {
    "self-reference": "interface",
    "function-range": "method",
    "generic-method": "method",
    "generic-alias": "type-parameter",
    "struct-tags": "string",
}

MIN_NATURAL_EXACT_F1 = 0.95
MIN_NATURAL_MACRO_F1 = 0.90
MIN_FOCUS_EXACT_F1 = 0.98


def targeted_scores(report: dict, *, roles: dict[str, str] | None = None,
                    minimum_support: int = MIN_ROLE_SUPPORT) -> list[dict]:
    features = report.get("focusFeatures", {})
    rows = []
    for feature, role in (roles or TARGETED_ROLES).items():
        metrics = features.get(feature, {}).get("byTokenType", {}).get(role)
        if not metrics:
            rows.append({"feature": feature, "role": role, "support": 0, "f1": None, "passed": False})
            continue
        support = int(metrics.get("support", 0))
        f1 = float(metrics.get("f1", 0.0))
        rows.append({"feature": feature, "role": role, "support": support, "f1": f1,
                     "passed": support >= minimum_support and f1 >= TARGET_F1})
    return rows


def targeted_gate_passed(report: dict, *, roles: dict[str, str] | None = None) -> bool:
    rows = targeted_scores(report, roles=roles)
    return bool(rows) and all(row["passed"] for row in rows)


def targeted_gate_summary(report: dict, *, roles: dict[str, str] | None = None) -> dict:
    rows = targeted_scores(report, roles=roles)
    return {"threshold": TARGET_F1, "minimumSupport": MIN_ROLE_SUPPORT,
            "passed": bool(rows) and all(row["passed"] for row in rows), "roles": rows}


def natural_role_scores(report: dict, *, minimum_support: int = MIN_ROLE_SUPPORT) -> list[dict]:
    roles = report.get("streams", {}).get("natural", {}).get("byTokenType", {})
    rows = []
    for role, metrics in roles.items():
        support = int(metrics.get("support", 0))
        f1 = float(metrics.get("f1", 0.0))
        status = "LOW_SUPPORT" if support < minimum_support else ("PASS" if f1 >= TARGET_F1 else "FAIL")
        rows.append({"role": role, "support": support, "f1": f1, "status": status})
    return rows


def natural_role_gate_summary(report: dict) -> dict:
    rows = natural_role_scores(report)
    checked = [row for row in rows if row["status"] != "LOW_SUPPORT"]
    return {"threshold": TARGET_F1, "minimumSupport": MIN_ROLE_SUPPORT,
            "passed": bool(checked) and all(row["status"] == "PASS" for row in checked),
            "roles": rows}


def quality_gate_summary(report: dict) -> dict:
    natural = report.get("streams", {}).get("natural", {})
    focus = report.get("streams", {}).get("focus", {})
    aggregate = {
        "naturalExactSpanF1": {"minimum": MIN_NATURAL_EXACT_F1,
                               "value": float(natural.get("exactSpan", {}).get("f1", 0.0))},
        "naturalMacroF1": {"minimum": MIN_NATURAL_MACRO_F1,
                            "value": float(natural.get("exactSpanMacroF1", 0.0))},
        "focusExactSpanF1": {"minimum": MIN_FOCUS_EXACT_F1,
                              "value": float(focus.get("exactSpan", {}).get("f1", 0.0))},
    }
    natural_roles = natural_role_gate_summary(report)
    targeted = targeted_gate_summary(report)
    aggregate_passed = all(row["value"] >= row["minimum"] for row in aggregate.values())
    return {"passed": aggregate_passed and natural_roles["passed"] and targeted["passed"],
            "aggregate": aggregate, "naturalRoleGate": natural_roles, "targetedRoleGate": targeted}
