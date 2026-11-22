import asyncio
import hashlib
import json
import logging
from contextlib import asynccontextmanager
from urllib.parse import urlsplit
from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, func, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from backend import models
from backend.config import ROOT, DATA_DIR
from backend.database import Base, engine, SessionLocal, get_db
from backend.models import (
    User,
    Exam,
    Blueprint,
    Question,
    Paper,
    PaperQuestion,
    Attempt,
    Answer,
    Result,
    ReviewAudit,
    now,
)
from backend.auth import (
    current_user,
    admin_user,
    password_hash,
    verify_password,
    DUMMY_HASH,
    set_session,
    COOKIE_NAME,
)
from backend.schemas import (
    Register,
    Credentials,
    PaperRequest,
    AnswerRequest,
    ReviewRequest,
)
from backend.services.paper_builder import build_paper
from backend.services.session_manager import lock_attempt
from backend.services.scoring import finalize


def expire_stale():
    with SessionLocal() as db:
        ids = list(
            db.scalars(
                select(Attempt.id).where(
                    Attempt.status == "in_progress",
                    Attempt.started_at + Attempt.duration_seconds <= now(),
                )
            )
        )
    for attempt_id in ids:
        with SessionLocal() as db:
            lock_attempt(db, attempt_id)
            db.commit()


async def expiry_loop():
    while True:
        await asyncio.sleep(10)
        try:
            await asyncio.to_thread(expire_stale)
        except SQLAlchemyError:
            logging.getLogger(__name__).exception(
                "Attempt expiry sweep failed; retrying on next interval"
            )


@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    await asyncio.to_thread(expire_stale)
    task = asyncio.create_task(expiry_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Gayatri Exam Portal", version="0.1.0", lifespan=lifespan)


@app.middleware("http")
async def browser_security(request: Request, call_next):
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        origin = request.headers.get("origin")
        if origin and urlsplit(origin).netloc != request.headers.get("host"):
            return JSONResponse(
                {"detail": "Cross-origin write rejected"}, status_code=403
            )
        if request.headers.get("sec-fetch-site") == "cross-site":
            return JSONResponse(
                {"detail": "Cross-site write rejected"}, status_code=403
            )
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


def user_view(user):
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}


@app.get("/api/health")
def health(db=Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "service": "gayatri-exam-portal"}


@app.post("/api/auth/register", status_code=201)
def register(body: Register, response: Response, db=Depends(get_db)):
    user = User(
        name=body.name,
        email=body.email,
        password_hash=password_hash(body.password),
        role="student",
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Email already registered")
    set_session(response, user)
    return user_view(user)


@app.post("/api/auth/login")
def login(body: Credentials, response: Response, db=Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email))
    valid = verify_password(body.password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid:
        raise HTTPException(401, "Invalid email or password")
    set_session(response, user)
    return user_view(user)


@app.post("/api/auth/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")


@app.get("/api/auth/me")
def me(user=Depends(current_user)):
    return user_view(user)


@app.get("/api/exams")
def exams(db=Depends(get_db)):
    result = []
    for exam in db.scalars(select(Exam).order_by(Exam.id)):
        sections = []
        for bp in db.scalars(
            select(Blueprint).where(Blueprint.exam_id == exam.id).order_by(Blueprint.id)
        ):
            base = [Question.exam_id == exam.id, Question.subject == bp.section]
            total = db.scalar(select(func.count()).select_from(Question).where(*base))
            approved = db.scalar(
                select(func.count())
                .select_from(Question)
                .where(
                    *base,
                    Question.approved.is_(True),
                    Question.correct_option.is_not(None),
                )
            )
            sections.append(
                {
                    "subject": bp.section,
                    "questions": bp.num_questions,
                    "bank_count": total,
                    "approved_count": approved,
                }
            )
        result.append(
            {
                "id": exam.id,
                "name": exam.name,
                "category": exam.category,
                "description": exam.description,
                "duration_seconds": exam.duration_seconds,
                "marks_per_question": exam.marks_per_question,
                "negative_marks": exam.negative_marks,
                "sections": sections,
                "mock_ready": bool(sections)
                and all(s["approved_count"] >= s["questions"] for s in sections),
                "years": list(
                    db.scalars(
                        select(Question.year)
                        .where(Question.exam_id == exam.id, Question.year.is_not(None))
                        .distinct()
                        .order_by(Question.year)
                    )
                ),
            }
        )
    return result


def attempt_view(db, attempt, include_review=False):
    paper = db.get(Paper, attempt.paper_id)
    responses = {
        a.question_id: a.selected_option
        for a in db.scalars(select(Answer).where(Answer.attempt_id == attempt.id))
    }
    questions = []
    for item in db.scalars(
        select(PaperQuestion)
        .where(PaperQuestion.paper_id == paper.id)
        .order_by(PaperQuestion.order_index)
    ):
        q = json.loads(item.snapshot_json)
        public = {
            key: q[key]
            for key in [
                "text",
                "options",
                "subject",
                "difficulty",
                "year",
                "reference_image",
                "review_flags",
                "external_id",
            ]
        }
        public.update(
            {
                "id": item.question_id,
                "order": item.order_index,
                "selected_option": responses.get(item.question_id),
            }
        )
        if include_review:
            public.update(
                {
                    key: q[key]
                    for key in ["correct_option", "explanation", "answer_key_source"]
                }
            )
        if include_review:
            public["accepted_options"] = q.get(
                "accepted_options", [q["correct_option"]] if q["correct_option"] else []
            )
            public["sourced_answer"] = q.get("sourced_answer")
        questions.append(public)
    timestamp = now()
    return {
        "id": attempt.id,
        "paper_id": paper.id,
        "exam_id": paper.exam_id,
        "mode": paper.mode,
        "status": attempt.status,
        "started_at": attempt.started_at,
        "expires_at": attempt.started_at + attempt.duration_seconds,
        "server_time": timestamp,
        "remaining_seconds": max(
            0, attempt.started_at + attempt.duration_seconds - timestamp
        )
        if attempt.status == "in_progress"
        else 0,
        "duration_seconds": attempt.duration_seconds,
        "questions": questions,
    }


@app.post("/api/attempts", status_code=201)
def start_attempt(body: PaperRequest, user=Depends(current_user), db=Depends(get_db)):
    exam = db.get(Exam, body.exam_id)
    if not exam:
        raise HTTPException(404, "Exam not found")
    paper = build_paper(db, exam, user.id, body.mode, body.year)
    attempt = Attempt(
        user_id=user.id, paper_id=paper.id, duration_seconds=paper.duration_seconds
    )
    db.add(attempt)
    db.flush()
    result = attempt_view(db, attempt)
    db.commit()
    return result


@app.get("/api/attempts")
def list_attempts(user=Depends(current_user), db=Depends(get_db)):
    result = []
    ids = list(
        db.scalars(
            select(Attempt.id)
            .where(Attempt.user_id == user.id)
            .order_by(Attempt.id.desc())
            .limit(100)
        )
    )
    for attempt_id in ids:
        a = lock_attempt(db, attempt_id, user.id)
        p = db.get(Paper, a.paper_id)
        grade = db.scalar(select(Result).where(Result.attempt_id == a.id))
        result.append(
            {
                "id": a.id,
                "mode": p.mode,
                "status": a.status,
                "started_at": a.started_at,
                "exam_name": db.get(Exam, p.exam_id).name,
                "raw_score": grade.raw_score if grade else None,
                "max_score": grade.max_score if grade else None,
            }
        )
    db.commit()
    return result


@app.get("/api/attempts/{attempt_id}")
def get_attempt(attempt_id: int, user=Depends(current_user), db=Depends(get_db)):
    attempt = lock_attempt(db, attempt_id, user.id)
    result = attempt_view(db, attempt)
    db.commit()
    return result


@app.put("/api/attempts/{attempt_id}/answer")
def save_answer(
    attempt_id: int, body: AnswerRequest, user=Depends(current_user), db=Depends(get_db)
):
    a = lock_attempt(db, attempt_id, user.id)
    if a.status != "in_progress":
        db.commit()  # Persist deadline finalization even when rejecting a late answer.
        raise HTTPException(409, "Attempt has ended; answers can no longer be changed")
    if not db.scalar(
        select(PaperQuestion.id).where(
            PaperQuestion.paper_id == a.paper_id,
            PaperQuestion.question_id == body.question_id,
        )
    ):
        raise HTTPException(400, "Question does not belong to this attempt")
    answer = db.scalar(
        select(Answer).where(
            Answer.attempt_id == a.id, Answer.question_id == body.question_id
        )
    )
    if answer:
        answer.selected_option = body.selected_option
    else:
        db.add(
            Answer(
                attempt_id=a.id,
                question_id=body.question_id,
                selected_option=body.selected_option,
            )
        )
    db.commit()
    return {"saved": True, "server_time": now()}


@app.post("/api/attempts/{attempt_id}/submit")
def submit(attempt_id: int, user=Depends(current_user), db=Depends(get_db)):
    a = lock_attempt(db, attempt_id, user.id)
    finalize(db, a, now())
    db.commit()
    return {"id": a.id, "status": a.status}


@app.get("/api/results/{attempt_id}")
def result(attempt_id: int, user=Depends(current_user), db=Depends(get_db)):
    a = lock_attempt(db, attempt_id, user.id)
    if a.status == "in_progress":
        raise HTTPException(409, "Submit the attempt before viewing the result")
    grade = db.scalar(select(Result).where(Result.attempt_id == a.id))
    view = attempt_view(db, a, include_review=True)
    view.update(
        {
            "raw_score": grade.raw_score,
            "max_score": grade.max_score,
            "topic_breakdown": json.loads(grade.breakdown_json),
            "percentile": None,
            "percentile_note": "Not published: attempts currently use individually sampled practice papers, not a comparable exam cohort.",
        }
    )
    db.commit()
    return view


@app.get("/api/admin/questions")
def admin_questions(
    subject: str | None = None,
    question_id: str | None = None,
    year: int | None = None,
    status: str = "pending",
    offset: int = 0,
    limit: int = 25,
    user=Depends(admin_user),
    db=Depends(get_db),
):
    conditions = []
    if question_id:
        conditions.append(Question.external_id == question_id.strip())
    if subject:
        conditions.append(Question.subject == subject)
    if year:
        conditions.append(Question.year == year)
    if status == "pending":
        conditions.append(Question.approved.is_(False))
    elif status == "approved":
        conditions.append(Question.approved.is_(True))
    elif status != "all":
        raise HTTPException(422, "Unknown review status")
    total = db.scalar(select(func.count()).select_from(Question).where(*conditions))
    items = []
    for q in db.scalars(
        select(Question)
        .where(*conditions)
        .order_by(Question.id)
        .offset(max(0, offset))
        .limit(min(100, max(1, limit)))
    ):
        items.append(
            {
                key: getattr(q, key)
                for key in [
                    "id",
                    "external_id",
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
                    "version",
                ]
            }
            | {
                "options": json.loads(q.options_json),
                "metadata": json.loads(q.metadata_json),
            }
        )
    return {"items": items, "total": total}


@app.put("/api/admin/questions/{question_id}/review")
def review(
    question_id: int, body: ReviewRequest, user=Depends(admin_user), db=Depends(get_db)
):
    from sqlalchemy import update

    if not body.confirm_source_reviewed:
        raise HTTPException(
            422,
            "Source image and flagged content must be manually reviewed before approval",
        )
    q = db.get(Question, question_id)
    if not q:
        raise HTTPException(404, "Question not found")
    metadata = json.loads(q.metadata_json)
    metadata["approved_answer"] = {
        "accepted_options": body.accepted_options,
        "question_sha256": hashlib.sha256(q.text.encode()).hexdigest(),
        "source": body.answer_key_source,
    }
    values = {
        "metadata_json": json.dumps(metadata),
        "correct_option": body.correct_option,
        "answer_key_source": body.answer_key_source,
        "explanation": body.explanation,
        "approved": True,
        "version": body.version + 1,
    }
    updated = db.execute(
        update(Question)
        .where(Question.id == question_id, Question.version == body.version)
        .values(**values)
    )
    if not updated.rowcount:
        raise HTTPException(409, "Question changed during review; reload before saving")
    db.add(
        ReviewAudit(
            question_id=question_id,
            reviewer_id=user.id,
            changes_json=json.dumps(
                {k: v for k, v in values.items() if k != "metadata_json"}
                | {"accepted_options": body.accepted_options}
            ),
        )
    )
    db.commit()
    return {"approved": True, "version": body.version + 1}


@app.get("/api/admin/reports")
def reports(user=Depends(admin_user), db=Depends(get_db)):
    return {
        "users": db.scalar(select(func.count()).select_from(User)),
        "questions": db.scalar(select(func.count()).select_from(Question)),
        "approved": db.scalar(
            select(func.count())
            .select_from(Question)
            .where(Question.approved.is_(True))
        ),
        "flagged": db.scalar(
            select(func.count())
            .select_from(Question)
            .where(Question.review_flags != "")
        ),
        "attempts": db.scalar(select(func.count()).select_from(Attempt)),
        "completed": db.scalar(select(func.count()).select_from(Result)),
    }


# Authenticated image serving prevents arbitrary file reads and directory traversal.
@app.get("/api/images/{image_path:path}")
def question_image(image_path: str, user=Depends(current_user)):
    base = (DATA_DIR / "images").resolve()
    target = (base / image_path).resolve()
    if (
        not target.is_relative_to(base)
        or target.suffix.lower() != ".png"
        or not target.is_file()
    ):
        raise HTTPException(404, "Image not found")
    return FileResponse(target, media_type="image/png")


@app.get("/api/admin/answer-key-coverage")
def answer_key_coverage(user=Depends(admin_user)):
    return json.loads((DATA_DIR / "answer_keys/neet/coverage_report.json").read_text())


DIST = ROOT / "frontend" / "dist"
if DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="frontend-assets")

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str):
        if path.startswith("api/"):
            raise HTTPException(404, "API endpoint not found")
        return FileResponse(DIST / "index.html")
