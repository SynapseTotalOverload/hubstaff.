FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1

# Install build dependencies and watchdog
ENV buildDeps='build-essential gcc musl-dev'

RUN apt-get update \
    && apt-get install -y $buildDeps --no-install-recommends \
    && pip install --upgrade pip wheel setuptools poetry watchdog \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cache dependencies
COPY poetry.lock pyproject.toml /app/
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction

# Copy source code
COPY app /app

# Use watchmedo to autoreload Python on file changes
CMD ["watchmedo", "auto-restart", "--directory=./app", "--pattern=*.py", "--recursive", "--", "python", "app/main.py"]
