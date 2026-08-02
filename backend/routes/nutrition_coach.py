"""Personalized AI Nutrition Coach endpoints.

``GET /api/nutrition/analytics`` — deterministic dietary analytics
(averages, DCI/NIS, risk trend, patterns, goals progress) computed from
stored meal history.  No ML re-run, no LLM call — fast and reliable.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import User
from backend.routes.deps import get_current_user
from backend.services.nutrition_assistant_service import (
    nutrition_assistant_service,
)

router = APIRouter(prefix="", tags=["AI Nutrition Coach"])


@router.get("/nutrition/analytics")
def nutrition_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Return the user's dietary analytics (weekly summary + patterns)."""
    analytics = nutrition_assistant_service.get_analytics(db, current_user.id)
    return {"analytics": analytics}
