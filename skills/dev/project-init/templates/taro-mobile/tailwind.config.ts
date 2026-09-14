import type { Config } from "tailwindcss";
import preset from "../tailwind.preset";

// taro-mobile tailwind 配置：extends frontend-common preset（design-token 单一来源，规约19）。
// content 覆盖 src 全量；weapp-tailwindcss 在 config/index.ts 抹平小程序端 class。
export default {
  presets: [preset],
  content: ["./src/**/*.{ts,tsx,html}"],
} satisfies Config;
