"""Tests for ErTing core module."""

import subprocess
from unittest.mock import patch

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from erting.core import (
    AudioConverter,
    DenoiseEngine,
    DenoiseResult,
    denoise_file,
)


class TestDenoiseResult:
    """Test DenoiseResult dataclass."""

    def test_success_result(self):
        r = DenoiseResult(
            success=True,
            input_path="/input.wav",
            output_path="/output.wav",
        )
        assert r.success is True
        assert r.input_path == "/input.wav"
        assert r.output_path == "/output.wav"
        assert r.error is None

    def test_failure_result(self):
        r = DenoiseResult(
            success=False,
            input_path="/input.wav",
            error="File not found",
        )
        assert r.success is False
        assert r.error == "File not found"

    def test_to_dict(self):
        r = DenoiseResult(
            success=True,
            input_path="/input.wav",
            output_path="/output.wav",
            metadata={"model": "test-model"},
        )
        d = r.to_dict()
        assert d["success"] is True
        assert d["input_path"] == "/input.wav"
        assert d["output_path"] == "/output.wav"
        assert d["metadata"]["model"] == "test-model"


class TestAudioConverter:
    """Test AudioConverter class."""

    def test_is_supported_wav(self):
        conv = AudioConverter()
        assert conv.is_supported("test.wav") is True
        assert conv.is_supported("test.mp3") is True
        assert conv.is_supported("test.mp4") is True
        assert conv.is_supported("test.txt") is False

    def test_nonexistent_file_raises(self):
        conv = AudioConverter()
        with pytest.raises(ValueError, match="not found"):
            conv.convert_to_wav("/nonexistent/file.wav")

    def test_cleanup(self):
        conv = AudioConverter()
        conv.cleanup()

    def test_convert_with_ffmpeg(self, tmp_path):
        """Test conversion using mocked ffmpeg."""
        conv = AudioConverter()
        input_file = tmp_path / "test.mp3"
        input_file.touch()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )
            temp_wav, original = conv.convert_to_wav(input_file)
            assert Path(temp_wav).exists() is False
            assert mock_run.call_count == 1
            call_args = mock_run.call_args[0][0]
            assert "ffmpeg" in call_args
            assert "16000" in call_args

    def test_ffmpeg_not_found_raises(self, tmp_path):
        """Test error when ffmpeg is not installed."""
        conv = AudioConverter()
        input_file = tmp_path / "test.mp3"
        input_file.touch()

        with patch("subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(RuntimeError, match="ffmpeg not found"):
                conv.convert_to_wav(input_file)

    def test_ffmpeg_error_raises(self, tmp_path):
        """Test error when ffmpeg fails."""
        conv = AudioConverter()
        input_file = tmp_path / "test.mp3"
        input_file.touch()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr="invalid data"
            )
            with pytest.raises(RuntimeError, match="ffmpeg error"):
                conv.convert_to_wav(input_file)


class TestDenoiseEngine:
    """Test DenoiseEngine class."""

    def test_nonexistent_file_returns_error(self):
        engine = DenoiseEngine()
        result = engine.denoise("/nonexistent/file.wav")
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_cleanup(self):
        engine = DenoiseEngine()
        engine.cleanup()


class TestDenoiseFile:
    """Test denoise_file convenience function."""

    def test_nonexistent_file(self):
        result = denoise_file("/nonexistent/file.wav")
        assert result.success is False
