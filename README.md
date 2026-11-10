# Gayatri Exam Portal

A NEET practice portal built from the supplied [15-day conversion plan](docs/Gayatri_Exam_Portal_15Day_Plan.pdf), with FastAPI, SQLAlchemy, SQLite, and React/Vite/Tailwind. This first implementation replaces the desktop entry point with a multi-user web workflow. The original Flet application remains in `legacy/desktop/` for reference; its committed chat database has been removed from the current tree, with a local backup outside the repository.

## What works

- Student registration and sign-in using password hashing and HttpOnly JWT cookies.
- A validated bank of **2,240 NEET questions**, covering supplied papers labelled 2015–2026, with **2,240 original source images**. The importer checks row hashes, subjects, years and image mappings, and retains existing reviews on repeat import.
- A clearly labelled **15-question, 20-minute short practice blueprint**: five questions per subject. This is a study session, not an official full-length NEET paper.
- Randomized, non-repeating papers; source-year filters; saved responses; a question palette; local flags; server-enforced timing and automatic submission.
- Immutable paper and answer-key snapshots, negative marking for reviewed mocks, and subject summaries.
- Administrator review with source metadata, images, verified key citations, explanations, revision checks and an audit trail.

**The supplied CSV has no answer keys.** All imported records begin unapproved, including the 633 records flagged for extraction review. Unscored practice is available immediately. Scored mocks remain blocked until each section has sufficient manually approved keys. No answers, official difficulty ratings, percentiles, or paper authenticity are invented. Practice uses bank questions only; AI gap-fill is not wired into this release.

## Run locally

Requires Python 3.10+ and Node.js 22.12+ (validated here with Python 3.12 and Node 24).

```bash
bash scripts/setup.sh
.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open the running service in your own browser. The built React frontend and API share the same origin. To work on React with hot reload, run `npm run dev --prefix frontend` in a second terminal; Vite proxies `/api` to the backend.

No administrator password is shipped. Create an account using the private prompt:

```bash
.venv/bin/python -m scripts.create_admin --email your-email@example.com --name 'Your Name'
```

Sign in as that administrator to access **Question review**. Do not approve a record based only on its automated difficulty or OCR-confidence label. Inspect all choices against the original image and provide a sourced answer key and explanation.

## Validate

```bash
.venv/bin/python -m pytest
npm run build --prefix frontend
# With the built portal running and Chromium installed:
cd frontend
npx playwright test
```

The API tests use a separate temporary database. Browser tests create a student in the running development database and complete a real unscored attempt. Playwright uses `/usr/bin/chromium` by default on this cloud machine; set `PLAYWRIGHT_CHROMIUM_EXECUTABLE` to another installed Chromium path when needed.

See [architecture](docs/ARCHITECTURE.md), [API contract](docs/API_SPEC.md), [database schema](docs/DB_SCHEMA.md), [deployment](docs/DEPLOYMENT.md), and [implementation status](docs/IMPLEMENTATION_STATUS.md). Dataset provenance and extraction limitations are preserved in [the supplied dataset README](data/question_bank/neet/README.md).
