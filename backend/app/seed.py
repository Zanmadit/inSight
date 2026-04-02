"""
Demo seed data. Run: cd backend && .venv/bin/python -m app.seed
(Docker: docker compose exec backend python -m app.seed)
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import delete

from app.database import AsyncSessionLocal
from app.models.admin_decision import AdminDecision
from app.models.applicant_profile import ApplicantProfile
from app.models.essay_review import EssayReview
from app.models.user import User
from app.services.auth_service import hash_password
from app.services.storage_service import ensure_bucket_exists, put_object_from_bytes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PASSWORD = "demo1234"

CRITERIA_NAMES = [
    "achievements",
    "extracurricular_activities",
    "leadership",
    "motivation",
    "growth_mindset",
    "clarity",
    "authenticity",
    "structure",
]


def _review_rows(scores: list[int]) -> list[dict]:
    status_map = {1: "weak", 2: "needs_work", 3: "average", 4: "good", 5: "excellent"}
    rows = []
    for crit, sc in zip(CRITERIA_NAMES, scores, strict=True):
        rows.append(
            {
                "criteria": crit,
                "score": sc,
                "max_score": 5,
                "status": status_map.get(sc, "average"),
                "recommendation": f"Demo feedback on {crit}.",
            }
        )
    return rows


def _calc_overall(scores: list[int]) -> Decimal:
    total = sum(scores)
    return Decimal(str(round((total / 40.0) * 10, 1)))


def _essay_long() -> str:
    return """When I started tenth grade, our school had no recycling programme. I asked teachers and classmates
why waste was simply thrown away, and nobody had a good answer. That question became a project. I formed a club,
recruited thirty students, and met the principal with a clear plan: bins, education slides, and weekly audits.
The first month was frustrating; students ignored the bins and custodians resisted change. Instead of quitting,
I listened, adjusted signs, and added friendly competitions between classes. By spring, diversion rates improved
and younger students asked to join.

Leading thirty peers taught me that motivation is not a speech; it is showing up when progress is invisible.
I learned to translate an environmental goal into daily habits and to celebrate small wins so burnout did not win.
The experience reshaped how I think about leadership: less about titles, more about accountability and empathy.

I want to study where ideas meet real communities. inVision U appeals to me because it values trajectory and
resilience as much as polish. I am excited to keep building programmes that make institutions kinder to people
and to the planet, and I hope to grow through rigorous coursework and mentorship that pushes my thinking beyond
what I already know."""


def _essay_short() -> str:
    return (
        "I want to go to university because it is important. I have worked hard in school and want a "
        "better future. I believe I can learn many things and become successful. Education opens doors "
        "and I am motivated to do my best every day for my family and my goals."
    )


async def main() -> None:
    await ensure_bucket_exists()

    async with AsyncSessionLocal() as db:
        await db.execute(delete(AdminDecision))
        await db.execute(delete(EssayReview))
        await db.execute(delete(ApplicantProfile))
        await db.execute(delete(User))
        await db.commit()

    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as db:
        admin = User(
            email="admin@invision.kz",
            password_hash=hash_password(PASSWORD),
            role="admin",
        )
        db.add(admin)
        await db.flush()

        applicants: list[
            tuple[str, dict]
        ] = [
            (
                "asel@example.kz",
                {
                    "full_name": "Asel Nurlanovna",
                    "iin": "040512345678",
                    "city": "Almaty",
                    "gpa": Decimal("4.80"),
                    "essay": _essay_long(),
                    "status": "submitted",
                    "locked": True,
                    "submitted_days_ago": 3,
                    "scores": [4, 4, 5, 5, 4, 4, 4, 4],
                    "strong": [
                        "Strong story of sustained initiative",
                        "Concrete example with thirty peers",
                        "Reflective insight on leadership",
                    ],
                    "weak": [
                        "Could quantify environmental outcomes further",
                        "Add academic connection to the project",
                        "Tighten opening hook",
                    ],
                    "final_sug": "Add one sentence connecting this work to your intended major.",
                    "final_ai": None,
                },
            ),
            (
                "bekzat@example.kz",
                {
                    "full_name": "Bekzat Akhmetov",
                    "iin": "030198765432",
                    "city": "Nur-Sultan",
                    "gpa": Decimal("3.20"),
                    "essay": _essay_short(),
                    "status": "submitted",
                    "locked": True,
                    "submitted_days_ago": 2,
                    "scores": [2, 2, 2, 3, 2, 2, 2, 3],
                    "strong": [
                        "States desire to pursue higher education",
                        "Acknowledges importance of effort",
                        "Message is easy to understand",
                    ],
                    "weak": [
                        "Lacks specific examples and outcomes",
                        "Arguments remain very generic",
                        "No clear narrative structure",
                    ],
                    "final_sug": "Replace broad claims with one detailed story from school or service.",
                    "final_ai": None,
                },
            ),
            (
                "dana@example.kz",
                {
                    "full_name": "Dana Seitkali",
                    "iin": None,
                    "city": "Shymkent",
                    "gpa": None,
                    "essay": None,
                    "status": "draft",
                    "locked": False,
                    "submitted_days_ago": None,
                    "scores": None,
                    "strong": None,
                    "weak": None,
                    "final_sug": None,
                    "final_ai": None,
                },
            ),
            (
                "marat@example.kz",
                {
                    "full_name": "Marat Dzhaksybekov",
                    "iin": "050011223344",
                    "city": "Karaganda",
                    "gpa": Decimal("4.50"),
                    "essay": _essay_long()[:800],
                    "status": "accepted",
                    "locked": True,
                    "submitted_days_ago": 10,
                    "scores": [5, 4, 5, 5, 5, 4, 5, 5],
                    "strong": [
                        "Exceptional specificity and initiative",
                        "Mature reflection on collaboration",
                        "Clear alignment with long-term goals",
                    ],
                    "weak": [
                        "Minor repetition in middle section",
                        "Could add quantitative metrics once more",
                        "Closing could link to programme resources",
                    ],
                    "final_sug": "Tighten the middle section to sharpen pacing.",
                    "final_ai": Decimal("82.5"),
                },
            ),
            (
                "ainur@example.kz",
                {
                    "full_name": "Ainur Bekova",
                    "iin": "060099887766",
                    "city": "Aktobe",
                    "gpa": Decimal("2.80"),
                    "essay": _essay_short(),
                    "status": "rejected",
                    "locked": True,
                    "submitted_days_ago": 8,
                    "scores": [2, 2, 2, 2, 2, 2, 2, 2],
                    "strong": [
                        "Clear interest in attending university",
                        "Polite and sincere tone",
                        "Identifies education as a goal",
                    ],
                    "weak": [
                        "Almost no concrete examples",
                        "Does not show depth of preparation",
                        "Needs stronger personal narrative",
                    ],
                    "final_sug": "Develop one narrative thread with obstacles and lessons learned.",
                    "final_ai": Decimal("38.0"),
                },
            ),
        ]

        profile_refs: list[tuple[ApplicantProfile, dict]] = []

        for email, meta in applicants:
            u = User(email=email, password_hash=hash_password(PASSWORD), role="applicant")
            db.add(u)
            await db.flush()
            prof = ApplicantProfile(user_id=u.id)
            prof.full_name = meta.get("full_name")
            prof.iin = meta.get("iin")
            prof.city = meta.get("city")
            prof.gpa = meta.get("gpa")
            prof.essay_text = meta.get("essay")
            prof.application_status = meta["status"]
            prof.is_locked = meta["locked"]
            if meta.get("submitted_days_ago") is not None:
                prof.submitted_at = now - timedelta(days=int(meta["submitted_days_ago"]))
            if meta.get("final_ai") is not None:
                prof.final_ai_score = meta["final_ai"]
                prof.ai_summary = (
                    "This candidate shows a mix of academic signals and narrative strength. "
                    "This score is advisory only. The final decision rests with the admissions committee."
                )
            if meta["status"] != "draft":
                vid = f"{u.id}/seed_{uuid.uuid4().hex[:8]}.mp4"
                tiny_mp4 = b"\x00\x00\x00\x20ftypmp41\x00\x00\x00\x00mp41isom" + b"\x00" * 400
                put_object_from_bytes(vid, tiny_mp4, content_type="video/mp4")
                prof.video_url = vid
                prof.video_filename = "intro.mp4"
                prof.video_transcript = (
                    "I care deeply about learning and community. I want to grow through mentorship and coursework."
                )
            db.add(prof)
            await db.flush()
            profile_refs.append((prof, meta))

        for prof, meta in profile_refs:
            scores = meta.get("scores")
            if not scores:
                continue
            overall = _calc_overall(scores)
            db.add(
                EssayReview(
                    applicant_profile_id=prof.id,
                    review_json=_review_rows(scores),
                    overall_score=overall,
                    summary_feedback="Demo essay review generated for seeded applicants.",
                    strongest_points=meta["strong"] or [],
                    weakest_points=meta["weak"] or [],
                    final_suggestion=meta["final_sug"] or "",
                )
            )

        marat = next(p for p, m in profile_refs if m["status"] == "accepted")
        ainur = next(p for p, m in profile_refs if m["status"] == "rejected")

        db.add(
            AdminDecision(
                applicant_profile_id=marat.id,
                decision="accepted",
                decision_note="Strong holistic profile.",
                decided_by=admin.id,
                decided_at=now - timedelta(days=1),
            )
        )
        db.add(
            AdminDecision(
                applicant_profile_id=ainur.id,
                decision="rejected",
                decision_note="Does not meet programme fit this cycle.",
                decided_by=admin.id,
                decided_at=now - timedelta(days=1),
            )
        )

        await db.commit()
    logger.info("Seed completed successfully.")


if __name__ == "__main__":
    asyncio.run(main())
