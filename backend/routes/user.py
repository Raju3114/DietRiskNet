from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List
from backend.database.database import get_db
from backend.routes.deps import get_current_user
from backend.database.models import User
from backend.schemas.schemas import (
    DashboardResponse, UserProfileResponse, UserSettingResponse, 
    UserSettingUpdate, LongitudinalTrendsResponse
)
from backend.services.user_services import (
    profile_service, dashboard_service, history_service, analytics_service
)
from backend.utils.logger import api_logger

router = APIRouter(prefix="", tags=["User & Dashboard"])

@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        data = dashboard_service.get_dashboard_data(current_user.id, db)
        return data
    except Exception as e:
        api_logger.error(f"Dashboard load error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load dashboard metrics.")

@router.get("/history", response_model=List[dict])
def get_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return history_service.get_history(current_user.id, db)
    except Exception as e:
        api_logger.error(f"History load error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load history logs.")

@router.get("/profile", response_model=UserProfileResponse)
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        # Load profile and settings
        profile = profile_service.get_profile(current_user.id, db)
        # Touch settings to ensure created
        profile_service.get_settings(current_user.id, db)
        db.refresh(profile)
        return profile
    except Exception as e:
        api_logger.error(f"Profile load error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load profile details.")

@router.put("/profile", response_model=UserProfileResponse)
def update_profile(
    full_name: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        profile_service.update_profile(current_user.id, full_name, db)
        profile = profile_service.get_profile(current_user.id, db)
        return profile
    except Exception as e:
        api_logger.error(f"Profile update error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update profile.")

@router.put("/settings", response_model=UserSettingResponse)
def update_settings(
    data: UserSettingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        settings_db = profile_service.update_settings(current_user.id, data, db)
        return settings_db
    except Exception as e:
        api_logger.error(f"Settings update error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update settings.")

@router.get("/analytics/trends", response_model=LongitudinalTrendsResponse)
def get_trends(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        trends = analytics_service.get_trends(current_user.id, days, db)
        return {"trends": trends}
    except Exception as e:
        api_logger.error(f"Trends analytics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to compile longitudinal analytics.")
