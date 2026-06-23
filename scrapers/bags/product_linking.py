"""Rules for when a scraped listing should link to a product row."""

from __future__ import annotations

import re

from bags.title_parser import ParsedProduct, parse_title

# Titles matching these are accessories/parts, not the bag itself.
ACCESSORY_PATTERNS: list[str] = [
    r"\bcharm\b",
    r"\bcover\b",
    r"protective",
    r"\bsilicone\b",
    r"stud feet",
    r"gift box",
    r"empty box",
    r"storage bag",
    r"dust bag",
    r"shopping bag ribbon",
    r"\bribbon\b",
    r"\bclochette\b",
    r"\btirette\b",
    r"felt cover",
    r"feet cover",
]

# Minimum ask price (USD) before linking to a product variant.
MIN_PRICE_USD: dict[tuple[str, str], float] = {
    ("Hermès", "Birkin"): 5000.0,
}


def is_likely_accessory(title: str | None) -> bool:
    if not title:
        return False
    normalized = title.lower()
    return any(re.search(pattern, normalized) for pattern in ACCESSORY_PATTERNS)


def has_variant_detail(parsed: ParsedProduct) -> bool:
    """Require at least one physical attribute so we don't create catch-all products."""
    return bool(parsed.size or parsed.color or parsed.leather)


def meets_min_price(parsed: ParsedProduct, price_amount: float | None) -> bool:
    floor = MIN_PRICE_USD.get((parsed.brand, parsed.model))
    if floor is None:
        return True
    if price_amount is None:
        return False
    return float(price_amount) >= floor


def should_link_listing(
    title: str | None,
    price_amount: float | None,
    parsed: ParsedProduct | None = None,
) -> bool:
    if not title:
        return False
    if is_likely_accessory(title):
        return False

    resolved = parsed or parse_title(title)
    if resolved is None:
        return False
    if not has_variant_detail(resolved):
        return False
    if not meets_min_price(resolved, price_amount):
        return False
    return True
