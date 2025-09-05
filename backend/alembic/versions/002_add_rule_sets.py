"""Add support for multiple rule sets

Revision ID: 002
Revises: 001
Create Date: 2025-01-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Create rule_sets table
    op.create_table('rule_sets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('preprocessing_prompt', sa.Text(), nullable=True),
        sa.Column('rule_set_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rule_sets_name'), 'rule_sets', ['name'], unique=True)
    op.create_index(op.f('ix_rule_sets_is_active'), 'rule_sets', ['is_active'])
    
    # Create rules table (replacing finra_rules)
    op.create_table('rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_set_id', sa.Integer(), nullable=False),
        sa.Column('rule_number', sa.String(), nullable=False),
        sa.Column('rule_title', sa.String(), nullable=False),
        sa.Column('effective_start_date', sa.DateTime(), nullable=True),
        sa.Column('effective_end_date', sa.DateTime(), nullable=True),
        sa.Column('rulebook_hierarchy', sa.String(), nullable=True),
        sa.Column('rule_text', sa.Text(), nullable=False),
        sa.Column('original_rule_text', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('rule_metadata', sa.JSON(), nullable=True),
        sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['rule_set_id'], ['rule_sets.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('rule_set_id', 'rule_number', name='uq_rule_set_rule_number')
    )
    op.create_index(op.f('ix_rules_rule_set_id'), 'rules', ['rule_set_id'])
    op.create_index(op.f('ix_rules_rule_number'), 'rules', ['rule_number'])
    op.create_index(op.f('ix_rules_category'), 'rules', ['category'])
    op.create_index(op.f('ix_rules_is_current'), 'rules', ['is_current'])
    op.create_index('idx_rule_search', 'rules', ['search_vector'], postgresql_using='gin')
    
    # Add rule_set_id to document_analyses
    op.add_column('document_analyses', sa.Column('rule_set_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_document_analyses_rule_set_id'), 'document_analyses', ['rule_set_id'])
    op.create_foreign_key('fk_document_analyses_rule_set_id', 'document_analyses', 'rule_sets', ['rule_set_id'], ['id'])
    
    # Drop old finra_rules table and its indexes if they exist
    op.execute("DROP INDEX IF EXISTS idx_rule_search")
    op.execute("DROP TABLE IF EXISTS finra_rules CASCADE")


def downgrade():
    # Drop new foreign keys and columns
    op.drop_constraint('fk_document_analyses_rule_set_id', 'document_analyses', type_='foreignkey')
    op.drop_index(op.f('ix_document_analyses_rule_set_id'), table_name='document_analyses')
    op.drop_column('document_analyses', 'rule_set_id')
    
    # Drop new tables
    op.drop_index('idx_rule_search', table_name='rules', postgresql_using='gin')
    op.drop_index(op.f('ix_rules_is_current'), table_name='rules')
    op.drop_index(op.f('ix_rules_category'), table_name='rules')
    op.drop_index(op.f('ix_rules_rule_number'), table_name='rules')
    op.drop_index(op.f('ix_rules_rule_set_id'), table_name='rules')
    op.drop_table('rules')
    
    op.drop_index(op.f('ix_rule_sets_is_active'), table_name='rule_sets')
    op.drop_index(op.f('ix_rule_sets_name'), table_name='rule_sets')
    op.drop_table('rule_sets')