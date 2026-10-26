"""users and audit_logs with row level security

Revision ID: 0001
Revises:
"""

import os
import re

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# Runtime role that receives table privileges. On Supabase, set APP_DB_ROLE to the API's role.
APP_ROLE = os.environ.get("APP_DB_ROLE", "jobpilot_app")
if not re.fullmatch(r"[a-z_][a-z0-9_]*", APP_ROLE):
    raise RuntimeError("APP_DB_ROLE must be a simple lowercase identifier")

CURRENT_USER_SQL = "nullif(current_setting('request.jwt.claim.sub', true), '')::uuid"


def upgrade() -> None:
    # Identity of the caller as set by the API for each transaction (see app/db/session.py).
    op.execute(
        f"""
        CREATE FUNCTION app_current_user_id() RETURNS uuid
        LANGUAGE sql STABLE AS $$ SELECT {CURRENT_USER_SQL} $$
        """
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("entity_type", sa.Text()),
        sa.Column("entity_id", sa.Text()),
        sa.Column(
            "details", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_user_id_created_at", "audit_logs", ["user_id", "created_at"])

    for table in ("users", "audit_logs"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")

    op.execute("CREATE POLICY users_select ON users FOR SELECT USING (id = app_current_user_id())")
    op.execute(
        "CREATE POLICY users_insert ON users FOR INSERT WITH CHECK (id = app_current_user_id())"
    )
    op.execute(
        "CREATE POLICY users_update ON users FOR UPDATE "
        "USING (id = app_current_user_id()) WITH CHECK (id = app_current_user_id())"
    )
    op.execute(
        "CREATE POLICY audit_select ON audit_logs FOR SELECT USING (user_id = app_current_user_id())"
    )
    op.execute(
        "CREATE POLICY audit_insert ON audit_logs FOR INSERT "
        "WITH CHECK (user_id = app_current_user_id())"
    )

    op.execute(f"GRANT SELECT, INSERT, UPDATE ON users TO {APP_ROLE}")
    # Append-only: no UPDATE or DELETE on audit_logs for the runtime role.
    op.execute(f"GRANT SELECT, INSERT ON audit_logs TO {APP_ROLE}")
    op.execute(f"GRANT EXECUTE ON FUNCTION app_current_user_id() TO {APP_ROLE}")


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("users")
    op.execute("DROP FUNCTION app_current_user_id()")
