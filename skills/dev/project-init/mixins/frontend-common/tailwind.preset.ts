// tailwind.preset.js —— 前端共享 design-token 单一来源（规约19）。
// 抽 src/design-token.ts 为唯一源头，此处注入 tailwind.config 主题；各 template 的 tailwind.config extends 本 preset。
// 禁两套 token 并存致视觉割裂；weapp-tailwindcss 生产构建开启按需裁剪（content purge）。
import { designTokens } from "./src/design-token.ts";

/** @type {import('tailwindcss').Config} */
export default {
  theme: {
    extend: {
      colors: designTokens.colors,
      spacing: designTokens.spacing,
    },
  },
  // content purge 由各 template 的 tailwind.config 声明（端路径不同：pc vs h5/weapp）
};
