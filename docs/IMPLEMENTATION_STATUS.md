# Status against the supplied 15-day plan

This change implements the first working NEET slice of the plan using the user's actual files, rather than fabricating SSC/Banking banks or claiming all fifteen days are complete.

| Plan area | Current implementation |
| --- | --- |
| Repository restructure | FastAPI backend, React/Vite/Tailwind frontend, data, scripts, docs; desktop retained in legacy; old chat DB removed from current Git tree |
| Schema and auth | SQLAlchemy pilot tables; email/password sessions; separate administrator creation |
| Real question ingestion | 2,240 uploaded questions and 2,240 images, exact hash and mapping validation, idempotent seeding |
| Question QA | Preserved metadata/review flags, image viewer, explicit answer-key review with citation and audit |
| Exam catalog/blueprint | One NEET short-study blueprint: 15 questions, 20 minutes, 5 per subject. Official full-length blueprint research still required |
| Paper assembly | Random sampling, no repeated question in a paper, immutable snapshots, pool shortage errors |
| Timed exam flow | Start, autosave, clear, navigate, local flag, resume, server expiry, background finalization, submit |
| Results | Unscored study review, approved mock negative marking, subject summaries, attempt history |
| Validation | API/integrity tests, actual dataset importer tests, frontend production build and browser test workflow |
| Deployment | Local setup and container configuration; public deployment, cohort UAT and load testing outstanding |
| Deferred | LM Studio generation, semantic deduplication/RAG, automated scraping/PDF extraction, topic tags, shared exam slots/percentiles, email notifications, a second exam category |

Missing prerequisites: a verified answer-key dataset and human review for scored NEET mocks; a reviewed syllabus and reachable LM Studio model for AI generation; curated banks/blueprints for additional exam categories. Existing desktop model-calling/context modules remain available as references for that later port. No external email or notification was sent.

## Current-instance validation

- Sixteen Python tests passed, including real-upload ingestion, key provenance, multiple-answer scoring, hidden draft keys, and rejection of corrupted/missing assets.
- Two real Chromium browser tests passed: the full student practice/mobile flow, and administrator source/conflict review with no automatic approval.
- Frontend production build passed; `pip check` passed; `npm audit` reported zero vulnerabilities after updating Vite and Playwright.
- Repeated real-dataset seeding inserted zero duplicates and retained existing records.
- Container build, public deployment, live LM Studio integration and GitHub Actions execution have not been validated here. The new workflow performs API, build, audit and browser checks in GitHub when permitted.

## Public answer-source integration

All 2,240 questions now have a research-ledger entry: 947 unapproved answer proposals, 74 conflicts, 889 unresolved question/option mappings, and 330 without a reliable source match. Evidence is pinned to public repository commits and checksums. Admin review and post-attempt study review display the proposals separately from approved keys. Multiple accepted choices are supported in review, immutable snapshots and scoring. No question was automatically approved. Direct NTA-site access remains blocked; see [ANSWER_KEYS.md](ANSWER_KEYS.md) for sources, reproducibility, known wrong keys and remaining work.
