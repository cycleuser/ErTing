"""Tests for ErTing CLI integration."""

import subprocess
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCLIFlags:
    """Test CLI unified flags."""

    def _run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "erting"] + list(args),
            capture_output=True,
            text=True,
            timeout=15,
        )

    def test_version_flag(self):
        r = self._run_cli("-V")
        assert r.returncode == 0

    def test_version_long_flag(self):
        r = self._run_cli("--version")
        assert r.returncode == 0

    def test_help_shows_unified_flags(self):
        r = self._run_cli("--help")
        assert r.returncode == 0
        assert "--json" in r.stdout
        assert "--quiet" in r.stdout or "-q" in r.stdout
        assert "--verbose" in r.stdout or "-v" in r.stdout
        assert "--output" in r.stdout or "-o" in r.stdout

    def test_missing_input_shows_help(self):
        r = self._run_cli()
        assert r.returncode == 1

    def test_nonexistent_file_returns_error(self):
        r = self._run_cli("/nonexistent/file.wav")
        assert r.returncode == 1

    def test_json_output_format(self, non_existent_file):
        r = self._run_cli("--json", str(non_existent_file))
        assert r.returncode == 1
        data = json.loads(r.stdout)
        assert "success" in data
        assert data["success"] is False
        assert "error" in data

    def test_quiet_flag_suppresses_output(self, non_existent_file):
        r = self._run_cli("-q", str(non_existent_file))
        assert r.returncode == 1
        assert r.stdout == ""

    def test_verbose_flag(self, non_existent_file):
        r = self._run_cli("-v", str(non_existent_file))
        assert r.returncode == 1
        assert "Processing:" in r.stderr or "Error" in r.stderr


import json
