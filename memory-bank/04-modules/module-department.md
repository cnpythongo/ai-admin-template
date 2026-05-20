# 部门管理模块详细需求

> 对应 PDD 第 4.2 节、实施计划 P2-A。本模块与权限管理、系统配置模块可并行开发。

---

## 1. 功能描述

提供多级树形部门结构的增删改查，支持部门与用户的关联管理，包含：

- 以树形结构展示所有部门（展开/折叠）
- 新增部门（指定名称、上级部门、排序号、负责人、状态）
- 编辑部门（修改基本信息）
- 删除部门（级联删除保护：有子部门或关联用户时禁止删除）
- 查看部门下的用户列表
- 同级部门排序（手动输入排序号调整）

---

## 2. 输入输出

### 2.1 后端 API

#### GET `/api/v1/departments/tree`

| 字段 | 说明 |
|------|------|
| **描述** | 获取部门树形结构 |
| **权限** | `system:department:list` |
| **请求参数** | 无 |
| **响应** | 见下方 `DepartmentTree` 结构 |
| **边缘处理** | 部门表为空时返回空数组 `[]` |

**DepartmentTree 结构：**

```json
{
  "id": 1,
  "name": "总公司",
  "parent_id": null,
  "sort": 1,
  "leader": "张三",
  "status": 1,
  "children": [
    {
      "id": 2,
      "name": "技术部",
      "parent_id": 1,
      "sort": 1,
      "leader": "李四",
      "status": 1,
      "children": []
    }
  ]
}
```

#### POST `/api/v1/departments`

| 字段 | 说明 |
|------|------|
| **描述** | 新增部门 |
| **权限** | `system:department:create` |
| **请求体** | `{ name: string, parent_id: number \| null, sort: number, leader?: string, status: 0 \| 1 }` |
| **响应** | 201，返回新创建的部门对象 |
| **校验** | name 必填且同父节点下唯一；parent_id 不存在或为自身时报 422 |

#### PUT `/api/v1/departments/{id}`

| 字段 | 说明 |
|------|------|
| **描述** | 编辑部门信息 |
| **权限** | `system:department:update` |
| **请求体** | `{ name?: string, parent_id?: number \| null, sort?: number, leader?: string, status?: 0 \| 1 }` |
| **校验** | parent_id 变更时必须做环检测（不能指向自身或子孙节点） |

#### DELETE `/api/v1/departments/{id}`

| 字段 | 说明 |
|------|------|
| **描述** | 删除部门 |
| **权限** | `system:department:delete` |
| **响应** | 204（成功）或 409（有子部门/关联用户） |
| **校验** | 有子部门（children 非空）→ 409 "请先删除子部门"；有用户关联 → 409 "该部门下还有 {n} 名用户，请先移除" |

#### GET `/api/v1/departments/{department_id}/users`

| 字段 | 说明 |
|------|------|
| **描述** | 查询部门下的用户列表 |
| **权限** | `system:department:list` |
| **响应** | 用户简要信息数组（id, username, email, status） |

### 2.2 前端 Props / 事件

#### DepartmentTree

| Prop | 类型 | 说明 |
|------|------|------|
| `dataSource` | `Department[]` | 树形部门数据 |
| `loading` | `boolean` | 加载状态 |
| `onEdit` | `(record: Department) => void` | 编辑回调 |
| `onDelete` | `(id: number) => void` | 删除回调 |
| `onViewUsers` | `(record: Department) => void` | 查看部门成员回调 |

#### DepartmentForm（Modal）

| Prop | 类型 | 说明 |
|------|------|------|
| `visible` | `boolean` | 弹窗可见性 |
| `record` | `Department \| null` | 编辑时传入当前行数据；新增时为 null |
| `parentTree` | `Department[]` | 上级部门树选项（TreeSelect 数据源） |
| `onSubmit` | `(values: DepartmentFormValues) => Promise<void>` | 提交流程 |
| `onCancel` | `() => void` | 取消关闭 |

#### DepartmentUsers（Drawer）

| Prop | 类型 | 说明 |
|------|------|------|
| `visible` | `boolean` | 抽屉可见性 |
| `department` | `Department` | 当前部门信息 |
| `onClose` | `() => void` | 关闭回调 |

---

## 3. 依赖接口

| 依赖 | 用途 | 备注 |
|------|------|------|
| [用户管理](./module-user.md) | 部门用户列表需要查询 User 表 | 仅查询关联，开发时序上可先 Mock |
| 操作日志 | 增删改操作需记录日志 | 在 P5 阶段接入 |

**内部依赖路径：**

```
部门 Service ──→ Department 模型
            ──→ 权限校验 require_permissions
            ──→ （可选）查询用户关联
```

---

## 4. 边缘情况

1. **环检测**：编辑部门时将 `parent_id` 改为自身或其子孙节点，后端必须做环检测（DFS 从目标节点遍历所有子节点），检测到环时返回 422 + 明确错误描述。
2. **同层同名**：同一 `parent_id` 下的部门 name 必须唯一。新增/编辑时需校验 `(parent_id, name)` 组合唯一性。
3. **根部门保护**：若系统预设了根部门（如"总公司"），删除根部门时需特殊提示，或直接禁止删除根部门（后台控制 `parent_id IS NULL` 且无其他同级节点时不可删除）。
4. **排序号重复**：同级部门 `sort` 值允许重复（重复时按 id 或 create_time 二次排序），但建议在 UI 层提供"一键重排"功能重新生成连续的 sort 值。

---

## 5. 建议文件路径

```
后端：
  app/models/department.py           # Department 模型
  app/schemas/department.py          # Pydantic Schema
  app/services/department_service.py # 业务逻辑（含环检测、树构建、级联校验）
  app/api/v1/departments.py          # 路由定义

前端：
  src/types/department.ts            # TypeScript 类型
  src/services/department.ts         # API 请求封装
  src/pages/department/index.tsx     # 部门管理页面
  src/pages/department/components/DepartmentForm.tsx   # 部门编辑表单弹窗
  src/pages/department/components/DepartmentUsers.tsx  # 部门成员抽屉
```
