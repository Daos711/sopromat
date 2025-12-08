"""
Виджет для отображения эпюр с помощью matplotlib
"""

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.patches import Polygon, FancyArrowPatch, Rectangle, FancyBboxPatch
from matplotlib.lines import Line2D
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

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

        p = solver.params
        r = solver.results

        # 3 подграфика: схема, Q(x), M(x) - без info панели
        gs = self.fig.add_gridspec(3, 1, height_ratios=[1.2, 1, 1], hspace=0.35)

        ax_scheme = self.fig.add_subplot(gs[0])
        ax_Q = self.fig.add_subplot(gs[1])
        ax_M = self.fig.add_subplot(gs[2])

        # Общие xlim для всех графиков
        xlim = (-0.1, p.L + 0.1)

        # --- Схема балки ---
        self._draw_beam_scheme(ax_scheme, p, r, xlim)

        # --- Эпюра Q(x) ---
        self._draw_Q_diagram(ax_Q, solver, xlim)

        # --- Эпюра M(x) ---
        self._draw_M_diagram(ax_M, solver, xlim)

        self.fig.tight_layout()
        self.draw()

    def _draw_beam_scheme(self, ax, p, r, xlim):
        """Рисование схемы балки"""
        L = p.L
        a = p.a

        # Балка
        beam_height = 0.12
        ax.add_patch(Rectangle((0, -beam_height/2), L, beam_height,
                                facecolor='lightblue', edgecolor='black', linewidth=2))

        # Ось x - справа от балки
        ax.annotate('', xy=(L + 0.3, 0), xytext=(L, 0),
                    arrowprops=dict(arrowstyle='->', color='black', lw=1.5))
        ax.text(L + 0.35, 0, 'x', fontsize=11, va='center')

        # Опора A (шарнирно-неподвижная)
        triangle_h = 0.15
        triangle_w = 0.20
        triangle = Polygon([
            (0, -beam_height/2),
            (-triangle_w/2, -beam_height/2 - triangle_h),
            (triangle_w/2, -beam_height/2 - triangle_h)
        ], facecolor='lightgray', edgecolor='black', linewidth=1.5)
        ax.add_patch(triangle)
        # Штриховка
        ground_y = -beam_height/2 - triangle_h
        ax.plot([-triangle_w/2 - 0.03, triangle_w/2 + 0.03], [ground_y, ground_y], 'k-', linewidth=1.5)
        for i in range(5):
            x_start = -triangle_w/2 + i * triangle_w / 4
            ax.plot([x_start, x_start - 0.04], [ground_y, ground_y - 0.05], 'k-', linewidth=1)
        ax.text(0, ground_y - 0.12, 'A', fontsize=10, ha='center', fontweight='bold')

        # Опора B (шарнирно-подвижная)
        triangle_B = Polygon([
            (L, -beam_height/2),
            (L - triangle_w/2, -beam_height/2 - triangle_h),
            (L + triangle_w/2, -beam_height/2 - triangle_h)
        ], facecolor='lightgray', edgecolor='black', linewidth=1.5)
        ax.add_patch(triangle_B)
        # Ролики
        roller_y = -beam_height/2 - triangle_h - 0.03
        for dx in [-0.05, 0, 0.05]:
            circle = plt.Circle((L + dx, roller_y), 0.025,
                                 facecolor='white', edgecolor='black', linewidth=1)
            ax.add_patch(circle)
        ax.plot([L - triangle_w/2 - 0.03, L + triangle_w/2 + 0.03],
                [roller_y - 0.03, roller_y - 0.03], 'k-', linewidth=1.5)
        ax.text(L, roller_y - 0.1, 'B', fontsize=10, ha='center', fontweight='bold')

        # Распределённая нагрузка q
        q_y_top = beam_height/2 + 0.25
        n_arrows = 10
        arrow_spacing = L / n_arrows
        for i in range(n_arrows + 1):
            x = i * arrow_spacing
            ax.annotate('', xy=(x, beam_height/2), xytext=(x, q_y_top),
                        arrowprops=dict(arrowstyle='->', color='blue', lw=1))
        ax.plot([0, L], [q_y_top, q_y_top], 'b-', linewidth=2)
        ax.text(L/2, q_y_top + 0.08, f'q = {p.q} кН/м', fontsize=9, ha='center', color='blue')

        # Сосредоточенная сила F
        F_y_top = q_y_top + 0.35
        ax.annotate('', xy=(a, q_y_top), xytext=(a, F_y_top),
                    arrowprops=dict(arrowstyle='->', color='red', lw=2.5))
        ax.text(a + 0.1, F_y_top - 0.05, f'F = {p.F} кН', fontsize=9, ha='left', color='red')

        # Реакции СВЕРХУ над опорами (как на примере)
        react_y_bottom = q_y_top + 0.05
        react_y_top = react_y_bottom + 0.25
        # RA
        ax.annotate('', xy=(0, react_y_bottom), xytext=(0, react_y_top),
                    arrowprops=dict(arrowstyle='->', color='green', lw=2))
        ax.text(0, react_y_top + 0.05, f'$R_A$={r.RA:.1f}', fontsize=9, color='green', ha='center')
        # RB
        ax.annotate('', xy=(L, react_y_bottom), xytext=(L, react_y_top),
                    arrowprops=dict(arrowstyle='->', color='green', lw=2))
        ax.text(L, react_y_top + 0.05, f'$R_B$={r.RB:.1f}', fontsize=9, color='green', ha='center')

        # Размеры
        y_dim_a = -beam_height/2 - triangle_h - 0.25
        y_dim_L = y_dim_a - 0.18

        ax.annotate('', xy=(a, y_dim_a), xytext=(0, y_dim_a),
                    arrowprops=dict(arrowstyle='<->', color='dimgray', lw=1))
        ax.text(a/2, y_dim_a + 0.05, f'a = {a:.2f} м', fontsize=8, ha='center', color='dimgray')

        ax.annotate('', xy=(L, y_dim_L), xytext=(0, y_dim_L),
                    arrowprops=dict(arrowstyle='<->', color='dimgray', lw=1))
        ax.text(L/2, y_dim_L + 0.05, f'L = {L:.2f} м', fontsize=8, ha='center', color='dimgray')

        # Пунктир от силы F вниз (граница участков)
        ax.axvline(x=a, color='gray', linestyle='--', alpha=0.7, linewidth=1)

        ax.set_xlim(xlim)
        ax.set_ylim(-0.7, 1.0)
        ax.set_aspect('equal', adjustable='datalim')
        ax.axis('off')
        ax.set_title(f'Задача 2. Вариант {p.N}', fontsize=13, fontweight='bold', pad=3)

    def _draw_Q_diagram(self, ax, solver, xlim):
        """Рисование эпюры поперечных сил Q(x)"""
        p = solver.params

        # Данные для двух участков ОТДЕЛЬНО (без соединения - разрыв первого рода)
        n_points = 100

        # Участок 1: от 0 до a
        x1 = np.linspace(0, p.a, n_points)
        Q1 = np.array([solver.Q(x) for x in x1])

        # Участок 2: от a до L
        x2 = np.linspace(p.a, p.L, n_points)
        Q2 = np.array([solver.Q(x) for x in x2])

        # Базовая линия
        ax.axhline(y=0, color='black', linewidth=1.5)

        # Эпюра участок 1 (заливка и линия)
        ax.fill_between(x1, 0, Q1, alpha=0.3, color='blue')
        ax.plot(x1, Q1, 'b-', linewidth=2)
        # Замыкающие вертикальные линии участка 1
        ax.plot([0, 0], [0, Q1[0]], 'b-', linewidth=2)
        ax.plot([p.a, p.a], [0, Q1[-1]], 'b-', linewidth=2)

        # Эпюра участок 2 (заливка и линия)
        ax.fill_between(x2, 0, Q2, alpha=0.3, color='blue')
        ax.plot(x2, Q2, 'b-', linewidth=2)
        # Замыкающие вертикальные линии участка 2
        ax.plot([p.a, p.a], [0, Q2[0]], 'b-', linewidth=2)
        ax.plot([p.L, p.L], [0, Q2[-1]], 'b-', linewidth=2)

        # Подписи значений
        Q_at_0 = solver.Q(0)
        Q_at_a_left = solver.Q(p.a - 1e-9)
        Q_at_a_right = solver.Q(p.a + 1e-9)
        Q_at_L = solver.Q(p.L)

        ax.text(0, Q_at_0, f'{Q_at_0:.2f}', fontsize=9, color='blue', ha='center',
                va='bottom' if Q_at_0 >= 0 else 'top')
        ax.text(p.a - 0.05, Q_at_a_left, f'{Q_at_a_left:.2f}', fontsize=9, color='blue', ha='right',
                va='bottom' if Q_at_a_left >= 0 else 'top')
        ax.text(p.a + 0.05, Q_at_a_right, f'{Q_at_a_right:.2f}', fontsize=9, color='blue', ha='left',
                va='bottom' if Q_at_a_right >= 0 else 'top')
        ax.text(p.L, Q_at_L, f'{Q_at_L:.2f}', fontsize=9, color='blue', ha='center',
                va='bottom' if Q_at_L >= 0 else 'top')

        # Штриховка
        n_lines = 25
        for x in np.linspace(0, p.a - 0.01, n_lines // 2):
            Q = solver.Q(x)
            if abs(Q) > 0.1:
                ax.plot([x, x], [0, Q], 'b-', alpha=0.3, linewidth=0.5)
        for x in np.linspace(p.a + 0.01, p.L, n_lines // 2):
            Q = solver.Q(x)
            if abs(Q) > 0.1:
                ax.plot([x, x], [0, Q], 'b-', alpha=0.3, linewidth=0.5)

        # Знаки в центре областей
        avg_Q1 = (Q_at_0 + Q_at_a_left) / 2
        if abs(avg_Q1) > 0.5:
            sign1 = '+' if avg_Q1 > 0 else '−'
            ax.text(p.a / 2, avg_Q1 / 2, sign1, fontsize=14, ha='center', va='center',
                    fontweight='bold', color='blue', alpha=0.7)

        avg_Q2 = (Q_at_a_right + Q_at_L) / 2
        if abs(avg_Q2) > 0.5:
            sign2 = '+' if avg_Q2 > 0 else '−'
            ax.text((p.a + p.L) / 2, avg_Q2 / 2, sign2, fontsize=14, ha='center', va='center',
                    fontweight='bold', color='blue', alpha=0.7)

        # Пунктир границы участков
        ax.axvline(x=p.a, color='gray', linestyle='--', alpha=0.7, linewidth=1)

        Q_max = max(max(Q1), max(Q2))
        Q_min = min(min(Q1), min(Q2))
        y_margin = max(abs(Q_max), abs(Q_min)) * 0.2
        ax.set_xlim(xlim)
        ax.set_ylim(Q_min - y_margin - 3, Q_max + y_margin + 3)

        ax.set_ylabel('Q, кН', fontsize=10)
        ax.set_title('Эпюра Q(x)', fontsize=11, pad=3)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='both', labelsize=9)

    def _draw_M_diagram(self, ax, solver, xlim):
        """Рисование эпюры изгибающих моментов M(x)"""
        p = solver.params
        r = solver.results

        x_data, M_data = solver.get_M_data()

        # Базовая линия
        ax.axhline(y=0, color='black', linewidth=1.5)

        # Эпюра
        ax.fill_between(x_data, 0, M_data, alpha=0.3, color='red')
        ax.plot(x_data, M_data, 'r-', linewidth=2)

        # Замыкающие вертикальные линии
        ax.plot([0, 0], [0, solver.M(0)], 'r-', linewidth=2)
        ax.plot([p.L, p.L], [0, solver.M(p.L)], 'r-', linewidth=2)

        # Точка максимума
        ax.plot(r.x_max, r.M_max, 'ro', markersize=6)
        ax.text(r.x_max, r.M_max + 2, f'{r.M_max:.2f}', fontsize=9, color='red', ha='center')

        # Значение в точке a
        M_a = solver.M(p.a)
        ax.text(p.a, M_a, f'{M_a:.2f}', fontsize=9, color='red', ha='center',
                va='bottom' if M_a >= 0 else 'top')

        # Штриховка
        n_lines = 25
        for x in np.linspace(0, p.L, n_lines):
            M = solver.M(x)
            if abs(M) > 0.1:
                ax.plot([x, x], [0, M], 'r-', alpha=0.3, linewidth=0.5)

        # Знак + в центре
        M_max = max(M_data)
        if M_max > 0.5:
            ax.text(p.L / 2, M_max / 2, '+', fontsize=14, ha='center', va='center',
                    fontweight='bold', color='red', alpha=0.7)

        # Пунктир границы участков
        ax.axvline(x=p.a, color='gray', linestyle='--', alpha=0.7, linewidth=1)

        M_min = min(M_data)
        y_margin = max(abs(M_max), abs(M_min)) * 0.2 if M_max != 0 else 5
        ax.set_xlim(xlim)
        ax.set_ylim(M_min - 2, M_max + y_margin + 3)

        ax.set_xlabel('x, м', fontsize=10)
        ax.set_ylabel('M, кН·м', fontsize=10)
        ax.set_title('Эпюра M(x)', fontsize=11, pad=3)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='both', labelsize=9)

    def plot_task3(self, solver):
        """Построить эпюры для задачи 3 (стержень)"""
        self.fig.clear()

        p = solver.params
        r = solver.results

        # 4 подграфика без info панели
        gs = self.fig.add_gridspec(4, 1, height_ratios=[1.0, 0.8, 0.8, 0.8], hspace=0.4)

        ax_scheme = self.fig.add_subplot(gs[0])
        ax_N = self.fig.add_subplot(gs[1])
        ax_sigma = self.fig.add_subplot(gs[2])
        ax_dl = self.fig.add_subplot(gs[3])

        # Общие xlim для всех графиков
        xlim = (-0.05, p.L + 0.05)

        # --- Схема стержня ---
        self._draw_rod_scheme(ax_scheme, p, r, xlim)

        # --- Эпюра N(x) ---
        self._draw_N_diagram(ax_N, solver, xlim)

        # --- Эпюра σ(x) ---
        self._draw_sigma_diagram(ax_sigma, solver, xlim)

        # --- Эпюра Δl(x) ---
        self._draw_delta_l_diagram(ax_dl, solver, xlim)

        self.fig.tight_layout()
        self.draw()

    def _draw_rod_scheme(self, ax, p, r, xlim):
        """Рисование схемы ступенчатого стержня"""
        L = p.L
        L1, L2, L3 = p.L1, p.L2, p.L3

        # Высоты участков (пропорционально площадям)
        max_A = max(p.A1, p.A2, p.A3)
        h1 = 0.18 * p.A1 / max_A + 0.06
        h2 = 0.18 * p.A2 / max_A + 0.06
        h3 = 0.18 * p.A3 / max_A + 0.06
        max_h = max(h1, h2, h3)

        # Участки
        ax.add_patch(Rectangle((0, -h1/2), L1, h1,
                                facecolor='lightblue', edgecolor='black', linewidth=1.5))
        ax.add_patch(Rectangle((L1, -h2/2), L2, h2,
                                facecolor='lightgreen', edgecolor='black', linewidth=1.5))
        ax.add_patch(Rectangle((L1 + L2, -h3/2), L3, h3,
                                facecolor='lightyellow', edgecolor='black', linewidth=1.5))

        # Подписи площадей выше участков
        ax.text(L1/2, h1/2 + 0.04, f'$A_1$={p.A1}', fontsize=8, ha='center', va='bottom')
        ax.text(L1 + L2/2, h2/2 + 0.04, f'$A_2$={p.A2}', fontsize=8, ha='center', va='bottom')
        ax.text(L1 + L2 + L3/2, h3/2 + 0.04, f'$A_3$={p.A3}', fontsize=8, ha='center', va='bottom')

        # Заделка
        wall_width = 0.03
        wall_height = max_h + 0.1
        ax.add_patch(Rectangle((-wall_width, -wall_height/2), wall_width, wall_height,
                                facecolor='gray', edgecolor='black'))
        for i in range(6):
            y_start = -wall_height/2 + i * wall_height / 5
            ax.plot([-wall_width, -wall_width - 0.03], [y_start, y_start - 0.02], 'k-', linewidth=1)
        ax.text(-wall_width - 0.02, -wall_height/2 - 0.06, 'A', fontsize=9, ha='center', fontweight='bold')

        # Ось x справа
        ax.annotate('', xy=(L + 0.1, 0), xytext=(L, 0),
                    arrowprops=dict(arrowstyle='->', color='black', lw=1.2))
        ax.text(L + 0.12, 0, 'x', fontsize=10, va='center')

        # Силы
        ax.annotate('', xy=(L1 + 0.04, 0), xytext=(L1 - 0.03, 0),
                    arrowprops=dict(arrowstyle='->', color='blue', lw=2))
        ax.text(L1, max_h/2 + 0.12, f'$F_1$={p.F1}', fontsize=8, ha='center', color='blue')

        ax.annotate('', xy=(L1 + L2 - 0.04, 0), xytext=(L1 + L2 + 0.03, 0),
                    arrowprops=dict(arrowstyle='->', color='red', lw=2))
        ax.text(L1 + L2, max_h/2 + 0.12, f'$F_2$={p.F2}', fontsize=8, ha='center', color='red')

        ax.annotate('', xy=(L + 0.06, 0), xytext=(L, 0),
                    arrowprops=dict(arrowstyle='->', color='blue', lw=2))
        ax.text(L + 0.03, max_h/2 + 0.12, f'$F_3$={p.F3}', fontsize=8, ha='left', color='blue')

        # Реакция RA слева
        if r.RA > 0:
            ax.annotate('', xy=(-wall_width + 0.08, 0), xytext=(-wall_width - 0.06, 0),
                        arrowprops=dict(arrowstyle='->', color='green', lw=2))
        else:
            ax.annotate('', xy=(-wall_width - 0.06, 0), xytext=(-wall_width + 0.08, 0),
                        arrowprops=dict(arrowstyle='->', color='green', lw=2))
        ax.text(-wall_width - 0.07, 0.08, f'$R_A$={r.RA:.1f}', fontsize=7, ha='center', color='green')

        # Размер L
        y_dim = -max_h/2 - 0.12
        ax.annotate('', xy=(L, y_dim), xytext=(0, y_dim),
                    arrowprops=dict(arrowstyle='<->', color='dimgray', lw=0.8))
        ax.text(L/2, y_dim + 0.04, f'L={L:.2f}м', fontsize=7, ha='center', color='dimgray')

        # Длины участков
        y_len = max_h/2 + 0.22
        ax.text(L1/2, y_len, f'$L_1$={L1:.2f}', fontsize=6, ha='center', color='gray')
        ax.text(L1 + L2/2, y_len, f'$L_2$={L2:.2f}', fontsize=6, ha='center', color='gray')
        ax.text(L1 + L2 + L3/2, y_len, f'$L_3$={L3:.2f}', fontsize=6, ha='center', color='gray')

        # Пунктиры границ участков
        ax.axvline(x=L1, color='gray', linestyle='--', alpha=0.7, linewidth=1)
        ax.axvline(x=L1 + L2, color='gray', linestyle='--', alpha=0.7, linewidth=1)

        ax.set_xlim(xlim)
        ax.set_ylim(-max_h/2 - 0.25, max_h/2 + 0.35)
        ax.set_aspect('equal', adjustable='datalim')
        ax.axis('off')
        ax.set_title(f'Задача 3. Вариант {p.N}', fontsize=12, fontweight='bold', pad=3)

    def _draw_N_diagram(self, ax, solver, xlim):
        """Рисование эпюры продольных сил N(x)"""
        p = solver.params
        r = solver.results

        x_data, N_data = solver.get_N_data()

        ax.axhline(y=0, color='black', linewidth=1.5)
        ax.fill_between(x_data, 0, N_data, alpha=0.3, color='blue', step='pre')
        ax.step(x_data, N_data, 'b-', linewidth=2, where='pre')

        # Вертикальные линии
        ax.plot([0, 0], [0, r.N1], 'b-', linewidth=2)
        ax.plot([p.L1, p.L1], [0, r.N1], 'b-', linewidth=2)
        ax.plot([p.L1, p.L1], [0, r.N2], 'b-', linewidth=2)
        ax.plot([p.L1 + p.L2, p.L1 + p.L2], [0, r.N2], 'b-', linewidth=2)
        ax.plot([p.L1 + p.L2, p.L1 + p.L2], [0, r.N3], 'b-', linewidth=2)
        ax.plot([p.L, p.L], [0, r.N3], 'b-', linewidth=2)

        # Подписи
        ax.text(p.L1/2, r.N1, f'{r.N1:.1f}', fontsize=9, color='blue', ha='center',
                va='bottom' if r.N1 >= 0 else 'top')
        ax.text(p.L1 + p.L2/2, r.N2, f'{r.N2:.1f}', fontsize=9, color='blue', ha='center',
                va='bottom' if r.N2 >= 0 else 'top')
        ax.text(p.L1 + p.L2 + p.L3/2, r.N3, f'{r.N3:.1f}', fontsize=9, color='blue', ha='center',
                va='bottom' if r.N3 >= 0 else 'top')

        # Знаки
        if abs(r.N1) > 0.5:
            ax.text(p.L1/2, r.N1/2, '+' if r.N1 > 0 else '−', fontsize=12, ha='center', va='center')
        if abs(r.N2) > 0.5:
            ax.text(p.L1 + p.L2/2, r.N2/2, '+' if r.N2 > 0 else '−', fontsize=12, ha='center', va='center')
        if abs(r.N3) > 0.5:
            ax.text(p.L1 + p.L2 + p.L3/2, r.N3/2, '+' if r.N3 > 0 else '−', fontsize=12, ha='center', va='center')

        # Пунктиры границ
        ax.axvline(x=p.L1, color='gray', linestyle='--', alpha=0.7, linewidth=1)
        ax.axvline(x=p.L1 + p.L2, color='gray', linestyle='--', alpha=0.7, linewidth=1)

        ax.set_xlim(xlim)
        ax.set_ylabel('N, кН', fontsize=9)
        ax.set_title('Эпюра N(x)', fontsize=10, pad=2)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='both', labelsize=8)

    def _draw_sigma_diagram(self, ax, solver, xlim):
        """Рисование эпюры напряжений σ(x)"""
        p = solver.params
        r = solver.results

        x_data, sigma_data = solver.get_sigma_data()

        ax.axhline(y=0, color='black', linewidth=1.5)
        ax.fill_between(x_data, 0, sigma_data, alpha=0.3, color='green', step='pre')
        ax.step(x_data, sigma_data, 'g-', linewidth=2, where='pre')

        # Вертикальные линии
        ax.plot([0, 0], [0, r.sigma1], 'g-', linewidth=2)
        ax.plot([p.L1, p.L1], [0, r.sigma1], 'g-', linewidth=2)
        ax.plot([p.L1, p.L1], [0, r.sigma2], 'g-', linewidth=2)
        ax.plot([p.L1 + p.L2, p.L1 + p.L2], [0, r.sigma2], 'g-', linewidth=2)
        ax.plot([p.L1 + p.L2, p.L1 + p.L2], [0, r.sigma3], 'g-', linewidth=2)
        ax.plot([p.L, p.L], [0, r.sigma3], 'g-', linewidth=2)

        # Подписи
        ax.text(p.L1/2, r.sigma1, f'{r.sigma1:.1f}', fontsize=9, color='green', ha='center',
                va='bottom' if r.sigma1 >= 0 else 'top')
        ax.text(p.L1 + p.L2/2, r.sigma2, f'{r.sigma2:.1f}', fontsize=9, color='green', ha='center',
                va='bottom' if r.sigma2 >= 0 else 'top')
        ax.text(p.L1 + p.L2 + p.L3/2, r.sigma3, f'{r.sigma3:.1f}', fontsize=9, color='green', ha='center',
                va='bottom' if r.sigma3 >= 0 else 'top')

        # Знаки
        if abs(r.sigma1) > 0.5:
            ax.text(p.L1/2, r.sigma1/2, '+' if r.sigma1 > 0 else '−', fontsize=12, ha='center', va='center',
                    fontweight='bold', color='green', alpha=0.7)
        if abs(r.sigma2) > 0.5:
            ax.text(p.L1 + p.L2/2, r.sigma2/2, '+' if r.sigma2 > 0 else '−', fontsize=12, ha='center', va='center',
                    fontweight='bold', color='green', alpha=0.7)
        if abs(r.sigma3) > 0.5:
            ax.text(p.L1 + p.L2 + p.L3/2, r.sigma3/2, '+' if r.sigma3 > 0 else '−', fontsize=12, ha='center', va='center',
                    fontweight='bold', color='green', alpha=0.7)

        # Пунктиры границ
        ax.axvline(x=p.L1, color='gray', linestyle='--', alpha=0.7, linewidth=1)
        ax.axvline(x=p.L1 + p.L2, color='gray', linestyle='--', alpha=0.7, linewidth=1)

        ax.set_xlim(xlim)
        ax.set_ylabel('σ, МПа', fontsize=9)
        ax.set_title('Эпюра σ(x)', fontsize=10, pad=2)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='both', labelsize=8)

    def _draw_delta_l_diagram(self, ax, solver, xlim):
        """Рисование эпюры удлинений Δl(x)"""
        p = solver.params
        r = solver.results

        x_data, dl_data = solver.get_delta_l_data()

        ax.axhline(y=0, color='black', linewidth=1.5)
        ax.fill_between(x_data, 0, dl_data, alpha=0.3, color='purple')
        ax.plot(x_data, dl_data, 'm-', linewidth=2)

        # Замыкающие линии
        ax.plot([0, 0], [0, 0], 'm-', linewidth=2)
        ax.plot([p.L, p.L], [0, solver._dl3], 'm-', linewidth=2)

        # Подписи значений на границах
        ax.text(p.L1, solver._dl1, f'{solver._dl1:.4f}', fontsize=8, color='purple', ha='center', va='bottom')
        ax.text(p.L1 + p.L2, solver._dl2, f'{solver._dl2:.4f}', fontsize=8, color='purple', ha='center', va='bottom')
        ax.text(p.L, solver._dl3, f'{solver._dl3:.4f}', fontsize=8, color='purple', ha='center', va='bottom')

        # Точка пересечения с нулём
        if r.x0 is not None:
            ax.plot(r.x0, 0, 'ko', markersize=5)
            ax.axvline(x=r.x0, color='gray', linestyle='--', alpha=0.5)
            ax.text(r.x0, -0.01, f'$x_0$={r.x0:.3f}', fontsize=7, color='black', ha='center', va='top')

        # ОДИН знак посередине всей эпюры (если вся в верхней или нижней полуплоскости)
        dl_min = min(dl_data)
        dl_max = max(dl_data)

        if dl_min >= 0:  # Вся эпюра в верхней полуплоскости
            ax.text(p.L / 2, dl_max / 2, '+', fontsize=14, ha='center', va='center',
                    fontweight='bold', color='purple', alpha=0.7)
        elif dl_max <= 0:  # Вся эпюра в нижней полуплоскости
            ax.text(p.L / 2, dl_min / 2, '−', fontsize=14, ha='center', va='center',
                    fontweight='bold', color='purple', alpha=0.7)
        else:  # Эпюра пересекает ноль - знаки в разных областях
            # Найдём где положительная и где отрицательная часть
            if r.x0 is not None:
                # До x0 и после x0
                if solver._dl1 > 0:
                    ax.text(r.x0 / 2, dl_max / 2, '+', fontsize=14, ha='center', va='center',
                            fontweight='bold', color='purple', alpha=0.7)
                    ax.text((r.x0 + p.L) / 2, dl_min / 2, '−', fontsize=14, ha='center', va='center',
                            fontweight='bold', color='purple', alpha=0.7)
                else:
                    ax.text(r.x0 / 2, dl_min / 2, '−', fontsize=14, ha='center', va='center',
                            fontweight='bold', color='purple', alpha=0.7)
                    ax.text((r.x0 + p.L) / 2, dl_max / 2, '+', fontsize=14, ha='center', va='center',
                            fontweight='bold', color='purple', alpha=0.7)

        # Пунктиры границ участков
        ax.axvline(x=p.L1, color='gray', linestyle='--', alpha=0.7, linewidth=1)
        ax.axvline(x=p.L1 + p.L2, color='gray', linestyle='--', alpha=0.7, linewidth=1)

        ax.set_xlim(xlim)
        ax.set_xlabel('x, м', fontsize=9)
        ax.set_ylabel('Δl, мм', fontsize=9)
        ax.set_title('Эпюра Δl(x)', fontsize=10, pad=2)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='both', labelsize=8)
