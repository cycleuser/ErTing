"""Tests for ErTing API functions and ToolResult."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from erting.api import ToolResult, denoise_audio, get_version


class TestToolResult:
    """Test ToolResult dataclass behavior."""

    def test_success_result(self):
        r = ToolResult(success=True, data={"key": "value"})
        assert r.success is True
        assert r.error is None
        assert r.data == {"key": "value"}

    def test_failure_result(self):
        r = ToolResult(success=False, error="something went wrong")
        assert r.success is False
        assert r.error == "something went wrong"
        assert r.data is None

    def test_to_dict(self):
        r = ToolResult(success=True, data=[1, 2, 3], metadata={"version": "0.1.0"})
        d = r.to_dict()
        assert set(d.keys()) == {"success", "data", "error", "metadata"}
        assert d["success"] is True
        assert d["data"] == [1, 2, 3]
        assert d["metadata"] == {"version": "0.1.0"}

    def test_default_metadata_isolation(self):
        r1 = ToolResult(success=True, data="test1")
        r2 = ToolResult(success=True, data="test2")
        r1.metadata["a"] = 1
        assert "a" not in r2.metadata

    def test_metadata_with_defaults(self):
        r = ToolResult(success=True)
        assert r.data is None
        assert r.error is None
        assert r.metadata == {}


class TestDenoiseAudio:
    """Test denoise_audio API function."""

    def test_nonexistent_file_returns_error(self, non_existent_file):
        result = denoise_audio(input_path=str(non_existent_file))
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_version_in_metadata(self, non_existent_file):
        result = denoise_audio(input_path=str(non_existent_file))
        assert "version" in result.metadata


class TestGetVersion:
    """Test get_version function."""

    def test_get_version_returns_version(self):
        result = get_version()
        assert result.success is True
        assert "version" in result.data
        assert result.data["version"] is not None

    def test_version_in_metadata(self):
        result = get_version()
        assert "version" in result.metadata
