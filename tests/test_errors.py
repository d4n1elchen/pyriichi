"""Tests for translated pyriichi errors."""

from pyriichi import RuleError, TileError


def test_error_defaults_to_traditional_chinese_value_error():
    error = RuleError("tile_set_not_initialized")

    assert isinstance(error, ValueError)
    assert str(error) == "牌山未初始化"
    assert error.zh == "牌山未初始化"


def test_error_exposes_other_languages():
    error = TileError("ura_dora_indicators_insufficient", {"count": 2, "actual": 1})

    assert error.zh == "裏寶牌指示牌不足，需要 2 張，只有 1 張"
    assert error.en == "Not enough ura dora indicators: need 2, only 1 available"
    assert error.ja == "裏ドラ表示牌が不足しています。必要: 2、現在: 1"
