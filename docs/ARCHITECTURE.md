# Architecture

The browser uses React/Vite/Tailwind; FastAPI serves REST JSON and the production frontend from one origin. Development Vite proxies `/api`, avoiding a permissive CORS policy. SQLAlchemy supports the SQLite pilot. No desktop dependency, model download or LM Studio service is required for curated-bank practice.

`backend/ingestion/bulk_import.py` validates the uploaded CSVs, exact question hashes and every image mapping before inserting any questions. The two differently named source-image ZIPs were combined into `data/images/question_images/`; all 942 uppercase-folder image paths were normalized. Diagrams remain in `data/images/diagrams/`. Uploaded reports and flags remain unchanged. Importing never overwrites human review.

The exam blueprint contains per-subject quotas. `paper_builder.py` samples without replacement and records a random seed. Paper questions snapshot text, options, metadata and eligible verified keys. A reviewer changing the live bank cannot retroactively change a student's paper. This version creates a private paper per attempt; shared scheduled cohorts and defensible percentile calculations are deferred.

Each attempt stores a server start timestamp and duration. Answers and finalization serialize through a database write lock; the deadline and ownership are checked under that lock. Expired answers are rejected and existing answers are finalized, even when the client never presses submit. A background sweeper runs every ten seconds and on startup. Every attempt/result read also checks expiry. Repeated submit calls return the existing outcome. Results have a unique constraint per attempt.

Cookie JWTs expire in eight hours. Passwords use salted PBKDF2-SHA256 (600,000 iterations). Users self-register as students only; administrators are created through a private CLI prompt. Origin checks reject cross-origin writes; cookies are HttpOnly and SameSite=Strict. Enable Secure cookies behind HTTPS. APIs do not return keys before finalization; image paths are validated and authenticated. API responses are not cached. Returned metadata and text are rendered as plain React text, not HTML.

Practice results remain unscored. Approved answer keys can be reviewed per question after submission; unapproved keys are removed from paper snapshots. Only approved, keyed records enter scored mocks. No LLM output is treated as verified. Source flag resolution is recorded through an explicit reviewer confirmation and an audit record; original extraction flags remain for provenance.

SQLite is appropriate for small pilots, not an untested large simultaneous exam cohort. Before such a deployment, run load tests, move to PostgreSQL with explicit migrations, and introduce a shared job runner and rate limiting. Adding a different database URL also needs its supported driver, a schema migration/data transfer plan, and validation; it is not a proven zero-step production migration.
