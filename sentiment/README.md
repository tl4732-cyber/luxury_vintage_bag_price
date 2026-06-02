# Phase 4: Social Sentiment Ingest

This module ingests brand/model mentions from Reddit and Instagram (official APIs only) into `social_mentions` for correlation with price trends.

## Platforms

| Platform | API | Notes |
|----------|-----|-------|
| Reddit | [PRAW](https://praw.readthedocs.io/) / OAuth2 | Subreddits: `handbags`, `luxurypurses`, `DesignerReps` |
| Instagram | [Graph API](https://developers.facebook.com/docs/instagram-api/) | Business/creator accounts only; no HTML scraping |

## Environment

```bash
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=luxury_vintage_bag_price/1.0
INSTAGRAM_ACCESS_TOKEN=
```

## Run ingest

```bash
python -m sentiment.ingest_reddit --limit 100
python -m sentiment.ingest_instagram --hashtag luxuryhandbags --limit 50
```

## Sentiment scoring

Phase 4 uses a simple lexicon scorer in `sentiment/scoring.py`. Replace with a transformer model (e.g. `distilbert-base-uncased-finetuned-sst-2-english`) when ready.

## Dashboard overlay

API endpoint (future): `GET /api/v1/products/{id}/sentiment` — daily mention volume and average sentiment vs `v_product_price_daily`.
