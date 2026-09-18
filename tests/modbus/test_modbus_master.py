# -*- coding: utf-8 -*-
"""
pytest 版 Modbus 主站读写验证。

前提：先启动模拟器（从站桩）
    py -3 tools/modbus/modbus_multi_device.py
再运行测试：
    py -3 -m pytest -v

未启动模拟器时，用例会自动 skip（提示先启动模拟器），不会报错。
"""

import pytest
from pymodbus.client import ModbusTcpClient

HOST = "127.0.0.1"
PORT = 502
UNITS = [1, 2, 3]  # 对应模拟器里的从站地址

# 寄存器点表（保持寄存器，地址从 0 开始），详见 docs/devices/register-map.md
SOC, VOLT, CUR, TEMP, STATE, ALARM = 0, 1, 2, 3, 4, 5
VALID_STATES = {0, 1, 2, 3}  # 0待机 1充电 2放电 3故障


@pytest.fixture(scope="module")
def client():
    """建立到模拟器的 TCP 连接；未启动模拟器则整个模块跳过。"""
    c = ModbusTcpClient(HOST, port=PORT)
    if not c.connect():
        pytest.skip(
            f"连接 {HOST}:{PORT} 失败，请先运行 py -3 tools/modbus/modbus_multi_device.py"
        )
    yield c
    c.close()


@pytest.mark.parametrize("unit", UNITS)
def test_read_registers(client, unit):
    """逐台读 6 个寄存器，校验数值落在合法范围内。"""
    rr = client.read_holding_registers(0, count=6, device_id=unit)
    assert not rr.isError(), f"从站 {unit} 读取失败: {rr}"

    soc, volt, cur, temp, state, alarm = rr.registers
    assert 0 <= soc <= 100, f"SOC 越界: {soc}"
    assert state in VALID_STATES, f"状态非法: {state}"
    assert alarm == 0, f"告警码非 0: {alarm}"


def test_write_state_roundtrip(client):
    """写状态寄存器：3(故障)→读回→1(充电)→读回，验证往返一致，最后还原。"""
    try:
        client.write_register(STATE, 3, device_id=1)
        rr = client.read_holding_registers(STATE, count=1, device_id=1)
        assert rr.registers[0] == 3, "写 3(故障) 后读回不一致"
    finally:
        client.write_register(STATE, 1, device_id=1)  # 无论成败都还原为充电

    rr = client.read_holding_registers(STATE, count=1, device_id=1)
    assert rr.registers[0] == 1, "写 1(充电) 后读回不一致"
