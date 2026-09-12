import { PropsWithChildren } from "react";
import { useLaunch } from "@tarojs/taro";
import { ConfigProvider } from "@nutui/nutui-react-taro";
import { designTokens } from "@/design-token";
import "./app.css";

// Taro3.6 应用入口。NutUI ConfigProvider 注入 design-token（规约19②，主题与 tailwind 同源）。
function App({ children }: PropsWithChildren) {
  useLaunch(() => {
    console.log("app launched");
  });
  return (
    <ConfigProvider
      theme={{
        primaryColor: designTokens.colors.primary,
        successColor: designTokens.colors.success,
        warningColor: designTokens.colors.warning,
        dangerColor: designTokens.colors.error,
      }}
    >
      {children}
    </ConfigProvider>
  );
}

export default App;
