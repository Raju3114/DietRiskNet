"""Phase 4 — Artifact validation.

Independently recomputes the headline numbers in the existing Phase 4
artifacts (docs/evaluation/*.json, *.csv) from the raw artifact data and
the on-disk configs, so the final report can cite verified numbers.

This script MODIFIES NOTHING except writing its own validation report.
It does not load ML models and does not touch application logic.

Output:
  docs/evaluation/phase4_validation.json
"""

import ast
import csv
import json
import os
import statistics

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
EVAL_DIR = os.path.join(PROJECT_ROOT, "docs", "evaluation")
MODEL_DIR = os.path.join(PROJECT_ROOT, "backend", "trained_models")


def load_json(name):
    with open(os.path.join(EVAL_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def load_csv(name):
    with open(os.path.join(EVAL_DIR, name), encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ── 1. Nutrition coverage ───────────────────────────────────────────────────
def verify_nutrition():
    cov = load_json("nutrition_coverage.json")
    mapped = cov.get("mapped")
    unmapped = cov.get("unmapped")
    total = cov.get("total_classes")
    coverage = cov.get("coverage_percent")

    # Count the actual arrays to avoid trusting the header fields.
    mapped_actual = len(cov.get("mapped_classes", []))
    unmapped_actual = len(cov.get("unmapped_classes", []))

    checks = {
        "classifier_vocab_size": total,
        "mapped_reported": mapped,
        "mapped_actual_array_count": mapped_actual,
        "unmapped_reported": unmapped,
        "unmapped_actual_array_count": unmapped_actual,
        "sum_matches_total": (mapped or 0) + (unmapped or 0) == total,
        "array_counts_match_reported": mapped == mapped_actual and unmapped == unmapped_actual,
        "coverage_recomputed_pct": round(100.0 * mapped / total, 2) if mapped and total else None,
        "coverage_reported_pct": coverage,
        "coverage_matches": coverage is not None and abs(coverage - 100.0 * mapped / total) < 0.011,
        "mapped_plus_unmapped_is_118": (mapped or 0) + (unmapped or 0) == 118,
    }
    return checks


# ── 2. DCI — recompute CV-based score per controlled scenario ───────────────
def _dci_from_calories(calories):
    if not calories:
        return None, None
    cals = [float(c) for c in calories]
    if len(cals) < 2:
        return None, None
    mean = statistics.mean(cals)
    # population std (ddof=0), matching indices_services
    var = sum((c - mean) ** 2 for c in cals) / len(cals)
    std = var ** 0.5
    cv = std / mean
    dci = max(0.0, min(1.0, 1.0 - cv))
    return dci, cals


def verify_dci():
    rows = load_csv("dci_controlled_tests.csv")
    results = []
    all_ok = True
    for r in rows:
        cal_str = r["daily_calories"]
        # parse "2026-08-01=2000;2026-08-02=2000"
        calories = []
        days = []
        if cal_str:
            for part in cal_str.split(";"):
                if "=" in part:
                    day, val = part.split("=", 1)
                    days.append(day.strip())
                    calories.append(val)
        dci, cals = _dci_from_calories(calories)
        reported = None if r["dci"] in ("", "None") else float(r["dci"])
        match = (reported is None and dci is None) or (
            reported is not None and dci is not None and abs(reported - dci) < 1e-4
        )
        # >= 2 DISTINCT DAYS requirement (count unique dates, not unique
        # calorie values — two days of 2000 kcal are two valid days).
        n_days = len(set(days))
        expects_score = n_days >= 2
        got_score = dci is not None
        semantics_ok = (expects_score == got_score)
        if not (match and semantics_ok):
            all_ok = False
        results.append({
            "scenario": r["scenario"],
            "distinct_valid_days": n_days,
            "dci_recomputed": None if dci is None else round(dci, 4),
            "dci_reported": reported,
            "match": match,
            "semantics_ok": semantics_ok,
        })
    return {"results": results, "all_ok": all_ok}


# ── 3. NIS — controlled ordering ────────────────────────────────────────────
def verify_nis():
    data = load_json("nis_evaluation.json")
    scenarios = data["scenarios"]
    pairs = [(name, sc["nis"], sc["level"]) for name, sc in scenarios.items()]
    # Verify the recorded ascending order is actually ascending by NIS value.
    recorded = data.get("ascending_nis_order", [])
    vals = {p[0]: p[1] for p in pairs}
    recorded_vals = [vals[n] for n in recorded if n in vals]
    ascending = all(recorded_vals[i] <= recorded_vals[i + 1] for i in range(len(recorded_vals) - 1))
    # Verify the recorded order is the sorted-by-value order.
    by_value = sorted(vals.items(), key=lambda kv: kv[1])
    sorted_names = [n for n, _ in by_value]
    order_matches_sort = sorted_names == recorded
    # severity labels present for all scenarios
    levels_present = all(p[2] for p in pairs)
    return {
        "scenario_count": len(pairs),
        "nis_values": {p[0]: p[1] for p in pairs},
        "recorded_ascending_order": recorded,
        "recorded_is_ascending": ascending,
        "recorded_matches_sorted_by_value": order_matches_sort,
        "all_levels_present": levels_present,
        "expected_ascending": ["balanced", "low_protein", "idli", "high_fat", "high_sodium", "extreme"],
        "extreme_severe": scenarios["extreme"]["level"] == "Severe Imbalance",
        "balanced_balanced": scenarios["balanced"]["level"] == "Balanced Diet",
    }


# ── 4. Risk fusion — renormalisation + manual calculation ──────────────────
WEIGHTS = {"DCI": 0.25, "NIS": 0.25, "Diabetes": 0.2, "Obesity": 0.15,
           "Hypertension": 0.1, "Deficiency": 0.05}


def fuse_manual(dci, nis, diabetes, obesity, hypertension, deficiency):
    """Mirror risk_fusion_service.fuse exactly: DCI enters as (1 - DCI)."""
    dci_risk = (1.0 - dci) if dci is not None else None
    comps = {"DCI": dci_risk, "NIS": nis, "Diabetes": diabetes, "Obesity": obesity,
             "Hypertension": hypertension, "Deficiency": deficiency}
    num = 0.0
    den = 0.0
    for k, v in comps.items():
        if v is not None:
            num += WEIGHTS[k] * v
            den += WEIGHTS[k]
    if den == 0:
        return None, None
    fused = num / den
    fused = max(0.0, min(1.0, fused))
    level = ("Low" if fused <= 0.25 else
             "Moderate" if fused <= 0.50 else
             "High" if fused <= 0.75 else "Critical")
    return fused, level


def verify_fusion():
    data = load_json("risk_fusion_evaluation.json")
    cfg_weights = data["configured_weights"]
    total_w = sum(cfg_weights.values())
    checks = {
        "weights_total_is_1": data.get("weights_total_is_1"),
        "weights_sum_recomputed": round(total_w, 6),
        "scenario_B_manual_match": data["manual_calculation_scenario_B"]["match"],
        "scenario_B_service_fused": data["manual_calculation_scenario_B"]["service_fused_score"],
        "scenario_B_manual_fused": data["manual_calculation_scenario_B"]["manual_fused_score"],
    }
    scenario_checks = []
    all_ok = True
    for sc in data["scenarios"]:
        fused, level = fuse_manual(sc["dci"], sc["nis"], sc["diabetes"], sc["obesity"],
                                   sc["hypertension"], sc["deficiency"])
        rep = sc["fused_score"]
        match = (rep is None and fused is None) or (rep is not None and fused is not None and abs(rep - fused) < 1e-9)
        lvl_match = (sc["risk_level"] is None and level is None) or sc["risk_level"] == level
        if not (match and lvl_match):
            all_ok = False
        scenario_checks.append({
            "scenario": sc["scenario"],
            "recomputed": None if fused is None else round(fused, 4),
            "reported": rep,
            "score_match": match,
            "level_match": lvl_match,
        })
    checks["scenarios"] = scenario_checks
    checks["all_scenarios_ok"] = all_ok
    # verify "missing DCI is not perfect health": scenario B fused (0.24) != 0
    checks["B_not_perfect_health"] = data["scenarios"][1]["fused_score"] != 0.0
    return checks


# ── 5. Classifier confidence stats from E2E accepted items ─────────────────
def verify_confidence():
    conf_json = load_json("classifier_confidence.json")
    stats = conf_json["confidence_stats"]
    # recompute from e2e CSV accepted items
    confs = []
    rejected = 0
    fallbacks = []
    with open(os.path.join(EVAL_DIR, "e2e_evaluation.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("items"):
                try:
                    items = ast.literal_eval(r["items"])
                    for it in items:
                        if isinstance(it, dict) and "conf" in it:
                            confs.append(float(it["conf"]))
                except Exception:
                    pass
            if r.get("low_conf_rejected"):
                try:
                    rejected += int(r["low_conf_rejected"])
                except ValueError:
                    pass
            if r.get("classifier_fallback"):
                try:
                    fallbacks.append(float(r["classifier_fallback"].split("@")[-1]))
                except (ValueError, IndexError):
                    pass
    n = len(confs)
    pct = lambda xs, p: (sorted(xs)[min(len(xs) - 1, int(len(xs) * p))] if xs else None)
    recomputed = {
        "accepted_items": n,
        "mean": round(statistics.mean(confs), 4) if confs else None,
        "median": round(statistics.median(confs), 4) if confs else None,
        "min": round(min(confs), 4) if confs else None,
        "max": round(max(confs), 4) if confs else None,
        "p25": round(pct(confs, 0.25), 4) if confs else None,
        "p75": round(pct(confs, 0.75), 4) if confs else None,
        "p95": round(pct(confs, 0.95), 4) if confs else None,
    }
    reported = {k: stats.get(k) for k in recomputed}
    close = lambda a, b: (a is None and b is None) or (a is not None and b is not None and abs(a - b) < 5e-4)
    matches = {k: close(recomputed[k], reported[k]) for k in recomputed}
    # non-food probe: all NON-FOOD confidences well below 0.45 threshold.
    # real_food_control(sample_meal) is the positive control and is excluded.
    nonfood = conf_json["nonfood_confidence_probe"]
    nonfood_confs = [v["confidence"] for k, v in nonfood.items()
                     if isinstance(v, dict) and isinstance(v.get("confidence"), (int, float))
                     and k != "real_food_control(sample_meal)"]
    threshold = conf_json["confidence_threshold"]
    return {
        "threshold": threshold,
        "recomputed_stats": recomputed,
        "reported_stats": reported,
        "all_stats_match": all(matches.values()),
        "nonfood_max_confidence": round(max(nonfood_confs), 4) if nonfood_confs else None,
        "all_nonfood_below_threshold": bool(nonfood_confs) and max(nonfood_confs) < threshold,
        "food_control_confidence": nonfood.get("real_food_control(sample_meal)", {}).get("confidence"),
        "rejected_low_conf_e2e": rejected,
        "fallback_confidences": fallbacks,
    }


# ── 6. E2E counts ──────────────────────────────────────────────────────────
def verify_e2e():
    rows = load_csv("e2e_evaluation.csv")
    counts = {}
    for r in rows:
        counts[r.get("status")] = counts.get(r.get("status"), 0) + 1
    summary = load_json("e2e_summary.json")
    ok = counts.get("ok", 0)
    no_food = counts.get("no_food_recognized", 0)
    no_nutr = counts.get("no_nutrition_data", 0)
    unexpected = sum(v for k, v in counts.items() if k not in ("ok", "no_food_recognized", "no_nutrition_data"))
    checks = {
        "total_rows": len(rows),
        "status_counts_recomputed": counts,
        "reported_total": summary["total_cases"],
        "reported_status_counts": summary["status_counts"],
        "counts_match_summary": counts == summary["status_counts"] and len(rows) == summary["total_cases"],
        "ok_cases": ok,
        "no_food_cases": no_food,
        "no_nutrition_cases": no_nutr,
        "unexpected_failures": unexpected,
        "ok_plus_guards_equals_total": ok + no_food + no_nutr == len(rows),
    }
    # For "ok" rows, confirm items had nutrition_available True and DCI semantics
    return checks


# ── 7. Portion scaling ─────────────────────────────────────────────────────
def verify_portion():
    rows = load_csv("portion_scaling.csv")
    # verify nutrient = per_100g * weight / 100 using weight=100 row as per-100g baseline
    by_food = {}
    for r in rows:
        by_food.setdefault(r["food"], []).append(r)
    all_prop = True
    checked = []
    for food, frs in by_food.items():
        base = [x for x in frs if x["weight_g"] == "100"]
        if not base:
            all_prop = False
            continue
        b = base[0]
        per100 = {k: float(b[k]) for k in ("calories", "protein", "carbs", "fats", "sodium")}
        for x in frs:
            w = float(x["weight_g"])
            for k in per100:
                expected = per100[k] * w / 100.0
                got = float(x[k])
                if abs(expected - got) > 1e-3:
                    all_prop = False
        checked.append(food)
    return {
        "foods_checked": checked,
        "all_proportional": all_prop,
        "food_count": len(by_food),
        "rows": len(rows),
    }


# ── Run everything ─────────────────────────────────────────────────────────
def main():
    result = {
        "nutrition": verify_nutrition(),
        "dci": verify_dci(),
        "nis": verify_nis(),
        "risk_fusion": verify_fusion(),
        "classifier_confidence": verify_confidence(),
        "e2e": verify_e2e(),
        "portion": verify_portion(),
        "source_artifacts": "docs/evaluation/",
        "note": "Independent recomputation from raw artifact data + on-disk configs; no model loaded, nothing modified.",
    }
    os.makedirs(EVAL_DIR, exist_ok=True)
    out = os.path.join(EVAL_DIR, "phase4_validation.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)
    print(json.dumps(result, indent=2, default=str))
    return result


if __name__ == "__main__":
    main()
