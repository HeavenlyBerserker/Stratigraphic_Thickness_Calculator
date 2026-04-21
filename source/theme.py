"""Qt stylesheets for light and dark application themes."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication

LIGHT_STYLESHEET = """
    QWidget {
        background-color: #ffffff;
        color: #000000;
    }
    QTabWidget::pane {
        border: 1px solid #cccccc;
        top: -1px;
        background: #ffffff;
    }
    QTabBar::tab {
        background: #f5f5f5;
        color: #000000;
        padding: 6px 14px;
        border: 1px solid #cccccc;
        border-bottom: none;
        border-top-left-radius: 3px;
        border-top-right-radius: 3px;
    }
    QTabBar::tab:selected {
        background: #ffffff;
        color: #000000;
        margin-bottom: -1px;
    }
    QGroupBox {
        color: #000000;
        background-color: #ffffff;
        border: 1px solid #cccccc;
        margin-top: 8px;
        padding-top: 8px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 8px;
        padding: 0 4px;
        color: #000000;
    }
    QLabel {
        background-color: transparent;
        color: #000000;
    }
    QTextEdit, QPlainTextEdit {
        background-color: #ffffff;
        color: #000000;
        border: 1px solid #cccccc;
    }
    QLineEdit, QSpinBox, QDoubleSpinBox {
        background-color: #ffffff;
        color: #000000;
    }
    QPushButton {
        background-color: #f0f0f0;
        color: #000000;
        border: 1px solid #afafaf;
        padding: 4px 14px;
        min-height: 20px;
    }
    QPushButton:hover {
        background-color: #e0e0e0;
    }
    QPushButton:pressed {
        background-color: #d0d0d0;
    }
    QToolButton#themeToggle {
        background-color: transparent;
        border: 1px solid #cccccc;
        border-radius: 4px;
        color: #000000;
        padding: 2px 6px;
    }
    QToolButton#themeToggle:hover {
        background-color: #eeeeee;
    }
    QStatusBar {
        background-color: #f5f5f5;
        color: #000000;
    }
    QMessageBox {
        background-color: #ffffff;
    }
    QMessageBox QLabel {
        color: #000000;
    }
"""

DARK_STYLESHEET = """
    QWidget {
        background-color: #2b2b2b;
        color: #e8e8e8;
    }
    QTabWidget::pane {
        border: 1px solid #555555;
        top: -1px;
        background: #2b2b2b;
    }
    QTabBar::tab {
        background: #3d3d3d;
        color: #e8e8e8;
        padding: 6px 14px;
        border: 1px solid #555555;
        border-bottom: none;
        border-top-left-radius: 3px;
        border-top-right-radius: 3px;
    }
    QTabBar::tab:selected {
        background: #2b2b2b;
        color: #ffffff;
        margin-bottom: -1px;
    }
    QGroupBox {
        color: #e8e8e8;
        background-color: #2b2b2b;
        border: 1px solid #555555;
        margin-top: 8px;
        padding-top: 8px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 8px;
        padding: 0 4px;
        color: #e8e8e8;
    }
    QLabel {
        background-color: transparent;
        color: #e8e8e8;
    }
    QTextEdit, QPlainTextEdit {
        background-color: #1e1e1e;
        color: #e8e8e8;
        border: 1px solid #555555;
    }
    QLineEdit, QSpinBox, QDoubleSpinBox {
        background-color: #1e1e1e;
        color: #e8e8e8;
    }
    QPushButton {
        background-color: #444444;
        color: #e8e8e8;
        border: 1px solid #666666;
        padding: 4px 14px;
        min-height: 20px;
    }
    QPushButton:hover {
        background-color: #555555;
    }
    QPushButton:pressed {
        background-color: #333333;
    }
    QToolButton#themeToggle {
        background-color: transparent;
        border: 1px solid #555555;
        border-radius: 4px;
        color: #e8e8e8;
        padding: 2px 6px;
    }
    QToolButton#themeToggle:hover {
        background-color: #3d3d3d;
    }
    QStatusBar {
        background-color: #252525;
        color: #e8e8e8;
    }
    QMessageBox {
        background-color: #2b2b2b;
    }
    QMessageBox QLabel {
        color: #e8e8e8;
    }
"""


def system_prefers_dark_mode(app: QApplication) -> bool:
    """
    True if the OS / Qt reports a dark color scheme, for matching startup theme.
    Falls back to window background lightness when the scheme is unknown.
    """
    hints = app.styleHints()
    try:
        scheme = hints.colorScheme()
        cs = Qt.ColorScheme
        if scheme == cs.Dark:
            return True
        if scheme == cs.Light:
            return False
    except AttributeError:
        pass
    bg = app.palette().color(QPalette.ColorRole.Window)
    return bg.lightness() < 128
