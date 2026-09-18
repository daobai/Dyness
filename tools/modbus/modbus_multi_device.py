# -*- coding: utf-8 -*-
"""
Modbus 多设备模拟器 —— 用 Python 在一台电脑上同时模拟多台储能设备（从站）

为什么用这个：免费版 Modbus 工具（Redisant / Modbus Poll）只能开 1 个连接/实例；
这个脚本可以同时模拟任意多台从站设备，彻底绕开限制。

运行：  py -3 tools/modbus/modbus_multi_device.py
停止：  按 Ctrl + C

自定义设备：改下面 DEVICES 字典，加一行就是多一台设备。

寄存器点表（保持寄存器，地址从 0 开始）：
  地址 0 = SOC(%)        地址 1 = 电压(V)×10       地址 2 = 电流(A)×10（充/放方向看地址 4）
  地址 3 = 温度(℃)×10    地址 4 = 状态(0待机 1充电 2放电 3故障)   地址 5 = 告警码(0无)
  地址 6 = 心跳 = 模拟器已运行秒数（自动每秒变化，用来确认设备“活着”、平台在实时读）
"""

import time

from pymodbus.server import StartTcpServer
from pymodbus.simulator import SimData, SimDevice, DataType

# ============ 设备配置（按需增删）============
# key = 从站地址(Slave ID / Unit ID)，主站读取时用 device_id 指定
# regs 顺序 = 上面点表：SOC, 电压×10, 电流×10, 温度×10, 状态, 告警码, 心跳
DEVICES = {
    1: {"name": "SN001", "regs": [86,  523, 121, 312, 1, 0, 0]},
    2: {"name": "SN002", "regs": [45,  508, 80,  298, 2, 0, 0]},
    3: {"name": "SN003", "regs": [100, 530, 0,   305, 0, 0, 0]},
}

PORT = 502
HB_ADDR = 6        # 心跳寄存器地址
START_TIME = time.monotonic()  # 记录启动时刻，用于算“运行秒数”


async def heartbeat_action(function_code, start_address, address, count,
                           current_registers, set_values):
    """每次读寄存器时回调：把心跳寄存器(地址6)实时填成“已运行秒数”。"""
    idx = HB_ADDR - start_address
    if 0 <= idx < len(current_registers):
        current_registers[idx] = int(time.monotonic() - START_TIME) & 0xFFFF
    return None  # None = 正常放行


def build_devices():
    devices = []
    for unit, d in DEVICES.items():
        dev = SimDevice(
            id=unit,
            simdata=[
                SimData(
                    address=0,
                    count=len(d["regs"]),
                    values=d["regs"],
                    datatype=DataType.REGISTERS,
                )
            ],
            action=heartbeat_action,
        )
        devices.append(dev)
    return devices


if __name__ == "__main__":
    devices = build_devices()

    print("=" * 60)
    print("  Modbus 多设备模拟器已启动")
    print(f"  监听: 0.0.0.0:{PORT}")
    for unit, d in DEVICES.items():
        r = d["regs"]
        print(f"    从站 {unit} = {d['name']}  SOC={r[0]}%  电压={r[1] / 10:.1f}V  状态={r[4]}")
    print("  主站读取时用 device_id = 1 / 2 / 3 ...")
    print("  按 Ctrl+C 停止")
    print("=" * 60)

    StartTcpServer(context=devices, address=("0.0.0.0", PORT))
