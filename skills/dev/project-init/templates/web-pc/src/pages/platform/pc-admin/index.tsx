import { Card, Button, Space } from "antd";

// pc-admin 叶子层示例页面（antd 仅在此层 + components/platform/pc 使用，规约18 两层锁隔离）。
export default function PcAdminIndex() {
  return (
    <Card title="PC 后台首页（示例）">
      <Space>
        <Button type="primary">示例操作</Button>
      </Space>
    </Card>
  );
}
