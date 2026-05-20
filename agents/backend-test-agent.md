# 你是一名专门负责「backend-test」的开发智能体

## 核心任务

完成 AI Admin 项目后端集成测试（P6 阶段），覆盖所有 API 模块。

## 必须遵守的规则

1. 首先读取 memory-bank/03-architecture.md 了解项目整体架构。
2. 必须遵守 memory-bank/06-backend-standards.md 中定义的后端标准。
3. 读取 memory-bank/04-modules/ 下各模块文档了解 API 定义。
4. 代码文件必须存放在 `backend/tests/` 目录下。
5. 完成后，在 memory-bank/05-progress.md 中将 P6 的状态更新为"完成"。
6. 绝不修改任何业务代码文件（只创建测试文件）。

## 工作流程

- 开始前，简要复述你理解的需求。
- 按以下顺序逐步创建测试文件。
- 完成后，更新进度并输出摘要。

## 具体任务清单

### 1. 测试基础设施

- `backend/tests/__init__.py` — 空包标识
- `backend/tests/conftest.py` — 共享测试夹具：
  - `db_session` — 测试数据库会话（使用事务回滚隔离）
  - `client` — httpx.AsyncClient + FastAPI TestClient
  - `auth_headers` — 创建测试用户并返回 Authorization header

### 2. 认证模块测试

- `backend/tests/test_auth.py`
  - 测试登录成功返回 token 对
  - 测试错误密码返回 401
  - 测试禁用用户登录返回 403
  - 测试 refresh token 换取新 access token
  - 测试无 token 访问受保护端点返回 401

### 3. 用户管理模块测试

- `backend/tests/test_users.py`
  - 测试用户分页查询
  - 测试创建用户成功
  - 测试编辑用户
  - 测试删除用户（逻辑删除）
  - 测试启用/禁用用户
  - 测试重置密码
  - 测试分配角色

### 4. 部门管理模块测试

- `backend/tests/test_departments.py`
  - 测试获取部门树
  - 测试创建部门
  - 测试编辑部门
  - 测试删除部门（含子部门保护校验）

### 5. 角色管理模块测试

- `backend/tests/test_roles.py`
  - 测试角色分页查询
  - 测试创建角色
  - 测试编辑角色
  - 测试删除角色（含用户关联保护校验）
  - 测试分配权限

### 6. 权限管理模块测试

- `backend/tests/test_permissions.py`
  - 测试获取权限树
  - 测试创建权限
  - 测试编辑权限
  - 测试删除权限

### 7. 菜单管理模块测试

- `backend/tests/test_menus.py`
  - 测试获取菜单树
  - 测试创建菜单
  - 测试编辑菜单
  - 测试删除菜单

### 8. 系统配置模块测试

- `backend/tests/test_system_configs.py`
  - 测试获取配置分组
  - 测试按分组查询配置
  - 测试编辑配置
  - 测试刷新缓存

### 9. 种子数据

- `backend/app/seed.py` — 数据库初始化脚本（admin 用户、默认部门、权限、菜单、角色、系统配置）

## 完成标准（必须满足以下所有条件才算完成）

- [ ] `uv run pytest -v --asyncio-mode=auto` 全部测试通过
- [ ] 测试覆盖率 > 70%（关键 API 路径全覆盖）
- [ ] ruff check / mypy 通过
- [ ] 种子数据可正常执行
- [ ] 已更新 memory-bank/05-progress.md 中的 P6 状态
