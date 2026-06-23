"""Add products table for brand/model attributes

Revision ID: 002
Revises: 001
Create Date: 2026-06-17

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("brand", sa.String(64), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("size", sa.String(32)),
        sa.Column("color", sa.String(64)),
        sa.Column("leather", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "brand",
            "model",
            "size",
            "color",
            "leather",
            name="uq_product_identity",
        ),
    )
    op.create_index("ix_products_brand_model", "products", ["brand", "model"])


def downgrade() -> None:
    op.drop_index("ix_products_brand_model", table_name="products")
    op.drop_table("products")
