FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

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

CMD ["hypercorn", "-k", "uvloop", "--workers", "5", "--bind", "0.0.0.0:8000", "mikosite.asgi:application"]
