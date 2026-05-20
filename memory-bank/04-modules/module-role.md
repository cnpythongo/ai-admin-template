# 角色管理模块详细需求

> 对应 PDD 第 4.3 节、实施计划 P3-B。本模块依赖权限管理完成，与菜单管理可并行开发。

---

## 1. 功能描述

提供角色的增删改查，角色与权限的绑定/解绑，角色与用户的关联管理，包含：

- 分页展示角色列表，支持按角色名、状态筛选
- 新增角色（名称、编码、描述）
- 编辑角色（编码不可修改）
- 删除角色（有用户关联时禁止删除）
- 权限分配：为角色分配菜单权限、按钮权限、API 权限
- 角色成员：查看并管理该角色下的用户列表
- 角色权限变更后主动失效相关用户的 Redis 权限缓存

---

## 2. 输入输出

### 2.1 后端 API

#### GET `/api/v1/roles`

| 字段 | 说明 |
|------|------|
| **描述** | 分页查询角色列表 |
| **权限** | `system:role:list` |
| **请求参数** | `?page=1&page_size=10&name=xxx&status=0\|1` |
| **响应** | 分页数据（含角色基本信息） |

#### POST `/api/v1/roles`

| 字段 | 说明 |
|------|------|
| **权限** | `system:role:create` |
| **请求体** | `{ name: string, code: string, description?: string, status?: 0 \| 1 }` |
| **校验** | `code` 全局唯一，不可修改；`code` 格式 `^[a-zA-Z][a-zA-Z0-9_]*$` |

#### PUT `/api/v1/roles/{id}`

| 字段 | 说明 |
|------|------|
| **权限** | `system:role:update` |
| **约束** | `code` 不允许修改 |

#### DELETE `/api/v1/roles/{id}`

| 字段 | 说明 |
|------|------|
| **权限** | `system:role:delete` |
| **校验** | 有关联用户（在 user_roles 表中存在）→ 409 "该角色下还有 {n} 名用户，请先移除" |

#### PUT `/api/v1/roles/{id}/permissions`

| 字段 | 说明 |
|------|------|
| **描述** | 分配角色权限（全量覆盖） |
| **权限** | `system:role:update` |
| **请求体** | `{ permission_ids: number[] }` |
| **逻辑** | 1. 全量替换 `role_permissions` 关联表 2. 查询所有拥有该角色的用户 3. 逐个删除这些用户的 Redis 缓存 `user_perm:{user_id}` 4. 返回成功 |
| **注意** | 空数组 `[]` 表示清空角色所有权限 |

#### GET `/api/v1/roles/{id}/permissions`

| 字段 | 说明 |
|------|------|
| **描述** | 获取角色已分配的权限 ID 列表 |
| **权限** | `system:role:list` |
| **响应** | 权限 ID 数组 `number[]` |

#### GET `/api/v1/roles/{id}/users`

| 字段 | 说明 |
|------|------|
| **描述** | 查询角色下的用户列表 |
| **权限** | `system:role:list` |
| **响应** | 用户简要信息数组（id, username, email, status） |

### 2.2 前端 Props / 事件

#### RoleTable

| Prop | 类型 | 说明 |
|------|------|------|
| `dataSource` | `Role[]` | 分页角色数据 |
| `loading` | `boolean` | 加载状态 |
| `pagination` | `{ current, pageSize, total }` | 分页信息 |
| `searchParams` | `{ name?, status? }` | 搜索条件 |
| `onSearch` | `(params) => void` | 搜索回调 |
| `onEdit` | `(record: Role) => void` | 编辑回调 |
| `onDelete` | `(id: number) => void` | 删除回调 |
| `onAssignPermissions` | `(record: Role) => void` | 权限分配回调 |
| `onViewUsers` | `(record: Role) => void` | 查看成员回调 |

#### RoleForm（Modal）

| Prop | 类型 | 说明 |
|------|------|------|
| `visible` | `boolean` | 弹窗可见性 |
| `record` | `Role \| null` | 编辑数据 |
| `onSubmit` | `(values: RoleFormValues) => Promise<void>` | 提交 |
| `onCancel` | `() => void` | 取消关闭 |

**约束：**
- 编辑模式下 `code` 字段禁用
- `code` 输入时自动转为小写，禁止空格和特殊字符

#### PermissionTree（Modal）- 权限分配

| Prop | 类型 | 说明 |
|------|------|------|
| `visible` | `boolean` | 弹窗可见性 |
| `role` | `Role` | 当前角色 |
| `permissionTree` | `Permission[]` | 完整权限树数据 |
| `checkedIds` | `number[]` | 已选中的权限 ID 列表 |
| `onSubmit` | `(permissionIds: number[]) => Promise<void>` | 提交分配 |
| `onCancel` | `() => void` | 取消关闭 |

**树形复选框行为：**
- 选中父节点时，所有子节点自动选中
- 取消父节点时，所有子节点自动取消
- 子节点部分选中时，父节点显示半选状态（Ant Design Tree `checkable` + `checkStrictly=false`）

---

## 3. 依赖接口

| 依赖 | 用途 | 备注 |
|------|------|------|
| [权限管理](./module-permission.md) | 权限分配需要读取权限树 | **必须先完成权限管理模块** |
| [用户管理](./module-user.md) | 角色成员列表 | 仅查询关联，可先 Mock |
| [菜单管理](./module-menu.md) | 角色权限影响菜单可见性 | 间接依赖（通过权限缓存影响） |
| Redis | 权限缓存失效 | 角色权限变更后清除相关用户缓存 |
| 操作日志 | 角色增删改操作需记录日志 | P5 阶段接入 |

---

## 4. 边缘情况

1. **角色编码不可变**：角色 `code` 在创建后不可修改，因为系统内部可能依赖 `code` 做逻辑判断（如超级管理员角色 `code=admin` 的特殊处理）。编辑角色时前端需禁用 `code` 输入框。
2. **权限分配的事务性**：权限分配包含两个步骤——更新数据库关联表 + 清除 Redis 缓存。如果数据库更新成功但 Redis 清除失败（如 Redis 宕机），用户的权限缓存会"过时"（旧权限依然有效，新权限下次登录才生效）。应记录日志并在下次请求时自动重建缓存（缓存未命中时从数据库加载）。
3. **空权限角色**：允许角色没有任何权限（`permission_ids=[]`）。这种角色只能访问完全不设权限限制的菜单和 API。前端权限分配弹窗应允许"全清"操作。
4. **角色删除保护**：如果角色下有大量用户（如数千人），删除时做 `count` 查询即可（`SELECT COUNT(*) FROM user_roles WHERE role_id=?`），不需要加载所有用户记录。返回的提示信息中的数字即为该 count 值。

---

## 5. 建议文件路径

```
后端：
  app/models/role.py                    # Role 模型 + role_permissions 关联表
  app/schemas/role.py                   # Pydantic Schema
  app/services/role_service.py          # 业务逻辑（CRUD、权限分配、缓存失效）
  app/services/permission_cache_service.py  # 权限缓存管理（失效/重建）
  app/api/v1/roles.py                   # 路由定义

前端：
  src/types/role.ts                     # TypeScript 类型
  src/services/role.ts                  # API 请求封装
  src/pages/role/index.tsx               # 角色管理页面
  src/pages/role/components/RoleForm.tsx       # 角色编辑表单
  src/pages/role/components/PermissionTree.tsx # 权限分配弹窗（复用于菜单模块？）
  src/pages/role/components/RoleUsers.tsx      # 角色成员抽屉
```
