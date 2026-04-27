"""ErTing Python API - ToolResult pattern for unified API access."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from erting import __version__

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """Standard return type for all API functions."""

    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
        }


def denoise_audio(
    *,
    input_path: str | Path,
    output_path: Optional[str | Path] = None,
    model_name: Optional[str] = None,
) -> ToolResult:
    """Denoise an audio or video file using AI.

    Args:
        input_path: Path to input audio/video file.
        output_path: Optional output path. If not provided,
                    defaults to input file with "_clean" suffix.
        model_name: Optional ModelScope model name.

    Returns:
        ToolResult with success status and output path.

    Example:
        >>> from erting.api import denoise_audio
        >>> result = denoise_audio(input_path="input.mp3")
        >>> print(result.success)
        True
        >>> print(result.data.get("output_path"))
        input_clean.wav
    """
    from erting.core import DenoiseEngine

    input_str = str(input_path)

    if output_path is not None:
        output_str = str(output_path)
    else:
        output_str = None

    try:
        engine = DenoiseEngine(model_name=model_name)
        try:
            result = engine.denoise(input_str, output_str)
            return ToolResult(
                success=result.success,
                data={
                    "input_path": result.input_path,
                    "output_path": result.output_path,
                },
                error=result.error,
                metadata={
                    "version": __version__,
                    "model": result.metadata.get("model"),
                    "original_format": result.metadata.get("original_format"),
                },
            )
        finally:
            engine.cleanup()

    except Exception as e:
        logger.error("Denoise API error: %s", e)
        return ToolResult(
            success=False,
            error=str(e),
            metadata={"version": __version__},
        )


def get_version() -> ToolResult:
    """Get the ErTing version.

    Returns:
        ToolResult with version information.
    """
    return ToolResult(
        success=True,
        data={"version": __version__},
        metadata={"version": __version__},
    )
