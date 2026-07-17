from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    settings = relationship("UserSetting", back_populates="user", uselist=False, cascade="all, delete-orphan")
    meals = relationship("Meal", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    diet_history = relationship("DietHistory", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="refresh_tokens")

class UserSetting(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    age = Column(Integer, default=30)
    gender = Column(String, default="Male")  # Male, Female
    height = Column(Float, default=170.0)  # cm
    weight = Column(Float, default=70.0)   # kg
    activity_level = Column(String, default="Moderate")  # Sedentary, Lightly Active, Moderately Active, Very Active
    existing_conditions = Column(JSON, default=list)  # ["diabetes", "hypertension"] etc
    rdi_custom = Column(JSON, nullable=True)  # Custom nutrition goals override
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="settings")

class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    image_path = Column(String, nullable=True)
    dci = Column(Float, nullable=True)  # Dietary Consistency Index
    dci_level = Column(String, nullable=True)  # High, Moderate, etc.
    nis = Column(Float, nullable=True)  # Nutritional Imbalance Score
    nis_level = Column(String, nullable=True)  # Balanced, Mild Imbalance, etc.
    risk_fusion_score = Column(Float, nullable=True)
    risk_fusion_level = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="meals")
    items = relationship("MealItem", back_populates="meal", cascade="all, delete-orphan")
    nutrition = relationship("MealNutrition", back_populates="meal", uselist=False, cascade="all, delete-orphan")
    predictions = relationship("DiseasePrediction", back_populates="meal", uselist=False, cascade="all, delete-orphan")
    fusion_result = relationship("RiskFusionResult", back_populates="meal", uselist=False, cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="meal", cascade="all, delete-orphan")
    history_entry = relationship("DietHistory", back_populates="meal", uselist=False, cascade="all, delete-orphan")

class MealItem(Base):
    __tablename__ = "meal_items"

    id = Column(Integer, primary_key=True, index=True)
    meal_id = Column(Integer, ForeignKey("meals.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    confidence = Column(Float, default=1.0)
    # Bounding Box (YOLO detection)
    x1 = Column(Float, nullable=True)
    y1 = Column(Float, nullable=True)
    x2 = Column(Float, nullable=True)
    y2 = Column(Float, nullable=True)
    weight_g = Column(Float, default=100.0) # Estimated weight in grams

    # Mapped nutrition values (per item)
    calories = Column(Float, default=0.0)
    protein = Column(Float, default=0.0)
    carbs = Column(Float, default=0.0)
    fats = Column(Float, default=0.0)
    sugar = Column(Float, default=0.0)
    fiber = Column(Float, default=0.0)
    sodium = Column(Float, default=0.0)
    calcium = Column(Float, default=0.0)
    iron = Column(Float, default=0.0)
    vitamin_c = Column(Float, default=0.0)
    folate = Column(Float, default=0.0)

    meal = relationship("Meal", back_populates="items")

class MealNutrition(Base):
    __tablename__ = "meal_nutritions"

    id = Column(Integer, primary_key=True, index=True)
    meal_id = Column(Integer, ForeignKey("meals.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Aggregated nutritional values for the entire meal
    calories = Column(Float, default=0.0)
    protein = Column(Float, default=0.0)
    carbs = Column(Float, default=0.0)
    fats = Column(Float, default=0.0)
    sugar = Column(Float, default=0.0)
    fiber = Column(Float, default=0.0)
    sodium = Column(Float, default=0.0)
    calcium = Column(Float, default=0.0)
    iron = Column(Float, default=0.0)
    vitamin_c = Column(Float, default=0.0)
    folate = Column(Float, default=0.0)

    meal = relationship("Meal", back_populates="nutrition")

class DiseasePrediction(Base):
    __tablename__ = "disease_predictions"

    id = Column(Integer, primary_key=True, index=True)
    meal_id = Column(Integer, ForeignKey("meals.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    diabetes_risk = Column(Float, default=0.0)
    obesity_risk = Column(Float, default=0.0)
    hypertension_risk = Column(Float, default=0.0)
    deficiency_risk = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    meal = relationship("Meal", back_populates="predictions")

class RiskFusionResult(Base):
    __tablename__ = "risk_fusion_results"

    id = Column(Integer, primary_key=True, index=True)
    meal_id = Column(Integer, ForeignKey("meals.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    fused_score = Column(Float, default=0.0)
    risk_level = Column(String, default="Low") # Low, Moderate, High, Critical
    created_at = Column(DateTime, default=datetime.utcnow)

    meal = relationship("Meal", back_populates="fusion_result")

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    meal_id = Column(Integer, ForeignKey("meals.id", ondelete="CASCADE"), nullable=False)
    content = Column(String, nullable=False)
    explanation = Column(String, nullable=False)
    category = Column(String, default="General") # General, Diabetes, Hypertension, Obesity, Deficiency
    created_at = Column(DateTime, default=datetime.utcnow)

    meal = relationship("Meal", back_populates="recommendations")

class DietHistory(Base):
    __tablename__ = "diet_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    meal_id = Column(Integer, ForeignKey("meals.id", ondelete="CASCADE"), unique=True, nullable=False)
    logged_date = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="diet_history")
    meal = relationship("Meal", back_populates="history_entry")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    action = Column(String, nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="audit_logs")

# Indexes
Index("idx_meal_user_created", Meal.user_id, Meal.created_at)
Index("idx_diet_history_user_logged", DietHistory.user_id, DietHistory.logged_date)
