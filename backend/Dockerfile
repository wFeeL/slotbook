FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_LINK_MODE=copy

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev || uv sync --no-dev

COPY app ./app
# Later tasks add the following — uncomment when their files exist:
#   COPY alembic ./alembic
#   COPY alembic.ini ./alembic.ini
#   COPY seed.py ./seed.py

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
