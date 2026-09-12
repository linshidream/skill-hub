import { Typography } from "antd";

// web-pc 根组件（示例占位，零业务名）。实际页面放 src/pages/platform/pc-admin 叶子层。
export default function App() {
  return (
    <div style={{ padding: 24 }}>
      <Typography>
        <Typography.Title level={2}>{{project.name}}</Typography.Title>
        <Typography.Paragraph>PC 后台工程骨架已就绪（vite + React + antd）。</Typography.Paragraph>
      </Typography>
    </div>
  );
}
