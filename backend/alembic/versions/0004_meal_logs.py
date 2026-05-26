"""add meal_logs table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-25

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'meal_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('dog_id', sa.Integer(), nullable=False),
        sa.Column('slot', sa.String(), nullable=False),
        sa.Column('meal_date', sa.Date(), nullable=False),
        sa.Column('percent_consumed', sa.Integer(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('ingredients', sa.String(), nullable=True),
        sa.UniqueConstraint('dog_id', 'slot', 'meal_date', name='uq_meal_log'),
    )


def downgrade() -> None:
    op.drop_table('meal_logs')
