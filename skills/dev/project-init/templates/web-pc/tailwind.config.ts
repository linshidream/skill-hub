import type { Config } from "tailwindcss";
import preset from "./tailwind.preset";

// web-pc tailwind 配置：extends frontend-common preset（design-token 单一来源，规约19）。
// content purge 按需裁剪（规约19③），防止产物臃肿。
export default {
  presets: [preset],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
} satisfies Config;
