# Local Development

## Services

- `web`: Next.js frontend
- `api-gateway`: public REST entry point
- `job-service`: jobs schema owner
- `orchestrator-service`: scraper schema owner
- `worker-service`: worker health/control API
- `worker-runner`: Celery execution runtime
- `ai-service`: AI schema owner
- `apply-service`: apply schema owner
- `notification-service`: notification scaffold
- `redis`: queue backend

## PostgreSQL

PostgreSQL is expected to run on the host machine and be reachable from Docker via `host.docker.internal`.

## First boot

1. Copy `.env.example` to `.env`.
2. Update PostgreSQL credentials.
3. Start infrastructure with `make up`.
4. Apply migrations for the owning services.

## Migration order

1. `apps/job-service`
2. `apps/orchestrator-service`
3. `apps/ai-service`
4. `apps/apply-service`

## Useful public endpoints

- `POST /api/v1/scrape-runs`
- `GET /api/v1/jobs`
- `GET /api/v1/jobs/{job_id}`
- `POST /api/v1/jobs/{job_id}/documents/resume`
- `POST /api/v1/jobs/{job_id}/documents/cover-letter`
- `GET /api/v1/jobs/{job_id}/documents`
- `POST /api/v1/jobs/{job_id}/apply`
- `POST /api/v1/apply-runs`
- `GET /api/v1/applications`

## Current limitations

- scraper adapters are framework-ready, but live board-specific fetching/parsing is still incomplete
- AI generation falls back to a development document when `OPENAI_API_KEY` is not configured
- apply automation intentionally falls back to `manual_assist` when true auto-apply is not realistic
