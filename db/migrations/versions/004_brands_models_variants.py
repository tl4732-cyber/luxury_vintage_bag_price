"""Normalize catalog: brands, models, product_variants

Revision ID: 004
Revises: 003
Create Date: 2026-06-17

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "brands",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "models",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("brand_id", sa.Integer(), sa.ForeignKey("brands.id"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("brand_id", "name", name="uq_model_brand_name"),
    )
    op.create_table(
        "product_variants",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("model_id", sa.Integer(), sa.ForeignKey("models.id"), nullable=False),
        sa.Column("size", sa.String(32)),
        sa.Column("color", sa.String(64)),
        sa.Column("leather", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("model_id", "size", "color", "leather", name="uq_variant_identity"),
    )
    op.create_index("ix_variants_model_id", "product_variants", ["model_id"])

    # Migrate flat products → normalized catalog
    op.execute(
        """
        INSERT INTO brands (name, created_at)
        SELECT DISTINCT brand, MIN(created_at)
        FROM products
        GROUP BY brand
        """
    )
    op.execute(
        """
        INSERT INTO models (brand_id, name, created_at)
        SELECT b.id, p.model, MIN(p.created_at)
        FROM products p
        JOIN brands b ON b.name = p.brand
        GROUP BY b.id, p.model
        """
    )
    op.execute(
        """
        INSERT INTO product_variants (model_id, size, color, leather, created_at)
        SELECT m.id, p.size, p.color, p.leather, p.created_at
        FROM products p
        JOIN brands b ON b.name = p.brand
        JOIN models m ON m.brand_id = b.id AND m.name = p.model
        """
    )

    op.add_column("listings", sa.Column("product_variant_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE listings l
        SET product_variant_id = pv.id
        FROM products p
        JOIN brands b ON b.name = p.brand
        JOIN models m ON m.brand_id = b.id AND m.name = p.model
        JOIN product_variants pv ON pv.model_id = m.id
            AND pv.size IS NOT DISTINCT FROM p.size
            AND pv.color IS NOT DISTINCT FROM p.color
            AND pv.leather IS NOT DISTINCT FROM p.leather
        WHERE l.product_id = p.id
        """
    )

    op.drop_index("ix_listings_product_id", table_name="listings")
    op.drop_constraint("fk_listings_product_id", "listings", type_="foreignkey")
    op.drop_column("listings", "product_id")
    op.drop_index("ix_products_brand_model", table_name="products")
    op.drop_table("products")

    op.create_foreign_key(
        "fk_listings_product_variant_id",
        "listings",
        "product_variants",
        ["product_variant_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_listings_product_variant_id", "listings", ["product_variant_id"])


def downgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("brand", sa.String(64), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("size", sa.String(32)),
        sa.Column("color", sa.String(64)),
        sa.Column("leather", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("brand", "model", "size", "color", "leather", name="uq_product_identity"),
    )
    op.create_index("ix_products_brand_model", "products", ["brand", "model"])

    op.execute(
        """
        INSERT INTO products (brand, model, size, color, leather, created_at)
        SELECT b.name, m.name, pv.size, pv.color, pv.leather, pv.created_at
        FROM product_variants pv
        JOIN models m ON m.id = pv.model_id
        JOIN brands b ON b.id = m.brand_id
        """
    )

    op.add_column("listings", sa.Column("product_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE listings l
        SET product_id = p.id
        FROM product_variants pv
        JOIN models m ON m.id = pv.model_id
        JOIN brands b ON b.id = m.brand_id
        JOIN products p ON p.brand = b.name AND p.model = m.name
            AND p.size IS NOT DISTINCT FROM pv.size
            AND p.color IS NOT DISTINCT FROM pv.color
            AND p.leather IS NOT DISTINCT FROM pv.leather
        WHERE l.product_variant_id = pv.id
        """
    )

    op.drop_index("ix_listings_product_variant_id", table_name="listings")
    op.drop_constraint("fk_listings_product_variant_id", "listings", type_="foreignkey")
    op.drop_column("listings", "product_variant_id")

    op.create_foreign_key(
        "fk_listings_product_id",
        "listings",
        "products",
        ["product_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_listings_product_id", "listings", ["product_id"])

    op.drop_index("ix_variants_model_id", table_name="product_variants")
    op.drop_table("product_variants")
    op.drop_table("models")
    op.drop_table("brands")
