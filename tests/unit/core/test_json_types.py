"""Tests for JSON immutable types."""

from __future__ import annotations

from types import MappingProxyType

import pytest

from quantlab.core.types.json_types import freeze_json


class TestFreezeJson:
    def test_freeze_none(self):
        assert freeze_json(None) is None

    def test_freeze_str(self):
        assert freeze_json("hello") == "hello"

    def test_freeze_int(self):
        assert freeze_json(42) == 42

    def test_freeze_float(self):
        assert freeze_json(3.14) == 3.14

    def test_freeze_bool(self):
        assert freeze_json(True) is True

    def test_freeze_list_to_tuple(self):
        result = freeze_json([1, 2, 3])
        assert result == (1, 2, 3)
        assert isinstance(result, tuple)

    def test_freeze_dict_to_mapping_proxy(self):
        result = freeze_json({"key": "value"})
        assert isinstance(result, MappingProxyType)
        assert result["key"] == "value"

    def test_freeze_nested(self):
        data = {"a": [1, {"b": [2, 3]}], "c": None}
        result = freeze_json(data)
        assert isinstance(result, MappingProxyType)
        assert isinstance(result["a"], tuple)
        inner = result["a"][1]
        assert isinstance(inner, MappingProxyType)
        assert isinstance(inner["b"], tuple)

    def test_freeze_dict_is_immutable(self):
        result = freeze_json({"key": "value"})
        with pytest.raises(TypeError):
            result["key"] = "new"  # type: ignore[index]

    def test_freeze_list_result_is_immutable(self):
        result = freeze_json([1, 2, 3])
        assert isinstance(result, tuple)
        with pytest.raises(TypeError):
            result[0] = 99  # type: ignore[index]

    def test_freeze_rejects_non_json_types(self):
        with pytest.raises(TypeError, match="Cannot freeze"):
            freeze_json(set())

    def test_freeze_rejects_custom_objects(self):
        class Custom:
            pass

        with pytest.raises(TypeError, match="Cannot freeze"):
            freeze_json(Custom())

    def test_determinism(self):
        data = {"x": [1, 2], "y": "z"}
        r1 = freeze_json(data)
        r2 = freeze_json(data)
        assert r1 == r2
