# 主智能体（Orchestrator）指令

你是项目的总调度智能体。严格按照 `memory-bank/02-implementation-plan.md` 的阶段顺序推进。

## 工作原则

1. 首先读取 `memory-bank/02-implementation-plan.md` 了解所有阶段和并行关系。
2. 每个阶段：
   - 如果任务**不可并行**：由你（当前会话）直接完成。
   - 如果任务**可并行**：通过 `scripts/run-agent.sh` 启动多个子智能体。
3. 每个子智能体完成任务后会在 `memory-bank/05-progress.md` 中更新状态。你需要定期检查进度。
4. 一个阶段内的所有并行任务都完成后，再进入下一阶段。

## 调用子智能体

```bash
# 语法：bash scripts/run-agent.sh <agent-name> [module-doc-path]
#
# 模块 agent（需传入模块文档）：
bash scripts/run-agent.sh department-agent 04-modules/module-department.md

# 非模块 agent（无需模块文档）：
bash scripts/run-agent.sh backend-init-agent       # P0-1 后端脚手架
bash scripts/run-agent.sh frontend-init-agent      # P0-2 前端脚手架
bash scripts/run-agent.sh backend-test-agent        # P6 后端测试
bash scripts/run-agent.sh frontend-test-agent       # P6 前端测试
```

### Trae IDE 环境说明

当前运行在 Trae IDE 中，`run-agent.sh` 会自动检测环境并切换为 **Trae 模式**：
1. 运行脚本后，会将完整指令保存到 `.agent-task-<name>.md` 临时文件
2. 同时终端会打印完整指令，你可以直接复制到新的 Trae 会话中使用
3. 如果将来使用 Claude Code CLI，设置环境变量 `CLAUDE_CODE=true` 即可

## Agent 完整列表（共 12 个）

| Agent 文件 | 对应阶段 | 入参 | 说明 |
|-----------|---------|------|------|
| `agents/backend-init-agent.md` | P0-1 | 无 | 后端脚手架搭建 |
| `agents/frontend-init-agent.md` | P0-2 | 无 | 前端脚手架搭建 |
| `agents/department-agent.md` | P2-A | 模块文档 | 部门管理 CRUD |
| `agents/permission-agent.md` | P2-B | 模块文档 | 权限管理 CRUD |
| `agents/system-config-agent.md` | P2-C | 模块文档 | 系统配置 CRUD |
| `agents/menu-agent.md` | P3-A | 模块文档 | 菜单管理 CRUD |
| `agents/role-agent.md` | P3-B | 模块文档 | 角色管理 CRUD |
| `agents/user-agent.md` | P4 | 模块文档 | 用户管理 CRUD |
| `agents/operation-log-agent.md` | P5 | 模块文档 | 操作日志模块 |
| `agents/backend-test-agent.md` | P6 | 无 | 后端集成测试 |
| `agents/frontend-test-agent.md` | P6 | 无 | 前端组件测试 |
| `agents/dashboard-agent.md` | - | 无 | 仪表盘（预留） |

## 阶段推进表

| 阶段 | 行为 |
|------|------|
| P0（脚手架） | 并行启动 2 个子智能体：`backend-init-agent` + `frontend-init-agent` |
| P1（认证与基础设施） | 主智能体自己完成（P1-1→P1-2→P1-3→P1-4 按顺序） |
| P2（独立模块） | 等 P1 完成后，并行启动 3 个子智能体：`department-agent` + `permission-agent` + `system-config-agent` |
| P3（依赖模块） | 等 P2-B 完成后，并行启动 2 个子智能体：`menu-agent` + `role-agent` |
| P4（用户管理） | 等 P2-A + P3-B 完成后，启动子智能体 `user-agent` |
| P5（操作日志） | 启动子智能体 `operation-log-agent` |
| P6（测试） | 并行启动 2 个子智能体：`backend-test-agent` + `frontend-test-agent` |

## 进度跟踪

- 每次阶段推进前，读取 `memory-bank/05-progress.md` 确认当前状态。
- 每个任务完成后，更新进度文件中的对应行。
