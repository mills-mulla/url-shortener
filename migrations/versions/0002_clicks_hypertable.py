""" convert clicks to timescaleDb hypertable
Revision ID: 0002_clicks_hypertable
Revises: 0001_initial
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() ->None:
    #The partition column must be part of every unique key
    op.execute("ALTER TABLE clicks DROP CONSTRAINT clicks_pkey")
    op.execute("ALTER TABLE clicks ADD PRIMARY KEY (id, ts)")
    op.execute("SELECT create_hypertable('clicks', 'ts', if_not_exists => true, migrate_data => true)")

def downgrade() -> None:
    raise NotImplementedError("A hypertable can't be converted back in place  since TimescaleDB does not provide a direct un-hypertable or alter table command")