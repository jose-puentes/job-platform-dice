# Job Bot

Job Bot is a production-oriented microservice platform for scraping, normalizing, browsing, and applying to jobs with AI-assisted resume and cover letter generation.

## Current phase

This repository currently includes:

- monorepo root structure
- local Docker Compose topology
- shared Python packages
- FastAPI service scaffolds
- Next.js frontend scaffold
- service-owned ORM models and Alembic scaffolds
- shared Celery queue bootstrap
- scrape run orchestration, worker execution, and job ingestion flow
- live gateway-backed jobs and scrape runs pages
- AI generation flow with prompt templates and DOCX output
- apply-service single and batch workflows with manual-assist fallback
- scraper adapter framework with board registry and normalization helpers

## Architecture

See [Phase 1 architecture](/d:/Dev/Job-Hunting/JobBot/dice-bot/docs/architecture/phase-1.md).

## Local development

1. Copy `.env.example` to `.env`.
2. Update PostgreSQL credentials to match your local server.
3. Run `make up`.

## Migrations

Run per service:

- `alembic -c apps/job-service/alembic.ini upgrade head`
- `alembic -c apps/orchestrator-service/alembic.ini upgrade head`
- `alembic -c apps/ai-service/alembic.ini upgrade head`
- `alembic -c apps/apply-service/alembic.ini upgrade head`

## Next implementation targets

- scraper adapters and ingestion pipeline
- public/internal API contracts for jobs, scrape runs, generation, and apply
- queue task payloads and orchestration handlers
- AI generation and DOCX output
- apply engine and batch workflows

## Current pipeline

1. `POST /api/v1/scrape-runs` creates a run in `orchestrator-service`.
2. The orchestrator creates `scrape_tasks` and dispatches Celery jobs.
3. `worker-runner` calls `scraper-service`.
4. `scraper-service` returns normalized jobs.
5. `worker-runner` sends them to `job-service`.
6. `job-service` upserts the canonical searchable catalog.
7. `worker-runner` reports task results back to `orchestrator-service`.

## Scraper status

The scraper-service now includes:

- a board adapter base contract
- a registry for board selection
- reusable normalization helpers
- a `greenhouse` adapter implementation pattern

The current `greenhouse` adapter is still a safe placeholder for a real HTTP-first integration. It demonstrates the correct service shape and normalization path, but it does not yet fetch live board data.

## Current AI and apply flow

1. Resume or cover letter generation creates a generation run in `ai-service`.
2. The worker executes the generation run and stores a DOCX file in `DOCUMENT_STORAGE_PATH`.
3. Single apply creates an `apply_run` with one attempt.
4. Batch apply creates one `apply_run` with many queued attempts.
5. Each apply attempt ensures documents exist, selects an apply strategy, and records the result.
6. Unsupported auto-apply scenarios fall back to `manual_assist` instead of pretending full automation.
