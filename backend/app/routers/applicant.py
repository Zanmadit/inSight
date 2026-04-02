from datetime import datetime, timezone
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_applicant
from app.models.applicant_profile import ApplicantProfile
from app.models.essay_review import EssayReview
from app.models.user import User
from app.schemas.applicant import (
    ApplicantProfileOut,
    EssayPatch,
    PresignedVideoResponse,
    ProfilePatch,
    SubmitResponse,
    VideoUploadResponse,
)
from app.schemas.essay_review import EssayReviewApiResponse
from app.services import applicant_service
from app.services.ai_pipeline import AIServiceUnavailableError, run_essay_review_graph
from app.services.storage_service import build_object_key, presigned_get_url, put_object_from_bytes
from app.services.whisper_service import transcribe_and_save_profile

router = APIRouter()
MAX_VIDEO_BYTES = 200 * 1024 * 1024


@router.get("/profile", response_model=ApplicantProfileOut)
async def get_profile(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_applicant)],
):
    profile = await applicant_service.get_or_create_profile(db, user)
    latest = await applicant_service.latest_essay_review(db, profile.id)
    return applicant_service.profile_to_out(profile, latest)


@router.patch("/profile", response_model=ApplicantProfileOut)
async def patch_profile(
    body: ProfilePatch,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_applicant)],
):
    profile = await applicant_service.get_or_create_profile(db, user)
    await applicant_service.ensure_not_locked(profile)
    if body.full_name is not None:
        profile.full_name = body.full_name
    if body.iin is not None:
        profile.iin = body.iin
    if body.city is not None:
        profile.city = body.city
    if body.gpa is not None:
        profile.gpa = body.gpa
    await db.flush()
    await db.refresh(profile)
    latest = await applicant_service.latest_essay_review(db, profile.id)
    return applicant_service.profile_to_out(profile, latest)


@router.patch("/essay", response_model=ApplicantProfileOut)
async def patch_essay(
    body: EssayPatch,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_applicant)],
):
    profile = await applicant_service.get_or_create_profile(db, user)
    await applicant_service.ensure_not_locked(profile)
    profile.essay_text = body.essay_text
    await db.flush()
    await db.refresh(profile)
    latest = await applicant_service.latest_essay_review(db, profile.id)
    return applicant_service.profile_to_out(profile, latest)


@router.post("/video", response_model=VideoUploadResponse)
async def upload_video(
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_applicant)],
    file: UploadFile = File(...),
):
    profile = await applicant_service.get_or_create_profile(db, user)
    await applicant_service.ensure_not_locked(profile)
    ct = file.content_type or ""
    if ct not in applicant_service.ACCEPTED_VIDEO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported video format. Use MP4, WebM, or QuickTime.",
        )
    total = 0
    chunks: list[bytes] = []
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_VIDEO_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Video file exceeds maximum size of 200MB",
            )
        chunks.append(chunk)
    data = b"".join(chunks)
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
    key = build_object_key(user.id, file.filename or "video.mp4")
    put_object_from_bytes(key, data, content_type=ct)
    profile.video_url = key
    profile.video_filename = file.filename
    await db.flush()
    await db.refresh(profile)
    background_tasks.add_task(transcribe_and_save_profile, profile.id, key)
    return VideoUploadResponse(video_url=key, video_filename=file.filename or "")


@router.get("/video-url", response_model=PresignedVideoResponse)
async def video_url(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_applicant)],
):
    profile = await applicant_service.get_or_create_profile(db, user)
    url = presigned_get_url(profile.video_url)
    return PresignedVideoResponse(presigned_url=url)


@router.post("/essay/review", response_model=EssayReviewApiResponse)
async def essay_review(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_applicant)],
):
    profile = await applicant_service.get_or_create_profile(db, user)
    await applicant_service.ensure_not_locked(profile)
    text = profile.essay_text or ""
    if len(text.strip()) < 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Essay must be at least 100 characters for AI review.",
        )
    try:
        out = await run_essay_review_graph(text)
    except AIServiceUnavailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    row = EssayReview(
        applicant_profile_id=profile.id,
        review_json=out["review_json"],
        overall_score=out["overall_score"],
        summary_feedback=out["summary_feedback"],
        strongest_points=out["strongest_points"],
        weakest_points=out["weakest_points"],
        final_suggestion=out["final_suggestion"],
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return EssayReviewApiResponse.model_validate(row)


@router.post("/submit", response_model=SubmitResponse)
async def submit(
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_applicant)],
):
    profile = await applicant_service.get_or_create_profile(db, user)
    await applicant_service.ensure_not_locked(profile)
    res = await db.execute(
        select(EssayReview.id)
        .where(EssayReview.applicant_profile_id == profile.id)
        .limit(1)
    )
    has_review = res.scalar_one_or_none() is not None
    err = applicant_service.validate_submit(profile, has_review)
    if err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err)
    now = datetime.now(timezone.utc)
    profile.is_locked = True
    profile.application_status = "submitted"
    profile.submitted_at = now
    await db.flush()
    background_tasks.add_task(applicant_service.run_background_scoring, profile.id)
    return SubmitResponse(submitted_at=now)
