# 项目开发总则 (AGENTS.md)

> 本文件是项目“最高索引”，所有智能体必须首先阅读此文件，然后按需跳转到具体标准文档。

## 1. 项目定位

- 项目类型：基础后台管理系统 (Admin Dashboard)
- 业务目标：后端提供用户管理、权限、CRUD 等 API；前端提供配套管理界面
- 非目标：不做移动端适配、WebSocket、SSR

## 2. 工程结构速览

ai-admin/
├── backend/               # 后端 FastAPI 源码
├── frontend/              # 前端 React + Antd 源码
└── AGENTS.md              # 本文件

> 完整目录树及分层约束见 `memory-bank/03-architecture.md`。

## 3. 关键规则文档索引

所有 Agent 在开始任何任务前，必须按角色读取对应的规则文件：

- 全局架构与模块约定：`memory-bank/03-architecture.md`
- 后端技术栈与编码规范：**`memory-bank/06-backend-standards.md`**
- 前端技术栈与编码规范：**`memory-bank/07-frontend-standards.md`**
- 常用运行命令：**`memory-bank/08-run-commands.md`**
- 产品设计文档：`memory-bank/01-product-design-doc.md`
- 实施计划：`memory-bank/02-implementation-plan.md`
- 模块需求详情：`memory-bank/04-modules/`
- 进度跟踪：`memory-bank/05-progress.md`

## 4. 全局不可违背约束（精简版）

以下几条是“红线”，所有前后端代码都必须遵守：

- 任何 I/O 操作必须使用对应语言/框架的异步方式，禁止同步阻塞。
- 所有密钥、连接串、环境相关配置必须通过环境变量/`.env` 提供，严禁硬编码。
- 后端数据库操作必须通过 `services` 层，前端 API 调用必须通过统一封装的请求模块。
- 生成代码必须通过预设的静态检查（后端 ruff/mypy，前端 ESLint/Prettier）。

## 5. 智能体协作约定

- 遵循 `memory-bank/` 目录下的编号顺序读取上下文，不可跳过阶段。
- 完成任务后更新 `memory-bank/05-progress.md` 中的对应状态。
- 修改数据库模型必须生成 Alembic 迁移脚本，修改 API 接口必须同步更新前端请求层定义。
