# -*- coding: utf-8 -*-
"""API 测试参数化入口 + 公共 fixture。

配置优先级：命令行参数 > 环境变量 > config.yaml
设备机型在 collect 阶段通过 GetDeviceList 探测，动态参数化 device。
日志：控制台实时显示 + 写 logs/api_test_<时间戳>.log。
报告：session 结束落盘 reports/report_<时间戳>.html / .json。
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import pytest
import yaml

CONFIG_FILE = Path(__file__).parent / "config" / "config.yaml"
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))  # 让 tests 能 import 项目根的 common 包

from common import report
from core import backup
from core.device import discover_devices, normalize_device_list


def pytest_addoption(parser):
    parser.addoption("--base-url", action="store", default=None, help="接入域名（覆盖配置/环境变量）")
    parser.addoption("--app-id", action="store", default=None, help="应用 ID")
    parser.addoption("--app-secret", action="store", default=None, help="应用密钥")
    parser.addoption("--device-sn", action="store", default=None, help="被测设备序列号，多台用逗号分隔")
    parser.addoption("--timeout", action="store", default=None, help="请求超时(秒)")
    parser.addoption("--request-interval", action="store", default=None, help="请求间隔(秒)，控制频率避免触发接口限流")
    parser.addoption("--model", action="store", default=None, help="手动指定机型（AquaVolt/AquaVolt_LV/SolarCube），探测失败时兜底")
    parser.addoption("--no-restore", action="store_true", default=False, help="测试后不恢复设备参数（默认自动恢复）")
    parser.addoption("--module", action="store", default=None, help="按模块筛选用例（逗号分隔，如 cygni,commerce）")
    parser.addoption("--smoke", action="store_true", default=False, help="只跑冒烟用例（核心查询，不跑下发）")


def pytest_collection_modifyitems(config, items):
    """按 --module / --smoke 筛选用例（collect 后，不匹配的不执行）。"""
    module_arg = config.getoption("--module") or ""
    smoke = config.getoption("--smoke")
    if not module_arg and not smoke:
        return
    modules = {m.strip() for m in module_arg.split(",") if m.strip()}
    selected = []
    for item in items:
        cs = getattr(item, "callspec", None)
        case = cs.params.get("case") if cs and "case" in cs.params else None
        if case is None:  # 非 test_api 用例（如 unit test），保留
            selected.append(item)
            continue
        if modules and case.get("module") not in modules:
            continue
        if smoke and case.get("smoke") != "1":
            continue
        selected.append(item)
    items[:] = selected


def _load_config():
    if not CONFIG_FILE.exists():
        return {}
    return yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8")) or {}


def resolve_config(config):
    """合并配置（命令行 > 环境变量 > config.yaml）。无 fixture 依赖，collect 阶段可复用。"""
    api = _load_config().get("api", {})

    def get(option, env, key, default=""):
        return config.getoption(option) or os.getenv(env) or api.get(key, default)

    device_sn = get("--device-sn", "API_DEVICE_SN", "device_sn", "")
    return {
        "base_url": get("--base-url", "API_BASE_URL", "base_url", ""),
        "app_id": get("--app-id", "API_APP_ID", "app_id", ""),
        "app_secret": get("--app-secret", "API_APP_SECRET", "app_secret", ""),
        "device_sn": device_sn,
        "device_list": normalize_device_list(device_sn),
        "timeout": float(get("--timeout", "API_TIMEOUT", "timeout", 30)),
        "request_interval": float(get("--request-interval", "API_REQUEST_INTERVAL", "request_interval", 0.6)),
        "model": get("--model", "API_MODEL", "model", ""),
        "headers": api.get("headers") or {},
        "vars": api.get("vars") or {},
    }


def pytest_configure(config):
    """给 `api` logger 挂一个按天滚动的 FileHandler（同一天多次运行追加到同一文件）。"""
    logs_dir = ROOT_DIR / "common" / "logs"
    month = datetime.now().strftime("%Y%m")
    day = datetime.now().strftime("%Y%m%d")
    log_file = logs_dir / month / f"api_test_{day}.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # 每次运行在文件里写一个起始分隔标记（只进文件，便于区分同一天的多次运行）
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n{'=' * 64}\n# 运行开始 {now}\n{'=' * 64}\n")

    api_logger = logging.getLogger("api")
    api_logger.setLevel(logging.INFO)
    fh = logging.FileHandler(log_file, encoding="utf-8")  # 默认 mode='a'，同一天追加
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("%(asctime)s %(message)s", "%Y-%m-%d %H:%M:%S"))
    api_logger.addHandler(fh)
    config._api_log_file = str(log_file)


def pytest_sessionfinish(session, exitstatus):
    """测试全部结束后，把收集到的结果写成 HTML + JSON 报告。"""
    if session.config.getoption("collectonly"):
        return

    cfg = resolve_config(session.config)
    devices = getattr(session.config, "_api_devices", None) or []
    meta = {
        "base_url": cfg["base_url"],
        "devices": [
            f"{d['deviceSn']}[{d.get('model') or '未知'}/{d.get('hardware') or '未知型号'}]"
            for d in devices
        ],
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    day = datetime.now().strftime("%Y%m%d")
    report_dir = ROOT_DIR / "common" / "reports" / day
    conclusion = report.build_conclusion()
    html_path, json_path = report.write_reports(report_dir, meta, conclusion)
    print(f"\n[报告] HTML: {html_path}")
    print(f"[报告] JSON: {json_path}")
    print(f"[日志] {getattr(session.config, '_api_log_file', '')}")

    # 测试后恢复设备参数（--no-restore 跳过）
    if devices and not session.config.getoption("--no-restore"):
        try:
            summary = backup.restore_devices(cfg, devices, ROOT_DIR / "common" / "backup")
        except Exception as e:
            logging.getLogger("api").info("[恢复] 设备参数恢复异常: %s", e)
        else:
            logging.getLogger("api").info("[恢复] 设备参数恢复结果:")
            for sn, status, results in summary:
                failed = [r for r in results if r[0] == "fail"]
                tail = f"（{len(failed)} 个接口失败）" if failed else ""
                logging.getLogger("api").info("  %s: %s%s", sn, status, tail)
                for _p, _s, err in failed:
                    logging.getLogger("api").info("    - %s: %s", _p, err)


@pytest.fixture(scope="session")
def cfg(request):
    """合并后的配置字典。"""
    return resolve_config(request.config)


@pytest.fixture(scope="session")
def http_session(cfg):
    """复用 TCP 连接的 requests.Session（鉴权头在每次请求时动态签名生成）。"""
    import requests

    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    s.headers.update(cfg["headers"])
    return s


def _discover_devices_cached(config):
    """collect 阶段探测设备列表（带缓存，只探测一次），并测试前备份设备参数。"""
    if config.getoption("collectonly"):
        return []
    cached = getattr(config, "_api_devices", None)
    if cached is None:
        cfg = resolve_config(config)
        try:
            cached = discover_devices(cfg)
        except Exception:
            cached = []
        config._api_devices = cached
        # 测试前备份设备参数（--no-restore 跳过）
        if cached and not config.getoption("--no-restore"):
            try:
                backup.backup_devices(cfg, cached, ROOT_DIR / "common" / "backup")
                logging.getLogger("api").info(
                    "[备份] 设备参数备份完成: %s", "、".join(d["deviceSn"] for d in cached))
            except Exception as e:
                logging.getLogger("api").info("[备份] 设备参数备份失败: %s", e)
    return cached


def pytest_generate_tests(metafunc):
    """为 `device` 参数动态生成用例×设备矩阵。"""
    if "device" not in metafunc.fixturenames:
        return
    devices = _discover_devices_cached(metafunc.config)
    if devices:
        params = devices
        ids = [f"{d['deviceSn']}[{d.get('model') or '未知'}]" for d in devices]
    else:
        params = [None]
        ids = ["无可用设备(探测失败或未配置)"]
    metafunc.parametrize("device", params, ids=ids)
