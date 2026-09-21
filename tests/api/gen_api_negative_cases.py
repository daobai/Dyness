# -*- coding: utf-8 -*-
"""生成户用储能（AquaVolt/AquaVolt_LV/SolarCube/SolarCube2）异常/边界/特殊参数用例 CSV。

覆盖 18 个接口的：异常(deviceSn 不存在)、特殊参数(空/缺失)、边界外(越界/枚举非法)、
边界值(合法最小/最大)。预期业务码：参数错误 -> 500（接口文档 L321「500 Invalid Parameter」），
合法边界值 -> 200。运行：py -3 tests/api/gen_api_negative_cases.py
"""

import csv
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "data" / "api_household_negative.csv"
FIELDS = ["case_id", "name", "method", "path", "headers", "params", "body",
          "expected_status", "expected_code", "assertions", "description", "enabled",
          "models", "module", "smoke"]

SN = "{{deviceSn}}"            # 模板变量，运行时替换为当前设备 SN
BAD_SN = "NOT_EXIST_SN_000"    # 不存在的设备序列号


def neg(case_id, name, path, body, description, expected_code="500", enabled="1", models="",
        module="household", smoke="0"):
    """异常用例：默认预期业务码 500（参数错误），HTTP 状态码仍 200。"""
    return {
        "case_id": case_id, "name": name, "method": "POST", "path": path,
        "headers": None, "params": None, "body": body,
        "expected_status": 200, "expected_code": expected_code,
        "assertions": "", "description": description, "enabled": enabled, "models": models,
        "module": module, "smoke": smoke,
    }


# 17 个 deviceSn 必填接口（11 查询 + 6 下发），用于批量生成 deviceSn 异常
_DEVICE_SN_PATHS = [
    ("GetDeviceInfBySN", "设备基本信息查询"),
    ("GetStatusInfBySN", "设备状态信息查询"),
    ("GetRealTimeDataBySN", "设备运行数据查询"),
    ("GetTotalEnergyDataBySN", "设备电量信息查询"),
    ("GetAlarmInfBySN", "设备故障信息查询"),
    ("GetBaseSetting", "安规国家查询"),
    ("GetWorkModeSetting", "工作模式查询"),
    ("GetBatterySetting", "电池参数查询"),
    ("GetLoadControlSetting", "负载控制查询"),
    ("GetPeakControlSetting", "峰值控制查询"),
    ("GetAdvancedSetting", "高级参数查询"),
    ("SetBaseSetting", "安规国家下发"),
    ("SetWorkModeSetting", "工作模式下发"),
    ("SetBatterySetting", "电池参数下发"),
    ("SetLoadControlSetting", "负载控制下发"),
    ("SetPeakControlSetting", "峰值控制下发"),
    ("SetAdvancedSetting", "高级参数下发"),
]

# 下发接口的正常 body（用于变异出越界/枚举非法参数）
_WORKGROUP = {
    "batteryWorkGroup": 1, "state": "1", "startTime": "07:00", "endTime": "17:00",
    "power": "2000", "mode": "1", "week": "0,1,2,3,4", "dodState": "1", "dod": "30",
    "socMaxChargeState": "1", "batterySocMaxCharge": "90",
}


def _wg(power=None, dod=None):
    g = dict(_WORKGROUP)
    if power is not None:
        g["power"] = power
    if dod is not None:
        g["dod"] = dod
    return g


CASES = []

# ===== 1. deviceSn 异常 / 特殊参数（17 接口 × 2）=====
_cid = 101
for path, cn in _DEVICE_SN_PATHS:
    p = f"/v2/{path}"
    CASES.append(neg(f"TC{_cid}", f"{cn}-deviceSn不存在", p,
                     {"deviceSn": BAD_SN}, "异常:deviceSn不存在"))
    _cid += 1
    CASES.append(neg(f"TC{_cid}", f"{cn}-deviceSn为空", p,
                     {"deviceSn": ""}, "特殊参数:deviceSn空字符串"))
    _cid += 1

# ===== 2. 分页参数越界 / 特殊参数 =====
CASES.append(neg(f"TC{_cid}", "设备信息查询-pageSize越界", "/v2/GetDeviceList",
                 {"pageNum": 1, "pageSize": 201}, "边界外:pageSize=201(最大200)")); _cid += 1
CASES.append(neg(f"TC{_cid}", "设备信息查询-pageSize为0", "/v2/GetDeviceList",
                 {"pageNum": 1, "pageSize": 0}, "边界外:pageSize=0")); _cid += 1
CASES.append(neg(f"TC{_cid}", "设备信息查询-pageSize非数字", "/v2/GetDeviceList",
                 {"pageNum": 1, "pageSize": "abc"}, "特殊参数:pageSize类型错误")); _cid += 1
CASES.append(neg(f"TC{_cid}", "设备故障信息查询-pageSize越界", "/v2/GetAlarmInfBySN",
                 {"deviceSn": SN, "pageNum": 1, "pageSize": 201}, "边界外:pageSize=201(最大200)")); _cid += 1

# ===== 3. 下发接口：枚举非法 / 越界 =====
CASES.append(neg(f"TC{_cid}", "安规国家下发-safetyCountry越界", "/v2/SetBaseSetting",
                 {"deviceSn": SN, "safetyCountry": "999"}, "边界外:safetyCountry=999(枚举外)")); _cid += 1
CASES.append(neg(f"TC{_cid}", "工作模式下发-workMode非法", "/v2/SetWorkModeSetting",
                 {"deviceSn": SN, "workMode": "99", "workGroups": [_wg()]}, "边界外:workMode=99(枚举外)", models="AquaVolt,SolarCube,SolarCube2")); _cid += 1
CASES.append(neg(f"TC{_cid}", "工作模式下发-workGroups功率越界", "/v2/SetWorkModeSetting",
                 {"deviceSn": SN, "workMode": "3", "workGroups": [_wg(power="2001")]}, "边界外:workGroups.power=2001(最大2000)", models="AquaVolt,SolarCube,SolarCube2")); _cid += 1
CASES.append(neg(f"TC{_cid}", "电池参数下发-onGridDischargeDod越界", "/v2/SetBatterySetting",
                 {"deviceSn": SN, "onGridDischargeDod": "101"}, "边界外:onGridDischargeDod=101(最大100)", models="AquaVolt,SolarCube,SolarCube2")); _cid += 1
CASES.append(neg(f"TC{_cid}", "电池参数下发-onGridDischargeDod为负", "/v2/SetBatterySetting",
                 {"deviceSn": SN, "onGridDischargeDod": "4"}, "边界外:onGridDischargeDod=4(最小5-1)", models="AquaVolt,SolarCube,SolarCube2")); _cid += 1
CASES.append(neg(f"TC{_cid}", "电池参数下发-batteryChargeLimit越界", "/v2/SetBatterySetting",
                 {"deviceSn": SN, "batteryChargeLimit": "101"}, "边界外:batteryChargeLimit=101(最大100)", models="AquaVolt,SolarCube,SolarCube2")); _cid += 1
CASES.append(neg(f"TC{_cid}", "负载控制下发-loadSwitch非法", "/v2/SetLoadControlSetting",
                 {"deviceSn": SN, "loadSwitch": "2"}, "边界外:loadSwitch=2(枚举0/1)", models="SolarCube,SolarCube2")); _cid += 1
CASES.append(neg(f"TC{_cid}", "负载控制下发-relayCloseSoc越界", "/v2/SetLoadControlSetting",
                 {"deviceSn": SN, "relayCloseSoc": "101"}, "边界外:relayCloseSoc=101(最大100)", models="SolarCube,SolarCube2")); _cid += 1
CASES.append(neg(f"TC{_cid}", "负载控制下发-pvPowerThreshold越界", "/v2/SetLoadControlSetting",
                 {"deviceSn": SN, "pvPowerThreshold": "65536"}, "边界外:pvPowerThreshold=65536(最大65535)", models="SolarCube,SolarCube2")); _cid += 1
CASES.append(neg(f"TC{_cid}", "峰值控制下发-triggerSoc越界", "/v2/SetPeakControlSetting",
                 {"deviceSn": SN, "triggerSoc": "101"}, "边界外:triggerSoc=101(最大100)", models="AquaVolt,SolarCube,SolarCube2")); _cid += 1
CASES.append(neg(f"TC{_cid}", "峰值控制下发-peakControlEnable非法", "/v2/SetPeakControlSetting",
                 {"deviceSn": SN, "peakControlEnable": "2"}, "边界外:peakControlEnable=2(枚举0/1)", models="AquaVolt,SolarCube,SolarCube2")); _cid += 1
CASES.append(neg(f"TC{_cid}", "高级参数下发-powerLevelSetting越界", "/v2/SetAdvancedSetting",
                 {"deviceSn": SN, "powerLevelSetting": "2001"}, "边界外:powerLevelSetting=2001(最大2000)")); _cid += 1
CASES.append(neg(f"TC{_cid}", "高级参数下发-isoSetting越界", "/v2/SetAdvancedSetting",
                 {"deviceSn": SN, "isoSetting": "9"}, "边界外:isoSetting=9(最小10)", models="SolarCube,SolarCube2")); _cid += 1
CASES.append(neg(f"TC{_cid}", "高级参数下发-gridPowerLimitValue越界", "/v2/SetAdvancedSetting",
                 {"deviceSn": SN, "gridPowerLimitGroup": {"gridPowerLimitValue": "801"}}, "边界外:gridPowerLimitValue=801(最大800)", models="AquaVolt,SolarCube,SolarCube2")); _cid += 1

# ===== 4. 必填缺失 =====
CASES.append(neg(f"TC{_cid}", "安规国家下发-缺safetyCountry", "/v2/SetBaseSetting",
                 {"deviceSn": SN}, "必填缺失:缺safetyCountry")); _cid += 1
CASES.append(neg(f"TC{_cid}", "工作模式下发-缺workGroups", "/v2/SetWorkModeSetting",
                 {"deviceSn": SN, "workMode": "3"}, "必填缺失:缺workGroups", models="AquaVolt,SolarCube,SolarCube2")); _cid += 1
CASES.append(neg(f"TC{_cid}", "工作模式下发-缺workMode", "/v2/SetWorkModeSetting",
                 {"deviceSn": SN, "workGroups": [_wg()]}, "必填缺失:缺workMode", models="AquaVolt,SolarCube,SolarCube2")); _cid += 1

# ===== 5. 边界值（合法，预期 200）=====
CASES.append(neg(f"TC{_cid}", "电池参数下发-onGridDischargeDod最小值", "/v2/SetBatterySetting",
                 {"deviceSn": SN, "onGridDischargeDod": "5"}, "边界值:onGridDischargeDod=5(最小)", "200", models="AquaVolt,SolarCube,SolarCube2")); _cid += 1
CASES.append(neg(f"TC{_cid}", "电池参数下发-onGridDischargeDod最大值", "/v2/SetBatterySetting",
                 {"deviceSn": SN, "onGridDischargeDod": "100"}, "边界值:onGridDischargeDod=100(最大)", "200", models="AquaVolt,SolarCube,SolarCube2")); _cid += 1
CASES.append(neg(f"TC{_cid}", "电池参数下发-batteryChargeLimit最小值", "/v2/SetBatterySetting",
                 {"deviceSn": SN, "batteryChargeLimit": "10"}, "边界值:batteryChargeLimit=10(最小)", "200", models="AquaVolt,SolarCube,SolarCube2")); _cid += 1
CASES.append(neg(f"TC{_cid}", "峰值控制下发-triggerSoc最大值", "/v2/SetPeakControlSetting",
                 {"deviceSn": SN, "triggerSoc": "100"}, "边界值:triggerSoc=100(最大)", "200", models="AquaVolt,SolarCube,SolarCube2")); _cid += 1

# ===== 6. 枚举参数多值覆盖（合法，预期 200；已在正常用例中的取值不再重复）=====
# safetyCountry 枚举 0/2/37/43/46/106（43 已在正常用例）
for _v in ["0", "2", "37", "46", "106"]:
    CASES.append(neg(f"TC{_cid}", f"安规国家下发-safetyCountry={_v}", "/v2/SetBaseSetting",
                     {"deviceSn": SN, "safetyCountry": _v}, f"枚举值:safetyCountry={_v}", "200")); _cid += 1
# workMode 枚举 SolarCube,SolarCube2 0/1/2/3/6（3 已在正常用例）
for _v, _m in [("0", "AquaVolt,SolarCube,SolarCube2"), ("1", "AquaVolt,SolarCube,SolarCube2"), ("2", "AquaVolt,SolarCube,SolarCube2"), ("6", "SolarCube,SolarCube2")]:
    CASES.append(neg(f"TC{_cid}", f"工作模式下发-workMode={_v}", "/v2/SetWorkModeSetting",
                     {"deviceSn": SN, "workMode": _v, "workGroups": [_wg()]}, f"枚举值:workMode={_v}", "200", models=_m)); _cid += 1
# extCtMeterSelect 枚举 0/1/2（1 已在正常用例）
CASES.append(neg(f"TC{_cid}", "高级参数下发-extCtMeterSelect=0", "/v2/SetAdvancedSetting",
                 {"deviceSn": SN, "extCtMeterGroup": {"extCtMeterSelect": "0"}},
                 "枚举值:extCtMeterSelect=0(无连接)", "200", models="AquaVolt,SolarCube,SolarCube2")); _cid += 1
CASES.append(neg(f"TC{_cid}", "高级参数下发-extCtMeterSelect=2", "/v2/SetAdvancedSetting",
                 {"deviceSn": SN, "extCtMeterGroup": {"extCtMeterSelect": "2", "meterApplication": "0"}},
                 "枚举值:extCtMeterSelect=2(外置Meter)", "200", models="AquaVolt,SolarCube,SolarCube2")); _cid += 1

# ===== 7. 补齐缺失参数：越界 / 枚举非法（预期 500）=====
# SetBatterySetting 补齐 offGridDischargeDod / batteryOffGridChargeLimit
CASES.append(neg(f"TC{_cid}", "电池参数下发-offGridDischargeDod越界", "/v2/SetBatterySetting",
                 {"deviceSn": SN, "offGridDischargeDod": "101"}, "边界外:offGridDischargeDod=101(最大100)")); _cid += 1
CASES.append(neg(f"TC{_cid}", "电池参数下发-offGridDischargeDod越界小", "/v2/SetBatterySetting",
                 {"deviceSn": SN, "offGridDischargeDod": "4"}, "边界外:offGridDischargeDod=4(最小5-1)")); _cid += 1
CASES.append(neg(f"TC{_cid}", "电池参数下发-offGridDischargeDod最小值", "/v2/SetBatterySetting",
                 {"deviceSn": SN, "offGridDischargeDod": "5"}, "边界值:offGridDischargeDod=5(最小)", "200")); _cid += 1
CASES.append(neg(f"TC{_cid}", "电池参数下发-offGridDischargeDod最大值", "/v2/SetBatterySetting",
                 {"deviceSn": SN, "offGridDischargeDod": "100"}, "边界值:offGridDischargeDod=100(最大)", "200")); _cid += 1
CASES.append(neg(f"TC{_cid}", "电池参数下发-batteryOffGridChargeLimit越界", "/v2/SetBatterySetting",
                 {"deviceSn": SN, "batteryOffGridChargeLimit": "101"}, "边界外:batteryOffGridChargeLimit=101(最大100)", models="SolarCube,SolarCube2")); _cid += 1
# SetLoadControlSetting 补齐 forceCloseTime / relayOpenSoc / forceCloseOffGridOnly / alwaysCloseOnGridMode
CASES.append(neg(f"TC{_cid}", "负载控制下发-forceCloseTime格式错误", "/v2/SetLoadControlSetting",
                 {"deviceSn": SN, "forceCloseTime": "abc"}, "特殊参数:forceCloseTime格式错误", models="SolarCube,SolarCube2")); _cid += 1
CASES.append(neg(f"TC{_cid}", "负载控制下发-relayOpenSoc越界", "/v2/SetLoadControlSetting",
                 {"deviceSn": SN, "relayOpenSoc": "101"}, "边界外:relayOpenSoc=101(最大100)", models="SolarCube,SolarCube2")); _cid += 1
CASES.append(neg(f"TC{_cid}", "负载控制下发-forceCloseOffGridOnly非法", "/v2/SetLoadControlSetting",
                 {"deviceSn": SN, "forceCloseOffGridOnly": "2"}, "边界外:forceCloseOffGridOnly=2(枚举0/1)", models="SolarCube,SolarCube2")); _cid += 1
CASES.append(neg(f"TC{_cid}", "负载控制下发-alwaysCloseOnGridMode非法", "/v2/SetLoadControlSetting",
                 {"deviceSn": SN, "alwaysCloseOnGridMode": "2"}, "边界外:alwaysCloseOnGridMode=2(枚举0/1)", models="SolarCube,SolarCube2")); _cid += 1
# SetPeakControlSetting 补齐 timeRange / peakControlPower
CASES.append(neg(f"TC{_cid}", "峰值控制下发-timeRange格式错误", "/v2/SetPeakControlSetting",
                 {"deviceSn": SN, "timeRange": "abc"}, "特殊参数:timeRange格式错误", models="AquaVolt,SolarCube,SolarCube2")); _cid += 1
CASES.append(neg(f"TC{_cid}", "峰值控制下发-peakControlPower越界", "/v2/SetPeakControlSetting",
                 {"deviceSn": SN, "peakControlPower": "65536"}, "边界外:peakControlPower=65536(最大65535)", models="AquaVolt,SolarCube,SolarCube2")); _cid += 1
# SetAdvancedSetting 补齐多个枚举非法（extCtMeterSelect 为嵌套字段）
CASES.append(neg(f"TC{_cid}", "高级参数下发-backupPowerSwitch非法", "/v2/SetAdvancedSetting",
                 {"deviceSn": SN, "backupPowerSwitch": "2"}, "边界外:backupPowerSwitch=2(枚举0/1)", models="AquaVolt,SolarCube,SolarCube2")); _cid += 1
CASES.append(neg(f"TC{_cid}", "高级参数下发-pvConnectMode非法", "/v2/SetAdvancedSetting",
                 {"deviceSn": SN, "pvConnectMode": "2"}, "边界外:pvConnectMode=2(枚举0/1)", models="AquaVolt,SolarCube,SolarCube2")); _cid += 1
CASES.append(neg(f"TC{_cid}", "高级参数下发-extCtMeterSelect非法", "/v2/SetAdvancedSetting",
                 {"deviceSn": SN, "extCtMeterGroup": {"extCtMeterSelect": "3"}},
                 "边界外:extCtMeterSelect=3(枚举0/1/2)", models="AquaVolt,SolarCube,SolarCube2")); _cid += 1
CASES.append(neg(f"TC{_cid}", "高级参数下发-acCouplingEnable非法", "/v2/SetAdvancedSetting",
                 {"deviceSn": SN, "acCouplingEnable": "2"}, "边界外:acCouplingEnable=2(枚举0/1)", models="AquaVolt,SolarCube,SolarCube2")); _cid += 1
CASES.append(neg(f"TC{_cid}", "高级参数下发-groundDetectionEnable非法", "/v2/SetAdvancedSetting",
                 {"deviceSn": SN, "groundDetectionEnable": "2"}, "边界外:groundDetectionEnable=2(枚举0/1)", models="AquaVolt,SolarCube,SolarCube2")); _cid += 1
CASES.append(neg(f"TC{_cid}", "高级参数下发-offGridOutputSwitch非法", "/v2/SetAdvancedSetting",
                 {"deviceSn": SN, "offGridOutputSwitch": "2"}, "边界外:offGridOutputSwitch=2(枚举0/1)", models="AquaVolt_LV")); _cid += 1
CASES.append(neg(f"TC{_cid}", "高级参数下发-sleepDetectionLevel非法", "/v2/SetAdvancedSetting",
                 {"deviceSn": SN, "sleepDetectionLevel": "3"}, "边界外:sleepDetectionLevel=3(枚举0/1/2)", models="AquaVolt_LV")); _cid += 1

# ===== 8. powerLevelSetting 边界值/等价类（范围 700~2000，每 10W 一档）=====
# 等价类代表值 1000 已用于正常用例 TC018；边界外 2001 见前面 TC150
CASES.append(neg(f"TC{_cid}", "高级参数下发-powerLevelSetting最小值", "/v2/SetAdvancedSetting",
                 {"deviceSn": SN, "powerLevelSetting": "700"}, "边界值:powerLevelSetting=700(最小)", "200")); _cid += 1
CASES.append(neg(f"TC{_cid}", "高级参数下发-powerLevelSetting最大值", "/v2/SetAdvancedSetting",
                 {"deviceSn": SN, "powerLevelSetting": "2000"}, "边界值:powerLevelSetting=2000(最大)", "200")); _cid += 1
CASES.append(neg(f"TC{_cid}", "高级参数下发-powerLevelSetting越界小", "/v2/SetAdvancedSetting",
                 {"deviceSn": SN, "powerLevelSetting": "699"}, "边界外:powerLevelSetting=699(最小700-1)")); _cid += 1
CASES.append(neg(f"TC{_cid}", "高级参数下发-powerLevelSetting非挡位", "/v2/SetAdvancedSetting",
                 {"deviceSn": SN, "powerLevelSetting": "705"}, "特殊参数:powerLevelSetting=705(非10W挡位)")); _cid += 1

# ===== 9. gridPowerLimitValue 边界值（范围 0~800）=====
CASES.append(neg(f"TC{_cid}", "高级参数下发-gridPowerLimitValue最小值", "/v2/SetAdvancedSetting",
                 {"deviceSn": SN, "gridPowerLimitGroup": {"gridPowerLimitValue": "0"}}, "边界值:gridPowerLimitValue=0(最小)", "200", models="AquaVolt,SolarCube,SolarCube2")); _cid += 1
CASES.append(neg(f"TC{_cid}", "高级参数下发-gridPowerLimitValue最大值", "/v2/SetAdvancedSetting",
                 {"deviceSn": SN, "gridPowerLimitGroup": {"gridPowerLimitValue": "800"}}, "边界值:gridPowerLimitValue=800(最大)", "200", models="AquaVolt,SolarCube,SolarCube2")); _cid += 1


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
    print(f"已生成 {len(CASES)} 条异常用例 -> {OUT}")


if __name__ == "__main__":
    main()
