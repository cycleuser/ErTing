"""ErTing GUI - PySide6-based graphical user interface with batch processing."""

from __future__ import annotations

import logging
import sys
import threading
from pathlib import Path

from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from erting import __version__
from erting.api import denoise_audio

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    ".mp3", ".wav", ".mp4", ".avi", ".mov", ".m4a",
    ".flac", ".ogg", ".wma", ".aac",
}

SUPPORTED_FILTER = "Audio/Video Files (*.mp3 *.wav *.mp4 *.avi *.mov *.m4a *.flac *.ogg *.wma *.aac)"


class DenoiseWorker(QThread):
    """Background worker for batch denoising."""

    progress = Signal(int, int, str, bool, str)
    finished = Signal(int, int)

    def __init__(self, files: list[str], output_dir: str | None, model_name: str | None):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.model_name = model_name

    def run(self):
        success_count = 0
        total = len(self.files)

        for idx, input_path in enumerate(self.files):
            output_path = None
            if self.output_dir:
                p = Path(input_path)
                output_path = str(Path(self.output_dir) / f"{p.stem}_clean.wav")

            result = denoise_audio(
                input_path=input_path,
                output_path=output_path,
                model_name=self.model_name,
            )

            if result.success:
                success_count += 1
                self.progress.emit(idx + 1, total, result.data.get("output_path", ""), True, "")
            else:
                self.progress.emit(idx + 1, total, "", False, result.error or "Unknown error")

        self.finished.emit(success_count, total)


class ErTingGUI(QMainWindow):
    """Main GUI application window."""

    def __init__(self):
        super().__init__()
        self.files: list[str] = []
        self.output_dir: str | None = None
        self.model_name: str = "iic/speech_zipenhancer_ans_multiloss_16k_base"
        self.worker: DenoiseWorker | None = None

        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        self.setWindowTitle(f"ErTing - AI Audio Denoising v{__version__}")
        self.resize(800, 600)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title = QLabel("ErTing - AI Audio Denoising")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # File list table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["File", "Status", "Output"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 100)
        layout.addWidget(self.table)

        # Model input
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model_input = QLineEdit(self.model_name)
        self.model_input.setPlaceholderText("iic/speech_zipenhancer_ans_multiloss_16k_base")
        model_layout.addWidget(self.model_input)
        layout.addLayout(model_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_add_files = QPushButton("Add Files")
        self.btn_add_files.clicked.connect(self._add_files)
        btn_layout.addWidget(self.btn_add_files)

        self.btn_add_dir = QPushButton("Add Directory")
        self.btn_add_dir.clicked.connect(self._add_directory)
        btn_layout.addWidget(self.btn_add_dir)

        self.btn_remove = QPushButton("Remove Selected")
        self.btn_remove.clicked.connect(self._remove_selected)
        btn_layout.addWidget(self.btn_remove)

        self.btn_clear = QPushButton("Clear All")
        self.btn_clear.clicked.connect(self._clear_all)
        btn_layout.addWidget(self.btn_clear)

        layout.addLayout(btn_layout)

        # Output dir
        out_layout = QHBoxLayout()
        out_layout.addWidget(QLabel("Output Dir:"))
        self.out_dir_input = QLineEdit()
        self.out_dir_input.setPlaceholderText("Leave empty to save alongside input files")
        out_layout.addWidget(self.out_dir_input)

        self.btn_out_dir = QPushButton("Browse...")
        self.btn_out_dir.clicked.connect(self._browse_output_dir)
        out_layout.addWidget(self.btn_out_dir)
        layout.addLayout(out_layout)

        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(10)

        self.btn_start = QPushButton("Start Denoising")
        self.btn_start.setFont(QFont("Arial", 12, QFont.Bold))
        self.btn_start.clicked.connect(self._start_denoise)
        action_layout.addWidget(self.btn_start)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_denoise)
        action_layout.addWidget(self.btn_stop)

        layout.addLayout(action_layout)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready - Add audio/video files to begin")

    def _apply_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a2e;
            }
            QWidget {
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
                font-size: 13px;
            }
            QLineEdit {
                background-color: #16213e;
                border: 1px solid #4a90d9;
                border-radius: 4px;
                padding: 6px;
                color: #e0e0e0;
            }
            QPushButton {
                background-color: #4a90d9;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
            QTableWidget {
                background-color: #16213e;
                border: 1px solid #4a90d9;
                border-radius: 4px;
                gridline-color: #2a2a4e;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QHeaderView::section {
                background-color: #0f3460;
                color: white;
                padding: 6px;
                border: none;
            }
            QProgressBar {
                border: 1px solid #4a90d9;
                border-radius: 4px;
                text-align: center;
                background-color: #16213e;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4a90d9;
                border-radius: 3px;
            }
            QStatusBar {
                background-color: #0f3460;
                color: #aaa;
            }
        """)

    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Audio/Video Files", "", SUPPORTED_FILTER
        )
        for f in files:
            if f not in self.files:
                self.files.append(f)
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(Path(f).name))
                self.table.setItem(row, 1, QTableWidgetItem("Pending"))
                self.table.setItem(row, 2, QTableWidgetItem(""))
        self.status.showMessage(f"Added {len(files)} file(s)")

    def _add_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if not directory:
            return
        count = 0
        for p in sorted(Path(directory).iterdir()):
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS:
                fp = str(p)
                if fp not in self.files:
                    self.files.append(fp)
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    self.table.setItem(row, 0, QTableWidgetItem(p.name))
                    self.table.setItem(row, 1, QTableWidgetItem("Pending"))
                    self.table.setItem(row, 2, QTableWidgetItem(""))
                    count += 1
        self.status.showMessage(f"Added {count} file(s) from directory")

    def _remove_selected(self):
        rows = sorted(set(i.row() for i in self.table.selectedIndexes()), reverse=True)
        for row in rows:
            self.files.pop(row)
            self.table.removeRow(row)

    def _clear_all(self):
        self.files.clear()
        self.table.setRowCount(0)
        self.progress.setVisible(False)
        self.status.showMessage("Cleared")

    def _browse_output_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.out_dir_input.setText(directory)
            self.output_dir = directory

    def _start_denoise(self):
        if not self.files:
            QMessageBox.warning(self, "Warning", "Please add audio/video files first.")
            return

        self.model_name = self.model_input.text().strip() or None
        self.output_dir = self.out_dir_input.text().strip() or None

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_add_files.setEnabled(False)
        self.btn_add_dir.setEnabled(False)
        self.btn_remove.setEnabled(False)
        self.btn_clear.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.progress.setMaximum(len(self.files))

        self.worker = DenoiseWorker(self.files, self.output_dir, self.model_name)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _stop_denoise(self):
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            self._reset_ui()
            self.status.showMessage("Stopped by user")

    def _on_progress(self, current: int, total: int, output: str, success: bool, error: str):
        self.progress.setValue(current)
        row = current - 1
        if row < self.table.rowCount():
            if success:
                self.table.item(row, 1).setText("Success")
                self.table.item(row, 1).setForeground(Qt.green)
                self.table.item(row, 2).setText(output)
            else:
                self.table.item(row, 1).setText("Failed")
                self.table.item(row, 1).setForeground(Qt.red)
                self.table.item(row, 2).setText(error)
        self.status.showMessage(f"Processing {current}/{total}")

    def _on_finished(self, success_count: int, total: int):
        self._reset_ui()
        self.status.showMessage(f"Done! {success_count}/{total} succeeded")
        QMessageBox.information(
            self,
            "Complete",
            f"Denoising complete!\n\n{success_count}/{total} files succeeded.",
        )

    def _reset_ui(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_add_files.setEnabled(True)
        self.btn_add_dir.setEnabled(True)
        self.btn_remove.setEnabled(True)
        self.btn_clear.setEnabled(True)


def main():
    """Launch the GUI application."""
    logging.basicConfig(level=logging.INFO)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = ErTingGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
