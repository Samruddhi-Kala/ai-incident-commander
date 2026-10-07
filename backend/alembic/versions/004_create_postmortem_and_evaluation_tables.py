"""Create postmortems and investigation_evaluations tables

Revision ID: 004_postmortem_eval
Revises: 003_tool_call_inv_nullable
Create Date: 2026-10-07 17:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004_postmortem_eval'
down_revision: Union[str, None] = '003_tool_call_inv_nullable'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. postmortems
    op.create_table(
        'postmortems',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('investigation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('investigations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('impact', sa.Text(), nullable=False),
        sa.Column('timeline', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('root_cause', sa.Text(), nullable=False),
        sa.Column('contributing_factors', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('remediation', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('lessons_learned', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('preventive_actions', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('idx_postmortems_investigation_id', 'postmortems', ['investigation_id'], unique=True)

    # 2. investigation_evaluations
    op.create_table(
        'investigation_evaluations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('investigation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('investigations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('evidence_score', sa.Float(), nullable=False),
        sa.Column('hypothesis_score', sa.Float(), nullable=False),
        sa.Column('verification_score', sa.Float(), nullable=False),
        sa.Column('rag_score', sa.Float(), nullable=False),
        sa.Column('tool_efficiency_score', sa.Float(), nullable=False),
        sa.Column('evaluation_reasoning', sa.Text(), nullable=False),
        sa.Column('metrics_breakdown', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('idx_evaluations_investigation_id', 'investigation_evaluations', ['investigation_id'])


def downgrade() -> None:
    op.drop_index('idx_evaluations_investigation_id', table_name='investigation_evaluations')
    op.drop_table('investigation_evaluations')
    op.drop_index('idx_postmortems_investigation_id', table_name='postmortems')
    op.drop_table('postmortems')
