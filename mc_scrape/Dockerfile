FROM python:3.10-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml .
RUN uv sync --no-dev

COPY metacritic/ metacritic/

ENTRYPOINT ["uv", "run", "python", "-m", "metacritic"]
