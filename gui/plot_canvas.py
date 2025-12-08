"""
Виджет для отображения эпюр с помощью matplotlib
"""

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.patches import Polygon, FancyArrowPatch, Rectangle, FancyBboxPatch
from matplotlib.lines import Line2D
import matplotlib.patches as mpatches

from typing import List, Tuple, Optional


class PlotCanvas(FigureCanvas):
    """Виджет для отображения эпюр"""

    def __init__(self, parent=None, width=12, height=10, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)

    def clear(self):
        """Очистить все графики"""
        self.fig.clear()
        self.draw()

    def plot_task2(self, solver):
        """Построить эпюры для задачи 2 (балка)"""
        self.fig.clear()

        # 4 подграфика: схема, Q(x), M(x), результаты
        gs = self.fig.add_gridspec(4, 1, height_ratios=[1.0, 1, 1, 0.3],
                                    hspace=0.5)

        ax_scheme = self.fig.add_subplot(gs[0])
        ax_Q = self.fig.add_subplot(gs[1])
        ax_M = self.fig.add_subplot(gs[2])
        ax_info = self.fig.add_subplot(gs[3])

        p = solver.params
        r = solver.results

        # --- Схема балки ---
        self._draw_beam_scheme(ax_scheme, p, r)

        # --- Эпюра Q(x) ---
        self._draw_Q_diagram(ax_Q, solver)

        # --- Эпюра M(x) ---
        self._draw_M_diagram(ax_M, solver)

        # --- Информация ---
        self._draw_task2_info(ax_info, p, r)

        self.fig.tight_layout()
        self.draw()

    def _draw_beam_scheme(self, ax, p, r):
        """Рисование схемы балки"""
        L = p.L
        a = p.a

        # Балка (шире)
        beam_height = 0.20
        ax.add_patch(Rectangle((0, -beam_height/2), L, beam_height,
                                facecolor='lightblue', edgecolor='black', linewidth=2))

        # Ось x - только справа от балки как продолжение
        ax.annotate('', xy=(L + 0.5, 0), xytext=(L, 0),
                    arrowprops=dict(arrowstyle='->', color='black', lw=1.5))
        ax.text(L + 0.55, 0, 'x', fontsize=12, va='center')

        # Опора A (шарнирно-неподвижная) - треугольник со штриховкой
        triangle_h = 0.22
        triangle_w = 0.28
        triangle = Polygon([
            (0, -beam_height/2),
            (-triangle_w/2, -beam_height/2 - triangle_h),
            (triangle_w/2, -beam_height/2 - triangle_h)
        ], facecolor='lightgray', edgecolor='black', linewidth=1.5)
        ax.add_patch(triangle)
        # Штриховка под опорой A (земля)
        ground_y = -beam_height/2 - triangle_h
        ax.plot([-triangle_w/2 - 0.05, triangle_w/2 + 0.05], [ground_y, ground_y], 'k-', linewidth=1.5)
        for i in range(6):
            x_start = -triangle_w/2 - 0.02 + i * (triangle_w + 0.04) / 5
            ax.plot([x_start, x_start - 0.06], [ground_y, ground_y - 0.08], 'k-', linewidth=1)
        ax.text(0, ground_y - 0.18, 'A', fontsize=11, ha='center', fontweight='bold')

        # Опора B (шарнирно-подвижная) - треугольник на линии с роликами
        triangle_B = Polygon([
            (L, -beam_height/2),
            (L - triangle_w/2, -beam_height/2 - triangle_h),
            (L + triangle_w/2, -beam_height/2 - triangle_h)
        ], facecolor='lightgray', edgecolor='black', linewidth=1.5)
        ax.add_patch(triangle_B)
        # Ролики под опорой B
        roller_y = -beam_height/2 - triangle_h - 0.05
        for dx in [-0.07, 0, 0.07]:
            circle = plt.Circle((L + dx, roller_y), 0.035,
                                 facecolor='white', edgecolor='black', linewidth=1)
            ax.add_patch(circle)
        # Линия под роликами
        ax.plot([L - triangle_w/2 - 0.05, L + triangle_w/2 + 0.05],
                [roller_y - 0.04, roller_y - 0.04], 'k-', linewidth=1.5)
        ax.text(L, roller_y - 0.16, 'B', fontsize=11, ha='center', fontweight='bold')

        # Распределённая нагрузка q
        q_y_top = beam_height/2 + 0.35
        n_arrows = 12
        arrow_spacing = L / n_arrows
        for i in range(n_arrows + 1):
            x = i * arrow_spacing
            ax.annotate('', xy=(x, beam_height/2), xytext=(x, q_y_top),
                        arrowprops=dict(arrowstyle='->', color='blue', lw=1.2))
        # Линия сверху
        ax.plot([0, L], [q_y_top, q_y_top], 'b-', linewidth=2)
        ax.text(L/2, q_y_top + 0.12, f'q = {p.q} кН/м', fontsize=10,
                ha='center', color='blue')

        # Сосредоточенная сила F (выше распределённой нагрузки)
        F_y_top = q_y_top + 0.45
        ax.annotate('', xy=(a, q_y_top), xytext=(a, F_y_top),
                    arrowprops=dict(arrowstyle='->', color='red', lw=2.5))
        ax.text(a + 0.15, F_y_top - 0.1, f'F = {p.F} кН', fontsize=10,
                ha='left', color='red')

        # Размеры - ниже опор, с отступом от стрелок
        y_dim_a = -beam_height/2 - triangle_h - 0.38
        y_dim_L = y_dim_a - 0.28

        # Размер a
        ax.annotate('', xy=(a, y_dim_a), xytext=(0, y_dim_a),
                    arrowprops=dict(arrowstyle='<->', color='dimgray', lw=1))
        ax.text(a/2, y_dim_a + 0.08, f'a = {a:.2f} м', fontsize=9, ha='center', color='dimgray')

        # Размер L
        ax.annotate('', xy=(L, y_dim_L), xytext=(0, y_dim_L),
                    arrowprops=dict(arrowstyle='<->', color='dimgray', lw=1))
        ax.text(L/2, y_dim_L + 0.08, f'L = {L:.2f} м', fontsize=9, ha='center', color='dimgray')

        # Реакции - слева и справа от опор, не поверх них
        react_arrow_len = 0.35
        # RA - слева от опоры A
        ax.annotate('', xy=(-0.25, -beam_height/2 + react_arrow_len),
                    xytext=(-0.25, -beam_height/2),
                    arrowprops=dict(arrowstyle='->', color='green', lw=2))
        ax.text(-0.4, -beam_height/2 + react_arrow_len/2, f'$R_A$={r.RA:.1f}',
                fontsize=9, color='green', ha='right', va='center')

        # RB - справа от опоры B
        ax.annotate('', xy=(L + 0.25, -beam_height/2 + react_arrow_len),
                    xytext=(L + 0.25, -beam_height/2),
                    arrowprops=dict(arrowstyle='->', color='green', lw=2))
        ax.text(L + 0.4, -beam_height/2 + react_arrow_len/2, f'$R_B$={r.RB:.1f}',
                fontsize=9, color='green', ha='left', va='center')

        ax.set_xlim(-0.7, L + 0.8)
        ax.set_ylim(-1.1, 1.2)
        ax.set_aspect('equal', adjustable='datalim')
        ax.axis('off')
        ax.set_title(f'Задача 2. Вариант {p.N}', fontsize=14, fontweight='bold', pad=5)

    def _draw_Q_diagram(self, ax, solver):
        """Рисование эпюры поперечных сил Q(x)"""
        p = solver.params
        r = solver.results

        x_data, Q_data = solver.get_Q_data()

        # Базовая линия
        ax.axhline(y=0, color='black', linewidth=1.5)

        # Эпюра с заливкой
        ax.fill_between(x_data, 0, Q_data, alpha=0.3, color='blue')
        ax.plot(x_data, Q_data, 'b-', linewidth=2)

        # Скачок в точке a
        Q_left = solver.Q(p.a - 1e-9)
        Q_right = solver.Q(p.a + 1e-9)
        ax.plot([p.a, p.a], [Q_left, Q_right], 'b-', linewidth=2)

        # Подписи значений
        key_points = solver.get_key_points_Q()
        for x, Q, label in key_points:
            ax.annotate(label, (x, Q), textcoords="offset points",
                        xytext=(0, 10 if Q >= 0 else -15),
                        ha='center', fontsize=9, color='blue')

        # Штриховка
        n_lines = 30
        x_hatch = np.linspace(0, p.L, n_lines)
        for x in x_hatch:
            Q = solver.Q(x)
            if abs(Q) > 0.1:
                ax.plot([x, x], [0, Q], 'b-', alpha=0.3, linewidth=0.5)

        # Знаки + и - в ЦЕНТРЕ областей
        Q_at_0 = solver.Q(0)
        Q_at_a_left = solver.Q(p.a - 1e-9)
        Q_at_a_right = solver.Q(p.a + 1e-9)
        Q_at_L = solver.Q(p.L)

        # Участок 1: от 0 до a
        avg_Q1 = (Q_at_0 + Q_at_a_left) / 2
        x_center1 = p.a / 2
        if abs(avg_Q1) > 0.5:
            sign1 = '+' if avg_Q1 > 0 else '−'
            ax.text(x_center1, avg_Q1 / 2, sign1, fontsize=14, ha='center', va='center',
                    fontweight='bold', color='blue', alpha=0.7)

        # Участок 2: от a до L
        avg_Q2 = (Q_at_a_right + Q_at_L) / 2
        x_center2 = (p.a + p.L) / 2
        if abs(avg_Q2) > 0.5:
            sign2 = '+' if avg_Q2 > 0 else '−'
            ax.text(x_center2, avg_Q2 / 2, sign2, fontsize=14, ha='center', va='center',
                    fontweight='bold', color='blue', alpha=0.7)

        # Увеличиваем отступы для подписей
        Q_max = max(Q_data)
        Q_min = min(Q_data)
        y_margin = max(abs(Q_max), abs(Q_min)) * 0.15
        ax.set_xlim(-0.1, p.L + 0.1)
        ax.set_ylim(Q_min - y_margin - 5, Q_max + y_margin + 5)

        ax.set_ylabel('Q, кН', fontsize=10)
        ax.set_title('Эпюра Q(x)', fontsize=11, pad=3)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='both', labelsize=9)

        # Отметка точки a
        ax.axvline(x=p.a, color='gray', linestyle='--', alpha=0.5)

    def _draw_M_diagram(self, ax, solver):
        """Рисование эпюры изгибающих моментов M(x)"""
        p = solver.params
        r = solver.results

        x_data, M_data = solver.get_M_data()

        # Базовая линия
        ax.axhline(y=0, color='black', linewidth=1.5)

        # Эпюра - M рисуется вниз для положительных значений (по правилам сопромата)
        # Но для наглядности оставим как есть (положительные вверх)
        ax.fill_between(x_data, 0, M_data, alpha=0.3, color='red')
        ax.plot(x_data, M_data, 'r-', linewidth=2)

        # Подписи значений
        key_points = solver.get_key_points_M()
        for x, M, label in key_points:
            ax.annotate(label, (x, M), textcoords="offset points",
                        xytext=(0, 10 if M >= 0 else -15),
                        ha='center', fontsize=9, color='red')

        # Точка максимума
        ax.plot(r.x_max, r.M_max, 'ro', markersize=8)

        # Штриховка
        n_lines = 30
        x_hatch = np.linspace(0, p.L, n_lines)
        for x in x_hatch:
            M = solver.M(x)
            if abs(M) > 0.1:
                ax.plot([x, x], [0, M], 'r-', alpha=0.3, linewidth=0.5)

        # Знак + в центре области (по x - центр балки, по y - середина высоты эпюры)
        M_max = max(M_data)
        M_min = min(M_data)
        if M_max > 0.5:
            # Центр по x - там где максимум эпюры примерно
            x_center = p.L / 2
            y_center = M_max / 2
            ax.text(x_center, y_center, '+', fontsize=14, ha='center', va='center',
                    fontweight='bold', color='red', alpha=0.7)

        # Увеличиваем отступы для подписей
        y_margin = max(abs(M_max), abs(M_min)) * 0.15 if M_max != 0 else 5
        ax.set_xlim(-0.1, p.L + 0.1)
        ax.set_ylim(M_min - 3, M_max + y_margin + 5)

        ax.set_xlabel('x, м', fontsize=10)
        ax.set_ylabel('M, кН·м', fontsize=10)
        ax.set_title('Эпюра M(x)', fontsize=11, pad=3)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='both', labelsize=9)

        # Отметка точки a
        ax.axvline(x=p.a, color='gray', linestyle='--', alpha=0.5)

    def _draw_task2_info(self, ax, p, r):
        """Информационная панель для задачи 2"""
        ax.axis('off')

        # Разбиваем на две строки для лучшего отображения
        info_text = (
            f"L={p.L:.2f}м, a={p.a:.2f}м, q={p.q}кН/м, F={p.F}кН\n"
            f"$R_A$={r.RA:.1f}кН, $R_B$={r.RB:.1f}кН, "
            f"$M_{{max}}$={r.M_max:.1f}кН·м (x={r.x_max:.2f}м)"
        )

        ax.text(0.5, 0.5, info_text, transform=ax.transAxes,
                fontsize=9, ha='center', va='center',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    def plot_task3(self, solver):
        """Построить эпюры для задачи 3 (стержень)"""
        self.fig.clear()

        # 5 подграфиков: схема, N(x), σ(x), Δl(x), результаты
        gs = self.fig.add_gridspec(5, 1, height_ratios=[1.0, 0.8, 0.8, 0.8, 0.25],
                                    hspace=0.55)

        ax_scheme = self.fig.add_subplot(gs[0])
        ax_N = self.fig.add_subplot(gs[1])
        ax_sigma = self.fig.add_subplot(gs[2])
        ax_dl = self.fig.add_subplot(gs[3])
        ax_info = self.fig.add_subplot(gs[4])

        p = solver.params
        r = solver.results

        # --- Схема стержня ---
        self._draw_rod_scheme(ax_scheme, p, r)

        # --- Эпюра N(x) ---
        self._draw_N_diagram(ax_N, solver)

        # --- Эпюра σ(x) ---
        self._draw_sigma_diagram(ax_sigma, solver)

        # --- Эпюра Δl(x) ---
        self._draw_delta_l_diagram(ax_dl, solver)

        # --- Информация ---
        self._draw_task3_info(ax_info, p, r)

        self.fig.tight_layout()
        self.draw()

    def _draw_rod_scheme(self, ax, p, r):
        """Рисование схемы ступенчатого стержня"""
        L = p.L
        L1, L2, L3 = p.L1, p.L2, p.L3

        # Высоты участков (пропорционально площадям)
        max_A = max(p.A1, p.A2, p.A3)
        h1 = 0.22 * p.A1 / max_A + 0.08
        h2 = 0.22 * p.A2 / max_A + 0.08
        h3 = 0.22 * p.A3 / max_A + 0.08
        max_h = max(h1, h2, h3)

        # Участок 1
        ax.add_patch(Rectangle((0, -h1/2), L1, h1,
                                facecolor='lightblue', edgecolor='black', linewidth=1.5))

        # Участок 2
        ax.add_patch(Rectangle((L1, -h2/2), L2, h2,
                                facecolor='lightgreen', edgecolor='black', linewidth=1.5))

        # Участок 3
        ax.add_patch(Rectangle((L1 + L2, -h3/2), L3, h3,
                                facecolor='lightyellow', edgecolor='black', linewidth=1.5))

        # Подписи площадей - ВЫШЕ участков, не на центральной линии
        ax.text(L1/2, h1/2 + 0.06, f'$A_1$={p.A1}', fontsize=8, ha='center', va='bottom')
        ax.text(L1 + L2/2, h2/2 + 0.06, f'$A_2$={p.A2}', fontsize=8, ha='center', va='bottom')
        ax.text(L1 + L2 + L3/2, h3/2 + 0.06, f'$A_3$={p.A3}', fontsize=8, ha='center', va='bottom')

        # Заделка слева
        wall_width = 0.04
        wall_height = max_h + 0.15
        ax.add_patch(Rectangle((-wall_width, -wall_height/2), wall_width, wall_height,
                                facecolor='gray', edgecolor='black'))
        # Штриховка заделки
        n_hatch = 7
        for i in range(n_hatch):
            y_start = -wall_height/2 + i * wall_height / (n_hatch - 1)
            ax.plot([-wall_width, -wall_width - 0.04], [y_start, y_start - 0.03],
                    'k-', linewidth=1)

        # Ось x - только справа от конструкции (продолжение)
        ax.annotate('', xy=(L + 0.15, 0), xytext=(L, 0),
                    arrowprops=dict(arrowstyle='->', color='black', lw=1.2))
        ax.text(L + 0.17, 0, 'x', fontsize=10, va='center')

        # Сила F1 (вправо, на границе L1)
        arrow_y = 0
        ax.annotate('', xy=(L1 + 0.06, arrow_y), xytext=(L1 - 0.04, arrow_y),
                    arrowprops=dict(arrowstyle='->', color='blue', lw=2))
        ax.text(L1, max_h/2 + 0.18, f'$F_1$={p.F1}', fontsize=9, ha='center', color='blue')

        # Сила F2 (влево, на границе L1+L2)
        ax.annotate('', xy=(L1 + L2 - 0.06, arrow_y), xytext=(L1 + L2 + 0.04, arrow_y),
                    arrowprops=dict(arrowstyle='->', color='red', lw=2))
        ax.text(L1 + L2, max_h/2 + 0.18, f'$F_2$={p.F2}', fontsize=9, ha='center', color='red')

        # Сила F3 (вправо, на конце L)
        ax.annotate('', xy=(L + 0.08, arrow_y), xytext=(L, arrow_y),
                    arrowprops=dict(arrowstyle='->', color='blue', lw=2))
        ax.text(L + 0.04, max_h/2 + 0.18, f'$F_3$={p.F3}', fontsize=9, ha='left', color='blue')

        # Реакция RA - слева от заделки, по оси симметрии (y=0)
        ra_arrow_len = 0.12
        if r.RA > 0:  # вправо
            ax.annotate('', xy=(-wall_width + ra_arrow_len, 0), xytext=(-wall_width - 0.08, 0),
                        arrowprops=dict(arrowstyle='->', color='green', lw=2))
        else:  # влево
            ax.annotate('', xy=(-wall_width - 0.08, 0), xytext=(-wall_width + ra_arrow_len, 0),
                        arrowprops=dict(arrowstyle='->', color='green', lw=2))
        ax.text(-wall_width - 0.1, 0.12, f'$R_A$={r.RA:.1f}', fontsize=8, ha='center', color='green')
        ax.text(-wall_width - 0.02, -wall_height/2 - 0.08, 'A', fontsize=10, ha='center', fontweight='bold')

        # Размеры - ниже конструкции, подписи НАД стрелками
        y_dim = -max_h/2 - 0.18
        # Общая длина L
        ax.annotate('', xy=(L, y_dim), xytext=(0, y_dim),
                    arrowprops=dict(arrowstyle='<->', color='dimgray', lw=0.8))
        ax.text(L/2, y_dim + 0.05, f'L={L:.2f}м', fontsize=8, ha='center', color='dimgray')

        # Подписи длин участков - выше сил
        y_len = max_h/2 + 0.32
        ax.text(L1/2, y_len, f'$L_1$={L1:.2f}', fontsize=7, ha='center', color='gray')
        ax.text(L1 + L2/2, y_len, f'$L_2$={L2:.2f}', fontsize=7, ha='center', color='gray')
        ax.text(L1 + L2 + L3/2, y_len, f'$L_3$={L3:.2f}', fontsize=7, ha='center', color='gray')

        ax.set_xlim(-0.22, L + 0.25)
        ax.set_ylim(-max_h/2 - 0.35, max_h/2 + 0.45)
        ax.set_aspect('equal', adjustable='datalim')
        ax.axis('off')
        ax.set_title(f'Задача 3. Вариант {p.N}', fontsize=13, fontweight='bold', pad=3)

    def _draw_N_diagram(self, ax, solver):
        """Рисование эпюры продольных сил N(x)"""
        p = solver.params
        r = solver.results

        x_data, N_data = solver.get_N_data()

        # Базовая линия
        ax.axhline(y=0, color='black', linewidth=1.5)

        # Эпюра с заливкой
        ax.fill_between(x_data, 0, N_data, alpha=0.3, color='blue', step='pre')
        ax.step(x_data, N_data, 'b-', linewidth=2, where='pre')

        # Вертикальные линии на границах
        ax.plot([p.L1, p.L1], [0, r.N1], 'b-', linewidth=2)
        ax.plot([p.L1, p.L1], [r.N1, r.N2], 'b-', linewidth=2)
        ax.plot([p.L1 + p.L2, p.L1 + p.L2], [0, r.N2], 'b-', linewidth=2)
        ax.plot([p.L1 + p.L2, p.L1 + p.L2], [r.N2, r.N3], 'b-', linewidth=2)
        ax.plot([p.L, p.L], [0, r.N3], 'b-', linewidth=2)

        # Подписи
        key_points = solver.get_key_points_N()
        for x, N, label in key_points:
            offset_y = 5 if N >= 0 else -12
            ax.annotate(label, (x, N), textcoords="offset points",
                        xytext=(0, offset_y), ha='center', fontsize=9, color='blue')

        # Знаки
        if r.N1 > 0:
            ax.text(p.L1/2, r.N1/2, '+', fontsize=12, ha='center', va='center')
        elif r.N1 < 0:
            ax.text(p.L1/2, r.N1/2, '−', fontsize=12, ha='center', va='center')

        if r.N2 > 0:
            ax.text(p.L1 + p.L2/2, r.N2/2, '+', fontsize=12, ha='center', va='center')
        elif r.N2 < 0:
            ax.text(p.L1 + p.L2/2, r.N2/2, '−', fontsize=12, ha='center', va='center')

        if r.N3 > 0:
            ax.text(p.L1 + p.L2 + p.L3/2, r.N3/2, '+', fontsize=12, ha='center', va='center')

        ax.set_xlim(-0.05, p.L + 0.05)
        ax.set_ylabel('N, кН', fontsize=9)
        ax.set_title('Эпюра N(x)', fontsize=10, pad=2)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='both', labelsize=8)

    def _draw_sigma_diagram(self, ax, solver):
        """Рисование эпюры напряжений σ(x)"""
        p = solver.params
        r = solver.results

        x_data, sigma_data = solver.get_sigma_data()

        ax.axhline(y=0, color='black', linewidth=1.5)
        ax.fill_between(x_data, 0, sigma_data, alpha=0.3, color='green', step='pre')
        ax.step(x_data, sigma_data, 'g-', linewidth=2, where='pre')

        # Вертикальные линии
        ax.plot([p.L1, p.L1], [0, r.sigma1], 'g-', linewidth=2)
        ax.plot([p.L1, p.L1], [r.sigma1, r.sigma2], 'g-', linewidth=2)
        ax.plot([p.L1 + p.L2, p.L1 + p.L2], [0, r.sigma2], 'g-', linewidth=2)
        ax.plot([p.L1 + p.L2, p.L1 + p.L2], [r.sigma2, r.sigma3], 'g-', linewidth=2)
        ax.plot([p.L, p.L], [0, r.sigma3], 'g-', linewidth=2)

        # Подписи
        key_points = solver.get_key_points_sigma()
        for x, sigma, label in key_points:
            offset_y = 5 if sigma >= 0 else -12
            ax.annotate(label, (x, sigma), textcoords="offset points",
                        xytext=(0, offset_y), ha='center', fontsize=9, color='green')

        # Знаки +/- в центре каждого участка
        if abs(r.sigma1) > 0.5:
            sign1 = '+' if r.sigma1 > 0 else '−'
            ax.text(p.L1/2, r.sigma1/2, sign1, fontsize=12, ha='center', va='center',
                    fontweight='bold', color='green', alpha=0.7)
        if abs(r.sigma2) > 0.5:
            sign2 = '+' if r.sigma2 > 0 else '−'
            ax.text(p.L1 + p.L2/2, r.sigma2/2, sign2, fontsize=12, ha='center', va='center',
                    fontweight='bold', color='green', alpha=0.7)
        if abs(r.sigma3) > 0.5:
            sign3 = '+' if r.sigma3 > 0 else '−'
            ax.text(p.L1 + p.L2 + p.L3/2, r.sigma3/2, sign3, fontsize=12, ha='center', va='center',
                    fontweight='bold', color='green', alpha=0.7)

        ax.set_xlim(-0.05, p.L + 0.05)
        ax.set_ylabel('σ, МПа', fontsize=9)
        ax.set_title('Эпюра σ(x)', fontsize=10, pad=2)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='both', labelsize=8)

    def _draw_delta_l_diagram(self, ax, solver):
        """Рисование эпюры удлинений Δl(x)"""
        p = solver.params
        r = solver.results

        x_data, dl_data = solver.get_delta_l_data()

        ax.axhline(y=0, color='black', linewidth=1.5)
        ax.fill_between(x_data, 0, dl_data, alpha=0.3, color='purple')
        ax.plot(x_data, dl_data, 'm-', linewidth=2)

        # Подписи
        key_points = solver.get_key_points_delta_l()
        for x, dl, label in key_points:
            offset_y = 5 if dl >= 0 else -12
            ax.annotate(label, (x, dl), textcoords="offset points",
                        xytext=(0, offset_y), ha='center', fontsize=9, color='purple')

        # Точка пересечения с нулём
        if r.x0 is not None:
            ax.plot(r.x0, 0, 'ko', markersize=6)
            ax.axvline(x=r.x0, color='gray', linestyle='--', alpha=0.5)

        # Знаки +/- на эпюре (в зависимости от преобладающего знака)
        # Находим среднее значение на каждом участке
        dl1_avg = solver._dl1 / 2 if solver._dl1 else 0
        dl2_avg = (solver._dl1 + solver._dl2) / 2 if solver._dl2 else 0
        dl3_avg = (solver._dl2 + solver._dl3) / 2 if solver._dl3 else 0

        # Знак на участке 1
        if abs(dl1_avg) > 0.001:
            sign1 = '+' if dl1_avg > 0 else '−'
            ax.text(p.L1/2, dl1_avg, sign1, fontsize=12, ha='center', va='center',
                    fontweight='bold', color='purple', alpha=0.7)

        # Знак на участке 2
        if abs(dl2_avg) > 0.001 and abs(solver._dl2 - solver._dl1) > 0.001:
            mid_x2 = p.L1 + p.L2/2
            mid_dl2 = solver._dl1 + (solver._dl2 - solver._dl1) / 2
            sign2 = '+' if mid_dl2 > 0 else '−'
            ax.text(mid_x2, mid_dl2, sign2, fontsize=12, ha='center', va='center',
                    fontweight='bold', color='purple', alpha=0.7)

        # Знак на участке 3
        if abs(dl3_avg) > 0.001 and abs(solver._dl3 - solver._dl2) > 0.001:
            mid_x3 = p.L1 + p.L2 + p.L3/2
            mid_dl3 = solver._dl2 + (solver._dl3 - solver._dl2) / 2
            sign3 = '+' if mid_dl3 > 0 else '−'
            ax.text(mid_x3, mid_dl3, sign3, fontsize=12, ha='center', va='center',
                    fontweight='bold', color='purple', alpha=0.7)

        ax.set_xlim(-0.05, p.L + 0.05)
        ax.set_xlabel('x, м', fontsize=9)
        ax.set_ylabel('Δl, мм', fontsize=9)
        ax.set_title('Эпюра Δl(x)', fontsize=10, pad=2)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='both', labelsize=8)

    def _draw_task3_info(self, ax, p, r):
        """Информационная панель для задачи 3"""
        ax.axis('off')

        x0_str = f"{r.x0:.3f}м" if r.x0 is not None else "нет"

        # Разбиваем на две строки для лучшего отображения
        info_text = (
            f"L={p.L:.2f}м, E={p.E}ГПа, "
            f"$F_1$={p.F1}кН, $F_2$={p.F2}кН, $F_3$={p.F3}кН\n"
            f"$R_A$={r.RA:.1f}кН, Δl={r.delta_l_total:.4f}мм, $x_0$={x0_str}"
        )

        ax.text(0.5, 0.5, info_text, transform=ax.transAxes,
                fontsize=8, ha='center', va='center',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))


# Нужен импорт для кружков
import matplotlib.pyplot as plt
