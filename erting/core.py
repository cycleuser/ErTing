"""ErTing - AI-powered audio/video denoising tool.

Core audio processing engine using ModelScope's speech enhancement models.
"""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class DenoiseResult:
    success: bool
    input_path: str
    output_path: Optional[str] = None
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "input_path": self.input_path,
            "output_path": self.output_path,
            "error": self.error,
            "metadata": self.metadata,
        }


class AudioConverter:
    """Handles audio format conversion to 16kHz WAV format required by the model."""

    SUPPORTED_FORMATS = {
        ".mp3", ".wav", ".mp4", ".avi", ".mov", ".flv", ".m4a",
        ".ogg", ".wma", ".aac", ".flac"
    }

    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "erting"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def is_supported(self, file_path: str | Path) -> bool:
        """Check if file format is supported for conversion."""
        path = Path(file_path)
        return path.suffix.lower() in self.SUPPORTED_FORMATS

    def convert_to_wav(self, input_path: str | Path) -> tuple[str, Path]:
        """Convert audio/video file to 16kHz mono WAV using ffmpeg.

        Args:
            input_path: Path to input file.

        Returns:
            Tuple of (temp_wav_path, original_path).

        Raises:
            ValueError: If file format is not supported.
            RuntimeError: If conversion fails.
        """
        import subprocess

        path = Path(input_path)
        if not path.exists():
            raise ValueError(f"Input file not found: {input_path}")

        if not self.is_supported(path):
            raise ValueError(
                f"Unsupported format: {path.suffix}. "
                f"Supported: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        temp_wav = self.temp_dir / f"{path.stem}_input.wav"

        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", str(path),
                "-ar", "16000",
                "-ac", "1",
                "-sample_fmt", "s16",
                str(temp_wav),
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg error: {result.stderr.strip()}")
            logger.info("Converted %s to 16kHz WAV: %s", path.name, temp_wav)
            return str(temp_wav), path
        except FileNotFoundError:
            raise RuntimeError(
                "ffmpeg not found. Install with: "
                "brew install ffmpeg (macOS) or apt install ffmpeg (Linux)"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Audio conversion timed out (5 min limit)")

    def cleanup(self):
        """Clean up temporary directory."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)


class DenoiseEngine:
    """AI-powered denoising engine using ModelScope."""

    DEFAULT_MODEL = "iic/speech_zipenhancer_ans_multiloss_16k_base"

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or self.DEFAULT_MODEL
        self._pipeline = None
        self.converter = AudioConverter()

    def _load_pipeline(self):
        """Lazy load the ModelScope pipeline."""
        if self._pipeline is None:
            try:
                from modelscope.pipelines import pipeline
                from modelscope.utils.constant import Tasks
            except ImportError as e:
                raise RuntimeError(
                    "ModelScope is required for denoising. "
                    "Install with: pip install modelscope"
                ) from e

            logger.info("Loading ModelScope model: %s", self.model_name)
            self._pipeline = pipeline(
                Tasks.acoustic_noise_suppression,
                model=self.model_name
            )
            logger.info("Model loaded successfully")

    def denoise(
        self,
        input_path: str | Path,
        output_path: Optional[str | Path] = None,
        model_name: Optional[str] = None,
    ) -> DenoiseResult:
        """Denoise an audio or video file.

        Args:
            input_path: Path to input audio/video file.
            output_path: Optional output path. If not provided,
                        defaults to input file with "_clean" suffix.
            model_name: Optional ModelScope model name.

        Returns:
            DenoiseResult with success status and output path.
        """
        input_str = str(input_path)
        path = Path(input_path)

        if not path.exists():
            return DenoiseResult(
                success=False,
                input_path=input_str,
                error=f"Input file not found: {input_str}",
            )

        if model_name:
            self.model_name = model_name
            self._pipeline = None

        try:
            if output_path is None:
                output_path = path.parent / f"{path.stem}_clean.wav"
            else:
                output_path = Path(output_path)

            temp_wav = None
            try:
                logger.info("Converting input to 16kHz WAV...")
                temp_wav, original_path = self.converter.convert_to_wav(input_path)

                logger.info("Running AI denoising...")
                self._load_pipeline()

                self._pipeline(
                    temp_wav,
                    output_path=str(output_path)
                )

                logger.info("Denoising complete: %s", output_path)

                return DenoiseResult(
                    success=True,
                    input_path=input_str,
                    output_path=str(output_path),
                    metadata={
                        "model": self.model_name,
                        "original_format": Path(input_str).suffix,
                    },
                )

            finally:
                if temp_wav and Path(temp_wav).exists():
                    Path(temp_wav).unlink(missing_ok=True)

        except Exception as e:
            logger.error("Denoising failed: %s", e)
            return DenoiseResult(
                success=False,
                input_path=input_str,
                error=str(e),
            )

    def cleanup(self):
        """Clean up resources."""
        self.converter.cleanup()
        self._pipeline = None


def denoise_file(
    input_path: str | Path,
    output_path: Optional[str | Path] = None,
    model_name: Optional[str] = None,
) -> DenoiseResult:
    """Convenience function for denoising a file.

    Args:
        input_path: Path to input audio/video file.
        output_path: Optional output path.
        model_name: Optional ModelScope model name.

    Returns:
        DenoiseResult with success status.
    """
    engine = DenoiseEngine(model_name=model_name)
    try:
        return engine.denoise(input_path, output_path)
    finally:
        engine.cleanup()
