"""Shared pytest fixtures and test configuration."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_wav_file(tmp_path):
    """Create a minimal valid WAV file for testing."""
    import wave
    import struct

    wav_path = tmp_path / "test_input.wav"

    with wave.open(str(wav_path), 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(struct.pack('<' + 'h' * 100, *([0] * 100)))

    return wav_path


@pytest.fixture
def non_existent_file(tmp_path):
    """Return path to non-existent file."""
    return tmp_path / "non_existent.wav"


class MockPipeline:
    """Mock ModelScope pipeline for testing."""

    def __call__(self, input_path, output_path=None):
        Path(output_path).touch()


class MockCompletedProcess:
    """Mock subprocess.CompletedProcess."""

    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
