import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.applicant_profile import ApplicantProfile


class EssayReview(Base):
    __tablename__ = "essay_reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    applicant_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applicant_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    review_json: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    overall_score: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False)
    summary_feedback: Mapped[str] = mapped_column(Text, nullable=False)
    strongest_points: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    weakest_points: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    final_suggestion: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    applicant_profile: Mapped["ApplicantProfile"] = relationship(back_populates="essay_reviews")
