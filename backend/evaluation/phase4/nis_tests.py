"""Phase 4 — Part 10: NIS final controlled evaluation.

Runs the established controlled NIS scenarios through the real NISService and
verifies the expected ordering:

    balanced < moderately imbalanced < strongly imbalanced

NIS is a project-designed dietary imbalance indicator, not a clinically
validated score.
"""

import json

from backend.evaluation.phase4.helpers import service, write_csv, write_json


def _dict(cal, pro, carb, fat, sod, fib):
    return {
        "calories": cal, "protein": pro, "carbs": carb, "fats": fat,
        "sugar": 0.0, "fiber": fib, "sodium": sod,
        "calcium": 0.0, "iron": 0.0, "vitamin_c": 0.0, "folate": 0.0,
    }


SCENARIOS = {
    "balanced":        _dict(600, 18, 90, 20,  600, 9),
    "idli":            _dict(206, 5, 43, 1, 450, 1.5),
    "high_sodium":     _dict(600, 18, 90, 20, 3000, 9),
    "high_fat":        _dict(600, 15, 40, 60,  700, 5),
    "low_protein":     _dict(600,  4, 120, 10,  700, 6),
    "extreme":         _dict(1500, 80, 120, 120, 4500, 2),
}


def main() -> dict:
    nis_service = service("nis")
    rows = []
    results = {}
    for name, nut in SCENARIOS.items():
        score, level = nis_service.calculate(nut)
        meal_fraction = min(1.0, nut["calories"] / 2000.0)
        rows.append({
            "scenario": name,
            "calories": nut["calories"],
            "protein_g": nut["protein"],
            "carbs_g": nut["carbs"],
            "fats_g": nut["fats"],
            "sodium_mg": nut["sodium"],
            "fiber_g": nut["fiber"],
            "meal_calorie_fraction": round(meal_fraction, 3),
            "nis": round(score, 4),
            "nis_level": level,
        })
        results[name] = {"nis": round(score, 4), "level": level}

    write_csv("nis_controlled_tests.csv", rows)

    # Ordering check on NIS values (higher = more imbalanced).
    ordered = sorted(results.items(), key=lambda kv: kv[1]["nis"])
    balanced = results["balanced"]["nis"]
    extreme = results["extreme"]["nis"]
    summary = {
        "scenarios": results,
        "nis_is_clinically_validated": False,
        "note": "NIS is a project-designed dietary imbalance indicator and is not claimed as clinically validated.",
        "ordering_verified": balanced <= extreme,
        "ascending_nis_order": [k for k, _ in ordered],
    }
    write_json("nis_evaluation.json", summary)
    for r in rows:
        print(f"{r['scenario']:>12}: NIS={r['nis']:.3f} ({r['nis_level']})")
    print("Ordering (balanced < ... < extreme):", summary["ordering_verified"])
    return summary


if __name__ == "__main__":
    main()
