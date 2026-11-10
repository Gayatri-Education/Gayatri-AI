"""Run with python -m scripts.seed_db from the repository root."""

from backend.database import Base, engine, SessionLocal
from backend import models
from backend.ingestion.bulk_import import import_neet
from backend.ingestion.answer_keys import import_answer_keys

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        print(import_neet(db))
        print(import_answer_keys(db))
        db.commit()
