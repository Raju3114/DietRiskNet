"""Meal report download endpoint.

``GET /api/report/{meal_id}`` returns a professionally formatted PDF of
the meal analysis (image, foods, nutrition, health analysis, AI
Dietitian).  The report is generated from the PERSISTED analysis — no ML
is re-run.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import User
from backend.routes.deps import get_current_user
from backend.services.report_service import ReportNotFoundError, report_service
from backend.utils.logger import api_logger

router = APIRouter(prefix="", tags=["Reports"])


@router.get("/report/{meal_id}")
def download_report(
    meal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    try:
        pdf_bytes = report_service.generate_report(
            db,
            user_id=current_user.id,
            meal_id=meal_id,
        )
    except ReportNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal not found for the current user.",
        )
    except Exception as exc:
        api_logger.error("Report generation failed (meal_id=%s): %s", meal_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate the meal report.",
        )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="dietrisknet-meal-{meal_id}.pdf"'
            )
        },
    )
