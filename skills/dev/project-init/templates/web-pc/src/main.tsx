import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ConfigProvider, App as AntdApp } from "antd";
import zhCN from "antd/locale/zh_CN";
import { designTokens } from "@/design-token";
import App from "@/App";
import "@/index.css";

// web-pc 入口：antd ConfigProvider 注入 design-token（规约19②，主题与 tailwind 同源）
const root = createRoot(document.getElementById("root")!);
root.render(
  <StrictMode>
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: designTokens.colors.primary,
          colorSuccess: designTokens.colors.success,
          colorWarning: designTokens.colors.warning,
          colorError: designTokens.colors.error,
          borderRadius: Number(designTokens.radius.md),
        },
      }}
    >
      <AntdApp>
        <App />
      </AntdApp>
    </ConfigProvider>
  </StrictMode>,
);
