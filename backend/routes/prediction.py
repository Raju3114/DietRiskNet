from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.routes.deps import get_current_user
from backend.database.models import User
from backend.schemas.schemas import (
    DiseasePredictionRequest, DiseasePredictionResponse,
    RiskFusionRequest, RiskFusionResponse,
    ExplainDietRequest, ExplainDietResponse
)
from backend.services.prediction_service import prediction_service as pred_service
from backend.services.risk_fusion_service import fusion_service as rf_service
from backend.services.recommendation_service import explain_diet_service as rec_service
from backend.utils.logger import api_logger

router = APIRouter(prefix="", tags=["ML Predictions & Recommendations"])

@router.post("/predict-diabetes", response_model=DiseasePredictionResponse)
def predict_diabetes(data: DiseasePredictionRequest):
    try:
        risk = pred_service.predict_diabetes(
            data.age, data.gender, data.weight / ((data.height/100)**2) if data.height > 0 else 22.0, data.existing_conditions
        )
        # Dummy fill others for consistency
        return {"diabetes_risk": risk, "obesity_risk": 0.0, "hypertension_risk": 0.0, "deficiency_risk": 0.0}
    except Exception as e:
        api_logger.error(f"Diabetes prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict-obesity", response_model=DiseasePredictionResponse)
def predict_obesity(data: DiseasePredictionRequest):
    try:
        bmi = data.weight / ((data.height/100)**2) if data.height > 0 else 22.0
        risk = pred_service.predict_obesity(
            data.age, data.gender, data.height, data.weight, bmi, data.meal_nutrition.dict()
        )
        return {"diabetes_risk": 0.0, "obesity_risk": risk, "hypertension_risk": 0.0, "deficiency_risk": 0.0}
    except Exception as e:
        api_logger.error(f"Obesity prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict-hypertension", response_model=DiseasePredictionResponse)
def predict_hypertension(data: DiseasePredictionRequest):
    try:
        bmi = data.weight / ((data.height/100)**2) if data.height > 0 else 22.0
        risk = pred_service.predict_hypertension(
            data.age, bmi, data.meal_nutrition.dict(), data.existing_conditions
        )
        return {"diabetes_risk": 0.0, "obesity_risk": 0.0, "hypertension_risk": risk, "deficiency_risk": 0.0}
    except Exception as e:
        api_logger.error(f"Hypertension prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict-deficiency", response_model=DiseasePredictionResponse)
def predict_deficiency(data: DiseasePredictionRequest):
    try:
        bmi = data.weight / ((data.height/100)**2) if data.height > 0 else 22.0
        risk = pred_service.predict_deficiency(
            data.age, data.gender, bmi, data.meal_nutrition.dict(), data.existing_conditions
        )
        return {"diabetes_risk": 0.0, "obesity_risk": 0.0, "hypertension_risk": 0.0, "deficiency_risk": risk}
    except Exception as e:
        api_logger.error(f"Deficiency prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/risk-fusion", response_model=RiskFusionResponse)
def risk_fusion(data: RiskFusionRequest):
    try:
        fused_score, risk_level = rf_service.fuse(
            data.dci, data.nis,
            data.disease_prediction.diabetes_risk,
            data.disease_prediction.obesity_risk,
            data.disease_prediction.hypertension_risk,
            data.disease_prediction.deficiency_risk
        )
        return {"fused_score": fused_score, "risk_level": risk_level}
    except Exception as e:
        api_logger.error(f"Risk fusion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/explain-diet", response_model=ExplainDietResponse)
def explain_diet(data: ExplainDietRequest):
    try:
        recs = rec_service.recommend(
            data.meal_nutrition.dict(),
            data.disease_prediction.dict(),
            data.dci, data.nis,
            data.history_summary
        )
        return {"recommendations": recs}
    except Exception as e:
        api_logger.error(f"Explain diet error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
