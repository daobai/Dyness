# -*- coding: utf-8 -*-
"""测试环境备份与恢复：下发测试前备份设备可下发参数，测试后恢复，防止参数被改导致设备损坏。"""

import json
import time
from pathlib import Path

from core.device import _post_json

# 查询(备份) -> 下发(恢复) 对应关系
CONTROL_PAIRS = [
    ("/v2/GetBaseSetting", "/v2/SetBaseSetting"),
    ("/v2/GetWorkModeSetting", "/v2/SetWorkModeSetting"),
    ("/v2/GetBatterySetting", "/v2/SetBatterySetting"),
    ("/v2/GetLoadControlSetting", "/v2/SetLoadControlSetting"),
    ("/v2/GetPeakControlSetting", "/v2/SetPeakControlSetting"),
    ("/v2/GetAdvancedSetting", "/v2/SetAdvancedSetting"),
]

# 各下发接口允许恢复的字段（查询返回的只读/预留字段下发时剔除；不在表内=用全部 data）
_RESTORE_FIELDS = {
    "/v2/SetAdvancedSetting": [
        "gridPowerLimitGroup", "backupPowerSwitch", "pvConnectMode",
        "extCtMeterGroup", "isoSetting", "acCouplingEnable",
        "powerLevelSetting", "groundDetectionEnable",
        "offGridOutputSwitch", "offGridVoltageLevel",
        "sleepFunctionSwitch", "sleepDetectionLevel",
    ],
}


def _backup_one(cfg, sn):
    """查询一台设备的 6 类可下发参数，返回 {get_path: data}。"""
    data = {}
    for get_path, _set_path in CONTROL_PAIRS:
        try:
            resp = _post_json(cfg, get_path, {"deviceSn": sn})
            data[get_path] = resp.json().get("data")
        except Exception as e:
            data[get_path] = {"__error__": str(e)}
        time.sleep(cfg.get("request_interval", 0.6))  # 限流间隔
    return data


def _restore_one(cfg, sn, data):
    """用备份 data 恢复一台设备，返回 [(set_path, 结果, 错误信息), ...]。"""
    results = []
    for get_path, set_path in CONTROL_PAIRS:
        raw = data.get(get_path)
        if not raw or not isinstance(raw, dict) or "__error__" in raw:
            results.append((set_path, "skip", ""))
            continue
        allowed = _RESTORE_FIELDS.get(set_path)
        if allowed is not None:
            body = {k: v for k, v in raw.items() if k in allowed}
        else:
            body = dict(raw)
        if not body:
            results.append((set_path, "skip", ""))
            continue
        try:
            _post_json(cfg, set_path, {"deviceSn": sn, **body})
            results.append((set_path, "ok", ""))
        except Exception as e:
            results.append((set_path, "fail", str(e)))
        time.sleep(cfg.get("request_interval", 0.6))  # 限流间隔
    return results


def backup_devices(cfg, devices, backup_dir):
    """备份每台设备的参数到 backup_dir/{sn}.json。"""
    backup_dir = Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    for d in devices:
        sn = d.get("deviceSn")
        if not sn:
            continue
        payload = {
            "deviceSn": sn,
            "model": d.get("model"),
            "hardware": d.get("hardware"),
            "backup_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "data": _backup_one(cfg, sn),
        }
        (backup_dir / f"{sn}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8",
        )


def restore_devices(cfg, devices, backup_dir):
    """从 backup_dir 读备份并恢复每台设备，返回 [(sn, 结果, 明细), ...]。"""
    backup_dir = Path(backup_dir)
    summary = []
    for d in devices:
        sn = d.get("deviceSn")
        f = backup_dir / f"{sn}.json"
        if not f.exists():
            summary.append((sn, "no-backup", []))
            continue
        try:
            payload = json.loads(f.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            summary.append((sn, "bad-file", []))
            continue
        results = _restore_one(cfg, sn, payload.get("data") or {})
        failed = [r for r in results if r[0] == "fail"]
        summary.append((sn, "ok" if not failed else "partial", results))
    return summary
