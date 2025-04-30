"""Add ticket status fields

Revision ID: add_ticket_status
Revises: initial_migration
Create Date: 2024-01-17 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_ticket_status'
down_revision = 'initial_migration'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('service_tickets', sa.Column('status', sa.String(20), nullable=False, server_default='open'))
    op.add_column('service_tickets', sa.Column('assigned_to', sa.String(100), nullable=True))
    op.add_column('service_tickets', sa.Column('last_updated', sa.DateTime(), nullable=True))

def downgrade() -> None:
    op.drop_column('service_tickets', 'status')
    op.drop_column('service_tickets', 'assigned_to')
    op.drop_column('service_tickets', 'last_updated')