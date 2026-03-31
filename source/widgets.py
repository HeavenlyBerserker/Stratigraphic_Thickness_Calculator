from __future__ import annotations

import io
import traceback
from contextlib import redirect_stderr, redirect_stdout
from typing import Callable

from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ModelTab(QWidget):
    """
    Generic tab layout:
    - input section
    - output section
    - combined stdout/stderr section at the bottom
    """

    def __init__(self, title: str, on_calculate: Callable[["ModelTab"], None]) -> None:
        super().__init__()
        self.on_calculate = on_calculate
        self.inputs: dict[str, QDoubleSpinBox] = {}
        self._build_ui(title)

    def _build_ui(self, title: str) -> None:
        root_layout = QVBoxLayout()
        self.setLayout(root_layout)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: 600;")
        root_layout.addWidget(title_label)

        content_layout = QHBoxLayout()
        root_layout.addLayout(content_layout, stretch=1)

        self.input_group = QGroupBox("Input")
        self.input_form = QFormLayout()
        self.input_group.setLayout(self.input_form)
        content_layout.addWidget(self.input_group, stretch=1)

        self.output_group = QGroupBox("Output")
        output_layout = QVBoxLayout()
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        output_layout.addWidget(self.output_text)
        self.output_group.setLayout(output_layout)
        content_layout.addWidget(self.output_group, stretch=1)

        button_row = QHBoxLayout()
        self.calculate_button = QPushButton("Calculate")
        self.calculate_button.clicked.connect(self._run_calculation)
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self._clear_all)
        button_row.addWidget(self.calculate_button)
        button_row.addWidget(self.clear_button)
        button_row.addStretch()
        root_layout.addLayout(button_row)

        logs_group = QGroupBox("Stdout / Stderr")
        logs_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText(
            "Combined logs. stderr entries are shown in red."
        )
        logs_layout.addWidget(self.log_text)
        logs_group.setLayout(logs_layout)
        root_layout.addWidget(logs_group)

    def add_float_input(
        self,
        key: str,
        label: str,
        decimals: int = 4,
        minimum: float = -100000.0,
        maximum: float = 100000.0,
        step: float = 0.1,
        default: float = 0.0,
    ) -> None:
        spin_box = QDoubleSpinBox()
        spin_box.setDecimals(decimals)
        spin_box.setRange(minimum, maximum)
        spin_box.setSingleStep(step)
        spin_box.setValue(default)
        self.inputs[key] = spin_box
        self.input_form.addRow(label, spin_box)

    def value(self, key: str) -> float:
        return self.inputs[key].value()

    def set_output(self, text: str, is_html: bool = False) -> None:
        if is_html:
            self.output_text.setHtml(text)
            return
        self.output_text.setPlainText(text)

    def _clear_all(self) -> None:
        self.output_text.clear()
        self.log_text.clear()

    def _append_log(self, text: str, is_error: bool) -> None:
        if not text:
            return
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        text_format = QTextCharFormat()
        text_format.setForeground(
            QColor("red") if is_error else QColor(255, 255, 255)
        )
        cursor.insertText(text, text_format)
        if not text.endswith("\n"):
            cursor.insertText("\n", text_format)
        self.log_text.setTextCursor(cursor)
        self.log_text.ensureCursorVisible()

    def _set_combined_logs(self, stdout_text: str, stderr_text: str) -> None:
        self.log_text.clear()
        stdout_lines = stdout_text.splitlines(keepends=True)
        stderr_lines = stderr_text.splitlines(keepends=True)
        max_len = max(len(stdout_lines), len(stderr_lines))
        for index in range(max_len):
            if index < len(stdout_lines):
                self._append_log(stdout_lines[index], is_error=False)
            if index < len(stderr_lines):
                self._append_log(stderr_lines[index], is_error=True)

    def _run_calculation(self) -> None:
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        self.log_text.clear()
        try:
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                self.on_calculate(self)
        except Exception as exc:  # pragma: no cover
            traceback.print_exc(file=stderr_buffer)
            self.set_output(f"Calculation failed: {exc}")
        finally:
            self._set_combined_logs(
                stdout_buffer.getvalue(),
                stderr_buffer.getvalue(),
            )
