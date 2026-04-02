from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_admin
from app.models.admin_decision import AdminDecision
from app.models.applicant_profile import ApplicantProfile
from app.models.essay_review import EssayReview
from app.models.user import User
from app.schemas.admin import (
    ApplicantDetailResponse,
    ApplicantListItem,
    ApplicantListResponse,
    AdminDecisionOut,
    StatsResponse,
    StatusPatchBody,
)
from app.schemas.applicant import AdminApplicantProfileOut, EssayReviewOut
from app.services import applicant_service
from app.services.storage_service import presigned_get_url

router = APIRouter()


@router.get("/stats", response_model=StatsResponse)
async def stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
):
    base = select(ApplicantProfile.application_status, func.count()).group_by(
        ApplicantProfile.application_status
    )
    result = await db.execute(base)
    rows = {r[0]: r[1] for r in result.all()}
    total = sum(rows.values())
    return StatsResponse(
        total=total,
        draft=rows.get("draft", 0),
        submitted=rows.get("submitted", 0),
        under_review=rows.get("under_review", 0),
        accepted=rows.get("accepted", 0),
        rejected=rows.get("rejected", 0),
    )


@router.get("/applicants", response_model=ApplicantListResponse)
async def list_applicants(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    q = select(ApplicantProfile, User.email).join(User, User.id == ApplicantProfile.user_id).where(
        User.role == "applicant"
    )
    if status_filter:
        q = q.where(ApplicantProfile.application_status == status_filter)
    if search and search.strip():
        term = f"%{search.strip()}%"
        q = q.where(or_(User.email.ilike(term), ApplicantProfile.full_name.ilike(term)))
    count_base = (
        select(func.count())
        .select_from(ApplicantProfile)
        .join(User, User.id == ApplicantProfile.user_id)
        .where(User.role == "applicant")
    )
    if status_filter:
        count_base = count_base.where(ApplicantProfile.application_status == status_filter)
    if search and search.strip():
        term = f"%{search.strip()}%"
        count_base = count_base.where(
            or_(User.email.ilike(term), ApplicantProfile.full_name.ilike(term))
        )
    total = (await db.execute(count_base)).scalar_one()
    q = q.offset((page - 1) * page_size).limit(page_size).order_by(ApplicantProfile.created_at.desc())
    result = await db.execute(q)
    items: list[ApplicantListItem] = []
    for row, email in result.all():
        items.append(
            ApplicantListItem(
                id=row.id,
                user_id=row.user_id,
                email=email,
                full_name=row.full_name,
                city=row.city,
                gpa=row.gpa,
                application_status=row.application_status,
                final_ai_score=row.final_ai_score,
                submitted_at=row.submitted_at,
                created_at=row.created_at,
            )
        )
    return ApplicantListResponse(items=items, total=total, page=page, page_size=page_size)


def _compute_components(
    profile: ApplicantProfile, latest: EssayReview | None
) -> tuple[Decimal | None, Decimal | None, Decimal | None]:
    if profile.final_ai_score is None:
        return None, None, None
    essay_c = None
    if latest:
        essay_c = Decimal(str(round((float(latest.overall_score) / 10.0) * 50, 1)))
    if profile.gpa is not None:
        prof_c = Decimal(str(round(min((float(profile.gpa) / 5.0) * 20.0, 20.0), 1)))
    else:
        prof_c = Decimal("10.0")
    final = float(profile.final_ai_score)
    if essay_c is not None:
        video_c = Decimal(str(round(final - float(essay_c) - float(prof_c), 1)))
    else:
        video_c = None
    return essay_c, video_c, prof_c


@router.get("/applicants/{profile_id}", response_model=ApplicantDetailResponse)
async def get_applicant(
    profile_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
):
    q = (
        select(ApplicantProfile, User.email)
        .join(User, User.id == ApplicantProfile.user_id)
        .where(ApplicantProfile.id == profile_id)
    )
    row = (await db.execute(q)).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Applicant not found")
    profile, email = row
    rev_q = (
        select(EssayReview)
        .where(EssayReview.applicant_profile_id == profile_id)
        .order_by(EssayReview.created_at.desc())
    )
    reviews = (await db.execute(rev_q)).scalars().all()
    latest = reviews[0] if reviews else None
    dec_q = (
        select(AdminDecision)
        .where(AdminDecision.applicant_profile_id == profile_id)
        .order_by(AdminDecision.decided_at.desc())
        .limit(1)
    )
    latest_dec = (await db.execute(dec_q)).scalar_one_or_none()
    essay_c, video_c, prof_c = _compute_components(profile, latest)
    return ApplicantDetailResponse(
        profile=applicant_service.profile_to_admin_out(profile, latest),
        email=email,
        essay_reviews=[EssayReviewOut.model_validate(r) for r in reviews],
        latest_decision=AdminDecisionOut.model_validate(latest_dec) if latest_dec else None,
        video_presigned_url=presigned_get_url(profile.video_url),
        essay_component_score=essay_c,
        video_component_score=video_c,
        profile_component_score=prof_c,
    )


@router.patch("/applicants/{profile_id}/status", response_model=AdminApplicantProfileOut)
async def patch_status(
    profile_id: UUID,
    body: StatusPatchBody,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
):
    if body.status in ("draft", "submitted"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status for admin update. Use under_review, accepted, or rejected.",
        )
    result = await db.execute(select(ApplicantProfile).where(ApplicantProfile.id == profile_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Applicant not found")
    profile.application_status = body.status
    decision = AdminDecision(
        applicant_profile_id=profile.id,
        decision=body.status,
        decision_note=body.decision_note,
        decided_by=admin.id,
    )
    db.add(decision)
    await db.flush()
    await db.refresh(profile)
    latest = await applicant_service.latest_essay_review(db, profile.id)
    return applicant_service.profile_to_admin_out(profile, latest)