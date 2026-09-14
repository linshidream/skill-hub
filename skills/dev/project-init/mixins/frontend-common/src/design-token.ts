// design-token.ts —— 设计令牌单一来源（规约19）。
// 唯一源头：分别注入 tailwind.config（见 tailwind.preset.js）与 NutUI/antd 主题，禁两套 token 并存致视觉割裂。
// 主题定制机制待首个落地项目冒烟核实后细化（见 compat-table pending）。

export const designTokens = {
  // 色彩令牌：中性词，零业务名
  colors: {
    primary: "#1677ff",
    success: "#52c41a",
    warning: "#faad14",
    error: "#ff4d4f",
    text: { base: "#1f1f1f", secondary: "#8c8c8c", disabled: "#bfbfbf" },
    bg: { page: "#f5f5f5", card: "#ffffff" },
    border: "#d9d9d9",
  },
  // 间距令牌（4px 栅格）
  spacing: {
    xs: "4px",
    sm: "8px",
    md: "16px",
    lg: "24px",
    xl: "32px",
  },
  // 圆角
  radius: { sm: "4px", md: "8px", lg: "12px" },
} as const;

export type DesignTokens = typeof designTokens;
