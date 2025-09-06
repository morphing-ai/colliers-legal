"""Initial Neurobot and embeddings schema

Revision ID: 001_initial_neurobot
Revises: 
Create Date: 2025-01-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial_neurobot'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create neurobots table
    op.create_table('neurobots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('function_name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('code', sa.Text(), nullable=False),
        sa.Column('neurobot_type', sa.String(), nullable=True),
        sa.Column('example_usage', sa.Text(), nullable=True),
        sa.Column('generation_prompt', sa.Text(), nullable=True),
        sa.Column('expected_parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('required_apis', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('calls_neurobots', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('return_schema', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('run_count', sa.Integer(), nullable=True),
        sa.Column('feedback_plus', sa.Integer(), nullable=True),
        sa.Column('feedback_minus', sa.Integer(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('avg_execution_time', sa.Float(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('function_name')
    )
    
    # Create index on neurobot_type
    op.create_index('ix_neurobots_type', 'neurobots', ['neurobot_type'])
    op.create_index('ix_neurobots_active', 'neurobots', ['is_active'])
    
    # Create clause_embeddings table
    op.create_table('clause_embeddings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contract_id', sa.String(), nullable=True),
        sa.Column('clause_text', sa.Text(), nullable=False),
        sa.Column('clause_type', sa.String(), nullable=True),
        sa.Column('embedding_vector', postgresql.ARRAY(sa.Float()), nullable=False),
        sa.Column('embedding_model', sa.String(), nullable=True, server_default='text-embedding-3-small'),
        sa.Column('risk_score', sa.Float(), nullable=True),
        sa.Column('paralegal_notes', sa.Text(), nullable=True),
        sa.Column('created_date', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create vector index for similarity search
    op.execute("""
        CREATE INDEX ix_clause_embeddings_vector 
        ON clause_embeddings 
        USING ivfflat (embedding_vector vector_cosine_ops)
        WITH (lists = 100)
    """)
    
    # Create clause_patterns table
    op.create_table('clause_patterns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pattern_name', sa.String(), nullable=False),
        sa.Column('pattern_description', sa.Text(), nullable=True),
        sa.Column('centroid_embedding', postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column('variance_threshold', sa.Float(), nullable=True),
        sa.Column('example_clauses', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('risk_level', sa.String(), nullable=True),
        sa.Column('frequency_seen', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('historical_outcomes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pattern_name')
    )
    
    # Create neurobot_execution_logs table
    op.create_table('neurobot_execution_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('neurobot_id', sa.Integer(), nullable=False),
        sa.Column('contract_id', sa.String(), nullable=True),
        sa.Column('section_name', sa.String(), nullable=True),
        sa.Column('input_params', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('output_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('execution_logs', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['neurobot_id'], ['neurobots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create neurobot_versions table for version control
    op.create_table('neurobot_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('neurobot_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('code_snapshot', sa.Text(), nullable=False),
        sa.Column('changed_by', sa.String(), nullable=False),
        sa.Column('change_date', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('change_notes', sa.Text(), nullable=True),
        sa.Column('rollback_reason', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['neurobot_id'], ['neurobots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create contracts table for document storage
    op.create_table('contracts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('upload_date', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('uploaded_by', sa.String(), nullable=True),
        sa.Column('contract_type', sa.String(), nullable=True),
        sa.Column('jurisdiction', sa.String(), nullable=True),
        sa.Column('parties', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('analysis_results', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('paralegal_review', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add check constraint for neurobot types
    op.execute("""
        ALTER TABLE neurobots 
        ADD CONSTRAINT check_neurobot_type 
        CHECK (neurobot_type IN ('compute', 'search', 'analyze', 'compare', 'extract', 'score', 'learn'))
    """)
    
    # Add check constraint for risk levels
    op.execute("""
        ALTER TABLE clause_patterns 
        ADD CONSTRAINT check_risk_level 
        CHECK (risk_level IN ('high', 'medium', 'low'))
    """)


def downgrade():
    op.drop_table('contracts')
    op.drop_table('neurobot_versions')
    op.drop_table('neurobot_execution_logs')
    op.drop_table('clause_patterns')
    op.drop_table('clause_embeddings')
    op.drop_table('neurobots')
    op.execute('DROP EXTENSION IF EXISTS vector')