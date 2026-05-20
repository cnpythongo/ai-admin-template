# 用户管理模块详细需求

> 对应 PDD 第 4.1 节、实施计划 P4。本模块依赖部门管理和角色管理完成后开发。

---

## 1. 功能描述

提供用户的增删改查、状态管理、密码重置、角色与部门分配，包含：

- 分页展示用户列表，多条件筛选（用户名、邮箱、手机号、部门、角色、状态）
- 新增用户（用户名、邮箱、手机号、密码、部门、角色）
- 编辑用户（用户名不可修改）
- 逻辑删除用户（超级管理员不可删除）
- 启用/禁用用户账号
- 密码重置为预设默认密码
- 为用户分配角色（一个或多个）
- 为用户分配部门（仅一个）
- 当前登录用户查看/编辑个人信息

---

## 2. 输入输出

### 2.1 后端 API

#### GET `/api/v1/users`

| 字段 | 说明 |
|------|------|
| **描述** | 分页查询用户列表 |
| **权限** | `system:user:list` |
| **请求参数** | `?page=1&page_size=10&username=xxx&email=xxx&phone=xxx&department_id=1&role_id=1&status=0\|1` |
| **响应** | 分页数据（密码字段永不返回） |

**UserResponse 结构：**

```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "phone": "13800138000",
  "status": 1,
  "department_id": 1,
  "department_name": "总公司",
  "role_ids": [1, 2],
  "role_names": ["超级管理员", "系统管理员"],
  "is_superuser": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

#### POST `/api/v1/users`

| 字段 | 说明 |
|------|------|
| **权限** | `system:user:create` |
| **请求体** | `{ username: string, email: string, phone?: string, password?: string, department_id?: number, role_ids?: number[] }` |
| **默认密码** | `password` 不传时使用系统配置中的默认密码（如 `123456`） |
| **校验** | `username` / `email` / `phone` 全局唯一（包括已逻辑删除的记录） |

#### PUT `/api/v1/users/{id}`

| 字段 | 说明 |
|------|------|
| **权限** | `system:user:update` |
| **约束** | `username` 不允许修改；不能修改自身角色为更低权限 |

#### DELETE `/api/v1/users/{id}`

| 字段 | 说明 |
|------|------|
| **权限** | `system:user:delete` |
| **逻辑** | 设置 `is_deleted=true`；**不可删除 `is_superuser=true` 的用户** |
| **校验** | 目标用户是超级管理员 → 403 "不能删除超级管理员"；目标用户是自身 → 400 "不能删除自己" |

#### PUT `/api/v1/users/{id}/status`

| 字段 | 说明 |
|------|------|
| **描述** | 启用/禁用用户 |
| **权限** | `system:user:update` |
| **请求体** | `{ status: 0 \| 1 }` |
| **校验** | **不可禁用 `is_superuser=true` 的用户**；不可禁用自身 |

#### POST `/api/v1/users/{id}/reset-password`

| 字段 | 说明 |
|------|------|
| **描述** | 重置用户密码为默认密码 |
| **权限** | `system:user:update` |
| **响应** | 200，返回无敏感信息的确认消息 |

#### PUT `/api/v1/users/{id}/roles`

| 字段 | 说明 |
|------|------|
| **描述** | 为用户分配角色（全量覆盖） |
| **权限** | `system:user:update` |
| **请求体** | `{ role_ids: number[] }` |

#### PUT `/api/v1/users/{id}/department`

| 字段 | 说明 |
|------|------|
| **描述** | 为用户分配部门 |
| **权限** | `system:user:update` |
| **请求体** | `{ department_id: number \| null }` |

#### GET `/api/v1/auth/me`

| 字段 | 说明 |
|------|------|
| **描述** | 获取当前登录用户信息 |
| **权限** | 登录即可 |
| **响应** | UserResponse（含权限标识列表 `permissions: string[]`） |

#### PUT `/api/v1/auth/me`

| 字段 | 说明 |
|------|------|
| **描述** | 当前用户修改个人信息 |
| **权限** | 登录即可 |
| **请求体** | `{ email?: string, phone?: string }` |
| **约束** | 不允许通过此接口修改 `username`、`password`、`department_id`、`role_ids` |

#### POST `/api/v1/auth/login`

| 字段 | 说明 |
|------|------|
| **描述** | 用户登录，返回 JWT 令牌对 |
| **权限** | 无（公开接口） |
| **请求体** | `{ username: string, password: string }` |
| **响应** | `{ access_token, refresh_token, token_type: "bearer" }` |
| **校验** | 用户名不存在或密码错误 → 401 "用户名或密码错误"；账户被禁用 → 403 "账户已被禁用" |

#### POST `/api/v1/auth/refresh`

| 字段 | 说明 |
|------|------|
| **描述** | 使用 refresh_token 刷新 access_token |
| **权限** | 无（凭 refresh_token 验证） |
| **请求体** | `{ refresh_token: string }` |
| **响应** | `{ access_token, refresh_token, token_type: "bearer" }` |
| **校验** | refresh_token 无效或过期 → 401 |

#### POST `/api/v1/auth/logout`

| 字段 | 说明 |
|------|------|
| **描述** | 用户登出，将 refresh_token 加入黑名单 |
| **权限** | 登录即可 |
| **请求头** | `Authorization: Bearer <token>` |
| **逻辑** | 将 refresh_token 加入 Redis 黑名单（TTL=7天） |

#### PUT `/api/v1/auth/me/password`

| 字段 | 说明 |
|------|------|
| **描述** | 当前用户修改密码 |
| **权限** | 登录即可 |
| **请求体** | `{ old_password: string, new_password: string }` |
| **校验** | 旧密码错误 → 400 "原密码不正确" |

### 2.2 前端 Props / 事件

#### UserPage

| 子组件 | 说明 |
|--------|------|
| **UserSearchForm** | 搜索栏：用户名 Input、邮箱 Input、部门 TreeSelect、角色 Select、状态 Select |
| **UserTable** | 用户分页表格，含行操作按钮（编辑/删除/状态切换/重置密码/角色分配） |

#### UserForm（Modal）

| Prop | 类型 | 说明 |
|------|------|------|
| `visible` | `boolean` | 弹窗可见性 |
| `record` | `User \| null` | 编辑数据 |
| `departmentTree` | `Department[]` | 部门树选项（TreeSelect） |
| `roleOptions` | `Role[]` | 角色选项（多选 Select） |
| `onSubmit` | `(values: UserFormValues) => Promise<void>` | 提交 |
| `onCancel` | `() => void` | 取消关闭 |

**表单行为：**
- 新增模式：显示所有字段（含密码字段，可选填）
- 编辑模式：用户名禁用，密码字段隐藏（用"重置密码"功能替代）
- 部门使用 TreeSelect（单选）
- 角色使用 Select（多选 mode="multiple"）

#### RoleAssignModal

| Prop | 类型 | 说明 |
|------|------|------|
| `visible` | `boolean` | 弹窗可见性 |
| `user` | `User` | 当前用户 |
| `roleOptions` | `Role[]` | 所有可选角色 |
| `onSubmit` | `(roleIds: number[]) => Promise<void>` | 提交分配 |
| `onCancel` | `() => void` | 取消关闭 |

#### ProfilePage

| 子组件 | 说明 |
|--------|------|
| **ProfileForm** | 个人资料编辑表单（邮箱、手机号） |
| **PasswordForm** | 修改密码表单（旧密码、新密码、确认密码） |

---

## 3. 依赖接口

| 依赖 | 用途 | 备注 |
|------|------|------|
| [部门管理](./module-department.md) | 用户部门选择（TreeSelect 数据源） | **必须先完成** |
| [角色管理](./module-role.md) | 用户角色分配（Select 数据源） | **必须先完成** |
| 操作日志 | 用户相关操作的日志记录 | P5 阶段接入 |

**依赖方向：**

```
User Service ──→ User 模型
           ──→ Department 模型（读部门树）
           ──→ Role 模型（读角色列表 + user_roles 关联）
           ──→ 权限校验 require_permissions
           ──→ auth_service（密码哈希 + JWT）
```

---

## 4. 边缘情况

1. **逻辑删除与唯一约束**：`is_deleted=true` 的用户记录仍占用 `username` / `email`/ `phone` 的唯一性。新增用户时，如果用户名与已删除用户重复，返回 409 "该用户名已被使用"。这一约束要求唯一索引包含 `is_deleted` 条件（部分索引）或在应用层做校验。
2. **超级管理员保护**：系统预设的 `admin` 用户（`is_superuser=true`）不可被删除、不可被禁用、角色不可被修改。前端遇到这些操作时应禁用相应按钮或拦截。后端 API 级别做二次校验。
3. **自操作保护**：用户不应能删除自己、禁用自己、或将自己的角色降级（移除自身已有的权限）。后端需在相关 API 中校验 `current_user.id != target_user.id`。
4. **默认密码安全**：首次创建用户或重置密码时使用默认密码，应在操作响应中告知"初始密码为 xxxxxx"，并建议用户在首次登录后修改密码。默认密码应在系统配置中可配置。
5. **分页+筛选性能**：用户表数据量较大时，多条件筛选（用户名模糊搜索、部门/角色查询）可能导致性能问题。需在 `username`、`email`、`phone`、`department_id`、`is_deleted` 上建立合适的复合索引。

---

## 5. 建议文件路径

```
后端：
  app/models/user.py                    # User 模型 + user_roles 关联表
  app/schemas/user.py                   # Pydantic Schema
  app/services/user_service.py          # 业务逻辑（CRUD、逻辑删除、状态管理、密码重置）
  app/api/v1/users.py                   # 用户管理路由
  app/api/v1/auth.py                    # 个人信息路由（/auth/me）

前端：
  src/types/user.ts                     # TypeScript 类型
  src/services/user.ts                  # API 请求封装
  src/pages/user/index.tsx               # 用户管理页面
  src/pages/user/components/UserForm.tsx      # 用户编辑表单
  src/pages/user/components/RoleAssignModal.tsx  # 角色分配弹窗
  src/pages/user/components/PasswordResetModal.tsx  # 密码重置确认弹窗
  src/pages/profile/index.tsx            # 个人信息页面
```
