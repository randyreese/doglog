"""rebuild meal_configs and medications with child tables

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-05-30

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('meal_configs')
    op.create_table(
        'meal_configs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('dog_id', sa.Integer(), nullable=False),
        sa.Column('meal_slot', sa.String(), nullable=False),
        sa.Column('effective_date', sa.Date(), nullable=False),
    )
    op.create_table(
        'meal_config_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('meal_config_id', sa.Integer(), nullable=False),
        sa.Column('food_name', sa.String(), nullable=False),
        sa.Column('amount', sa.String(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
    )
    op.drop_table('medications')
    op.create_table(
        'medications',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('dog_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
    )
    op.create_table(
        'medication_doses',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('medication_id', sa.Integer(), nullable=False),
        sa.Column('label', sa.String(), nullable=False),
        sa.Column('amount', sa.String(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
    )


def downgrade() -> None:
    op.drop_table('medication_doses')
    op.drop_table('medications')
    op.drop_table('meal_config_items')
    op.drop_table('meal_configs')
    op.create_table(
        'meal_configs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('dog_id', sa.Integer(), nullable=False),
        sa.Column('meal_slot', sa.String(), nullable=False),
        sa.Column('food_name', sa.String(), nullable=False),
        sa.Column('amount', sa.String(), nullable=True),
        sa.Column('effective_date', sa.Date(), nullable=False),
    )
    op.create_table(
        'medications',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('dog_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('dosage', sa.String(), nullable=True),
        sa.Column('frequency', sa.String(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
    )
