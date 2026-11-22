# API contract

Interactive OpenAPI documentation is exposed by FastAPI at `/docs`. JSON writes are same-origin; authentication is an eight-hour HttpOnly session cookie. Missing authentication returns 401, another student's attempt returns 404, student access to admin APIs returns 403. Error messages use `{"detail": ...}`. Validation errors return 422.

| Method | Route | Behavior |
| --- | --- | --- |
| GET | `/api/health` | Database connectivity check |
| POST | `/api/auth/register` | `name`, `email`, `password` (10–128 characters); creates student and cookie |
| POST | `/api/auth/login` | Email/password; sets cookie |
| POST | `/api/auth/logout` | Clears cookie |
| GET | `/api/auth/me` | Current public user |
| GET | `/api/exams` | Blueprints, section bank counts, approved counts, years, mock readiness |
| POST | `/api/attempts` | `{exam_id, mode: "practice" or "mock", year?: integer}`; atomically creates immutable paper and starts timer |
| GET | `/api/attempts` | Current student's latest 100 attempts; expiry checked |
| GET | `/api/attempts/{id}` | Paper without keys, saved responses, deadline, server time and remaining seconds |
| PUT | `/api/attempts/{id}/answer` | `{question_id, selected_option: "A"–"D" or null}`; upsert/clear, rejects late or foreign questions |
| POST | `/api/attempts/{id}/submit` | Finalize once; idempotent |
| GET | `/api/results/{id}` | Available after finalization; grade or null, immutable review, subject breakdown; percentile deliberately null |
| GET | `/api/images/{relative_path}` | Authenticated PNG access under the image root only |
| GET | `/api/admin/questions` | Admin; filters `subject`, `year`, exact dataset `question_id`, `status=pending/approved/all`, `offset`, `limit` (max 100) |
| PUT | `/api/admin/questions/{id}/review` | Admin; `correct_option`, `answer_key_source`, `explanation`, `confirm_source_reviewed=true`, `version`, optional `accepted_options` (unique A–D choices including `correct_option`); stale version returns 409 |
| GET | `/api/admin/reports` | Admin; counts of students/users, questions, approvals, extraction flags, attempts and completions |

A mock paper with an insufficient reviewed pool returns 409 with section shortages. It never falls back to guessed keys or silent AI generation. Practice is explicitly unscored. Quotas, duration and marking are frozen at paper creation. Correct +4, incorrect −1, unanswered 0 under the seeded short-study blueprint; raw score may be negative.

`GET /api/admin/answer-key-coverage` returns the static research report for administrators. Post-submission results now include `accepted_options` for approved scoring keys and a separately labelled `sourced_answer` research proposal. Neither field is exposed during active attempts. See [source/key policy](ANSWER_KEYS.md).
