import json
import os
import numpy as np
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from backend.config import settings
from backend.database.models import Meal, MealNutrition
from backend.utils.logger import app_logger

class DCIService:
    def __init__(self):
        self.config = {}
        self.load_config()

    def load_config(self):
        try:
            if os.path.exists(settings.DCI_CONFIG_PATH):
                with open(settings.DCI_CONFIG_PATH, "r") as f:
                    self.config = json.load(f)
                app_logger.info("Loaded DCI configurations successfully.")
            else:
                app_logger.error(f"DCI Config not found at {settings.DCI_CONFIG_PATH}")
        except Exception as e:
            app_logger.error(f"Failed to load DCI config: {e}")

    def calculate(self, meal_nutrition_dict: dict, user_id: int, db: Session) -> tuple:
        """
        Calculates Dietary Consistency Index (DCI).
        Returns (dci_score, dci_level)
        """
        # Step 1: Calculate DCI score in range [0, 1]
        # Query user's meal history for last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        past_meals = db.query(Meal).filter(
            Meal.user_id == user_id,
            Meal.created_at >= seven_days_ago
        ).all()
        
        # Aggregate calories per day
        daily_calories = {}
        for m in past_meals:
            # Format date as YYYY-MM-DD
            day_str = m.created_at.strftime("%Y-%m-%d")
            # Get meal calories
            cal = m.nutrition.calories if m.nutrition else 0
            daily_calories[day_str] = daily_calories.get(day_str, 0.0) + cal

        # If we have at least 2 days of history, we measure calorie consistency (longitudinal)
        if len(daily_calories) >= 2:
            calories_list = list(daily_calories.values())
            mean_cal = np.mean(calories_list)
            std_cal = np.std(calories_list)
            
            if mean_cal > 0:
                cv = std_cal / mean_cal
                # DCI is 1 - CV (higher consistency = lower CV)
                dci_score = max(0.0, min(1.0, 1.0 - cv))
            else:
                dci_score = 1.0
            app_logger.info(f"DCI calculated longitudinally over {len(daily_calories)} days: {dci_score:.4f}")
        else:
            # Fallback to meal macronutrient balance against target (55% carbs, 15% protein, 30% fats)
            carbs_cal = meal_nutrition_dict.get("carbs", 0) * 4
            protein_cal = meal_nutrition_dict.get("protein", 0) * 4
            fats_cal = meal_nutrition_dict.get("fats", 0) * 9
            total_macro_cal = carbs_cal + protein_cal + fats_cal
            
            if total_macro_cal > 0:
                p_carbs = carbs_cal / total_macro_cal
                p_protein = protein_cal / total_macro_cal
                p_fats = fats_cal / total_macro_cal
                
                # Compute absolute deviation from balanced targets
                deviation = abs(p_carbs - 0.55) + abs(p_protein - 0.15) + abs(p_fats - 0.30)
                # Max deviation is 2.0 (e.g. 100% carbs when targets are 55/15/30)
                # DCI = 1 - deviation/2
                dci_score = max(0.0, min(1.0, 1.0 - (deviation / 2.0)))
            else:
                dci_score = 1.0
            app_logger.info(f"DCI calculated from meal macro balance: {dci_score:.4f}")

        # Step 2: Map score to categories from configuration file
        dci_level = "Unknown"
        for level, range_limits in self.config.items():
            low, high = range_limits
            if low <= dci_score <= high:
                dci_level = level
                break
                
        return dci_score, dci_level


class NISService:
    def __init__(self):
        self.config = {}
        self.load_config()

    def load_config(self):
        try:
            if os.path.exists(settings.NIS_CONFIG_PATH):
                with open(settings.NIS_CONFIG_PATH, "r") as f:
                    self.config = json.load(f)
                app_logger.info("Loaded NIS configurations successfully.")
            else:
                app_logger.error(f"NIS Config not found at {settings.NIS_CONFIG_PATH}")
        except Exception as e:
            app_logger.error(f"Failed to load NIS config: {e}")

    def calculate(self, meal_nutrition_dict: dict) -> tuple:
        """
        Calculates Nutritional Imbalance Score (NIS).
        Returns (nis_score, nis_level)
        """
        rdi = self.config.get("RDI", {
            "Calories": 2000, "Protein": 60, "Carbs": 300, "Fat": 65, "Sodium": 2300, "Fiber": 30
        })
        thresholds = self.config.get("Thresholds", {})
        
        # Map keys from Pydantic schema to RDI keys
        nutrition_map = {
            "Calories": "calories",
            "Protein": "protein",
            "Carbs": "carbs",
            "Fat": "fats",
            "Sodium": "sodium",
            "Fiber": "fiber"
        }
        
        deviations = []
        for rdi_key, schema_key in nutrition_map.items():
            rdi_val = rdi.get(rdi_key, 1.0)
            # Ensure no division by zero
            if rdi_val <= 0:
                rdi_val = 1.0
            actual_val = meal_nutrition_dict.get(schema_key, 0.0)
            
            # Relative deviation: |actual - RDI| / RDI
            dev = abs(actual_val - rdi_val) / rdi_val
            deviations.append(dev)
            
        # Overall NIS score is average relative deviation
        nis_score = float(np.mean(deviations))
        
        # Map score to level
        nis_level = "Unknown"
        for level, range_limits in thresholds.items():
            low, high = range_limits
            if low <= nis_score <= high:
                nis_level = level
                break
                
        return nis_score, nis_level
