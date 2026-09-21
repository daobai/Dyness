# -*- coding: utf-8 -*-
"""生成低压电池（BMS 电池系统）API 测试数据 CSV。

基于 docs/interfaces 下低压电池（Low-voltage Battery）接口文档生成，共 6 个接口。
覆盖：正常流 + 异常(deviceSn 不存在/空/缺失) + 分页越界 + 电池加热参数边界值/越界/枚举/温差约束。
运行：py -3 tests/api/gen_lowvoltage_cases.py
"""

import csv
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "data" / "api_lowvoltage.csv"
FIELDS = ["case_id", "name", "method", "path", "headers", "params", "body",
          "expected_status", "expected_code", "assertions", "description", "enabled",
          "models", "module", "smoke"]

SN = "{{deviceSn}}"
BAD_SN = "NOT_EXIST_SN_000"


def c(case_id, name, path, body, assertions, description, enabled="1", models="",
      expected_code="200", module="lowvoltage", smoke="0"):
    return {
        "case_id": case_id, "name": name, "method": "POST", "path": path,
        "headers": None, "params": None, "body": body,
        "expected_status": 200, "expected_code": expected_code, "assertions": assertions,
        "description": description, "enabled": enabled, "models": models,
        "module": module, "smoke": smoke,
    }


def _hp(status="1", tempMin="10", tempMax="20", startTime="08:30", endTime="10:30", weekInfo="0,1,2,3,4"):
    """生成一组电池加热时段参数。"""
    return [{"status": status, "startTime": startTime, "endTime": endTime,
             "tempMin": tempMin, "tempMax": tempMax, "weekInfo": weekInfo}]


CASES = [
    # ===== 查询类（核心查询 smoke=1）=====
    c("TC001", "低压电池-设备信息查询", "/v2/GetDeviceInfBySN",
      {"deviceSn": SN},
      "$.code == 200;$.data.hostDeviceName exists;$.data.hostSoftwareVersion exists",
      "查询类:设备信息", smoke="1"),
    c("TC002", "低压电池-实时运行数据", "/v2/GetRealTimeDataBySN",
      {"deviceSn": SN},
      "$.code == 200;$.data.batteryInfo.soc exists;$.data.batteryInfo.batteryVoltage exists;$.data.batteryInfo.soh exists",
      "查询类:实时运行数据", smoke="1"),
    c("TC003", "低压电池-故障信息查询", "/v2/GetAlarmInfBySN",
      {"deviceSn": SN, "pageNum": 1, "pageSize": 200},
      "$.code == 200;$.data.total exists;$.data.list exists",
      "查询类:故障信息", smoke="1"),
    c("TC004", "低压电池-并机信息查询", "/v2/GetParallelInfBySN",
      {"deviceSn": SN},
      "$.code == 200;$.data.parallelPackSn exists;$.data.parallelPackSoc exists;$.data.parallelPackVoltage exists",
      "查询类:并机信息", smoke="1"),

    # ===== 控制类：查询 + 下发 =====
    c("TC005", "低压电池-电池加热查询", "/v2/GetBatterySetting",
      {"deviceSn": SN}, "$.code == 200;$.data.heatingPeriodList exists", "控制类:电池加热查询"),
    c("TC006", "低压电池-电池加热下发", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp()},
      "$.code == 200", "下发:电池加热(改设备,慎用)"),

    # ===== 异常：deviceSn 不存在 / 空 / 缺失（预期 500）=====
    c("TC101", "低压电池-设备信息-deviceSn不存在", "/v2/GetDeviceInfBySN",
      {"deviceSn": BAD_SN}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC102", "低压电池-设备信息-deviceSn为空", "/v2/GetDeviceInfBySN",
      {"deviceSn": ""}, "", "特殊参数:deviceSn空字符串", expected_code="500"),
    c("TC103", "低压电池-设备信息-缺deviceSn", "/v2/GetDeviceInfBySN",
      {}, "", "必填缺失:缺deviceSn", expected_code="500"),
    c("TC104", "低压电池-实时数据-deviceSn不存在", "/v2/GetRealTimeDataBySN",
      {"deviceSn": BAD_SN}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC105", "低压电池-实时数据-deviceSn为空", "/v2/GetRealTimeDataBySN",
      {"deviceSn": ""}, "", "特殊参数:deviceSn空字符串", expected_code="500"),
    c("TC106", "低压电池-故障信息-deviceSn不存在", "/v2/GetAlarmInfBySN",
      {"deviceSn": BAD_SN}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC107", "低压电池-并机信息-deviceSn不存在", "/v2/GetParallelInfBySN",
      {"deviceSn": BAD_SN}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC108", "低压电池-并机信息-deviceSn为空", "/v2/GetParallelInfBySN",
      {"deviceSn": ""}, "", "特殊参数:deviceSn空字符串", expected_code="500"),
    c("TC109", "低压电池-电池加热查询-deviceSn不存在", "/v2/GetBatterySetting",
      {"deviceSn": BAD_SN}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC110", "低压电池-电池加热下发-deviceSn不存在", "/v2/SetBatterySetting",
      {"deviceSn": BAD_SN, "heatingPeriodList": _hp()}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC111", "低压电池-电池加热下发-缺deviceSn", "/v2/SetBatterySetting",
      {"heatingPeriodList": _hp()}, "", "必填缺失:缺deviceSn", expected_code="500"),

    # ===== 分页越界（GetAlarmInfBySN）=====
    c("TC121", "低压电池-故障信息-pageSize越界", "/v2/GetAlarmInfBySN",
      {"deviceSn": SN, "pageNum": 1, "pageSize": 201}, "", "边界外:pageSize=201(最大200)", expected_code="500"),
    c("TC122", "低压电池-故障信息-pageSize为0", "/v2/GetAlarmInfBySN",
      {"deviceSn": SN, "pageNum": 1, "pageSize": 0}, "", "边界外:pageSize=0", expected_code="500"),
    c("TC123", "低压电池-故障信息-pageSize非数字", "/v2/GetAlarmInfBySN",
      {"deviceSn": SN, "pageNum": 1, "pageSize": "abc"}, "", "特殊参数:pageSize类型错误", expected_code="500"),

    # ===== 电池加热参数：枚举 / 边界值 / 越界 / 约束 =====
    c("TC131", "低压电池-加热开关=关", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(status="0")}, "$.code == 200", "枚举值:status=0(关)", "200"),
    c("TC132", "低压电池-加热开关=开", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(status="1")}, "$.code == 200", "枚举值:status=1(开)", "200"),
    c("TC133", "低压电池-加热开关非法", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(status="2")}, "", "边界外:status=2(枚举0/1)", expected_code="500"),
    c("TC134", "低压电池-温度下限最小值", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(tempMin="10")}, "$.code == 200", "边界值:tempMin=10(最小)", "200"),
    c("TC135", "低压电池-温度下限最大值", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(tempMin="15", tempMax="20")}, "$.code == 200", "边界值:tempMin=15(最大)", "200"),
    c("TC136", "低压电池-温度下限越界小", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(tempMin="9")}, "", "边界外:tempMin=9(最小10-1)", expected_code="500"),
    c("TC137", "低压电池-温度下限越界大", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(tempMin="16", tempMax="20")}, "", "边界外:tempMin=16(最大15+1)", expected_code="500"),
    c("TC138", "低压电池-温度上限最小值", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(tempMin="10", tempMax="15")}, "$.code == 200", "边界值:tempMax=15(最小)", "200"),
    c("TC139", "低压电池-温度上限最大值", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(tempMax="20")}, "$.code == 200", "边界值:tempMax=20(最大)", "200"),
    c("TC140", "低压电池-温度上限越界小", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(tempMin="10", tempMax="14")}, "", "边界外:tempMax=14(最小15-1)", expected_code="500"),
    c("TC141", "低压电池-温度上限越界大", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(tempMax="21")}, "", "边界外:tempMax=21(最大20+1)", expected_code="500"),
    c("TC142", "低压电池-加热温差不足5度", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(tempMin="12", tempMax="16")}, "", "约束:温差=4(需≥5)", expected_code="500"),
    c("TC143", "低压电池-开始时间格式错误", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(startTime="abc")}, "", "特殊参数:startTime格式错误", expected_code="500"),
    c("TC144", "低压电池-加热时段超过4组", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": [_hp() for _ in range(5)]},
      "", "边界外:heatingPeriodList=5组(最多4组)", expected_code="500"),
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
    print(f"已生成 {len(CASES)} 条低压电池用例 -> {OUT}")


if __name__ == "__main__":
    main()
