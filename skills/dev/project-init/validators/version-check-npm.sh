#!/usr/bin/env bash
# version-check-npm.sh —— 按"系列"筛最新稳定 GA，不取全局 latest（npm 适配）
# 用法: version-check-npm.sh <npm-pkg> <series-prefix>
#   <npm-pkg> 形如 react / antd / @tarojs/taro / @nutui/nutui-react-taro
#   <series-prefix> 形如 18. 5.22. 3.6. 3.4. 3. （结尾可带可不带点）
# 输出: 该系列最大稳定纯版本号（去 -beta/-rc/-alpha/-next/-canary 等预发布 + experimental/tag 变体）。
# 兼容无 patch 版本：series=18. 既能匹配 18 也能匹配 18.x；series=3.6. 匹配 3.6.x。
# scoped 包 URL 编码：@tarojs/taro -> registry.npmjs.org/@tarojs%2Ftaro
set -euo pipefail
PKG="$1"; SERIES="$2"
[[ -z "$PKG" || -z "$SERIES" ]] && { echo "usage: $0 <npm-pkg> <series-prefix>" >&2; exit 2; }
# scoped 包：把首个 / 编码为 %2F（@scope/pkg -> @scope%2Fpkg）；非 scoped 不动
if [[ "$PKG" == @* ]]; then
  URL_PKG="${PKG/\//%2F}"
else
  URL_PKG="$PKG"
fi
META="https://registry.npmjs.org/${URL_PKG}"
curl -sS --max-time 30 "$META" | python3 -c '
import sys, json, re
pkg, series = sys.argv[1], sys.argv[2]
try:
    data = json.load(sys.stdin)
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr); sys.exit(1)
versions = list((data.get("versions") or {}).keys())
# 稳定 GA：纯 x.y[.z...]，不含 - (预发布) 也不含非数字段
ga = [v for v in versions if re.match(r"^\d+(\.\d+)*$", v)]
prefix = series.rstrip(".")
matched = [v for v in ga if v == prefix or v.startswith(series)]
if not matched:
    print(f"ERROR: 系列 {series} 无稳定 GA（pkg={pkg}，共 {len(versions)} 版本）", file=sys.stderr)
    sys.exit(1)
print("\n".join(matched))
' "$PKG" "$SERIES" | sort -V | tail -1
