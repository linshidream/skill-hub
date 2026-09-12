# 前端工程开发规约手册

> 双轨同源：可执行规则进 `eslint.config.js`（规范源权威），不可执行约定进本手册。两者同源不漂移，
> `scripts/check-spec-sync.js` 校验【E】编号一一对应，漂移即 CI 红。
> 标注：【E】=eslint 可执行 / 【M】=人读手册 / 【双】=双轨。目标读者：后端工程师，用 Java 对标讲。

---

## 一、框架规约

1. 【M】Taro 钉系列 `3.6.x`，依赖版本由 `version-check` 实时解析该系列最新稳定 patch，禁硬编码具体 patch 号入库。对标 maven version-check。
2. 【M】禁用库清单（避坑核心）：shadcn/ui、Radix UI、Chakra UI（纯 Web 重 DOM，无法编译小程序）、antd-mobile（仅 H5）、Taro5、Tailwind v4。对标后端"禁用不安全依赖"。
3. 【E】`service`/`types`/`utils`/`hooks/business` 层禁引 React/Taro 框架 API（eslint import-boundary）。对标"Service 层禁引 Controller"。
4. 【M】运行时平台差异：H5 有 `window`/`document`，小程序与 RN 完全没有。后端最大暗礁——禁在 service/utils/types 用任何 DOM/BOM API；端专属能力只放 `hooks/platform`、`components/platform`。条件编译统一 `process.env.TARO_ENV`，禁混 `NODE_ENV` 判端。

## 二、项目规约

5. 【M】目录骨架遵循 README 横切分层 + 叶子层分端。对标 Maven 标准目录结构。随 `project-init` 生成，禁手改顶层结构。
6. 【M】分层对标：`api`=Feign 请求层、`service`=Service 业务层、`types`=实体/DTO、`components`/`pages`=视图层。后端一眼对上。
7. 【M】`assets` 统一入口，禁图片散落各页（反面教材：存量旧项目常 466 张图散落各页目录）。对标后端 `resources/`。
8. 【M】跨项目复用边界：`service`/`types`/`utils` 可复用，`pages`/`components` 不可。对标后端 common 模块复用边界。
9. 【M】`package.json` 依赖须与 manifest 声明 series 一致，新增第三方依赖需明确许可（直接继承 project-init 现有红线）。

## 三、代码规约

10. 【E】统一 TS/TSX，禁纯 JS 业务代码（tsconfig strict + noUncheckedIndexedAccess）。对标 Java 强类型，TS interface=Java 实体。
11. 【E】命名：组件 PascalCase、Hook `use` 前缀、service 方法驼峰、api 函数动词开头。对标 Java 命名规约。
12. 【M】单文件行数上限 ≤400 行，禁上千行（页面拆区块组件）。对标"类不过大"。
13. 【E】禁 `any`，禁 `@ts-ignore` 滥用（须附修复 TODO）。对标后端禁裸 Object/无类型。
14. 【M】提交信息：体系内项目沿用中文描述（如"用户管理优化"）；此条为项目级惯例非通用强制，新独立项目可改英文 Conventional Commits，但一项目内禁中英混用。

## 四、版本规约

15. 【M】依赖钉 series，version-check 解析，禁随意升级大版本；package.json 用精确锁（无 `^`），pnpm `save-exact=true`，防模糊版本漂移到不兼容版本（NutUI 等 Taro 生态库尤其严）。对标 maven 版本管理。
16. 【M】`pnpm-lock.yaml` 必须入库（对标 package-lock）；`.nvmrc` + `engines` 字段锁定 Node 基线（对标 JDK 版本约束）。
17. 【M】禁 Ant Motion 类动效库引入（多端不可用），动效用 CSS animation / Taro 内置。

## 五、前端特点规约

### 5.1 UI 组件

18. 【E】H5/小程序通用组件用 `@nutui/nutui-react-taro`；`antd` 仅 `components/platform/pc`、`pages/platform/pc-admin`；iOS App(RN) 端用 `react-native-paper`（叶子层 `components/platform/rn`，端延后）。eslint import-boundary 两层锁：① 小程序/H5 模块禁导 `antd`、`@ant-design/*`；② 非 pc 模块禁导 `@/components/platform/pc/**`、`@/pages/platform/pc-admin/**`（防 pc 叶子层把 antd 间接带入小程序）。对标按端隔离依赖。
19. 【M】样式工程三协调：① tailwind 只做布局/间距/对齐，禁覆盖 NutUI 组件核心样式；② design-token 单一来源（`src/design-token.ts` 注入 tailwind 与 NutUI 主题，禁两套 token 并存）；③ weapp-tailwindcss 生产构建开启按需裁剪（content purge），禁全量引入致小程序 wxss 撞限。对标"不覆盖框架内部 + 统一配置源"。
20. 【M】动效降级认知：小程序无 Ant Motion，用 CSS animation / Taro 内置动画，视觉表现力会降级，需求方需预期对齐。

### 5.2 状态管理

21. 【M】服务端状态（列表/详情/mutation）用 TanStack Query，禁各页面手写 useState+useEffect 请求（存量旧项目式债务温床）。对标后端查询缓存层。依赖首个落地项目 Taro weapp 冒烟结论：React Query 在 weapp 运行时的 selector 订阅若不过，改缓存方案不动双层架构。
22. 【M】客户端共享态用 Zustand；极小跨页态用 React Context（零依赖）。禁一项目混用多套状态方案。
23. 【M】业务状态机（如订单/结算流转）是后端业务，不归前端状态管理，前端只展示后端状态+提交动作。

### 5.3 JS/TS/逻辑/API

24. 【M】`api/` 只放地址+请求方法+参数封装，禁塞页面逻辑。对标前端工程师分层。
25. 【E】请求层统一封装（`Taro.request`/统一 client），禁散调裸 fetch（eslint 检测，api 层除外）。对标后端 FeignClient 统一。
26. 【M】`service` 纯函数纯 TS，可单测，对标 Java Service。禁在 service 引 React/Taro。
27. 【M】三端共用类型定义放 `types/`，端无关。这是 Taro 多端复用的核心价值。
