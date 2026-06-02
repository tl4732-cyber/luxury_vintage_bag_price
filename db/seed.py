"""Seed catalog brands and sample product models."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from slugify import slugify
from sqlalchemy import select

from db.models import Brand, Product, ProductModel
from db.session import get_session_factory

SEED_BRANDS = [
    ("Chanel", "chanel"),
    ("Hermès", "hermes"),
    ("Louis Vuitton", "louis-vuitton"),
    ("Gucci", "gucci"),
    ("Prada", "prada"),
]

SEED_MODELS = {
    "chanel": [
        ("Classic Flap Bag", "classic-flap-bag", "handbag"),
        ("Boy Bag", "boy-bag", "handbag"),
    ],
    "hermes": [
        ("Birkin", "birkin", "handbag"),
        ("Kelly", "kelly", "handbag"),
    ],
    "louis-vuitton": [
        ("Speedy", "speedy", "handbag"),
        ("Neverfull", "neverfull", "handbag"),
    ],
}


def seed():
    Session = get_session_factory()
    with Session() as session:
        for name, slug in SEED_BRANDS:
            existing = session.execute(select(Brand).where(Brand.slug == slug)).scalar_one_or_none()
            if not existing:
                session.add(Brand(name=name, slug=slug))
        session.flush()

        for brand_slug, models in SEED_MODELS.items():
            brand = session.execute(
                select(Brand).where(Brand.slug == brand_slug)
            ).scalar_one()
            for model_name, model_slug, category in models:
                exists = session.execute(
                    select(ProductModel).where(
                        ProductModel.brand_id == brand.id,
                        ProductModel.slug == model_slug,
                    )
                ).scalar_one_or_none()
                if not exists:
                    pm = ProductModel(
                        brand_id=brand.id,
                        name=model_name,
                        slug=model_slug,
                        category=category,
                    )
                    session.add(pm)
                    session.flush()
                    session.add(Product(product_model_id=pm.id))
        session.commit()
    print("Seed complete.")


if __name__ == "__main__":
    seed()
