# 操作日志模块详细需求

> 对应 PDD 第 4.7 节、实施计划 P5。本模块依赖所有其他模块完成，是最后实现的业务模块。

---

## 1. 功能描述

自动记录用户的关键操作行为，提供多维度的日志检索与审计能力，包含：

- 分页展示操作日志列表，多维度筛选（操作用户、操作模块、操作类型、操作时间范围）
- 查看单条日志的完整详情（操作人、IP、模块、类型、描述、时间、请求参数、结果）
- 操作人可点击跳转至对应用户详情
- 支持配置日志保留天数（默认 90 天），定时任务自动清理过期日志
- 自动记录所有系统资源的增删改操作（用户/部门/角色/权限/菜单/系统配置）及用户登录行为
- 日志仅允许查询，不允许修改或删除（除自动清理外）

---

## 2. 输入输出

### 2.1 后端 API

#### GET `/api/v1/operation-logs`

| 字段 | 说明 |
|------|------|
| **描述** | 分页查询操作日志 |
| **权限** | `system:operation_log:list` |
| **请求参数** | `?page=1&page_size=10&user_id=1&module=user\|department\|role\|permission\|menu\|system_config&action=create\|update\|delete\|login\|other&status=success\|fail&start_date=2025-01-01&end_date=2025-01-31` |
| **排序** | 默认按 `created_at DESC` 排列 |

**OperationLogResponse 结构：**

```json
{
  "id": 1,
  "user_id": 1,
  "username": "admin",
  "module": "user",
  "action": "create",
  "target_id": "2",
  "target_name": "zhangsan",
  "description": "创建了用户 zhangsan",
  "ip_address": "192.168.1.100",
  "request_params": "{\"username\":\"zhangsan\",\"email\":\"zhangsan@example.com\",\"role_ids\":[2]}",
  "status": "success",
  "created_at": "2025-01-15T10:30:00Z"
}
```

#### GET `/api/v1/operation-logs/{id}`

| 字段 | 说明 |
|------|------|
| **描述** | 获取日志详情 |
| **权限** | `system:operation_log:list` |
| **响应** | 单条日志完整信息 |

#### GET `/api/v1/operation-logs/modules`

| 字段 | 说明 |
|------|------|
| **描述** | 获取所有操作模块名称列表 |
| **权限** | `system:operation_log:list` |
| **响应** | 字符串数组 |

#### GET `/api/v1/operation-logs/actions`

| 字段 | 说明 |
|------|------|
| **描述** | 获取操作类型列表，可按模块筛选 |
| **权限** | `system:operation_log:list` |
| **请求参数** | `?module=user`（可选） |
| **响应** | 字符串数组 |

**注意：** 操作日志没有 CREATE / UPDATE / DELETE 接口，仅提供查询。

### 2.2 日志记录时机（后端内部调用）

日志记录不是由前端调用，而是在后端 Service 层通过统一方式自动触发：

```python
# 调用方式示例（P5 阶段在相关 Service 中注入）
from app.services.operation_log_service import OperationLogService

# 在 Service 方法的 CRUD 操作成功后调用
await OperationLogService.log_action(
    db=db,
    user_id=current_user.id,
    module="user",          # 固定枚举：user|department|role|permission|menu|system_config
    action="create",        # 枚举：create|update|delete|login|other
    target_id=str(user.id),
    target_name=user.username,
    description=f"创建了用户 {user.username}",
    ip_address=request.client.host,
    request_params=json.dumps(create_data, ensure_ascii=False),
    status="success"
)
```

**记录点覆盖：**

| 模块 | 记录点 |
|------|--------|
| 用户管理 | 创建/编辑/删除用户、启用/禁用、重置密码、角色/部门分配 |
| 部门管理 | 创建/编辑/删除部门 |
| 角色管理 | 创建/编辑/删除角色、权限分配 |
| 权限管理 | 创建/编辑/删除权限 |
| 菜单管理 | 创建/编辑/删除菜单、菜单-权限绑定 |
| 系统配置 | 创建/编辑/删除配置项、修改配置值、刷新缓存 |
| 认证 | 登录成功、登录失败 |

### 2.3 前端 Props / 事件

#### OperationLogPage

| 子组件 | 说明 |
|--------|------|
| **LogSearchForm** | 筛选栏：用户 Select（搜索模式）、模块 Select、操作类型 Select、日期范围 DatePicker.RangePicker、查询/重置按钮 |
| **LogTable** | 日志分页表格，列：操作人（可点击跳转）、模块、操作类型、操作描述、IP、操作时间、状态（成功/失败标签） |
| **LogDetailDrawer** | 日志详情抽屉：完整展示字段 + 请求参数 JSON 格式化展示 |

#### LogTable

| Prop | 类型 | 说明 |
|------|------|------|
| `dataSource` | `OperationLog[]` | 分页日志数据 |
| `loading` | `boolean` | 加载状态 |
| `pagination` | `{ current, pageSize, total }` | 分页信息 |
| `onViewDetail` | `(record: OperationLog) => void` | 查看详情回调 |
| `onUserClick` | `(userId: number) => void` | 操作人点击跳转回调 |

#### LogDetailDrawer

| Prop | 类型 | 说明 |
|------|------|------|
| `visible` | `boolean` | 抽屉可见性 |
| `record` | `OperationLog \| null` | 日志数据 |
| `onClose` | `() => void` | 关闭回调 |

---

## 3. 依赖接口

| 依赖 | 用途 | 备注 |
|------|------|------|
| [用户管理](./module-user.md) | 操作人点击跳转用户详情 | 前端路由联动 |
| [部门管理](./module-department.md) | 日志记录点 | 需在部门 Service 注入记录代码 |
| [角色管理](./module-role.md) | 日志记录点 | 需在角色 Service 注入记录代码 |
| [权限管理](./module-permission.md) | 日志记录点 | 需在权限 Service 注入记录代码 |
| [菜单管理](./module-menu.md) | 日志记录点 | 需在菜单 Service 注入记录代码 |
| [系统配置](./module-system-config.md) | 日志记录点 | 需在配置 Service 注入记录代码 |
| auth_service | 登录日志记录点 | 登录成功/失败时记录 |
| Redis | 异步日志队列 | 业务接口 LPUSH，Worker BRPOP |

---

## 4. 边缘情况

1. **异步写入可靠性**：日志采用 Redis 列表作为异步队列，Worker 批量消费。如果 Worker 崩溃，队列中的日志会堆积在 Redis 中，重启后继续消费。如果 Redis 宕机，日志丢失（可接受，业务操作本身不受影响）。在日志重要性评估上：不影响主业务流程，允许最多丢失数秒内的日志。
2. **队列积压降级**：Redis 队列长度应设置上限（如 10000 条），超过上限时丢弃最旧的日志（`LTRIM`），避免日志队列耗尽 Redis 内存。
3. **请求参数脱敏**：记录 `request_params` 时，敏感字段（如 `password`、`old_password`、`new_password`）需要在记录前过滤/替换为 `"******"`，避免明文密码写入日志表。
4. **日志清理的边界**：定时清理脚本删除过期日志时，使用 `DELETE FROM operation_logs WHERE created_at < NOW() - INTERVAL {days} DAY`，每次清理限制批量大小（如每次 1000 条），避免长事务锁表。可在低峰时段执行。
5. **联合索引设计**：操作日志表的查询模式是 `WHERE user_id=? AND module=? AND action=? AND created_at BETWEEN ? AND ?`，应建立联合索引 `(module, action, created_at)` 和 `(user_id, created_at)`，避免全表扫描。
6. **操作人用户已删除**：如果操作日志中的 `user_id` 对应的用户已被逻辑删除（`is_deleted=true`），前端点击操作人跳转时，应跳转到用户详情页并提示"该用户已被删除"，而非 404。

---

## 5. 建议文件路径

```
后端：
  app/models/operation_log.py              # OperationLog 模型
  app/services/operation_log_service.py    # 日志记录业务逻辑（log_action、分页查询、清理）
  app/services/log_worker.py               # 后台异步消费 worker（asyncio 任务）
  app/api/v1/operation_logs.py             # 路由定义（仅 GET 查询）
  app/tasks/__init__.py                    # 定时任务模块
  app/tasks/log_cleanup.py                 # 日志清理定时任务

前端：
  src/types/operation_log.ts               # TypeScript 类型
  src/services/operation_log.ts            # API 请求封装
  src/pages/operation-log/index.tsx         # 操作日志页面
  src/pages/operation-log/components/LogDetailDrawer.tsx  # 日志详情抽屉
```
