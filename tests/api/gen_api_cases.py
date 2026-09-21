# -*- coding: utf-8 -*-
"""生成户用储能（AquaVolt/AquaVolt_LV/SolarCube/SolarCube2）API 测试数据 CSV。

基于 docs/interfaces 下 Dyness Open API Protocol V1.4 接口文档生成，共 18 个接口。
运行：py -3 tests/api/gen_api_cases.py
"""

import csv
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "data" / "api_household.csv"
FIELDS = ["case_id", "name", "method", "path", "headers", "params", "body",
          "expected_status", "expected_code", "assertions", "description", "enabled",
          "models", "module", "func_module", "risk", "smoke"]

SN = "{{deviceSn}}"  # 模板变量，运行时替换为当前设备的 SN

# 风险等级说明：
# - 空（safe）: 安全，查询类或普通参数下发，默认执行
# - warning: 警告，会改变设备运行状态但可恢复，默认执行
# - danger: 危险，关机/恢复出厂/系统重启等不可逆操作，需 --include-danger 才执行


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


# 接口路径 -> 功能模块映射（一级模块/二级模块 层级格式，详见 config/biz_module_tree.md）
_FUNC_MODULE_MAP = {
    # 电站中心
    "GetDeviceList": "电站中心/电站管理",
    "GetDeviceInfBySN": "电站中心/设备管理",
    "GetStatusInfBySN": "电站中心/设备管理",
    "GetRealTimeDataBySN": "电站中心/数据查询",
    "GetTotalEnergyDataBySN": "电站中心/数据查询",
    "GetAlarmInfBySN": "电站中心/告警管理",
    "GetParallelInfBySN": "电站中心/设备管理",
    # 设备参数配置
    "GetBaseSetting": "设备参数配置/安规国家设置",
    "SetBaseSetting": "设备参数配置/安规国家设置",
    "GetWorkModeSetting": "设备参数配置/工作模式设置",
    "SetWorkModeSetting": "设备参数配置/工作模式设置",
    "GetBatterySetting": "设备参数配置/电池参数设置",
    "SetBatterySetting": "设备参数配置/电池参数设置",
    "GetLoadControlSetting": "设备参数配置/负载控制设置",
    "SetLoadControlSetting": "设备参数配置/负载控制设置",
    "GetPeakControlSetting": "设备参数配置/峰值控制设置",
    "SetPeakControlSetting": "设备参数配置/峰值控制设置",
    "GetAdvancedSetting": "设备参数配置/高级参数设置",
    "SetAdvancedSetting": "设备参数配置/高级参数设置",
    "GetGeneratorControlSetting": "设备参数配置/发电机控制",
    "SetGeneratorControlSetting": "设备参数配置/发电机控制",
    # 工商业储能
    "SetCommerceSystemSetting": "工商业储能/系统设置",
    "SetCommerceBatterySetting": "工商业储能/电池参数",
    "SetCommerceRunModeSetting": "工商业储能/运行模式",
    "SetCommercePeakValleyPeriodSetting": "工商业储能/峰谷时段",
    "SetCommerceAdvancedSetting": "工商业储能/高级设置",
}


def _get_func_module(path):
    """根据接口路径推断功能模块。"""
    api_name = path.rstrip("/").split("/")[-1]
    return _FUNC_MODULE_MAP.get(api_name, "")


def c(case_id, name, path, body, assertions, description, enabled="1", models="",
      expected_code="200", module="household", risk="", smoke="0"):
    return {
        "case_id": case_id, "name": name, "method": "POST", "path": path,
        "headers": None, "params": None, "body": body,
        "expected_status": 200, "expected_code": expected_code, "assertions": assertions,
        "description": description, "enabled": enabled, "models": models,
        "module": module, "func_module": _get_func_module(path),
        "risk": risk or _get_risk(path, body), "smoke": smoke,
    }


CASES = [
    # ===== 查询类（默认启用）=====
    c("TC001", "设备信息查询", "/v2/GetDeviceList",
      {"pageNum": 1, "pageSize": 200},
      "$.code == 200;$.data exists;$.data[0].deviceSn exists;$.data[0].deviceModel exists",
      "查询类:设备列表(分页)", smoke="1"),
    c("TC002", "设备基本信息查询", "/v2/GetDeviceInfBySN",
      {"deviceSn": SN},
      "$.code == 200;$.data.deviceSn exists;$.data.deviceModel exists;$.data.firmwareVersion exists;$.data.inverterRatedPower exists",
      "查询类:设备基本信息", smoke="1"),
    c("TC003", "设备状态信息查询", "/v2/GetStatusInfBySN",
      {"deviceSn": SN},
      "$.code == 200;$.data.workStatus exists;$.data.runModel exists;$.data.batteryCommunication exists;[AquaVolt,SolarCube,SolarCube2] $.data.meterCommunication exists",
      "查询类:设备状态", smoke="1"),
    c("TC004", "设备运行数据查询", "/v2/GetRealTimeDataBySN",
      {"deviceSn": SN},
      "$.code == 200;$.data.batteryInfo.soc exists;[SolarCube,SolarCube2] $.data.pvInfo.pvTotalPower exists;$.data.gridInfo.gridPower exists;$.data.loadInfo.loadTotalPower exists",
      "查询类:实时运行数据", smoke="1"),
    c("TC005", "设备电量信息查询", "/v2/GetTotalEnergyDataBySN",
      {"deviceSn": SN},
      "$.code == 200;$.data.batteryInfo.totalChargeEnergy exists;[AquaVolt,SolarCube,SolarCube2] $.data.pvInfo.totalPvGeneration exists;$.data.gridInfo.totalBuyEnergy exists;$.data.loadInfo.totalElectricity exists",
      "查询类:累计电量", smoke="1"),
    c("TC006", "设备故障信息查询", "/v2/GetAlarmInfBySN",
      {"deviceSn": SN, "pageNum": 1, "pageSize": 200},
      "$.code == 200;$.data.total exists;$.data.list exists",
      "查询类:故障信息", smoke="1"),

    # ===== 控制类：查询（默认启用）=====
    c("TC007", "安规国家查询", "/v2/GetBaseSetting",
      {"deviceSn": SN}, "$.code == 200;$.data.safetyCountry exists", "控制类:安规国家查询"),
    c("TC009", "工作模式查询", "/v2/GetWorkModeSetting",
      {"deviceSn": SN}, "$.code == 200;$.data.workMode exists", "控制类:工作模式查询"),
    c("TC011", "电池参数查询", "/v2/GetBatterySetting",
      {"deviceSn": SN}, "$.code == 200;[AquaVolt,SolarCube,SolarCube2] $.data.onGridDischargeDod exists", "控制类:电池参数查询"),
    c("TC013", "负载控制查询", "/v2/GetLoadControlSetting",
      {"deviceSn": SN}, "$.code == 200;[SolarCube,SolarCube2] $.data.loadSwitch exists", "控制类:负载控制查询"),
    c("TC015", "峰值控制查询", "/v2/GetPeakControlSetting",
      {"deviceSn": SN}, "$.code == 200;[AquaVolt,SolarCube,SolarCube2] $.data.peakControlEnable exists", "控制类:峰值控制查询"),
    c("TC017", "高级参数查询", "/v2/GetAdvancedSetting",
      {"deviceSn": SN}, "$.code == 200;$.data.powerLevelSetting exists", "控制类:高级参数查询"),

    # ===== 控制类：下发（会真实修改设备参数，谨慎执行）=====
    c("TC008", "安规国家下发", "/v2/SetBaseSetting",
      {"deviceSn": SN, "safetyCountry": "43"}, "$.code == 200", "下发:安规国家(改设备,慎用)", "1"),
    c("TC010", "工作模式下发", "/v2/SetWorkModeSetting",
      {"deviceSn": SN, "workMode": "3", "[AquaVolt,SolarCube,SolarCube2] workGroups": [
          {"batteryWorkGroup": 1, "state": "1", "startTime": "07:00", "endTime": "17:00",
           "power": "2000", "mode": "1", "week": "0,1,2,3,4", "dodState": "1", "dod": "30",
           "socMaxChargeState": "1", "batterySocMaxCharge": "90"}]},
      "$.code == 200", "下发:工作模式(改设备,慎用)", "1"),
    c("TC012", "电池参数下发", "/v2/SetBatterySetting",
      {"deviceSn": SN, "[AquaVolt,SolarCube,SolarCube2] onGridDischargeDod": "20", "offGridDischargeDod": "20",
       "[AquaVolt,SolarCube,SolarCube2] batteryChargeLimit": "70", "[SolarCube,SolarCube2] batteryOffGridChargeLimit": "70"},
      "$.code == 200", "下发:电池参数(改设备,慎用)", "1"),
    c("TC014", "负载控制下发", "/v2/SetLoadControlSetting",
      {"deviceSn": SN, "loadSwitch": "0", "forceCloseTime": "07:00-17:00",
       "relayCloseSoc": "70", "relayOpenSoc": "30", "forceCloseOffGridOnly": "0",
       "alwaysCloseOnGridMode": "0", "pvPowerThreshold": "100"},
      "$.code == 200", "下发:负载控制(改设备,慎用)", "1", "SolarCube,SolarCube2"),
    c("TC016", "峰值控制下发", "/v2/SetPeakControlSetting",
      {"deviceSn": SN, "peakControlEnable": "0", "triggerSoc": "20",
       "timeRange": "17:00-22:00", "peakControlPower": "2000"},
      "$.code == 200", "下发:峰值控制(改设备,慎用)", "1", "AquaVolt,SolarCube,SolarCube2"),
    c("TC018", "高级参数下发", "/v2/SetAdvancedSetting",
      {"deviceSn": SN,
       "gridPowerLimitGroup": {"gridPowerLimitSwitch": "1", "gridPowerLimitValue": "500"},
       "backupPowerSwitch": "1", "pvConnectMode": "0",
       "extCtMeterGroup": {"extCtMeterSelect": "1", "ctApplication": "1"},
       "isoSetting": "500", "acCouplingEnable": "1", "powerLevelSetting": "1000",
       "groundDetectionEnable": "1"},
      "$.code == 200", "下发:高级参数(改设备,慎用)", "1", "SolarCube,SolarCube2"),
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
