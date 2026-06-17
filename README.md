# WB Analytics SaaS

SaaS-сервис аналитики для продавцов **Wildberries**: подключаешь WB API-токен,
сервис выгружает продажи/заказы/остатки, считает метрики и шлёт уведомления в Telegram.

**Стек:** FastAPI · PostgreSQL · SQLAlchemy 2.0 (async) · Alembic · Celery · Redis ·
JWT · Docker · pytest.

## 🚀 Живое демо

> Открой ссылку → раздел **«Попробовать за 1 минуту»** ниже.

**Демо:** `https://<твой-сервис>.onrender.com/docs`

## Попробовать за 1 минуту (через Swagger UI `/docs`)

1. `POST /api/v1/auth/register` — `{"email": "you@example.com", "password": "supersecret1"}`
2. `POST /api/v1/auth/login` — тот же логин/пароль, скопируй `access_token`,
   нажми **Authorize** вверху страницы и вставь токен.
3. `POST /api/v1/demo/seed` — засеять аккаунт демо-данными (продажи за 30 дней).
4. Смотри аналитику:
   - `GET /api/v1/analytics/summary` — сводка за период
   - `GET /api/v1/analytics/sales-dynamics` — динамика по дням
   - `GET /api/v1/analytics/top-products` — топ товаров по выручке
   - `GET /api/v1/analytics/low-stock` — заканчивающиеся остатки

## Возможности

- 🔐 Аутентификация: JWT (access + refresh), пароли — bcrypt.
- 🔑 Подключение WB-токена: проверяется против WB API, хранится зашифрованным (Fernet).
- 🔄 Синхронизация продаж/заказов/остатков из WB Statistics API (идемпотентный upsert).
- 📊 Аналитика: сводка, динамика, топ товаров, низкие остатки.
- 🤖 Telegram-уведомления: дневная сводка и алерты о низких остатках.
- ⏱ Фоновые задачи: Celery + Redis + Beat (синк и рассылки по расписанию).

## Запуск локально (Docker)

```bash
cp .env.example .env
# сгенерируй секреты и впиши в .env:
python -c "import secrets; print(secrets.token_urlsafe(32))"                                # SECRET_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"   # ENCRYPTION_KEY

docker compose up --build
```

Открой http://localhost:8000/docs

## Тесты

```bash
pip install -r requirements-dev.txt
pytest          # на in-memory SQLite, БД не нужна
ruff check .
```

## Структура

```
app/
├── core/      конфиг, БД, безопасность (JWT, хэши, шифрование)
├── models/    SQLAlchemy-модели: User, Sale, Order, Stock
├── schemas/   Pydantic-схемы
├── api/       роутеры v1: auth, users, sync, analytics, demo
├── services/  WB-клиент, синхронизация, аналитика, Telegram
└── workers/   Celery: приложение, задачи, расписание
```
