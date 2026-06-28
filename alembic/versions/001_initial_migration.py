"""initial migration

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column(
            "preferred_study_time",
            sa.Enum("Morning", "Afternoon", "Night", name="studytimepreference"),
            nullable=False,
            server_default="Morning",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # ── study_plans ───────────────────────────────────────────────────────────
    op.create_table(
        "study_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("subjects", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("exam_date", sa.DateTime(), nullable=False),
        sa.Column("daily_study_hours", sa.Float(), nullable=False),
        sa.Column(
            "difficulty",
            sa.Enum("Easy", "Medium", "Hard", name="difficulty"),
            nullable=False,
        ),
        sa.Column("ai_explanation", sa.Text(), nullable=True),
        sa.Column("study_tips", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_study_plans_id"), "study_plans", ["id"], unique=False)

    # ── study_tasks ───────────────────────────────────────────────────────────
    op.create_table(
        "study_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("subject", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("duration_hours", sa.Float(), nullable=False),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["study_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_study_tasks_id"), "study_tasks", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_study_tasks_id"), table_name="study_tasks")
    op.drop_table("study_tasks")

    op.drop_index(op.f("ix_study_plans_id"), table_name="study_plans")
    op.drop_table("study_plans")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS difficulty")
    op.execute("DROP TYPE IF EXISTS studytimepreference")
