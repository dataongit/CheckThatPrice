FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# tzdata so TZ / RUN_AT are interpreted in the user's local time.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata chromium chromium-driver xvfb xauth \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencies first so the layer is cached until pyproject.toml/uv.lock change.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

# Application sources. What stays out (list.json, .env, manageList.py,
# .venv, __pycache__) is listed in .dockerignore - list.json and .env are
# bind mounted at runtime so the user owns and edits them on the host.
COPY . .
RUN chmod +x entrypoint.sh

# Runs as uid/gid 1000 so a bind mounted list.json owned by the host user
# stays writable (the checker rewrites prices into it).
RUN useradd --uid 1000 --create-home checker && chown -R checker:checker /app
USER checker

# Default: sleep until RUN_AT (00:00) every night and run one check.
# Override the command to do anything else, e.g. `python main.py` for a
# single immediate run driven by host cron instead.
ENTRYPOINT ["/app/entrypoint.sh"]
