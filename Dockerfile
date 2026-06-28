# Stage 1: Build dependencies and pre-download InsightFace models
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

RUN uv run python -c "from insightface.app import FaceAnalysis; FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider']).prepare(ctx_id=0, det_size=(640, 640))"

# Stage 2: Production runtime
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libsm6 \
    libxext6 \
    libxrender1 \
    util-linux \
    && rm -rf /var/lib/apt/lists/*

# CHANGED: create a "shared" group with a fixed GID, add appuser to it
RUN groupadd -g 9999 shared \
    && useradd --create-home --shell /bin/bash -G shared appuser

ENV HOME=/home/appuser

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /root/.insightface /home/appuser/.insightface
COPY --chown=appuser:appuser . .

# CHANGED: entrypoint script that fixes shared-storage permissions as root,
# then drops down to appuser before running the real command
COPY <<-'ENTRYPOINT' /usr/local/bin/docker-entrypoint.sh
#!/bin/sh
set -e

SHARED_DIR="${SHARED_STORAGE_PATH:-/shared-storage}"
mkdir -p "$SHARED_DIR"
chgrp -R shared "$SHARED_DIR" 2>/dev/null || true
chmod -R g+rwX "$SHARED_DIR" 2>/dev/null || true
find "$SHARED_DIR" -type d -exec chmod g+s {} + 2>/dev/null || true

exec setpriv --reuid=appuser --regid=shared --init-groups "$@"
ENTRYPOINT

RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# REMOVED: the old "USER appuser" line — the entrypoint now handles
# dropping privileges itself, so this container must start as root

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')" || exit 1

# CHANGED: route startup through the new entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]