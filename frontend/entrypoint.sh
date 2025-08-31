#!/usr/bin/env sh
set -e

: "${BACKEND_URL:?Env BACKEND_URL is required}"

envsubst '${BACKEND_URL}' \
  < /etc/nginx/conf.d/default.conf.template \
  > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
