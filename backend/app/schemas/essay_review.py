import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel


class EssayReviewApiResponse(BaseModel):
    id: uuid.UUID
    overall_score: Decimal
    summary_feedback: str
    review_json: list[dict[str, Any]]
    strongest_points: list[str]
    weakest_points: list[str]
    final_suggestion: str
    created_at: datetime

    model_config = {"from_attributes": True}
