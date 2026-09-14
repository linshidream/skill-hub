import { QueryClient, useQuery } from "@tanstack/react-query";

// 服务端状态缓存层（规约21）：query=GET 带缓存，mutation=POST 失效缓存。对标后端查询缓存层。
// 统一 QueryClient 单例，禁各页面手写 useState+useEffect 请求（存量旧项目式债务温床）。
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000, // 30s 内不重复请求（对标后端缓存 TTL）
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// 业务 Hook 封装示例（调 api 层，禁在 service 引 React/Taro——本文件是 hooks/business 层）
export { useQuery };
