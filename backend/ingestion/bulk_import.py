"""Validate the supplied NEET package before importing any records."""

import csv
import hashlib
import json
from pathlib import Path
from sqlalchemy import select
from backend.config import DATA_DIR
from backend.models import Exam, Blueprint, Question

COLUMNS = [
    "question",
    "subjects",
    "difficulty",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "year",
]
SUBJECTS = {"Physics", "Chemistry", "Biology"}


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        return reader.fieldnames, rows


def validate_package(directory, images_dir):
    columns, questions = read_csv(directory / "neet_pyq.csv")
    _, metadata = read_csv(directory / "question_metadata.csv")
    if columns != COLUMNS:
        raise ValueError("Question CSV has an unexpected schema")
    if not questions or len(questions) != len(metadata):
        raise ValueError("Question and metadata counts do not match")
    ids, row_ids = set(), set()
    by_row = {}
    for meta in metadata:
        row = int(meta["csv_row"])
        if (
            meta["question_id"] in ids
            or row in row_ids
            or not 1 <= row <= len(questions)
        ):
            raise ValueError("Duplicate IDs or invalid CSV row mapping")
        q = questions[row - 1]
        if (
            hashlib.sha256(q["question"].encode()).hexdigest()
            != meta["question_sha256"]
        ):
            raise ValueError(f"Question hash mismatch at row {row}")
        if q["subjects"] != meta["subject"] or q["subjects"] not in SUBJECTS:
            raise ValueError(f"Invalid subject at row {row}")
        if (
            q["difficulty"] not in {"Easy", "Moderate", "Hard"}
            or not 2015 <= int(q["year"]) <= 2026
        ):
            raise ValueError(f"Invalid difficulty or year at row {row}")
        if any(not isinstance(value, str) or not value.strip() for value in q.values()):
            raise ValueError(f"Empty or malformed cell at row {row}")
        ids.add(meta["question_id"])
        row_ids.add(row)
        by_row[row] = meta
    _, images = read_csv(directory / "image_map.csv")
    references = set()
    for mapping in images:
        row = int(mapping["csv_row"])
        meta = by_row.get(row)
        if (
            not meta
            or mapping["question_id"] != meta["question_id"]
            or mapping["question_sha256"] != meta["question_sha256"]
        ):
            raise ValueError("Image map does not match question metadata")
        path = (images_dir / mapping["image_path"]).resolve()
        if (
            not path.is_relative_to(images_dir.resolve())
            or not path.is_file()
            or path.suffix != ".png"
        ):
            raise ValueError(f"Missing or unsafe source image: {mapping['image_path']}")
        references.add(mapping["image_path"])
    import re

    for row, q in enumerate(questions, 1):
        paths = [by_row[row]["reference_image"]]
        for value in q.values():
            paths.extend(
                path.split(";", 1)[0].strip()
                for path in re.findall(r"\[image:\s*([^\]]+)\]", value)
            )
        if any(path not in references for path in paths):
            raise ValueError(f"Unmapped image in row {row}")
    return questions, by_row


def import_neet(
    db, directory=DATA_DIR / "question_bank" / "neet", images_dir=DATA_DIR / "images"
):
    questions, metadata = validate_package(directory, images_dir)
    exam = db.scalar(select(Exam).where(Exam.name == "NEET PYQ · short practice"))
    if not exam:
        exam = Exam(
            name="NEET PYQ · short practice",
            category="NEET",
            description="15 questions from uploaded 2015–2026 papers: 5 each in Physics, Chemistry and Biology. A 20-minute study session, not a full official NEET simulation.",
            duration_seconds=1200,
            marks_per_question=4,
            negative_marks=1,
        )
        db.add(exam)
        db.flush()
        for subject in ["Physics", "Chemistry", "Biology"]:
            db.add(Blueprint(exam_id=exam.id, section=subject, num_questions=5))
    existing = set(db.scalars(select(Question.external_id)))
    inserted = 0
    for index, q in enumerate(questions, 1):
        meta = metadata[index]
        if meta["question_id"] in existing:
            continue  # Never overwrite a reviewer's corrections on repeat import.
        db.add(
            Question(
                exam_id=exam.id,
                external_id=meta["question_id"],
                text=q["question"],
                options_json=json.dumps(
                    {letter: q[f"option_{letter.lower()}"] for letter in "ABCD"}
                ),
                subject=q["subjects"],
                difficulty=q["difficulty"],
                year=int(q["year"]),
                reference_image=meta["reference_image"],
                review_flags=meta["review_flags"],
                metadata_json=json.dumps(meta),
                approved=False,
                correct_option=None,
                source="bank",
            )
        )
        inserted += 1
    db.flush()
    return {
        "validated": len(questions),
        "inserted": inserted,
        "retained": len(questions) - inserted,
    }
