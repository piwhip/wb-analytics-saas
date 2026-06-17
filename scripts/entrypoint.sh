#!/usr/bin/env bash
set -e

# Ждём готовности БД (простая проверка по TCP через python).
wait_for_db() {
  # На облачном хостинге БД задаётся через DATABASE_URL и доступна сразу —
  # локальное ожидание по TCP не нужно.
  if [ -n "${DATABASE_URL}" ]; then
    echo "DATABASE_URL is set (managed DB) — skipping TCP wait."
    return 0
  fi
  echo "Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
  python - <<'PY'
import os, socket, time
host = os.getenv("POSTGRES_HOST", "db")
port = int(os.getenv("POSTGRES_PORT", "5432"))
for _ in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            print("PostgreSQL is up.")
            break
    except OSError:
        time.sleep(1)
else:
    raise SystemExit("PostgreSQL not reachable")
PY
}

case "$1" in
  api)
    wait_for_db
    echo "Running migrations..."
    alembic upgrade head
    echo "Starting API..."
    exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
    ;;
  worker)
    wait_for_db
    exec celery -A app.workers.celery_app:celery_app worker --loglevel=info
    ;;
  beat)
    wait_for_db
    exec celery -A app.workers.celery_app:celery_app beat --loglevel=info
    ;;
  *)
    exec "$@"
    ;;
esac
