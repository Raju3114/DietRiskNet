import os
import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator

logger = logging.getLogger("app")

# Sentinel: a value that is clearly NOT a production secret.
# pydantic-settings will override this from the SECRET_KEY env var automatically.
_INSECURE_DEV_SECRET = "CHANGE_ME___insecure_dev_jwt_key___DO_NOT_USE_IN_PRODUCTION"

class Settings(BaseSettings):
    PROJECT_NAME: str = "DietRiskNet"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", _INSECURE_DEV_SECRET)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # DB URL, defaulting to local SQLite for ease of run, but configurable for PostgreSQL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./dietrisknet.db")

    # Paths to ML Models
    MODELS_DIR: str = os.getenv(
        "MODELS_DIR",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "trained_models"))
    )
    YOLO_MODEL_PATH: str = os.path.join(MODELS_DIR, "DietRiskNet_FoodDetector_YOLOv8.pt")
    
    # Food Classifier Model (Configurable via Environment Variable!)
    FOOD_CLASSIFIER_MODEL: str = os.getenv("FOOD_CLASSIFIER_MODEL", "DietRiskNet_FoodClassifier_EfficientNetB3.pth")

    # Minimum top-1 classifier confidence required to accept a recognised
    # food.  Measured during the validation audit: a real food crop scored
    # ~0.87 while solid-color / noise / gradient non-food images scored
    # <= 0.03.  0.45 is deliberately conservative — it rejects non-food with
    # a huge margin while leaving a wide safety gap for genuine (even
    # slightly occluded) food crops.  Configurable via env var.
    CLASSIFIER_CONFIDENCE_THRESHOLD: float = float(os.getenv("CLASSIFIER_CONFIDENCE_THRESHOLD", "0.45"))

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
    NUTRITION_CSV_PATH: str = os.getenv(
        "NUTRITION_CSV_PATH",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "nutrition", "indian_food_nutrition_processed.csv"))
    )

    # File uploads directory
    #
    # Retention policy: uploaded meal images are retained indefinitely.
    # They are referenced by Meal.image_path and displayed on the
    # Analysis page, so they must NOT be deleted while a Meal record
    # exists. To reclaim disk, remove only ORPHANED files (uploads whose
    # filename has no matching Meal.image_path) via an external job;
    # do not delete on report generation because the image is still
    # needed by the web UI.
    UPLOAD_DIR: str = os.getenv(
        "UPLOAD_DIR",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "uploads"))
    )

    # LLM provider configuration.
    # provider options: "ollama" (default, local, no API key required),
    # "gemini" (optional cloud). Future: "openai", "claude", "azure_openai".
    # When "gemini" is selected and Gemini fails, requests automatically
    # fall back to local Ollama.
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")

    # Ollama-specific settings (default LOCAL provider).  The app works
    # with no API key when a local Ollama server + model are available.
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    OLLAMA_TIMEOUT: float = float(os.getenv("OLLAMA_TIMEOUT", "120"))

    # Gemini-specific settings (OPTIONAL cloud provider). GEMINI_API_KEY
    # is intentionally empty by default — leaving it empty disables Gemini
    # gracefully (the rule-based recommendation engine and Ollama still
    # work).
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    GEMINI_TIMEOUT_SECONDS: float = float(os.getenv("GEMINI_TIMEOUT", "15"))

    # Load configuration from environment variables first, then from a
    # root-level `.env` file (kept out of version control).  This makes
    # the documented "copy .env.example to .env" workflow work.
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @model_validator(mode="after")
    def warn_if_insecure_secret_key(self):
        known_insecure = {
            _INSECURE_DEV_SECRET,
            "dietrisknet_super_secret_jwt_key_2026_capstone",
        }
        if self.SECRET_KEY in known_insecure:
            import warnings
            msg = (
                f"SECRET_KEY is set to an insecure default value "
                f"({self.SECRET_KEY[:20]}...). "
                "Generate a strong random key for production and set it "
                "via the SECRET_KEY environment variable."
            )
            warnings.warn(msg, RuntimeWarning, stacklevel=2)
            logger.critical("SECURITY: %s", msg)
        return self

settings = Settings()

# Ensure uploads directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
