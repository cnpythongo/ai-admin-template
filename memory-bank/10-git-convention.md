# Git 提交规范

> 基于 Conventional Commits 2.0，与项目模块化结构对齐。

---

## 1. 提交格式

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**必须遵循：**
- `type` 和 `scope` 均为**小写英文字母**
- `description` 使用**中文**描述
- 行首不要加标点符号，`description` 末尾不加句号
- 一行不超过 72 个字符

---

## 2. Type 类型

| Type | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(user): 新增用户分页查询接口` |
| `fix` | 修复 Bug | `fix(menu): 修复菜单树递归层级错误` |
| `refactor` | 重构（不改变外部行为） | `refactor(backend): 抽取权限校验公共方法` |
| `style` | 代码格式修改（ruff / prettier / ESLint） | `style: 修复 ruff E501 行过长问题` |
| `docs` | 只改文档（memory-bank / README） | `docs: 补充 Evaluator 设计方案文档` |
| `test` | 增改测试 | `test(auth): 添加令牌刷新测试用例` |
| `chore` | 构建、CI、依赖等非源码变更 | `chore: 更新 ruff 至 0.15.13` |
| `perf` | 性能优化 | `perf(cache): 使用 Redis pipeline 批量写入权限` |

---

## 3. Scope 范围

按项目模块划分：

| Scope | 对应目录 | 说明 |
|-------|----------|------|
| `backend` | `backend/` | 后端全局改动（config / main / seed） |
| `auth` | `backend/app/api/v1/auth.py` | 认证模块 |
| `user` | `backend/app/api/v1/users.py` + services/models/schemas | 用户管理 |
| `department` | `backend/app/api/v1/departments.py` | 部门管理 |
| `role` | `backend/app/api/v1/roles.py` | 角色管理 |
| `permission` | `backend/app/api/v1/permissions.py` | 权限管理 |
| `menu` | `backend/app/api/v1/menus.py` | 菜单管理 |
| `system-config` | `backend/app/api/v1/system_configs.py` | 系统配置 |
| `operation-log` | `backend/app/api/v1/operation_logs.py` | 操作日志 |
| `frontend` | `frontend/` | 前端全局改动（App / router / stores） |
| `evaluator` | `scripts/evaluator.py` | 验收脚本 |
| `ci` | `.github/`、`Dockerfile` 等 | CI/CD 相关 |

**多模块改动：** 如果一次提交涉及多个模块，使用 `*` 或省略 scope：

```
feat: 实现操作日志分页查询接口（涉及 auth middleware 改造）
```

---

## 4. 提交示例

### 新功能

```
feat(department): 新增部门树接口

- 支持按状态筛选
- 空数据时返回空数组而非 404
```

### Bug 修复

```
fix(operation-log): 修复权限标识 system:log:list → system:operation_log:list

同步更新 seed.py 和文档
```

### 重构

```
refactor(backend): 抽取 OperationLogResponse 公共 schema

复用 get_list 和 get_detail 的序列化逻辑
```

### 代码风格

```
style: 修复 ruff E501 行过长问题（seed.py / security.py）
```

---

## 5. 分支策略

```
main          ← 生产分支，只接受 PR merge
  └─ develop  ← 开发主分支
       ├─ feat/user-management
       ├─ fix/department-delete-bug
       └─ refactor/permission-cache
```

| 分支前缀 | 用途 |
|---------|------|
| `feat/*` | 新功能开发 |
| `fix/*` | Bug 修复 |
| `refactor/*` | 重构 |
| `docs/*` | 文档 |
| `chore/*` | 构建/工具链 |

---

## 6. 提交频率

- **功能粒度为最小可验证单位**：每个接口 + 对应的测试作为一次提交
- 文件数量不宜过多（建议 ≤15 个文件/提交）
- 每次提交后确保 `ruff` 和 `tsc --noEmit` 通过
