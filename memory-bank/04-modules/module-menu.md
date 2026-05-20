# 菜单管理模块详细需求

> 对应 PDD 第 4.5 节、实施计划 P3-A。本模块依赖权限管理完成，与角色管理可并行开发。

---

## 1. 功能描述

提供动态菜单树的配置维护，支持前端动态路由生成，包含：

- 以树形结构展示所有菜单项（展开/折叠）
- 新增菜单（名称、图标、路由路径、前端组件路径、上级菜单、排序号、是否隐藏、是否外链）
- 编辑/删除菜单（级联删除保护）
- 菜单与权限标识手动绑定（一个菜单可关联多个权限标识）
- 根据当前用户权限动态生成可访问的菜单树和路由表
- 支持"内部路由"和"外部链接"两种菜单类型

---

## 2. 输入输出

### 2.1 后端 API

#### GET `/api/v1/menus/tree`

| 字段 | 说明 |
|------|------|
| **描述** | 获取完整菜单树（管理端用） |
| **权限** | `system:menu:list` |
| **响应** | 菜单树数组 |

#### GET `/api/v1/menus/user-menus`

| 字段 | 说明 |
|------|------|
| **描述** | 获取当前用户可访问的菜单树（动态路由用） |
| **权限** | 登录即可（无需额外权限标识） |
| **逻辑** | 遍历完整菜单树，根据当前用户的权限标识集合过滤：菜单绑定的权限标识中，只要有一个在当前用户的权限集合内，就保留该菜单；对于父菜单，只要有任意一个子菜单可见，父菜单就可见 |
| **响应** | 过滤后的菜单树（不含绑定权限信息） |

**MenuTree 响应结构：**

```json
{
  "id": 1,
  "name": "系统管理",
  "icon": "SettingOutlined",
  "route_path": "/system",
  "component": null,
  "hidden": false,
  "is_external_link": false,
  "sort": 1,
  "parent_id": null,
  "permission_ids": [1, 2],
  "children": [
    {
      "id": 2,
      "name": "用户管理",
      "icon": "UserOutlined",
      "route_path": "/system/user",
      "component": "system/user/index",
      "hidden": false,
      "is_external_link": false,
      "sort": 1,
      "parent_id": 1,
      "permission_ids": [1],
      "children": []
    }
  ]
}
```

#### POST `/api/v1/menus`

| 字段 | 说明 |
|------|------|
| **权限** | `system:menu:create` |
| **请求体** | `{ name, icon?, route_path, component?, parent_id?, sort, hidden, is_external_link, permission_ids: number[] }` |
| **校验** | `route_path` 在同级菜单下唯一；外链时 `is_external_link=true`，此时 `component` 不需要填写 |

#### PUT `/api/v1/menus/{id}`

| 字段 | 说明 |
|------|------|
| **权限** | `system:menu:update` |
| **校验** | parent_id 变更时环检测；permission_ids 会全量替换 |

#### DELETE `/api/v1/menus/{id}`

| 字段 | 说明 |
|------|------|
| **权限** | `system:menu:delete` |
| **校验** | 有子菜单 → 409 "请先删除子菜单" |

### 2.2 前端 Props / 事件

#### MenuTree

| Prop | 类型 | 说明 |
|------|------|------|
| `dataSource` | `Menu[]` | 树形菜单数据 |
| `loading` | `boolean` | 加载状态 |
| `onEdit` | `(record: Menu) => void` | 编辑回调 |
| `onDelete` | `(id: number) => void` | 删除回调 |
| `onCreateChild` | `(parent: Menu) => void` | 创建子菜单回调 |

#### MenuForm（Modal）

| Prop | 类型 | 说明 |
|------|------|------|
| `visible` | `boolean` | 弹窗可见性 |
| `record` | `Menu \| null` | 编辑数据 |
| `parentTree` | `Menu[]` | 上级菜单树选项 |
| `permissionTree` | `Permission[]` | 权限树（用于权限多选 TreeSelect） |
| `onSubmit` | `(values: MenuFormValues) => Promise<void>` | 提交 |
| `onCancel` | `() => void` | 取消关闭 |

**表单特殊字段：**

| 字段 | 控件 | 说明 |
|------|------|------|
| `icon` | `IconPicker` | 图标选择器（@ant-design/icons 列表） |
| `route_path` | `Input` | 路由路径，如 `/system/user` |
| `component` | `Input` | 前端组件路径，对应 `src/pages/` 下的路径（如 `system/user/index`） |
| `permission_ids` | `TreeSelect`（多选） | 从权限树中选择关联权限 |
| `hidden` | `Switch` | 是否在侧边栏隐藏（作为纯路由目录） |
| `is_external_link` | `Switch` | 是否为外部链接，开启后隐藏 component 字段，显示 url 字段 |

#### dynamic_routes.tsx（路由生成逻辑）

```typescript
// 流程：从 Zustand store 获取 userMenus → 递归构建 RouteObject[]
// 隐藏菜单（hidden=true）不出现在侧边栏，但仍生成路由
// 外链菜单（is_external_link=true）不生成路由，仅在侧边栏渲染为 <a> 标签
```

---

## 3. 依赖接口

| 依赖 | 用途 | 备注 |
|------|------|------|
| [权限管理](./module-permission.md) | 菜单-权限绑定需要读取权限树 | **必须先完成权限管理模块** |
| [用户管理](./module-user.md) | `user-menus` 接口根据用户权限过滤 | 仅数据依赖，API 独立 |
| 操作日志 | 菜单增删改需记录日志 | P5 阶段接入 |

**依赖方向：**

```
菜单 Service ──→ Menu 模型
           ──→ Permission 模型（读权限树用于绑定）
           ──→ 权限校验 require_permissions
           ──→ User → Role → Permission（user-menus 过滤链）
```

---

## 4. 边缘情况

1. **菜单与权限的绑定关系**：一个菜单可绑定零个、一个或多个权限标识。零个权限的菜单对所有登录用户可见；一个或多个权限的菜单，用户只要拥有其中任意一个即可访问。
2. **隐藏菜单的权限校验**：`hidden=true` 的菜单虽然不在侧边栏展示，但路由仍然存在。如果绑定了权限标识，路由守卫仍然需要做权限校验，否则用户可以直接通过 URL 访问隐藏菜单页面。
3. **外链菜单处理**：`is_external_link=true` 的菜单在侧边栏渲染为 `<a href="url" target="_blank">`，不参与前端路由。`component` 字段此时无意义，后端应忽略。
4. **根菜单保护**：删除根级菜单时，如果有子菜单应禁止删除；如果根菜单被删除，所有子菜单失去入口，需提示先迁移或删除子菜单。
5. **路由冲突**：不同菜单的 `route_path` 应全局唯一（不限于同级），否则动态路由生成时后面的会覆盖前面的。需做全局唯一校验。

---

## 5. 建议文件路径

```
后端：
  app/models/menu.py                # Menu 模型
  app/schemas/menu.py               # Pydantic Schema
  app/services/menu_service.py      # 业务逻辑（树构建、权限过滤、绑定管理）
  app/api/v1/menus.py               # 路由定义

前端：
  src/types/menu.ts                 # TypeScript 类型
  src/services/menu.ts              # API 请求封装
  src/pages/menu/index.tsx           # 菜单管理页面
  src/pages/menu/components/MenuForm.tsx  # 菜单编辑表单（图标选择器/权限多选）
  src/router/dynamic_routes.tsx      # 动态路由生成
  src/components/IconPicker.tsx      # 图标选择器共享组件
```
