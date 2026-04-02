# inVision U

## Project Overview

inVision U is a full-stack admissions screening platform for university programmes. Applicants complete a profile, essay, and short video; an AI pipeline provides structured essay feedback and an advisory composite score for staff. **AI does not make admission decisions**: it recommends and explains only; the admissions committee has final authority. The product is designed with fairness guardrails: scoring prompts avoid demographic fields, and advisory outputs are clearly labeled for staff and applicants.

## Architecture Diagram

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Browser   │────▶│   Frontend   │────▶│   Backend   │
│  (React)    │     │ (Vite/nginx) │     │  (FastAPI)  │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                 │
                    ┌────────────────────────────┼────────────────────────┐
                    │                            │                        │
                    ▼                            ▼                        ▼
              ┌──────────┐                ┌──────────┐           ┌─────────────┐
              │PostgreSQL│                │  MinIO   │           │ OpenAI API  │
              │    15    │                │  videos  │           │ gpt-4o-mini  │
              └──────────┘                └──────────┘           └─────────────┘
                                                 │
                                                 ▼
                                          ┌─────────────┐
                                          │Whisper(base)│
                                          │  (local)    │
                                          └─────────────┘
```

## Prerequisites

- Docker and Docker Compose
- OpenAI API key
- No other local installs are strictly required when using Docker.

## Quick Start

```bash
git clone <repo>
cd <repo>
cp .env.example .env
# Edit .env: set OPENAI_API_KEY, JWT_SECRET_KEY, POSTGRES_PASSWORD, MINIO_ROOT_PASSWORD
# Use the same POSTGRES_PASSWORD you intend for Postgres; Compose builds DATABASE_URL from POSTGRES_* (do not rely on a separate mismatched DATABASE_URL).
# If the backend logs show “password authentication failed for user invision”, Postgres was likely initialized with a different password: run `docker compose down -v` (removes DB data) then `docker compose up --build` again, or set POSTGRES_PASSWORD back to the value used when the volume was first created.
docker-compose up --build
# Wait for services to be healthy
docker-compose exec backend python -m app.seed
# Open: http://localhost:5173
```

## Demo Accounts (after seeding)

| Email               | Password | Role      |
|---------------------|----------|-----------|
| admin@invision.kz   | demo1234 | admin     |
| asel@example.kz     | demo1234 | applicant |
| bekzat@example.kz   | demo1234 | applicant |
| dana@example.kz     | demo1234 | applicant |
| marat@example.kz    | demo1234 | applicant |
| ainur@example.kz    | demo1234 | applicant |

## API Documentation

`http://localhost:8000/docs` — FastAPI Swagger UI (OpenAPI) in development.
`http://localhost:5173` — frontend

## Development Without Docker (Optional)

**Backend**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
# Ensure PostgreSQL, MinIO, and .env DATABASE_URL / MINIO_* match local services
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**

```bash
cd frontend
npm install
export VITE_API_URL=http://localhost:8000/api/v1
npm run dev
```

## LangGraph Pipeline Description

**Essay review (after “Check my essay”)**

```
[START] → parse_essay → score_criteria → generate_summary → [END]
```

- `parse_essay`: validates non-empty essay and passes text through.
- `score_criteria`: LLM returns JSON for eight criteria (1–5 each) with advisory language.
- `generate_summary`: computes overall score = (sum of scores / 40) × 10; LLM produces summary, three strengths, three weaknesses, and one final suggestion.

**Full candidate scoring (background, after submit)**

```
[START] → score_essay_component → score_video_component → aggregate_score → write_explanation → [END]
```

- `score_essay_component`: maps latest essay review overall (0–10) to 0–50.
- `score_video_component`: if transcript missing → 0; else LLM scores clarity, motivation, examples (0–10 each), summed to 0–30.
- `aggregate_score`: profile component from GPA (0–20, neutral 10 if GPA missing); total 0–100 rounded to one decimal.
- `write_explanation`: LLM writes advisory narrative; must end with the required disclaimer sentence.

## Fairness & Explainability

**Used in AI scoring (LLM or derived):** essay text; latest essay review outputs for the essay component; spoken interview **transcript** for the video component; a **numeric GPA value** only for deterministic profile normalization (no LLM on GPA).

**Not passed into LLM prompts for scoring:** IIN, city, names, email, or other demographic/profile descriptors. Essay and video prompts are limited to essay text and transcript text respectively, plus the explicit scoring instructions.

## Limitations

- Whisper transcription quality depends on audio clarity, language, and codec support inside the container.
- AI scores and narratives are **advisory only**; they do not replace human decisions.
- This MVP has not undergone a production security review (secrets, hardening, rate limits, etc.).
