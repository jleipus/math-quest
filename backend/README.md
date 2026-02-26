# Backend API

FastAPI backend for DAIS Active Learning.

## Requirements

- Python 3.11+ (project target is 3.12+; current workspace uses 3.11 and runs fine)
- CPU-first dependencies in `requirements.txt` (recommended default)

## Install

From repository root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

Or with your active Python:

```powershell
python -m pip install -r backend/requirements.txt
```

This setup uses CPU OCR by default for portability and stable startup.

## Run

From repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

API base: `http://127.0.0.1:8000/api/v1`

## LLM Configuration

Assistant analysis requires a configured Hugging Face provider.
The backend now uses a pretrained OCR CNN (`easyocr`) to convert student drawings/writing into text, and only that text is sent to Hugging Face inference.

`backend/config.py` is the single source of truth for configuration.

### Hugging Face API setup

Set these values in `backend/config.py`:

- `llm_provider = "huggingface"`
- `hf_provider = "featherless-ai"`
- `hf_model = "AI-Sweden-Models/Llama-3-8B"`
- `assistant_confidence_threshold = 0.4`

Set your token via environment variable:

- `HF_TOKEN=your_huggingface_token`

If the HF token is missing or the inference call fails, `/assistant/analyse` returns an error.
On first OCR use, EasyOCR may download model files automatically.

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
