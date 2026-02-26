# Backend (FastAPI)

Fresh backend for the frontend API at `http://localhost:8000/api/v1`.

## Run locally

From workspace root:

```powershell
C:/Users/vavyl/Desktop/dais-active-learning/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
Set-Location backend
C:/Users/vavyl/Desktop/dais-active-learning/.venv/Scripts/python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Open health check:

- `http://localhost:8000/health`

## Stop local server

- In the terminal running uvicorn, press `Ctrl + C`.

## Docker (if available)

```powershell
docker compose up --build backend
```

Detached mode:

```powershell
docker compose up --build -d backend
```

## Frontend API base URL

- `http://localhost:8000/api/v1`

## Endpoints used by frontend

### Curriculum

- `GET /api/v1/curriculum/grades`
  - Response: `{ "grades": string[] }`

### Game

- `POST /api/v1/game/init`
  - Request: `{ "grade": string }`
  - Response: `{ "session_id", "player_hp", "enemy_hp", "max_energy", "floor" }`

- `POST /api/v1/game/draw`
  - Request: `{ "session_id": string }`
  - Response: `{ "hand": Card[], "enemy_next_damage": number }`

- `POST /api/v1/game/answer`
  - Request: `{ "session_id", "task_id", "answer" }`
  - Response: `{ "correct", "card_id", "message" }`

- `POST /api/v1/game/play_card`
  - Request: `{ "session_id", "card_id" }`
  - Response: `{ "enemy_hp", "player_hp", "effect_value", "card_type", "enemy_defeated" }`

- `POST /api/v1/game/end_turn`
  - Request: `{ "session_id": string }`
  - Response: `{ "player_hp", "enemy_damage", "shield_absorbed", "hand", "enemy_next_damage", "enemy_hp", "enemy_max_hp" }`

### Agent

- `POST /api/v1/agent/help`
  - Request: `{ "session_id", "task_id", "student_work"?: Stroke[] }`
  - Response: `{ "guiding_question", "context_used" }`

### User model

- `GET /api/v1/user_model/{session_id}`
  - Response: `{ "session_id", "topics": TopicRecord[] }`

## Notes

- Current backend uses in-memory session storage (data resets on restart).
- CORS is controlled by `DAIS_ALLOWED_ORIGINS` (defaults to `http://localhost:3000`).

## LLM hint provider (Hugging Face)

The help endpoint (`POST /api/v1/agent/help`) uses:

- `AI-Sweden-Models/Llama-3-8B-instruct:featherless-ai`
- via OpenAI-compatible API base: `https://router.huggingface.co/v1`

Token handling (current implementation):

- `HF_TOKEN` is currently hardcoded in `backend/main.py`.
- No `.env` token setup is required for local run.

Fallback behavior:

- If hint generation fails, backend falls back to a built-in generic guiding question.
- If card generation fails after retries, backend returns `502` with `Could not generate cards with LLM at this time`.
