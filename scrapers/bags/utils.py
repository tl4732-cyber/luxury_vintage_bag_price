import hashlib
import json
from datetime import datetime, timezone

from slugify import slugify

CONDITION_MAP = {
    "new with tags": "new",
    "new without tags": "like_new",
    "new with box": "new",
    "new without box": "like_new",
    "new": "new",
    "excellent": "excellent",
    "very good": "very_good",
    "good": "good",
    "fair": "fair",
    "poor": "poor",
    "pre-owned": "good",
    "used": "good",
    "like new": "like_new",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_condition(raw: str | None) -> str | None:
    if not raw:
        return None
    key = raw.strip().lower()
    return CONDITION_MAP.get(key, slugify(key, max_length=64) or None)


def compute_content_hash(fields: dict) -> str:
    """Hash normalized listing fields for change detection."""
    payload = {
        k: fields.get(k)
        for k in (
            "title",
            "brand",
            "model",
            "size",
            "color",
            "material",
            "year",
            "hardware",
            "condition_normalized",
            "status",
        )
    }
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def listing_source_key(marketplace: str, source_listing_id: str) -> str:
    return hashlib.sha256(f"{marketplace}:{source_listing_id}".encode()).hexdigest()
