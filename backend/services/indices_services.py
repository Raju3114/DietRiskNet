import json
import os
import numpy as np
from sqlalchemy.orm import Session
from datetime import timedelta
from backend.utils.datetime_utils import utcnow
from backend.config import settings
from backend.database.models import Meal, MealNutrition
from backend.utils.logger import app_logger
from backend.services.classification import ThresholdConfig


class DCIService:
    def __init__(self):
        self.config: ThresholdConfig = None
        self.load_config()

    def load_config(self):
        try:
            if os.path.exists(settings.DCI_CONFIG_PATH):
                self.config = ThresholdConfig.from_file(
                    settings.DCI_CONFIG_PATH,
                    higher_is_better=True,
                    name="DCI",
                )
                app_logger.info("Loaded DCI configurations successfully.")
            else:
                app_logger.error(f"DCI Config not found at {settings.DCI_CONFIG_PATH}")
        except Exception as e:
            app_logger.error(f"Failed to load DCI config: {e}")
            raise

    def calculate(self, meal_nutrition_dict: dict, user_id: int, db: Session) -> tuple:
        """
        Calculates Dietary Consistency Index (DCI).
        Returns (dci_score, dci_level).

        DCI measures *longitudinal* dietary consistency: the day-to-day
        variation of total calorie intake.  It requires at least 2 DISTINCT
        calendar days with valid (non-zero) nutrition data within the last 7
        days.

        With fewer than 2 valid days — or a historical mean calorie intake of
        zero — DCI is UNAVAILABLE and the level is "Insufficient Data".  It is
        deliberately NOT computed from a single meal's macro balance (that
        would measure meal quality, not consistency), and it never fabricates
        a perfect score.

        Formula (unchanged longitudinal definition):
            CV = std(daily_calories) / mean(daily_calories)
            DCI = clamp(1 - CV, 0, 1)
        """
        # Step 1: Calculate DCI score in range [0, 1]
        # Query user's meal history for last 7 days
        seven_days_ago = utcnow() - timedelta(days=7)
        past_meals = db.query(Meal).filter(
            Meal.user_id == user_id,
            Meal.created_at >= seven_days_ago
        ).all()

        # Aggregate calories per day, keeping only days with valid (>0) intake.
        # Zero-calorie / nutrition-unavailable meals do NOT establish history.
        daily_calories = {}
        for m in past_meals:
            cal = m.nutrition.calories if m.nutrition else 0.0
            if cal <= 0:
                continue
            day_str = m.created_at.strftime("%Y-%m-%d")
            daily_calories[day_str] = daily_calories.get(day_str, 0.0) + cal

        valid_days = len(daily_calories)
        if valid_days < 2:
            app_logger.info(
                f"DCI unavailable: only {valid_days} valid day(s) of history "
                "(<2 distinct days required)."
            )
            return None, "Insufficient Data"

        calories_list = list(daily_calories.values())
        mean_cal = float(np.mean(calories_list))
        if mean_cal <= 0:
            app_logger.info("DCI unavailable: historical mean calorie intake is zero.")
            return None, "Insufficient Data"

        std_cal = float(np.std(calories_list))
        cv = std_cal / mean_cal
        # DCI is 1 - CV (higher consistency = lower CV)
        dci_score = max(0.0, min(1.0, 1.0 - cv))
        app_logger.info(f"DCI calculated longitudinally over {valid_days} days: {dci_score:.4f}")

        # Step 2: Classify score into a level using threshold-based classification
        dci_level = self.config.classify(dci_score)

        return dci_score, dci_level


class NISService:
    def __init__(self):
        self.config: ThresholdConfig = None
        self.rdi: dict = {}
        self.load_config()

    def load_config(self):
        try:
            if os.path.exists(settings.NIS_CONFIG_PATH):
                with open(settings.NIS_CONFIG_PATH, "r") as f:
                    data = json.load(f)
                self.rdi = data.get("RDI", {})
                self.config = ThresholdConfig.from_dict(
                    data,
                    higher_is_better=False,
                    name="NIS",
                )
                app_logger.info("Loaded NIS configurations successfully.")
            else:
                app_logger.error(f"NIS Config not found at {settings.NIS_CONFIG_PATH}")
        except Exception as e:
            app_logger.error(f"Failed to load NIS config: {e}")
            raise

    def calculate(self, meal_nutrition_dict: dict) -> tuple:
        """
        Calculates Nutritional Imbalance Score (NIS).
        Returns (nis_score, nis_level)

        NIS is a *meal-level* relative nutrient deviation score in [0, 1]
        (higher = more imbalanced).

        The meal is compared against a calorie-proportional share of the
        daily RDI instead of the full daily RDI.  A meal that supplies a
        fraction ``f`` of the day's calories is expected to supply roughly
        ``f`` of each daily nutrient target:

            meal_fraction = min(1, meal_calories / daily_calorie_target)
            meal_rdi[k]   = daily_rdi[k] * meal_fraction
            deviation[k]  = |actual[k] - meal_rdi[k]| / meal_rdi[k]
            NIS           = clamp(mean(deviation), 0, 1)

        Rationale: comparing one meal against the full daily RDI made every
        normal meal look severely imbalanced, because a single meal is
        naturally smaller than a whole day's intake (e.g. an idli meal
        previously scored NIS ~0.96 = "Severe Imbalance").

        If the meal has no / unknown calories (e.g. every item's nutrition
        was unresolved), a documented default fraction of 1/3 of the daily
        target is used (three-meals-per-day convention).  This default is a
        placeholder that can later be driven by meal type
        (breakfast/lunch/dinner/snack) or a configurable value.

        Each relative deviation is left unclamped so a single severe
        nutrient (e.g. 4x daily sodium) is fully reflected, and the final
        score is bounded to [0, 1] to stay interpretable for risk fusion.
        """
        rdi = self.rdi if self.rdi else {
            "Calories": 2000, "Protein": 60, "Carbs": 300, "Fat": 65, "Sodium": 2300, "Fiber": 30
        }

        # Map keys from Pydantic schema to RDI keys
        nutrition_map = {
            "Calories": "calories",
            "Protein": "protein",
            "Carbs": "carbs",
            "Fat": "fats",
            "Sodium": "sodium",
            "Fiber": "fiber"
        }

        # Meal-level RDI allowance (see docstring).
        daily_cal = rdi.get("Calories", 2000)
        meal_cal = meal_nutrition_dict.get("calories", 0.0)
        if daily_cal > 0 and meal_cal > 0:
            meal_fraction = min(1.0, meal_cal / daily_cal)
        else:
            # Unknown-size meal: default to one third of the daily target.
            meal_fraction = 1.0 / 3.0

        deviations = []
        for rdi_key, schema_key in nutrition_map.items():
            rdi_val = rdi.get(rdi_key, 1.0)
            # Ensure no division by zero
            if rdi_val <= 0:
                rdi_val = 1.0
            meal_rdi_val = rdi_val * meal_fraction
            if meal_rdi_val <= 0:
                meal_rdi_val = 1.0
            actual_val = meal_nutrition_dict.get(schema_key, 0.0)

            # Relative deviation from the meal-level RDI share
            dev = abs(actual_val - meal_rdi_val) / meal_rdi_val
            deviations.append(dev)

        # Overall NIS is the average relative deviation, bounded to [0, 1].
        nis_score = float(max(0.0, min(1.0, np.mean(deviations))))

        # Classify score into a level using threshold-based classification
        nis_level = self.config.classify(nis_score)

        return nis_score, nis_level

# Singleton instances of indices services
dci_service = DCIService()
nis_service = NISService()
