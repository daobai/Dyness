# -*- coding: utf-8 -*-
"""生成 Junior Box API 测试数据 CSV。

基于 docs/interfaces 下 Junior Box 接口文档生成，共 7 个接口。
覆盖：正常流 + 异常(deviceSn 不存在/空/缺失) + 分页越界 + 基础设置/分时设置参数边界值/越界/枚举/必填缺失。
运行：py -3 tests/api/gen_juniorbox_cases.py
"""

import csv
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "data" / "api_juniorbox.csv"
FIELDS = ["case_id", "name", "method", "path", "headers", "params", "body",
          "expected_status", "expected_code", "assertions", "description", "enabled",
          "models", "module", "smoke"]

SN = "{{deviceSn}}"
BAD_SN = "NOT_EXIST_SN_000"


def c(case_id, name, path, body, assertions, description, enabled="1", models="",
      expected_code="200", module="juniorbox", smoke="0"):
    return {
        "case_id": case_id, "name": name, "method": "POST", "path": path,
        "headers": None, "params": None, "body": body,
        "expected_status": 200, "expected_code": expected_code, "assertions": assertions,
        "description": description, "enabled": enabled, "models": models,
        "module": module, "smoke": smoke,
    }


def _wg(power="320", state="1", mode="0", batteryWorkGroup=1):
    """生成一组分时工作策略。"""
    return [{"batteryWorkGroup": batteryWorkGroup, "state": state, "mode": mode,
             "startTime": "08:00", "endTime": "18:00", "power": power, "week": "0,1,2,3,4"}]


CASES = [
    # ===== 查询类（核心查询 smoke=1）=====
    c("TC001", "JuniorBox-设备信息查询", "/v2/GetDeviceInfBySN",
      {"deviceSn": SN},
      "$.code == 200;$.data.hostDeviceName exists;$.data.hostVersion exists",
      "查询类:设备信息", smoke="1"),
    c("TC002", "JuniorBox-实时运行数据", "/v2/GetRealTimeDataBySN",
      {"deviceSn": SN},
      "$.code == 200;$.data.batteryInfo.soc exists;$.data.batteryInfo.batteryVoltage exists;$.data.batteryInfo.soh exists",
      "查询类:实时运行数据", smoke="1"),
    c("TC003", "JuniorBox-故障信息查询", "/v2/GetAlarmInfBySN",
      {"deviceSn": SN, "pageNum": 1, "pageSize": 200},
      "$.code == 200;$.data.total exists;$.data.list exists",
      "查询类:故障信息", smoke="1"),

    # ===== 控制类：查询 + 下发 =====
    c("TC004", "JuniorBox-基础设置查询", "/v2/GetBaseSetting",
      {"deviceSn": SN},
      "$.code == 200;$.data.workMode exists;$.data.powerLimit exists;$.data.dischargeDepth exists",
      "控制类:基础设置查询"),
    c("TC005", "JuniorBox-基础设置下发", "/v2/SetBaseSetting",
      {"deviceSn": SN, "workMode": "3", "powerLimit": "100", "dischargeDepth": "20"},
      "$.code == 200", "下发:基础设置(改设备,慎用)"),
    c("TC006", "JuniorBox-分时设置查询", "/v2/GetWorkModeSetting",
      {"deviceSn": SN}, "$.code == 200;$.data.workGroups exists", "控制类:分时设置查询"),
    c("TC007", "JuniorBox-分时设置下发", "/v2/SetWorkModeSetting",
      {"deviceSn": SN, "workGroups": _wg()},
      "$.code == 200", "下发:分时设置(改设备,慎用)"),

    # ===== 异常：deviceSn 不存在 / 空 / 缺失（预期 500）=====
    c("TC101", "JuniorBox-设备信息-deviceSn不存在", "/v2/GetDeviceInfBySN",
      {"deviceSn": BAD_SN}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC102", "JuniorBox-设备信息-deviceSn为空", "/v2/GetDeviceInfBySN",
      {"deviceSn": ""}, "", "特殊参数:deviceSn空字符串", expected_code="500"),
    c("TC103", "JuniorBox-实时数据-deviceSn不存在", "/v2/GetRealTimeDataBySN",
      {"deviceSn": BAD_SN}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC104", "JuniorBox-故障信息-deviceSn不存在", "/v2/GetAlarmInfBySN",
      {"deviceSn": BAD_SN}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC105", "JuniorBox-基础设置查询-deviceSn不存在", "/v2/GetBaseSetting",
      {"deviceSn": BAD_SN}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC106", "JuniorBox-基础设置下发-deviceSn不存在", "/v2/SetBaseSetting",
      {"deviceSn": BAD_SN, "workMode": "3", "powerLimit": "100", "dischargeDepth": "20"},
      "", "异常:deviceSn不存在", expected_code="500"),
    c("TC107", "JuniorBox-分时设置查询-deviceSn不存在", "/v2/GetWorkModeSetting",
      {"deviceSn": BAD_SN}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC108", "JuniorBox-分时设置下发-deviceSn不存在", "/v2/SetWorkModeSetting",
      {"deviceSn": BAD_SN, "workGroups": _wg()}, "", "异常:deviceSn不存在", expected_code="500"),

    # ===== 分页越界（GetAlarmInfBySN）=====
    c("TC121", "JuniorBox-故障信息-pageSize越界", "/v2/GetAlarmInfBySN",
      {"deviceSn": SN, "pageNum": 1, "pageSize": 201}, "", "边界外:pageSize=201(最大200)", expected_code="500"),
    c("TC122", "JuniorBox-故障信息-pageSize为0", "/v2/GetAlarmInfBySN",
      {"deviceSn": SN, "pageNum": 1, "pageSize": 0}, "", "边界外:pageSize=0", expected_code="500"),
    c("TC123", "JuniorBox-故障信息-pageSize非数字", "/v2/GetAlarmInfBySN",
      {"deviceSn": SN, "pageNum": 1, "pageSize": "abc"}, "", "特殊参数:pageSize类型错误", expected_code="500"),

    # ===== 基础设置：workMode 枚举 + dischargeDepth 边界 =====
    c("TC131", "JuniorBox-工作模式=自发自用", "/v2/SetBaseSetting",
      {"deviceSn": SN, "workMode": "0", "powerLimit": "100", "dischargeDepth": "20"},
      "$.code == 200", "枚举值:workMode=0(自发自用)", "200"),
    c("TC132", "JuniorBox-工作模式=离网", "/v2/SetBaseSetting",
      {"deviceSn": SN, "workMode": "1", "powerLimit": "100", "dischargeDepth": "20"},
      "$.code == 200", "枚举值:workMode=1(离网)", "200"),
    c("TC133", "JuniorBox-工作模式=经济", "/v2/SetBaseSetting",
      {"deviceSn": SN, "workMode": "3", "powerLimit": "100", "dischargeDepth": "20"},
      "$.code == 200", "枚举值:workMode=3(经济)", "200"),
    c("TC134", "JuniorBox-工作模式=电池优先", "/v2/SetBaseSetting",
      {"deviceSn": SN, "workMode": "6", "powerLimit": "100", "dischargeDepth": "20"},
      "$.code == 200", "枚举值:workMode=6(电池优先)", "200"),
    c("TC135", "JuniorBox-工作模式非法", "/v2/SetBaseSetting",
      {"deviceSn": SN, "workMode": "9", "powerLimit": "100", "dischargeDepth": "20"},
      "", "边界外:workMode=9(枚举0/1/3/6)", expected_code="500"),
    c("TC136", "JuniorBox-放电深度最小值", "/v2/SetBaseSetting",
      {"deviceSn": SN, "workMode": "3", "powerLimit": "100", "dischargeDepth": "0"},
      "$.code == 200", "边界值:dischargeDepth=0(最小)", "200"),
    c("TC137", "JuniorBox-放电深度最大值", "/v2/SetBaseSetting",
      {"deviceSn": SN, "workMode": "3", "powerLimit": "100", "dischargeDepth": "100"},
      "$.code == 200", "边界值:dischargeDepth=100(最大)", "200"),
    c("TC138", "JuniorBox-放电深度越界", "/v2/SetBaseSetting",
      {"deviceSn": SN, "workMode": "3", "powerLimit": "100", "dischargeDepth": "101"},
      "", "边界外:dischargeDepth=101(最大100)", expected_code="500"),
    c("TC139", "JuniorBox-基础设置缺workMode", "/v2/SetBaseSetting",
      {"deviceSn": SN, "powerLimit": "100", "dischargeDepth": "20"},
      "", "必填缺失:缺workMode", expected_code="500"),

    # ===== 分时设置：power 边界 + 枚举 =====
    c("TC151", "JuniorBox-分时功率最小值", "/v2/SetWorkModeSetting",
      {"deviceSn": SN, "workGroups": _wg(power="0")}, "$.code == 200", "边界值:power=0(最小)", "200"),
    c("TC152", "JuniorBox-分时功率最大值", "/v2/SetWorkModeSetting",
      {"deviceSn": SN, "workGroups": _wg(power="800")}, "$.code == 200", "边界值:power=800(最大)", "200"),
    c("TC153", "JuniorBox-分时功率越界", "/v2/SetWorkModeSetting",
      {"deviceSn": SN, "workGroups": _wg(power="801")}, "", "边界外:power=801(最大800)", expected_code="500"),
    c("TC154", "JuniorBox-分组号越界", "/v2/SetWorkModeSetting",
      {"deviceSn": SN, "workGroups": _wg(batteryWorkGroup=5)}, "", "边界外:batteryWorkGroup=5(最大4)", expected_code="500"),
    c("TC155", "JuniorBox-分组状态非法", "/v2/SetWorkModeSetting",
      {"deviceSn": SN, "workGroups": _wg(state="2")}, "", "边界外:state=2(枚举0/1)", expected_code="500"),
    c("TC156", "JuniorBox-分组模式非法", "/v2/SetWorkModeSetting",
      {"deviceSn": SN, "workGroups": _wg(mode="2")}, "", "边界外:mode=2(枚举0/1)", expected_code="500"),
    c("TC157", "JuniorBox-分时设置缺workGroups", "/v2/SetWorkModeSetting",
      {"deviceSn": SN}, "", "必填缺失:缺workGroups", expected_code="500"),
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
    print(f"已生成 {len(CASES)} 条 Junior Box 用例 -> {OUT}")


if __name__ == "__main__":
    main()
