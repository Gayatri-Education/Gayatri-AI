from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)
from backend.database import Base


def now():
    return datetime.now(timezone.utc).timestamp()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(254), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(20), nullable=False, default="student")


class Exam(Base):
    __tablename__ = "exams"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    duration_seconds = Column(Integer, nullable=False, default=1200)
    marks_per_question = Column(Float, nullable=False, default=4)
    negative_marks = Column(Float, nullable=False, default=1)


class Blueprint(Base):
    __tablename__ = "exam_blueprints"
    id = Column(Integer, primary_key=True)
    exam_id = Column(ForeignKey("exams.id"), nullable=False)
    section = Column(String(50), nullable=False)
    num_questions = Column(Integer, nullable=False)
    __table_args__ = (UniqueConstraint("exam_id", "section"),)


class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    exam_id = Column(ForeignKey("exams.id"), nullable=False, index=True)
    external_id = Column(String(100), unique=True, nullable=False)
    text = Column(Text, nullable=False)
    options_json = Column(Text, nullable=False)
    subject = Column(String(50), nullable=False, index=True)
    difficulty = Column(String(20), nullable=False)
    year = Column(Integer, nullable=True)
    correct_option = Column(String(1), nullable=True)
    explanation = Column(Text, nullable=False, default="")
    answer_key_source = Column(Text, nullable=False, default="")
    source = Column(String(20), nullable=False, default="bank")
    reference_image = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=False, default="{}")
    review_flags = Column(Text, nullable=False, default="")
    approved = Column(Boolean, nullable=False, default=False, index=True)
    version = Column(Integer, nullable=False, default=1)


class Paper(Base):
    __tablename__ = "papers"
    id = Column(Integer, primary_key=True)
    exam_id = Column(ForeignKey("exams.id"), nullable=False)
    created_by = Column(ForeignKey("users.id"), nullable=False)
    mode = Column(String(20), nullable=False)
    seed = Column(String(64), nullable=False)
    generated_at = Column(Float, default=now, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    marks_per_question = Column(Float, nullable=False)
    negative_marks = Column(Float, nullable=False)


class PaperQuestion(Base):
    __tablename__ = "paper_questions"
    id = Column(Integer, primary_key=True)
    paper_id = Column(ForeignKey("papers.id"), nullable=False, index=True)
    question_id = Column(ForeignKey("questions.id"), nullable=False)
    order_index = Column(Integer, nullable=False)
    snapshot_json = Column(Text, nullable=False)
    __table_args__ = (
        UniqueConstraint("paper_id", "order_index"),
        UniqueConstraint("paper_id", "question_id"),
    )


class Attempt(Base):
    __tablename__ = "attempts"
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id"), nullable=False, index=True)
    paper_id = Column(ForeignKey("papers.id"), nullable=False, unique=True)
    started_at = Column(Float, default=now, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    submitted_at = Column(Float, nullable=True)
    status = Column(String(30), nullable=False, default="in_progress")


class Answer(Base):
    __tablename__ = "attempt_answers"
    id = Column(Integer, primary_key=True)
    attempt_id = Column(ForeignKey("attempts.id"), nullable=False, index=True)
    question_id = Column(ForeignKey("questions.id"), nullable=False)
    selected_option = Column(String(1), nullable=True)
    __table_args__ = (UniqueConstraint("attempt_id", "question_id"),)


class Result(Base):
    __tablename__ = "results"
    id = Column(Integer, primary_key=True)
    attempt_id = Column(ForeignKey("attempts.id"), unique=True, nullable=False)
    raw_score = Column(Float, nullable=True)
    max_score = Column(Float, nullable=True)
    breakdown_json = Column(Text, nullable=False)


class ReviewAudit(Base):
    __tablename__ = "review_audit"
    id = Column(Integer, primary_key=True)
    question_id = Column(ForeignKey("questions.id"), nullable=False)
    reviewer_id = Column(ForeignKey("users.id"), nullable=False)
    reviewed_at = Column(Float, nullable=False, default=now)
    changes_json = Column(Text, nullable=False)
