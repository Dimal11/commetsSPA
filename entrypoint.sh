#!/usr/bin/env sh
set -e

export PORT="${PORT:-8080}"

python manage.py collectstatic --noinput || true

if [ "${MIGRATE_ON_START:-0}" = "1" ]; then
  python manage.py migrate --noinput || echo "Migrations failed; starting anyway"
fi

exec gunicorn core.wsgi:application \
  --bind 0.0.0.0:"$PORT" \
  --workers ${WEB_CONCURRENCY:-2} \
  --threads ${GTHREADS:-4} \
  --access-logfile - \
  --error-logfile - \
  --timeout "${GUNICORN_TIMEOUT:-120}"