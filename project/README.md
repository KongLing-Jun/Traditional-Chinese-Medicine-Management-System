# TCM Management System (Django + Vue3)

Backend stack:
- Python 3.11.9+
- Django 5.2
- Django REST Framework
- JWT auth (simplejwt)
- RBAC (DRF permission class + role menu API)
- MySQL as default runtime database

Frontend stack:
- Vue 3 + Vite
- Pinia
- Vue Router
- Axios

## Features

- JWT login/refresh/logout APIs
- Role-based menu and permission checks
- Operation audit logs for auth and key CRUD/inventory actions
- Unified API error response (`code/message/errors`)
- Dashboard, users, herbs, formulas, inventory modules
- Vue3 pages for dashboard/users/herbs/formulas/inventory

## Project structure

- Django backend: repository root
- Vue frontend: `frontend/`

## Backend setup (MySQL)

1. Install dependencies

```bash
pip install -r requirements.txt
```

2. Configure MySQL env vars (PowerShell example)

```powershell
$env:MYSQL_DATABASE="zhongyao"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD="123456"
$env:MYSQL_HOST="127.0.0.1"
$env:MYSQL_PORT="3306"
$env:FRONTEND_ORIGINS="http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:5175,http://localhost:5175"
```

Notes:
- Runtime defaults to MySQL database `zhongyao`.
- For local fallback to SQLite, set: `$env:USE_SQLITE="1"`.
- Test runs auto-switch to SQLite.
- If Vite runs on another local port (e.g. `5175`), include it in `FRONTEND_ORIGINS`.

3. Create database, migrate, seed, and run

```bash
mysql -uroot -p123456 -e "CREATE DATABASE IF NOT EXISTS zhongyao DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

```bash
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Or run one command in PowerShell:

```powershell
.\start_backend.ps1
```

Quick fullstack verification (backend + DB + CORS + frontend proxy):

```powershell
.\check_fullstack.ps1
```

Optional parameters:

```powershell
.\check_fullstack.ps1 -BackendBase "http://127.0.0.1:8000" -FrontendBase "http://localhost:5175" -Username "admin" -Password "admin123456"
```

Demo accounts:
- `admin / admin123456`
- `pharmacist / pharmacist123`
- `assistant / assistant123`

## Frontend setup (Vue3)

```bash
cd frontend
npm install
npm run dev
```

Default frontend URL: `http://127.0.0.1:5173`

Frontend API base defaults to same-origin and uses Vite proxy (`/api -> http://127.0.0.1:8000`),
so local development does not require browser CORS setup.

Optional frontend env (`frontend/.env`):

```env
VITE_API_BASE_URL=
VITE_API_PROXY=http://127.0.0.1:8000
```

Notes:
- Keep `VITE_API_BASE_URL` empty in local development (recommended).
- Only set `VITE_API_BASE_URL` to an absolute URL when you intentionally want direct cross-origin requests.

## API examples

- `POST /api/auth/login/`
- `POST /api/auth/logout/`
- `POST /api/auth/refresh/`
- `GET /api/auth/access/`
- `GET /api/users/`
- `GET /api/logs/`
- `GET /api/herbs/`
- `GET /api/formulas/`
- `GET /api/inventory/stocks/`
- `GET /api/inventory/records/`
- `POST /api/inventory/inbound/`
- `POST /api/inventory/outbound/`
- `POST /api/inventory/check/`

## Tests

```bash
python manage.py test
```
