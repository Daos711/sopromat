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

        # Балка
        beam_height = 0.15
        ax.add_patch(Rectangle((0, -beam_height/2), L, beam_height,
                                facecolor='lightblue', edgecolor='black', linewidth=2))

        # Ось x
        ax.annotate('', xy=(L + 0.3, 0), xytext=(-0.3, 0),
                    arrowprops=dict(arrowstyle='->', color='black', lw=1.5))
        ax.text(L + 0.35, 0, 'x', fontsize=12, va='center')

        # Опора A (шарнирно-неподвижная) - треугольник
        triangle_h = 0.25
        triangle_w = 0.3
        triangle = Polygon([
            (0, -beam_height/2),
            (-triangle_w/2, -beam_height/2 - triangle_h),
            (triangle_w/2, -beam_height/2 - triangle_h)
        ], facecolor='gray', edgecolor='black')
        ax.add_patch(triangle)
        # Штриховка под опорой
        for i in range(5):
            x_start = -triangle_w/2 + i * triangle_w/5
            ax.plot([x_start, x_start + 0.08],
                    [-beam_height/2 - triangle_h - 0.02, -beam_height/2 - triangle_h - 0.1],
                    'k-', linewidth=1)
        ax.text(0, -beam_height/2 - triangle_h - 0.2, 'A', fontsize=12, ha='center')

        # Опора B (шарнирно-подвижная) - треугольник на кружках
        triangle_B = Polygon([
            (L, -beam_height/2),
            (L - triangle_w/2, -beam_height/2 - triangle_h),
            (L + triangle_w/2, -beam_height/2 - triangle_h)
        ], facecolor='gray', edgecolor='black')
        ax.add_patch(triangle_B)
        # Кружки (ролики)
        for dx in [-0.08, 0.08]:
            circle = plt.Circle((L + dx, -beam_height/2 - triangle_h - 0.05), 0.04,
                                 facecolor='white', edgecolor='black')
            ax.add_patch(circle)
        ax.text(L, -beam_height/2 - triangle_h - 0.2, 'B', fontsize=12, ha='center')

        # Распределённая нагрузка q
        n_arrows = 15
        arrow_spacing = L / n_arrows
        for i in range(n_arrows + 1):
            x = i * arrow_spacing
            ax.annotate('', xy=(x, beam_height/2), xytext=(x, beam_height/2 + 0.4),
                        arrowprops=dict(arrowstyle='->', color='blue', lw=1.5))
        # Линия сверху
        ax.plot([0, L], [beam_height/2 + 0.4, beam_height/2 + 0.4], 'b-', linewidth=2)
        ax.text(L/2, beam_height/2 + 0.5, f'q = {p.q} кН/м', fontsize=11,
                ha='center', color='blue')

        # Сосредоточенная сила F
        ax.annotate('', xy=(a, beam_height/2), xytext=(a, beam_height/2 + 0.7),
                    arrowprops=dict(arrowstyle='->', color='red', lw=2.5))
        ax.text(a, beam_height/2 + 0.8, f'F = {p.F} кН', fontsize=11,
                ha='center', color='red')

        # Размеры
        y_dim = -beam_height/2 - triangle_h - 0.5
        ax.annotate('', xy=(a, y_dim), xytext=(0, y_dim),
                    arrowprops=dict(arrowstyle='<->', color='black', lw=1))
        ax.text(a/2, y_dim - 0.1, f'a = {a:.2f} м', fontsize=10, ha='center')

        ax.annotate('', xy=(L, y_dim - 0.3), xytext=(0, y_dim - 0.3),
                    arrowprops=dict(arrowstyle='<->', color='black', lw=1))
        ax.text(L/2, y_dim - 0.4, f'L = {p.L:.2f} м', fontsize=10, ha='center')

        # Реакции
        ax.annotate('', xy=(0, -beam_height/2 - 0.05), xytext=(0, -beam_height/2 - 0.4),
                    arrowprops=dict(arrowstyle='->', color='green', lw=2))
        ax.text(-0.15, -beam_height/2 - 0.25, f'$R_A$={r.RA:.1f}', fontsize=10, color='green')

        ax.annotate('', xy=(L, -beam_height/2 - 0.05), xytext=(L, -beam_height/2 - 0.4),
                    arrowprops=dict(arrowstyle='->', color='green', lw=2))
        ax.text(L + 0.1, -beam_height/2 - 0.25, f'$R_B$={r.RB:.1f}', fontsize=10, color='green')

        ax.set_xlim(-0.5, L + 0.7)
        ax.set_ylim(-1.3, 1.1)
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
            offset = 0.5 if Q >= 0 else -0.5
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

        # Знаки + и -
        Q_max = max(Q_data)
        Q_min = min(Q_data)
        if Q_max > 0.5:
            ax.text(p.a/2, Q_max/2, '+', fontsize=16, ha='center', va='center')
        if Q_min < -0.5:
            ax.text((p.a + p.L)/2, Q_min/2, '−', fontsize=16, ha='center', va='center')

        ax.set_xlim(-0.1, p.L + 0.1)
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

        # Знак +
        M_max = max(M_data)
        if M_max > 0.5:
            ax.text(r.x_max, M_max/2, '+', fontsize=16, ha='center', va='center')

        ax.set_xlim(-0.1, p.L + 0.1)
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

        info_text = (
            f"L={p.L:.2f}м, a={p.a:.2f}м, q={p.q}кН/м, F={p.F}кН  |  "
            f"$R_A$={r.RA:.1f}кН, $R_B$={r.RB:.1f}кН, "
            f"$x_{{max}}$={r.x_max:.2f}м, $M_{{max}}$={r.M_max:.1f}кН·м ({r.max_loc})"
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

        # Нормализуем координаты для лучшего отображения
        scale = 1.0 / L  # масштаб для нормализации

        # Высоты участков (пропорционально площадям)
        max_A = max(p.A1, p.A2, p.A3)
        h1 = 0.25 * p.A1 / max_A + 0.1
        h2 = 0.25 * p.A2 / max_A + 0.1
        h3 = 0.25 * p.A3 / max_A + 0.1

        # Участок 1
        ax.add_patch(Rectangle((0, -h1/2), L1, h1,
                                facecolor='lightblue', edgecolor='black', linewidth=1.5))
        ax.text(L1/2, 0, f'$A_1$={p.A1}', fontsize=8, ha='center', va='center')

        # Участок 2
        ax.add_patch(Rectangle((L1, -h2/2), L2, h2,
                                facecolor='lightgreen', edgecolor='black', linewidth=1.5))
        ax.text(L1 + L2/2, 0, f'$A_2$={p.A2}', fontsize=8, ha='center', va='center')

        # Участок 3
        ax.add_patch(Rectangle((L1 + L2, -h3/2), L3, h3,
                                facecolor='lightyellow', edgecolor='black', linewidth=1.5))
        ax.text(L1 + L2 + L3/2, 0, f'$A_3$={p.A3}', fontsize=8, ha='center', va='center')

        # Заделка слева
        wall_width = 0.03
        ax.add_patch(Rectangle((-wall_width, -0.3), wall_width, 0.6,
                                facecolor='gray', edgecolor='black'))
        # Штриховка заделки
        for i in range(6):
            y_start = -0.25 + i * 0.1
            ax.plot([-wall_width, -wall_width - 0.05], [y_start, y_start - 0.04],
                    'k-', linewidth=1)
        ax.text(-0.06, -0.38, 'A', fontsize=10, ha='center')

        # Ось x
        ax.annotate('', xy=(L + 0.1, 0), xytext=(-0.08, 0),
                    arrowprops=dict(arrowstyle='->', color='black', lw=1))
        ax.text(L + 0.12, 0, 'x', fontsize=10, va='center')

        # Сила F1 (вправо, в точке L1)
        ax.annotate('', xy=(L1 + 0.08, 0), xytext=(L1 - 0.02, 0),
                    arrowprops=dict(arrowstyle='->', color='blue', lw=2))
        ax.text(L1, 0.28, f'$F_1$={p.F1}', fontsize=9, ha='center', color='blue')

        # Сила F2 (влево, в точке L1+L2)
        ax.annotate('', xy=(L1 + L2 - 0.08, 0), xytext=(L1 + L2 + 0.02, 0),
                    arrowprops=dict(arrowstyle='->', color='red', lw=2))
        ax.text(L1 + L2, 0.28, f'$F_2$={p.F2}', fontsize=9, ha='center', color='red')

        # Сила F3 (вправо, в точке L)
        ax.annotate('', xy=(L + 0.1, 0), xytext=(L - 0.02, 0),
                    arrowprops=dict(arrowstyle='->', color='blue', lw=2))
        ax.text(L + 0.02, 0.28, f'$F_3$={p.F3}', fontsize=9, ha='left', color='blue')

        # Реакция RA
        if r.RA > 0:  # вправо
            ax.annotate('', xy=(0.06, -0.18), xytext=(-0.02, -0.18),
                        arrowprops=dict(arrowstyle='->', color='green', lw=2))
        else:  # влево
            ax.annotate('', xy=(-0.02, -0.18), xytext=(0.06, -0.18),
                        arrowprops=dict(arrowstyle='->', color='green', lw=2))
        ax.text(0.02, -0.28, f'$R_A$={r.RA:.1f}', fontsize=8, ha='center', color='green')

        # Размеры - на одной линии, компактно
        y_dim = -0.42
        # Общая длина L
        ax.annotate('', xy=(L, y_dim), xytext=(0, y_dim),
                    arrowprops=dict(arrowstyle='<->', color='black', lw=0.8))
        ax.text(L/2, y_dim - 0.06, f'L={L:.2f}м', fontsize=8, ha='center')

        # Подписи участков сверху схемы
        ax.text(L1/2, 0.4, f'$L_1$={L1:.2f}', fontsize=7, ha='center', color='gray')
        ax.text(L1 + L2/2, 0.4, f'$L_2$={L2:.2f}', fontsize=7, ha='center', color='gray')
        ax.text(L1 + L2 + L3/2, 0.4, f'$L_3$={L3:.2f}', fontsize=7, ha='center', color='gray')

        ax.set_xlim(-0.15, L + 0.2)
        ax.set_ylim(-0.55, 0.5)
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

        info_text = (
            f"L={p.L:.2f}м, E={p.E}ГПа, "
            f"$F_1$={p.F1}кН(→), $F_2$={p.F2}кН(←), $F_3$={p.F3}кН(→)  |  "
            f"$R_A$={r.RA:.1f}кН, Δl={r.delta_l_total:.4f}мм, $x_0$={x0_str}"
        )

        ax.text(0.5, 0.5, info_text, transform=ax.transAxes,
                fontsize=8, ha='center', va='center',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))


# Нужен импорт для кружков
import matplotlib.pyplot as plt
