# -*- coding: utf-8 -*-
"""数据驱动 API 测试：从 CSV 读取用例，逐条签名并发请求、断言。

数据：tests/api/data/api_testdata.csv（正常流）+ api_testdata_negative.csv（异常/边界/特殊参数）
设备/机型：collect 阶段通过 GetDeviceList 探测，动态参数化（见 conftest.py）
日志：完整请求报文 + 响应报文（见 logs/api_test_*.log）
报告：每条结果含完整报文，session 结束落盘 reports/（见 common/report.py）
运行：py -3 -m pytest tests/api -v [--app-id=... --app-secret=... --device-sn=SN1,SN2]
"""

import json
import logging
import time
from pathlib import Path

import pytest

from common import report
from core.assertions import (
    BusinessCodeError,
    FieldAssertionError,
    HttpStatusError,
    assert_response,
)
from core.device import filter_assertions, filter_body, model_matches
from core.loader import build_url, load_cases, resolve_vars
from core.sign import sign_request

log = logging.getLogger("api")

# 正常流 + 异常/边界/特殊参数用例，分别存放、合并加载（异常文件不存在则忽略）
CSV_FILES = [
    Path(__file__).parent / "data" / "api_testdata.csv",
    Path(__file__).parent / "data" / "api_testdata_negative.csv",
]

CASES = []
for _csv in CSV_FILES:
    CASES.extend(load_cases(_csv))
_PARAMS = CASES if CASES else [None]
_IDS = [f"{c['case_id']} {c['path'].rstrip('/').split('/')[-1]} {c['name']}" for c in CASES] if CASES else ["CSV 中无用例"]


def _assertion_count(assertions):
    return sum(1 for e in (assertions or "").split(";") if e.strip())


def _record(case, device, url, status, outcome, error="", duration="",
            request=None, response=None):
    """把一条用例结果（含完整请求/响应报文）写入报告收集器。"""
    report.record({
        "case_id": (case or {}).get("case_id", ""),
        "name": (case or {}).get("name", ""),
        "device_sn": (device or {}).get("deviceSn", ""),
        "model": (device or {}).get("model") or "",
        "method": (case or {}).get("method", ""),
        "path": (case or {}).get("path", ""),
        "description": (case or {}).get("description", ""),
        "url": url or "",
        "status": status,
        "outcome": outcome,
        "duration": duration,
        "error": error,
        "request": request or {},
        "response": response or {},
    })


@pytest.mark.parametrize("case", _PARAMS, ids=_IDS)
def test_api(http_session, cfg, case, device):
    if case is None:
        _record(None, None, None, None, "SKIP", f"CSV 中无用例，请先填写 {CSV_FILE}")
        pytest.skip(f"CSV 中无用例，请先填写 {CSV_FILE}")
    if device is None:
        _record(case, None, None, None, "SKIP", "未探测到可用设备：请检查 device_sn 配置、网络与鉴权")
        pytest.skip("未探测到可用设备：请检查 device_sn 配置、网络与鉴权")

    model = device.get("model")
    case_id = case["case_id"]
    url = build_url(case["path"], cfg["base_url"])

    # 1. 用例级机型过滤（CSV models 列：空=全机型，否则仅指定机型）
    if case.get("models") and not model_matches(case["models"], model):
        reason = f"机型不匹配: {case_id} 仅支持 {sorted(case['models'])}，当前机型 {model or '未知'}"
        _record(case, device, url, None, "SKIP", reason)
        pytest.skip(reason)

    # 2. 断言级机型裁剪（[机型] 前缀断言，不匹配的跳过）
    assertions = filter_assertions(case["assertions"], model)

    # 3. 模板变量替换（{{deviceSn}} -> 当前设备的 SN）
    vars_map = {**(cfg.get("vars") or {}), "deviceSn": device["deviceSn"]}
    body = resolve_vars(case["body"], vars_map)
    params = resolve_vars(case["params"], vars_map)

    # 3.5 按机型裁剪下发 body（字段名带 [机型] 前缀的，不匹配当前机型则剔除）
    body = filter_body(body, model)

    # 4. 序列化 body（签名与发送体必须完全一致）
    body_str = None
    if body is not None:
        body_str = (json.dumps(body, sort_keys=True, separators=(",", ":"))
                    if isinstance(body, dict) else str(body))

    # 5. 自签名鉴权，组装完整请求头
    auth_headers = sign_request(
        cfg["app_id"], cfg["app_secret"],
        case["method"], case["path"], body_str or "",
    )
    headers = {**(case["headers"] or {}), **auth_headers}

    # ---- 完整请求报文日志 ----
    log.info("=" * 64)
    log.info("[%s] %s", case_id, case["name"])
    log.info("设备: %s  机型: %s", device["deviceSn"], model or "未知")
    log.info("请求: %s %s", case["method"], url)
    log.info("请求头: %s", json.dumps(headers, ensure_ascii=False))
    log.info("请求体: %s", body_str or "(空)")

    status = None
    resp = None
    outcome = "PASS"
    error = ""
    start = time.time()
    try:
        # 控制请求频率，避免触发接口限流（文档 ≤2 次/秒，默认间隔 0.6s 留余量）
        interval = cfg.get("request_interval")
        if interval:
            time.sleep(interval)
        resp = http_session.request(
            method=case["method"],
            url=url,
            params=params,
            data=body_str,
            headers=headers,
            timeout=cfg["timeout"],
        )
        status = resp.status_code
        # ---- 完整响应报文日志 ----
        log.info("响应状态: %s", status)
        log.info("响应头: %s", json.dumps(dict(resp.headers), ensure_ascii=False))
        log.info("响应体: %s", resp.text)
        assert_response(resp, case["expected_status"], case["expected_code"], assertions)
        log.info("结果: 通过(PASS)  断言 %d 条", _assertion_count(assertions))
    except HttpStatusError as e:  # HTTP 状态码不符 -> 不通过
        outcome = "FAIL"
        error = str(e)
        log.info("结果: 不通过(FAIL)  %s", e)
        raise
    except BusinessCodeError as e:  # code 非预期 / 响应体非法 -> 不通过
        outcome = "FAIL"
        error = str(e)
        log.info("结果: 不通过(FAIL)  %s", e)
        raise
    except FieldAssertionError as e:  # HTTP 200 且 code=200，但字段与文档不一致 -> 待确认
        outcome = "PENDING"
        error = str(e)
        log.info("结果: 待确认(PENDING)  %s", e)
        raise
    except Exception as e:  # 请求异常（超时/连接失败等）-> 不通过
        outcome = "FAIL"
        error = str(e)
        raise
    finally:
        _record(
            case, device, url, status, outcome, error,
            f"{time.time() - start:.2f}s",
            request={"headers": headers, "body": body_str or ""},
            response={
                "status": status,
                "headers": dict(resp.headers) if resp is not None else {},
                "body": resp.text if resp is not None else "",
            },
        )
