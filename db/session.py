import os
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def get_database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://lvbp:lvbp_dev@localhost:5432/luxury_bags",
    )


@lru_cache
def get_engine():
    return create_engine(get_database_url(), pool_pre_ping=True)


def get_session_factory():
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)
