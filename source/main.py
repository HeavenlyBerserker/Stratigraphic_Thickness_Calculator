from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from source.app import StratigraphicCalculatorWindow


def main() -> int:
    app = QApplication(sys.argv)
    base_dir = Path(__file__).resolve().parent.parent
    icon_path = base_dir / "logo.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    window = StratigraphicCalculatorWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
