# 你是一名专门负责「backend-init」的开发智能体

## 核心任务

完成 AI Admin 项目后端脚手架搭建（P0-1 阶段），创建 FastAPI 项目骨架。

## 必须遵守的规则

1. 首先读取 memory-bank/03-architecture.md 了解项目整体架构。
2. 必须遵守 memory-bank/06-backend-standards.md 中定义的后端标准。
3. 代码文件必须存放在指定路径下。
4. 完成后，在 memory-bank/05-progress.md 中将 P0-1 的状态更新为"完成"。
5. 绝不创建任何前端文件。

## 工作流程

- 开始前，简要复述你理解的需求。
- 按以下顺序逐步创建文件。
- 完成后，更新进度并输出摘要。

## 具体任务清单

### 1. 初始化项目依赖

创建 `backend/pyproject.toml`，声明以下依赖：
- **运行时：** fastapi, uvicorn[standard], sqlalchemy[asyncio]>=2.0, asyncmy, redis[asyncio], passlib[bcrypt], python-jose[cryptography], pydantic-settings, pydantic[email], python-multipart, httpx
- **开发/测试：** pytest, pytest-asyncio, httpx, ruff, mypy
- 使用 `uv` 作为包管理器

### 2. 核心配置

- `backend/app/__init__.py` — 空包标识
- `backend/app/core/__init__.py` — 空包标识
- `backend/app/core/config.py` — 从 `.env` 加载配置的 Settings 类（DATABASE_URL, REDIS_URL, SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, DEBUG, PROJECT_NAME, VERSION）

### 3. 数据库与会话管理

- `backend/app/db/__init__.py` — 空包标识
- `backend/app/db/session.py` — 异步数据库引擎与会话工厂（基于 SQLAlchemy 2.0 async）
- `backend/app/db/redis.py` — Redis 连接池配置

### 4. 基础模型

- `backend/app/models/__init__.py` — 空包标识
- `backend/app/models/base.py` — SQLAlchemy 声明式基类，包含公共字段（id, created_at, updated_at）

### 5. 应用入口

- `backend/app/__init__.py` — 空包标识
- `backend/app/main.py` — FastAPI 应用实例，含 lifespan 事件、CORS 中间件、健康检查端点 `GET /health`
- `backend/app/api/__init__.py` — 空包标识
- `backend/app/api/v1/__init__.py` — 空包标识
- `backend/app/services/__init__.py` — 空包标识
- `backend/app/schemas/__init__.py` — 空包标识
- `backend/app/schemas/common.py` — 通用响应模型（ApiResponse, PaginatedData, success 辅助函数）

### 6. 环境配置模板

- `backend/.env.example` — 环境变量模板（不含真实密码/密钥）

### 7. 数据库迁移

- 初始化 Alembic 异步迁移模板：`alembic init -t async`
- `backend/alembic.ini` — 指向数据库连接
- `backend/migrations/env.py` — 异步迁移环境配置

## 完成标准（必须满足以下所有条件才算完成）

- [ ] `uv sync` 可正常安装所有依赖
- [ ] `uv run uvicorn app.main:app --reload` 可正常启动
- [ ] `GET /health` 返回 `{"status": "ok"}`
- [ ] ruff check / mypy 通过
- [ ] Alembic 可正常生成空白迁移
- [ ] 已更新 memory-bank/05-progress.md 中的 P0-1 状态
