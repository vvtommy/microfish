FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir uv


COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project


COPY src ./src
COPY Readmd.md Readmd_cn.md ./
RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["uv", "run", "microfish"]
