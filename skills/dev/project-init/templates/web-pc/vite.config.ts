import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

// vite 配置（纯 PC web，非 Taro）。@ 别名对齐 tsconfig paths。
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "src") },
  },
  build: { outDir: "dist", sourcemap: false },
  server: { port: 5173 },
});
