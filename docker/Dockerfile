FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

FROM base AS test
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY tests ./tests
COPY examples ./examples
RUN pip install --no-cache-dir ".[dev]"
CMD ["pytest", "tests/", "-v"]
