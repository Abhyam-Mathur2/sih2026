from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_reviewer
from app.db.session import get_db
from app.models.material_match import MatchStatus, MatchType
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.material_match import MatchDetailRead, MatchRead, MatchReview, TriggerMatchRequest
from app.services import match_service

router = APIRouter()


@router.get("", response_model=PaginatedResponse[MatchDetailRead], summary="List matches")
async def list_matches(
    status: MatchStatus | None = Query(None),
    match_type: MatchType | None = Query(None),
    source_material_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[MatchDetailRead]:
    skip = (page - 1) * size
    items, total = await match_service.list_matches(
        db,
        status=status,
        match_type=match_type,
        source_material_id=source_material_id,
        skip=skip,
        limit=size,
    )
    return PaginatedResponse.create(
        items=[MatchDetailRead.model_validate(m) for m in items],
        total=total, page=page, size=size,
    )


@router.get("/{match_id}", response_model=MatchDetailRead, summary="Get match details")
async def get_match(
    match_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> MatchDetailRead:
    match = await match_service.get_match(db, match_id)
    return MatchDetailRead.model_validate(match)


@router.post("/{match_id}/review", response_model=MatchRead, summary="Review (approve/reject) a match")
async def review_match(
    match_id: int,
    payload: MatchReview,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> MatchRead:
    match = await match_service.review_match(
        db,
        match_id=match_id,
        action=payload.action,
        reviewer=current_user,
        comment=payload.reviewer_comment,
        modified_score=payload.modified_score,
    )
    return MatchRead.model_validate(match)

@router.post("/{match_id}/approve", response_model=MatchRead)
async def approve_match(match_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_reviewer)) -> MatchRead:
    return MatchRead.model_validate(await match_service.review_match(db, match_id, MatchStatus.APPROVED, user))

@router.post("/{match_id}/reject", response_model=MatchRead)
async def reject_match(match_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_reviewer)) -> MatchRead:
    return MatchRead.model_validate(await match_service.review_match(db, match_id, MatchStatus.REJECTED, user))


@router.post("/trigger", response_model=list[MatchRead], status_code=201, summary="Trigger AI matching for a material")
async def trigger_matching(
    payload: TriggerMatchRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_reviewer),
) -> list[MatchRead]:
    matches = await match_service.trigger_matching_for_material(db, payload.material_id, payload.top_k)
    return [MatchRead.model_validate(m) for m in matches]


@router.post("/batch-detect", status_code=200, summary="Batch duplicate detection across all materials")
async def batch_detect(
    top_k: int = Query(10, ge=1, le=50),
    min_score: float = Query(60.0, ge=0, le=100),
    limit_materials: int = Query(500, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_reviewer),
) -> dict:
    return await match_service.batch_detect_duplicates(
        db, top_k=top_k, min_score=min_score, limit_materials=limit_materials
    )
