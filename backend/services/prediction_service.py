import os
import pickle
import pandas as pd
import numpy as np
from backend.config import settings
from backend.utils.logger import ml_logger

class DiseasePredictionService:
    def __init__(self):
        self.models = {}
        self.load_models()

    def load_models(self):
        model_files = {
            "diabetes": settings.DIABETES_MODEL_PATH,
            "obesity": settings.OBESITY_MODEL_PATH,
            "hypertension": settings.HYPERTENSION_MODEL_PATH,
            "deficiency": settings.DEFICIENCY_MODEL_PATH
        }
        
        for key, path in model_files.items():
            try:
                ml_logger.info(f"Loading {key} XGBoost model from {path}")
                if os.path.exists(path):
                    with open(path, "rb") as f:
                        self.models[key] = pickle.load(f)
                    ml_logger.info(f"{key} XGBoost model loaded successfully.")
                else:
                    ml_logger.error(f"XGBoost model not found at {path}")
            except Exception as e:
                ml_logger.error(f"Failed to load {key} XGBoost model: {e}")
                raise e

    def predict_all(self, age: int, gender: str, height: float, weight: float, 
                    meal_nutrition_dict: dict, dci: float, nis: float, 
                    existing_conditions: list) -> dict:
        """
        Executes all four XGBoost prediction pipelines and returns risk scores.
        """
        # Calculate BMI
        bmi = 22.0
        if height > 0:
            bmi = weight / ((height / 100.0) ** 2)

        # 1. Diabetes Prediction
        diabetes_risk = self.predict_diabetes(age, gender, bmi, existing_conditions)

        # 2. Obesity Prediction
        obesity_risk = self.predict_obesity(age, gender, height, weight, bmi, meal_nutrition_dict)

        # 3. Hypertension Prediction
        hypertension_risk = self.predict_hypertension(age, bmi, meal_nutrition_dict, existing_conditions)

        # 4. Nutritional Deficiency Prediction
        deficiency_risk = self.predict_deficiency(age, gender, bmi, meal_nutrition_dict, existing_conditions)

        return {
            "diabetes_risk": diabetes_risk,
            "obesity_risk": obesity_risk,
            "hypertension_risk": hypertension_risk,
            "deficiency_risk": deficiency_risk
        }

    def predict_diabetes(self, age: int, gender: str, bmi: float, existing_conditions: list) -> float:
        model = self.models.get("diabetes")
        if model is None:
            return 0.1
        try:
            # Features: ['gender', 'age', 'hypertension', 'heart_disease', 'smoking_history', 'bmi', 'HbA1c_level', 'blood_glucose_level']
            has_hypertension = 1 if "hypertension" in existing_conditions else 0
            has_heart_disease = 1 if "heart_disease" in existing_conditions else 0
            
            # Estimate clinical values based on existing conditions
            hba1c = 7.0 if "diabetes" in existing_conditions else 5.5
            glucose = 160.0 if "diabetes" in existing_conditions else 100.0
            
            inp = {
                'gender': gender,
                'age': float(age),
                'hypertension': has_hypertension,
                'heart_disease': has_heart_disease,
                'smoking_history': 'never',
                'bmi': bmi,
                'HbA1c_level': hba1c,
                'blood_glucose_level': glucose
            }
            
            df = pd.DataFrame([inp])
            for col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].astype('category')
                    
            proba = model.predict_proba(df)[0]
            # Risk is probability of positive class (index 1)
            return float(proba[1])
        except Exception as e:
            ml_logger.error(f"Error predicting diabetes: {e}")
            return 0.1

    def predict_obesity(self, age: int, gender: str, height: float, weight: float, bmi: float, 
                        meal_nutrition_dict: dict) -> float:
        model = self.models.get("obesity")
        if model is None:
            return 0.1
        try:
            # Features: ['Gender', 'Age', 'Height', 'Weight', 'family_history', 'FAVC', 'FCVC', 'NCP', 'CAEC', 'SMOKE', 'CH2O', 'SCC', 'FAF', 'TUE', 'CALC', 'MTRANS']
            # AVC: High caloric food consumption. If calories > 700 -> 'yes'
            favc = 'yes' if meal_nutrition_dict.get("calories", 0) > 700 else 'no'
            # CVC: Vegetable frequency. Based on fiber. If fiber > 5g -> 3.0, if > 2g -> 2.0, else 1.0
            fiber = meal_nutrition_dict.get("fiber", 0)
            fcvc = 3.0 if fiber > 5.0 else (2.0 if fiber > 2.0 else 1.0)
            
            inp = {
                'Gender': gender,
                'Age': float(age),
                'Height': height / 100.0, # Model expects height in meters!
                'Weight': weight,
                'family_history': 'yes',
                'FAVC': favc,
                'FCVC': fcvc,
                'NCP': 3.0,
                'CAEC': 'Sometimes',
                'SMOKE': 'no',
                'CH2O': 2.0,
                'SCC': 'no',
                'FAF': 1.0,
                'TUE': 1.0,
                'CALC': 'Sometimes',
                'MTRANS': 'Public_Transportation'
            }
            
            df = pd.DataFrame([inp])
            for col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].astype('category')
                    
            proba = model.predict_proba(df)[0]
            # Multi-class: 7 classes. Sum probabilities of Overweight and Obese classes (indices 2 to 6)
            obesity_prob = float(np.sum(proba[2:]))
            return obesity_prob
        except Exception as e:
            ml_logger.error(f"Error predicting obesity: {e}")
            return 0.1

    def predict_hypertension(self, age: int, bmi: float, meal_nutrition_dict: dict, 
                             existing_conditions: list) -> float:
        model = self.models.get("hypertension")
        if model is None:
            return 0.1
        try:
            # Features: ['Age', 'Salt_Intake', 'Stress_Score', 'BP_History', 'Sleep_Duration', 'BMI', 'Medication', 'Family_History', 'Exercise_Level', 'Smoking_Status']
            # Sodium is in mg. Convert to estimated salt intake in grams (1g salt ~ 400mg sodium)
            sodium = meal_nutrition_dict.get("sodium", 0.0)
            salt_intake = max(1.0, sodium / 400.0)
            
            has_bp_history = 1 if "hypertension" in existing_conditions else 0
            
            inp = {
                'Age': float(age),
                'Salt_Intake': salt_intake,
                'Stress_Score': 3.0,
                'BP_History': has_bp_history,
                'Sleep_Duration': 7.0,
                'BMI': bmi,
                'Medication': 0,
                'Family_History': 0,
                'Exercise_Level': 2.0,
                'Smoking_Status': 'Never'
            }
            
            df = pd.DataFrame([inp])
            for col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].astype('category')
                    
            proba = model.predict_proba(df)[0]
            # Binary model, return positive probability (index 1)
            return float(proba[1])
        except Exception as e:
            ml_logger.error(f"Error predicting hypertension: {e}")
            return 0.1

    def predict_deficiency(self, age: int, gender: str, bmi: float, meal_nutrition_dict: dict, 
                           existing_conditions: list) -> float:
        model = self.models.get("deficiency")
        if model is None:
            return 0.1
        try:
            # Features: ['age', 'gender', 'bmi', 'smoking_status', 'alcohol_consumption', 'exercise_level', 'diet_type', 'sun_exposure', 'income_level', 'latitude_region', ...]
            # Compare meal nutrient levels to RDI and calculate RDA percentages
            vit_c_pct = min(100.0, (meal_nutrition_dict.get("vitamin_c", 0.0) / 90.0) * 100.0)
            folate_pct = min(100.0, (meal_nutrition_dict.get("folate", 0.0) / 400.0) * 100.0)
            calcium_pct = min(100.0, (meal_nutrition_dict.get("calcium", 0.0) / 1000.0) * 100.0)
            iron_pct = min(100.0, (meal_nutrition_dict.get("iron", 0.0) / 18.0) * 100.0)
            
            has_deficiency = 1 if "deficiency" in existing_conditions else 0
            
            inp = {
                'age': float(age),
                'gender': gender,
                'bmi': bmi,
                'smoking_status': 'Never',
                'alcohol_consumption': 'Low',
                'exercise_level': 'Moderate',
                'diet_type': 'Mixed',
                'sun_exposure': 'Moderate',
                'income_level': 'Medium',
                'latitude_region': 'Tropical',
                'vitamin_a_percent_rda': 80.0,
                'vitamin_c_percent_rda': vit_c_pct,
                'vitamin_d_percent_rda': 50.0,
                'vitamin_e_percent_rda': 85.0,
                'vitamin_b12_percent_rda': 70.0,
                'folate_percent_rda': folate_pct,
                'calcium_percent_rda': calcium_pct,
                'iron_percent_rda': iron_pct,
                'hemoglobin_g_dl': 14.0,
                'serum_vitamin_d_ng_ml': 30.0,
                'serum_vitamin_b12_pg_ml': 400.0,
                'serum_folate_ng_ml': 12.0,
                'symptoms_count': 0,
                'symptoms_list': 'None',
                'has_night_blindness': 0,
                'has_fatigue': 0,
                'has_bleeding_gums': 0,
                'has_bone_paint': 0, # wait! Let's look at the exact spelling in the dataset
                'has_bone_pain': 0,
                'has_muscle_weakness': 0,
                'has_numbness_tingling': 0,
                'has_memory_problems': 0,
                'has_pale_skin': 0,
                'has_multiple_deficiencies': has_deficiency
            }
            
            # The columns in the dataset keys:
            # Let's inspect the model features in we printed:
            # 'has_bone_pain' was correct in printout.
            # Let's clean standard fields to match exact feature_names_in_
            features = model.feature_names_in_
            filtered_inp = {}
            for f in features:
                if f in inp:
                    filtered_inp[f] = inp[f]
                else:
                    # Default backup
                    filtered_inp[f] = 0.0
                    
            df = pd.DataFrame([filtered_inp])
            for col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].astype('category')
                    
            proba = model.predict_proba(df)[0]
            # Risk is 1 - proba[0] (i.e. the probability of having any deficiency)
            return float(1.0 - proba[0])
        except Exception as e:
            ml_logger.error(f"Error predicting nutritional deficiency: {e}")
            return 0.1
