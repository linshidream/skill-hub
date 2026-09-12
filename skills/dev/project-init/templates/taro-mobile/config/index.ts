import { defineConfig, type UserConfigExport } from "@tarojs/cli";
import path from "node:path";
import { UnifiedWebpackPluginV5 } from "weapp-tailwindcss/webpack";
import devConfig from "./dev";
import prodConfig from "./prod";

// Taro3.6 多端编译配置（H5 + 微信小程序）。
// weapp-tailwindcss：小程序端抹平 tailwind class（规约19③ 生产按需裁剪），webpackChain 注入 V5 插件。
// 注：weapp-tailwindcss 与 Taro 版本兼容性在首个落地项目冒烟核实（见 compat-table pending）。
export default defineConfig<"webpack5">(async (merge) => {
  const base: UserConfigExport<"webpack5"> = {
    projectName: "{{project.name}}",
    date: "2026-08-18",
    designWidth: 750,
    deviceRatio: { 640: 2.34 / 2, 750: 1, 828: 1.81 / 2 },
    sourceRoot: "src",
    outputRoot: {
      h5: "dist",
      weapp: "dist",
    } as any,
    alias: { "@": path.resolve(__dirname, "..", "src") },
    jsxAtomicClass: undefined as any,
    plugins: [],
    mini: {
      postcss: {
        autoprefixer: { enable: true },
        tailwindcss: { enable: true },
      },
      webpackChain(chain: any) {
        chain.plugin("weapp-tailwindcss").use(UnifiedWebpackPluginV5, [{ appType: "taro" }]);
      },
    },
    h5: {
      output: "dist",
      postcss: {
        autoprefixer: { enable: true },
        tailwindcss: { enable: true },
      },
      devServer: { port: 10086 },
    },
    copy: { patterns: [], options: {} },
    logger: { quiet: false, stats: true },
  };
  return merge({}, base, process.env.NODE_ENV === "production" ? prodConfig : devConfig);
});
