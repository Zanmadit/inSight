import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel

from app.schemas.applicant import AdminApplicantProfileOut, EssayReviewOut


class StatsResponse(BaseModel):
    total: int
    draft: int
    submitted: int
    under_review: int
    accepted: int
    rejected: int


class ApplicantListItem(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    email: str
    full_name: str | None
    city: str | None
    gpa: Decimal | None
    application_status: str
    final_ai_score: Decimal | None
    submitted_at: datetime | None
    created_at: datetime


class ApplicantListResponse(BaseModel):
    items: list[ApplicantListItem]
    total: int
    page: int
    page_size: int


class AdminDecisionOut(BaseModel):
    id: uuid.UUID
    applicant_profile_id: uuid.UUID
    decision: str
    decision_note: str | None
    decided_by: uuid.UUID
    decided_at: datetime

    model_config = {"from_attributes": True}


class ApplicantDetailResponse(BaseModel):
    profile: AdminApplicantProfileOut
    email: str
    essay_reviews: list[EssayReviewOut]
    latest_decision: AdminDecisionOut | None
    video_presigned_url: str | None
    essay_component_score: Decimal | None = None
    video_component_score: Decimal | None = None
    profile_component_score: Decimal | None = None


class StatusPatchBody(BaseModel):
    status: Literal["under_review", "accepted", "rejected"]
    decision_note: str | None = None
