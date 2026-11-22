import csv
import shutil
from pathlib import Path
import pytest
from sqlalchemy import select, func
from backend.config import DATA_DIR
from backend.database import SessionLocal
from backend.ingestion.bulk_import import import_neet, validate_package
from backend.models import Question


def test_real_dataset_import_is_complete_and_repeatable():
    with SessionLocal() as db:
        assert import_neet(db) == {"validated": 2240, "inserted": 2240, "retained": 0}
        q = db.scalar(select(Question))
        q.explanation = "Keep reviewer work"
        db.commit()
        assert import_neet(db)["inserted"] == 0
        assert db.get(Question, q.id).explanation == "Keep reviewer work"
        assert (
            db.scalar(
                select(func.count())
                .select_from(Question)
                .where(Question.approved.is_(True))
            )
            == 0
        )
        assert (
            db.scalar(
                select(func.count())
                .select_from(Question)
                .where(Question.review_flags != "")
            )
            == 633
        )
        assert (
            db.scalar(
                select(func.count())
                .select_from(Question)
                .where(Question.subject == "Biology")
            )
            == 1120
        )


def test_corrupted_question_and_missing_image_are_rejected(tmp_path):
    source = DATA_DIR / "question_bank" / "neet"
    for name in ["neet_pyq.csv", "question_metadata.csv", "image_map.csv"]:
        shutil.copy(source / name, tmp_path / name)
    with (tmp_path / "neet_pyq.csv").open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)
    rows[0]["question"] += " tampered"
    with (tmp_path / "neet_pyq.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(ValueError, match="hash mismatch"):
        validate_package(tmp_path, DATA_DIR / "images")
    with pytest.raises(ValueError, match="Missing or unsafe"):
        validate_package(source, tmp_path)
