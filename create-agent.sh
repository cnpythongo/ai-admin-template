#!/bin/bash
# 批量创建 Subagent 配置文件

# 进入 memory-bank/04-modules 目录，避免 glob 路径问题
cd memory-bank/04-modules || { echo "错误：找不到 04-modules 目录"; exit 1; }

# 收集所有模块文件
module_files=( module-*.md )
if [ ! -e "${module_files[0]}" ]; then
  echo "错误：没有找到任何 module-*.md 文件。"
  exit 1
fi

# 遍历每个模块文件
for module_file in "${module_files[@]}"; do
  # 去除 .md 后缀
  module_name="${module_file%.md}"
  # 去掉前缀 "module-"
  agent_name="${module_name#module-}-agent"

  # 代理文件路径
  agent_file="../../agents/${agent_name}.md"

  # 生成智能体配置内容（注意：反引号保持转义）
  cat > "$agent_file" <<EOF
你是一名专门负责「${module_name}」的开发智能体。

## 核心任务
严格按照 memory-bank/04-modules/module-${module_name}.md 中定义的需求，完成该模块的代码开发。

## 必须遵守的规则
1. 首先读取 memory-bank/03-architecture.md 了解项目整体架构。
2. 开发后端代码时，必须遵守 memory-bank/06-backend-standards.md。
3. 开发前端代码时，必须遵守 memory-bank/07-frontend-standards.md。
4. 代码文件必须存放在模块文档指定的路径下。
5. 完成后，在 memory-bank/05-progress.md 中将该模块的状态更新为“完成”，并附上关键函数签名。
6. 绝不修改任何其他模块的文件。

## 工作流程
- 开始前，简要复述你理解的需求。
- 逐步生成代码文件。
- 完成后，更新进度并输出摘要。
EOF

  echo "已创建智能体: ${agent_name}"
done

cd ../..  # 返回项目根目录