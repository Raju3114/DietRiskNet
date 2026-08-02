"""Deterministic health-score computation.

The health score is a weighted, explainable heuristic built from the
existing ML-produced metrics.  It NEVER consults an LLM — the AI
Dietitian only receives the final score to explain to the user.

Component caps (maximum total penalty = 100):
  fusion penalty    up to 30   (weighted disease risk)
  NIS penalty       up to 20   (nutrient imbalance)
  DCI penalty       up to 10   (consistency below 0.70)
  calories penalty  up to 10   (> 800 kcal in a single meal)
  sodium penalty    up to 10   (> 800 mg in a single meal)
  sugar penalty     up to 10   (> 15 g free sugar)
  fiber penalty     up to 10   (< 2 g dietary fiber)

Returns ``{score, level, explanation}`` so the UI can display both the
number and a human-readable reason without calling the LLM.
"""

from __future__ import annotations

from typing import Dict

# Level thresholds (inclusive lower bound).
_LEVELS = (
    (90, "Excellent"),
    (75, "Good"),
    (50, "Moderate"),
    (0, "Needs improvement"),
)


def _level_for(score: int) -> str:
    for threshold, label in _LEVELS:
        if score >= threshold:
            return label
    return _LEVELS[-1][1]


def compute_health_score(
    *,
    dci: float,
    nis: float,
    fusion_score: float,
    nutrition: Dict[str, float],
) -> Dict[str, object]:
    """Compute a deterministic health score in ``[0, 100]``.

    Parameters
    ----------
    dci : float
        Dietary Consistency Index (0-1, higher is better).
    nis : float
        Nutritional Imbalance Score (0+, lower is better).
    fusion_score : float
        Weighted fused risk score (0-1, lower is better).
    nutrition : dict
        Aggregated meal nutrients, at minimum containing
        ``calories``, ``sodium``, ``sugar``, and ``fiber``.
    """
    score = 100.0
    reasons: list[str] = []

    # Fusion risk (0-1) — primary risk component, up to 30 points.
    fusion_pen = min(max(float(fusion_score or 0.0), 0.0), 1.0) * 30.0
    if fusion_pen > 0:
        reasons.append(f"Fused risk {fusion_score:.2f} ({-fusion_pen:.0f} pts)")
    score -= fusion_pen

    # NIS (0-1 interpreted) — imbalance beyond what fusion already weights.
    nis_pen = min(max(float(nis or 0.0), 0.0), 1.0) * 20.0
    if nis_pen > 0:
        reasons.append(f"NIS {nis:.2f} imbalance ({-nis_pen:.0f} pts)")
    score -= nis_pen

    # DCI — extra penalty only below the 0.70 consistency threshold.
    if dci < 0.70:
        dci_pen = (0.70 - float(dci)) * 10.0
        reasons.append(f"DCI {dci:.2f} below 0.70 ({-dci_pen:.0f} pts)")
        score -= dci_pen

    # Single-meal calorie density (> 800 kcal).
    calories = float(nutrition.get("calories", 0.0) or 0.0)
    if calories > 800:
        cal_pen = min((calories - 800) / 800.0, 1.0) * 10.0
        reasons.append(f"Calories {calories:.0f} kcal ({-cal_pen:.0f} pts)")
        score -= cal_pen

    # Sodium (> 800 mg).
    sodium = float(nutrition.get("sodium", 0.0) or 0.0)
    if sodium > 800:
        sodium_pen = min((sodium - 800) / 1500.0, 1.0) * 10.0
        reasons.append(f"Sodium {sodium:.0f} mg ({-sodium_pen:.0f} pts)")
        score -= sodium_pen

    # Free sugar (> 15 g).
    sugar = float(nutrition.get("sugar", 0.0) or 0.0)
    if sugar > 15:
        sugar_pen = min((sugar - 15) / 35.0, 1.0) * 10.0
        reasons.append(f"Sugar {sugar:.0f} g ({-sugar_pen:.0f} pts)")
        score -= sugar_pen

    # Fiber (< 2 g).
    fiber = float(nutrition.get("fiber", 0.0) or 0.0)
    if fiber < 2.0:
        fiber_pen = min((2.0 - fiber) / 2.0, 1.0) * 10.0
        reasons.append(f"Fiber {fiber:.1f} g ({-fiber_pen:.0f} pts)")
        score -= fiber_pen

    final_score = int(round(max(0.0, min(100.0, score))))
    level = _level_for(final_score)

    if not reasons:
        explanation = "No major nutritional or risk concerns detected."
    else:
        explanation = "Score reduced for: " + "; ".join(reasons) + "."

    return {
        "score": final_score,
        "level": level,
        "explanation": explanation,
    }
