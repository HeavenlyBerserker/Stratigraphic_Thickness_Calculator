"""Desktop Batch Processing tab."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from source.batch import (
    parse_batch_workbook,
    process_batch_rows,
    write_batch_example,
    write_batch_results,
    write_batch_template,
)
from source.help_dialog import show_help_documentation


class _BatchWorker(QThread):
    progress = Signal(int, int, str)
    finished_ok = Signal(list, str, str)
    failed = Signal(str)

    def __init__(
        self,
        input_path: Path,
        output_path: Path,
        plots_dir: Path,
        plot_format: str,
    ) -> None:
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.plots_dir = plots_dir
        self.plot_format = plot_format

    def run(self) -> None:
        try:
            rows = parse_batch_workbook(self.input_path)

            def _progress(current: int, total: int, message: str) -> None:
                self.progress.emit(current, total, message)

            results = process_batch_rows(rows, progress_cb=_progress)
            saved_plots = write_batch_results(
                self.output_path,
                results,
                plots_dir=self.plots_dir,
                plot_format=self.plot_format,
            )
            plots_note = ""
            if saved_plots is not None:
                plots_note = f"\nMonte Carlo plots: {saved_plots}"
            self.finished_ok.emit(results, str(self.output_path), plots_note)
        except Exception as exc:
            self.failed.emit(str(exc))


class BatchTab(QWidget):
    _LOG_COLORS = {
        "normal": {"light": "#000000", "dark": "#e8e8e8"},
        "success": {"light": "#15803d", "dark": "#4ade80"},
        "warning": {"light": "#a16207", "dark": "#facc15"},
        "error": {"light": "#b91c1c", "dark": "#f87171"},
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._input_path: Path | None = None
        self._output_path: Path | None = None
        self._worker: _BatchWorker | None = None
        self._dark_mode = False
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        self._title_label = QLabel("Batch Processing")
        self._title_label.setStyleSheet("font-size: 16px; font-weight: 600;")
        root.addWidget(self._title_label)

        intro = QLabel(
            "Load an Excel workbook with one well per row (see template). "
            "Each row selects a model with column T (1–8) and runs deterministic "
            "and optional Monte Carlo calculations."
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        top_row = QHBoxLayout()
        self._template_btn = QPushButton("Download Template (.xlsx)")
        self._example_btn = QPushButton("Download Example (.xlsx)")
        self._help_btn = QPushButton("Help && Documentation")
        self._template_btn.clicked.connect(self._download_template)
        self._example_btn.clicked.connect(self._download_example)
        self._help_btn.clicked.connect(
            lambda: show_help_documentation(self.window(), topic="batch_desktop")
        )
        top_row.addWidget(self._template_btn)
        top_row.addWidget(self._example_btn)
        top_row.addWidget(self._help_btn)
        top_row.addStretch()
        root.addLayout(top_row)

        format_row = QHBoxLayout()
        format_row.addWidget(QLabel("Monte Carlo plot format:"))
        self._plot_format = QComboBox()
        self._plot_format.addItem("PNG", "png")
        self._plot_format.addItem("SVG", "svg")
        self._plot_format.setCurrentIndex(0)
        format_row.addWidget(self._plot_format)
        format_row.addStretch()
        root.addLayout(format_row)

        choose_row = QHBoxLayout()
        self._choose_btn = QPushButton("Choose File to Batch Process")
        self._choose_btn.clicked.connect(self._choose_input_file)
        self._file_label = QLabel("No batch file selected.")
        self._file_label.setWordWrap(True)
        choose_row.addWidget(self._choose_btn)
        choose_row.addWidget(self._file_label, stretch=1)
        root.addLayout(choose_row)

        run_row = QHBoxLayout()
        self._run_btn = QPushButton("Batch Process")
        self._run_btn.clicked.connect(self._run_batch)
        self._output_label = QLabel("No output file selected.")
        self._output_label.setWordWrap(True)
        run_row.addWidget(self._run_btn)
        run_row.addWidget(self._output_label, stretch=1)
        root.addLayout(run_row)

        logs_group = QGroupBox("Batch log")
        logs_layout = QVBoxLayout(logs_group)
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setPlaceholderText("Batch status messages appear here.")
        logs_layout.addWidget(self._log)
        root.addWidget(logs_group, stretch=1)

        status_bar = QHBoxLayout()
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(True)
        self._status_icon = QLabel("")
        self._status_icon.setFixedWidth(36)
        self._status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_bar.addWidget(self._progress, stretch=1)
        status_bar.addWidget(self._status_icon)
        root.addLayout(status_bar)

    def apply_theme(self, dark: bool) -> None:
        self._dark_mode = dark
        title_color = "#e8e8e8" if dark else "#000000"
        self._title_label.setStyleSheet(
            f"font-size: 16px; font-weight: 600; color: {title_color};"
        )
        self._status_icon.setStyleSheet("font-size: 20px;")

    def _log_color(self, kind: str) -> QColor:
        palette = self._LOG_COLORS.get(kind, self._LOG_COLORS["normal"])
        key = "dark" if self._dark_mode else "light"
        return QColor(palette[key])

    def _append_log(self, text: str, *, kind: str = "normal") -> None:
        if not text:
            return
        cursor = self._log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        fmt = QTextCharFormat()
        fmt.setForeground(self._log_color(kind))
        cursor.insertText(text, fmt)
        if not text.endswith("\n"):
            cursor.insertText("\n", fmt)
        self._log.setTextCursor(cursor)
        self._log.ensureCursorVisible()

    def _set_status_icon(self, icon: str) -> None:
        self._status_icon.setText(icon)

    def _download_template(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Batch Template",
            str(Path.cwd() / "batch_template.xlsx"),
            "Excel Workbook (*.xlsx)",
        )
        if not path:
            return
        if not path.lower().endswith(".xlsx"):
            path += ".xlsx"
        try:
            write_batch_template(Path(path))
            self._append_log(f"Saved template to {path}")
        except OSError as exc:
            QMessageBox.warning(self, "Save Batch Template", str(exc))

    def _download_example(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Batch Example",
            str(Path.cwd() / "batch_example.xlsx"),
            "Excel Workbook (*.xlsx)",
        )
        if not path:
            return
        if not path.lower().endswith(".xlsx"):
            path += ".xlsx"
        try:
            write_batch_example(Path(path))
            self._append_log(f"Saved example workbook to {path}")
        except OSError as exc:
            QMessageBox.warning(self, "Save Batch Example", str(exc))

    def _choose_input_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Batch Input Workbook",
            str(Path.cwd()),
            "Excel Workbook (*.xlsx)",
        )
        if not path:
            return
        self._input_path = Path(path)
        self._file_label.setText(self._input_path.name)
        self._append_log(f"Selected batch file: {self._input_path}")

    def _choose_output_file(self) -> Path | None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Batch Results",
            str(self._output_path or (Path.cwd() / "batch_results.xlsx")),
            "Excel Workbook (*.xlsx)",
        )
        if not path:
            return None
        if not path.lower().endswith(".xlsx"):
            path += ".xlsx"
        self._output_path = Path(path)
        self._output_label.setText(self._output_path.name)
        return self._output_path

    def _set_running(self, running: bool) -> None:
        self._template_btn.setEnabled(not running)
        self._example_btn.setEnabled(not running)
        self._choose_btn.setEnabled(not running)
        self._run_btn.setEnabled(not running)
        self._plot_format.setEnabled(not running)
        if running:
            self._set_status_icon("")

    def _run_batch(self) -> None:
        if self._input_path is None:
            self._append_log("Choose a batch input workbook first.", kind="error")
            self._set_status_icon("❌")
            return
        out = self._choose_output_file()
        if out is None:
            return
        plots_dir = out.with_suffix("").parent / f"{out.stem}_mc_plots"
        plot_format = str(self._plot_format.currentData() or "png")

        self._set_running(True)
        self._progress.setValue(0)
        self._append_log(f"Starting batch: {self._input_path.name}")
        self._append_log(f"Output: {out}")
        self._append_log(f"Monte Carlo plot format: {plot_format.upper()}")

        self._worker = _BatchWorker(self._input_path, out, plots_dir, plot_format)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_ok.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_progress(self, current: int, total: int, message: str) -> None:
        pct = int(round(100.0 * current / max(total, 1)))
        self._progress.setValue(pct)
        self._append_log(message)

    def _on_finished(self, results, output_path: str, plots_note: str) -> None:
        self._set_running(False)
        self._progress.setValue(100)
        errors = [r for r in results if r.status != "OK"]
        warned = [r for r in results if r.status == "OK" and r.warnings]

        for result in errors:
            self._append_log(
                f"{result.well_id}: {result.error}",
                kind="error",
            )

        for result in warned:
            for warning in result.warnings:
                self._append_log(f"{result.well_id}: {warning}", kind="warning")

        ok_count = len(results) - len(errors)
        if errors:
            self._append_log(
                f"Batch finished with {len(errors)} error(s), {ok_count} OK. "
                f"Results: {output_path}{plots_note}",
                kind="error",
            )
            self._set_status_icon("❌")
        elif warned:
            self._append_log(
                f"Success with {len(warned)} warning(s). "
                f"Processed {len(results)} row(s). Results: {output_path}{plots_note}",
                kind="warning",
            )
            self._set_status_icon("⚠️")
        else:
            self._append_log(
                f"Success. Processed {len(results)} row(s). "
                f"Results: {output_path}{plots_note}",
                kind="success",
            )
            self._set_status_icon("✅")
        self._worker = None

    def _on_failed(self, message: str) -> None:
        self._set_running(False)
        self._progress.setValue(0)
        self._append_log(f"Batch failed: {message}", kind="error")
        self._set_status_icon("❌")
        self._worker = None
