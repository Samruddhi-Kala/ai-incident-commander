"""Create core database tables

Revision ID: 002_create_core_tables
Revises: 001_initial_pgvector
Create Date: 2026-09-19 22:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '002_create_core_tables'
down_revision: Union[str, None] = '001_initial_pgvector'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='Responder'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_role', 'users', ['role'])

    # 2. services
    op.create_table(
        'services',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(length=100), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_team', sa.String(length=100), nullable=False),
        sa.Column('tier', sa.String(length=20), nullable=False, server_default='Tier-2'),
        sa.Column('repository_url', sa.String(length=255), nullable=True),
        sa.Column('dependencies', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('idx_services_name', 'services', ['name'], unique=True)

    # 3. incidents
    op.create_table(
        'incidents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='SEV-2'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='Triggered'),
        sa.Column('service_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('services.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_incidents_status_severity', 'incidents', ['status', 'severity'])
    op.create_index('idx_incidents_service_id', 'incidents', ['service_id'])

    # 4. investigations
    op.create_table(
        'investigations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('incidents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('investigation_number', sa.String(length=50), nullable=False, unique=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='Active'),
        sa.Column('probable_root_cause', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_investigations_incident_id', 'investigations', ['incident_id'])
    op.create_index('idx_investigations_number', 'investigations', ['investigation_number'], unique=True)

    # 5. investigation_steps
    op.create_table(
        'investigation_steps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('investigation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('investigations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('step_order', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='Pending'),
        sa.Column('output_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('idx_steps_investigation_order', 'investigation_steps', ['investigation_id', 'step_order'])

    # 6. evidence
    op.create_table(
        'evidence',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('investigation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('investigations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_tool', sa.String(length=100), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('raw_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('relevance_score', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('collected_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('idx_evidence_investigation_id', 'evidence', ['investigation_id'])

    # 7. hypotheses
    op.create_table(
        'hypotheses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('investigation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('investigations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('hypothesis_text', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='Proposed'),
        sa.Column('supporting_evidence_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False, server_default=sa.text("'{}'")),
        sa.Column('opposing_evidence_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False, server_default=sa.text("'{}'")),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('idx_hypotheses_investigation_id', 'hypotheses', ['investigation_id'])

    # 8. tool_calls
    op.create_table(
        'tool_calls',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('investigation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('investigations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('arguments', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='Success'),
        sa.Column('execution_time_ms', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('idx_tool_calls_investigation_id', 'tool_calls', ['investigation_id'])
    op.create_index('idx_tool_calls_tool_name', 'tool_calls', ['tool_name'])

    # 9. remediation_actions
    op.create_table(
        'remediation_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('investigation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('investigations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action_name', sa.String(length=100), nullable=False),
        sa.Column('parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('reasoning', sa.Text(), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=False, server_default='HIGH'),
        sa.Column('approval_status', sa.String(length=30), nullable=False, server_default='PENDING'),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approval_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('execution_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('idx_remediations_investigation_id', 'remediation_actions', ['investigation_id'])
    op.create_index('idx_remediations_approval_status', 'remediation_actions', ['approval_status'])

    # 10. documents
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('file_path', sa.String(length=255), nullable=False),
        sa.Column('associated_service_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('services.id', ondelete='SET NULL'), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('idx_documents_category', 'documents', ['category'])
    op.create_index('idx_documents_hash', 'documents', ['content_hash'])

    # 11. document_chunks
    op.create_table(
        'document_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('embedding', Vector(1536), nullable=False),
        sa.Column('ts_vector', postgresql.TSVECTOR(), nullable=True),
    )
    op.create_index('idx_chunks_document_id', 'document_chunks', ['document_id'])
    op.create_index('idx_chunks_ts_vector', 'document_chunks', ['ts_vector'], postgresql_using='gin')
    op.execute(
        "CREATE INDEX idx_chunks_embedding_hnsw ON document_chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);"
    )

    # 12. audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('incidents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('remediation_action_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('remediation_actions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('actor_type', sa.String(length=50), nullable=False),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    op.create_index('idx_audit_incident_id', 'audit_logs', ['incident_id'])
    op.create_index('idx_audit_action_type', 'audit_logs', ['action_type'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('document_chunks')
    op.drop_table('documents')
    op.drop_table('remediation_actions')
    op.drop_table('tool_calls')
    op.drop_table('hypotheses')
    op.drop_table('evidence')
    op.drop_table('investigation_steps')
    op.drop_table('investigations')
    op.drop_table('incidents')
    op.drop_table('services')
    op.drop_table('users')
