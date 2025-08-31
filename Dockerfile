FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=on \
    PORT=8080 \
    DJANGO_SETTINGS_MODULE=core.settings

RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app
RUN chown -R appuser:appuser /app

RUN chmod +x /app/entrypoint.sh

RUN useradd -m appuser
USER appuser

EXPOSE 8080
CMD ["/app/entrypoint.sh"]
