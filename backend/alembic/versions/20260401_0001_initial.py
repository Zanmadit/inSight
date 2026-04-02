"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("role IN ('applicant', 'admin')", name="ck_users_role"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "applicant_profiles",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("iin", sa.String(length=12), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("gpa", sa.Numeric(3, 2), nullable=True),
        sa.Column("essay_text", sa.Text(), nullable=True),
        sa.Column("video_url", sa.Text(), nullable=True),
        sa.Column("video_filename", sa.String(length=255), nullable=True),
        sa.Column("video_transcript", sa.Text(), nullable=True),
        sa.Column("application_status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column("is_locked", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("final_ai_score", sa.Numeric(4, 1), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "application_status IN ('draft','submitted','under_review','accepted','rejected')",
            name="ck_applicant_profiles_application_status",
        ),
        sa.CheckConstraint(
            "(gpa IS NULL) OR (gpa >= 0 AND gpa <= 5)",
            name="ck_applicant_profiles_gpa",
        ),
        sa.CheckConstraint(
            "(final_ai_score IS NULL) OR (final_ai_score >= 0 AND final_ai_score <= 100)",
            name="ck_applicant_profiles_final_ai_score",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "essay_reviews",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("applicant_profile_id", sa.UUID(), nullable=False),
        sa.Column("review_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("overall_score", sa.Numeric(3, 1), nullable=False),
        sa.Column("summary_feedback", sa.Text(), nullable=False),
        sa.Column("strongest_points", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("weakest_points", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("final_suggestion", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["applicant_profile_id"], ["applicant_profiles.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "admin_decisions",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("applicant_profile_id", sa.UUID(), nullable=False),
        sa.Column("decision", sa.String(length=20), nullable=False),
        sa.Column("decision_note", sa.Text(), nullable=True),
        sa.Column("decided_by", sa.UUID(), nullable=False),
        sa.Column(
            "decided_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "decision IN ('under_review','accepted','rejected')",
            name="ck_admin_decisions_decision",
        ),
        sa.ForeignKeyConstraint(
            ["applicant_profile_id"], ["applicant_profiles.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["decided_by"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("admin_decisions")
    op.drop_table("essay_reviews")
    op.drop_table("applicant_profiles")
    op.drop_table("users")
