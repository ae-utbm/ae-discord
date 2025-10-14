FROM debian:13.1-slim

ENV TZ="Europe/Paris"
RUN date

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates
# install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY bot.toml pyproject.toml uv.lock .python-version app/
COPY src app/src
WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --compile-bytecode

ENTRYPOINT ["uv", "run", "-m", "src.main"]
