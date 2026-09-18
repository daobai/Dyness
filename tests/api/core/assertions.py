# -*- coding: utf-8 -*-
"""响应断言工具：状态码 + 业务码 + 字段级 JSONPath 校验。

结果三分类（供 test_api.py 据此判定 outcome）：
  HttpStatusError     —— HTTP 状态码与预期不符              -> FAIL（不通过）
  BusinessCodeError   —— 响应体非法 / 缺 code / code != 200  -> FAIL（不通过）
  FieldAssertionError —— HTTP 200 且 code=200，但字段与文档不一致 -> PENDING（待确认）

其余异常（请求超时、连接失败等）由调用方捕获，也归为 FAIL（不通过）。
"""

from jsonpath_ng import parse


class HttpStatusError(AssertionError):
    """HTTP 状态码与预期不符（不通过）。"""


class BusinessCodeError(AssertionError):
    """响应体非 JSON / 顶层非对象 / 缺 code / code 非 200（不通过）。"""


class FieldAssertionError(AssertionError):
    """字段级断言失败（HTTP 200 且 code=200，但参数与文档不一致，待确认）。"""


def jsonpath_get(data, expr):
    """按 JSONPath 表达式取值，返回匹配到的值列表（无匹配返回空列表）。"""
    if data is None:
        return []
    try:
        return [m.value for m in parse(expr).find(data)]
    except Exception as e:  # 表达式非法等
        raise AssertionError(f"JSONPath 表达式非法: {expr} -> {e}")


def _coerce(s):
    """把字符串转成 int/float/bool/None，转不了就保持原字符串。"""
    if not isinstance(s, str):
        return s
    s = s.strip()
    if s.lower() in ("null", "none", ""):
        return None
    if s.lower() == "true":
        return True
    if s.lower() == "false":
        return False
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _check_one(expr, data):
    """解析并执行单条断言表达式：`<jsonpath> <操作符> [期望值]`。"""
    parts = expr.split(None, 2)
    if len(parts) == 2:
        path, op = parts
        raw_expected = ""
    elif len(parts) == 3:
        path, op, raw_expected = parts
    else:
        raise AssertionError(f"断言表达式无法解析（格式: <jsonpath> <操作符> [期望值]）: {expr}")

    matches = jsonpath_get(data, path)
    actual = matches[0] if matches else None

    # 归一化：响应里数字/布尔常为字符串（如 "200"、"true"），统一转成数值便于比较
    actual_norm = _coerce(actual) if isinstance(actual, str) else actual

    if op == "exists":
        assert matches, f"断言失败: {path} 应存在，但未匹配到"
        return
    if op == "not_exists":
        assert not matches, f"断言失败: {path} 不应存在，但值为 {actual!r}"
        return

    expected = _coerce(raw_expected)

    if op in ("==", "="):
        assert actual_norm == expected, f"断言失败: {path} 期望 == {expected!r}，实际 {actual_norm!r}"
    elif op == "!=":
        assert actual_norm != expected, f"断言失败: {path} 期望 != {expected!r}，实际 {actual_norm!r}"
    elif op in (">", ">=", "<", "<="):
        try:
            a, b = float(actual_norm), float(expected)
        except (TypeError, ValueError):
            raise AssertionError(f"断言失败: {path} 无法数值比较，实际 {actual_norm!r}，期望 {expected!r}")
        ok = {">": a > b, ">=": a >= b, "<": a < b, "<=": a <= b}[op]
        assert ok, f"断言失败: {path} 期望 {op} {expected!r}，实际 {actual_norm!r}"
    elif op == "contains":
        needle = raw_expected.strip()
        if isinstance(actual, str):
            ok = needle in actual
        elif isinstance(actual, (list, tuple)):
            ok = _coerce(needle) in actual
        else:
            ok = False
        assert ok, f"断言失败: {path} 应包含 {needle!r}，实际 {actual!r}"
    elif op == "in":
        allowed = {_coerce(x) for x in raw_expected.split(",") if x.strip()}
        assert actual_norm in allowed, f"断言失败: {path}={actual_norm!r} 不在集合 {allowed} 中"
    else:
        raise AssertionError(
            f"不支持的断言操作符: {op}（支持 == != > >= < <= contains in exists not_exists）"
        )


def _parse_body(resp):
    """解析响应体为 JSON 对象；非法则抛 BusinessCodeError。"""
    try:
        data = resp.json()
    except ValueError as e:
        raise BusinessCodeError(
            f"响应体不是合法 JSON（无法判断业务码 code）: {resp.text[:200]}"
        ) from e
    if not isinstance(data, dict):
        raise BusinessCodeError(f"响应体顶层不是 JSON 对象: {str(data)[:200]}")
    return data


def _check_code(data, expected_code):
    """校验顶层业务码 code == expected_code；否则抛 BusinessCodeError。"""
    code = data.get("code")
    if code is None:
        raise BusinessCodeError("响应体缺少业务码 code 字段")
    if _coerce(code) != _coerce(expected_code):
        raise BusinessCodeError(f"响应体业务码 code 非 {expected_code}，实际 {code!r}")


def assert_response(resp, expected_status, expected_code, assertions):
    """断言 HTTP 状态码、业务码 code，再执行字段级校验。

    expected_code 为预期业务码（正常 200，异常/参数错误通常 500）。
    字段级断言失败抛 FieldAssertionError（= 待确认），
    而非普通 AssertionError，便于上层区分「文档不一致」与「请求失败」。
    """
    # 1. HTTP 状态码
    if resp.status_code != expected_status:
        raise HttpStatusError(
            f"HTTP 状态码不符: 期望 {expected_status}，实际 {resp.status_code}\n"
            f"URL: {resp.request.method} {resp.request.url}\n"
            f"响应: {resp.text[:500]}"
        )

    # 2. 业务码 code（必须是 JSON 对象且 code == expected_code）
    data = _parse_body(resp)
    _check_code(data, expected_code)

    # 3. 字段级断言（失败统一转 FieldAssertionError -> 待确认）
    if not assertions:
        return
    for expr in assertions.split(";"):
        expr = expr.strip()
        if not expr:
            continue
        try:
            _check_one(expr, data)
        except FieldAssertionError:
            raise
        except AssertionError as e:
            raise FieldAssertionError(str(e)) from e
