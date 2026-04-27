"""ErTing OpenAI Function-Calling Tools."""

from __future__ import annotations

import json
from typing import Any

TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "erting_denoise_audio",
            "description": "Denoise an audio or video file using AI-powered noise suppression. Supports MP3, WAV, MP4, AVI, MOV, M4A, FLAC and other formats. The input file is automatically converted to 16kHz WAV for processing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_path": {
                        "type": "string",
                        "description": "Path to input audio/video file to denoise",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional output file path. If not provided, defaults to input file with '_clean' suffix",
                    },
                    "model_name": {
                        "type": "string",
                        "description": "Optional ModelScope model name. Default: iic/speech_zipenhancer_ans_multiloss_16k_base",
                        "default": "iic/speech_zipenhancer_ans_multiloss_16k_base",
                    },
                },
                "required": ["input_path"],
            },
        },
    },
]


def dispatch(name: str, arguments: dict[str, Any] | str) -> dict:
    """Dispatch tool call to appropriate API function.

    Args:
        name: Tool name (e.g., "erting_denoise_audio").
        arguments: Tool arguments as dict or JSON string.

    Returns:
        Result dict from the API function.

    Raises:
        ValueError: If tool name is unknown.
    """
    if isinstance(arguments, str):
        arguments = json.loads(arguments)

    if name == "erting_denoise_audio":
        from erting.api import denoise_audio

        result = denoise_audio(
            input_path=arguments["input_path"],
            output_path=arguments.get("output_path"),
            model_name=arguments.get("model_name"),
        )
        return result.to_dict()

    raise ValueError(f"Unknown tool: {name}")
