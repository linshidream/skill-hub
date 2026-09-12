import { View, Text } from "@tarojs/components";
import { Button } from "@nutui/nutui-react-taro";
import "./index.css";

// 示例页面（占位，零业务名）。NutUI 组件用于 h5/weapp 通用叶子层。
export default function Index() {
  return (
    <View className="page">
      <Text>{{project.name}}</Text>
      <Button type="primary">示例操作</Button>
    </View>
  );
}
