from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- Authentication ---
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    full_name: Optional[str] = None

class TokenRefresh(BaseModel):
    refresh_token: str

# --- Settings and Profile ---
class UserSettingUpdate(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    activity_level: Optional[str] = None
    existing_conditions: Optional[List[str]] = None
    rdi_custom: Optional[Dict[str, float]] = None

class UserSettingResponse(BaseModel):
    id: int
    user_id: int
    age: int
    gender: str
    height: float
    weight: float
    activity_level: str
    existing_conditions: List[str]
    rdi_custom: Optional[Dict[str, float]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserProfileResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    settings: Optional[UserSettingResponse] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- Meal Item / Nutrition ---
class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

class MealItemBase(BaseModel):
    name: str
    confidence: float
    bounding_box: Optional[BoundingBox] = None
    weight_g: float = 100.0

class MealItemResponse(BaseModel):
    id: int
    name: str
    confidence: float
    x1: Optional[float] = None
    y1: Optional[float] = None
    x2: Optional[float] = None
    y2: Optional[float] = None
    weight_g: float
    calories: float
    protein: float
    carbs: float
    fats: float
    sugar: float
    fiber: float
    sodium: float
    calcium: float
    iron: float
    vitamin_c: float
    folate: float
    # False when the classifier recognised a food that has no record in the
    # nutrition database (its nutrient fields are then all zero and must NOT
    # be treated as measured values).
    nutrition_available: bool = True

    class Config:
        from_attributes = True

class NutritionResponse(BaseModel):
    calories: float
    protein: float
    carbs: float
    fats: float
    sugar: float
    fiber: float
    sodium: float
    calcium: float
    iron: float
    vitamin_c: float
    folate: float

    class Config:
        from_attributes = True

# --- Pipeline APIs Requests/Responses ---
class FoodDetectionResponse(BaseModel):
    detections: List[MealItemBase]

class FoodClassificationResponse(BaseModel):
    class_name: str
    confidence: float

class NutritionAnalysisRequest(BaseModel):
    items: List[MealItemBase]

class NutritionAnalysisResponse(BaseModel):
    items: List[MealItemResponse]
    aggregated: NutritionResponse

class CalculateDCIRequest(BaseModel):
    meal_nutrition: NutritionResponse
    user_id: int

class CalculateDCIResponse(BaseModel):
    # dci is null when the user has <2 valid days of longitudinal history.
    dci: Optional[float] = None
    dci_level: Optional[str] = None

class CalculateNISRequest(BaseModel):
    meal_nutrition: NutritionResponse

class CalculateNISResponse(BaseModel):
    nis: float
    nis_level: str

# --- Disease & Risk Fusion ---
class DiseasePredictionRequest(BaseModel):
    age: int
    gender: str
    height: float
    weight: float
    meal_nutrition: NutritionResponse
    existing_conditions: List[str]
    # NOTE: DCI / NIS are intentionally absent — the XGBoost prediction models
    # do not consume them (they feed risk fusion / recommendations instead).

class DiseasePredictionResponse(BaseModel):
    diabetes_risk: float
    obesity_risk: float
    hypertension_risk: float
    deficiency_risk: float

class RiskFusionRequest(BaseModel):
    # dci is null when the user has insufficient longitudinal history; fusion
    # renormalises the remaining component weights instead of fabricating a value.
    dci: Optional[float] = None
    nis: Optional[float] = None
    disease_prediction: DiseasePredictionResponse

class RiskFusionResponse(BaseModel):
    # Null when no meaningful risk component is available.
    fused_score: Optional[float] = None
    risk_level: Optional[str] = None

# --- Recommendation ---
class ExplainDietRequest(BaseModel):
    meal_nutrition: NutritionResponse
    disease_prediction: DiseasePredictionResponse
    # dci is null when the user has insufficient longitudinal history; the
    # recommendation engine only warns about consistency when a value exists.
    dci: Optional[float] = None
    nis: Optional[float] = None
    history_summary: Optional[Dict[str, Any]] = None

class RecommendationItem(BaseModel):
    category: str
    content: str
    explanation: str

class ExplainDietResponse(BaseModel):
    recommendations: List[RecommendationItem]

# --- AI Dietitian (Gemini) ---
class AIDietitianResponse(BaseModel):
    summary: str
    meal_quality: str
    health_score: int
    health_level: str
    health_explanation: str
    risk_explanation: str
    recommendations: List[str] = Field(default_factory=list)
    healthier_alternatives: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)

# --- Meal Complete Analysis ---
class MealAnalysisResponse(BaseModel):
    meal_id: int
    image_path: Optional[str]
    items: List[MealItemResponse]
    nutrition: NutritionResponse
    # Indices / risk are null when no item had usable nutrition (insufficient
    # data) — they must not be fabricated from zero-nutrient input.
    dci: Optional[float] = None
    dci_level: Optional[str] = None
    nis: Optional[float] = None
    nis_level: Optional[str] = None
    predictions: Optional[DiseasePredictionResponse] = None
    fusion: Optional[RiskFusionResponse] = None
    recommendations: List[RecommendationItem] = Field(default_factory=list)
    ai_dietitian: Optional[AIDietitianResponse] = None  # nullable; null when Gemini unavailable
    created_at: datetime

# --- Dashboard & Longitudinal trends ---
class DashboardResponse(BaseModel):
    daily_aggregated: NutritionResponse
    daily_percentage_rdi: Dict[str, float]
    # DCI / NIS / risk are null when the user has no logged meals yet
    # (insufficient data) — they must not be fabricated as perfect health.
    dci: Optional[float] = None
    dci_level: Optional[str] = None
    nis: Optional[float] = None
    nis_level: Optional[str] = None
    fused_risk_score: Optional[float] = None
    fused_risk_level: Optional[str] = None
    recent_meals: List[Dict[str, Any]]
    recommendations: List[RecommendationItem]

class TrendDataPoint(BaseModel):
    date: str
    calories: float
    protein: float
    carbs: float
    fats: float
    # dci / nis are null when no longitudinal value exists (do not fabricate).
    dci: Optional[float] = None
    nis: Optional[float] = None
    diabetes_risk: float
    obesity_risk: float
    hypertension_risk: float
    deficiency_risk: float

class LongitudinalTrendsResponse(BaseModel):
    trends: List[TrendDataPoint]
