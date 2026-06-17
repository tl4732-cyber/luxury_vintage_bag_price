"""Initial schema for Step 6

Revision ID: 001
Revises:
Create Date: 2026-06-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "marketplaces",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(32), nullable=False, unique=True),
        sa.Column("name", sa.String(128), nullable=False),
    )
    op.create_table(
        "listings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("marketplace_id", sa.Integer(), sa.ForeignKey("marketplaces.id"), nullable=False),
        sa.Column("source_listing_id", sa.String(128), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("title", sa.Text()),
        sa.Column("condition_raw", sa.String(128)),
        sa.Column("condition_normalized", sa.String(64)),
        sa.Column(
            "status",
            sa.Enum("active", "sold", "removed", name="listing_status"),
            server_default="active",
        ),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("marketplace_id", "source_listing_id", name="uq_listing_marketplace_source"),
    )
    op.create_table(
        "price_observations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listings.id"), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("price_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), server_default="USD"),
        sa.Column(
            "price_type",
            sa.Enum("ask", "sold", name="price_type"),
            server_default="ask",
        ),
    )
    op.create_index("ix_price_obs_listing_observed", "price_observations", ["listing_id", "observed_at"])
    op.execute(
        """
        INSERT INTO marketplaces (code, name) VALUES
        ('ebay', 'eBay'),
        ('therealreal', 'The RealReal')
        ON CONFLICT (code) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_index("ix_price_obs_listing_observed", table_name="price_observations")
    op.drop_table("price_observations")
    op.drop_table("listings")
    op.drop_table("marketplaces")
    sa.Enum(name="listing_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="price_type").drop(op.get_bind(), checkfirst=True)
