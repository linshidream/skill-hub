#!/usr/bin/env node
// check-spec-sync.js —— 规约双轨同源校验（规约 P1-3）。
// 扫手册 docs/frontend-spec.md 的【E】编号集 A，与 eslint.config.js 注释中 // 规约N 编号集 B，
// A ≠ B 即 exit 1（漏配/漂移 CI 红）。不做双向 codegen（三次法则，不过早抽象）。
// 挂 pre-commit / CI：单边改不跟 → CI 挡。
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const specPath = join(root, "docs", "frontend-spec.md");
const eslintPath = join(root, "eslint.config.js");

function fail(msg) {
  console.error(`[check-spec-sync] FAIL: ${msg}`);
  process.exit(1);
}

for (const p of [specPath, eslintPath]) {
  if (!existsSync(p)) fail(`缺少文件 ${p}`);
}

// A：手册中【E】(eslint 可执行) 规约编号——行首 "<N>. 【E】" 形式。
// 【M】规则不进 eslint，不参与比对（不会误报漂移）。
const spec = readFileSync(specPath, "utf8");
const setA = new Set();
for (const m of spec.matchAll(/^\s*(\d+)\.\s*【E】/gm)) setA.add(Number(m[1]));

// B：eslint.config.js 注释中的 // 规约N（仅【E】规则在 config 中有注释锚点）
const eslintCfg = readFileSync(eslintPath, "utf8");
const setB = new Set();
for (const m of eslintCfg.matchAll(/规约\s*(\d+)/g)) setB.add(Number(m[1]));

const onlyA = [...setA].filter((n) => !setB.has(n)).sort((a, b) => a - b);
const onlyB = [...setB].filter((n) => !setA.has(n)).sort((a, b) => a - b);

if (onlyA.length || onlyB.length) {
  let msg = "规约双轨不同源（eslint 可执行源 ↔ 人读手册漂移）\n";
  if (onlyA.length) msg += `  手册有但 eslint 缺：【E】规约 ${onlyA.join(", ")}（漏配可执行规则）\n`;
  if (onlyB.length) msg += `  eslint 有但手册缺：规约 ${onlyB.join(", ")}（手册未记录）\n`;
  fail(msg);
}

console.log(`[check-spec-sync] OK：手册【E】${setA.size} 条 ↔ eslint 注释 ${setB.size} 条，一一对应，同源不漂移。`);
