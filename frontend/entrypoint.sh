#!/usr/bin/env sh
set -e

: "${BACKEND_URL:?Env BACKEND_URL is required}"
export PORT="${PORT:-8080}"

envsubst '${BACKEND_URL} ${PORT}' \
  < /etc/nginx/conf.d/default.conf.template \
  > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
