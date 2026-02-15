# Backend API

FastAPI backend for DAIS Active Learning.

## Requirements

- Python 3.11+ (project target is 3.12+; current workspace uses 3.11 and runs fine)
- Dependencies in `requirements.txt`

## Install

From repository root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

Or with your active Python:

```powershell
python -m pip install -r backend/requirements.txt
```

## Run

From repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

API base: `http://127.0.0.1:8000/api/v1`

## LLM Configuration

By default, assistant analysis uses mock fallback logic.

### Gemini API setup

To use Google Gemini API:

```env
DAIS_LLM_PROVIDER=gemini
DAIS_GEMINI_API_KEY=your_gemini_api_key
DAIS_GEMINI_MODEL=gemini-2.0-flash
DAIS_GEMINI_API_BASE=https://generativelanguage.googleapis.com/v1beta
DAIS_GEMINI_TEMPERATURE=0.2
DAIS_ASSISTANT_CONFIDENCE_THRESHOLD=0.6
```

If the Gemini call fails (or key is missing), the service automatically falls back to deterministic mock analysis.

## API Examples (PowerShell)

### 1) Get curriculum topics

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/api/v1/curriculum/topics" | ConvertTo-Json -Depth 8
```

### 2) Generate tasks

```powershell
$body = @{
  topic = "addition"
  difficulty = "easy"
  count = 1
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/tasks/generate" `
  -ContentType "application/json" `
  -Body $body | ConvertTo-Json -Depth 8
```

### 3) Analyse student drawing/writing

`content` must be a JSON-serialized **string** of the stroke array.

```powershell
$genBody = @{ topic = "addition"; difficulty = "easy"; count = 1 } | ConvertTo-Json
$generated = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v1/tasks/generate" -ContentType "application/json" -Body $genBody
$taskId = $generated.data.tasks[0].task_id

$analyseBody = '{"task_id":"' + $taskId + '","content":"[{\"points\":[{\"x\":10,\"y\":20},{\"x\":40,\"y\":50}],\"timestamp_ms\":1234567890}]"}'

Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/assistant/analyse" `
  -ContentType "application/json" `
  -Body $analyseBody | ConvertTo-Json -Depth 8
```

## Response Envelope

Success:

```json
{
  "data": { },
  "error": null
}
```

Error:

```json
{
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message"
  }
}
```
