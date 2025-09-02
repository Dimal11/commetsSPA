#!/usr/bin/env sh
set -euo pipefail

export PORT="${PORT:-8080}"
export WEB_CONCURRENCY="${WEB_CONCURRENCY:-2}"
export GTHREADS="${GTHREADS:-4}"
export GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-120}"

export MIGRATE_ON_START="${MIGRATE_ON_START:-1}"
export MIGRATE_RETRIES="${MIGRATE_RETRIES:-15}"
export MIGRATE_SLEEP="${MIGRATE_SLEEP:-3}"

python manage.py collectstatic --noinput || true

if [ "$MIGRATE_ON_START" = "1" ]; then
  echo "Applying database migrations..."
  i=1
  until python manage.py migrate --noinput; do
    if [ "$i" -ge "$MIGRATE_RETRIES" ]; then
      echo "Migrations failed after $i attempts. Exiting."
      exit 1
    fi
    echo "Migrations attempt $i failed. Retrying in ${MIGRATE_SLEEP}s..."
    i=$((i+1))
    sleep "$MIGRATE_SLEEP"
  done
  echo "Migrations applied successfully."
fi

exec gunicorn core.wsgi:application \
  --bind 0.0.0.0:"$PORT" \
  --workers "$WEB_CONCURRENCY" \
  --threads "$GTHREADS" \
  --access-logfile - \
  --error-logfile - \
  --timeout "$GUNICORN_TIMEOUT"