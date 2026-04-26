FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    N_WORKERS=5 \
    HYPERCORN_BIND=0.0.0.0:8000

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libcairo2-dev \
    python3-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY mikosite/ ./mikosite/
WORKDIR /app/mikosite

ENTRYPOINT ["/bin/sh", "/entrypoint.sh"]

CMD ["sh", "-c", "exec hypercorn -k uvloop --workers \"$N_WORKERS\" --bind \"$HYPERCORN_BIND\" mikosite.asgi:application"]
