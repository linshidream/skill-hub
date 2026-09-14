import { create } from "zustand";

// 客户端共享态（规约22）：跨页共享的纯前端态放这里（选货篮/登录态/草稿）。
// 服务端态（列表/详情/mutation）走 TanStack Query（见 hooks/business/use-query-client），禁各页面手写请求（规约21）。
// 极小跨页态用 React Context（零依赖），不预置；禁一项目混用多套状态方案。
interface AppState {
  // 示例：登录态（中性词，零业务名）
  token: string | null;
  setToken: (token: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  token: null,
  setToken: (token) => set({ token }),
}));
