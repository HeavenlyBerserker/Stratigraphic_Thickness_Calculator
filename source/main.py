from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from source.app import StratigraphicCalculatorWindow
from source.theme import DARK_STYLESHEET, LIGHT_STYLESHEET, system_prefers_dark_mode


def main() -> int:
    app = QApplication(sys.argv)
    use_dark = system_prefers_dark_mode(app)
    app.setStyleSheet(DARK_STYLESHEET if use_dark else LIGHT_STYLESHEET)
    # Increase default UI size globally for readability.
    app.setFont(QFont("Segoe UI", 12))
    base_dir = Path(__file__).resolve().parent.parent
    icon_path = base_dir / "logo.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    window = StratigraphicCalculatorWindow(initial_dark=use_dark)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
