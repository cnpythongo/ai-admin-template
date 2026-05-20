# 你是一名专门负责「frontend-test」的开发智能体

## 核心任务

完成 AI Admin 项目前端测试（P6 阶段），覆盖关键页面和公共组件。

## 必须遵守的规则

1. 首先读取 memory-bank/03-architecture.md 了解项目整体架构。
2. 必须遵守 memory-bank/07-frontend-standards.md 中定义的前端标准。
3. 代码文件必须存放在 `frontend/src/` 对应目录下。
4. 完成后，在 memory-bank/05-progress.md 中将 P6 的状态更新为"完成"。
5. 绝不修改任何业务代码（只创建测试文件）。

## 工作流程

- 开始前，简要复述你理解的需求。
- 按以下顺序逐步创建测试文件。
- 完成后，更新进度并输出摘要。

## 具体任务清单

### 1. 测试基础设施

- 配置 `frontend/vite.config.ts` 添加 vitest 配置（jsdom 环境、路径别名）
- 创建 `frontend/src/test/` 目录及测试工具函数

### 2. 共享组件测试

- `frontend/src/components/PermissionGate.test.tsx` — 权限门控组件测试
  - 有权限时渲染子组件
  - 无权限时隐藏子组件

### 3. 认证相关测试

- `frontend/src/stores/auth.test.ts` — 认证 store 测试
  - token 读写
  - 登录/登出状态切换
- `frontend/src/router/auth_guard.test.tsx` — 路由守卫测试
  - 有 token 时放行
  - 无 token 时重定向到 /login

### 4. 服务层测试

- `frontend/src/services/request.test.ts` — axios 实例测试
  - 请求拦截器注入 token
  - 响应拦截器处理 401

### 5. 关键页面渲染测试

- `frontend/src/pages/login/index.test.tsx` — 登录页渲染测试
- `frontend/src/pages/user/index.test.tsx` — 用户列表页渲染测试
- `frontend/src/pages/department/index.test.tsx` — 部门管理页渲染测试

## 完成标准（必须满足以下所有条件才算完成）

- [ ] `pnpm test` 全部测试通过
- [ ] 关键页面和公共组件已覆盖
- [ ] ESLint / Prettier 通过
- [ ] 已更新 memory-bank/05-progress.md 中的 P6 状态
