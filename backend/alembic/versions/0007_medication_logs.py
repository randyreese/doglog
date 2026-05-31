"""add medication_logs table

Revision ID: a1b2c3d4e5f6
Revises: f6a7b8c9d0e1
Create Date: 2026-05-31

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0007medicationlogs'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'medication_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dog_id', sa.Integer(), nullable=False),
        sa.Column('medication_id', sa.Integer(), nullable=False),
        sa.Column('log_date', sa.Date(), nullable=False),
        sa.Column('doses_given', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dog_id', 'medication_id', 'log_date', name='uq_medication_log'),
    )
    op.create_index('ix_medication_logs_id', 'medication_logs', ['id'])


def downgrade() -> None:
    op.drop_index('ix_medication_logs_id', table_name='medication_logs')
    op.drop_table('medication_logs')
