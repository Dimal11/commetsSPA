#!/usr/bin/env sh
set -e

export PORT="${PORT:-8080}"

python manage.py collectstatic --noinput || true

if [ "${MIGRATE_ON_START:-1}" = "1" ]; then
  python manage.py migrate --noinput
fi

exec gunicorn core.wsgi:application \
  --bind 0.0.0.0:"$PORT" \
  --workers ${WEB_CONCURRENCY:-2} \
  --threads ${GTHREADS:-4} \
  --access-logfile - \
  --error-logfile - \
  --timeout 0