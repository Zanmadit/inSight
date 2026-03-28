# ---------- Stage 1: Build ----------
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /build

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app/ app/
COPY README.md ./
RUN uv sync --frozen --no-dev

# ---------- Stage 2: Runtime ----------
FROM python:3.12-slim AS runtime

RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /srv

COPY --from=builder /build/.venv .venv
COPY --from=builder /build/app app

ENV PATH="/srv/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

USER app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
