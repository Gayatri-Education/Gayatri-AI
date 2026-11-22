# Database schema

SQLAlchemy definitions are in `backend/models.py`. On the initial pilot deployment, startup creates missing tables. `create_all` is **not** a migration framework; schema changes on an existing installation require a reviewed migration and backup.

| Table | Main constraints and purpose |
| --- | --- |
| users | Unique normalized email, salted password hash, student/admin role |
| exams | Unique catalog name, duration, positive/negative marks |
| exam_blueprints | Unique exam/subject section; question quotas |
| questions | Unique dataset ID, preserved source metadata and flags, nullable key, review version, approval status |
| papers | Exam, owner, sampling seed, mode, duration and marking snapshots |
| paper_questions | Unique paper/order and paper/question; immutable serialized question/key snapshot |
| attempts | User, unique paper, server start/duration, finalization timestamp and status |
| attempt_answers | Unique attempt/question; nullable selected option for clearing |
| results | Unique attempt; nullable aggregate grade for practice, subject breakdown JSON |
| review_audit | Reviewer, question, timestamp and approved changes |

Topic analysis currently uses the three subject sections. The uploaded data has no finer topic tags or verified answer keys, so neither is synthesized. Result percentiles are deferred until comparable scheduled cohorts exist. A question approval affects future papers only.

SQLite uses foreign keys, WAL journaling and a 30-second busy timeout. Writable state lives under ignored `var/`, with optional `PORTAL_STATE_DIR` and `DATABASE_URL` overrides. The old tracked chat database is absent from the current tree; historical commits may still contain it.
