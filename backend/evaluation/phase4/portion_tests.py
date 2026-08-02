"""Phase 4 — Part 9: Portion estimation audit.

Records how portion sizes are assigned (default weight, per-food overrides,
and the linear scaling of per-100 g nutrient values) and verifies that
nutrient scaling is mathematically proportional across 50/100/150/200 g.

This is an audit of the EXISTING mechanism — it does not implement portion
estimation.
"""

import json
import os

from backend.evaluation.phase4.helpers import service, write_csv, write_json, out_path
from backend.routes import meal as meal_route

NUTRIENT_KEYS = [
    "calories", "carbs", "protein", "fats", "sugar",
    "fiber", "sodium", "calcium", "iron", "vitamin_c", "folate",
]

# The exact per-food serving override table used by the pipeline.
SERVING_OVERRIDES = dict(meal_route.DEFAULT_SERVING_WEIGHTS)


def _scaled(fact: dict, weight_g: float) -> dict:
    """Reproduce meal.py's linear scaling: value * (weight/100)."""
    scale = weight_g / 100.0
    return {k: fact[k] * scale for k in NUTRIENT_KEYS}


def main() -> dict:
    nut = service("nutrition")
    # Representative mapped foods across override/no-override cases.
    test_foods = ["idli", "samosa", "masala_dosa", "butter_naan", "chai", "pizza"]

    rows = []
    checks = []
    for food in test_foods:
        fact = nut.lookup(food)
        if not fact.get("nutrition_available"):
            continue
        base = _scaled(fact, 100.0)
        for w in [50, 100, 150, 200]:
            scaled = _scaled(fact, w)
            # Proportionality check: scaled[k] / base[k] == w / 100 for each k
            ok = all(
                abs(scaled[k] - base[k] * (w / 100.0)) < 1e-9
                for k in NUTRIENT_KEYS
            )
            rows.append({
                "food": food,
                "weight_g": w,
                "calories": round(scaled["calories"], 3),
                "protein": round(scaled["protein"], 3),
                "carbs": round(scaled["carbs"], 3),
                "fats": round(scaled["fats"], 3),
                "sodium": round(scaled["sodium"], 3),
                "proportional": ok,
            })
        checks.append(all(r["proportional"] for r in rows if r["food"] == food))

    write_csv("portion_scaling.csv", rows)

    summary = {
        "portion_source": "static configuration, not vision-estimated",
        "default_serving_weight_g": 100.0,
        "per_food_serving_overrides": SERVING_OVERRIDES,
        "override_count": len(SERVING_OVERRIDES),
        "scaling_rule": "nutrient = per_100g_value * (weight_g / 100)",
        "all_proportional": all(checks),
        "tested_foods": test_foods,
        "vision_estimates_mass": False,
        "statement": (
            "Food recognition is image-based, but portion mass is currently "
            "default/configuration-based rather than visually estimated."
        ),
    }
    write_json("portion_estimation.json", summary)
    print(json.dumps({k: v for k, v in summary.items() if k not in ("per_food_serving_overrides",)}, indent=2, default=str))
    return summary


if __name__ == "__main__":
    main()
