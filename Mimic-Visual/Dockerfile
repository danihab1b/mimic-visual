# ===========================================================================
# Mimic-Visual Dockerfile
# Multi-stage build: base -> production
#
# Default image: CPU-only, surya OCR, sentence-transformers embeddings.
# To add easyocr/doctr, create a derived image or use the [all] extra.
# ===========================================================================

# ---------------------------------------------------------------------------
# Stage 1: base — system deps + Python + Playwright Chromium
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        wget \
        gnupg \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Playwright system deps + Chromium
RUN pip install --no-cache-dir playwright \
    && playwright install --with-deps chromium

# ---------------------------------------------------------------------------
# Stage 2: deps — install Python dependencies (CPU-only)
#
# Core + render + surya OCR + sentence-transformers embeddings.
# Pin torch to CPU-only variant to avoid pulling CUDA packages.
# ---------------------------------------------------------------------------
FROM base AS deps

WORKDIR /app

COPY pyproject.toml ./

# Force CPU-only torch before installing anything that depends on it
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir ".[render,ocr-surya,embed]"

# ---------------------------------------------------------------------------
# Stage 3: production — copy source + set entrypoint
# ---------------------------------------------------------------------------
FROM deps AS production

WORKDIR /app

COPY src/ ./src/
COPY visrag.yaml ./
COPY entrypoint.sh ./

RUN chmod +x entrypoint.sh

# Runtime directories
RUN mkdir -p /app/pages /app/index /app/config

ENV PYTHONPATH=/app/src \
    VISRAG_CONFIG=/app/visrag.yaml

EXPOSE 30001

ENTRYPOINT ["./entrypoint.sh"]
CMD ["serve"]
