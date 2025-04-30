"""Initial migration

Revision ID: initial_migration
Revises: 
Create Date: 2024-01-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'initial_migration'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create troubleshooting_histories table
    op.create_table('troubleshooting_histories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('door_serial', sa.String(length=20), nullable=False),
        sa.Column('door_type', sa.String(length=50), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('final_node', sa.String(length=50), nullable=False),
        sa.Column('history_steps', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create service_tickets table
    op.create_table('service_tickets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('history_id', sa.Integer(), nullable=False),
        sa.Column('contact_name', sa.String(length=100), nullable=False),
        sa.Column('contact_phone', sa.String(length=20), nullable=False),
        sa.Column('contact_email', sa.String(length=100), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False),
        sa.Column('additional_info', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['history_id'], ['troubleshooting_histories.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('service_tickets')
    op.drop_table('troubleshooting_histories')