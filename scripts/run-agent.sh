#!/bin/bash
# 子智能体启动脚本
# 用法: bash scripts/run-agent.sh <agent-name> [module-doc-path]
#
# 环境适配：
#   - CLAUDE_CODE=true  : 使用 Claude Code CLI (默认)
#   - 其他情况 (Trae)    : 输出完整 prompt 到临时文件，便于复制到新会话
#
# 示例:
#   bash scripts/run-agent.sh department-agent memory-bank/04-modules/module-department.md
#   bash scripts/run-agent.sh backend-init-agent            # P0-1 脚手架
#   bash scripts/run-agent.sh frontend-test-agent           # P6 前端测试

set -e

if [ $# -lt 1 ]; then
  echo "用法: $0 <agent-name> [module-doc-path]"
  echo "示例:"
  echo "  $0 department-agent memory-bank/04-modules/module-department.md"
  echo "  $0 backend-init-agent"
  echo "  $0 frontend-test-agent"
  exit 1
fi

AGENT_NAME="$1"
MODULE_DOC="${2:-}"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENT_FILE="$PROJECT_ROOT/agents/${AGENT_NAME}.md"

# 验证 agent 定义文件是否存在
if [ ! -f "$AGENT_FILE" ]; then
  echo "错误：找不到 agent 定义文件 $AGENT_FILE"
  echo "可用 agents:"
  ls -1 "$PROJECT_ROOT/agents/" | sed 's/\.md$//' | sed 's/^/  - /'
  exit 1
fi

# 组装完整指令
AGENT_INSTRUCTION=$(cat "$AGENT_FILE")
PROMPT="${AGENT_INSTRUCTION}"

# 如果传入了模块文档，追加到指令末尾
if [ -n "$MODULE_DOC" ]; then
  MODULE_PATH="$PROJECT_ROOT/$MODULE_DOC"
  if [ ! -f "$MODULE_PATH" ]; then
    echo "错误：找不到模块文档 $MODULE_DOC"
    exit 1
  fi
  MODULE_CONTENT=$(cat "$MODULE_PATH")
  PROMPT="${PROMPT}\n\n## 需求文档\n\n${MODULE_CONTENT}"
fi

if [ "${CLAUDE_CODE}" = "true" ]; then
  # ============================================
  # 模式 1: Claude Code CLI（macOS Terminal）
  # ============================================
  CMD="cd $PROJECT_ROOT && claude --resume -p '$(echo "$PROMPT" | sed "s/'/'\\\\''/g")'"

  osascript <<EOF
tell application "Terminal"
    activate
    tell application "System Events" to keystroke "t" using command down
    delay 0.5
    do script "${CMD}" in front window
end tell
EOF

  echo "已启动子智能体: ${AGENT_NAME} (Claude Code 新终端窗口)"
else
  # ============================================
  # 模式 2: Trae IDE / 通用模式
  # 将完整指令保存到临时文件
  # ============================================
  OUTPUT_FILE="${PROJECT_ROOT}/.agent-task-${AGENT_NAME}.md"

  cat > "$OUTPUT_FILE" <<- PROMPT_EOF
# 子智能体任务: ${AGENT_NAME}

> 由 \`scripts/run-agent.sh\` 在 $(date '+%Y-%m-%d %H:%M:%S') 生成

---

${PROMPT}

---

## 工作说明

请在一个**新的 AI 会话**中完成上述任务。完成后更新 \`memory-bank/05-progress.md\`。
PROMPT_EOF

  echo ""
  echo "================================================"
  echo " 子智能体: ${AGENT_NAME}"
  echo " 模式    : Trae IDE（指令已保存到文件）"
  echo "================================================"
  echo ""
  echo "请在新会话中粘贴以下内容："
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  cat "$OUTPUT_FILE"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "提示文件已保存到: ${OUTPUT_FILE}"
  echo "也可直接复制上面的内容到新 Trae 会话中使用。"
fi
