import json
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from backend.main import app, expire_stale
from backend.database import SessionLocal
from backend.models import User, Question, Attempt, Answer, Result, ReviewAudit, now
from backend.tests.conftest import register


def start(client, exam, mode="mock"):
    response = client.post("/api/attempts", json={"exam_id": exam, "mode": mode})
    assert response.status_code == 201, response.text
    return response.json()


def test_auth_roles_csrf_and_student_isolation(client, exam):
    first = register(client)
    a = start(client, exam)
    assert not any("correct_option" in q or "explanation" in q for q in a["questions"])
    assert client.get("/api/admin/questions").status_code == 403
    assert (
        client.post(
            "/api/auth/logout", headers={"Origin": "https://evil.test"}
        ).status_code
        == 403
    )
    assert client.get("/api/auth/me").status_code == 200
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get(f"/api/attempts/{a['id']}").status_code == 401
    second = register(client, "other@example.com")
    assert first["id"] != second["id"]
    for path in [f"/api/attempts/{a['id']}", f"/api/results/{a['id']}"]:
        assert client.get(path).status_code == 404
    assert client.post(f"/api/attempts/{a['id']}/submit").status_code == 404
    assert (
        client.put(
            f"/api/attempts/{a['id']}/answer",
            json={"question_id": a["questions"][0]["id"], "selected_option": "A"},
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/auth/login",
            json={"email": "student@example.com", "password": "incorrect-password"},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/auth/login",
            json={"email": "student@example.com", "password": "long-test-password"},
        ).status_code
        == 200
    )


def test_scores_negative_marking_snapshot_and_idempotency(client, exam):
    register(client)
    a = start(client, exam)
    assert client.get(f"/api/results/{a['id']}").status_code == 409
    with SessionLocal() as db:
        q = db.get(Question, a["questions"][0]["id"])
        q.correct_option = "D"
        q.text = "Edited after paper generation"
        db.commit()
    for q, choice in zip(a["questions"], ["A", "B"]):
        assert (
            client.put(
                f"/api/attempts/{a['id']}/answer",
                json={"question_id": q["id"], "selected_option": choice},
            ).status_code
            == 200
        )
    assert (
        client.put(
            f"/api/attempts/{a['id']}/answer",
            json={"question_id": 99999, "selected_option": "A"},
        ).status_code
        == 400
    )
    assert (
        client.put(
            f"/api/attempts/{a['id']}/answer",
            json={"question_id": a["questions"][0]["id"], "selected_option": "E"},
        ).status_code
        == 422
    )
    for _ in range(2):
        assert client.post(f"/api/attempts/{a['id']}/submit").status_code == 200
    result = client.get(f"/api/results/{a['id']}").json()
    assert result["raw_score"] == 3 and result["max_score"] == 12
    assert result["questions"][0]["correct_option"] == "A"
    assert result["questions"][0]["text"] != "Edited after paper generation"
    assert result["percentile"] is None
    assert (
        client.put(
            f"/api/attempts/{a['id']}/answer",
            json={"question_id": a["questions"][0]["id"], "selected_option": "B"},
        ).status_code
        == 409
    )
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Result)) == 1


def test_late_answers_are_rejected_and_saved_answers_are_scored(client, exam):
    register(client)
    a = start(client, exam)
    q = a["questions"][0]
    assert (
        client.put(
            f"/api/attempts/{a['id']}/answer",
            json={"question_id": q["id"], "selected_option": "A"},
        ).status_code
        == 200
    )
    with SessionLocal() as db:
        attempt = db.get(Attempt, a["id"])
        attempt.started_at = now() - 120
        db.commit()
    assert (
        client.put(
            f"/api/attempts/{a['id']}/answer",
            json={"question_id": q["id"], "selected_option": "B"},
        ).status_code
        == 409
    )
    result = client.get(f"/api/results/{a['id']}").json()
    assert result["status"] == "auto_submitted"
    assert result["raw_score"] == 4
    assert result["questions"][0]["selected_option"] == "A"
    with SessionLocal() as db:
        saved = db.get(Attempt, a["id"])
        assert saved.submitted_at == saved.started_at + saved.duration_seconds


def test_background_expiry_without_student_request(client, exam):
    register(client)
    a = start(client, exam)
    with SessionLocal() as db:
        attempt = db.get(Attempt, a["id"])
        attempt.started_at = now() - 120
        db.commit()
    expire_stale()
    expire_stale()
    with SessionLocal() as db:
        assert db.get(Attempt, a["id"]).status == "auto_submitted"
        assert db.scalar(select(func.count()).select_from(Result)) == 1


def test_missing_keys_block_mock_but_allow_unscored_practice(client, exam):
    register(client)
    with SessionLocal() as db:
        for q in db.scalars(select(Question)):
            q.approved = False  # Even a draft key must not be shown as verified.
        db.commit()
    blocked = client.post("/api/attempts", json={"exam_id": exam, "mode": "mock"})
    assert blocked.status_code == 409 and "available 0" in blocked.text
    a = start(client, exam, "practice")
    client.put(
        f"/api/attempts/{a['id']}/answer",
        json={"question_id": a["questions"][0]["id"], "selected_option": "A"},
    )
    client.post(f"/api/attempts/{a['id']}/submit")
    result = client.get(f"/api/results/{a['id']}").json()
    assert result["raw_score"] is None and result["max_score"] is None
    assert all(q["correct_option"] is None for q in result["questions"])
    assert sum(b["ungraded"] for b in result["topic_breakdown"].values()) == 1


def test_admin_review_requires_confirmation_and_records_audit(client, exam):
    user = register(client)
    with SessionLocal() as db:
        db.get(User, user["id"]).role = "admin"
        q = db.scalar(select(Question))
        q.approved = False
        db.commit()
        qid = q.id
    rows = client.get("/api/admin/questions").json()
    assert rows["total"] == 1
    body = {
        "correct_option": "C",
        "answer_key_source": "Reviewed official key page 2",
        "explanation": "Detailed reviewer explanation",
        "confirm_source_reviewed": False,
        "version": 1,
    }
    assert (
        client.put(f"/api/admin/questions/{qid}/review", json=body).status_code == 422
    )
    body["confirm_source_reviewed"] = True
    assert (
        client.put(f"/api/admin/questions/{qid}/review", json=body).status_code == 200
    )
    assert (
        client.put(f"/api/admin/questions/{qid}/review", json=body).status_code == 409
    )
    with SessionLocal() as db:
        q = db.get(Question, qid)
        assert q.correct_option == "C" and q.approved and q.version == 2
        assert db.scalar(select(func.count()).select_from(ReviewAudit)) == 1


def test_answer_clear_upsert_and_concurrent_submit(client, exam):
    register(client)
    a = start(client, exam)
    payload = {"question_id": a["questions"][0]["id"], "selected_option": "A"}
    assert (
        client.put(f"/api/attempts/{a['id']}/answer", json=payload).status_code == 200
    )
    assert (
        client.put(
            f"/api/attempts/{a['id']}/answer", json=payload | {"selected_option": None}
        ).status_code
        == 200
    )
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Answer)) == 1

    def submit(_):
        return client.post(f"/api/attempts/{a['id']}/submit").status_code

    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(submit, range(4))) == [200] * 4
    result = client.get(f"/api/results/{a['id']}").json()
    assert result["raw_score"] == 0
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Result)) == 1
