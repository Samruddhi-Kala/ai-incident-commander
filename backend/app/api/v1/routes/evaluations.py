"""
Evaluation API Endpoints

Provides endpoints to list and query AI investigation evaluations.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.evaluation_service import EvaluationService
from app.schemas.evaluation import EvaluationListResponse, InvestigationEvaluationResponse

router = APIRouter()


@router.get(
    "",
    response_model=EvaluationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all investigation evaluations",
)
def list_evaluations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    List all investigation evaluations with pagination.
    """
    service = EvaluationService(db)
    items, total = service.list_evaluations(skip=skip, limit=limit)
    return EvaluationListResponse(
        items=[InvestigationEvaluationResponse.model_validate(item) for item in items],
        total=total,
    )
