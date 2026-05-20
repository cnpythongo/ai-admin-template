# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Admin dashboard (后台管理系统) — FastAPI backend + React frontend. This is a fresh project skeleton; most code is yet to be implemented.

## Commands

### Backend (`cd backend`)

| Command | Description |
|---------|-------------|
| `uv sync` | Install/sync dependencies |
| `uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` | Start dev server |
| `uv run pytest -v --asyncio-mode=auto` | Run all tests |
| `uv run pytest -v --asyncio-mode=auto tests/path/to/test.py -k "test_name"` | Run a single test |
| `uv run alembic revision --autogenerate -m "message"` | Generate migration |
| `uv run alembic upgrade head` | Apply migrations |
| `uv run ruff check .` | Lint check |
| `uv run mypy .` | Type check |

### Frontend (`cd frontend`)

| Command | Description |
|---------|-------------|
| `pnpm install` | Install dependencies |
| `pnpm dev` | Start dev server |
| `pnpm build` | Production build |
| `pnpm test` | Run tests |
| `pnpm lint` | Lint (ESLint) |

## Architecture

### Layered structure (strict, no cross-layer calls)

**Backend (FastAPI):**
```
routes (api/) → services/ → models/ + db/
```
- `app/api/` — Route handlers (versioned, e.g. v1/v2)
- `app/services/` — Business logic layer (no direct DB access)
- `app/models/` — SQLAlchemy 2.0 async models
- `app/schemas/` — Pydantic request/response schemas
- `app/core/` — Config, security, dependency injection
- `app/db/` — DB session management, Redis connection pool
- `tests/` — pytest-asyncio + httpx.AsyncClient
- `migrations/` — Alembic migration scripts

**Frontend (React):**
```
pages/ → components/ + hooks/ → services/ (axios)
           stores/ (Zustand)
```
- `src/pages/` — Page-level components (route targets)
- `src/components/` — Shared/reusable components
- `src/hooks/` — Custom React hooks
- `src/services/` — Axios-based API client layer (unified interceptors)
- `src/stores/` — Zustand state stores
- `src/types/` — TypeScript type definitions
- `src/utils/` — Utility functions

### Tech stack

- **Backend:** Python 3.13, FastAPI, uv, SQLAlchemy 2.0 (async), MySQL/PostgreSQL, Redis, Alembic, pytest-asyncio
- **Frontend:** React 18+, TypeScript, Vite, Ant Design 5.x, Zustand, React Router v6, axios, Vitest

### Seven modules (built in dependency order)

1. **Department** (P2-A) — Tree-based department CRUD, cycle detection, cascade delete protection
2. **Permission** (P2-B) — Three-tier permissions (menu/button/API), tree structure, code validation
3. **System Config** (P2-C) — Grouped config, sensitive value encryption, Redis cache, dynamic form
4. **Menu** (P3-A) — Dynamic menu tree, permission binding, user-specific menu filtering
5. **Role** (P3-B) — Role-permission binding, cache invalidation on permission change
6. **User** (P4) — Multi-condition pagination, soft delete, status toggle, password reset, role/dept assignment
7. **Operation Log** (P5) — Async Redis queue → batch DB write, multi-dimension filtering, auto cleanup

### Implementation phases

| Phase | Description | Parallelism |
|-------|-------------|-------------|
| P0 | Project scaffolding (frontend + backend) | Frontend/backend in parallel |
| P1 | Auth & infrastructure (models, JWT, permissions) | Sequential |
| P2 | Independent modules (dept, permission, config) | All 3 in parallel |
| P3 | Dependent modules (menu, role) | Parallel (both depend on P2-B) |
| P4 | User management (depends on P2-A + P3-B) | Sequential |
| P5 | Operation log (depends on all above) | Sequential |
| P6 | Integration tests & seed data | Backend/frontend tests in parallel |

## Key Constraints

- All I/O must be async (FastAPI async routes, SQLAlchemy async sessions, httpx.AsyncClient, aioredis)
- No synchronous blocking calls (`time.sleep` → `asyncio.sleep`, `requests` → `httpx.AsyncClient`)
- DB operations through services layer only, never from routes directly
- All secrets/config from environment variables / `.env` — never hardcoded
- Backend: passlib for password hashing, JWT for auth, FastAPI Depends for DI
- Frontend: no `any` types, handle loading/error states for all async requests, route guards for permissions
- Django-style model naming: lowercase snake_case, plural table names (e.g. `users`, `roles`)
- New models require Alembic migration; new API endpoints require frontend service layer updates

## Unified API Format

```json
// Success: {"code": 0, "data": {...}, "message": "ok"}
// Paginated: {"code": 0, "data": {"items": [...], "total": 100, "page": 1, "page_size": 10}, "message": "ok"}
// Error: {"code": 40001, "data": null, "message": "用户名已存在"}
```

## Multi-Agent Orchestration

- `.claude/rules.md` — Orchestrator agent instructions for multi-agent workflow
- `scripts/run-agent.sh` — Launches sub-agents in new terminal windows
- `agents/` — Per-module agent task definitions (user-agent, role-agent, etc.)
- Each sub-agent completes its module and updates `memory-bank/05-progress.md`

## Reference Documents (memory-bank/)

Context documents are numbered and should be read in order:

1. `01-product-design-doc.md` — Product requirements
2. `02-implementation-plan.md` — Task breakdown (phases, parallelism, file paths)
3. `03-architecture.md` — Architecture decisions, data flows, component tree
4. `04-modules/` — Module-level requirements
5. `05-progress.md` — Progress tracking (update after completing tasks)
6. `06-backend-standards.md` — Backend coding standards (detailed)
7. `07-frontend-standards.md` — Frontend coding standards (detailed)
8. `08-run-commands.md` — All run commands
