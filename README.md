# Comments SPA

Backend: **Django REST Framework + Strawberry GraphQL** · Frontend: **Vue.js** · **Docker** · **Google Cloud**

SPA «Комментарии»: дерево ответов, валидация (CAPTCHA), вложения (изображения ≤ 320×240; TXT ≤ 100KB), пагинация/сортировка, защита от XSS/SQL‑инъекций.

---

## Где развернуто

- **Backend (Cloud Run):** [https://comments-backend-755819237934.europe-central2.run.app](https://comments-backend-755819237934.europe-central2.run.app)
- **Frontend (Cloud Run):** [https://commets-frontend-755819237934.europe-central2.run.app](https://commets-frontend-755819237934.europe-central2.run.app)
- **БД:** Cloud SQL (PostgreSQL)
- **Медиа (GCS):** bucket `comments-spa-470716-comments-media`

---

## Стек

- **Backend:** Python 3 · Django · DRF · **Strawberry GraphQL**
- **Frontend:** Vue 3 · Vite · Vue Router
- **Инфра:** Cloud Run · Cloud SQL · Google Cloud Storage · Secret Manager · Artifact Registry
- **Контейнеры:** отдельные Dockerfile для backend и frontend

---

## Структура репозитория

```
.
├── comments/              # модели/сериализаторы/утилиты/вьюхи
│   └── schema.py          # части GraphQL-схемы (если разнесено)
├── core/                  # settings/urls/asgi/wsgi
├── frontend/              # исходники Vue
│   ├── public/
│   └── src/
├── venv/                  # локальное окружение (не используется в контейнерах)
├── Dockerfile             # backend Dockerfile (Django)
├── entrypoint.sh          # backend entrypoint
├── README.md
├── requirements.txt
├── .env.example
└── (файлы фронта: frontend/Dockerfile, nginx.conf.template, entrypoint.sh)
```

---

## Быстрый запуск локально (Docker, без Compose)

**Требования:** установлен Docker.

### Backend (SQLite для dev)

```bash
# из корня репозитория
# 1) сборка образа
docker build -t comments-backend:dev .
# 2) миграции
docker run --rm   -e DJANGO_SECRET_KEY=dev -e DJANGO_DEBUG=1   -e DATABASE_URL=sqlite:///db.sqlite3   comments-backend:dev python manage.py migrate
# 3) запуск сервера
docker run --rm -p 8000:8000   -e DJANGO_SECRET_KEY=dev -e DJANGO_DEBUG=1   -e DATABASE_URL=sqlite:///db.sqlite3   comments-backend:dev python manage.py runserver 0.0.0.0:8000
```

Откройте: **[http://localhost:8000](http://localhost:8000)** (GraphQL: **/graphql**).

### Frontend

```bash
cd frontend
# 1) сборка
docker build -t comments-frontend:dev .
# 2) запуск (nginx в контейнере слушает 8080)
docker run --rm -p 8080:8080 comments-frontend:dev
```

Откройте: **[http://localhost:8080](http://localhost:8080)**.

---

## Переменные окружения

**Backend:**

```
DJANGO_SECRET_KEY=...
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://<user>:<pass>@<host>:5432/<db>  # в проде; локально можно sqlite
GS_BUCKET_NAME=comments-spa-470716-comments-media
GS_QUERYSTRING_AUTH=0  # 0 — обычные ссылки; 1 — подписанные URL
```

**Frontend:**

```
VITE_API_BASE=https://comments-backend-755819237934.europe-central2.run.app
VITE_GRAPHQL_URL=https://comments-backend-755819237934.europe-central2.run.app/graphql
VITE_CAPTCHA_PATH=/api/captcha/
```

---

## Эндпоинты

- **GraphQL:** `POST /graphql` (GraphiQL включён в dev)
- **REST:**
  - `POST /api/attachments/upload/` (multipart/form-data)
  - `GET /api/captcha/`

---

## Безопасность (как реализовано)

- **XSS‑защита:**
  - Очистка пользовательского HTML через `bleach` в `comments/utils.py` — разрешены только теги `<a>`, `<code>`, `<i>`, `<strong>`; атрибуты `href`, `title`; протоколы `http`, `https`, `mailto`. Остальное вырезается, теги корректно закрываются.
  - На фронте предпросмотр отображает уже **санитизированный** фрагмент.
  - Заголовки Django (SECURE_*) и CORS настроены под прод‑домены.
- **SQL‑инъекции:**
  - Все обращения к БД — через **Django ORM** и параметризованные запросы; **raw SQL не используется**.
  - Валидация полей на уровне сериализаторов/схем (email/url/ограничения размеров файлов).
- **Вложения:**
  - Проверка контента/расширений; изображения автоповорачиваются по EXIF и масштабируются до ≤ 320×240; TXT ≤ 100KB.

---

## Примечания

- Базовые пути бекенда заданы в `core/urls.py`. Вариант конфигурации:

```
urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', csrf_exempt(GraphQLView.as_view(schema=schema)),
    path('api/attachments/upload/', upload_attachment_view),
    path('api/captcha/', captcha_image),
    path('api/', include('comments.urls')),
]
```

- Для браузерных cookie‑сессий лучше **не** снимать CSRF со всего GraphQL; при токенной/JWT‑аутентификации `csrf_exempt` допустим.
