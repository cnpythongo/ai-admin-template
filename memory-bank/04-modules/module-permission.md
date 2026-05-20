# 权限管理模块详细需求

> 对应 PDD 第 4.4 节、实施计划 P2-B。本模块与部门管理、系统配置可并行开发，是菜单管理和角色管理的前置依赖。

---

## 1. 功能描述

提供细粒度权限资源（Permission Resource）的定义与管理，包含：

- 以树形结构展示所有权限资源
- 支持三种权限类型：**菜单权限**（页面访问）、**按钮权限**（页面内操作）、**API 权限**（后端接口）
- 新增权限（名称、编码、类型、上级权限、API 路径与方法）
- 编辑/删除权限（级联删除保护）
- 权限编码唯一性校验，规范格式 `模块:子模块:操作`

---

## 2. 输入输出

### 2.1 后端 API

#### GET `/api/v1/permissions/tree`

| 字段 | 说明 |
|------|------|
| **描述** | 获取权限树形结构 |
| **权限** | `system:permission:list` |
| **请求参数** | 可选 `?type=menu\|button\|api` 按类型筛选 |
| **响应** | 权限树数组（含 type 枚举，前端按类型着色） |

**PermissionTree 响应结构：**

```json
{
  "id": 1,
  "name": "用户管理",
  "code": "system:user",
  "type": "menu",
  "parent_id": null,
  "children": [
    {
      "id": 2,
      "name": "创建用户",
      "code": "system:user:create",
      "type": "button",
      "parent_id": 1,
      "children": []
    },
    {
      "id": 3,
      "name": "新增用户接口",
      "code": "system:user:create-api",
      "type": "api",
      "parent_id": 1,
      "api_path": "/api/v1/users",
      "api_method": "POST",
      "children": []
    }
  ]
}
```

#### POST `/api/v1/permissions`

| 字段 | 说明 |
|------|------|
| **权限** | `system:permission:create` |
| **请求体** | `{ name: string, code: string, type: "menu" \| "button" \| "api", parent_id?: number, api_path?: string, api_method?: "GET" \| "POST" \| "PUT" \| "DELETE" }` |
| **校验** | `code` 全局唯一，格式正则 `^[a-z]+:[a-z]+(:[a-z]+)?$`；`type=api` 时 `api_path` 和 `api_method` 必填 |

#### PUT `/api/v1/permissions/{id}`

| 字段 | 说明 |
|------|------|
| **权限** | `system:permission:update` |
| **约束** | `code` 不允许修改（唯一标识，修改等价于新建） |
| **校验** | parent_id 变更时不能指向自身或子孙节点 |

#### DELETE `/api/v1/permissions/{id}`

| 字段 | 说明 |
|------|------|
| **权限** | `system:permission:delete` |
| **校验** | 有子权限 → 409 "请先删除子权限"；有角色引用（在 role_permissions 表中存在）→ 409 "该权限已被 {n} 个角色使用" |

### 2.2 前端 Props / 事件

#### PermissionTree

| Prop | 类型 | 说明 |
|------|------|------|
| `dataSource` | `Permission[]` | 树形权限数据 |
| `loading` | `boolean` | 加载状态 |
| `typeFilter` | `string \| undefined` | 按类型筛选 |
| `onEdit` | `(record: Permission) => void` | 编辑回调 |
| `onDelete` | `(id: number) => void` | 删除回调 |

#### PermissionForm（Modal）

| Prop | 类型 | 说明 |
|------|------|------|
| `visible` | `boolean` | 弹窗可见性 |
| `record` | `Permission \| null` | 编辑数据 |
| `parentTree` | `Permission[]` | 上级权限树选项 |
| `onSubmit` | `(values: PermissionFormValues) => Promise<void>` | 提交 |
| `onCancel` | `() => void` | 取消关闭 |

**表单联动行为：**
- `type` 切换为 `"api"` 时，显示 `api_path`（Input）和 `api_method`（Select：GET/POST/PUT/DELETE）字段
- `type` 为 `"menu"` 或 `"button"` 时，隐藏 API 字段
- `code` 字段输入时自动转为小写，禁止输入空格和中文

---

## 3. 依赖接口

| 依赖 | 用途 | 备注 |
|------|------|------|
| [角色管理](./module-role.md) | 角色权限分配需读取权限树 | 角色模块是本模块的消费者 |
| [菜单管理](./module-menu.md) | 菜单绑定权限需读取权限树 | 菜单模块是本模块的消费者 |
| 操作日志 | 权限增删改需记录日志 | P5 阶段接入 |

**依赖方向：** 权限管理不依赖其他业务模块，仅依赖基础设施（模型、权限校验）。

---

## 4. 边缘情况

1. **编码格式校验**：权限编码必须符合 `模块:子模块:操作` 规范（如 `system:user:create`）。前端需做正则校验，后端做二次校验。允许两级格式（`模块:子模块`）作为菜单级别权限，三级格式（`模块:子模块:操作`）作为按钮/API 级别权限。
2. **类型变更约束**：已创建的权限不允许变更 `type` 字段（例如把菜单权限改为 API 权限），因为类型不同会导致子权限语义不一致。如有需要应删除重建。
3. **API 权限路径冲突**：不同权限记录不应指向相同的 `(api_path, api_method)` 组合，否则权限判定时会产生歧义。需在创建/编辑时做唯一性校验。
4. **权限编码变更影响**：权限 `code` 在角色菜单绑定后被引用，修改 `code` 会导致引用断裂。设计上禁止修改 `code`，如需变更应删除重建并重新分配角色。

---

## 5. 建议文件路径

```
后端：
  app/models/permission.py              # Permission 模型（含 type 枚举）
  app/schemas/permission.py             # Pydantic Schema
  app/services/permission_service.py    # 业务逻辑（树构建、编码校验、级联校验）
  app/api/v1/permissions.py             # 路由定义

前端：
  src/types/permission.ts               # TypeScript 类型（含 PermissionType 枚举）
  src/services/permission.ts            # API 请求封装
  src/pages/permission/index.tsx         # 权限管理页面
  src/pages/permission/components/PermissionForm.tsx  # 权限编辑表单（含类型联动）
```
