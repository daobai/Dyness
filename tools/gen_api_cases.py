# -*- coding: utf-8 -*-
"""生成 API 测试数据 CSV（tests/api/data/api_testdata.csv）。

基于 docs/interfaces 下的 Dyness Open API Protocol V1.4 接口文档生成，共 18 个接口。
运行：py -3 tools/gen_api_cases.py
"""

import csv
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "tests" / "api" / "data" / "api_testdata.csv"
FIELDS = ["case_id", "name", "method", "path", "headers", "params", "body",
          "expected_status", "expected_code", "assertions", "description", "enabled", "models"]

SN = "{{deviceSn}}"  # 模板变量，运行时替换为当前设备的 SN


def c(case_id, name, path, body, assertions, description, enabled="1", models="", expected_code="200"):
    return {
        "case_id": case_id, "name": name, "method": "POST", "path": path,
        "headers": None, "params": None, "body": body,
        "expected_status": 200, "expected_code": expected_code, "assertions": assertions,
        "description": description, "enabled": enabled, "models": models,
    }


CASES = [
    # ===== 查询类（默认启用）=====
    c("TC001", "设备信息查询", "/v2/GetDeviceList",
      {"pageNum": 1, "pageSize": 200},
      "$.code == 200;$.data exists;$.data[0].deviceSn exists;$.data[0].deviceModel exists",
      "查询类:设备列表(分页)"),
    c("TC002", "设备基本信息查询", "/v2/GetDeviceInfBySN",
      {"deviceSn": SN},
      "$.code == 200;$.data.deviceSn exists;$.data.deviceModel exists;$.data.firmwareVersion exists;$.data.inverterRatedPower exists",
      "查询类:设备基本信息"),
    c("TC003", "设备状态信息查询", "/v2/GetStatusInfBySN",
      {"deviceSn": SN},
      "$.code == 200;$.data.workStatus exists;$.data.runModel exists;$.data.batteryCommunication exists;[AquaVolt,SolarCube] $.data.meterCommunication exists",
      "查询类:设备状态"),
    c("TC004", "设备运行数据查询", "/v2/GetRealTimeDataBySN",
      {"deviceSn": SN},
      "$.code == 200;$.data.batteryInfo.soc exists;[SolarCube] $.data.pvInfo.pvTotalPower exists;$.data.gridInfo.gridPower exists;$.data.loadInfo.loadTotalPower exists",
      "查询类:实时运行数据"),
    c("TC005", "设备电量信息查询", "/v2/GetTotalEnergyDataBySN",
      {"deviceSn": SN},
      "$.code == 200;$.data.batteryInfo.totalChargeEnergy exists;[AquaVolt,SolarCube] $.data.pvInfo.totalPvGeneration exists;$.data.gridInfo.totalBuyEnergy exists;$.data.loadInfo.totalElectricity exists",
      "查询类:累计电量"),
    c("TC006", "设备故障信息查询", "/v2/GetAlarmInfBySN",
      {"deviceSn": SN, "pageNum": 1, "pageSize": 200},
      "$.code == 200;$.data.total exists;$.data.list exists",
      "查询类:故障信息"),

    # ===== 控制类：查询（默认启用）=====
    c("TC007", "安规国家查询", "/v2/GetBaseSetting",
      {"deviceSn": SN}, "$.code == 200;$.data.safetyCountry exists", "控制类:安规国家查询"),
    c("TC009", "工作模式查询", "/v2/GetWorkModeSetting",
      {"deviceSn": SN}, "$.code == 200;$.data.workMode exists", "控制类:工作模式查询"),
    c("TC011", "电池参数查询", "/v2/GetBatterySetting",
      {"deviceSn": SN}, "$.code == 200;[AquaVolt,SolarCube] $.data.onGridDischargeDod exists", "控制类:电池参数查询"),
    c("TC013", "负载控制查询", "/v2/GetLoadControlSetting",
      {"deviceSn": SN}, "$.code == 200;[SolarCube] $.data.loadSwitch exists", "控制类:负载控制查询"),
    c("TC015", "峰值控制查询", "/v2/GetPeakControlSetting",
      {"deviceSn": SN}, "$.code == 200;[AquaVolt,SolarCube] $.data.peakControlEnable exists", "控制类:峰值控制查询"),
    c("TC017", "高级参数查询", "/v2/GetAdvancedSetting",
      {"deviceSn": SN}, "$.code == 200;$.data.powerLevelSetting exists", "控制类:高级参数查询"),

    # ===== 控制类：下发（会真实修改设备参数，谨慎执行）=====
    c("TC008", "安规国家下发", "/v2/SetBaseSetting",
      {"deviceSn": SN, "safetyCountry": "43"}, "$.code == 200", "下发:安规国家(改设备,慎用)", "1"),
    c("TC010", "工作模式下发", "/v2/SetWorkModeSetting",
      {"deviceSn": SN, "workMode": "3", "[AquaVolt,SolarCube] workGroups": [
          {"batteryWorkGroup": 1, "state": "1", "startTime": "07:00", "endTime": "17:00",
           "power": "2000", "mode": "1", "week": "0,1,2,3,4", "dodState": "1", "dod": "30",
           "socMaxChargeState": "1", "batterySocMaxCharge": "90"}]},
      "$.code == 200", "下发:工作模式(改设备,慎用)", "1"),
    c("TC012", "电池参数下发", "/v2/SetBatterySetting",
      {"deviceSn": SN, "[AquaVolt,SolarCube] onGridDischargeDod": "20", "offGridDischargeDod": "20",
       "[AquaVolt,SolarCube] batteryChargeLimit": "70", "[SolarCube] batteryOffGridChargeLimit": "70"},
      "$.code == 200", "下发:电池参数(改设备,慎用)", "1"),
    c("TC014", "负载控制下发", "/v2/SetLoadControlSetting",
      {"deviceSn": SN, "loadSwitch": "0", "forceCloseTime": "07:00-17:00",
       "relayCloseSoc": "70", "relayOpenSoc": "30", "forceCloseOffGridOnly": "0",
       "alwaysCloseOnGridMode": "0", "pvPowerThreshold": "100"},
      "$.code == 200", "下发:负载控制(改设备,慎用)", "1", "SolarCube"),
    c("TC016", "峰值控制下发", "/v2/SetPeakControlSetting",
      {"deviceSn": SN, "peakControlEnable": "0", "triggerSoc": "20",
       "timeRange": "17:00-22:00", "peakControlPower": "2000"},
      "$.code == 200", "下发:峰值控制(改设备,慎用)", "1", "AquaVolt,SolarCube"),
    c("TC018", "高级参数下发", "/v2/SetAdvancedSetting",
      {"deviceSn": SN,
       "gridPowerLimitGroup": {"gridPowerLimitSwitch": "1", "gridPowerLimitValue": "500"},
       "backupPowerSwitch": "1", "pvConnectMode": "0",
       "extCtMeterGroup": {"extCtMeterSelect": "1", "ctApplication": "1"},
       "isoSetting": "500", "acCouplingEnable": "1", "powerLevelSetting": "1000",
       "groundDetectionEnable": "1"},
      "$.code == 200", "下发:高级参数(改设备,慎用)", "1", "SolarCube"),
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
    print(f"已生成 {len(CASES)} 条用例 -> {OUT}")


if __name__ == "__main__":
    main()
