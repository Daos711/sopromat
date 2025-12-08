#!/usr/bin/env python3
"""
Sopromat GUI - Построение эпюр для задач по сопротивлению материалов
Задача 2: Балка на опорах - эпюры Q(x) и M(x)
Задача 3: Ступенчатый стержень - эпюры N(x), σ(x), Δl(x)
"""

import sys
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
