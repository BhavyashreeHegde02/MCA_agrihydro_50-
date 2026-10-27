# Jalachakra API image.
#
# Built from the repository root, because the service imports the `ml` package
# that lives beside `backend/`:
#     docker build -f backend/Dockerfile -t jalachakra-api .
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app:/app/backend

WORKDIR /app

# libgomp is required by xgboost's runtime; curl is used by the healthcheck.
RUN apt-get update \
 && apt-get install --no-install-recommends -y libgomp1 curl \
 && rm -rf /var/lib/apt/lists/*

# Dependencies first, so a source change does not invalidate the layer.
COPY backend/requirements.txt ./deps/requirements.txt
RUN pip install --upgrade pip \
 && pip install -r deps/requirements.txt

# Application code and the assets the service reads at runtime.
COPY ml/ ./ml/
COPY backend/ ./backend/
COPY config/ ./config/
COPY datasets/cleaned/ ./datasets/cleaned/
COPY datasets/processed/ ./datasets/processed/
COPY artifacts/ ./artifacts/

# Run as a non-root user.
RUN useradd --create-home --uid 10001 jalachakra \
 && chown -R jalachakra:jalachakra /app
USER jalachakra

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
