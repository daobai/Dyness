# -*- coding: utf-8 -*-
"""生成工商业（DH-F/DH-Y 系列）API 测试数据 CSV。

基于 docs/interfaces 下工商业（I&C Energy Storage Battery）接口文档生成，共 5 个 SetCommerce* 下发接口。
覆盖：正常流 + 异常(deviceSn 不存在/空、collectorSn 缺失) + 各接口参数边界值/越界/枚举。
运行：py -3 tests/api/gen_commerce_cases.py
"""

import csv
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "data" / "api_commerce.csv"
FIELDS = ["case_id", "name", "method", "path", "headers", "params", "body",
          "expected_status", "expected_code", "assertions", "description", "enabled",
          "models", "module", "func_module", "risk", "smoke"]

SN = "{{deviceSn}}"           # 设备 SN 模板变量
CSN = "{{collectorSn}}"       # 采集器 SN 模板变量（工商业设备必填）
BAD_SN = "NOT_EXIST_SN_000"

# 接口路径 -> 功能模块映射（一级模块/二级模块 层级格式，详见 config/biz_module_tree.md）
_FUNC_MODULE_MAP = {
    "SetCommerceSystemSetting": "工商业储能/系统设置",
    "SetCommerceBatterySetting": "工商业储能/电池参数",
    "SetCommerceRunModeSetting": "工商业储能/运行模式",
    "SetCommercePeakValleyPeriodSetting": "工商业储能/峰谷时段",
    "SetCommerceAdvancedSetting": "工商业储能/高级设置",
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
      expected_code="200", module="commerce", risk="", smoke="0"):
    return {
        "case_id": case_id, "name": name, "method": "POST", "path": path,
        "headers": None, "params": None, "body": body,
        "expected_status": 200, "expected_code": expected_code, "assertions": assertions,
        "description": description, "enabled": enabled, "models": models,
        "module": module, "func_module": _get_func_module(path), "risk": risk or _get_risk(path, body), "smoke": smoke,
    }


def _price(startTime="08:00", price="0.2", priceGroup="1", timeType=1):
    return [{"startTime": startTime, "price": price, "priceGroup": priceGroup, "timeType": timeType}]


CASES = [
    # ===== 正常流（下发，会真实改设备，谨慎）=====
    c("TC001", "工商业系统设置下发", "/v2/SetCommerceSystemSetting",
      {"deviceSn": SN, "collectorSn": CSN, "controlMode": "1", "controlWay": "2",
       "operateMode": "2", "powerMargin": "80", "backwashSet": "1"},
      "$.code == 200", "下发:工商业系统设置"),
    c("TC002", "工商业电池参数下发", "/v2/SetCommerceBatterySetting",
      {"deviceSn": SN, "collectorSn": CSN, "socProtectEnable": "1",
       "maxChargeEndSoc": "95", "minDisChargeEndSoc": "20", "offGridCutoffSoc": "15"},
      "$.code == 200", "下发:工商业电池参数"),
    c("TC003", "工商业运行模式下发", "/v2/SetCommerceRunModeSetting",
      {"deviceSn": SN, "collectorSn": CSN, "operateMode": "0"},
      "$.code == 200", "下发:工商业运行模式"),
    c("TC004", "工商业峰谷时段下发", "/v2/SetCommercePeakValleyPeriodSetting",
      {"deviceSn": SN, "electricityPriceTimeRanges": _price()},
      "$.code == 200", "下发:工商业峰谷时段"),
    c("TC005", "工商业高级设置下发", "/v2/SetCommerceAdvancedSetting",
      {"deviceSn": SN, "collectorSn": CSN, "faultReset": "3"},
      "$.code == 200", "下发:工商业高级设置"),

    # ===== 异常：deviceSn 不存在 / 空（预期 500）=====
    c("TC101", "工商业系统设置-deviceSn不存在", "/v2/SetCommerceSystemSetting",
      {"deviceSn": BAD_SN, "collectorSn": CSN}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC102", "工商业电池参数-deviceSn不存在", "/v2/SetCommerceBatterySetting",
      {"deviceSn": BAD_SN, "collectorSn": CSN}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC103", "工商业运行模式-deviceSn不存在", "/v2/SetCommerceRunModeSetting",
      {"deviceSn": BAD_SN, "collectorSn": CSN}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC104", "工商业峰谷时段-deviceSn不存在", "/v2/SetCommercePeakValleyPeriodSetting",
      {"deviceSn": BAD_SN}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC105", "工商业高级设置-deviceSn不存在", "/v2/SetCommerceAdvancedSetting",
      {"deviceSn": BAD_SN, "collectorSn": CSN}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC106", "工商业系统设置-deviceSn为空", "/v2/SetCommerceSystemSetting",
      {"deviceSn": "", "collectorSn": CSN}, "", "特殊参数:deviceSn空字符串", expected_code="500"),
    c("TC107", "工商业电池参数-deviceSn为空", "/v2/SetCommerceBatterySetting",
      {"deviceSn": "", "collectorSn": CSN}, "", "特殊参数:deviceSn空字符串", expected_code="500"),
    c("TC108", "工商业运行模式-deviceSn为空", "/v2/SetCommerceRunModeSetting",
      {"deviceSn": "", "collectorSn": CSN}, "", "特殊参数:deviceSn空字符串", expected_code="500"),
    c("TC109", "工商业峰谷时段-deviceSn为空", "/v2/SetCommercePeakValleyPeriodSetting",
      {"deviceSn": ""}, "", "特殊参数:deviceSn空字符串", expected_code="500"),
    c("TC110", "工商业高级设置-deviceSn为空", "/v2/SetCommerceAdvancedSetting",
      {"deviceSn": "", "collectorSn": CSN}, "", "特殊参数:deviceSn空字符串", expected_code="500"),

    # ===== 异常：collectorSn 缺失（预期 500）=====
    c("TC111", "工商业系统设置-缺collectorSn", "/v2/SetCommerceSystemSetting",
      {"deviceSn": SN}, "", "必填缺失:缺collectorSn", expected_code="500"),
    c("TC112", "工商业电池参数-缺collectorSn", "/v2/SetCommerceBatterySetting",
      {"deviceSn": SN}, "", "必填缺失:缺collectorSn", expected_code="500"),
    c("TC113", "工商业运行模式-缺collectorSn", "/v2/SetCommerceRunModeSetting",
      {"deviceSn": SN}, "", "必填缺失:缺collectorSn", expected_code="500"),
    c("TC115", "工商业高级设置-缺collectorSn", "/v2/SetCommerceAdvancedSetting",
      {"deviceSn": SN}, "", "必填缺失:缺collectorSn", expected_code="500"),

    # ===== 系统设置：枚举 / 越界 =====
    c("TC121", "工商业系统设置-controlMode越界", "/v2/SetCommerceSystemSetting",
      {"deviceSn": SN, "collectorSn": CSN, "controlMode": "3"}, "", "边界外:controlMode=3(枚举0/1/2)", expected_code="500"),
    c("TC122", "工商业系统设置-controlWay越界", "/v2/SetCommerceSystemSetting",
      {"deviceSn": SN, "collectorSn": CSN, "controlWay": "3"}, "", "边界外:controlWay=3(枚举0/1/2)", expected_code="500"),
    c("TC123", "工商业系统设置-operateMode越界", "/v2/SetCommerceSystemSetting",
      {"deviceSn": SN, "collectorSn": CSN, "operateMode": "7"}, "", "边界外:operateMode=7(最大6)", expected_code="500"),
    c("TC124", "工商业系统设置-powerMargin越界小", "/v2/SetCommerceSystemSetting",
      {"deviceSn": SN, "collectorSn": CSN, "powerMargin": "1.4"}, "", "边界外:powerMargin=1.4(最小1.5)", expected_code="500"),
    c("TC125", "工商业系统设置-powerMargin越界大", "/v2/SetCommerceSystemSetting",
      {"deviceSn": SN, "collectorSn": CSN, "powerMargin": "10.1"}, "", "边界外:powerMargin=10.1(最大10)", expected_code="500"),

    # ===== 电池参数：枚举 / 边界值 / 越界 =====
    c("TC131", "工商业电池参数-socProtectEnable非法", "/v2/SetCommerceBatterySetting",
      {"deviceSn": SN, "collectorSn": CSN, "socProtectEnable": "2"}, "", "边界外:socProtectEnable=2(枚举0/1)", expected_code="500"),
    c("TC132", "工商业电池参数-offGridCutoffSoc最小值", "/v2/SetCommerceBatterySetting",
      {"deviceSn": SN, "collectorSn": CSN, "offGridCutoffSoc": "5"}, "$.code == 200", "边界值:offGridCutoffSoc=5(最小)", "200"),
    c("TC133", "工商业电池参数-offGridCutoffSoc最大值", "/v2/SetCommerceBatterySetting",
      {"deviceSn": SN, "collectorSn": CSN, "offGridCutoffSoc": "50"}, "$.code == 200", "边界值:offGridCutoffSoc=50(最大)", "200"),
    c("TC134", "工商业电池参数-offGridCutoffSoc越界小", "/v2/SetCommerceBatterySetting",
      {"deviceSn": SN, "collectorSn": CSN, "offGridCutoffSoc": "4"}, "", "边界外:offGridCutoffSoc=4(最小5-1)", expected_code="500"),
    c("TC135", "工商业电池参数-offGridCutoffSoc越界大", "/v2/SetCommerceBatterySetting",
      {"deviceSn": SN, "collectorSn": CSN, "offGridCutoffSoc": "51"}, "", "边界外:offGridCutoffSoc=51(最大50+1)", expected_code="500"),
    c("TC136", "工商业电池参数-maxChargeEndSoc越界", "/v2/SetCommerceBatterySetting",
      {"deviceSn": SN, "collectorSn": CSN, "maxChargeEndSoc": "101"}, "", "边界外:maxChargeEndSoc=101(最大100)", expected_code="500"),
    c("TC137", "工商业电池参数-backupPowerSocEnable非法", "/v2/SetCommerceBatterySetting",
      {"deviceSn": SN, "collectorSn": CSN, "backupPowerSocEnable": "2"}, "", "边界外:backupPowerSocEnable=2(枚举0/1)", expected_code="500"),

    # ===== 运行模式：枚举 / 边界值 / 越界 =====
    c("TC141", "工商业运行模式-operateMode最小值", "/v2/SetCommerceRunModeSetting",
      {"deviceSn": SN, "collectorSn": CSN, "operateMode": "0"}, "$.code == 200", "边界值:operateMode=0(最小)", "200"),
    c("TC142", "工商业运行模式-operateMode最大值", "/v2/SetCommerceRunModeSetting",
      {"deviceSn": SN, "collectorSn": CSN, "operateMode": "5"}, "$.code == 200", "边界值:operateMode=5(最大)", "200"),
    c("TC143", "工商业运行模式-operateMode越界", "/v2/SetCommerceRunModeSetting",
      {"deviceSn": SN, "collectorSn": CSN, "operateMode": "6"}, "", "边界外:operateMode=6(最大5)", expected_code="500"),
    c("TC144", "工商业运行模式-operateModeC260越界", "/v2/SetCommerceRunModeSetting",
      {"deviceSn": SN, "collectorSn": CSN, "operateModeC260": "7"}, "", "边界外:operateModeC260=7(最大6)", expected_code="500"),
    c("TC145", "工商业运行模式-threePartyVppOperateMode越界", "/v2/SetCommerceRunModeSetting",
      {"deviceSn": SN, "collectorSn": CSN, "threePartyVppOperateMode": "4"}, "", "边界外:threePartyVppOperateMode=4(最大3)", expected_code="500"),
    c("TC146", "工商业运行模式-timingMode越界", "/v2/SetCommerceRunModeSetting",
      {"deviceSn": SN, "collectorSn": CSN, "timingMode": "3"}, "", "边界外:timingMode=3(最大2)", expected_code="500"),

    # ===== 峰谷时段：边界值 / 越界 =====
    c("TC151", "工商业峰谷时段-month最小值", "/v2/SetCommercePeakValleyPeriodSetting",
      {"deviceSn": SN, "month": "1"}, "$.code == 200", "边界值:month=1(最小)", "200"),
    c("TC152", "工商业峰谷时段-month最大值", "/v2/SetCommercePeakValleyPeriodSetting",
      {"deviceSn": SN, "month": "12"}, "$.code == 200", "边界值:month=12(最大)", "200"),
    c("TC153", "工商业峰谷时段-month越界", "/v2/SetCommercePeakValleyPeriodSetting",
      {"deviceSn": SN, "month": "13"}, "", "边界外:month=13(最大12)", expected_code="500"),
    c("TC154", "工商业峰谷时段-priceGroup越界", "/v2/SetCommercePeakValleyPeriodSetting",
      {"deviceSn": SN, "priceGroup": "5"}, "", "边界外:priceGroup=5(最大4)", expected_code="500"),
    c("TC155", "工商业峰谷时段-timeType越界", "/v2/SetCommercePeakValleyPeriodSetting",
      {"deviceSn": SN, "timeType": "4"}, "", "边界外:timeType=4(最大3)", expected_code="500"),
    c("TC156", "工商业峰谷时段-timeType越界小", "/v2/SetCommercePeakValleyPeriodSetting",
      {"deviceSn": SN, "timeType": "-2"}, "", "边界外:timeType=-2(最小-1)", expected_code="500"),

    # ===== 高级设置：枚举 / 越界 =====
    c("TC161", "工商业高级设置-reset越界小", "/v2/SetCommerceAdvancedSetting",
      {"deviceSn": SN, "collectorSn": CSN, "reset": "3"}, "", "边界外:reset=3(最小4)", expected_code="500"),
    c("TC162", "工商业高级设置-reset越界大", "/v2/SetCommerceAdvancedSetting",
      {"deviceSn": SN, "collectorSn": CSN, "reset": "7"}, "", "边界外:reset=7(最大6)", expected_code="500"),
    c("TC163", "工商业高级设置-faultReset非法", "/v2/SetCommerceAdvancedSetting",
      {"deviceSn": SN, "collectorSn": CSN, "faultReset": "9"}, "", "边界外:faultReset=9(仅3)", expected_code="500"),
    # systemReset 参数（系统重启）
    c("TC164", "工商业高级设置-systemReset正常值", "/v2/SetCommerceAdvancedSetting",
      {"deviceSn": SN, "collectorSn": CSN, "systemReset": "1"}, "$.code == 200", "边界值:systemReset=1(系统重启)", "200"),
    c("TC165", "工商业高级设置-systemReset越界小", "/v2/SetCommerceAdvancedSetting",
      {"deviceSn": SN, "collectorSn": CSN, "systemReset": "0"}, "", "边界外:systemReset=0(仅1)", expected_code="500"),
    c("TC166", "工商业高级设置-systemReset越界大", "/v2/SetCommerceAdvancedSetting",
      {"deviceSn": SN, "collectorSn": CSN, "systemReset": "2"}, "", "边界外:systemReset=2(仅1)", expected_code="500"),

    # ===== 枚举覆盖补充 =====
    # SetCommerceSystemSetting: controlMode 枚举 0/1/2
    c("TC171", "工商业系统设置-controlMode=0", "/v2/SetCommerceSystemSetting",
      {"deviceSn": SN, "collectorSn": CSN, "controlMode": "0"},
      "$.code == 200", "枚举值:controlMode=0", "200"),
    c("TC172", "工商业系统设置-controlMode=1", "/v2/SetCommerceSystemSetting",
      {"deviceSn": SN, "collectorSn": CSN, "controlMode": "1"},
      "$.code == 200", "枚举值:controlMode=1", "200"),
    c("TC173", "工商业系统设置-controlMode=2", "/v2/SetCommerceSystemSetting",
      {"deviceSn": SN, "collectorSn": CSN, "controlMode": "2"},
      "$.code == 200", "枚举值:controlMode=2", "200"),
    # controlWay 枚举 0/1/2
    c("TC174", "工商业系统设置-controlWay=0", "/v2/SetCommerceSystemSetting",
      {"deviceSn": SN, "collectorSn": CSN, "controlMode": "1", "controlWay": "0"},
      "$.code == 200", "枚举值:controlWay=0", "200"),
    c("TC175", "工商业系统设置-controlWay=1", "/v2/SetCommerceSystemSetting",
      {"deviceSn": SN, "collectorSn": CSN, "controlMode": "1", "controlWay": "1"},
      "$.code == 200", "枚举值:controlWay=1", "200"),
    c("TC176", "工商业系统设置-controlWay=2", "/v2/SetCommerceSystemSetting",
      {"deviceSn": SN, "collectorSn": CSN, "controlMode": "1", "controlWay": "2"},
      "$.code == 200", "枚举值:controlWay=2", "200"),
    # SetCommerceRunModeSetting: operateMode 枚举 0~5
    c("TC177", "工商业运行模式-operateMode=0", "/v2/SetCommerceRunModeSetting",
      {"deviceSn": SN, "collectorSn": CSN, "operateMode": "0"},
      "$.code == 200", "枚举值:operateMode=0", "200"),
    c("TC178", "工商业运行模式-operateMode=1", "/v2/SetCommerceRunModeSetting",
      {"deviceSn": SN, "collectorSn": CSN, "operateMode": "1"},
      "$.code == 200", "枚举值:operateMode=1", "200"),
    c("TC179", "工商业运行模式-operateMode=2", "/v2/SetCommerceRunModeSetting",
      {"deviceSn": SN, "collectorSn": CSN, "operateMode": "2"},
      "$.code == 200", "枚举值:operateMode=2", "200"),
    c("TC180", "工商业运行模式-operateMode=3", "/v2/SetCommerceRunModeSetting",
      {"deviceSn": SN, "collectorSn": CSN, "operateMode": "3"},
      "$.code == 200", "枚举值:operateMode=3", "200"),
    c("TC181", "工商业运行模式-operateMode=4", "/v2/SetCommerceRunModeSetting",
      {"deviceSn": SN, "collectorSn": CSN, "operateMode": "4"},
      "$.code == 200", "枚举值:operateMode=4", "200"),
    c("TC182", "工商业运行模式-operateMode=5", "/v2/SetCommerceRunModeSetting",
      {"deviceSn": SN, "collectorSn": CSN, "operateMode": "5"},
      "$.code == 200", "枚举值:operateMode=5", "200"),
    # threePartyVppOperateMode 枚举 0~3
    c("TC183", "工商业运行模式-threePartyVppOperateMode=0", "/v2/SetCommerceRunModeSetting",
      {"deviceSn": SN, "collectorSn": CSN, "operateMode": "0", "threePartyVppOperateMode": "0"},
      "$.code == 200", "枚举值:threePartyVppOperateMode=0", "200"),
    c("TC184", "工商业运行模式-threePartyVppOperateMode=1", "/v2/SetCommerceRunModeSetting",
      {"deviceSn": SN, "collectorSn": CSN, "operateMode": "0", "threePartyVppOperateMode": "1"},
      "$.code == 200", "枚举值:threePartyVppOperateMode=1", "200"),
    c("TC185", "工商业运行模式-threePartyVppOperateMode=2", "/v2/SetCommerceRunModeSetting",
      {"deviceSn": SN, "collectorSn": CSN, "operateMode": "0", "threePartyVppOperateMode": "2"},
      "$.code == 200", "枚举值:threePartyVppOperateMode=2", "200"),
    c("TC186", "工商业运行模式-threePartyVppOperateMode=3", "/v2/SetCommerceRunModeSetting",
      {"deviceSn": SN, "collectorSn": CSN, "operateMode": "0", "threePartyVppOperateMode": "3"},
      "$.code == 200", "枚举值:threePartyVppOperateMode=3", "200"),
    # SetCommercePeakValleyPeriodSetting: timeType 枚举 -1~3
    c("TC187", "工商业峰谷时段-timeType=-1", "/v2/SetCommercePeakValleyPeriodSetting",
      {"deviceSn": SN, "electricityPriceTimeRanges": _price(timeType=-1)},
      "$.code == 200", "枚举值:timeType=-1", "200"),
    c("TC188", "工商业峰谷时段-timeType=0", "/v2/SetCommercePeakValleyPeriodSetting",
      {"deviceSn": SN, "electricityPriceTimeRanges": _price(timeType=0)},
      "$.code == 200", "枚举值:timeType=0", "200"),
    c("TC189", "工商业峰谷时段-timeType=1", "/v2/SetCommercePeakValleyPeriodSetting",
      {"deviceSn": SN, "electricityPriceTimeRanges": _price(timeType=1)},
      "$.code == 200", "枚举值:timeType=1", "200"),
    c("TC190", "工商业峰谷时段-timeType=2", "/v2/SetCommercePeakValleyPeriodSetting",
      {"deviceSn": SN, "electricityPriceTimeRanges": _price(timeType=2)},
      "$.code == 200", "枚举值:timeType=2", "200"),
    c("TC191", "工商业峰谷时段-timeType=3", "/v2/SetCommercePeakValleyPeriodSetting",
      {"deviceSn": SN, "electricityPriceTimeRanges": _price(timeType=3)},
      "$.code == 200", "枚举值:timeType=3", "200"),

    # ===== 必填字段缺失补充 =====
    c("TC192", "工商业系统设置-缺controlMode", "/v2/SetCommerceSystemSetting",
      {"deviceSn": SN, "collectorSn": CSN, "controlWay": "2"},
      "", "必填缺失:缺controlMode", expected_code="500"),
    c("TC193", "工商业系统设置-缺controlWay", "/v2/SetCommerceSystemSetting",
      {"deviceSn": SN, "collectorSn": CSN, "controlMode": "1"},
      "", "必填缺失:缺controlWay", expected_code="500"),
    c("TC194", "工商业系统设置-缺operateMode", "/v2/SetCommerceSystemSetting",
      {"deviceSn": SN, "collectorSn": CSN, "controlMode": "1", "controlWay": "2"},
      "", "必填缺失:缺operateMode", expected_code="500"),
    c("TC195", "工商业电池参数-缺socProtectEnable", "/v2/SetCommerceBatterySetting",
      {"deviceSn": SN, "collectorSn": CSN, "maxChargeEndSoc": "95"},
      "", "必填缺失:缺socProtectEnable", expected_code="500"),
    c("TC196", "工商业电池参数-缺maxChargeEndSoc", "/v2/SetCommerceBatterySetting",
      {"deviceSn": SN, "collectorSn": CSN, "socProtectEnable": "1"},
      "", "必填缺失:缺maxChargeEndSoc", expected_code="500"),
    c("TC197", "工商业运行模式-缺operateMode", "/v2/SetCommerceRunModeSetting",
      {"deviceSn": SN, "collectorSn": CSN}, "", "必填缺失:缺operateMode", expected_code="500"),
    c("TC198", "工商业峰谷时段-缺electricityPriceTimeRanges", "/v2/SetCommercePeakValleyPeriodSetting",
      {"deviceSn": SN}, "", "必填缺失:缺electricityPriceTimeRanges", expected_code="500"),
    c("TC199", "工商业高级设置-缺reset或faultReset", "/v2/SetCommerceAdvancedSetting",
      {"deviceSn": SN, "collectorSn": CSN}, "", "必填缺失:缺reset/faultReset", expected_code="500"),

    # ===== deviceSn 错误参数补充 =====
    c("TC201", "工商业系统设置-deviceSn含特殊字符", "/v2/SetCommerceSystemSetting",
      {"deviceSn": "<script>alert(1)</script>", "collectorSn": CSN},
      "", "特殊参数:deviceSn含脚本标签", expected_code="500"),
    c("TC202", "工商业系统设置-deviceSn超长", "/v2/SetCommerceSystemSetting",
      {"deviceSn": "X" * 500, "collectorSn": CSN},
      "", "特殊参数:deviceSn超长(500字符)", expected_code="500"),
    c("TC203", "工商业系统设置-deviceSn含换行符", "/v2/SetCommerceSystemSetting",
      {"deviceSn": "SN\n001", "collectorSn": CSN},
      "", "特殊参数:deviceSn含换行符", expected_code="500"),
    c("TC204", "工商业系统设置-deviceSn为布尔值", "/v2/SetCommerceSystemSetting",
      {"deviceSn": True, "collectorSn": CSN},
      "", "特殊参数:deviceSn为布尔值", expected_code="500"),
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
    print(f"已生成 {len(CASES)} 条工商业用例 -> {OUT}")


if __name__ == "__main__":
    main()
