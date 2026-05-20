# 前端开发标准

## 技术栈

- React 18+, TypeScript, Vite
- UI：Ant Design 5.x
- 状态管理：Zustand
- 路由：React Router v6
- HTTP：axios（统一拦截器）
- 包管理：pnpm
- 测试：Vitest + React Testing Library

## 目录约定

frontend/
├── public/
├── src/
│   ├── assets/        # 静态资源
│   ├── components/    # 共享组件
│   ├── pages/         # 页面组件
│   ├── hooks/         # 自定义 Hook
│   ├── services/      # API 请求层（封装 axios）
│   ├── stores/        # 状态管理（Zustand）：auth.ts（认证）、tabs.ts（多标签页导航）
│   ├── types/         # TypeScript 类型定义
│   ├── utils/         # 工具函数
│   ├── App.tsx
│   └── main.tsx
├── package.json
├── tsconfig.json
├── vite.config.ts
└── .env.example

## 编码规范

- 组件：函数式组件 + Hooks，禁止 class 组件
- 类型安全：严禁使用 any，所有 props、API 响应必须有明确类型
- 异步处理：所有异步请求必须处理 loading、error 状态，使用 Ant Design 的 Spin、message.error 等给予反馈
- 权限：路由守卫实现页面级权限，按钮级权限封装为自定义组件或函数
- 样式：优先使用 Ant Design 内置样式，定制主题用 ConfigProvider，避免滥用行内样式
- 环境变量：API 地址等配置从 .env 读取，禁止硬编码
- **布局规范：**
  - `html`、`body`、`#root` 必须设置 `height: 100%; width: 100%; overflow: hidden;`，全局 `* { margin: 0; padding: 0; box-sizing: border-box; }`
  - 主体框架 `<Layout>` 应使用 `height: 100vh` 填满视口，Content 区域设置 `flex: 1; overflow: auto; background: #fff;`，内部滚动由子页面自行控制
  - 所有列表页根容器统一使用 `<div style={{ padding: 24, background: '#fff', minHeight: '100%' }}>`，确保背景白色且撑满内容区
- **列表页规范：模块列表页禁止使用 Card 组件作为外层容器包裹；如需页面标题，使用 `Typography.Title level={4}`，搜索和操作按钮区域直接放在标题下方**
- **多标签页导航规范：应用采用 SPA 标签页（Tab）导航模式，使用 Zustand 状态管理（`stores/tabs.ts`）维护打开的标签页列表：**
  - 点击侧边栏菜单项时创建新标签页并导航，标签页标题取自菜单名称
  - 点击标签页切换内容，点击关闭按钮移除标签页并自动跳转到相邻标签页
  - `HomePage`（`pages/home/index.tsx`）在 Header 下方渲染 `<Tabs type="editable-card" hideAdd>` 标签栏，Content 区域中通过 `<Outlet />` 渲染标签页内容

## 测试要求

- 单元测试：Vitest + React Testing Library
- 至少覆盖关键页面和公共组件

## 禁止行为

- 禁止直接操作 DOM（声明式原则），特殊情况使用 ref 并注释说明
- 禁止在 render 中编写复杂逻辑，提取为函数或 Hook
- 禁止发起未处理错误的异步请求
- 禁止将 token 等敏感信息明文存储在 localStorage，至少做 base64 混淆或使用内存存储
