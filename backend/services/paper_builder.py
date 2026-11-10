import json
import random
import secrets
from fastapi import HTTPException
from sqlalchemy import select
from backend.models import Blueprint, Question, Paper, PaperQuestion
from backend.ingestion.answer_keys import approved_options


def build_paper(db, exam, user_id, mode, year=None):
    blueprints = db.scalars(
        select(Blueprint).where(Blueprint.exam_id == exam.id).order_by(Blueprint.id)
    ).all()
    if not blueprints:
        raise HTTPException(409, "No blueprint configured for this exam")
    seed = secrets.token_hex(16)
    rng = random.Random(seed)
    selected = []
    shortages = []
    for section in blueprints:
        query = select(Question).where(
            Question.exam_id == exam.id, Question.subject == section.section
        )
        if mode == "mock":
            query = query.where(
                Question.approved.is_(True), Question.correct_option.is_not(None)
            )
        if year:
            query = query.where(Question.year == year)
        candidates = list(db.scalars(query.order_by(Question.id)))
        if len(candidates) < section.num_questions:
            shortages.append(
                f"{section.section}: need {section.num_questions}, available {len(candidates)}"
            )
        else:
            selected.extend(rng.sample(candidates, section.num_questions))
    if shortages:
        raise HTTPException(
            409,
            "Not enough eligible questions. "
            + "; ".join(shortages)
            + ". Review and approve answer keys or select unscored practice.",
        )
    paper = Paper(
        exam_id=exam.id,
        created_by=user_id,
        mode=mode,
        seed=seed,
        duration_seconds=exam.duration_seconds,
        marks_per_question=exam.marks_per_question,
        negative_marks=exam.negative_marks,
    )
    db.add(paper)
    db.flush()
    for index, q in enumerate(selected):
        # Full immutable snapshot: subsequent admin edits cannot change this paper's scoring.
        snapshot = {
            key: getattr(q, key)
            for key in [
                "text",
                "subject",
                "difficulty",
                "year",
                "correct_option",
                "explanation",
                "answer_key_source",
                "reference_image",
                "review_flags",
                "approved",
                "external_id",
            ]
        }
        snapshot["options"] = json.loads(q.options_json)
        snapshot["accepted_options"] = approved_options(q)
        snapshot["sourced_answer"] = json.loads(q.metadata_json).get("sourced_answer")
        if not q.approved:
            snapshot["correct_option"] = None
            snapshot["explanation"] = ""
            snapshot["answer_key_source"] = ""
        db.add(
            PaperQuestion(
                paper_id=paper.id,
                question_id=q.id,
                order_index=index,
                snapshot_json=json.dumps(snapshot),
            )
        )
    db.flush()
    return paper
