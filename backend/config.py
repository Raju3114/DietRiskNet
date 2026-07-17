import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "DietRiskNet"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dietrisknet_super_secret_jwt_key_2026_capstone")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # DB URL, defaulting to local SQLite for ease of run, but configurable for PostgreSQL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./dietrisknet.db")

    # Paths to ML Models
    MODELS_DIR: str = os.getenv("MODELS_DIR", r"d:\DietRiskNet\backend\trained_models")
    YOLO_MODEL_PATH: str = os.path.join(MODELS_DIR, "DietRiskNet_FoodDetector_YOLOv8.pt")
    
    # Food Classifier Model (Configurable via Environment Variable!)
    FOOD_CLASSIFIER_MODEL: str = os.getenv("FOOD_CLASSIFIER_MODEL", "DietRiskNet_FoodClassifier_EfficientNetB3.pth")

    # XGBoost Disease Risk Prediction Models
    DIABETES_MODEL_PATH: str = os.path.join(MODELS_DIR, "DietRiskNet_Diabetes_XGBoost.pkl")
    OBESITY_MODEL_PATH: str = os.path.join(MODELS_DIR, "DietRiskNet_Obesity_XGBoost.pkl")
    HYPERTENSION_MODEL_PATH: str = os.path.join(MODELS_DIR, "DietRiskNet_Hypertension_XGBoost.pkl")
    DEFICIENCY_MODEL_PATH: str = os.path.join(MODELS_DIR, "DietRiskNet_NutritionalDeficiency_XGBoost.pkl")

    # Configurations
    DCI_CONFIG_PATH: str = os.path.join(MODELS_DIR, "DietRiskNet_DCI_Config.json")
    NIS_CONFIG_PATH: str = os.path.join(MODELS_DIR, "DietRiskNet_NIS_Config.json")
    RISK_FUSION_CONFIG_PATH: str = os.path.join(MODELS_DIR, "DietRiskNet_RiskFusion_Config.json")

    # Nutrition database
    NUTRITION_CSV_PATH: str = os.getenv("NUTRITION_CSV_PATH", r"d:\DietRiskNet\nutrition\indian_food_nutrition_processed.csv")

    # File uploads directory
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", r"d:\DietRiskNet\backend\uploads")

    class Config:
        case_sensitive = True

settings = Settings()

# Ensure uploads directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
