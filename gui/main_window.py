"""
Главное окно приложения Sopromat GUI
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSpinBox, QComboBox, QPushButton, QGroupBox,
    QScrollArea, QSizePolicy, QMessageBox, QFrame, QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from .plot_canvas import PlotCanvas
from solvers import Task2Solver, Task3Solver


class MainWindow(QMainWindow):
    """Главное окно приложения"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Сопромат - Построение эпюр")
        self.setMinimumSize(1100, 800)  # Увеличенное окно чтобы всё влезало

        self._setup_ui()

    def _setup_ui(self):
        """Настройка интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        # Левая панель - управление
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)

        # Правая панель - графики
        plot_panel = self._create_plot_panel()
        main_layout.addWidget(plot_panel, stretch=1)

    def _create_control_panel(self) -> QWidget:
        """Создание панели управления"""
        panel = QWidget()
        panel.setMaximumWidth(320)
        panel.setMinimumWidth(280)
        layout = QVBoxLayout(panel)

        # Заголовок
        title = QLabel("Параметры")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Группа ввода варианта
        input_group = QGroupBox("Ввод данных")
        input_layout = QVBoxLayout(input_group)

        # Номер варианта
        variant_layout = QHBoxLayout()
        variant_label = QLabel("Вариант N:")
        variant_label.setFont(QFont("Arial", 11))
        self.variant_spinbox = QSpinBox()
        self.variant_spinbox.setRange(1, 35)
        self.variant_spinbox.setValue(1)
        self.variant_spinbox.setFont(QFont("Arial", 11))
        variant_layout.addWidget(variant_label)
        variant_layout.addWidget(self.variant_spinbox)
        input_layout.addLayout(variant_layout)

        # Выбор задачи
        task_layout = QHBoxLayout()
        task_label = QLabel("Задача:")
        task_label.setFont(QFont("Arial", 11))
        self.task_combo = QComboBox()
        self.task_combo.addItems([
            "Задача 2 - Балка (Q, M)",
            "Задача 3 - Стержень (N, σ, Δl)"
        ])
        self.task_combo.setFont(QFont("Arial", 10))
        task_layout.addWidget(task_label)
        task_layout.addWidget(self.task_combo)
        input_layout.addLayout(task_layout)

        layout.addWidget(input_group)

        # Кнопка построения
        self.build_button = QPushButton("Построить эпюры")
        self.build_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.build_button.setMinimumHeight(50)
        self.build_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.build_button.clicked.connect(self._on_build_clicked)
        layout.addWidget(self.build_button)

        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # Группа результатов
        results_group = QGroupBox("Исходные данные и результаты")
        results_layout = QVBoxLayout(results_group)

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Courier New", 10))
        self.results_text.setMinimumHeight(400)  # Увеличено для меньшего скроллинга
        self.results_text.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)
        results_layout.addWidget(self.results_text)

        layout.addWidget(results_group, stretch=1)  # stretch=1 чтобы занимало доступное место

        layout.addStretch()  # Пустое место перед справкой

        # Описание задач - внизу панели
        info_group = QGroupBox("Справка")
        info_layout = QVBoxLayout(info_group)
        info_text = QLabel(
            "<b>Задача 2:</b> Балка на двух опорах<br>"
            "с распределённой нагрузкой q<br>"
            "и сосредоточенной силой F.<br><br>"
            "<b>Задача 3:</b> Ступенчатый стержень<br>"
            "с осевыми силами F₁, F₂, F₃."
        )
        info_text.setWordWrap(True)
        info_text.setFont(QFont("Arial", 9))
        info_layout.addWidget(info_text)
        layout.addWidget(info_group)

        return panel

    def _create_plot_panel(self) -> QWidget:
        """Создание панели с графиками"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.plot_canvas = PlotCanvas(width=11, height=12, dpi=100)
        self.plot_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.plot_canvas.setMinimumSize(750, 750)

        scroll.setWidget(self.plot_canvas)
        return scroll

    def _on_build_clicked(self):
        """Обработчик нажатия кнопки построения"""
        variant = self.variant_spinbox.value()
        task_index = self.task_combo.currentIndex()

        try:
            if task_index == 0:
                self._solve_task2(variant)
            else:
                self._solve_task3(variant)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка расчёта: {str(e)}")

    def _solve_task2(self, variant: int):
        """Решение и отображение задачи 2"""
        solver = Task2Solver(variant)
        results = solver.solve()

        # Отображаем результаты в текстовом поле
        p = solver.params
        r = results

        text = f"""ЗАДАЧА 2 - БАЛКА НА ОПОРАХ
Вариант: N = {variant}

═══ Индексы ═══
R = {p.R}, K = {p.K}, S = {p.S}

═══ Исходные данные ═══
L = {p.L:.2f} м
a = {p.a:.2f} м
q = {p.q} кН/м
F = {p.F} кН

═══ Результаты ═══
RA = {r.RA:.1f} кН
RB = {r.RB:.1f} кН

x_max = {r.x_max:.2f} м
M_max = {r.M_max:.1f} кН·м
Расположение: {r.max_loc}

═══ Проверка ═══
ΣY = RA + RB - qL - F
   = {r.RA:.2f} + {r.RB:.2f} - {p.q*p.L:.2f} - {p.F}
   = {r.RA + r.RB - p.q*p.L - p.F:.4f} ≈ 0 ✓
"""
        self.results_text.setText(text)

        # Строим графики
        self.plot_canvas.plot_task2(solver)

    def _solve_task3(self, variant: int):
        """Решение и отображение задачи 3"""
        solver = Task3Solver(variant)
        results = solver.solve()

        p = solver.params
        r = results

        x0_str = f"{r.x0:.3f} м" if r.x0 is not None else "отсутствует"

        text = f"""ЗАДАЧА 3 - СТУПЕНЧАТЫЙ СТЕРЖЕНЬ
Вариант: N = {variant}

═══ Индексы ═══
R = {p.R}, K = {p.K}, S = {p.S}

═══ Исходные данные ═══
L = {p.L:.2f} м
L1 = {p.L1:.3f} м
L2 = {p.L2:.3f} м
L3 = {p.L3:.3f} м

A1 = {p.A1} см²
A2 = {p.A2} см²
A3 = {p.A3} см²

E = {p.E} ГПа

F1 = {p.F1} кН (→)
F2 = {p.F2} кН (←)
F3 = {p.F3} кН (→)

═══ Результаты ═══
RA = {r.RA:.1f} кН

Продольные силы:
  N1 = {r.N1:.1f} кН
  N2 = {r.N2:.1f} кН
  N3 = {r.N3:.1f} кН

Напряжения:
  σ1 = {r.sigma1:.2f} МПа
  σ2 = {r.sigma2:.2f} МПа
  σ3 = {r.sigma3:.2f} МПа

Полное удлинение:
  Δl(L) = {r.delta_l_total:.4f} мм

Пересечение Δl с нулём:
  x0 = {x0_str}

═══ Проверка ═══
ΣX = RA + F1 - F2 + F3
   = {r.RA:.1f} + {p.F1} - {p.F2} + {p.F3}
   = {r.RA + p.F1 - p.F2 + p.F3:.1f} = 0 ✓
"""
        self.results_text.setText(text)

        # Строим графики
        self.plot_canvas.plot_task3(solver)
