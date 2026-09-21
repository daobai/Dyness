# -*- coding: utf-8 -*-
"""生成高压电池（BDU/BMS 系统）API 测试数据 CSV。

基于 docs/interfaces 下高压电池（High-voltage Battery）接口文档生成，共 5 个接口。
覆盖：正常流 + 异常(deviceSn 不存在/空/缺失) + 分页越界 + 电池加热参数边界值/越界/枚举/温差约束。
运行：py -3 tests/api/gen_highvoltage_cases.py
"""

import csv
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "data" / "api_highvoltage.csv"
FIELDS = ["case_id", "name", "method", "path", "headers", "params", "body",
          "expected_status", "expected_code", "assertions", "description", "enabled",
          "models", "module", "func_module", "risk", "smoke"]

SN = "{{deviceSn}}"
BAD_SN = "NOT_EXIST_SN_000"

# 接口路径 -> 功能模块映射（一级模块/二级模块 层级格式，详见 config/biz_module_tree.md）
_FUNC_MODULE_MAP = {
    # 电站中心
    "GetDeviceInfBySN": "电站中心/设备管理",
    "GetRealTimeDataBySN": "电站中心/数据查询",
    "GetAlarmInfBySN": "电站中心/告警管理",
    # 设备参数配置
    "GetBatterySetting": "设备参数配置/电池参数设置",
    "SetBatterySetting": "设备参数配置/电池参数设置",
}


def _get_risk(path, body):
    """根据接口路径和请求体判断风险等级。"""
    api_name = path.rstrip("/").split("/")[-1]
    if not isinstance(body, dict):
        return ""
    # 工商业高级设置 - systemReset/reset/faultReset 参数
    if api_name == "SetCommerceAdvancedSetting":
        if "systemReset" in body or "reset" in body or "faultReset" in body:
            return "danger"
    # 户用高级参数 - systemReset 参数
    if api_name == "SetAdvancedSetting":
        if "systemReset" in body:
            return "danger"
    return ""


def _get_func_module(path):
    """根据接口路径推断功能模块。"""
    api_name = path.rstrip("/").split("/")[-1]
    return _FUNC_MODULE_MAP.get(api_name, "")


def c(case_id, name, path, body, assertions, description, enabled="1", models="",
      expected_code="200", module="highvoltage", risk="", smoke="0"):
    return {
        "case_id": case_id, "name": name, "method": "POST", "path": path,
        "headers": None, "params": None, "body": body,
        "expected_status": 200, "expected_code": expected_code, "assertions": assertions,
        "description": description, "enabled": enabled, "models": models,
        "module": module, "func_module": _get_func_module(path), "risk": risk or _get_risk(path, body), "smoke": smoke,
    }


def _hp(status="1", tempMin="10", tempMax="20", startTime="08:30", endTime="10:30", weekInfo="0,1,2,3,4"):
    """生成一组电池加热时段参数。"""
    return [{"status": status, "startTime": startTime, "endTime": endTime,
             "tempMin": tempMin, "tempMax": tempMax, "weekInfo": weekInfo}]


CASES = [
    # ===== 查询类（核心查询 smoke=1）=====
    c("TC001", "高压电池-设备信息查询", "/v2/GetDeviceInfBySN",
      {"deviceSn": SN},
      "$.code == 200;$.data.bduSn exists;$.data.appVersion exists",
      "查询类:设备信息", smoke="1"),
    c("TC002", "高压电池-实时运行数据", "/v2/GetRealTimeDataBySN",
      {"deviceSn": SN},
      "$.code == 200;$.data.batteryInfo.soc exists;$.data.batteryInfo.batteryVoltage exists;$.data.batteryInfo.soh exists",
      "查询类:实时运行数据", smoke="1"),
    c("TC003", "高压电池-故障信息查询", "/v2/GetAlarmInfBySN",
      {"deviceSn": SN, "pageNum": 1, "pageSize": 200},
      "$.code == 200;$.data.total exists;$.data.list exists",
      "查询类:故障信息", smoke="1"),

    # ===== 控制类：查询 + 下发 =====
    c("TC004", "高压电池-电池加热查询", "/v2/GetBatterySetting",
      {"deviceSn": SN}, "$.code == 200;$.data.heatingPeriodList exists", "控制类:电池加热查询"),
    c("TC005", "高压电池-电池加热下发", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp()},
      "$.code == 200", "下发:电池加热(改设备,慎用)"),

    # ===== 异常：deviceSn 不存在 / 空 / 缺失（预期 500）=====
    c("TC101", "高压电池-设备信息-deviceSn不存在", "/v2/GetDeviceInfBySN",
      {"deviceSn": BAD_SN}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC102", "高压电池-设备信息-deviceSn为空", "/v2/GetDeviceInfBySN",
      {"deviceSn": ""}, "", "特殊参数:deviceSn空字符串", expected_code="500"),
    c("TC103", "高压电池-设备信息-缺deviceSn", "/v2/GetDeviceInfBySN",
      {}, "", "必填缺失:缺deviceSn", expected_code="500"),
    c("TC104", "高压电池-实时数据-deviceSn不存在", "/v2/GetRealTimeDataBySN",
      {"deviceSn": BAD_SN}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC105", "高压电池-实时数据-deviceSn为空", "/v2/GetRealTimeDataBySN",
      {"deviceSn": ""}, "", "特殊参数:deviceSn空字符串", expected_code="500"),
    c("TC106", "高压电池-故障信息-deviceSn不存在", "/v2/GetAlarmInfBySN",
      {"deviceSn": BAD_SN}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC107", "高压电池-电池加热查询-deviceSn不存在", "/v2/GetBatterySetting",
      {"deviceSn": BAD_SN}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC108", "高压电池-电池加热查询-deviceSn为空", "/v2/GetBatterySetting",
      {"deviceSn": ""}, "", "特殊参数:deviceSn空字符串", expected_code="500"),
    c("TC109", "高压电池-电池加热下发-deviceSn不存在", "/v2/SetBatterySetting",
      {"deviceSn": BAD_SN, "heatingPeriodList": _hp()}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC110", "高压电池-电池加热下发-缺deviceSn", "/v2/SetBatterySetting",
      {"heatingPeriodList": _hp()}, "", "必填缺失:缺deviceSn", expected_code="500"),

    # ===== 分页越界（GetAlarmInfBySN）=====
    c("TC121", "高压电池-故障信息-pageSize越界", "/v2/GetAlarmInfBySN",
      {"deviceSn": SN, "pageNum": 1, "pageSize": 201}, "", "边界外:pageSize=201(最大200)", expected_code="500"),
    c("TC122", "高压电池-故障信息-pageSize为0", "/v2/GetAlarmInfBySN",
      {"deviceSn": SN, "pageNum": 1, "pageSize": 0}, "", "边界外:pageSize=0", expected_code="500"),
    c("TC123", "高压电池-故障信息-pageSize非数字", "/v2/GetAlarmInfBySN",
      {"deviceSn": SN, "pageNum": 1, "pageSize": "abc"}, "", "特殊参数:pageSize类型错误", expected_code="500"),

    # ===== 电池加热参数：枚举 / 边界值 / 越界 / 约束 =====
    # status 枚举 0/1（合法 200），2（非法 500）
    c("TC131", "高压电池-加热开关=关", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(status="0")}, "$.code == 200", "枚举值:status=0(关)", "200"),
    c("TC132", "高压电池-加热开关=开", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(status="1")}, "$.code == 200", "枚举值:status=1(开)", "200"),
    c("TC133", "高压电池-加热开关非法", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(status="2")}, "", "边界外:status=2(枚举0/1)", expected_code="500"),
    # tempMin 范围 10~15
    c("TC134", "高压电池-温度下限最小值", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(tempMin="10")}, "$.code == 200", "边界值:tempMin=10(最小)", "200"),
    c("TC135", "高压电池-温度下限最大值", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(tempMin="15", tempMax="20")}, "$.code == 200", "边界值:tempMin=15(最大)", "200"),
    c("TC136", "高压电池-温度下限越界小", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(tempMin="9")}, "", "边界外:tempMin=9(最小10-1)", expected_code="500"),
    c("TC137", "高压电池-温度下限越界大", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(tempMin="16", tempMax="20")}, "", "边界外:tempMin=16(最大15+1)", expected_code="500"),
    # tempMax 范围 15~20
    c("TC138", "高压电池-温度上限最小值", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(tempMin="10", tempMax="15")}, "$.code == 200", "边界值:tempMax=15(最小)", "200"),
    c("TC139", "高压电池-温度上限最大值", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(tempMax="20")}, "$.code == 200", "边界值:tempMax=20(最大)", "200"),
    c("TC140", "高压电池-温度上限越界小", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(tempMin="10", tempMax="14")}, "", "边界外:tempMax=14(最小15-1)", expected_code="500"),
    c("TC141", "高压电池-温度上限越界大", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(tempMax="21")}, "", "边界外:tempMax=21(最大20+1)", expected_code="500"),
    # 温差约束：上下限温差 ≥5°C
    c("TC142", "高压电池-加热温差不足5度", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(tempMin="12", tempMax="16")}, "", "约束:温差=4(需≥5)", expected_code="500"),
    # startTime 格式错误
    c("TC143", "高压电池-开始时间格式错误", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(startTime="abc")}, "", "特殊参数:startTime格式错误", expected_code="500"),
    # heatingPeriodList 最多 4 组
    c("TC144", "高压电池-加热时段超过4组", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": [_hp() for _ in range(5)]},
      "", "边界外:heatingPeriodList=5组(最多4组)", expected_code="500"),

    # ===== 枚举覆盖补充：weekInfo 字段 =====
    c("TC151", "高压电池-加热-weekInfo=工作日", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(weekInfo="0,1,2,3,4")},
      "$.code == 200", "枚举值:weekInfo=0,1,2,3,4(工作日)", "200"),
    c("TC152", "高压电池-加热-weekInfo=周末", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(weekInfo="5,6")},
      "$.code == 200", "枚举值:weekInfo=5,6(周末)", "200"),
    c("TC153", "高压电池-加热-weekInfo=全部", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(weekInfo="0,1,2,3,4,5,6")},
      "$.code == 200", "枚举值:weekInfo=0,1,2,3,4,5,6(全部)", "200"),
    c("TC154", "高压电池-加热-weekInfo=单天", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(weekInfo="0")},
      "$.code == 200", "枚举值:weekInfo=0(周一)", "200"),
    c("TC155", "高压电池-加热-weekInfo=空", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": _hp(weekInfo="")},
      "$.code == 200", "枚举值:weekInfo=空(不限制)", "200"),

    # ===== 必填字段缺失补充 =====
    c("TC161", "高压电池-加热下发-缺heatingPeriodList", "/v2/SetBatterySetting",
      {"deviceSn": SN}, "", "必填缺失:缺heatingPeriodList", expected_code="500"),
    c("TC162", "高压电池-加热下发-时段缺status", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": [{"startTime": "08:30", "endTime": "10:30",
       "tempMin": "10", "tempMax": "20", "weekInfo": "0,1,2,3,4"}]},
      "", "必填缺失:时段缺status", expected_code="500"),
    c("TC163", "高压电池-加热下发-时段缺startTime", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": [{"status": "1", "endTime": "10:30",
       "tempMin": "10", "tempMax": "20", "weekInfo": "0,1,2,3,4"}]},
      "", "必填缺失:时段缺startTime", expected_code="500"),
    c("TC164", "高压电池-加热下发-时段缺endTime", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": [{"status": "1", "startTime": "08:30",
       "tempMin": "10", "tempMax": "20", "weekInfo": "0,1,2,3,4"}]},
      "", "必填缺失:时段缺endTime", expected_code="500"),
    c("TC165", "高压电池-加热下发-时段缺tempMin", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": [{"status": "1", "startTime": "08:30",
       "endTime": "10:30", "tempMax": "20", "weekInfo": "0,1,2,3,4"}]},
      "", "必填缺失:时段缺tempMin", expected_code="500"),
    c("TC166", "高压电池-加热下发-时段缺tempMax", "/v2/SetBatterySetting",
      {"deviceSn": SN, "heatingPeriodList": [{"status": "1", "startTime": "08:30",
       "endTime": "10:30", "tempMin": "10", "weekInfo": "0,1,2,3,4"}]},
      "", "必填缺失:时段缺tempMax", expected_code="500"),

    # ===== deviceSn 错误参数补充 =====
    c("TC181", "高压电池-设备信息-deviceSn含特殊字符", "/v2/GetDeviceInfBySN",
      {"deviceSn": "SN<>?001"}, "", "特殊参数:deviceSn含特殊字符", expected_code="500"),
    c("TC182", "高压电池-设备信息-deviceSn超长", "/v2/GetDeviceInfBySN",
      {"deviceSn": "H" * 300}, "", "特殊参数:deviceSn超长(300字符)", expected_code="500"),
    c("TC183", "高压电池-设备信息-deviceSn含Tab", "/v2/GetDeviceInfBySN",
      {"deviceSn": "SN\t001"}, "", "特殊参数:deviceSn含Tab", expected_code="500"),
    c("TC184", "高压电池-设备信息-deviceSn为数字类型", "/v2/GetDeviceInfBySN",
      {"deviceSn": 123456789}, "", "特殊参数:deviceSn为数字类型", expected_code="500"),
    c("TC185", "高压电池-设备信息-deviceSn为空对象", "/v2/GetDeviceInfBySN",
      {"deviceSn": {}}, "", "特殊参数:deviceSn为空对象", expected_code="500"),
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
    print(f"已生成 {len(CASES)} 条高压电池用例 -> {OUT}")


if __name__ == "__main__":
    main()
