# BottleCRM — Deployment Architecture Summary

## Overview

BottleCRM is a full-stack CRM platform with Django REST Framework (backend) and SvelteKit (frontend), using PostgreSQL Row-Level Security (RLS) for multi-tenant data isolation. It runs entirely via Docker Compose for local development and can be adapted for production deployment.

---

## Services (6 containers)

| Service | Image / Build | Port | Purpose |
|---|---|---|---|
| **db** | `postgres:16-alpine` | `5432` | Primary database with RLS |
| **redis** | `redis:7-alpine` | `6379` | Cache + Celery message broker |
| **backend** | Dockerfile (python:3.12-slim) | `8000` | Django REST API (dev server) |
| **celery-worker** | same Dockerfile | — | Async background task processing |
| **celery-beat** | same Dockerfile | — | Scheduled periodic tasks |
| **frontend** | `frontend/Dockerfile` (node:22-slim) | `5173` | SvelteKit dev server (HMR) |

---

## Architecture Diagram (logical flow)

```
Browser/Client ──► Frontend (:5173) ──► Backend (:8000) ──► PostgreSQL (:5432)
                                                                  ▲
                    Celery Worker ──► Redis (:6379) ───────────────┘
                    Celery Beat  ──► Redis (:6379)
```

---

## Dependencies

### Runtime
- **PostgreSQL 16** — primary data store; RLS enforces multi-tenant row isolation
- **Redis 7** — Celery broker and result backend
- **Python 3.12** — Django 5.x + DRF, gunicorn (prod), Celery
- **Node.js 22** — SvelteKit 2.x + Svelte 5 (runes), pnpm package manager

### System Packages (inside backend container)
- `libpq-dev` — PostgreSQL client libraries
- `libcairo2`, `libpango-1.0-0`, `libpangocairo-1.0-0`, `libgdk-pixbuf2.0-0` — WeasyPrint (PDF generation)
- `libffi-dev`, `shared-mime-info`

### Python Package Manager
- **uv** (Astral) — fast Python dependency manager; installed via `ghcr.io/astral-sh/uv:0.11` multi-stage copy

---

## Files

| File | Purpose |
|---|---|
| `Dockerfile` | Backend/Celery image: installs system deps, uv, syncs Python deps, copies source |
| `frontend/Dockerfile` | Frontend image: Node 22 + pnpm, installs npm deps, runs `pnpm dev --host` |
| `docker-compose.yml` | Orchestrates all 6 services, volumes, health checks, and dependencies |
| `.env.docker` | Default environment variables for Docker dev (committed to repo) |
| `docker/backend/entrypoint.sh` | Backend startup: waits for PG, runs migrations, creates default admin, collects static, starts dev server |
| `docker/postgres/init-rls-user.sql` | Initializes `crm_user` (non-superuser) with schema privileges for RLS enforcement |

---

## Docker Compose Key Details

### Health Checks
- **db**: `pg_isready -U postgres` (5s interval, 3s timeout, 5 retries)
- **redis**: `redis-cli ping` (same params)
- **backend** + **celery-\*** wait for both `db` and `redis` to be healthy via `depends_on.condition: service_healthy`

### Volumes
- `postgres_data` — persisted database files
- `frontend_node_modules` — cached npm/pnpm packages
- Bind mounts: `./backend:/app` — live code reload for Django; `./frontend:/app` — live HMR for SvelteKit

### Networking
- Default `docker-compose` network (bridge); services resolve each other by service name (e.g., backend → `db`, `redis`)
- Ports exposed to host: `5432`, `6379`, `8000`, `5173`

---

## How to Run

### Local Development (Docker Compose)

```bash
# From project root
docker compose up --build       # first run (builds images)
docker compose up               # subsequent runs (code hot-reloads)
docker compose down             # stop all services
docker compose down -v          # stop + delete volumes (full reset)
```

An admin user (`admin@localhost` / `admin`) is created automatically on first start.

### Local Development (Manual, without Docker)

**Backend:**
```bash
cd backend
uv sync                                    # install deps
cp .env.example .env                       # configure env
uv run python manage.py migrate
uv run python manage.py runserver          # :8000
```

**Frontend:**
```bash
cd frontend
pnpm install
pnpm run dev                               # :5173
```

**Celery (separate terminal):**
```bash
cd backend
uv run celery -A crm worker --loglevel=INFO
```

### Production Considerations

The current setup is designed for **development** — notable gaps for production:

| Concern | Dev Default | Production Recommendation |
|---|---|---|
| **WSGI server** | `python manage.py runserver` (dev) | Replace with **gunicorn** (included via `uvicorn[standard]` or gunicorn in pyproject.toml) |
| **Secret key** | `django-insecure-docker-dev-key-change-in-production` | Use a strong, rotated secret via env/secret manager |
| **Debug mode** | `DEBUG=True` | Set `DEBUG=False` |
| **CORS** | `CORS_ALLOW_ALL=True` | Restrict to specific origins |
| **Email** | Console backend (stdout) | AWS SES or a transactional email provider |
| **PostgreSQL user** | Single `postgres` superuser + `crm_user` app user | Separate credentials, least-privilege RLS user only |
| **Static/media files** | Local filesystem via `collectstatic` | Upload to **AWS S3** (or equivalent object store) |
| **Frontend** | `pnpm dev` (dev server, no SSR) | Build with `pnpm build` and serve via Node or a CDN |
| **SSL/TLS** | None | Terminate TLS at reverse proxy (nginx/Caddy) |
| **Secrets management** | .env.docker committed to repo | External secret store (Docker secrets, Vault, 1Password) |
| **Process manager** | None (single container) | Orchestrate via Kubernetes, Nomad, or Docker Swarm |

### Production-Ready Stack (Recommended)

```
                     ┌──────────────┐
                     │   CDN / S3   │  (static files, media)
                     └──────┬───────┘
                            │
┌───── Client ──────►  ┌───┴────┐
                        │  nginx  │  (reverse proxy, SSL, rate limiting)
                        └───┬────┘
                            │
               ┌────────────┼────────────┐
               │            │            │
         ┌─────▼────┐ ┌────▼────┐  ┌───▼────┐
         │ Django   │ │ Worker  │  │ Beat   │
         │ (gunicorn)│ │         │  │        │
         └─────┬────┘ └────┬────┘  └────────┘
               │            │
         ┌─────▼────┐ ┌────▼────┐
         │ PostgreSQL│ │  Redis  │
         └──────────┘ └─────────┘
```

---

## Key Security Pattern: RLS Multi-Tenancy

- PostgreSQL RLS (Row-Level Security) enforces tenant isolation at the database level
- A non-superuser `crm_user` is created on init via `docker/postgres/init-rls-user.sql`
- Every query is automatically scoped to the requesting organization
- The MCP server (AI agent integration) inherits the user's org/role/RLS scope

---

## Summary

BottleCRM is a **6-service Docker Compose application** built on **Django 5 + SvelteKit 2**, requiring **PostgreSQL 16** and **Redis 7**. Docker is the primary development path (`docker compose up --build`), with a manual uv/pnpm alternative available. The setup is dev-oriented out of the box — moving to production requires adding gunicorn, a reverse proxy with TLS, S3 for media/static files, disabling debug mode, and rotating the secret key.
