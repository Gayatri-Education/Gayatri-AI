import os
import tempfile
from pathlib import Path

TEST_STATE = tempfile.TemporaryDirectory(prefix="gayatri-tests-")
os.environ["PORTAL_STATE_DIR"] = TEST_STATE.name
os.environ["DATABASE_URL"] = f"sqlite:///{Path(TEST_STATE.name) / 'test.db'}"
os.environ["PORTAL_SECRET"] = "test-only-session-secret-never-used-in-production-123"

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine, SessionLocal
from backend.models import Exam, Blueprint, Question
import json


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def exam():
    with SessionLocal() as db:
        exam = Exam(
            name="Test blueprint",
            category="NEET",
            description="Fixture only",
            duration_seconds=60,
            marks_per_question=4,
            negative_marks=1,
        )
        db.add(exam)
        db.flush()
        exam_id = exam.id
        for i, subject in enumerate(["Physics", "Chemistry", "Biology"]):
            db.add(Blueprint(exam_id=exam.id, section=subject, num_questions=1))
            db.add(
                Question(
                    exam_id=exam.id,
                    external_id=f"fixture-{i}",
                    text=f"{subject} fixture question",
                    options_json=json.dumps(
                        {
                            "A": "Correct fixture answer",
                            "B": "Wrong fixture answer",
                            "C": "Another distractor",
                            "D": "Last distractor",
                        }
                    ),
                    subject=subject,
                    difficulty="Easy",
                    year=2025,
                    approved=True,
                    correct_option="A",
                    answer_key_source="Unit-test fixture",
                    explanation="Fixture explanation",
                )
            )
        db.commit()
    return exam_id


def register(client, email="student@example.com"):
    result = client.post(
        "/api/auth/register",
        json={"name": "Test Student", "email": email, "password": "long-test-password"},
    )
    assert result.status_code == 201, result.text
    return result.json()
