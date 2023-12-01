FROM python:3.11-bookworm as builder

RUN pip install poetry==1.7.1

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN touch README.md

RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --without dev --no-root

FROM python:3.11-slim-bookworm as runtime

RUN useradd -m docker 
USER docker

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder --chown=docker ${VIRTUAL_ENV} ${VIRTUAL_ENV}

WORKDIR /app

COPY --chown=docker src/ /app/

ENV NUM_WORKERS=1

EXPOSE 8000

CMD gunicorn canopy_server.app:app --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers $NUM_WORKERS