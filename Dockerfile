FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

COPY webapp_files/pyproject.toml webapp_files/uv.lock ./
RUN uv sync --locked --no-dev --group prod

COPY webapp_files/ ./

RUN SECRET_KEY=build-placeholder python manage.py collectstatic --noinput

CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn --bind 0.0.0.0:8000 --workers 1 --threads 4 biketransit.wsgi"]
