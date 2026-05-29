"""rebuild milestones table with full schema

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-05-28

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('milestones')
    op.create_table(
        'milestones',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('dog_id', sa.Integer(), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('notes1', sa.String(), nullable=True),
        sa.Column('notes2', sa.String(), nullable=True),
        sa.Column('weight_lbs', sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('milestones')
    op.create_table(
        'milestones',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('dog_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('notes', sa.String(), nullable=True),
    )
