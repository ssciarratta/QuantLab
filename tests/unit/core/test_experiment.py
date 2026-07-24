"""Tests for ExperimentManifest invariants and immutability."""

from __future__ import annotations

from datetime import datetime
from types import MappingProxyType

import pytest

from quantlab.core.types.experiment import ExperimentManifest


class TestExperimentManifest:
    @pytest.fixture
    def valid_kwargs(self, utc_now):
        return {
            "experiment_id": "exp-001",
            "version": "1.0.0",
            "timestamp": utc_now,
            "checksum": "abc123def456",
            "instruments": ["BTC-USDT", "ETH-USDT"],
            "seed": 42,
            "commit": "abc123",
            "lockfile_hash": "sha256:deadbeef",
        }

    def test_valid_manifest(self, valid_kwargs):
        m = ExperimentManifest.create(**valid_kwargs)
        assert m.experiment_id == "exp-001"
        assert isinstance(m.instruments, tuple)
        assert isinstance(m.resolved_config, MappingProxyType)

    def test_empty_experiment_id_rejected(self, valid_kwargs):
        valid_kwargs["experiment_id"] = ""
        with pytest.raises(ValueError, match="experiment_id"):
            ExperimentManifest.create(**valid_kwargs)

    def test_empty_version_rejected(self, valid_kwargs):
        valid_kwargs["version"] = ""
        with pytest.raises(ValueError, match="version"):
            ExperimentManifest.create(**valid_kwargs)

    def test_naive_timestamp_rejected(self, valid_kwargs):
        valid_kwargs["timestamp"] = datetime(2024, 1, 1)
        with pytest.raises(ValueError, match="timezone"):
            ExperimentManifest.create(**valid_kwargs)

    def test_empty_checksum_rejected(self, valid_kwargs):
        valid_kwargs["checksum"] = ""
        with pytest.raises(ValueError, match="checksum"):
            ExperimentManifest.create(**valid_kwargs)

    def test_empty_instruments_rejected(self, valid_kwargs):
        valid_kwargs["instruments"] = []
        with pytest.raises(ValueError, match="instruments"):
            ExperimentManifest.create(**valid_kwargs)

    def test_empty_instrument_name_rejected(self, valid_kwargs):
        valid_kwargs["instruments"] = ["BTC-USDT", ""]
        with pytest.raises(ValueError, match="instrument"):
            ExperimentManifest.create(**valid_kwargs)

    def test_empty_commit_rejected(self, valid_kwargs):
        valid_kwargs["commit"] = ""
        with pytest.raises(ValueError, match="commit"):
            ExperimentManifest.create(**valid_kwargs)

    def test_empty_lockfile_hash_rejected(self, valid_kwargs):
        valid_kwargs["lockfile_hash"] = ""
        with pytest.raises(ValueError, match="lockfile_hash"):
            ExperimentManifest.create(**valid_kwargs)

    def test_resolved_config_immutable(self, valid_kwargs):
        valid_kwargs["resolved_config"] = {"key": "value"}
        m = ExperimentManifest.create(**valid_kwargs)
        with pytest.raises(TypeError):
            m.resolved_config["new"] = "x"  # type: ignore[index]

    def test_instruments_is_tuple(self, valid_kwargs):
        m = ExperimentManifest.create(**valid_kwargs)
        assert isinstance(m.instruments, tuple)
