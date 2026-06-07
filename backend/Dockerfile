FROM python:3.12-slim

WORKDIR /app

# Poetry manages dependencies. Install it into the system interpreter and
# disable venv creation so packages land on the default PATH.
ENV POETRY_VERSION=2.1.4 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1
RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

# Install dependencies first (cached unless the lockfile changes).
COPY pyproject.toml poetry.lock ./
RUN poetry install --without dev

COPY backend/ ./backend/

RUN python -m backend.scripts.index_curriculum

EXPOSE 8080

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
