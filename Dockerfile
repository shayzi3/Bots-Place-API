FROM python:3.14-slim

# uv из официального образа
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# зависимости отдельным слоем — кэшируется, пока не менялся uv.lock
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# код проекта
COPY . .
RUN uv sync --frozen --no-dev

EXPOSE 8086

CMD ["uvicorn", "bots_place.app.main:app", "--host", "0.0.0.0", "--port", "8086"]
