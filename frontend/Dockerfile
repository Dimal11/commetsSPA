FROM node:20-alpine AS build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM nginx:alpine
COPY frontend/nginx.conf.template /etc/nginx/conf.d/default.conf.template
COPY --from=build /app/dist/ /usr/share/nginx/html/
COPY frontend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 8080
CMD ["/entrypoint.sh"]
