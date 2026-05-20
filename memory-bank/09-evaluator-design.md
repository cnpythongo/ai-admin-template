# Evaluator（评估者）设计方案

> 对应 Harness Engineering 三角色中的 **Evaluator**，负责验证 Generator 产出的代码质量，
> 并向 Planner 反馈验收结果，形成开发闭环。

---

## 1. 设计目标

在 Generator（Claude Code 子智能体）完成代码生成后，Evaluator 自动执行以下检查：

| 检查维度 | 目标 | 失败影响 |
|---------|------|---------|
| **API 接口完整性** | 验证 module-*.md 中定义的每个 API 端点都已实现且签名匹配 | 前端无法联调 |
| **权限校验正确性** | 验证每个 API 端点都绑定了正确的 `require_permissions` 或登录依赖 | 安全隐患 |
| **静态代码质量** | 通过 ruff 检查，确保代码风格一致、无语法错误 | 代码可维护性差 |
| **模块隔离性** | 验证 Generator 未修改其他模块的文件 | 架构污染 |

---

## 2. 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                     evaluator.py                            │
│                                                             │
│  ┌─────────────────┐   ┌──────────────┐   ┌──────────────┐ │
│  │  Module Doc      │   │  Source Code  │   │  Static      │ │
│  │  Parser          │   │  Scanner      │   │  Analyzer     │ │
│  │  (markdown->API  │   │  (Python AST) │   │  (ruff)       │ │
│  │   endpoint list) │   │               │   │              │ │
│  └────────┬────────┘   └──────┬───────┘   └──────┬───────┘ │
│           │                   │                   │          │
│           ▼                   ▼                   ▼          │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                 Report Generator                        │ │
│  │  输出结构化的 Pass/Fail 报告 + 失败详情                  │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 2.1 核心模块说明

#### Module Doc Parser

- 读取 `memory-bank/04-modules/*.md`（除 `module-dashboard.md`）
- 通过正则匹配提取 API 端点定义：
  - HTTP 方法（GET/POST/PUT/DELETE）
  - 路由路径
  - 权限标识
  - 请求/响应结构约束
- 输出：`list[ExpectedEndpoint]`

#### Source Code Scanner

- 读取 `backend/app/api/v1/*.py`
- 使用 Python AST 解析每个路由文件：
  - 提取 `router = APIRouter(prefix=...)` 的前缀
  - 提取 `@router.get/post/put/delete(...)` 装饰器的路径和参数
  - 查找 `Depends(require_permissions(...))` 调用，提取权限标识
- 输出：`list[ActualEndpoint]`

#### Static Analyzer

- 调用 `uv run ruff check app/`（针对 `backend/app/` 目录）
- 解析输出结果：错误文件列表、错误类型、行号、描述
- 统计：错误总数、按严重级别/文件分布

#### Report Generator

- 对比 Expected vs Actual，生成差异报告
- 为每个检查项输出：
  - ✅ Pass / ❌ Fail / ⚠️ Warning
  - 失败时附带详细信息（如"预期有 POST /api/v1/departments，但未找到"）
- 汇总统计：通过率、未实现端点数、ruff 错误数

---

## 3. 数据模型

### 3.1 ExpectedEndpoint（从模块文档解析）

```python
@dataclass
class ExpectedEndpoint:
    module: str           # 所属模块名，如 "department"
    method: str           # HTTP 方法：GET / POST / PUT / DELETE
    path: str             # 路由路径，如 "/api/v1/departments/tree"
    permission: str | None  # 权限标识，如 "system:department:list"
    summary: str          # API 描述
```

### 3.2 ActualEndpoint（从代码扫描）

```python
@dataclass
class ActualEndpoint:
    file: str             # 源文件路径
    method: str           # HTTP 方法
    path: str             # 完整路由路径（prefix + decorator path）
    permissions: list[str]  # 权限标识列表
    summary: str          # summary 参数（如果存在）
```

### 3.3 CheckResult（检查结果）

```python
@dataclass
class CheckResult:
    category: str         # "api" / "ruff" / "isolation"
    status: str           # "pass" / "fail" / "warning"
    item: str             # 检查项名称
    detail: str           # 详细信息
```

---

## 4. 工作流程

```
Step 1: 解析模块文档 -> Expected API 列表
    |
Step 2: 扫描源文件 -> Actual API 列表
    |
Step 3: 对比 Expected vs Actual
    |  +- 每个 Expected 端点：在 Actual 中找到匹配 -> ✅ Pass
    |  |                      未找到匹配 -> ❌ Fail
    |  +- 每个 Actual 端点：Extra（文档未定义但已实现）-> ⚠️ Warning
    |
Step 4: 运行 ruff check
    |  +- 零错误 -> ✅ Pass
    |  +- 有错误 -> ❌ Fail（附错误详情）
    |
Step 5: 生成报告
       +- 输出到终端（简要）
       +- 保存到文件（可选）
```

---

## 5. 使用方式

### 5.1 命令行执行

```bash
# 在项目根目录执行
cd /Users/lyhapple/workspace/mycompany/ai-admin
uv run python scripts/evaluator.py

# 指定输出文件
uv run python scripts/evaluator.py --output evaluator-report.md

# 仅检查某个模块
uv run python scripts/evaluator.py --module department
```

### 5.2 集成到开发流程

Generator Agent 完成代码后，在主智能体的调度脚本中自动调用：

```bash
# 在 run-agent.sh 中，子智能体完成后追加
if uv run python scripts/evaluator.py --module $MODULE; then
    echo "✅ $MODULE 模块验收通过"
else
    echo "❌ $MODULE 模块验收未通过，需重新生成"
    exit 1
fi
```

---

## 6. 验收标准

| 级别 | 通过条件 |
|------|---------|
| **P0（必须通过）** | API 端点 100% 实现、ruff 零错误、未修改其他模块文件 |
| **P1（建议通过）** | API 端点 100% 实现、ruff 零错误 |
| **P2（最低要求）** | 核心 CRUD 端点实现、ruff 错误数 <= 3 |

---

## 7. 限制与注意事项

1. **文档与代码的同步问题**：Parser 依赖模块文档的格式一致性。如果文档格式不规范，可能导致错误解析。需要维护文档格式的统一。
2. **动态路由匹配**：代码中的路径可能包含参数（如 `{id}`），需要与文档中的路径（如 `{id}`）做归一化匹配。
3. **权限类型的区分**：有些端点使用 `require_permissions`，有些使用 `get_current_user`（登录即可），有些两者都不用，Parser 需要区分这些情况。
4. **ruff 依赖**：确保项目依赖中已安装 `ruff`。如果未安装，静默跳过 ruff 检查并给出 Warning。
5. **前端代码暂不纳入**：当前 Evaluator 仅检查后端代码。前端代码的检查（TypeScript 类型正确性、组件是否存在等）可以后续补充。

---

## 8. 后续扩展

| 功能 | 优先级 | 说明 |
|------|--------|------|
| 前端文件完整性检查 | P3 | 检查模块文档中定义的前端组件文件是否存在 |
| API 响应结构检查 | P3 | 验证实际响应字段是否与文档定义的 JSON 结构匹配 |
| mypy 类型检查 | P3 | 集成 mypy 静态类型检查 |
| 自动修复建议 | P4 | 对常见问题（如缺少权限、缺少路由）给出代码修复建议 |
| pytest 集成 | P4 | 自动运行模块相关测试并报告覆盖率 |
