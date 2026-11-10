from fastapi import HTTPException
from sqlalchemy import update
from backend.models import Attempt, now
from backend.services.scoring import finalize


def lock_attempt(db, attempt_id, user_id=None):
    # A database write lock serializes answer/submit/expiry on SQLite. On Postgres
    # the UPDATE obtains the row lock before the status/deadline is rechecked.
    query = update(Attempt).where(Attempt.id == attempt_id)
    if user_id is not None:
        query = query.where(Attempt.user_id == user_id)
    changed = db.execute(query.values(status=Attempt.status))
    if not changed.rowcount:
        raise HTTPException(404, "Attempt not found")
    attempt = db.get(Attempt, attempt_id, populate_existing=True)
    timestamp = now()
    if (
        attempt.status == "in_progress"
        and timestamp >= attempt.started_at + attempt.duration_seconds
    ):
        finalize(db, attempt, timestamp, automatic=True)
    return attempt
