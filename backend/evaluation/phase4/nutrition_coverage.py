"""Phase 4 — Part 8: Classifier-to-nutrition coverage audit.

For every one of the 118 classifier classes, run the SAME lookup the real
pipeline uses (NutritionService.lookup) and record whether nutrition was
resolved and by which priority.  Pure function — no model loading.
"""

import json
import os

from backend.evaluation.phase4.helpers import service, write_csv, write_json, out_path

# Priority labels mirror nutrition_service.lookup priorities.
# We detect them by checking the resolved record's name and availability flag.
PRIORITY_HINTS = {
    "priority1_exact": "exact",
    "priority2_alias": "synonym/alias",
    "priority3_normalized": "normalized",
    "priority4_fuzzy": "fuzzy",
    "unresolved": "unresolved",
}


def _classify_priority(cls: str, result: dict) -> str:
    # Re-implement the four lookup stages without running them twice: we call
    # lookup() once and classify by matching against the returned record.
    nut = service("nutrition")
    if not result.get("nutrition_available"):
        return "unresolved"
    resolved_name = result["name"]
    # Exact
    if resolved_name in nut.nutrition_db:
        if resolved_name == cls:
            return "priority1_exact"
    # Alias
    from backend.services.nutrition_service import SYNONYM_MAP
    alias = SYNONYM_MAP.get(cls)
    if alias and alias in nut.nutrition_db and resolved_name == alias:
        return "priority2_alias"
    # Normalized
    norm = nut._normalize_name(cls)
    if norm in nut.normalized_db and resolved_name == nut.normalized_db[norm]["name"]:
        return "priority3_normalized"
    return "priority4_fuzzy"


def main() -> dict:
    nut = service("nutrition")
    classes_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "trained_models", "efficientnet_classes.json"
    )
    with open(classes_path, encoding="utf-8") as f:
        classes = json.load(f)

    rows = []
    for cls in sorted(classes):
        result = nut.lookup(cls)
        priority = _classify_priority(cls, result)
        rows.append({
            "class": cls,
            "mapped": str(result.get("nutrition_available", False)),
            "priority": priority,
            "resolved_dish": result.get("name", ""),
        })

    mapped = [r for r in rows if r["mapped"] == "True"]
    unmapped = [r for r in rows if r["mapped"] == "False"]
    coverage = round(len(mapped) / len(rows) * 100.0, 2) if rows else 0.0

    write_csv("nutrition_coverage.csv", rows)
    summary = {
        "total_classes": len(rows),
        "mapped": len(mapped),
        "unmapped": len(unmapped),
        "coverage_percent": coverage,
        "mapped_classes": [r["class"] for r in mapped],
        "unmapped_classes": [r["class"] for r in unmapped],
        "priority_breakdown": {
            p: sum(1 for r in rows if r["priority"] == p)
            for p in ["priority1_exact", "priority2_alias", "priority3_normalized", "priority4_fuzzy", "unresolved"]
        },
    }
    write_json("nutrition_coverage.json", summary)
    print(f"Total: {summary['total_classes']}  Mapped: {summary['mapped']}  "
          f"Unmapped: {summary['unmapped']}  Coverage: {coverage}%")
    print("Unmapped:", ", ".join(summary["unmapped_classes"]))
    return summary


if __name__ == "__main__":
    main()
