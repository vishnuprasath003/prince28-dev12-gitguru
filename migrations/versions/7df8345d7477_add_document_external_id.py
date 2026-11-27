"""add document external id

Revision ID: 7df8345d7477
Revises: a5356c5c9b92
Create Date: 2026-11-27 13:57:02.760378
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7df8345d7477"
down_revision: str | Sequence[str] | None = "a5356c5c9b92"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add the column temporarily as nullable
    op.add_column(
        "documents",
        sa.Column("external_id", sa.String(length=24), nullable=True),
    )

    # 2. Backfill existing documents using their SHA-256 hash
    op.execute(
        """
        UPDATE documents
        SET external_id = 'f-' || SUBSTRING(sha256 FROM 1 FOR 20)
        WHERE external_id IS NULL
        """
    )

    # 3. Make the column NOT NULL after backfill
    op.alter_column(
        "documents",
        "external_id",
        existing_type=sa.String(length=24),
        nullable=False,
    )

    # 4. Create unique index
    op.create_index(
        op.f("ix_documents_external_id"),
        "documents",
        ["external_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_documents_external_id"),
        table_name="documents",
    )

    op.drop_column("documents", "external_id")
