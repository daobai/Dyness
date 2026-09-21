# -*- coding: utf-8 -*-
"""生成 OTA/固件升级 API 测试数据 CSV。

基于 ems-device 系统的固件管理接口生成。
覆盖：固件列表查询 + 固件升级 + 固件下发 + 禁升名单管理。
运行：py -3 tests/api/gen_ota_cases.py
"""

import csv
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "data" / "api_ota.csv"
FIELDS = ["case_id", "name", "method", "path", "headers", "params", "body",
          "expected_status", "expected_code", "assertions", "description", "enabled",
          "models", "module", "func_module", "risk", "smoke"]

SN = "{{deviceSn}}"  # 模板变量

# 风险等级说明：
# - 空（safe）: 安全，查询类操作，默认执行
# - warning: 警告，会改变系统状态但可恢复，默认执行
# - danger: 危险，固件升级/下发等可能导致设备不可用的操作，需 --include-danger 才执行

# 危险接口列表（固件升级/下发类）
_DANGER_PATHS = {
    "/firmware/ota",                    # 运营端固件升级
    "/firmware/upgrade",                # 伙伴端/终端固件升级
    "/firmware/manager/issue",          # 固件下发
}

# 警告接口列表（删除/停用/禁升名单操作）
_WARNING_PATHS = {
    "/firmware/manager/delete",         # 固件删除
    "/firmware/manager/task/disable",   # 停用升级任务
    "/firmware/disable-upgrade/save",   # 禁升名单新增
    "/firmware/disable-upgrade/delete", # 禁升名单删除
}


def _get_risk(path):
    """根据接口路径判断风险等级。"""
    if path in _DANGER_PATHS:
        return "danger"
    if path in _WARNING_PATHS:
        return "warning"
    return ""


# 接口路径 -> 功能模块映射（OTA/固件管理 作为一级业务模块）
_FUNC_MODULE_MAP = {
    # 固件查询
    "/firmware/list": "OTA升级/固件列表",
    "/firmware/common/list": "OTA升级/固件列表",
    "/firmware/manager/list": "OTA升级/固件列表(运营端)",
    "/firmware/manager/detail": "OTA升级/固件详情",
    # 固件升级（危险）
    "/firmware/ota": "OTA升级/固件升级(运营端)",
    "/firmware/upgrade": "OTA升级/固件升级",
    "/firmware/upgrade/resultV3": "OTA升级/升级结果查询",
    "/firmware/ota/record/list": "OTA升级/升级记录",
    # 固件下发（危险）
    "/firmware/manager/issue": "OTA升级/固件下发",
    # 升级任务
    "/firmware/manager/task/page": "OTA升级/升级任务列表",
    "/firmware/manager/task/detail": "OTA升级/升级任务详情",
    "/firmware/manager/task/device/page": "OTA升级/任务设备列表",
    "/firmware/manager/task/disable": "OTA升级/停用升级任务",
    # 固件管理
    "/firmware/manager/insertOrUpdate": "OTA升级/新增固件",
    "/firmware/manager/delete": "OTA升级/删除固件",
    "/firmware/manager/enableSnList": "OTA升级/可下发设备列表",
    # 禁升名单
    "/firmware/disable-upgrade/page": "OTA升级/禁升名单",
    "/firmware/disable-upgrade/save": "OTA升级/禁升名单新增",
    "/firmware/disable-upgrade/delete": "OTA升级/禁升名单删除",
    "/firmware/disable-upgrade/import": "OTA升级/禁升名单导入",
    "/firmware/disable-upgrade/effective/list": "OTA升级/禁升名单查询",
    # 设备升级检查
    "/device/check/ota": "OTA升级/设备升级检查",
    "/device/check/upgrade": "OTA升级/设备升级检查",
    "/device/whetherCanOta": "OTA升级/设备升级检查",
    # ROM/电池类型查询
    "/firmware/getOtaAllRomType": "OTA升级/ROM类型",
    "/firmware/getOtaBatteryTypeList": "OTA升级/电池类型",
    "/firmware/latest/getCanUpgradeFirmwareVersion": "OTA升级/最新版本",
}


def _get_func_module(path):
    """根据接口路径推断功能模块。"""
    return _FUNC_MODULE_MAP.get(path, "OTA升级/其他")


def c(case_id, name, path, body, assertions, description, enabled="1",
      expected_code="200", risk="", smoke="0"):
    return {
        "case_id": case_id, "name": name, "method": "POST", "path": path,
        "headers": None, "params": None, "body": body,
        "expected_status": 200, "expected_code": expected_code, "assertions": assertions,
        "description": description, "enabled": enabled, "models": "",
        "module": "ota", "func_module": _get_func_module(path),
        "risk": risk or _get_risk(path), "smoke": smoke,
    }


CASES = [
    # ===== 固件查询类（安全）=====
    c("TC001", "固件列表查询", "/firmware/list",
      {"pageNum": 1, "pageSize": 20},
      "$.code == 200", "查询:固件列表", smoke="1"),
    c("TC002", "固件交集列表查询", "/firmware/common/list",
      {"pageNum": 1, "pageSize": 20},
      "$.code == 200", "查询:固件交集列表"),
    c("TC003", "固件详情查询", "/firmware/manager/detail",
      {"id": "1"},
      "$.code == 200", "查询:固件详情"),
    c("TC004", "ROM类型查询", "/firmware/getOtaAllRomType",
      {},
      "$.code == 200", "查询:ROM类型列表"),
    c("TC005", "电池类型查询", "/firmware/getOtaBatteryTypeList",
      {},
      "$.code == 200", "查询:电池类型列表"),
    c("TC006", "最新固件版本查询", "/firmware/latest/getCanUpgradeFirmwareVersion",
      {"deviceSn": SN},
      "$.code == 200", "查询:最新可升级版本"),

    # ===== 升级记录查询（安全）=====
    c("TC011", "升级记录列表", "/firmware/ota/record/list",
      {"pageNum": 1, "pageSize": 20, "deviceSn": SN},
      "$.code == 200", "查询:升级记录"),
    c("TC012", "升级任务列表", "/firmware/manager/task/page",
      {"pageNum": 1, "pageSize": 20},
      "$.code == 200", "查询:升级任务列表"),
    c("TC013", "升级任务详情", "/firmware/manager/task/detail",
      {"taskId": "1"},
      "$.code == 200", "查询:升级任务详情"),
    c("TC014", "任务设备列表", "/firmware/manager/task/device/page",
      {"taskId": "1", "pageNum": 1, "pageSize": 20},
      "$.code == 200", "查询:任务设备列表"),

    # ===== 设备升级检查（安全）=====
    c("TC021", "设备OTA检查", "/device/check/ota",
      {"deviceSn": SN},
      "$.code == 200", "查询:设备是否有OTA固件"),
    c("TC022", "设备升级检查", "/device/check/upgrade",
      {"deviceSn": SN},
      "$.code == 200", "查询:设备是否可升级"),
    c("TC023", "设备是否可OTA", "/device/whetherCanOta",
      {"deviceSn": SN},
      "$.code == 200", "查询:设备是否可OTA"),

    # ===== 禁升名单查询（安全）=====
    c("TC031", "禁升名单分页查询", "/firmware/disable-upgrade/page",
      {"pageNum": 1, "pageSize": 20},
      "$.code == 200", "查询:禁升名单"),
    c("TC032", "禁升名单有效SN查询", "/firmware/disable-upgrade/effective/list",
      {"deviceSn": SN},
      "$.code == 200", "查询:有效禁升SN"),
    c("TC033", "可下发设备列表", "/firmware/manager/enableSnList",
      {"firmwareId": "1"},
      "$.code == 200", "查询:可下发设备列表"),

    # ===== 固件升级（危险 - danger）=====
    c("TC101", "运营端固件升级", "/firmware/ota",
      {"deviceSn": SN, "firmwareId": "1"},
      "$.code == 200", "下发:固件升级(运营端)"),
    c("TC102", "伙伴端固件升级", "/firmware/upgrade",
      {"deviceSn": SN, "firmwareId": "1"},
      "$.code == 200", "下发:固件升级(伙伴端)"),
    c("TC103", "固件升级结果查询V3", "/firmware/upgrade/resultV3",
      {"deviceSn": SN},
      "$.code == 200", "查询:升级结果V3"),

    # ===== 固件下发（危险 - danger）=====
    c("TC111", "固件统一下发", "/firmware/manager/issue",
      {"firmwareId": "1", "deviceSnList": [SN]},
      "$.code == 200", "下发:固件统一下发"),

    # ===== 固件管理（警告 - warning）=====
    c("TC121", "固件删除", "/firmware/manager/delete",
      {"id": "99999"},
      "$.code == 200", "下发:删除固件"),
    c("TC122", "停用升级任务", "/firmware/manager/task/disable",
      {"taskId": "99999"},
      "$.code == 200", "下发:停用升级任务"),

    # ===== 禁升名单管理（警告 - warning）=====
    c("TC131", "禁升名单新增", "/firmware/disable-upgrade/save",
      {"deviceSn": SN, "firmwareId": "1", "reason": "测试"},
      "$.code == 200", "下发:禁升名单新增"),
    c("TC132", "禁升名单删除", "/firmware/disable-upgrade/delete",
      {"id": "99999"},
      "$.code == 200", "下发:禁升名单删除"),

    # ===== 异常参数测试 =====
    c("TC201", "固件列表-pageSize越界", "/firmware/list",
      {"pageNum": 1, "pageSize": 1001},
      "", "边界外:pageSize=1001"),
    c("TC202", "固件升级-缺deviceSn", "/firmware/ota",
      {"firmwareId": "1"},
      "", "必填缺失:缺deviceSn"),
    c("TC203", "固件升级-deviceSn不存在", "/firmware/ota",
      {"deviceSn": "NOT_EXIST_SN_000", "firmwareId": "1"},
      "", "异常:deviceSn不存在"),
    c("TC204", "固件下发-缺firmwareId", "/firmware/manager/issue",
      {"deviceSnList": [SN]},
      "", "必填缺失:缺firmwareId"),
    c("TC205", "固件下发-空设备列表", "/firmware/manager/issue",
      {"firmwareId": "1", "deviceSnList": []},
      "", "特殊参数:空设备列表"),
]


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for case in CASES:
            row = dict(case)
            for k in ("headers", "params", "body"):
                v = row.get(k)
                row[k] = "" if v is None else json.dumps(v, ensure_ascii=False, separators=(",", ":"))
            w.writerow(row)
    print(f"已生成 {len(CASES)} 条 OTA 用例 -> {OUT}")

    # 统计风险等级
    risk_count = {"": 0, "warning": 0, "danger": 0}
    for case in CASES:
        risk = case.get("risk") or ""
        if risk in risk_count:
            risk_count[risk] += 1
        else:
            risk_count[""] += 1
    print(f"  安全(safe): {risk_count['']} 条")
    print(f"  警告(warning): {risk_count['warning']} 条")
    print(f"  危险(danger): {risk_count['danger']} 条")


if __name__ == "__main__":
    main()
