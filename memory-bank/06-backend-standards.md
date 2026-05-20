# 后端开发标准

## 技术栈

- Python 3.13, FastAPI, uv 管理环境
- 数据库：MySQL / PostgreSQL（双后端），SQLAlchemy 2.0 异步模式
- 驱动：asyncmy (MySQL) / asyncpg (PostgreSQL)
- 缓存：Redis (redis.asyncio)
- 测试：pytest-asyncio + httpx.AsyncClient

## 目录约定

backend/
├── app/
│   ├── core/          # 配置、安全、依赖注入
│   ├── models/        # SQLAlchemy 模型
│   ├── schemas/       # Pydantic 请求/响应模型
│   ├── api/           # 路由 (版本化 v1/v2)
│   ├── services/      # 业务逻辑层（禁止直接操作数据库）
│   ├── db/            # 数据库会话管理、Redis 连接池
│   └── main.py        # FastAPI 实例与启动
├── tests/
├── migrations/
├── .env.example
└── pyproject.toml     # uv 管理依赖

## 编码规范

- 类型注解：所有函数必须有完整参数和返回值类型注解
- 异步：涉及 I/O 的第三方库必须使用异步版本
- 错误处理：统一异常模型，返回 {"detail": "message"}，利用 HTTPException
- 日志：使用 logging 模块，配置文件化，关键操作记 INFO 日志
- 依赖注入：数据库会话、当前用户等通过 FastAPI Depends 获取
- 安全：密码哈希（passlib），JWT 令牌验证，管理接口需权限检查

## 数据库规则

- 多库兼容：只使用 ANSI SQL 和 SQLAlchemy 通用类型，避免方言特性
- 表命名：小写蛇形命名，复数形式（如 users, roles）
- 迁移：必须使用 Alembic 异步模板管理 schema 变更
- 连接池：数据库和 Redis 均需配置连接池，大小可通过环境变量调节

## 测试要求

- 单元测试：pytest-asyncio + httpx.AsyncClient
- 覆盖所有 service 层业务逻辑，关键 API 端到端测试
- 测试数据库使用独立库，保证幂等

## 禁止行为

- 禁止在异步环境使用同步 HTTP 客户端（如 requests），必须用 httpx.AsyncClient
- 禁止在 async def 路由内调用 time.sleep()，使用 asyncio.sleep
- 禁止直接 print 调试，使用 logger
- 禁止硬编码密钥或连接串，一律从环境变量或 .env 读取
