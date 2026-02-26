# Backend Requirements

Language: Python 3.12+  
Framework: FastAPI + Pydantic
Curriculum source: [matteboken](https://www.matteboken.se/lektioner/mellanstadiet/)

## General API Conventions

- All endpoints use `Content-Type: application/json`.
- All responses follow the structure:

  ```json
  {
    "data": { ... },
    "error": null
  }
  ```

  On error:

  ```json
  {
    "data": null,
    "error": { "code": "ERROR_CODE", "message": "Human-readable message" }
  }
  ```

- API base path: `/api/v1`
- No Auth needed for this version.

## Task Generation

### `POST /api/v1/tasks/generate`

Generates one or more math tasks for a student, aligned to a curriculum topic.

**Request body:**

```json
{
  "topic": "string",      // e.g. "addition", "fractions", "multiplication"
  "difficulty": "string", // "easy" | "medium" | "hard"
  "count": 1,             // Number of tasks to generate (1–10)
}
```

**Response:**

```json
{
  "data": {
    "tasks": [
      {
        "task_id": "uuid",
        "question": "string",        // Human-readable question, e.g. "What is 3/4 + 1/2?"
        "expected_answer": "string", // Correct answer
        "topic": "string",
        "difficulty": "string"
      }
    ]
  },
  "error": null
}
```

### `GET /api/v1/curriculum/topics`

Returns the list of available curriculum topics, fetched and cached from the curriculum website.

**Response:**

```json
{
  "data": {
    "topics": [
      {
        "id": "string",
        "name": "string",          // e.g. "Fractions"
        "subtopics": ["string"],   // e.g. ["Adding fractions", "Simplifying fractions"]
        "grade_level": "string"    // e.g. "Year 5"
      }
    ]
  },
  "error": null
}
```

## Handwriting / Drawing Assistant

This feature analyses what the student is drawing/writing (submitted as a series of strokes) and provides assistance.

### `POST /api/v1/assistant/analyse`

Analyses a student's in-progress work and returns feedback.

**Request body:**

```json
{
  "task_id": "string",
  "content": "string", // JSON-serialised stroke array
}
```

Stroke array format:

```json
[
  {
    "points": [{"x": 10, "y": 20}, {"x": 11, "y": 21}],
    "timestamp_ms": 1234567890
  }
]
```

**Response:**

```json
{
  "data": {
    "has_issue": true,
    "message": "string",          // Kid-friendly message, e.g. "Looks like you added instead of multiplied here!"
    "suggestion": "string",       // Optional next step hint
    "confidence": 0.85            // 0.0–1.0 — how confident the model is that an issue was detected
  },
  "error": null
}
```

**Notes:**

- The backend should rasterise the strokes to a PNG image, run OCR on it, and pass only extracted text to the LLM.
- The LLM should be given the original task question as context, so it can reason about what the student is attempting.
- If `confidence` is below a configurable threshold (default: `0.6`), `has_issue` should be `false` and no message shown — avoid over-interrupting the student.

## Project Structure

```plain
backend/
  main.py               # FastAPI app entrypoint
  routers/
    tasks.py            # Task generation and validation routes
    curriculum.py       # Curriculum topic routes
    assistant.py        # Drawing assistant routes
  services/
    llm.py              # LLM client and prompt templates
    curriculum.py       # Curriculum fetching and caching
    vision.py           # Stroke-to-image rasterisation
  models/
    task.py             # Pydantic models for tasks
    assistant.py        # Pydantic models for assistant requests/responses
  config.py             # Settings loaded from environment variables
```
