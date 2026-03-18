# Phase 1 Architecture

This document captures the approved architecture for the Job Bot platform:

- true microservice boundaries
- service-owned PostgreSQL schemas
- REST for synchronous interactions
- queues and events for background processing
- `job-service` as the only searchable source of truth
- `scraper-service` as adapter execution only
- `orchestrator-service` for scrape lifecycle tracking
- `ai-service` for OpenAI and DOCX generation
- `apply-service` for single and batch application workflows

Phase 2 implementation will build these decisions incrementally.

