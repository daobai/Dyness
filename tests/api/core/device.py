# -*- coding: utf-8 -*-
"""机型识别 + 用例/断言按机型裁剪。

- 探测入口：GetDeviceList（一次请求拿全部设备的系列名 deviceModel，见接口文档 L414/420/426）
- 归一化：models.yaml 的「别名 + 硬件型号前缀」两级映射
- 未知机型不抛异常，返回原值：该设备只跑通用用例、跳过机型受限项
"""

import json
import re
import time
from pathlib import Path

import requests
import yaml

from core.sign import sign_request

_MODELS_FILE = Path(__file__).resolve().parent.parent / "data" / "models.yaml"
_MODELS_CACHE = None


def _load_models():
    """读取 models.yaml（带缓存）。"""
    global _MODELS_CACHE
    if _MODELS_CACHE is None:
        if _MODELS_FILE.exists():
            _MODELS_CACHE = yaml.safe_load(_MODELS_FILE.read_text(encoding="utf-8")) or {}
        else:
            _MODELS_CACHE = {}
    return _MODELS_CACHE


def normalize_device_list(raw):
    """把 device_sn 的任意形态(str/list/逗号分隔)归一为去重保序的 SN 列表。"""
    if raw is None or raw == "":
        return []
    if isinstance(raw, (list, tuple)):
        items = [str(x).strip() for x in raw]
    else:
        items = [x.strip() for x in str(raw).split(",")]
    return list(dict.fromkeys(x for x in items if x))


def normalize_model(raw, models=None):
    """原始 deviceModel -> 标准系列名 AquaVolt/AquaVolt_LV/SolarCube；未知返回原值。"""
    if not raw:
        return None
    raw = str(raw).strip()
    if not raw:
        return None
    models = models or _load_models()

    # 1) 系列别名精确匹配（忽略大小写）
    aliases = models.get("aliases") or {}
    for canonical, names in aliases.items():
        if raw.lower() in (n.lower() for n in names):
            return canonical

    # 2) 硬件型号前缀匹配（如 D3.6LXC-5 -> AquaVolt）
    hardware = models.get("hardware_models") or {}
    for prefix, canonical in hardware.items():
        if raw.lower().startswith(prefix.lower()):
            return canonical

    # 3) 兜底返回原值（未知机型：通用用例仍跑，机型受限项跳过）
    return raw


def parse_models(value):
    """'AquaVolt,SolarCube' -> {'AquaVolt','SolarCube'}；空/None -> None(全机型)。"""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    result = set()
    for item in s.split(","):
        item = item.strip()
        if not item:
            continue
        result.add(normalize_model(item) or item)
    return result or None


def model_matches(case_models, device_model):
    """case_models 为空 -> True；device_model 未知 -> False(保守跳过)。"""
    if not case_models:
        return True
    if not device_model:
        return False
    return device_model in case_models


_ASSERT_PREFIX_RE = re.compile(r"^\s*\[([^\]]*)\]\s*(.*)$", re.S)


def split_assertion(expr):
    """'[A,B] $.x exists' -> ({'A','B'}, '$.x exists')；无前缀 -> (None, expr)。"""
    m = _ASSERT_PREFIX_RE.match(expr)
    if m:
        return parse_models(m.group(1)), m.group(2).strip()
    return None, expr.strip()


def filter_assertions(assertions, device_model):
    """按机型裁剪断言：保留无前缀的 + 前缀含当前机型的。"""
    if not assertions:
        return assertions
    kept = []
    for expr in assertions.split(";"):
        expr = expr.strip()
        if not expr:
            continue
        models, rest = split_assertion(expr)
        if model_matches(models, device_model):
            kept.append(rest)
    return "; ".join(kept)


def filter_body(body, device_model):
    """按机型裁剪下发 body：字段名可带 `[机型]` 前缀，不匹配当前机型的字段剔除（递归）。"""
    if isinstance(body, dict):
        result = {}
        for k, v in body.items():
            models, key = split_assertion(k)
            if model_matches(models, device_model):
                result[key] = filter_body(v, device_model)
        return result
    if isinstance(body, list):
        return [filter_body(x, device_model) for x in body]
    return body


class ProbeError(RuntimeError):
    """机型探测失败。"""


def _build_url(path, base_url):
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return base_url.rstrip("/") + "/" + path.lstrip("/")


def _post_json(cfg, path, body):
    body_str = json.dumps(body, sort_keys=True, separators=(",", ":"))
    headers = sign_request(cfg["app_id"], cfg["app_secret"], "POST", path, body_str)
    resp = requests.post(
        _build_url(path, cfg["base_url"]), data=body_str,
        headers=headers, timeout=cfg.get("timeout", 30),
    )
    if resp.status_code != 200:
        raise ProbeError(f"{path} 返回 {resp.status_code}: {resp.text[:200]}")
    return resp


def _fetch_device_list(cfg):
    """分页调 GetDeviceList，返回账号下全部设备的原始列表。"""
    devices = []
    page_num, page_size = 1, 200
    while True:
        resp = _post_json(cfg, "/v2/GetDeviceList", {"pageNum": page_num, "pageSize": page_size})
        try:
            data = resp.json().get("data") or []
        except ValueError:
            data = []
        if isinstance(data, list):
            devices.extend(data)
        if len(data) < page_size:
            break
        page_num += 1
        time.sleep(cfg.get("request_interval", 0.6))  # 接口限流 ≤2次/秒，翻页留间隔
    return devices


def _fetch_hardware_model(cfg, sn):
    """调 GetDeviceInfBySN 拿硬件型号（deviceModel 是硬件型号，如 D3.6LXC-5）。"""
    try:
        resp = _post_json(cfg, "/v2/GetDeviceInfBySN", {"deviceSn": sn})
        data = resp.json().get("data") or {}
        return data.get("deviceModel")
    except (ProbeError, ValueError):
        return None


def discover_devices(cfg):
    """探测设备列表 -> [{"deviceSn": str, "model": str|None, "hardware": str|None}, ...]。

    - 机型（系列名）来自 GetDeviceList 的 deviceModel；config.model 可手动指定兜底。
    - 硬件型号来自 GetDeviceInfBySN 的 deviceModel（拿不到则为 None）。
    - 配置了 device_sn 列表则按其过滤；未配置则返回账号下全部设备；整体失败返回 []。
    """
    device_sns = normalize_device_list(cfg.get("device_sn"))
    manual_model = normalize_model(cfg.get("model"))  # config 手动指定机型（兜底）

    try:
        raw_devices = _fetch_device_list(cfg)
    except ProbeError:
        raw_devices = []

    by_sn = {}
    for d in raw_devices:
        if not isinstance(d, dict):
            continue
        sn = str(d.get("deviceSn") or "").strip()
        if not sn:
            continue
        by_sn[sn] = {"model": normalize_model(d.get("deviceModel")), "hardware": None}

    # 逐台拿硬件型号（失败不影响机型判断）
    for sn in by_sn:
        by_sn[sn]["hardware"] = _fetch_hardware_model(cfg, sn)
        time.sleep(cfg.get("request_interval", 0.6))  # 限流间隔

    def build(sn):
        info = by_sn.get(sn) or {}
        return {
            "deviceSn": sn,
            "model": manual_model or info.get("model"),
            "hardware": info.get("hardware"),
        }

    if device_sns:
        return [build(sn) for sn in device_sns]
    return [build(sn) for sn in by_sn]
