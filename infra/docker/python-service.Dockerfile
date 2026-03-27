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
    pip install --no-cache-dir /workspace/service && \
    if [ "$SERVICE_PATH" = "apps/apply-service" ]; then \
      apt-get update && \
      apt-get install -y --no-install-recommends fluxbox x11vnc novnc websockify xvfb && \
      rm -rf /var/lib/apt/lists/* && \
      python -m playwright install --with-deps chromium && \
      chmod +x /workspace/service/docker-entrypoint.sh; \
    fi

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${SERVICE_PORT:-8000}"]
