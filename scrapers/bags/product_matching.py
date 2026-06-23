from sqlalchemy import select

from bags.title_parser import ParsedProduct
from db.models import Brand, Model, ProductVariant


def get_or_create_brand(session, name: str) -> Brand:
    brand = session.execute(select(Brand).where(Brand.name == name)).scalar_one_or_none()
    if brand is None:
        brand = Brand(name=name)
        session.add(brand)
        session.flush()
    return brand


def get_or_create_model(session, brand_id: int, name: str) -> Model:
    model = session.execute(
        select(Model).where(Model.brand_id == brand_id, Model.name == name)
    ).scalar_one_or_none()
    if model is None:
        model = Model(brand_id=brand_id, name=name)
        session.add(model)
        session.flush()
    return model


def get_or_create_variant(session, parsed: ParsedProduct) -> ProductVariant:
    brand = get_or_create_brand(session, parsed.brand)
    model = get_or_create_model(session, brand.id, parsed.model)

    variant = session.execute(
        select(ProductVariant).where(
            ProductVariant.model_id == model.id,
            ProductVariant.size == parsed.size,
            ProductVariant.color == parsed.color,
            ProductVariant.leather == parsed.leather,
        )
    ).scalar_one_or_none()
    if variant is None:
        variant = ProductVariant(
            model_id=model.id,
            size=parsed.size,
            color=parsed.color,
            leather=parsed.leather,
        )
        session.add(variant)
        session.flush()
    return variant
