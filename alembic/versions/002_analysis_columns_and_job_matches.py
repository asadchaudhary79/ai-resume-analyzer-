"""Add analysis columns and job_matches table

Revision ID: 002
Revises: 001
Create Date: 2025-02-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("analyses", sa.Column("ats_keywords_missing", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("analyses", sa.Column("experience_level", sa.String(32), nullable=True))
    op.create_table(
        "job_matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_description", sa.Text(), nullable=False),
        sa.Column("match_score", sa.Integer(), nullable=False),
        sa.Column("matched_keywords", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("missing_keywords", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("should_apply", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("job_matches")
    op.drop_column("analyses", "experience_level")
    op.drop_column("analyses", "ats_keywords_missing")
