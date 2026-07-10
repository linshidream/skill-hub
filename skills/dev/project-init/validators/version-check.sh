#!/usr/bin/env bash
# version-check.sh —— 按"系列"筛最新 GA，不取全局 latest
# 用法: version-check.sh <maven-path> <series-prefix>
#   <series-prefix> 形如 1.0. 3.5. 2.7. 2.0. 5.8. 7.4. 8. （结尾可带可不带点）
# 输出: 该系列最大 GA 纯版本号（去 M/RC/SNAPSHOT/android 变体）。查不到 exit 1。
# 兼容无 patch 版本：series=7.4. 既能匹配 7.4 也能匹配 7.4.x。
set -euo pipefail
PATH_ART="$1"; SERIES="$2"
[[ -z "$PATH_ART" || -z "$SERIES" ]] && { echo "usage: $0 <maven-path> <series-prefix>" >&2; exit 2; }
META="https://repo1.maven.org/maven2/${PATH_ART}/maven-metadata.xml"
curl -sS --max-time 30 "$META" | python3 -c '
import sys, re, xml.etree.ElementTree as ET
series = sys.argv[1]
try: t=ET.parse(sys.stdin).getroot()
except Exception as e: print(f"ERROR: {e}",file=sys.stderr); sys.exit(1)
vs=[v.text for v in t.findall("versioning/versions/version")]
ga=[v for v in vs if re.match(r"^\d+(\.\d+)*$", v)]
prefix=series.rstrip(".")
matched=[v for v in ga if v==prefix or v.startswith(series)]
print("\n".join(matched))
' "$SERIES" | sort -V | tail -1
