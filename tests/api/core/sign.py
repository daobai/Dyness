# -*- coding: utf-8 -*-
"""Dyness OpenAPI 自签名鉴权（HMAC-SHA1）。

签名算法（见 docs/interfaces 下的 Open API Protocol V1.4）：
    Content-MD5    = Base64(MD5(body))
    Date           = GMT 时间，格式 "Mon, 17 Sep 2026 14:00:00 GMT"
    string_to_sign = "POST\\n{Content-MD5}\\napplication/json\\n{Date}\\n{接口路径}"
    sign           = Base64(HMAC-SHA1(appSecret, string_to_sign))
    Authorization  = "API {appId}:{sign}"
"""

import base64
import hashlib
import hmac
from datetime import datetime, timezone

_WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def gmt_date():
    now = datetime.now(timezone.utc)
    return (f"{_WEEKDAYS[now.weekday()]}, {now.day:02d} {_MONTHS[now.month - 1]} "
            f"{now.year} {now.strftime('%H:%M:%S')} GMT")


def content_md5(body_str):
    return base64.b64encode(hashlib.md5(body_str.encode("UTF-8")).digest()).decode("UTF-8")


def sign_request(app_id, app_secret, method, canonical_resource, body_str=""):
    """生成签名请求头。canonical_resource 为接口路径（如 /v2/GetRealTimeDataBySN）。"""
    body_md5 = content_md5(body_str)
    date = gmt_date()
    string_to_sign = f"{method}\n{body_md5}\napplication/json\n{date}\n{canonical_resource}"

    secret_bytes = app_secret.encode("UTF-8")
    sign_bytes = hmac.new(secret_bytes, string_to_sign.encode("UTF-8"), hashlib.sha1).digest()
    sign_b64 = base64.b64encode(sign_bytes).decode("UTF-8")

    return {
        "Content-Type": "application/json",
        "Date": date,
        "Content-MD5": body_md5,
        "Authorization": f"API {app_id}:{sign_b64}",
    }
