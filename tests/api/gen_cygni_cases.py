# -*- coding: utf-8 -*-
"""生成 Cygni（HA-HS 系列）API 测试数据 CSV。

基于 docs/interfaces 下 Cygni HA-HS 接口文档生成，共 21 个接口。
覆盖：正常流 + 异常(deviceSn 不存在/空/缺失) + 分页越界 + 下发参数边界值/越界/枚举/必填缺失。
运行：py -3 tests/api/gen_cygni_cases.py
"""

import csv
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "data" / "api_cygni.csv"
FIELDS = ["case_id", "name", "method", "path", "headers", "params", "body",
          "expected_status", "expected_code", "assertions", "description", "enabled",
          "models", "module", "smoke"]

SN = "{{deviceSn}}"
BAD_SN = "NOT_EXIST_SN_000"


def c(case_id, name, path, body, assertions, description, enabled="1", models="",
      expected_code="200", module="cygni", smoke="0"):
    return {
        "case_id": case_id, "name": name, "method": "POST", "path": path,
        "headers": None, "params": None, "body": body,
        "expected_status": 200, "expected_code": expected_code, "assertions": assertions,
        "description": description, "enabled": enabled, "models": models,
        "module": module, "smoke": smoke,
    }


def _wg(power="2000"):
    return [{"batteryWorkGroup": 1, "state": "1", "startTime": "07:00", "endTime": "17:00",
             "power": power, "mode": "1", "week": "0,1,2,3,4", "dodState": "1", "dod": "30",
             "socMaxChargeState": "1", "batterySocMaxCharge": "90"}]


CASES = [
    # ===== 查询类（核心查询 smoke=1）=====
    c("TC001", "Cygni-设备列表查询", "/v2/GetDeviceList",
      {"pageNum": 1, "pageSize": 200},
      "$.code == 200;$.data exists;$.data[0].deviceSn exists;$.data[0].deviceModel exists",
      "查询类:设备列表", smoke="1"),
    c("TC002", "Cygni-设备信息查询", "/v2/GetDeviceInfBySN",
      {"deviceSn": SN},
      "$.code == 200;$.data.deviceSn exists;$.data.deviceModel exists;$.data.firmwareVersion exists;$.data.inverterRatedPower exists",
      "查询类:设备信息", smoke="1"),
    c("TC003", "Cygni-设备状态查询", "/v2/GetStatusInfBySN",
      {"deviceSn": SN},
      "$.code == 200;$.data.workStatus exists;$.data.runModel exists",
      "查询类:设备状态", smoke="1"),
    c("TC004", "Cygni-实时运行数据", "/v2/GetRealTimeDataBySN",
      {"deviceSn": SN},
      "$.code == 200;$.data.batteryInfo.soc exists;$.data.gridInfo.gridPower exists;$.data.loadInfo.loadTotalPower exists",
      "查询类:实时运行数据", smoke="1"),
    c("TC005", "Cygni-累计电量", "/v2/GetTotalEnergyDataBySN",
      {"deviceSn": SN},
      "$.code == 200;$.data.batteryInfo.totalChargeEnergy exists;$.data.gridInfo.totalBuyEnergy exists;$.data.loadInfo.totalElectricity exists",
      "查询类:累计电量", smoke="1"),
    c("TC006", "Cygni-故障信息查询", "/v2/GetAlarmInfBySN",
      {"deviceSn": SN, "pageNum": 1, "pageSize": 200},
      "$.code == 200;$.data.total exists;$.data.list exists",
      "查询类:故障信息", smoke="1"),
    c("TC007", "Cygni-并机信息查询", "/v2/GetParallelInfBySN",
      {"deviceSn": SN},
      "$.code == 200;$.data.parallelStatus exists;$.data.parallelRole exists;$.data.parallelPhase exists",
      "查询类:并机信息", smoke="1"),

    # ===== 控制类：查询 =====
    c("TC008", "Cygni-安规国家查询", "/v2/GetBaseSetting",
      {"deviceSn": SN}, "$.code == 200;$.data.safetyCountry exists", "控制类:安规国家查询"),
    c("TC009", "Cygni-工作模式查询", "/v2/GetWorkModeSetting",
      {"deviceSn": SN}, "$.code == 200;$.data.workMode exists", "控制类:工作模式查询"),
    c("TC010", "Cygni-电池参数查询", "/v2/GetBatterySetting",
      {"deviceSn": SN}, "$.code == 200;$.data.onGridDischargeDod exists", "控制类:电池参数查询"),
    c("TC011", "Cygni-负载控制查询", "/v2/GetLoadControlSetting",
      {"deviceSn": SN}, "$.code == 200;$.data.loadSwitch exists", "控制类:负载控制查询"),
    c("TC012", "Cygni-峰值控制查询", "/v2/GetPeakControlSetting",
      {"deviceSn": SN}, "$.code == 200;$.data.peakControlEnable exists", "控制类:峰值控制查询"),
    c("TC013", "Cygni-高级参数查询", "/v2/GetAdvancedSetting",
      {"deviceSn": SN}, "$.code == 200;$.data.powerLevelSetting exists", "控制类:高级参数查询"),
    c("TC014", "Cygni-发电机控制查询", "/v2/GetGeneratorControlSetting",
      {"deviceSn": SN}, "$.code == 200;$.data.generatorWorkMode exists", "控制类:发电机控制查询"),

    # ===== 控制类：下发 =====
    c("TC015", "Cygni-安规国家下发", "/v2/SetBaseSetting",
      {"deviceSn": SN, "safetyCountry": "43"}, "$.code == 200", "下发:安规国家(改设备,慎用)"),
    c("TC016", "Cygni-工作模式下发", "/v2/SetWorkModeSetting",
      {"deviceSn": SN, "workMode": "3", "workGroups": _wg()},
      "$.code == 200", "下发:工作模式(改设备,慎用)"),
    c("TC017", "Cygni-电池参数下发", "/v2/SetBatterySetting",
      {"deviceSn": SN, "onGridDischargeDod": "20", "offGridDischargeDod": "20",
       "batteryChargeLimit": "70", "batteryOffGridChargeLimit": "70"},
      "$.code == 200", "下发:电池参数(改设备,慎用)"),
    c("TC018", "Cygni-负载控制下发", "/v2/SetLoadControlSetting",
      {"deviceSn": SN, "loadSwitch": "0", "forceCloseTime": "07:00-17:00",
       "relayCloseSoc": "70", "relayOpenSoc": "30", "forceCloseOffGridOnly": "0",
       "alwaysCloseOnGridMode": "0", "pvPowerThreshold": "100"},
      "$.code == 200", "下发:负载控制(改设备,慎用)"),
    c("TC019", "Cygni-峰值控制下发", "/v2/SetPeakControlSetting",
      {"deviceSn": SN, "peakControlEnable": "0", "triggerSoc": "20",
       "timeRange": "17:00-22:00", "peakControlPower": "2000"},
      "$.code == 200", "下发:峰值控制(改设备,慎用)"),
    c("TC020", "Cygni-高级参数下发", "/v2/SetAdvancedSetting",
      {"deviceSn": SN, "powerLevelSetting": "1000"},
      "$.code == 200", "下发:高级参数(改设备,慎用)"),
    c("TC021", "Cygni-发电机控制下发", "/v2/SetGeneratorControlSetting",
      {"deviceSn": SN, "generatorWorkMode": "1", "timingModeSwitch": "1",
       "timingModeTimeRange": "08:00-12:00", "autoModeStartSoc": "30",
       "autoModeStopSoc": "80", "chargeSettingSwitch": "1",
       "batteryStartChargeSoc": "25", "batteryStopChargeSoc": "90",
       "chargePower": "2000", "generatorRatedPower": "5000"},
      "$.code == 200", "下发:发电机控制(改设备,慎用)"),

    # ===== 异常：deviceSn 不存在 / 空（预期 500）=====
    c("TC101", "Cygni-设备信息-deviceSn不存在", "/v2/GetDeviceInfBySN",
      {"deviceSn": BAD_SN}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC102", "Cygni-设备信息-deviceSn为空", "/v2/GetDeviceInfBySN",
      {"deviceSn": ""}, "", "特殊参数:deviceSn空字符串", expected_code="500"),
    c("TC103", "Cygni-实时数据-deviceSn不存在", "/v2/GetRealTimeDataBySN",
      {"deviceSn": BAD_SN}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC104", "Cygni-实时数据-deviceSn为空", "/v2/GetRealTimeDataBySN",
      {"deviceSn": ""}, "", "特殊参数:deviceSn空字符串", expected_code="500"),
    c("TC105", "Cygni-状态信息-deviceSn不存在", "/v2/GetStatusInfBySN",
      {"deviceSn": BAD_SN}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC106", "Cygni-故障信息-deviceSn不存在", "/v2/GetAlarmInfBySN",
      {"deviceSn": BAD_SN}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC107", "Cygni-并机信息-deviceSn不存在", "/v2/GetParallelInfBySN",
      {"deviceSn": BAD_SN}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC108", "Cygni-并机信息-deviceSn为空", "/v2/GetParallelInfBySN",
      {"deviceSn": ""}, "", "特殊参数:deviceSn空字符串", expected_code="500"),
    c("TC109", "Cygni-安规国家查询-deviceSn不存在", "/v2/GetBaseSetting",
      {"deviceSn": BAD_SN}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC110", "Cygni-电池参数查询-deviceSn不存在", "/v2/GetBatterySetting",
      {"deviceSn": BAD_SN}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC111", "Cygni-发电机控制查询-deviceSn不存在", "/v2/GetGeneratorControlSetting",
      {"deviceSn": BAD_SN}, "", "异常:deviceSn不存在", expected_code="500"),
    c("TC112", "Cygni-发电机控制下发-deviceSn不存在", "/v2/SetGeneratorControlSetting",
      {"deviceSn": BAD_SN, "generatorWorkMode": "1"}, "", "异常:deviceSn不存在", expected_code="500"),

    # ===== 分页越界 =====
    c("TC121", "Cygni-设备列表-pageSize越界", "/v2/GetDeviceList",
      {"pageNum": 1, "pageSize": 201}, "", "边界外:pageSize=201(最大200)", expected_code="500"),
    c("TC122", "Cygni-设备列表-pageSize为0", "/v2/GetDeviceList",
      {"pageNum": 1, "pageSize": 0}, "", "边界外:pageSize=0", expected_code="500"),
    c("TC123", "Cygni-故障信息-pageSize越界", "/v2/GetAlarmInfBySN",
      {"deviceSn": SN, "pageNum": 1, "pageSize": 201}, "", "边界外:pageSize=201(最大200)", expected_code="500"),

    # ===== 下发接口：边界值 / 越界 / 枚举 / 必填缺失 =====
    # SetBatterySetting（0~95 / 10~100）
    c("TC131", "Cygni-电池参数-并网放电深度最小值", "/v2/SetBatterySetting",
      {"deviceSn": SN, "onGridDischargeDod": "5", "offGridDischargeDod": "20",
       "batteryChargeLimit": "70", "batteryOffGridChargeLimit": "70"},
      "$.code == 200", "边界值:onGridDischargeDod=5(最小)", "200"),
    c("TC132", "Cygni-电池参数-并网放电深度最大值", "/v2/SetBatterySetting",
      {"deviceSn": SN, "onGridDischargeDod": "100", "offGridDischargeDod": "20",
       "batteryChargeLimit": "70", "batteryOffGridChargeLimit": "70"},
      "$.code == 200", "边界值:onGridDischargeDod=100(最大)", "200"),
    c("TC133", "Cygni-电池参数-并网放电深度越界", "/v2/SetBatterySetting",
      {"deviceSn": SN, "onGridDischargeDod": "101", "offGridDischargeDod": "20",
       "batteryChargeLimit": "70", "batteryOffGridChargeLimit": "70"},
      "", "边界外:onGridDischargeDod=101(最大100)", expected_code="500"),
    c("TC134", "Cygni-电池参数-充电限值越界", "/v2/SetBatterySetting",
      {"deviceSn": SN, "onGridDischargeDod": "20", "offGridDischargeDod": "20",
       "batteryChargeLimit": "101", "batteryOffGridChargeLimit": "70"},
      "", "边界外:batteryChargeLimit=101(最大100)", expected_code="500"),
    # SetPeakControlSetting（0~100 / 0~65535）
    c("TC135", "Cygni-峰值控制-triggerSoc越界", "/v2/SetPeakControlSetting",
      {"deviceSn": SN, "peakControlEnable": "0", "triggerSoc": "101",
       "timeRange": "17:00-22:00", "peakControlPower": "2000"},
      "", "边界外:triggerSoc=101(最大100)", expected_code="500"),
    c("TC136", "Cygni-峰值控制-peakControlPower越界", "/v2/SetPeakControlSetting",
      {"deviceSn": SN, "peakControlEnable": "0", "triggerSoc": "20",
       "timeRange": "17:00-22:00", "peakControlPower": "65536"},
      "", "边界外:peakControlPower=65536(最大65535)", expected_code="500"),
    c("TC137", "Cygni-峰值控制-peakControlEnable非法", "/v2/SetPeakControlSetting",
      {"deviceSn": SN, "peakControlEnable": "2", "triggerSoc": "20",
       "timeRange": "17:00-22:00", "peakControlPower": "2000"},
      "", "边界外:peakControlEnable=2(枚举0/1)", expected_code="500"),
    # SetWorkModeSetting
    c("TC138", "Cygni-工作模式-workMode非法", "/v2/SetWorkModeSetting",
      {"deviceSn": SN, "workMode": "99", "workGroups": _wg()},
      "", "边界外:workMode=99(枚举外)", expected_code="500"),
    c("TC139", "Cygni-工作模式-缺workGroups", "/v2/SetWorkModeSetting",
      {"deviceSn": SN, "workMode": "3"}, "", "必填缺失:缺workGroups", expected_code="500"),
    # SetLoadControlSetting
    c("TC140", "Cygni-负载控制-loadSwitch非法", "/v2/SetLoadControlSetting",
      {"deviceSn": SN, "loadSwitch": "2"}, "", "边界外:loadSwitch=2(枚举0/1)", expected_code="500"),
    # SetAdvancedSetting（powerLevelSetting 0~65535）
    c("TC141", "Cygni-高级参数-powerLevelSetting越界", "/v2/SetAdvancedSetting",
      {"deviceSn": SN, "powerLevelSetting": "65536"}, "", "边界外:powerLevelSetting=65536(最大65535)", expected_code="500"),
    c("TC142", "Cygni-高级参数-isoSetting越界", "/v2/SetAdvancedSetting",
      {"deviceSn": SN, "isoSetting": "9"}, "", "边界外:isoSetting=9(最小10)", expected_code="500"),
    # SetBaseSetting
    c("TC143", "Cygni-安规国家-safetyCountry越界", "/v2/SetBaseSetting",
      {"deviceSn": SN, "safetyCountry": "999"}, "", "边界外:safetyCountry=999(枚举外)", expected_code="500"),
    c("TC144", "Cygni-安规国家-缺safetyCountry", "/v2/SetBaseSetting",
      {"deviceSn": SN}, "", "必填缺失:缺safetyCountry", expected_code="500"),
    # SetGeneratorControlSetting（0/1/2/3 枚举 / 0~100）
    c("TC145", "Cygni-发电机-工作模式非法", "/v2/SetGeneratorControlSetting",
      {"deviceSn": SN, "generatorWorkMode": "9"}, "", "边界外:generatorWorkMode=9(枚举0/1/2/3)", expected_code="500"),
    c("TC146", "Cygni-发电机-启动SOC越界", "/v2/SetGeneratorControlSetting",
      {"deviceSn": SN, "autoModeStartSoc": "101"}, "", "边界外:autoModeStartSoc=101(最大100)", expected_code="500"),
    c("TC147", "Cygni-发电机-停止SOC越界", "/v2/SetGeneratorControlSetting",
      {"deviceSn": SN, "autoModeStopSoc": "101"}, "", "边界外:autoModeStopSoc=101(最大100)", expected_code="500"),
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
    print(f"已生成 {len(CASES)} 条 Cygni 用例 -> {OUT}")


if __name__ == "__main__":
    main()
