"""
Reddit mention ingest into social_mentions.

Usage: python -m sentiment.ingest_reddit --limit 100
Requires REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT.
"""

import argparse
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select

from db.models import SocialMention
from db.session import get_session_factory
from sentiment.scoring import score_text

SUBREDDITS = ["handbags", "luxurypurses"]
BRAND_KEYWORDS = ["chanel", "hermes", "hermès", "louis vuitton", "gucci", "prada", "birkin", "kelly"]


def fetch_reddit_posts(limit: int) -> list[dict]:
    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    if not client_id or not client_secret:
        return _mock_posts()

    try:
        import httpx
    except ImportError:
        return _mock_posts()

    # Minimal OAuth-less public JSON fallback for dev (rate limited)
    posts = []
    user_agent = os.environ.get("REDDIT_USER_AGENT", "lvbp/1.0")
    headers = {"User-Agent": user_agent}
    with httpx.Client(headers=headers, timeout=30) as client:
        for sub in SUBREDDITS:
            url = f"https://www.reddit.com/r/{sub}/hot.json?limit={min(limit, 25)}"
            resp = client.get(url)
            if resp.status_code != 200:
                continue
            for child in resp.json().get("data", {}).get("children", []):
                d = child.get("data", {})
                posts.append(
                    {
                        "source_id": d.get("id", ""),
                        "url": f"https://reddit.com{d.get('permalink', '')}",
                        "title": d.get("title", ""),
                        "selftext": d.get("selftext", ""),
                        "score": d.get("score", 0),
                        "created_utc": d.get("created_utc"),
                    }
                )
    return posts[:limit]


def _mock_posts() -> list[dict]:
    return [
        {
            "source_id": "mock_reddit_1",
            "url": "https://reddit.com/r/handbags/mock1",
            "title": "Chanel Classic Flap prices seem to be holding steady",
            "selftext": "Love my classic flap, timeless investment.",
            "score": 42,
            "created_utc": datetime.now(timezone.utc).timestamp(),
        },
        {
            "source_id": "mock_reddit_2",
            "url": "https://reddit.com/r/handbags/mock2",
            "title": "Hermes Birkin waitlist frustration",
            "selftext": "Overpriced resale market is disappointing.",
            "score": 18,
            "created_utc": datetime.now(timezone.utc).timestamp(),
        },
    ]


def _mentions_luxury(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in BRAND_KEYWORDS)


def ingest(limit: int):
    posts = fetch_reddit_posts(limit)
    Session = get_session_factory()
    with Session() as session:
        for post in posts:
            text = f"{post.get('title', '')} {post.get('selftext', '')}".strip()
            if not _mentions_luxury(text):
                continue
            existing = session.execute(
                select(SocialMention).where(
                    SocialMention.platform == "reddit",
                    SocialMention.source_id == post["source_id"],
                )
            ).scalar_one_or_none()
            if existing:
                continue
            brand_raw = next((kw.title() for kw in BRAND_KEYWORDS if kw in text.lower()), None)
            mention = SocialMention(
                platform="reddit",
                source_id=post["source_id"],
                url=post.get("url"),
                brand_raw=brand_raw,
                text_content=text[:4000],
                sentiment_score=score_text(text),
                engagement_count=post.get("score"),
                posted_at=datetime.fromtimestamp(
                    post["created_utc"], tz=timezone.utc
                )
                if post.get("created_utc")
                else None,
            )
            session.add(mention)
        session.commit()
    print(f"Ingested up to {len(posts)} Reddit posts (filtered by luxury keywords).")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()
    ingest(args.limit)


if __name__ == "__main__":
    main()
