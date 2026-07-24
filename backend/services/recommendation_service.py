from typing import List, Dict, Any
from backend.utils.logger import app_logger

class ExplainDietService:
    def recommend(self, meal_nutrition_dict: dict, disease_prediction_dict: dict, 
                  dci: float, nis: float, history_summary: dict = None) -> List[Dict[str, str]]:
        """
        Generates personalized disease-risk-aware dietary recommendations with explanations.
        """
        recommendations = []
        
        # 1. Nutrition specific checks (Sodium, Sugar, Calories, Fiber)
        sodium = meal_nutrition_dict.get("sodium", 0.0)
        sugar = meal_nutrition_dict.get("sugar", 0.0)
        calories = meal_nutrition_dict.get("calories", 0.0)
        fiber = meal_nutrition_dict.get("fiber", 0.0)
        
        # 2. Disease risks
        diab_risk = disease_prediction_dict.get("diabetes_risk", 0.0)
        ob_risk = disease_prediction_dict.get("obesity_risk", 0.0)
        hyp_risk = disease_prediction_dict.get("hypertension_risk", 0.0)
        def_risk = disease_prediction_dict.get("deficiency_risk", 0.0)

        # -- General Nutrition and NIS Check --
        if nis > 0.4:
            recommendations.append({
                "category": "General Nutrition",
                "content": "Diversify your ingredients with fresh fruits, lean proteins, and leafy greens.",
                "explanation": f"Your Nutritional Imbalance Score (NIS) is {nis:.2f}, indicating a high variance from recommended daily intakes. This meal deviates significantly from the balanced RDI baseline."
            })

        # -- Hypertension & Sodium Check --
        if hyp_risk > 0.4 or sodium > 800:
            why = ""
            if hyp_risk > 0.4:
                why += f"Your predicted Hypertension risk is elevated at {hyp_risk*100:.1f}%. "
            if sodium > 800:
                why += f"This single meal contains {sodium:.1f}mg of sodium, which is more than 35% of your recommended daily sodium limit (2300mg). "
            
            recommendations.append({
                "category": "Hypertension",
                "content": "Reduce salt usage and limit high-sodium processed foods. Supplement with potassium-rich foods (like bananas and spinach).",
                "explanation": why + "Reducing sodium intake is clinical practice to decrease blood pressure and lower cardiovascular stress."
            })

        # -- Diabetes & Sugar/Carbs Check --
        if diab_risk > 0.4 or sugar > 15.0:
            why = ""
            if diab_risk > 0.4:
                why += f"Your Diabetes Risk is predicted to be {diab_risk*100:.1f}%. "
            if sugar > 15.0:
                why += f"This meal contains a high amount of free sugars ({sugar:.1f}g). "
                
            recommendations.append({
                "category": "Diabetes",
                "content": "Switch to whole grains and low-glycemic index foods. Strictly limit sugary drinks and sweets.",
                "explanation": why + "Consuming refined carbohydrates and free sugars triggers rapid insulin spikes, which increases insulin resistance and elevates diabetic risk."
            })

        # -- Obesity & Calories Check --
        if ob_risk > 0.5 or calories > 800:
            why = ""
            if ob_risk > 0.5:
                why += f"Your Obesity risk is calculated at {ob_risk*100:.1f}%. "
            if calories > 800:
                why += f"This meal is calorie-dense, providing {calories:.1f} kcal (40% of the standard daily 2000 kcal recommendation). "
                
            recommendations.append({
                "category": "Obesity",
                "content": "Control your portion sizes and practice mindful eating. Increase dietary fiber to feel full longer.",
                "explanation": why + "A consistent surplus in calorie intake without equal energy expenditure triggers adipose tissue storage, driving weight gain."
            })

        # -- Nutritional Deficiency & Fiber/Minerals Check --
        if def_risk > 0.4 or fiber < 2.0:
            why = ""
            if def_risk > 0.4:
                why += f"The system predicts a {def_risk*100:.1f}% risk of nutritional deficiency. "
            if fiber < 2.0:
                why += "This meal is very low in dietary fiber (under 2g). "
                
            recommendations.append({
                "category": "Deficiency",
                "content": "Incorporate more fiber-rich beans, legumes, lentils, and iron/calcium-fortified foods into your diet.",
                "explanation": why + "Low dietary fiber and lack of micronutrients (vitamins, calcium, iron) lead to digestive issues, fatigue, and compromise metabolic efficiency."
            })

        # -- Dietary Consistency (DCI) Check --
        if dci < 0.7:
            recommendations.append({
                "category": "Diet Consistency",
                "content": "Establish regular meal timings and aim for consistent daily calorie budgets.",
                "explanation": f"Your Dietary Consistency Index (DCI) is low ({dci:.2f}). Large fluctuations in daily calories or macronutrient ratios disrupt circadian rhythms and impair metabolic health."
            })

        # Base case fallback if everything is perfect
        if not recommendations:
            recommendations.append({
                "category": "General Health",
                "content": "Excellent meal balance! Keep up your current eating habits.",
                "explanation": "Your nutrient distribution is aligned with reference limits, and all disease risk scores remain in the safe range."
            })

        return recommendations

# Singleton instance of ExplainDietService
explain_diet_service = ExplainDietService()
