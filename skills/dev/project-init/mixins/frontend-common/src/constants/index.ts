// constants/index.ts —— 常量/枚举/配置统一入口（对标 Java constants 包，Taro 社区惯用 constants 取代 data）
// 禁魔法数值（对齐全局代码准则：统一抽取为具名常量）
export const API_PREFIX = "/api";
export const PAGE_SIZE_DEFAULT = 20;

// 枚举示例：业务单据状态（通用批发业务概念，零业务方名）
export enum OrderStatus {
  Pending = "pending",
  Confirmed = "confirmed",
  Settled = "settled",
  Cancelled = "cancelled",
}
