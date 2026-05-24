"""add unique constraint on pee_poo_events (dog_id, type, timestamp)

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-24

"""
from typing import Sequence, Union
from alembic import op

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove duplicates, keeping the earliest id for each (dog_id, type, timestamp)
    op.execute(
        "DELETE FROM pee_poo_events WHERE id NOT IN ("
        "  SELECT MIN(id) FROM pee_poo_events GROUP BY dog_id, type, timestamp"
        ")"
    )
    with op.batch_alter_table('pee_poo_events') as batch_op:
        batch_op.create_unique_constraint('uq_pee_poo_event', ['dog_id', 'type', 'timestamp'])


def downgrade() -> None:
    with op.batch_alter_table('pee_poo_events') as batch_op:
        batch_op.drop_constraint('uq_pee_poo_event', type_='unique')
