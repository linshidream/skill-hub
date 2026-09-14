// eslint.config.js —— 前端规约可执行源（规范源权威）。人读手册 docs/frontend-spec.md 是其镜像+非可执行补充。
// 双轨同源：每条 rule 上方标注对应规约编号（// 规约N）；scripts/check-spec-sync.js 校验【E】编号与 config 一一对应，漂移即 CI 红。
// import-boundary 两层锁（规约 18）：① 小程序/H5 模块禁导 antd/@ant-design/*；② 非 pc 模块禁导 pc 叶子层。
import tseslint from "typescript-eslint";
import importPlugin from "eslint-plugin-import";

export default tseslint.config(
  // ===== 全局基线 =====
  {
    files: ["src/**/*.{ts,tsx}"],
    extends: [...tseslint.configs.recommended],
    languageOptions: {
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
    },
  },

  // 规约10【E】：统一 TS/TSX，禁纯 JS 业务代码（tsconfig strict + noUncheckedIndexedAccess 在 tsconfig.json 兜底）
  // 规约13【E】：禁 any，禁 @ts-ignore 滥用
  {
    files: ["src/**/*.{ts,tsx}"],
    rules: {
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/ban-ts-comment": "error",
      "no-console": ["warn", { allow: ["warn", "error"] }],
    },
  },

  // 规约3【E】：service/types/utils/hooks/business 层禁引 React/Taro 框架 API（端无关纯 TS，可单测可跨项目复用）
  // 对标 Java "Service 层禁引 Controller"。失败即说明把 UI 逻辑塞进了逻辑层。
  {
    files: ["src/{service,types,utils,hooks/business}/**/*.{ts,tsx}"],
    rules: {
      "no-restricted-imports": ["error", {
        paths: [
          { name: "react", message: "规约3：service/types/utils/hooks/business 禁引 React（端无关纯 TS层）" },
          { name: "@tarojs/taro", message: "规约3：service/types/utils/hooks/business 禁引 Taro" },
          { name: "@nutui/nutui-react-taro", message: "规约3：禁引 NutUI（UI 库不进逻辑层）" },
          { name: "antd", message: "规约3：禁引 antd（UI 库不进逻辑层）" },
        ],
        patterns: [
          { group: ["@tarojs/*"], message: "规约3：禁引 Taro 框架 API（端无关层）" },
          { group: ["react-*"], message: "规约3：禁引 React 周边库（端无关层）" },
        ],
      }],
    },
  },

  // 规约18【E】第一层锁：小程序/H5 模块禁导 antd / @ant-design/*（antd 仅限 pc 叶子层）
  {
    files: ["src/components/platform/{h5,weapp}/**/*.{ts,tsx}", "src/pages/platform/{h5,weapp}/**/*.{ts,tsx}"],
    rules: {
      "no-restricted-imports": ["error", {
        paths: [
          { name: "antd", message: "规约18：小程序/H5 端禁导 antd（仅 pc 叶子层允许）" },
        ],
        patterns: [
          { group: ["@ant-design/*"], message: "规约18：小程序/H5 端禁导 @ant-design/*" },
        ],
      }],
    },
  },

  // 规约18【E】第二层锁：非 pc 模块禁导 pc 叶子层组件（防 pc 组件把 antd 间接带入小程序/H5）
  {
    files: ["src/**/*.{ts,tsx}"],
    ignores: ["src/components/platform/pc/**", "src/pages/platform/pc-admin/**"],
    rules: {
      "no-restricted-imports": ["error", {
        patterns: [
          { group: ["@/components/platform/pc/**", "@/pages/platform/pc-admin/**", "../platform/pc/**", "../../platform/pc/**"],
            message: "规约18：非 pc 模块禁导 pc 叶子层组件（防 antd 间接串入小程序/H5）" },
        ],
      }],
    },
  },

  // 规约25【E】：请求层统一封装，禁散调裸 fetch（对标后端 FeignClient 统一）
  {
    files: ["src/**/*.{ts,tsx}"],
    ignores: ["src/api/**"],
    rules: {
      "no-restricted-imports": ["error", {
        patterns: [
          { group: ["node:fetch"], message: "规约25：禁裸 fetch，统一走 src/api 封装" },
        ],
      }],
      "no-restricted-globals": ["error", { name: "fetch", message: "规约25：禁裸 fetch，统一走 src/api 封装（api 层除外）" }],
    },
  },

  // 规约11【E】：命名约束（组件 PascalCase、Hook use 前缀由文件名 lint 兜底）
  {
    files: ["src/**/*.{ts,tsx}"],
    rules: {
      "import/order": ["warn", { "newlines-between": "always" }],
    },
    settings: {
      "import/resolver": { typescript: { project: "./tsconfig.json" } },
    },
    plugins: { import: importPlugin },
  },
);
