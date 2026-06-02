"""Apply analytics SQL views to the database."""

import os
import sys

from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.session import get_engine

VIEWS_DIR = os.path.join(os.path.dirname(__file__), "views")


def apply_views():
    engine = get_engine()
    files = sorted(f for f in os.listdir(VIEWS_DIR) if f.endswith(".sql"))
    with engine.connect() as conn:
        for filename in files:
            path = os.path.join(VIEWS_DIR, filename)
            with open(path, encoding="utf-8") as f:
                sql = f.read()
            conn.execute(text(sql))
            conn.commit()
            print(f"Applied {filename}")
    print("All views applied.")


if __name__ == "__main__":
    apply_views()
