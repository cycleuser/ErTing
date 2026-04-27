"""Tests for ErTing OpenAI function-calling tools."""

import json
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from erting.tools import TOOLS, dispatch


class TestToolsSchema:
    """Test TOOLS schema structure."""

    def test_tools_is_list(self):
        assert isinstance(TOOLS, list)
        assert len(TOOLS) > 0

    def test_tool_structure(self):
        for tool in TOOLS:
            assert tool["type"] == "function"
            func = tool["function"]
            assert "name" in func
            assert "description" in func
            assert "parameters" in func

    def test_tool_has_required_fields(self):
        for tool in TOOLS:
            func = tool["function"]
            params = func["parameters"]
            assert params["type"] == "object"
            assert "properties" in params
            assert "required" in params

    def test_required_fields_in_properties(self):
        for tool in TOOLS:
            func = tool["function"]
            props = func["parameters"]["properties"]
            for req in func["parameters"]["required"]:
                assert req in props

    def test_erting_denoise_audio_exists(self):
        tool_names = [t["function"]["name"] for t in TOOLS]
        assert "erting_denoise_audio" in tool_names


class TestToolsDispatch:
    """Test dispatch function."""

    def test_dispatch_unknown_tool_raises(self):
        with pytest.raises(ValueError, match="Unknown tool"):
            dispatch("unknown_tool", {})

    def test_dispatch_denoise_audio_with_args(self, non_existent_file):
        args = {
            "input_path": str(non_existent_file),
        }
        result = dispatch("erting_denoise_audio", args)
        assert "success" in result
        assert result["success"] is False
        assert "error" in result

    def test_dispatch_accepts_json_string(self, non_existent_file):
        args_json = json.dumps({"input_path": str(non_existent_file)})
        result = dispatch("erting_denoise_audio", args_json)
        assert "success" in result
