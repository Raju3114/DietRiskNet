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

class FoodClassificationRequest(BaseModel):
    crop_image_base64: str

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
    dci: float
    dci_level: str

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
    dci: float
    nis: float
    existing_conditions: List[str]

class DiseasePredictionResponse(BaseModel):
    diabetes_risk: float
    obesity_risk: float
    hypertension_risk: float
    deficiency_risk: float

class RiskFusionRequest(BaseModel):
    dci: float
    nis: float
    disease_prediction: DiseasePredictionResponse

class RiskFusionResponse(BaseModel):
    fused_score: float
    risk_level: str

# --- Recommendation ---
class ExplainDietRequest(BaseModel):
    meal_nutrition: NutritionResponse
    disease_prediction: DiseasePredictionResponse
    dci: float
    nis: float
    history_summary: Optional[Dict[str, Any]] = None

class RecommendationItem(BaseModel):
    category: str
    content: str
    explanation: str

class ExplainDietResponse(BaseModel):
    recommendations: List[RecommendationItem]

# --- Meal Complete Analysis ---
class MealAnalysisResponse(BaseModel):
    meal_id: int
    image_path: Optional[str]
    items: List[MealItemResponse]
    nutrition: NutritionResponse
    dci: float
    dci_level: str
    nis: float
    nis_level: str
    predictions: DiseasePredictionResponse
    fusion: RiskFusionResponse
    recommendations: List[RecommendationItem]
    created_at: datetime

# --- Dashboard & Longitudinal trends ---
class DashboardResponse(BaseModel):
    daily_aggregated: NutritionResponse
    daily_percentage_rdi: Dict[str, float]
    dci: float
    dci_level: str
    nis: float
    nis_level: str
    fused_risk_score: float
    fused_risk_level: str
    recent_meals: List[Dict[str, Any]]
    recommendations: List[RecommendationItem]

class TrendDataPoint(BaseModel):
    date: str
    calories: float
    protein: float
    carbs: float
    fats: float
    dci: float
    nis: float
    diabetes_risk: float
    obesity_risk: float
    hypertension_risk: float
    deficiency_risk: float

class LongitudinalTrendsResponse(BaseModel):
    trends: List[TrendDataPoint]
