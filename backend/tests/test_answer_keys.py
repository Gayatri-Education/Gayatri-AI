import hashlib
import json
import shutil
from pathlib import Path
import pytest
from sqlalchemy import select
from backend.database import SessionLocal
from backend.config import DATA_DIR
from backend.models import User, Question, ReviewAudit
from backend.ingestion.bulk_import import import_neet
from backend.ingestion.answer_keys import import_answer_keys, read_ledger
from backend.tests.conftest import register

KEY_DIR = DATA_DIR / "answer_keys/neet"


def test_complete_ledger_and_repeat_import_preserve_reviews():
    rows = read_ledger()
    assert len(rows) == 2240
    assert sum(r["status"] == "sourced_candidate" for r in rows) == 947
    assert sum(r["status"] == "conflict" for r in rows) == 74
    assert all(not r["published"] for r in rows)
    by_id = {r["question_id"]: r for r in rows}
    # A real wrong source key must be surfaced as a conflict, not promoted.
    coil = by_id["NEET_2024_PHYSICS_001"]
    assert coil["status"] == "conflict" and not coil["accepted_options"]
    assert {"A", "D"} <= {
        e["accepted_options"][0] for e in coil["evidence"] if e["accepted_options"]
    }
    # OCR on the source puts labels after text in Q62. Never transfer a
    # partially matched label: it would incorrectly turn source B into target C.
    assert by_id["NEET_2025_CHEMISTRY_062"]["status"] == "mapping_required"
    assert not by_id["NEET_2025_CHEMISTRY_062"]["accepted_options"]
    # The mirrored 2025 final key accepts either answer 1 or 2 on Q63.
    multi = by_id["NEET_2025_CHEMISTRY_063"]
    assert any(e["source_answer_options"] == ["A", "B"] for e in multi["evidence"])
    with SessionLocal() as db:
        import_neet(db)
        first = import_answer_keys(db)
        assert first == {
            "attached": 2240,
            "preserved_approved": 0,
            "stale_or_missing": 0,
        }
        q = db.scalar(
            select(Question).where(Question.external_id == "NEET_2025_CHEMISTRY_082")
        )
        assert q.correct_option == "B" and not q.approved
        assert q.explanation == ""
        q.approved = True
        q.correct_option = "D"
        q.explanation = "Retain real reviewer corrections"
        db.commit()
        again = import_answer_keys(db)
        assert again["preserved_approved"] == 1
        assert (
            q.correct_option == "D"
            and q.explanation == "Retain real reviewer corrections"
        )
        conflict = db.scalar(
            select(Question).where(Question.external_id == coil["question_id"])
        )
        assert conflict.correct_option is None and not conflict.approved


def test_ledger_rejects_auto_publication_and_stale_question(tmp_path):
    shutil.copy(KEY_DIR / "sources.json", tmp_path / "sources.json")
    document = json.loads((KEY_DIR / "answer_ledger.json").read_text())
    document["questions"][0]["published"] = True
    (tmp_path / "answer_ledger.json").write_text(json.dumps(document))
    with pytest.raises(ValueError, match="cannot publish"):
        read_ledger(tmp_path)
    with SessionLocal() as db:
        import_neet(db)
        q = db.scalar(select(Question))
        q.text += " edited locally"
        db.commit()
        assert import_answer_keys(db)["stale_or_missing"] == 1


def test_proposed_keys_are_hidden_until_submission_and_never_scored(client, exam):
    register(client)
    with SessionLocal() as db:
        q = db.scalar(select(Question))
        q.approved = False
        q.metadata_json = json.dumps(
            {
                "sourced_answer": {
                    "status": "sourced_candidate",
                    "accepted_options": ["A"],
                    "evidence": [],
                    "published": False,
                }
            }
        )
        db.commit()
    attempt = client.post(
        "/api/attempts", json={"exam_id": exam, "mode": "practice"}
    ).json()
    assert all(
        "sourced_answer" not in q and "accepted_options" not in q
        for q in attempt["questions"]
    )
    client.post(f"/api/attempts/{attempt['id']}/submit")
    result = client.get(f"/api/results/{attempt['id']}").json()
    proposed = next(q for q in result["questions"] if q["sourced_answer"])
    assert proposed["sourced_answer"]["accepted_options"] == ["A"]
    assert proposed["accepted_options"] == [] and proposed["correct_option"] is None
    assert result["raw_score"] is None
    assert client.get("/api/admin/answer-key-coverage").status_code == 403


def test_multiple_accepted_keys_score_either_choice_and_snapshot_is_immutable(
    client, exam
):
    user = register(client)
    with SessionLocal() as db:
        db.get(User, user["id"]).role = "admin"
        q = db.scalar(select(Question))
        qid = q.id
        db.commit()
    payload = {
        "correct_option": "A",
        "accepted_options": ["A", "B"],
        "answer_key_source": "Test fixture for multiple accepted final-key answers",
        "explanation": "Either of two choices earns full credit in this fixture.",
        "confirm_source_reviewed": True,
        "version": 1,
    }
    assert (
        client.put(f"/api/admin/questions/{qid}/review", json=payload).status_code
        == 200
    )
    assert (
        client.put(
            f"/api/admin/questions/{qid}/review",
            json=payload | {"version": 2, "accepted_options": ["B"]},
        ).status_code
        == 422
    )
    attempt = client.post(
        "/api/attempts", json={"exam_id": exam, "mode": "mock"}
    ).json()
    client.put(
        f"/api/attempts/{attempt['id']}/answer",
        json={"question_id": qid, "selected_option": "B"},
    )
    # Later review narrows the bank key; the paper still accepts both old choices.
    assert (
        client.put(
            f"/api/admin/questions/{qid}/review",
            json=payload | {"version": 2, "accepted_options": ["A"]},
        ).status_code
        == 200
    )
    client.post(f"/api/attempts/{attempt['id']}/submit")
    result = client.get(f"/api/results/{attempt['id']}").json()
    assert result["raw_score"] == 4
    reviewed = next(q for q in result["questions"] if q["id"] == qid)
    assert reviewed["accepted_options"] == ["A", "B"]
