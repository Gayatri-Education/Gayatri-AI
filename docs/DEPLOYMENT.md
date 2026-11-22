# Development and pilot deployment

Run `bash scripts/setup.sh` from any working directory. It creates `.venv`, installs pinned top-level Python requirements, runs `npm ci` against the committed lockfile, imports the supplied data idempotently, and builds the browser application. Start the service with `.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000`. Check `/api/health` and perform the documented student workflow. This release does not require LM Studio or Hugging Face downloads.

The development JWT signing key is generated once at `var/session.key` with mode 0600. It is never committed. Set `PORTAL_SECRET` to a securely generated value of at least 32 characters for production/multiple processes, and retain it across restarts. Set environment variables in the shell or deployment service; the local Uvicorn command does not automatically load `.env`. Never put secret values in the repository.

## Containers

Copy `.env.example` to `.env`, enter a unique `PORTAL_SECRET`, then run `docker compose up --build -d`. Compose loads `.env`. Port 8000 is bound to loopback by default; use a TLS reverse proxy for browser access. Set `COOKIE_SECURE=true` only behind HTTPS. The container runs as a non-root user and keeps SQLite/state in the `portal_state` volume. Data is validated on startup; a missing/corrupted asset stops seeding rather than publishing an incomplete bank.

Create an administrator interactively:

```bash
docker compose exec portal python -m scripts.create_admin --email admin@example.com --name 'Administrator'
```

Back up the state volume and signing key. For a consistent SQLite backup, use SQLite's online backup API or stop the portal before copying its database; copying a live `.db` file alone can miss WAL updates. Restarting the service finalizes expired attempts. Stopping it does not pause exam time.

## Before public production use

This is a first pilot implementation, not a verified high-volume production deployment. Configure trusted TLS proxy/host rules, distributed authentication rate limiting, monitoring, backups/restore drills, account recovery and retention policy. Cookie logout clears that browser's token; stolen tokens remain valid until expiration, so production token revocation/rotation needs a session store. No default administrator exists. No credentials are required for the uploaded local question bank.

Review all answer keys and source authenticity before claiming official-paper accuracy or launching scored cohorts. Rights to redistribute uploaded papers/images have not been independently established. Assess those rights before public distribution. The source dataset states its years follow supplied filenames and its difficulty ratings are heuristic.

Load-test a representative concurrent cohort before advertising capacity. SQLite's single writer is an MVP limit; large synchronized exams need PostgreSQL, tested migrations, pooled connections and an external expiry worker. Email notifications, scheduling, AI gap-fill, syllabus semantic retrieval, PDF scraping and percentile analytics are separate next-phase work. The container files are supplied for review; a container image has not been built or deployment performed in this session.
