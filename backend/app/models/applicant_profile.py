import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.admin_decision import AdminDecision
    from app.models.essay_review import EssayReview
    from app.models.user import User


class ApplicantProfile(Base):
    __tablename__ = "applicant_profiles"
    __table_args__ = (
        CheckConstraint(
            "application_status IN ('draft','submitted','under_review','accepted','rejected')",
            name="ck_applicant_profiles_application_status",
        ),
        CheckConstraint("(gpa IS NULL) OR (gpa >= 0 AND gpa <= 5)", name="ck_applicant_profiles_gpa"),
        CheckConstraint(
            "(final_ai_score IS NULL) OR (final_ai_score >= 0 AND final_ai_score <= 100)",
            name="ck_applicant_profiles_final_ai_score",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    iin: Mapped[str | None] = mapped_column(String(12), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    gpa: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    essay_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    video_transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    application_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="draft"
    )
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    final_ai_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="applicant_profile")
    essay_reviews: Mapped[list["EssayReview"]] = relationship(
        back_populates="applicant_profile",
    )
    admin_decisions: Mapped[list["AdminDecision"]] = relationship(
        back_populates="applicant_profile",
    )
