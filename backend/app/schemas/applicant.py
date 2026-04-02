import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class EssayReviewOut(BaseModel):
    id: uuid.UUID
    overall_score: Decimal
    summary_feedback: str
    review_json: list[dict[str, Any]]
    strongest_points: list[str]
    weakest_points: list[str]
    final_suggestion: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ApplicantProfileOut(BaseModel):
    """Applicant-facing profile shape (§7.2) — no video_transcript."""

    id: uuid.UUID
    user_id: uuid.UUID
    full_name: str | None
    iin: str | None
    city: str | None
    gpa: Decimal | None
    essay_text: str | None
    video_url: str | None
    video_filename: str | None
    application_status: str
    is_locked: bool
    submitted_at: datetime | None
    final_ai_score: Decimal | None
    ai_summary: str | None
    latest_essay_review: EssayReviewOut | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AdminApplicantProfileOut(ApplicantProfileOut):
    """Full profile for admin card including Whisper transcript."""

    video_transcript: str | None = None


class ProfilePatch(BaseModel):
    full_name: str | None = None
    iin: str | None = None
    city: str | None = None
    gpa: Decimal | None = Field(default=None, ge=0, le=5)


class EssayPatch(BaseModel):
    essay_text: str


class VideoUploadResponse(BaseModel):
    video_url: str
    video_filename: str
    message: str = "Video uploaded. Transcription in progress."


class PresignedVideoResponse(BaseModel):
    presigned_url: str | None


class SubmitResponse(BaseModel):
    message: str = "Your application has been submitted successfully. Editing is now disabled."
    submitted_at: datetime
