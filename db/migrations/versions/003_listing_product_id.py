"""Link listings to products

Revision ID: 003
Revises: 002
Create Date: 2026-06-17

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("listings", sa.Column("product_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_listings_product_id",
        "listings",
        "products",
        ["product_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_listings_product_id", "listings", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_listings_product_id", table_name="listings")
    op.drop_constraint("fk_listings_product_id", "listings", type_="foreignkey")
    op.drop_column("listings", "product_id")
