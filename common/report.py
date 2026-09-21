# -*- coding: utf-8 -*-
"""测试报告：收集每条用例结果，零依赖生成 HTML + JSON 报告。

通用测试基础设施，供 api / modbus 等所有测试模块复用。
结果由各测试通过 report.record(...) 收集，
在对应 conftest 的 pytest_sessionfinish 里调用 report.write_reports(...) 落盘。
"""

import html
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

_RESULTS = []


def reset():
    _RESULTS.clear()


def record(entry):
    """追加一条用例结果。

    entry 字段：case_id / name / device_sn / model / method / url /
               status / outcome(PASS|PENDING|FAIL|SKIP) / duration / error
    """
    _RESULTS.append(entry)


def results():
    return list(_RESULTS)


_OUTCOME_LABEL = {"PASS": "通过", "PENDING": "待确认", "FAIL": "不通过", "SKIP": "跳过"}


def _summary(results=None):
    rs = results if results is not None else _RESULTS
    total = len(rs)
    passed = sum(1 for r in rs if r["outcome"] == "PASS")
    pending = sum(1 for r in rs if r["outcome"] == "PENDING")
    failed = sum(1 for r in rs if r["outcome"] == "FAIL")
    skipped = sum(1 for r in rs if r["outcome"] == "SKIP")
    executed = total - skipped
    rate = f"{passed / executed * 100:.1f}%" if executed else "-"
    return {
        "total": total, "passed": passed, "pending": pending,
        "failed": failed, "skipped": skipped, "rate": rate,
    }


def _parse_code_mismatch(error):
    """从错误信息提取 (预期业务码, 实际业务码)。"""
    m = re.search(r"code 非 (\S+)，实际 '(\S+)'", error or "")
    return (m.group(1), m.group(2)) if m else (None, None)


def _resp_info(r):
    """从响应体提取 info 字段（如 NETWORK_ERROR / Request parameter exception）。"""
    body = (r.get("response") or {}).get("body") or ""
    m = re.search(r'"info"\s*:\s*"([^"]*)"', body)
    return m.group(1) if m else ""


def _case_category(r):
    """从 description 提取用例类别（冒号前缀）；无则归「其他」。"""
    desc = (r.get("description") or "").strip()
    if ":" in desc:
        return desc.split(":", 1)[0]
    return "其他"


def build_conclusion(results=None):
    """自动从结果生成测试结论（每条一行）：总览 + 类别统计 + 不通过归类 + 待确认。"""
    rs = results if results is not None else _RESULTS

    lines = []
    s = _summary(rs)

    # 1. 总览统计（无论结果如何都给出）
    lines.append(
        f"总览：共 {s['total']} 条，通过 {s['passed']}，待确认 {s['pending']}，"
        f"不通过 {s['failed']}，跳过 {s['skipped']}，通过率 {s['rate']}"
    )

    # 2. 按用例类别统计
    cats = defaultdict(lambda: [0, 0, 0])  # 类别 -> [总数, 通过, 不通过]
    for r in rs:
        c = cats[_case_category(r)]
        c[0] += 1
        if r["outcome"] == "PASS":
            c[1] += 1
        elif r["outcome"] == "FAIL":
            c[2] += 1
    if cats:
        lines.append("接口类别统计：")
        for cat, (total, passed, failed) in sorted(cats.items(), key=lambda x: -x[1][0]):
            lines.append(f"  {cat}：{total} 条（通过 {passed}，不通过 {failed}）")

    # 3. 不通过归类
    groups = defaultdict(list)
    for r in rs:
        if r["outcome"] == "FAIL":
            exp, act = _parse_code_mismatch(r.get("error"))
            if act == "429":
                key = "限流(429)"
            elif exp == "500" and act == "200":
                key = "参数校验缺失(预期500实际200)"
            elif exp == "200" and act == "500":
                info = _resp_info(r)
                if info == "NETWORK_ERROR":
                    key = "设备通信错误(NETWORK_ERROR)"
                elif info == "Request parameter exception":
                    key = "参数错误(Request parameter exception)"
                else:
                    key = "正常/边界值被拒(预期200实际500)"
            elif exp and act:
                key = f"业务码不符(预期{exp}实际{act})"
            else:
                key = "其他错误"
            groups[key].append(r)
    if groups:
        lines.append("不通过归类：")
        for key, items in groups.items():
            ids = "、".join(r["case_id"] for r in items)
            lines.append(f"  {key}：{len(items)} 个（{ids}）")

    # 4. 待确认
    pending = [r for r in rs if r["outcome"] == "PENDING"]
    if pending:
        ids = "、".join(r["case_id"] for r in pending)
        lines.append(f"待确认：{len(pending)} 个（{ids}）")

    return lines


def render_json(meta, conclusion=None):
    data = {"meta": meta, "summary": _summary(), "results": _RESULTS}
    if conclusion:
        data["conclusion"] = conclusion
    return json.dumps(data, ensure_ascii=False, indent=2)


_CSS = """
body{font-family:-apple-system,'Segoe UI','Microsoft YaHei',sans-serif;margin:24px;color:#24292f;background:#f6f8fa}
h1{font-size:22px;margin:0 0 4px}
.sub{color:#57606a;font-size:13px;margin-bottom:16px}
.cards{display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap}
.card{background:#fff;border:1px solid #d0d7de;border-radius:8px;padding:14px 20px;min-width:110px;box-shadow:0 1px 2px rgba(0,0,0,.05)}
.card .num{font-size:26px;font-weight:600}
.card .lbl{font-size:12px;color:#57606a}
.card.pass .num{color:#1a7f37}.card.fail .num{color:#cf222e}.card.skip .num{color:#9a6700}.card.pending .num{color:#bc4c00}
table{border-collapse:collapse;width:100%;background:#fff;border:1px solid #d0d7de;font-size:13px}
th,td{border:1px solid #d0d7de;padding:7px 10px;text-align:left;vertical-align:top}
th{background:#f6f8fa;font-weight:600;white-space:nowrap}
tr.pass{background:#f6fff8}tr.fail{background:#fff5f5}tr.skip{background:#fffbe6}tr.pending{background:#fff8f0}
.badge{display:inline-block;padding:1px 8px;border-radius:10px;font-size:12px;font-weight:600}
.badge.pass{background:#dafbe1;color:#1a7f37}.badge.fail{background:#ffebe9;color:#cf222e}.badge.skip{background:#fff8c5;color:#9a6700}.badge.pending{background:#ffd8b5;color:#bc4c00}
.url{max-width:320px;word-break:break-all;font-family:ui-monospace,Consolas,monospace;font-size:12px}
.error{max-width:360px;word-break:break-all;color:#cf222e;font-family:ui-monospace,Consolas,monospace;font-size:12px}
pre{max-width:600px;overflow:auto;white-space:pre-wrap;word-break:break-all;font-size:12px;margin:0}
.concl{background:#fff;border:1px solid #d0d7de;border-radius:8px;padding:12px 18px;margin-bottom:16px}
.concl h2{font-size:15px;margin:0 0 8px}
.concl ul{margin:0;padding-left:20px;font-size:13px;line-height:1.8}
"""


def _fmt_headers(headers):
    if not headers:
        return "(无)"
    return "\n".join(f"{k}: {v}" for k, v in headers.items())


def _build_message(r):
    """把一条结果的完整请求/响应组装成可打印的报文文本。"""
    req = r.get("request") or {}
    resp = r.get("response") or {}
    lines = [f"{r.get('method', '')} {r.get('url', '')}"]
    lines.append("\n[请求头]")
    lines.append(_fmt_headers(req.get("headers")))
    lines.append("[请求体]")
    lines.append(req.get("body") or "(空)")
    lines.append(f"\n[响应 {resp.get('status', r.get('status')) or ''}]")
    lines.append("[响应头]")
    lines.append(_fmt_headers(resp.get("headers")))
    lines.append("[响应体]")
    lines.append(resp.get("body") or "(空)")
    return "\n".join(lines)


def render_html(meta, conclusion=None):
    s = _summary()
    concl_html = ""
    if conclusion:
        items = "".join(f"<li>{html.escape(str(c))}</li>" for c in conclusion)
        concl_html = f'<div class="concl"><h2>测试结论</h2><ul>{items}</ul></div>'

    # 不通过明细（FAIL + PENDING）
    fail_rows = []
    for r in _RESULTS:
        if r["outcome"] in ("FAIL", "PENDING"):
            cls = {"FAIL": "fail", "PENDING": "pending"}.get(r["outcome"], "fail")
            label = _OUTCOME_LABEL.get(r["outcome"], r["outcome"])
            fail_rows.append(
                f"<tr class='{cls}'>"
                f"<td>{html.escape(str(r.get('case_id') or ''))}</td>"
                f"<td>{html.escape(str(r.get('name') or ''))}</td>"
                f"<td><span class='badge {cls}'>{html.escape(label)}</span></td>"
                f"<td class='error'>{html.escape(str(r.get('error') or ''))}</td>"
                f"</tr>"
            )
    fail_html = ""
    if fail_rows:
        fail_html = (
            '<div class="concl"><h2>不通过明细</h2>'
            '<table><thead><tr><th>用例ID</th><th>名称</th><th>结果</th><th>失败原因</th></tr></thead><tbody>'
            + "".join(fail_rows) +
            "</tbody></table></div>"
        )

    rows = []
    for i, r in enumerate(_RESULTS, 1):
        outcome = r["outcome"]
        cls = {"PASS": "pass", "PENDING": "pending", "FAIL": "fail", "SKIP": "skip"}.get(outcome, "fail")
        rows.append(
            f"<tr class='{cls}'>"
            f"<td>{i}</td>"
            f"<td>{html.escape(str(r.get('case_id') or ''))}</td>"
            f"<td>{html.escape(str(r.get('name') or ''))}</td>"
            f"<td>{html.escape(str(r.get('device_sn') or ''))}</td>"
            f"<td>{html.escape(str(r.get('model') or ''))}</td>"
            f"<td>{html.escape(str(r.get('method') or ''))}</td>"
            f"<td class='url'>{html.escape(str(r.get('url') or ''))}</td>"
            f"<td>{r.get('status') if r.get('status') is not None else ''}</td>"
            f"<td><span class='badge {cls}'>{html.escape(_OUTCOME_LABEL.get(outcome, outcome))}</span></td>"
            f"<td>{html.escape(str(r.get('duration') or ''))}</td>"
            f"<td class='error'>{html.escape(str(r.get('error') or ''))}</td>"
            f"<td><details><summary>报文</summary><pre>{html.escape(_build_message(r))}</pre></details></td>"
            f"</tr>"
        )
    devices = "、".join(meta.get("devices") or []) or "（未配置）"
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>API 测试报告</title><style>{_CSS}</style></head>
<body>
<h1>Dyness OpenAPI 测试报告</h1>
<div class="sub">生成时间 {html.escape(meta.get('generated_at') or '')}　|
base_url: {html.escape(meta.get('base_url') or '')}　|　设备: {html.escape(devices)}</div>
<div class="cards">
<div class="card"><div class="num">{s['total']}</div><div class="lbl">总用例</div></div>
<div class="card pass"><div class="num">{s['passed']}</div><div class="lbl">通过</div></div>
<div class="card pending"><div class="num">{s['pending']}</div><div class="lbl">待确认</div></div>
<div class="card fail"><div class="num">{s['failed']}</div><div class="lbl">不通过</div></div>
<div class="card skip"><div class="num">{s['skipped']}</div><div class="lbl">跳过</div></div>
<div class="card"><div class="num">{s['rate']}</div><div class="lbl">通过率</div></div>
</div>
{concl_html}
{fail_html}
<table><thead><tr>
<th>#</th><th>用例ID</th><th>名称</th><th>设备SN</th><th>机型</th><th>方法</th><th>URL</th><th>状态码</th><th>结果</th><th>耗时</th><th>结果说明</th><th>报文</th>
</tr></thead><tbody>
{chr(10).join(rows) if rows else '<tr><td colspan="12">无结果（collect-only 或未执行）</td></tr>'}
</tbody></table>
</body></html>"""


def write_reports(out_dir, meta, conclusion=None):
    """把结果写到 out_dir 下的 report_<时间戳>.html / .json。返回 (html_path, json_path)。

    conclusion 为可选的测试结论列表（每条一行），渲染进报告的「测试结论」区块。
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_path = out_dir / f"report_{ts}.html"
    json_path = out_dir / f"report_{ts}.json"
    html_path.write_text(render_html(meta, conclusion), encoding="utf-8")
    json_path.write_text(render_json(meta, conclusion), encoding="utf-8")
    return str(html_path), str(json_path)
