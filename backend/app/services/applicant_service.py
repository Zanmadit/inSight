import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.applicant_profile import ApplicantProfile
from app.models.essay_review import EssayReview
from app.models.user import User
from app.schemas.applicant import AdminApplicantProfileOut, ApplicantProfileOut, EssayReviewOut
from app.services import ai_pipeline
from app.services.storage_service import presigned_get_url

logger = logging.getLogger(__name__)

ACCEPTED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}


async def get_or_create_profile(db: AsyncSession, user: User) -> ApplicantProfile:
    result = await db.execute(select(ApplicantProfile).where(ApplicantProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if profile is None:
        profile = ApplicantProfile(user_id=user.id)
        db.add(profile)
        await db.flush()
        await db.refresh(profile)
    return profile


async def latest_essay_review(
    db: AsyncSession, profile_id: uuid.UUID
) -> EssayReview | None:
    q = (
        select(EssayReview)
        .where(EssayReview.applicant_profile_id == profile_id)
        .order_by(EssayReview.created_at.desc())
        .limit(1)
    )
    result = await db.execute(q)
    return result.scalar_one_or_none()


def profile_to_out(profile: ApplicantProfile, latest: EssayReview | None) -> ApplicantProfileOut:
    return ApplicantProfileOut(
        id=profile.id,
        user_id=profile.user_id,
        full_name=profile.full_name,
        iin=profile.iin,
        city=profile.city,
        gpa=profile.gpa,
        essay_text=profile.essay_text,
        video_url=profile.video_url,
        video_filename=profile.video_filename,
        application_status=profile.application_status,
        is_locked=profile.is_locked,
        submitted_at=profile.submitted_at,
        final_ai_score=profile.final_ai_score,
        ai_summary=profile.ai_summary,
        latest_essay_review=EssayReviewOut.model_validate(latest) if latest else None,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def profile_to_admin_out(
    profile: ApplicantProfile, latest: EssayReview | None
) -> AdminApplicantProfileOut:
    base = profile_to_out(profile, latest)
    return AdminApplicantProfileOut(
        **base.model_dump(),
        video_transcript=profile.video_transcript,
    )


async def ensure_not_locked(profile: ApplicantProfile) -> None:
    from fastapi import HTTPException, status

    if profile.is_locked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Application is locked")


def validate_submit(profile: ApplicantProfile, has_review: bool) -> str | None:
    if not (profile.full_name and profile.full_name.strip()):
        return "Full name is required."
    if not (profile.iin and profile.iin.strip()):
        return "IIN is required."
    if not (profile.city and profile.city.strip()):
        return "City is required."
    if profile.gpa is None:
        return "GPA is required."
    et = profile.essay_text or ""
    if len(et.strip()) < 100:
        return "Essay must be at least 100 characters."
    if not (profile.video_url and profile.video_url.strip()):
        return "Video upload is required."
    if not has_review:
        return "At least one essay review is required before submission."
    return None


async def run_background_scoring(profile_id: uuid.UUID) -> None:
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(ApplicantProfile).where(ApplicantProfile.id == profile_id)
            )
            profile = result.scalar_one_or_none()
            if profile is None:
                return
            er = await latest_essay_review(db, profile_id)
            review_dict: dict = {}
            if er:
                review_dict = {
                    "overall_score": float(er.overall_score),
                    "review_json": er.review_json,
                }
            gpa_f = float(profile.gpa) if profile.gpa is not None else None
            transcript = profile.video_transcript
            try:
                out = await ai_pipeline.run_candidate_scoring_graph(
                    str(profile_id),
                    profile.essay_text or "",
                    gpa_f,
                    transcript,
                    review_dict,
                )
                profile.final_ai_score = Decimal(str(out["final_ai_score"]))
                profile.ai_summary = out.get("ai_summary") or ""
            except Exception as e:
                logger.exception("Background scoring failed for %s: %s", profile_id, e)
                profile.final_ai_score = None
                profile.ai_summary = "AI scoring failed. Please contact support."
            await db.commit()
        except Exception:
            await db.rollback()
            logger.exception("Background scoring session error for %s", profile_id)
