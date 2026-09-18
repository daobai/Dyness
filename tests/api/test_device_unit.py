# -*- coding: utf-8 -*-
"""机型归一化与断言裁剪的离线单元测试（不联网、不依赖 config）。"""

from core.device import (
    filter_assertions,
    filter_body,
    model_matches,
    normalize_device_list,
    normalize_model,
    parse_models,
    split_assertion,
)


def test_normalize_model_aliases():
    assert normalize_model("SolarCube2") == "SolarCube"
    assert normalize_model("SolarCube(2)") == "SolarCube"
    assert normalize_model("SC") == "SolarCube"
    assert normalize_model("AquaVolt-LV") == "AquaVolt_LV"
    assert normalize_model("AV") == "AquaVolt"


def test_normalize_model_hardware():
    assert normalize_model("D3.6LXC-5") == "AquaVolt"
    assert normalize_model("D5.0LXC-8") == "AquaVolt"
    # SolarCube 子型号（LHC 系列）
    assert normalize_model("D800-LHC") == "SolarCube"
    assert normalize_model("D2.0-LHC") == "SolarCube"
    assert normalize_model("D800-LHC-02") == "SolarCube"


def test_normalize_model_unknown_falls_back():
    assert normalize_model("UnknownModel") == "UnknownModel"
    assert normalize_model("") is None
    assert normalize_model(None) is None


def test_normalize_device_list():
    assert normalize_device_list("SN1,SN2,SN1") == ["SN1", "SN2"]
    assert normalize_device_list(["SN1", "SN2"]) == ["SN1", "SN2"]
    assert normalize_device_list("") == []
    assert normalize_device_list(None) == []


def test_parse_models():
    assert parse_models("") is None
    assert parse_models(None) is None
    assert parse_models("AquaVolt,SolarCube") == {"AquaVolt", "SolarCube"}
    assert parse_models("SolarCube2") == {"SolarCube"}  # 归一化


def test_model_matches():
    assert model_matches(None, "SolarCube") is True
    assert model_matches({"SolarCube"}, "SolarCube") is True
    assert model_matches({"SolarCube"}, "AquaVolt") is False
    assert model_matches({"SolarCube"}, None) is False


def test_split_assertion():
    assert split_assertion("[A,B] $.x exists") == ({"A", "B"}, "$.x exists")
    assert split_assertion("$.x exists") == (None, "$.x exists")


def test_filter_assertions():
    a = "$.code == 200;[AquaVolt,SolarCube] $.data.onGridDischargeDod exists"
    assert filter_assertions(a, "AquaVolt") == "$.code == 200; $.data.onGridDischargeDod exists"
    assert filter_assertions(a, "SolarCube") == "$.code == 200; $.data.onGridDischargeDod exists"
    assert filter_assertions(a, "AquaVolt_LV") == "$.code == 200"
    assert filter_assertions(a, None) == "$.code == 200"


def test_filter_body():
    body = {
        "deviceSn": "x",
        "[AquaVolt,SolarCube] onGridDischargeDod": "20",
        "offGridDischargeDod": "20",
        "[SolarCube] batteryOffGridChargeLimit": "70",
    }
    assert filter_body(body, "SolarCube") == {
        "deviceSn": "x", "onGridDischargeDod": "20",
        "offGridDischargeDod": "20", "batteryOffGridChargeLimit": "70",
    }
    assert filter_body(body, "AquaVolt") == {
        "deviceSn": "x", "onGridDischargeDod": "20", "offGridDischargeDod": "20",
    }
    assert filter_body(body, "AquaVolt_LV") == {"deviceSn": "x", "offGridDischargeDod": "20"}
    # 无前缀 body 不变（向后兼容）
    assert filter_body({"deviceSn": "x", "safetyCountry": "43"}, "SolarCube") == {
        "deviceSn": "x", "safetyCountry": "43"}
