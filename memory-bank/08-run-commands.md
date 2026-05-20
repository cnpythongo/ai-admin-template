# 常用命令

## 后端 (在 backend/ 下执行)

- 环境初始化：`uv sync`
- 开发服务器：`uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- 运行测试：`uv run pytest -v --asyncio-mode=auto`
- 数据库迁移：`uv run alembic revision --autogenerate -m "描述"` / `uv run alembic upgrade head`

## 前端 (在 frontend/ 下执行)

- 安装依赖：`pnpm install`
- 开发服务器：`pnpm dev`
- 构建：`pnpm build`
- 测试：`pnpm test`
