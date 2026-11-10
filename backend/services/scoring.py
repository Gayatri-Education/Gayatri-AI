import json
from sqlalchemy import select
from backend.models import Answer, PaperQuestion, Result, Paper


def finalize(db, attempt, timestamp, automatic=False):
    if attempt.status != "in_progress":
        return
    paper = db.get(Paper, attempt.paper_id)
    responses = {
        a.question_id: a.selected_option
        for a in db.scalars(select(Answer).where(Answer.attempt_id == attempt.id))
    }
    items = db.scalars(
        select(PaperQuestion).where(PaperQuestion.paper_id == paper.id)
    ).all()
    breakdown = {}
    raw = 0.0
    for item in items:
        q = json.loads(item.snapshot_json)
        bucket = breakdown.setdefault(
            q["subject"],
            {
                "total": 0,
                "answered": 0,
                "correct": 0,
                "incorrect": 0,
                "unanswered": 0,
                "ungraded": 0,
            },
        )
        bucket["total"] += 1
        answer = responses.get(item.question_id)
        if not answer:
            bucket["unanswered"] += 1
        else:
            bucket["answered"] += 1
            if not q["correct_option"]:
                bucket["ungraded"] += 1
            elif answer == q["correct_option"]:
                bucket["correct"] += 1
                raw += paper.marks_per_question
            else:
                bucket["incorrect"] += 1
                raw -= paper.negative_marks
    # Practice intentionally has no aggregate grade, even if some keys are later approved.
    scored = paper.mode == "mock"
    db.add(
        Result(
            attempt_id=attempt.id,
            raw_score=raw if scored else None,
            max_score=len(items) * paper.marks_per_question if scored else None,
            breakdown_json=json.dumps(breakdown),
        )
    )
    attempt.status = "auto_submitted" if automatic else "submitted"
    attempt.submitted_at = min(timestamp, attempt.started_at + attempt.duration_seconds)
    db.flush()
