"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-01

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "brands",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "marketplaces",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(32), nullable=False, unique=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("base_url", sa.String(256), nullable=False),
    )
    op.create_table(
        "product_models",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("brand_id", sa.Integer(), sa.ForeignKey("brands.id"), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("slug", sa.String(256), nullable=False),
        sa.Column("category", sa.String(64)),
        sa.Column("default_size", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("brand_id", "slug", name="uq_product_model_brand_slug"),
    )
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_model_id", sa.Integer(), sa.ForeignKey("product_models.id"), nullable=False),
        sa.Column("size", sa.String(64)),
        sa.Column("material", sa.String(128)),
        sa.Column("hardware_color", sa.String(64)),
        sa.Column("style_code", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "product_attributes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("attr_key", sa.String(64), nullable=False),
        sa.Column("attr_value", sa.String(256), nullable=False),
        sa.Column(
            "source",
            sa.Enum("normalized", "raw", name="attribute_source"),
            server_default="raw",
        ),
    )
    op.create_table(
        "product_aliases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("alias_text", sa.String(512), nullable=False),
        sa.Column("marketplace_id", sa.Integer(), sa.ForeignKey("marketplaces.id")),
    )
    op.create_table(
        "listings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("marketplace_id", sa.Integer(), sa.ForeignKey("marketplaces.id"), nullable=False),
        sa.Column("source_listing_id", sa.String(128), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id")),
        sa.Column("title", sa.Text()),
        sa.Column("condition_raw", sa.String(128)),
        sa.Column("condition_normalized", sa.String(64)),
        sa.Column("seller_type", sa.String(64)),
        sa.Column(
            "status",
            sa.Enum("active", "sold", "removed", name="listing_status"),
            server_default="active",
        ),
        sa.Column("brand_raw", sa.String(128)),
        sa.Column("model_raw", sa.String(256)),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("match_confidence", sa.Numeric(5, 4)),
        sa.UniqueConstraint(
            "marketplace_id", "source_listing_id", name="uq_listing_marketplace_source"
        ),
    )
    op.create_index("ix_listings_product_id", "listings", ["product_id"])
    op.create_index("ix_listings_status", "listings", ["status"])
    op.create_table(
        "price_observations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listings.id"), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("price_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), server_default="USD"),
        sa.Column(
            "price_type",
            sa.Enum("ask", "sold", "auction_current", name="price_type"),
            server_default="ask",
        ),
        sa.Column("is_sale", sa.Boolean(), server_default="false"),
        sa.Column("raw_price_text", sa.String(64)),
    )
    op.create_index(
        "ix_price_obs_listing_observed", "price_observations", ["listing_id", "observed_at"]
    )
    op.create_table(
        "listing_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("listing_id", sa.Integer(), sa.ForeignKey("listings.id"), nullable=False),
        sa.Column("scraped_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("payload_json", postgresql.JSONB(), nullable=False),
    )
    op.create_table(
        "scrape_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("spider_name", sa.String(64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(32), server_default="running"),
        sa.Column("items_seen", sa.Integer(), server_default="0"),
        sa.Column("items_new", sa.Integer(), server_default="0"),
        sa.Column("errors_count", sa.Integer(), server_default="0"),
    )
    op.create_table(
        "social_mentions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("platform", sa.String(32), nullable=False),
        sa.Column("source_id", sa.String(128), nullable=False),
        sa.Column("url", sa.Text()),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id")),
        sa.Column("brand_raw", sa.String(128)),
        sa.Column("model_raw", sa.String(256)),
        sa.Column("text_content", sa.Text()),
        sa.Column("sentiment_score", sa.Numeric(6, 4)),
        sa.Column("engagement_count", sa.BigInteger()),
        sa.Column("posted_at", sa.DateTime(timezone=True)),
        sa.Column("scraped_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("platform", "source_id", name="uq_social_platform_source"),
    )

    op.execute(
        """
        INSERT INTO marketplaces (code, name, base_url) VALUES
        ('ebay', 'eBay', 'https://www.ebay.com'),
        ('therealreal', 'The RealReal', 'https://www.therealreal.com')
        ON CONFLICT (code) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_table("social_mentions")
    op.drop_table("scrape_runs")
    op.drop_table("listing_snapshots")
    op.drop_index("ix_price_obs_listing_observed", table_name="price_observations")
    op.drop_table("price_observations")
    op.drop_index("ix_listings_status", table_name="listings")
    op.drop_index("ix_listings_product_id", table_name="listings")
    op.drop_table("listings")
    op.drop_table("product_aliases")
    op.drop_table("product_attributes")
    op.drop_table("products")
    op.drop_table("product_models")
    op.drop_table("marketplaces")
    op.drop_table("brands")
    sa.Enum(name="attribute_source").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="listing_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="price_type").drop(op.get_bind(), checkfirst=True)
