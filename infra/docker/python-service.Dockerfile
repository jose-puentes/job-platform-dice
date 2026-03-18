FROM python:3.12-slim

ARG SERVICE_PATH

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

COPY pyproject.toml /workspace/pyproject.toml
COPY packages /workspace/packages
COPY ${SERVICE_PATH} /workspace/service

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
      fastapi \
      uvicorn[standard] \
      pydantic \
      pydantic-settings \
      httpx \
      sqlalchemy \
      alembic \
      psycopg[binary] \
      redis \
      celery \
      openai \
      python-docx && \
    pip install --no-cache-dir /workspace/packages/shared-config && \
    pip install --no-cache-dir /workspace/packages/shared-db && \
    pip install --no-cache-dir /workspace/packages/shared-events && \
    pip install --no-cache-dir /workspace/packages/shared-queue && \
    pip install --no-cache-dir /workspace/packages/shared-types && \
    pip install --no-cache-dir /workspace/packages/shared-utils && \
    pip install --no-cache-dir /workspace/packages/shared-http && \
    pip install --no-cache-dir /workspace/service

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${SERVICE_PORT:-8000}"]
