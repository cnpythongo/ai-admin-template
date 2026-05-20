# ai-admin-template

一个基础于Harness Engineering理论从0开构建的后台管理框架模板.

- FastAPI backend + React frontend. This is a fresh project skeleton; most code is yet to be implemented.

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
