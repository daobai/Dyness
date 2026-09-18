# -*- coding: utf-8 -*-
"""用例加载与请求构造工具。"""

import csv
import json

from core.device import parse_models


def _json_or_none(s):
    s = (s or "").strip()
    if not s:
        return None
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 字段解析失败: {s!r} -> {e}")


def resolve_vars(obj, vars_map):
    """递归替换字符串值里的 `{{var}}` 模板变量。"""
    if isinstance(obj, str):
        for k, v in vars_map.items():
            obj = obj.replace("{{" + k + "}}", str(v))
        return obj
    if isinstance(obj, dict):
        return {k: resolve_vars(v, vars_map) for k, v in obj.items()}
    if isinstance(obj, list):
        return [resolve_vars(v, vars_map) for v in obj]
    return obj


def load_cases(csv_file):
    """读取 CSV，返回用例字典列表；跳过注释行和 enabled=0 的行。"""
    if not csv_file.exists():
        return []

    with open(csv_file, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    cases = []
    for row in rows:
        case_id = (row.get("case_id") or "").strip()
        if not case_id or case_id.startswith("#"):
            continue
        enabled = (row.get("enabled") or "1").strip().lower()
        if enabled in ("0", "no", "false", "off"):
            continue
        cases.append({
            "case_id": case_id,
            "name": (row.get("name") or "").strip(),
            "method": (row.get("method") or "GET").strip().upper(),
            "path": (row.get("path") or "").strip(),
            "headers": _json_or_none(row.get("headers")),
            "params": _json_or_none(row.get("params")),
            "body": _json_or_none(row.get("body")),
            "expected_status": int((row.get("expected_status") or "200").strip()),
            "expected_code": (row.get("expected_code") or "200").strip(),
            "assertions": (row.get("assertions") or "").strip(),
            "description": (row.get("description") or "").strip(),
            "models": parse_models(row.get("models")),
        })
    return cases


def build_url(path, base_url):
    """path 支持相对路径（拼 base_url）或完整 URL。"""
    if path.startswith("http://") or path.startswith("https://"):
        return path
    if not base_url:
        raise AssertionError(
            "base_url 未配置且 path 不是完整 URL，请用 --base-url 或 config.yaml 配置"
        )
    return base_url.rstrip("/") + "/" + path.lstrip("/")
