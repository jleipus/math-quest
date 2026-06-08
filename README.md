# Supporting Active Learning in Math Tasks

## Group project for the Responsible Design of Interactive AI Systems course at Umeå University

<p align="center">
  <img src="./report/images/title_card.png" alt="Splash screen" width="600"/>
</p>

Mathematics classrooms often struggle to support students with widely different skill levels, leading to disengagement for some and anxiety for others.
This project presents the design of a gamified web-based tutoring system for primary school students aged 10-12, where mathematical challenges are embedded in a turn-based card combat game.
The system uses a RAG architecture constrained by a pedagogical strategy, designed so that the AI provides guiding questions rather than direct answers.

[Read the full report (PDF)](report.pdf)

## Project structure

This repo holds two independent apps — a Next.js frontend and a [Poetry](https://python-poetry.org)-managed
Python backend:

```plain
apps/web/      Next.js frontend (self-contained npm app, deployed on Firebase App Hosting)
backend/       FastAPI backend (RAG + game logic, deployed on Cloud Run)
report/        LaTeX source for the report
```

`apps/web` is a standalone npm project with its own `package-lock.json`, so all frontend
commands run from inside `apps/web`. The repo-root `package.json` provides convenience
launchers (`npm run dev`, `npm run build`, etc.) that forward to it.

The frontend is deployed via [Firebase App Hosting](https://firebase.google.com/docs/app-hosting)
(configured in `apps/web/apphosting.yaml`), which builds from the connected GitHub repo
(root directory `apps/web`) and auto-deploys on push to `master`. The backend image is built
and deployed to Cloud Run by the `.github/workflows/deploy.yml` workflow.

## Prerequisites

- **Node.js** ≥ 20 and npm
- **Python** 3.12
- **Poetry** (`pipx install poetry`)

## Environment variables

**Backend** - copy `.env.example` to `.env` in the repo root:

```bash
DAIS_LLM_PROVIDER=claude            # or "gemini"
DAIS_CLAUDE_API_KEY=...             # key for the selected provider
DAIS_ALLOWED_ORIGINS='["http://localhost:3000"]'
DAIS_FIREBASE_SERVICE_ACCOUNT_JSON= # optional for local dev
```

**Frontend** - create `apps/web/.env.local`:

```bash
NEXT_PUBLIC_BACKEND_URL=http://localhost:8080
# Firebase config is optional locally; the app runs without it.
NEXT_PUBLIC_FIREBASE_API_KEY=
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=
NEXT_PUBLIC_FIREBASE_PROJECT_ID=
NEXT_PUBLIC_FIREBASE_APP_ID=
```

## Running locally

Run both from the repo root.

**Backend** (port 8080):

```bash
poetry install                                        # create the venv
poetry run python -m backend.scripts.index_curriculum # one-time: build the RAG index into ./data
poetry run uvicorn backend.main:app --reload --reload-dir backend --port 8080
```

API docs are then at <http://localhost:8080/docs>.

**Frontend** (port 3000):

```bash
cd apps/web
npm install
npm run dev          # or `npm run dev` from the repo root (forwards here)
```

App is served at <http://localhost:3000>.

### Docker Compose alternative

```bash
docker compose up --build
```

Runs the backend on 8080. The first build is slow because the curriculum index is built into the backend image. Run the frontend separately with `npm run dev`.

## Regenerating API types

The frontend's TypeScript types (`apps/web/lib/api-schema.ts`) are generated from the backend's OpenAPI schema, which is the single source of truth. After changing the Pydantic models in `backend/models/`, regenerate them:

```bash
npm run gen:api-types
```
