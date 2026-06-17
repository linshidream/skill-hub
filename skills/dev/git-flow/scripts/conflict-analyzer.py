#!/usr/bin/env python3
"""
git-flow 冲突分析器

分析 git merge 冲突，分类为 trivial（可生成候选方案）或 business（需人工决策），
并对 trivial 冲突生成候选解决内容。V1 不直接写回冲突文件。

V1 实现前 4 种 trivial 分类：
  1. import 顺序差异
  2. 文件末尾空行差异
  3. 注释差异（非 TODO/FIXME/HACK）
  4. 空白字符差异

V2 将增加：
  5. 相邻非重叠编辑（需语言 parser 支持）

用法:
  python3 conflict-analyzer.py [--max-auto-files 3] [--auto-resolve trivial]
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

IMPORT_PATTERNS = [
    re.compile(r'^\s*import\s+'),       # Java, Python, TypeScript
    re.compile(r'^\s*#include\s+'),      # C/C++
    re.compile(r'^\s*require\s*[\(]'),   # Node.js require()
    re.compile(r'^\s*from\s+\S+\s+import\s+'),  # Python from...import
]

COMMENT_PATTERNS = [
    re.compile(r'^\s*//'),              # Java, JS, Go
    re.compile(r'^\s*#(?!include)'),    # Python, Shell (not C #include)
    re.compile(r'^\s*/\*'),             # Block comment start
    re.compile(r'^\s*\*'),              # Block comment middle
    re.compile(r'^\s*\*/'),             # Block comment end
]

ACTIONABLE_COMMENT = re.compile(r'\b(TODO|FIXME|HACK|XXX|BUG)\b', re.IGNORECASE)


def get_conflict_files() -> list[str]:
    result = subprocess.run(
        ['git', 'diff', '--name-only', '--diff-filter=U'],
        capture_output=True, text=True
    )
    return [f for f in result.stdout.strip().split('\n') if f]


def read_file_content(filepath: str) -> str:
    try:
        return Path(filepath).read_text(encoding='utf-8', errors='replace')
    except (OSError, IOError):
        return ''


def parse_conflict_blocks(content: str) -> list[dict]:
    blocks = []
    current: dict[str, Any] | None = None

    for line in content.split('\n'):
        if line.startswith('<<<<<<<'):
            current = {'ours': [], 'theirs': [], 'section': 'ours'}
        elif line.startswith('=======') and current is not None:
            current['section'] = 'theirs'
        elif line.startswith('>>>>>>>') and current is not None:
            del current['section']
            blocks.append(current)
            current = None
        elif current is not None:
            current[current['section']].append(line)

    return blocks


def is_import_line(line: str) -> bool:
    return any(p.match(line) for p in IMPORT_PATTERNS)


def is_comment_line(line: str) -> bool:
    return any(p.match(line) for p in COMMENT_PATTERNS)


def has_actionable_comment(line: str) -> bool:
    return bool(ACTIONABLE_COMMENT.search(line))


def is_whitespace_only_diff(ours: list[str], theirs: list[str]) -> bool:
    ours_stripped = [l.strip() for l in ours if l.strip()]
    theirs_stripped = [l.strip() for l in theirs if l.strip()]
    return ours_stripped == theirs_stripped


def is_trailing_newline_diff(ours: list[str], theirs: list[str]) -> bool:
    ours_content = [l for l in ours if l.strip()]
    theirs_content = [l for l in theirs if l.strip()]
    if ours_content != theirs_content:
        return False
    ours_empty = len(ours) - len(ours_content)
    theirs_empty = len(theirs) - len(theirs_content)
    return ours_empty != theirs_empty


def classify_block(block: dict) -> dict:
    ours = block['ours']
    theirs = block['theirs']

    if is_trailing_newline_diff(ours, theirs):
        resolved = [l for l in (ours if ours else theirs) if l.strip()]
        resolved.append('')
        return {
            'reason': 'trailing_newline',
            'confidence': 0.98,
            'auto_resolution': '\n'.join(resolved),
        }

    if is_whitespace_only_diff(ours, theirs):
        return {
            'reason': 'whitespace',
            'confidence': 0.97,
            'auto_resolution': '\n'.join(ours),
        }

    if all(is_import_line(l) for l in ours if l.strip()) and \
       all(is_import_line(l) for l in theirs if l.strip()):
        merged = sorted(set(l.rstrip() for l in ours + theirs if l.strip()))
        return {
            'reason': 'import_order',
            'confidence': 0.95,
            'auto_resolution': '\n'.join(merged),
        }

    ours_non_empty = [l for l in ours if l.strip()]
    theirs_non_empty = [l for l in theirs if l.strip()]
    if (all(is_comment_line(l) for l in ours_non_empty) and
        all(is_comment_line(l) for l in theirs_non_empty)):
        if any(has_actionable_comment(l) for l in ours_non_empty + theirs_non_empty):
            return {
                'reason': 'actionable_comment',
                'confidence': 0.5,
                'auto_resolution': None,
            }
        return {
            'reason': 'comment',
            'confidence': 0.95,
            'auto_resolution': '\n'.join(theirs),
        }

    return {
        'reason': 'function_body_change',
        'confidence': 0.0,
        'auto_resolution': None,
    }


def get_commit_context(filepath: str) -> dict:
    context = {}
    for side, ref in [('ours', 'HEAD'), ('theirs', 'MERGE_HEAD')]:
        result = subprocess.run(
            ['git', 'log', ref, '-1', '--format=%s', '--', filepath],
            capture_output=True, text=True
        )
        context[f'{side}_commit'] = result.stdout.strip() if result.returncode == 0 else ''
    return context


def analyze_file(filepath: str) -> dict:
    content = read_file_content(filepath)
    blocks = parse_conflict_blocks(content)

    if not blocks:
        return {'file': filepath, 'category': 'business', 'reason': 'parse_error',
                'confidence': 0.0, 'blocks': 0}

    classifications = [classify_block(b) for b in blocks]

    all_trivial = all(c['confidence'] >= 0.75 for c in classifications)
    min_confidence = min(c['confidence'] for c in classifications) if classifications else 0.0

    if all_trivial:
        resolutions = []
        for block, cls in zip(blocks, classifications):
            if cls['auto_resolution'] is not None:
                resolutions.append(cls['auto_resolution'])
            else:
                resolutions.append('\n'.join(block['ours']))

        return {
            'file': filepath,
            'category': 'trivial',
            'reason': classifications[0]['reason'] if len(set(c['reason'] for c in classifications)) == 1
                      else 'mixed_trivial',
            'confidence': min_confidence,
            'auto_resolution': '\n---\n'.join(resolutions),
            'blocks': len(blocks),
        }
    else:
        commit_ctx = get_commit_context(filepath)
        ours_ctx = '\n'.join(blocks[0]['ours'][:10]) if blocks else ''
        theirs_ctx = '\n'.join(blocks[0]['theirs'][:10]) if blocks else ''

        return {
            'file': filepath,
            'category': 'business',
            'reason': next((c['reason'] for c in classifications if c['confidence'] < 0.75),
                          'function_body_change'),
            'confidence': min_confidence,
            'ours_context': ours_ctx,
            'theirs_context': theirs_ctx,
            **commit_ctx,
            'blocks': len(blocks),
        }


def main():
    parser = argparse.ArgumentParser(description='Analyze git merge conflicts')
    parser.add_argument('--max-auto-files', type=int, default=3)
    parser.add_argument('--auto-resolve', choices=['trivial', 'none'], default='trivial')
    args = parser.parse_args()

    conflict_files = get_conflict_files()
    if not conflict_files:
        print(json.dumps({
            'total_conflicts': 0,
            'by_category': {'trivial': [], 'business': []},
            'recommendation': 'auto_resolvable',
        }, ensure_ascii=False, indent=2))
        return

    results = [analyze_file(f) for f in conflict_files]

    trivial = [r for r in results if r['category'] == 'trivial']
    business = [r for r in results if r['category'] == 'business']

    if not business and len(trivial) <= args.max_auto_files and args.auto_resolve == 'trivial':
        recommendation = 'auto_resolvable'
    elif not business:
        recommendation = 'suggest_rebase'
    else:
        recommendation = 'needs_human'

    output = {
        'total_conflicts': len(conflict_files),
        'by_category': {
            'trivial': trivial,
            'business': business,
        },
        'recommendation': recommendation,
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
