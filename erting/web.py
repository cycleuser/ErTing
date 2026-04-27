"""ErTing Web - Flask web interface for audio/video denoising."""

from __future__ import annotations

import logging
import os
import tempfile
import time
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
from flask_cors import CORS

from erting import __version__
from erting.api import denoise_audio

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024
CORS(app)

app.config["UPLOAD_FOLDER"] = tempfile.mkdtemp(prefix="erting_upload_")
app.config["OUTPUT_FOLDER"] = tempfile.mkdtemp(prefix="erting_output_")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)


@app.route("/")
def index():
    """Render main page."""
    return render_template("index.html", version=__version__)


@app.route("/api/denoise", methods=["POST"])
def api_denoise():
    """Handle file upload and denoising request."""
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"}), 400

    model_name = request.form.get("model_name")

    input_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(input_path)

    try:
        stem = Path(file.filename).stem
        output_filename = f"{stem}_clean.wav"
        output_path = os.path.join(app.config["OUTPUT_FOLDER"], output_filename)

        result = denoise_audio(
            input_path=input_path,
            output_path=output_path,
            model_name=model_name,
        )

        if result.success:
            return jsonify({
                "success": True,
                "download_url": f"/api/download/{output_filename}",
                "filename": output_filename,
                "metadata": result.metadata,
            })
        else:
            return jsonify({
                "success": False,
                "error": result.error,
            }), 500

    except Exception as e:
        logger.error("Denoising error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500

    finally:
        if Path(input_path).exists():
            Path(input_path).unlink(missing_ok=True)


@app.route("/api/download/<filename>")
def api_download(filename):
    """Download processed audio file."""
    safe_name = Path(filename).name
    file_path = os.path.join(app.config["OUTPUT_FOLDER"], safe_name)

    if not Path(file_path).exists():
        return jsonify({"success": False, "error": "File not found"}), 404

    return send_file(
        file_path,
        as_attachment=True,
        download_name=safe_name,
        mimetype="audio/wav",
    )


@app.route("/api/status")
def api_status():
    """Check service status."""
    return jsonify({
        "status": "ok",
        "version": __version__,
    })


def cleanup_old_files(max_age_hours: int = 24):
    """Remove processed files older than max_age_hours."""
    cutoff = time.time() - (max_age_hours * 3600)
    for folder in [app.config["UPLOAD_FOLDER"], app.config["OUTPUT_FOLDER"]]:
        for f in Path(folder).iterdir():
            if f.is_file() and f.stat().st_mtime < cutoff:
                f.unlink(missing_ok=True)
                logger.info("Cleaned up old file: %s", f.name)


def main(host: str = "0.0.0.0", port: int = 5001, debug: bool = False):
    """Run the Flask web server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logger.info("Starting ErTing Web on %s:%d", host, port)
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
