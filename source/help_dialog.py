"""Help & Documentation dialog for the desktop app."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QTextBrowser,
    QVBoxLayout,
)

from source.app_info import HelpTopic, help_documentation_html


class HelpDocumentationDialog(QDialog):
    """Modal dialog showing usage instructions, implementer info, and references."""

    def __init__(self, parent=None, *, topic: HelpTopic = "calculator") -> None:
        super().__init__(parent)
        self.setWindowTitle("Help & Documentation")
        self.resize(640, 520)

        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(True)
        self._browser.setHtml(help_documentation_html(topic))
        self._browser.setReadOnly(True)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        close_btn = buttons.button(QDialogButtonBox.StandardButton.Close)
        if close_btn is not None:
            close_btn.setText("Close")

        layout = QVBoxLayout(self)
        layout.addWidget(self._browser)
        layout.addWidget(buttons)


def show_help_documentation(
    parent=None,
    *,
    topic: HelpTopic = "calculator",
) -> None:
    """Open the Help & Documentation dialog."""
    dialog = HelpDocumentationDialog(parent, topic=topic)
    dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
    dialog.exec()
