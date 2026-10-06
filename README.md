Ini README lengkap buat project lu. Copy-paste ke `README.md`:

```markdown
# NUTRI Backend

FastAPI modular backend — feature-first architecture, async PostgreSQL via SQLAlchemy 2.0, Alembic migration, structured JSON logging, dan dependency injection lewat FastAPI `Depends()`.

Bagian dari issue **NUTRI-101**: fondasi scalable, testable, bebas technical debt untuk seluruh tim.

---

## 📋 Prasyarat

- **Python 3.12+**
- **Poetry 2.x**
- **pipx** (untuk install Poetry)
- **Git Bash** (Windows) atau shell Unix

## 🚀 Quick Start

### 1. Install dependencies

```bash
poetry install --extras dev
```

### 2. Setup environment

```bash
cp .env.example .env
# Edit .env — isi SUPABASE_URL, SUPABASE_ANON_KEY, dll
```

### 3. Jalankan migration

```bash
poetry run alembic upgrade head
```

### 4. Start server

```bash
poetry run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Buka:
- **Swagger UI**: http://127.0.0.1:8000/docs (hanya saat `ENV=dev`)
- **ReDoc**: http://127.0.0.1:8000/redoc
- **Health**: http://127.0.0.1:8000/api/v1/healthz

---

## 🧪 Testing

```bash
poetry run pytest -v --cov=app/core --cov=app/features --cov-report=term-missing
```

Coverage target: **≥80%** untuk `app/core/` & `app/features/`.

HTML report:

```bash
poetry run pytest --cov=app/core --cov=app/features --cov-report=html
# Buka htmlcov/index.html
```

---

## 🗂️ Struktur Folder

```
backend/
├── app/
│   ├── main.py                    # App factory, middleware, exception handlers
│   ├── core/
│   │   ├── config.py              # Pydantic BaseSettings
│   │   ├── exceptions.py          # Custom exception classes
│   │   └── logging.py             # Structured JSON logging + middleware
│   ├── db/
│   │   ├── base.py                # SQLAlchemy DeclarativeBase
│   │   ├── session.py             # Async engine + sessionmaker + get_db
│   │   ├── models/                # ORM models (per file)
│   │   └── migrations/            # Alembic (env.py, versions/)
│   ├── shared/
│   │   ├── schemas.py             # BaseResponse, Pagination
│   │   └── deps.py                # DI: get_db, get_current_user, dll
│   └── features/                  # Feature-first
│       ├── health/                # /healthz, /readyz
│       ├── auth/
│       ├── consent/
│       ├── profile/
│       └── nutrition/
│           ├── engine/            # Rule Engine (pure)
│           ├── limits/            # Daily Limits
│           └── references/        # Reference Registry
├── tests/
│   ├── conftest.py
│   ├── core/
│   └── features/
├── alembic.ini
├── .env.example
├── pyproject.toml
└── README.md
```

---

## 🔌 Endpoints

| Method | Path | Deskripsi | Auth |
|---|---|---|---|
| GET | `/api/v1/healthz` | Liveness probe (independen DB) | ❌ |
| GET | `/api/v1/readyz` | Readiness probe (cek koneksi DB) | ❌ |
| GET | `/docs` | Swagger UI (hanya ENV=dev) | ❌ |
| GET | `/redoc` | ReDoc UI (hanya ENV=dev) | ❌ |

**Contoh response `/healthz`:**

```json
{"status": "healthy", "version": "1.0.0"}
```

**Contoh response `/readyz` (DB up):**

```json
{"status": "ready", "database": "up"}
```

**Contoh response error standar:**

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Resource not found",
    "details": {}
  }
}
```

---

## ⚙️ Environment Variables

Semua env divalidasi saat boot. Kalau ada yang invalid atau missing, server **gagal start** dengan Pydantic `ValidationError` yang eksplisit.

| Variable | Wajib | Deskripsi |
|---|---|---|
| `SUPABASE_URL` | ✅ | Base URL Supabase (`https://xxx.supabase.co`) |
| `SUPABASE_ANON_KEY` | ✅ | Public key (aman di-expose ke frontend) |
| `SUPABASE_SERVICE_ROLE_KEY` | ✅ | Secret key — bypass RLS. **Jangan expose ke frontend.** |
| `SUPABASE_JWT_SECRET` | ✅ | Secret untuk verify JWT user |
| `DATABASE_URL` | ✅ | Postgres connection string (`postgresql+asyncpg://...`) |
| `GEMINI_API_KEY` | ✅ | API key Gemini |
| `ENV` | ✅ | `dev` / `staging` / `prod` |
| `CORS_ORIGINS` | ✅ | Comma-separated list origin |

### Fail-Safe

- `ENV=prod` + `CORS_ORIGINS=*` → **boot gagal** (mencegah wildcard di production)
- `ENV=prod` → `/docs` & `/redoc` **otomatis disabled**

---

## 🗄️ Database Migration

### Bikin migration baru

Setelah ubah/tambah model di `app/db/models/`:

```bash
poetry run alembic revision --autogenerate -m "pesan migration"
poetry run alembic upgrade head
```

### Rollback

```bash
poetry run alembic downgrade -1
```

### Lihat status

```bash
poetry run alembic current
poetry run alembic history
```

> **Catatan:** Semua migration harus reversible. Setiap `upgrade()` wajib punya `downgrade()` yang benar.

---

## 🏗️ Arsitektur

### Feature-First

Setiap domain (health, auth, consent, profile, nutrition) punya folder sendiri dengan:

```
features/<domain>/
├── __init__.py         # Expose router
├── router.py           # HTTP endpoints (thin)
├── schemas.py          # Pydantic request/response models
└── service.py          # Business logic
```

**Aturan penting:**
- ❌ **Tidak ada logic bisnis di router** — router cuma parse input, panggil service, return response
- ✅ Logic bisnis di `service.py`
- ✅ Dependency disuntik lewat `app/shared/deps.py`

### Dependency Injection

```python
from app.shared.deps import DBDep, SettingsDep, CurrentUser

@router.get("/items")
async def list_items(db: DBDep, user: CurrentUser) -> list[Item]:
    return await item_service.list_for_user(db, user["user_id"])
```

### Error Handling

Semua custom error inherits dari `AppException`. Handler global (di `main.py`) format output-nya konsisten:

```json
{"error": {"code": "...", "message": "...", "details": {}}}
```

Error tak terduga → 500 tanpa stack trace (tidak expose internal).

### Logging

Setiap request di-log secara structured (JSON di prod, pretty console di dev) dengan field:

- `request_id` (auto-generated / dari header `X-Request-ID`)
- `path`, `method`
- `latency_ms`
- `status_code`
- `level`: INFO (2xx/3xx), WARNING (4xx), ERROR (5xx)
