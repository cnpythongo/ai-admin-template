# 系统配置模块详细需求

> 对应 PDD 第 4.6 节、实施计划 P2-C。本模块与部门管理、权限管理可并行开发。

---

## 1. 功能描述

提供全局系统参数的统一管理，支持多类型配置项，包含：

- 按分组管理配置项（如"基本设置"、"安全设置"、"邮件设置"、"日志设置"）
- 每个分组下包含若干配置项：配置键（唯一标识）、配置名称、配置值、值类型、备注
- 配置列表以分组-配置项两级结构展示
- 编辑配置时根据值类型动态渲染对应表单控件
- 修改配置后立即生效（写入数据库并刷新 Redis 缓存）
- 支持手动刷新全部配置缓存
- 敏感配置项仅超级管理员可见可编辑

---

## 2. 输入输出

### 2.1 后端 API

#### GET `/api/v1/system-configs/groups`

| 字段 | 说明 |
|------|------|
| **描述** | 获取所有配置分组 |
| **权限** | `system:config:list` |
| **响应** | `[{ name: "基本设置", code: "basic" }, { name: "安全设置", code: "security" }]` |

#### GET `/api/v1/system-configs?group={code}`

| 字段 | 说明 |
|------|------|
| **描述** | 按分组获取配置项列表 |
| **权限** | `system:config:list` |
| **响应** | 配置项数组（敏感字段值统一脱敏为 `******`） |

**ConfigItem 响应结构：**

```json
{
  "id": 1,
  "key": "site_name",
  "name": "站点名称",
  "value": "AI Admin",
  "value_type": "string",
  "group": "basic",
  "is_sensitive": false,
  "remark": "系统前端显示的站点名称"
}
```

#### PUT `/api/v1/system-configs/{id}`

| 字段 | 说明 |
|------|------|
| **描述** | 更新配置项值 |
| **权限** | `system:config:update`（敏感配置项需超级管理员权限） |
| **请求体** | `{ value: any }` |
| **逻辑** | 1. 校验 `value` 与 `value_type` 匹配 2. 敏感字段加密存储 3. 写入数据库 4. 删除 Redis 缓存 `config:{key}` |
| **响应** | 200，返回更新后的配置项（敏感值仍脱敏） |

#### POST `/api/v1/system-configs/refresh-cache`

| 字段 | 说明 |
|------|------|
| **描述** | 手动刷新全部配置缓存 |
| **权限** | `system:config:update` |
| **逻辑** | 遍历所有配置项，逐个写入 Redis（或删除全部缓存键后等待下次请求回查数据库） |

### 2.2 前端 Props / 事件

#### SystemConfigPage

| 组件 | 说明 |
|------|------|
| **ConfigGroupMenu** | 左侧分组导航菜单，`Menu` 组件，选中高亮 |
| **ConfigList** | 右侧配置项列表，`Table` 组件 |
| **ConfigForm** | 编辑配置项弹窗，根据 `value_type` 动态渲染表单控件 |

**ConfigForm 值类型 → 控件映射：**

| value_type | 控件 | 说明 |
|------------|------|------|
| `string` | `Input` | 普通文本输入框 |
| `integer` | `InputNumber` | 数字输入框 |
| `boolean` | `Switch` | 开关切换 |
| `json` | `TextArea` | 多行文本（JSON 格式），带 JSON 语法校验 |
| `select` | `Select` | 下拉选择，通过 `options` 字段定义可选值 |

**敏感配置项编辑交互：**

- 列表中展示脱敏文本 `******`
- 编辑弹窗中显示为禁用态 Input，旁边有一个"修改"按钮
- 点击"修改"后 Input 变为可编辑状态，用户填写新值
- 提交时如果 Input 为空或未修改，不更新该字段

---

## 3. 依赖接口

| 依赖 | 用途 | 备注 |
|------|------|------|
| Redis | 配置缓存（热加载） | 需 `db/redis.py` 连接池支持 |
| 权限校验 | 敏感配置项访问控制 | 超级管理员 vs 普通管理员差异化 |
| 操作日志 | 配置修改需记录日志 | P5 阶段接入 |

**内部依赖路径：**

```
SystemConfig Service ──→ SystemConfig 模型
                    ──→ Redis 缓存（config:{key}）
                    ──→ 权限校验（区分敏感配置）
```

---

## 4. 边缘情况

1. **缓存穿透**：系统启动时 Redis 若未就绪，读取配置应回退到数据库查询（`get from db if cache miss` 策略）。写入时"先写数据库，再删缓存"，确保最终一致性。
2. **值类型校验失败**：编辑配置时前端需做类型校验（如 integer 字段输入非数字时即时提示），后端同样做二次校验。JSON 类型需做 JSON.parse 校验，失败时返回 422 + 具体错误位置。
3. **枚举值越界**：`select` 类型的配置项提交的值不在 `options` 定义范围内时，后端应拒绝并返回 400。
4. **并发写冲突**：两个管理员同时编辑同一配置项，后者覆盖前者（最终写入覆盖）。可在前端做"编辑时锁定"提示，但后端不做乐观锁（配置项冲突代价低）。
5. **缓存与数据库不一致**：手动触发"刷新缓存"时，若 Redis 不可用应给出明确错误提示，但不影响数据库中的配置值。

---

## 5. 建议文件路径

```
后端：
  app/models/system_config.py              # SystemConfig 模型
  app/schemas/system_config.py             # Pydantic Schema
  app/services/system_config_service.py    # 业务逻辑（缓存读写、加密脱敏、类型校验）
  app/api/v1/system_configs.py             # 路由定义

前端：
  src/types/system_config.ts               # TypeScript 类型
  src/services/system_config.ts            # API 请求封装
  src/pages/system-config/index.tsx         # 系统配置页面
  src/pages/system-config/components/ConfigGroupForm.tsx  # 分组编辑表单
  src/pages/system-config/components/ConfigForm.tsx       # 配置项编辑表单（动态控件）
```
