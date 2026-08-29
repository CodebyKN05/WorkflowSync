"""add reconciliation_run_id to match

Revision ID: dd7df5dbeb77
Revises: 20a4d3d1114e
Create Date: 2026-08-30 01:40:16.803373

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd7df5dbeb77'
down_revision: Union[str, Sequence[str], None] = '20a4d3d1114e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('matches', sa.Column('reconciliation_run_id', sa.Uuid(), nullable=False))
    op.create_foreign_key('fk_matches_reconciliation_run_id', 'matches', 'reconciliation_runs', ['reconciliation_run_id'], ['id'])
    op.create_index(op.f('ix_matches_reconciliation_run_id'), 'matches', ['reconciliation_run_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_matches_reconciliation_run_id'), table_name='matches')
    op.drop_constraint('fk_matches_reconciliation_run_id', 'matches', type_='foreignkey')
    op.drop_column('matches', 'reconciliation_run_id')
