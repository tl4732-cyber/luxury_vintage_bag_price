"""Simple lexicon-based sentiment for Phase 4 MVP."""

POSITIVE = {
    "love",
    "beautiful",
    "stunning",
    "grail",
    "investment",
    "timeless",
    "gorgeous",
    "perfect",
    "obsessed",
}
NEGATIVE = {
    "overpriced",
    "fake",
    "scam",
    "disappointed",
    "damaged",
    "waste",
    "ripoff",
    "falling",
    "decline",
}


def score_text(text: str | None) -> float | None:
    if not text:
        return None
    words = set(text.lower().split())
    pos = len(words & POSITIVE)
    neg = len(words & NEGATIVE)
    total = pos + neg
    if total == 0:
        return 0.0
    return round((pos - neg) / total, 4)
