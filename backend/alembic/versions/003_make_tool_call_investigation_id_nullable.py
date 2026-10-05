"""Make tool_calls investigation_id nullable

Revision ID: 003_make_tool_call_investigation_id_nullable
Revises: 002_create_core_tables
Create Date: 2026-10-05 15:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_tool_call_inv_nullable'
down_revision: Union[str, None] = '002_create_core_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'tool_calls',
        'investigation_id',
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        'tool_calls',
        'investigation_id',
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
