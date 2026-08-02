"""Deterministic nutrition analytics for the personalized AI Nutrition Coach.

Computes a weekly/dietary summary and behaviour patterns from PERSISTED
meal analyses.  It NEVER re-runs YOLO, EfficientNet, nutrition, DCI,
NIS, or disease prediction — it only aggregates existing database rows.

The output powers:
- the frontend dashboard (average calories / protein / DCI / NIS, meals
  this week, risk trend, progress indicators)
- the coach chat context (patterns like "high sodium in 4 of last 5
  meals") so Gemini can personalise its advice
"""

from __future__ import annotations

import statistics
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.database.models import Meal

# Analysis window (number of most recent meals to consider).
RECENT_MEALS_LIMIT = 14
# Sodium considered "high" in a single meal (mg).
HIGH_SODIUM_MG = 800.0
# Protein considered "low" in a single meal (g).
LOW_PROTEIN_G = 15.0
# Fiber target per meal (g).
FIBER_TARGET_G = 3.0
# Risk considered "elevated".
RISK_THRESHOLD = 0.4

_RISK_KEYS = (
    ("diabetes_risk", "diabetes"),
    ("obesity_risk", "obesity"),
    ("hypertension_risk", "hypertension"),
    ("deficiency_risk", "deficiency"),
)


class NutritionAnalyticsService:
    """Aggregates stored meal data into a personalised nutrition summary."""

    def compute_analytics(self, db: Session, user_id: int) -> Dict[str, Any]:
        meals = self._recent_meals(db, user_id, RECENT_MEALS_LIMIT)
        return self._build_analytics(meals)

    # ------------------------------------------------------------------
    # Public helpers (usable by the assistant / dashboard)
    # ------------------------------------------------------------------

    @staticmethod
    def summary_for_context(analytics: Dict[str, Any]) -> str:
        """Render a compact, plain-text coach summary for the chat prompt."""
        if not analytics or analytics.get("meals_analyzed", 0) == 0:
            return "The user has no analysed meals yet."

        dci_display = (
            f"{analytics['avg_dci']:.2f}"
            if analytics.get("avg_dci") is not None
            else "not available (insufficient data)"
        )
        lines = [
            f"The user has analysed {analytics['meals_analyzed']} meals "
            f"({analytics['meals_this_week']} in the last 7 days).",
            f"Average per meal: {analytics['avg_calories']:.0f} kcal, "
            f"{analytics['avg_protein']:.0f} g protein, "
            f"{analytics['avg_carbs']:.0f} g carbs, "
            f"{analytics['avg_fats']:.0f} g fat.",
            f"Average DCI: {dci_display}; "
            f"average NIS: {analytics['avg_nis']:.2f}.",
        ]

        if analytics.get("highest_risk"):
            hr = analytics["highest_risk"]
            lines.append(
                f"Highest predicted risk: {hr['name']} at "
                f"{hr['value'] * 100:.0f}%."
            )

        for pattern in analytics.get("patterns", []):
            lines.append(f"- {pattern}")

        for habit in analytics.get("positive_habits", []):
            lines.append(f"Positive: {habit}")

        for habit in analytics.get("habits_to_improve", []):
            lines.append(f"To improve: {habit}")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _recent_meals(db: Session, user_id: int, limit: int) -> List[Meal]:
        return (
            db.query(Meal)
            .filter(Meal.user_id == user_id)
            .order_by(Meal.created_at.desc())
            .limit(limit)
            .all()
        )

    def _build_analytics(self, meals: List[Meal]) -> Dict[str, Any]:
        if not meals:
            return self._empty()

        # Most-recent-first; reorder to chronological for trends.
        meals_chrono = list(reversed(meals))

        valid = [m for m in meals_chrono if m.nutrition is not None]
        nutrition = [m.nutrition for m in valid]

        avg = lambda key: statistics.fmean(
            [getattr(n, key, 0.0) for n in nutrition]
        ) if nutrition else 0.0

        dcis = [m.dci for m in meals_chrono if m.dci is not None]
        nises = [m.nis for m in meals_chrono if m.nis is not None]

        # A genuine DCI can never be 0.0 (DCI = 1 - CV, and with valid
        # positive daily intakes CV < 1), so treating "no DCI measured" as
        # NULL — rather than a numeric 0.0 — is unambiguous and lets the
        # API expose availability explicitly.
        avg_dci = statistics.fmean(dcis) if dcis else None
        avg_nis = statistics.fmean(nises) if nises else 0.0

        # Highest predicted risk across recent meals.
        highest_risk = self._highest_risk(meals_chrono)

        # Best / worst meal.
        best_meal = self._best_meal(meals_chrono)
        worst_meal = self._worst_meal(meals_chrono)

        # Most common food.
        most_common = self._most_common_food(meals_chrono)

        # Patterns + habits.
        patterns = self._detect_patterns(meals_chrono, nutrition)
        positive_habits = self._positive_habits(meals_chrono, avg_dci, avg_nis)
        habits_to_improve = self._habits_to_improve(patterns, avg_dci, avg_nis)

        # Trends (compare first half vs second half of the window).
        dci_trend = self._dci_trend(meals_chrono)
        risk_trend = self._risk_trend(meals_chrono)

        # Goals + progress.
        goals = self._goals(meals_chrono, nutrition, avg_dci, avg_nis)

        week_start = datetime.utcnow().replace(tzinfo=None) - timedelta(days=7)
        meals_this_week = sum(
            1 for m in meals_chrono
            if m.created_at is not None and m.created_at >= week_start
        )

        return {
            "meals_analyzed": len(meals_chrono),
            "meals_this_week": meals_this_week,
            "avg_calories": round(avg("calories"), 1),
            "avg_protein": round(avg("protein"), 1),
            "avg_carbs": round(avg("carbs"), 1),
            "avg_fats": round(avg("fats"), 1),
            "avg_sodium": round(avg("sodium"), 1),
            "avg_fiber": round(avg("fiber"), 1),
            "avg_dci": round(avg_dci, 2) if avg_dci is not None else None,
            "avg_nis": round(avg_nis, 2),
            "highest_risk": highest_risk,
            "best_meal": best_meal,
            "meal_needing_improvement": worst_meal,
            "most_common_food": most_common,
            "patterns": patterns,
            "positive_habits": positive_habits,
            "habits_to_improve": habits_to_improve,
            "dci_trend": dci_trend,
            "risk_trend": risk_trend,
            "goals": goals,
            "nutrient_deficiencies": self._deficiencies(avg("protein"), avg("fiber")),
        }

    @staticmethod
    def _empty() -> Dict[str, Any]:
        return {
            "meals_analyzed": 0,
            "meals_this_week": 0,
            "avg_calories": 0.0, "avg_protein": 0.0,
            "avg_carbs": 0.0, "avg_fats": 0.0,
            "avg_sodium": 0.0, "avg_fiber": 0.0,
            "avg_dci": None, "avg_nis": 0.0,
            "highest_risk": None, "best_meal": None,
            "meal_needing_improvement": None, "most_common_food": None,
            "patterns": [], "positive_habits": [],
            "habits_to_improve": [], "dci_trend": None,
            "risk_trend": None, "goals": [],
            "nutrient_deficiencies": [],
        }

    # ------------------------------------------------------------------
    @staticmethod
    def _highest_risk(meals: List[Meal]) -> Optional[Dict[str, Any]]:
        best = None
        for m in meals:
            if m.predictions is None:
                continue
            for key, name in _RISK_KEYS:
                value = getattr(m.predictions, key)
                if value is not None and (best is None or value > best["value"]):
                    best = {"name": name, "value": round(float(value), 4)}
        return best

    @staticmethod
    def _best_meal(meals: List[Meal]) -> Optional[Dict[str, Any]]:
        candidates = [m for m in meals if m.dci is not None]
        if not candidates:
            return None
        best = max(candidates, key=lambda m: m.dci)
        return {
            "date": best.created_at.strftime("%Y-%m-%d") if best.created_at else None,
            "dci": best.dci,
        }

    @staticmethod
    def _worst_meal(meals: List[Meal]) -> Optional[Dict[str, Any]]:
        candidates = [m for m in meals if m.nis is not None]
        if not candidates:
            return None
        worst = max(candidates, key=lambda m: m.nis)
        return {
            "date": worst.created_at.strftime("%Y-%m-%d") if worst.created_at else None,
            "nis": worst.nis,
        }

    @staticmethod
    def _most_common_food(meals: List[Meal]) -> Optional[str]:
        # Count case-insensitively (so "Pav Bhaji", "pav_bhaji", "pav bhaji"
        # are NOT treated as three separate foods), but return a canonical
        # label for display.  Classifier labels / nutrition mappings are not
        # altered — this only normalizes how names are grouped for counting.
        counter: Counter = Counter()
        labels: Dict[str, str] = {}
        for m in meals:
            for item in m.items:
                if item.name:
                    key = item.name.strip().lower()
                    if key and key not in labels:
                        labels[key] = item.name.strip()
                    counter[key] += 1
        if not counter:
            return None
        return labels[counter.most_common(1)[0][0]]

    def _detect_patterns(
        self,
        meals: List[Meal],
        nutrition: List[Any],
    ) -> List[str]:
        patterns: List[str] = []
        recent5 = meals[:5]

        sodium_high = sum(
            1 for m in recent5
            if m.nutrition is not None and m.nutrition.sodium > HIGH_SODIUM_MG
        )
        if len(recent5) >= 3 and sodium_high >= 3:
            patterns.append(
                f"You have consumed high sodium in {sodium_high} of your "
                f"last {len(recent5)} meals."
            )

        protein_low = sum(
            1 for m in recent5
            if m.nutrition is not None and m.nutrition.protein < LOW_PROTEIN_G
        )
        if len(recent5) >= 3 and protein_low >= 3:
            patterns.append(
                f"{protein_low} of your last {len(recent5)} meals were low "
                f"in protein."
            )

        if nutrition:
            avg_fiber = statistics.fmean(n.fiber for n in nutrition)
            if avg_fiber < FIBER_TARGET_G:
                patterns.append(
                    f"Your meals average only {avg_fiber:.1f}g of fiber per meal."
                )

        # Vegetable-intake heuristic: any item name containing a veg keyword.
        veg_keywords = ("vegetable", "salad", "palak", "saag", "bhindi",
                        "gobhi", "gobi", "aloo", "matar", "baingan")
        veg_meals = sum(
            1 for m in recent5
            if any(k in it.name.lower() for it in m.items for k in veg_keywords)
        )
        if len(recent5) >= 3 and veg_meals <= 1:
            patterns.append(
                "You appear to be eating vegetables less frequently."
            )

        if len(meals) >= 2:
            patterns.append(
                "Remember to maintain hydration — aim for about 2–3 litres "
                "of water daily."
            )

        return patterns

    @staticmethod
    def _positive_habits(
        meals: List[Meal],
        avg_dci: float,
        avg_nis: float,
    ) -> List[str]:
        habits: List[str] = []
        if avg_dci is not None and avg_dci >= 0.7:
            habits.append("Your diet is consistent (DCI ≥ 0.70).")
        if avg_nis <= 0.3:
            habits.append("Your meals are nutritionally balanced (NIS ≤ 0.30).")
        if len(meals) >= 5:
            habits.append(f"You have logged {len(meals)} meals so far.")
        return habits

    @staticmethod
    def _habits_to_improve(
        patterns: List[str],
        avg_dci: float,
        avg_nis: float,
    ) -> List[str]:
        improve: List[str] = []
        if any("sodium" in p for p in patterns):
            improve.append("Reduce sodium intake.")
        if any("protein" in p for p in patterns):
            improve.append("Increase protein intake.")
        if any("fiber" in p for p in patterns):
            improve.append("Add more fiber-rich foods.")
        if avg_dci is not None and avg_dci < 0.7:
            improve.append("Improve meal consistency.")
        if avg_nis > 0.4:
            improve.append("Balance your macronutrients closer to targets.")
        return improve

    @staticmethod
    def _dci_trend(meals: List[Meal]) -> Optional[Dict[str, Any]]:
        dcis = [m.dci for m in meals if m.dci is not None]
        if len(dcis) < 2:
            return None
        half = len(dcis) // 2
        first = statistics.fmean(dcis[:half])
        second = statistics.fmean(dcis[half:])
        delta = second - first
        return {
            "delta": round(delta, 3),
            "direction": "improved" if delta > 0 else ("declined" if delta < 0 else "stable"),
        }

    @staticmethod
    def _risk_trend(meals: List[Meal]) -> Optional[Dict[str, Any]]:
        by_risk: Dict[str, List[float]] = {name: [] for _, name in _RISK_KEYS}
        for m in meals:
            if m.predictions is None:
                continue
            for key, name in _RISK_KEYS:
                value = getattr(m.predictions, key)
                if value is not None:
                    by_risk[name].append(float(value))

        best = None
        for name, values in by_risk.items():
            if len(values) < 2:
                continue
            half = len(values) // 2
            first = statistics.fmean(values[:half])
            second = statistics.fmean(values[half:])
            delta = second - first
            if best is None or abs(delta) > abs(best["delta"]):
                best = {"name": name, "delta": round(delta, 3)}
        if best is None:
            return None
        best["direction"] = (
            "decreased" if best["delta"] < 0
            else ("increased" if best["delta"] > 0 else "stable")
        )
        return best

    def _goals(
        self,
        meals: List[Meal],
        nutrition: List[Any],
        avg_dci: float,
        avg_nis: float,
    ) -> List[Dict[str, Any]]:
        goals: List[Dict[str, Any]] = []
        if not meals:
            return goals

        if nutrition:
            avg_sodium = statistics.fmean(n.sodium for n in nutrition)
            avg_protein = statistics.fmean(n.protein for n in nutrition)
            avg_fiber = statistics.fmean(n.fiber for n in nutrition)

            goals.append(self._goal(
                "sodium", "Reduce sodium",
                max(0.0, min(1.0, 1.0 - (avg_sodium - HIGH_SODIUM_MG) / HIGH_SODIUM_MG)),
            ))
            goals.append(self._goal(
                "protein", "Increase protein",
                max(0.0, min(1.0, avg_protein / (LOW_PROTEIN_G * 2))),
            ))
            goals.append(self._goal(
                "fiber", "Eat more fiber",
                max(0.0, min(1.0, avg_fiber / (FIBER_TARGET_G * 2))),
            ))

        # DCI may be None (insufficient data) — do not coerce it to a fake
        # numeric progress; the frontend renders "—" when no DCI is available.
        consistency_progress = avg_dci if avg_dci is not None else 0.0
        goals.append(self._goal(
            "consistency", "Keep meals consistent",
            max(0.0, min(1.0, consistency_progress)),
        ))
        goals.append(self._goal(
            "balance", "Balance your diet",
            max(0.0, min(1.0, 1.0 - avg_nis)),
        ))
        goals.append(self._goal(
            "hydration", "Drink more water", 0.5,
        ))

        return goals

    @staticmethod
    def _goal(goal_id: str, title: str, progress: float) -> Dict[str, Any]:
        progress = round(max(0.0, min(1.0, progress)), 2)
        status = "on-track" if progress >= 0.6 else ("needs-attention" if progress < 0.4 else "in-progress")
        return {"id": goal_id, "title": title, "progress": progress, "status": status}

    @staticmethod
    def _deficiencies(avg_protein: float, avg_fiber: float) -> List[str]:
        missing: List[str] = []
        if avg_protein < LOW_PROTEIN_G:
            missing.append("protein")
        if avg_fiber < FIBER_TARGET_G:
            missing.append("fiber")
        return missing


# Singleton for convenience (matches the project's service pattern).
nutrition_analytics_service = NutritionAnalyticsService()
