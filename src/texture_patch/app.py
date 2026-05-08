"""Entry point: python -m texture_patch.app"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from texture_patch.views.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Texture Patch Prototype")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
