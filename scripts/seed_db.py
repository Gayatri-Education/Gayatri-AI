"""Run with python -m scripts.seed_db from the repository root."""

from backend.database import Base, engine, SessionLocal
from backend import models
from backend.ingestion.bulk_import import import_neet

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        print(import_neet(db))
        db.commit()
