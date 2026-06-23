"""Extract brand, model, size, color, and leather from listing titles."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedProduct:
    brand: str
    model: str
    size: str | None = None
    color: str | None = None
    leather: str | None = None


BRAND_ALIASES: list[tuple[str, str]] = [
    ("hermes", "Hermès"),
    ("hermès", "Hermès"),
    ("chanel", "Chanel"),
    ("louis vuitton", "Louis Vuitton"),
    ("lv", "Louis Vuitton"),
    ("gucci", "Gucci"),
    ("dior", "Dior"),
    ("fendi", "Fendi"),
    ("bottega veneta", "Bottega Veneta"),
    ("celine", "Céline"),
    ("céline", "Céline"),
    ("prada", "Prada"),
    ("saint laurent", "Saint Laurent"),
    ("ysl", "Saint Laurent"),
    ("loewe", "Loewe"),
    ("goyard", "Goyard"),
]

# Longer model names first so "Classic Double Flap" wins over "Classic Flap".
MODEL_PATTERNS: list[tuple[str, str]] = [
    ("Classic Double Flap", r"classic\s+double\s+flap|double\s+flap"),
    ("Classic Flap", r"classic\s+flap|reissue\s+2\.55|2\.55"),
    ("Boy Bag", r"\bboy\s+bag\b|\bboy\b"),
    ("Haut à Courroies", r"\bhac\b|haut\s+[àa]\s+courroies"),
    ("Birkin", r"\bbirkin\b"),
    ("Kelly", r"\bkelly\b"),
    ("Constance", r"\bconstance\b"),
    ("Garden Party", r"\bgarden\s+party\b"),
    ("Picotin", r"\bpicotin\b"),
    ("Evelyne", r"\bevelyne\b"),
    ("Lindy", r"\blindy\b"),
    ("Neverfull", r"\bneverfull\b"),
    ("Speedy", r"\bspeedy\b"),
    ("Alma", r"\balma\b"),
    ("Pochette Métis", r"\bpochette\s+m[ée]tis\b"),
    ("Dionysus", r"\bdionysus\b"),
    ("Marmont", r"\bmarmont\b"),
    ("Jackie", r"\bjackie\b"),
    ("Baguette", r"\bbaguette\b"),
    ("Peekaboo", r"\bpeekaboo\b"),
]

LEATHER_ALIASES: list[tuple[str, str]] = [
    ("taurillon clemence", "Taurillon Clemence"),
    ("veau swift", "Swift"),
    ("clemence", "Clemence"),
    ("courchevel", "Courchevel"),
    ("caviar", "Caviar"),
    ("lambskin", "Lambskin"),
    ("chevre", "Chèvre"),
    ("chèvre", "Chèvre"),
    ("alligator", "Alligator"),
    ("crocodile", "Crocodile"),
    ("ostrich", "Ostrich"),
    ("ardennes", "Ardennes"),
    ("box leather", "Box"),
    ("epsom", "Epsom"),
    ("swift", "Swift"),
    ("togo", "Togo"),
]

COLOR_ALIASES: list[tuple[str, str]] = [
    ("etoupe/beige", "Etoupe"),
    ("étoupe/beige", "Etoupe"),
    ("bleu jean", "Bleu Jean"),
    ("rouge tomate", "Rouge Tomate"),
    ("thalassa blue", "Thalassa Blue"),
    ("tanzanite blue", "Tanzanite Blue"),
    ("tanzanite", "Tanzanite Blue"),
    ("poppy orange", "Poppy Orange"),
    ("etoupe", "Etoupe"),
    ("étoupe", "Etoupe"),
    ("pelouse", "Pelouse"),
    ("raisin", "Raisin"),
    ("noir", "Black"),
    ("black", "Black"),
    ("white", "White"),
    ("gold", "Gold"),
    ("beige", "Beige"),
    ("brown", "Brown"),
    ("red", "Red"),
    ("rouge", "Red"),
    ("blue", "Blue"),
    ("orange", "Orange"),
    ("pink", "Pink"),
    ("green", "Green"),
    ("grey", "Grey"),
    ("gray", "Gray"),
    ("purple", "Purple"),
    ("tan", "Tan"),
    ("navy", "Navy"),
    ("cream", "Cream"),
    ("ivory", "Ivory"),
]

SIZE_PATTERN = re.compile(
    r"\b(mini|small|medium|large|pm|mm|gm|15|20|25|28|30|32|35|40|45|50)\b",
    re.IGNORECASE,
)
SIZE_GLUE_PATTERN = re.compile(r"\b(15|20|25|28|30|32|35|40|45|50)([a-z])", re.IGNORECASE)

# Strip hardware phrases so "Gold Hardware" is not parsed as bag color Gold.
HARDWARE_PHRASES = re.compile(
    r"\b(?:gold|silver|palladium|rose gold|gunmetal)[\s-]*(?:tone\s+)?hardware\b"
    r"|\b(?:gold|silver|palladium)\s+tone\b"
    r"|\b(?:gold|silver|palladium)\s+metal\s+fittings\b",
    re.IGNORECASE,
)


def _normalize_text(text: str) -> str:
    lowered = unicodedata.normalize("NFKD", text).lower()
    return lowered.encode("ascii", "ignore").decode("ascii")


def _find_alias(
    text: str,
    aliases: list[tuple[str, str]],
    *,
    word_boundary: bool = False,
) -> str | None:
    for needle, canonical in sorted(aliases, key=lambda pair: len(pair[0]), reverse=True):
        if word_boundary or len(needle) <= 4:
            if re.search(rf"\b{re.escape(needle)}\b", text):
                return canonical
        elif needle in text:
            return canonical
    return None


def _find_brand(text: str) -> str | None:
    return _find_alias(text, BRAND_ALIASES, word_boundary=True)


def _find_model(text: str) -> str | None:
    for canonical, pattern in MODEL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return canonical
    return None


def _find_size(text: str) -> str | None:
    match = SIZE_PATTERN.search(text)
    if not match:
        return None
    return match.group(1).lower()


def _expand_glued_tokens(text: str) -> str:
    """Split glued tokens like '35orange' or 'bluetogo'."""
    expanded = SIZE_GLUE_PATTERN.sub(r"\1 \2", text)
    for needle, _ in sorted(LEATHER_ALIASES, key=lambda pair: len(pair[0]), reverse=True):
        expanded = re.sub(
            rf"([a-z]){re.escape(needle)}",
            rf"\1 {needle}",
            expanded,
        )
    return expanded


def parse_title(title: str | None) -> ParsedProduct | None:
    """Return parsed bag identity when brand and model are found in the title."""
    if not title or not title.strip():
        return None

    normalized = _expand_glued_tokens(_normalize_text(title))
    brand = _find_brand(normalized)
    if not brand:
        return None

    model = _find_model(title)
    if not model:
        return None

    size = _find_size(normalized)
    leather = _find_alias(normalized, LEATHER_ALIASES, word_boundary=True)

    color_text = HARDWARE_PHRASES.sub(" ", normalized)
    if leather:
        color_text = re.sub(rf"\b{re.escape(leather.lower())}\b", " ", color_text)
    color = _find_alias(color_text, COLOR_ALIASES, word_boundary=True)

    return ParsedProduct(
        brand=brand,
        model=model,
        size=size,
        color=color,
        leather=leather,
    )
