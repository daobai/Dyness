# -*- coding: utf-8 -*-
"""生成接口清单（docs/接口清单.md），扫描 tests/api/data/api_*.csv 统计各产品线的接口覆盖。

运行：py -3 tests/api/gen_interface_list.py
"""

import csv
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
OUT = Path(__file__).resolve().parent.parent.parent / "docs" / "接口清单.md"

MOD_CN = {'household': '户用储能', 'cygni': 'Cygni', 'highvoltage': '高压电池',
          'lowvoltage': '低压电池', 'juniorbox': 'JuniorBox', 'commerce': '工商业'}


def main():
    data = defaultdict(lambda: defaultdict(int))  # 接口 -> 模块 -> 用例数
    modules = []
    for f in sorted(DATA_DIR.glob("api_*.csv")):
        with open(f, encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                p = r["path"]
                m = r["module"]
                data[p][m] += 1
                if m not in modules:
                    modules.append(m)

    interfaces = sorted(data.keys())

    lines = []
    lines.append("# API 接口清单与测试覆盖")
    lines.append("")
    lines.append("> 本文件由用例 CSV 自动生成，运行 `py -3 tests/api/gen_interface_list.py` 刷新。")
    lines.append("")
    lines.append("## 接口 × 产品线覆盖矩阵")
    lines.append("")
    lines.append("| 接口 | " + " | ".join(MOD_CN.get(m, m) for m in modules) + " | 合计 |")
    lines.append("|" + "---|" * (len(modules) + 2))
    total_all = 0
    for p in interfaces:
        row = []
        s = 0
        for m in modules:
            n = data[p].get(m, 0)
            s += n
            row.append(str(n) if n else "-")
        total_all += s
        lines.append("| " + p.split("/")[-1] + " | " + " | ".join(row) + f" | {s} |")
    lines.append("")
    lines.append(f"共 **{len(interfaces)}** 个独立接口，**{total_all}** 条用例。")
    lines.append("")
    lines.append("## 各模块用例统计")
    lines.append("")
    lines.append("| 模块 | 用例数 |")
    lines.append("|---|---|")
    for m in modules:
        s = sum(data[p].get(m, 0) for p in interfaces)
        lines.append(f"| {MOD_CN.get(m, m)} | {s} |")
    lines.append("")
    lines.append("## 各模块接口明细")
    lines.append("")
    for m in modules:
        lines.append(f"### {MOD_CN.get(m, m)}（module={m}）")
        lines.append("")
        lines.append("| 接口 | 用例数 |")
        lines.append("|---|---|")
        for p in interfaces:
            n = data[p].get(m, 0)
            if n:
                lines.append(f"| {p.split('/')[-1]} | {n} |")
        lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"已生成 {OUT}（{len(interfaces)} 个接口，{total_all} 条用例，{len(modules)} 个模块）")


if __name__ == "__main__":
    main()
