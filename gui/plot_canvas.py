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
        gs = self.fig.add_gridspec(3, 1, height_ratios=[1.5, 1, 1], hspace=0.25)

        ax_scheme = self.fig.add_subplot(gs[0])
        ax_Q = self.fig.add_subplot(gs[1])
        ax_M = self.fig.add_subplot(gs[2])

        # Общие xlim для всех графиков - РОВНО от 0 до L, без отступов
        xlim = (0, p.L)

        # --- Схема балки ---
        self._draw_beam_scheme(ax_scheme, p, r, xlim)

        # --- Эпюра Q(x) ---
        self._draw_Q_diagram(ax_Q, solver, xlim)

        # --- Эпюра M(x) ---
        self._draw_M_diagram(ax_M, solver, xlim)

        self.fig.tight_layout()

        # Сквозные пунктирные линии через все графики
        from matplotlib.lines import Line2D
        from matplotlib.patches import ConnectionPatch
        axes = [ax_scheme, ax_Q, ax_M]

        # Функция для рисования РОВНОГО сквозного пунктира
        def draw_through_line(x_pos):
            # Получаем x в координатах фигуры (одинаковый для всех осей)
            # Используем первую ось для преобразования
            x_fig = ax_Q.transData.transform((x_pos, 0))[0]
            x_fig = self.fig.transFigure.inverted().transform((x_fig, 0))[0]

            # Получаем y границы всех осей в координатах фигуры
            y_top = ax_scheme.get_position().y1
            y_bottom = ax_M.get_position().y0

            # Рисуем одну ровную вертикальную линию через всю фигуру
            line = Line2D([x_fig, x_fig], [y_bottom, y_top],
                         transform=self.fig.transFigure,
                         color='gray', linestyle='--', alpha=0.7, linewidth=1)
            self.fig.add_artist(line)

        # Пунктир на x=0 (левая граница)
        draw_through_line(0)
        # Пунктир на x=a (точка приложения силы)
        draw_through_line(p.a)
        # Пунктир на x=L (правая граница)
        draw_through_line(p.L)

        # Соединяющий пунктир от Q=0 до M_max (если Q пересекает ноль)
        Q_at_a_right = solver.Q(p.a + 1e-9)
        Q_at_L = solver.Q(p.L)
        if Q_at_a_right * Q_at_L < 0 and p.a < r.x_max < p.L - 0.01:
            x_zero = p.a + (0 - Q_at_a_right) * (p.L - p.a) / (Q_at_L - Q_at_a_right)
            con = ConnectionPatch(
                xyA=(x_zero, 0), coordsA=ax_Q.transData,
                xyB=(x_zero, r.M_max), coordsB=ax_M.transData,
                color='gray', linestyle='--', alpha=0.7, linewidth=1
            )
            self.fig.add_artist(con)

        self.draw()

    def _draw_beam_scheme(self, ax, p, r, xlim):
        """Рисование схемы балки"""
        L = p.L
        a = p.a

        # Балка
        beam_height = 0.08
        ax.add_patch(Rectangle((0, -beam_height/2), L, beam_height,
                                facecolor='lightblue', edgecolor='black', linewidth=2))

        # Ось x убрана по просьбе пользователя

        # Опора A (шарнирно-неподвижная) - clip_on=False чтобы не обрезалось
        triangle_h = 0.12
        triangle_w = L * 0.06
        triangle = Polygon([
            (0, -beam_height/2),
            (-triangle_w/2, -beam_height/2 - triangle_h),
            (triangle_w/2, -beam_height/2 - triangle_h)
        ], facecolor='lightgray', edgecolor='black', linewidth=1.5, clip_on=False)
        ax.add_patch(triangle)
        # Штриховка
        ground_y = -beam_height/2 - triangle_h
        ax.plot([-triangle_w/2 - L*0.01, triangle_w/2 + L*0.01], [ground_y, ground_y], 'k-', linewidth=1.5, clip_on=False)
        for i in range(5):
            x_start = -triangle_w/2 + i * triangle_w / 4
            ax.plot([x_start, x_start - L*0.015], [ground_y, ground_y - 0.04], 'k-', linewidth=1, clip_on=False)
        # Подпись A слева от опоры
        ax.text(-triangle_w/2 - L*0.02, ground_y - 0.04, 'A', fontsize=10, ha='right', fontweight='bold', clip_on=False)

        # Опора B (шарнирно-подвижная) - clip_on=False чтобы не обрезалось
        triangle_B = Polygon([
            (L, -beam_height/2),
            (L - triangle_w/2, -beam_height/2 - triangle_h),
            (L + triangle_w/2, -beam_height/2 - triangle_h)
        ], facecolor='lightgray', edgecolor='black', linewidth=1.5, clip_on=False)
        ax.add_patch(triangle_B)
        # Два ролика - маленькие, между треугольником и штриховкой
        roller_r = L * 0.008  # Радиус ролика
        roller_y = -beam_height/2 - triangle_h - roller_r - 0.005  # Чуть ниже треугольника
        for dx in [-L*0.018, L*0.018]:
            circle = plt.Circle((L + dx, roller_y), roller_r,
                                 facecolor='white', edgecolor='black', linewidth=1, clip_on=False)
            ax.add_patch(circle)
        # Линия под роликами
        ground_y_B = roller_y - roller_r - 0.01
        ax.plot([L - triangle_w/2 - L*0.01, L + triangle_w/2 + L*0.01],
                [ground_y_B, ground_y_B], 'k-', linewidth=1.5, clip_on=False)
        # Штриховка под роликами
        for i in range(5):
            x_start = L - triangle_w/2 + i * triangle_w / 4
            ax.plot([x_start, x_start - L*0.015], [ground_y_B, ground_y_B - 0.04], 'k-', linewidth=1, clip_on=False)
        # Подпись B справа от опоры
        ax.text(L + triangle_w/2 + L*0.02, ground_y_B - 0.02, 'B', fontsize=10, ha='left', fontweight='bold', clip_on=False)

        # Распределённая нагрузка q
        q_y_top = beam_height/2 + 0.18
        n_arrows = 12
        arrow_spacing = L / n_arrows
        for i in range(n_arrows + 1):
            x = i * arrow_spacing
            ax.annotate('', xy=(x, beam_height/2), xytext=(x, q_y_top),
                        arrowprops=dict(arrowstyle='->', color='blue', lw=1))
        ax.plot([0, L], [q_y_top, q_y_top], 'b-', linewidth=2)
        ax.text(L/2, q_y_top + 0.05, f'q = {p.q} кН/м', fontsize=9, ha='center', color='blue')

        # Сосредоточенная сила F - от верха до БАЛКИ (не до линии q)
        F_y_top = q_y_top + 0.25
        ax.annotate('', xy=(a, beam_height/2), xytext=(a, F_y_top),
                    arrowprops=dict(arrowstyle='->', color='red', lw=2.5))
        ax.text(a + L*0.02, F_y_top, f'F = {p.F} кН', fontsize=9, ha='left', va='center', color='red')

        # Реакции ОТ ВЕРХНЕЙ ЧАСТИ БАЛКИ ВВЕРХ (стрелка начинается на балке, идёт вверх)
        # Вектор должен быть выше линии q (выше q_y_top)
        react_start = beam_height/2  # От верхней части балки
        react_len = 0.35  # Длинный вектор выше линии q
        # RA - от верхней части балки A вверх, ровно над x=0
        ax.annotate('', xy=(0, react_start + react_len), xytext=(0, react_start),
                    arrowprops=dict(arrowstyle='->', color='green', lw=2.5))
        ra_val = r.RA
        ra_str = f'{ra_val:.0f}' if ra_val == int(ra_val) else f'{ra_val:.1f}'
        ax.text(0, react_start + react_len + 0.03, f'$R_A$={ra_str}', fontsize=9, color='green', ha='center', va='bottom')
        # RB - от верхней части балки B вверх, ровно над x=L
        ax.annotate('', xy=(L, react_start + react_len), xytext=(L, react_start),
                    arrowprops=dict(arrowstyle='->', color='green', lw=2.5))
        rb_val = r.RB
        rb_str = f'{rb_val:.0f}' if rb_val == int(rb_val) else f'{rb_val:.1f}'
        ax.text(L, react_start + react_len + 0.03, f'$R_B$={rb_str}', fontsize=9, color='green', ha='center', va='bottom')

        # Размеры
        y_dim_a = ground_y - 0.12
        y_dim_L = y_dim_a - 0.12

        ax.annotate('', xy=(a, y_dim_a), xytext=(0, y_dim_a),
                    arrowprops=dict(arrowstyle='<->', color='dimgray', lw=1))
        ax.text(a/2, y_dim_a + 0.04, f'a = {a:.2f} м', fontsize=8, ha='center', color='dimgray')

        ax.annotate('', xy=(L, y_dim_L), xytext=(0, y_dim_L),
                    arrowprops=dict(arrowstyle='<->', color='dimgray', lw=1))
        ax.text(L/2, y_dim_L + 0.04, f'L = {L:.2f} м', fontsize=8, ha='center', color='dimgray')

        # Пунктиры границ рисуются как сквозные линии в plot_task2

        # xlim ТАКОЙ ЖЕ как у эпюр для единых пунктирных линий
        # Опоры рисуются с clip_on=False, так что они будут видны
        ax.set_xlim(xlim)
        ax.set_ylim(-0.65, 0.75)  # Расширим, чтобы опоры были полностью видны
        ax.axis('off')
        ax.set_title(f'Задача 2. Вариант {p.N}', fontsize=13, fontweight='bold', pad=15)

    def _draw_Q_diagram(self, ax, solver, xlim):
        """Рисование эпюры поперечных сил Q(x)"""
        p = solver.params

        # Данные для двух участков ОТДЕЛЬНО (без соединения - разрыв первого рода)
        n_points = 100
        eps = 1e-6  # Малый зазор чтобы участки НЕ соединялись в точке разрыва

        # Участок 1: от 0 до a (НЕ включая a - останавливаемся чуть раньше)
        x1 = np.linspace(0, p.a - eps, n_points)
        Q1 = np.array([solver.Q(x) for x in x1])

        # Участок 2: от a до L (НЕ включая a - начинаем чуть позже)
        x2 = np.linspace(p.a + eps, p.L, n_points)
        Q2 = np.array([solver.Q(x) for x in x2])

        # Базовая линия
        ax.axhline(y=0, color='black', linewidth=1.5)

        # Эпюра участок 1 (заливка и линия)
        ax.fill_between(x1, 0, Q1, alpha=0.3, color='blue')
        ax.plot(x1, Q1, 'b-', linewidth=2)
        # Замыкающая вертикальная линия ТОЛЬКО слева (x=0)
        ax.plot([0, 0], [0, Q1[0]], 'b-', linewidth=2)
        # НА ГРАНИЦЕ РАЗРЫВА (x=a) вертикальных линий НЕТ - только пунктир

        # Эпюра участок 2 (заливка и линия)
        ax.fill_between(x2, 0, Q2, alpha=0.3, color='blue')
        ax.plot(x2, Q2, 'b-', linewidth=2)
        # Замыкающая вертикальная линия ТОЛЬКО справа (x=L)
        ax.plot([p.L, p.L], [0, Q2[-1]], 'b-', linewidth=2)
        # НА ГРАНИЦЕ РАЗРЫВА (x=a) вертикальных линий НЕТ - только пунктир

        # РАЗРЫВ ПЕРВОГО РОДА: участки НЕ соединены - между ними только пунктир

        # Подписи значений - умное позиционирование вне эпюры
        Q_at_0 = solver.Q(0)
        Q_at_a_left = solver.Q(p.a - 1e-9)
        Q_at_a_right = solver.Q(p.a + 1e-9)
        Q_at_L = solver.Q(p.L)

        # Вычисляем отступ для подписей (выносим за пределы эпюры, но не далеко)
        Q_range = max(max(Q1), max(Q2)) - min(min(Q1), min(Q2))
        label_offset = max(Q_range * 0.08, 1.5)  # Небольшой отступ

        # Функция для определения позиции подписи (выносим за эпюру)
        def get_label_y(Q_val, offset):
            if Q_val >= 0:
                return Q_val + offset, 'bottom'
            else:
                return Q_val - offset, 'top'

        # Подпись в x=0
        y_pos, va = get_label_y(Q_at_0, label_offset)
        ax.text(p.L * 0.02, y_pos, f'{Q_at_0:.2f}', fontsize=9, color='blue', ha='left', va=va)

        # Подписи у точки разрыва (x=a) - проверка на перекрытие
        y_left, va_left = get_label_y(Q_at_a_left, label_offset)
        y_right, va_right = get_label_y(Q_at_a_right, label_offset)

        # Если подписи слишком близко по вертикали, раздвигаем их
        if abs(y_left - y_right) < label_offset * 1.2:
            # Верхнюю поднимаем выше, нижнюю опускаем ниже
            if y_left >= y_right:
                y_left += label_offset * 0.6
                y_right -= label_offset * 0.6
            else:
                y_right += label_offset * 0.6
                y_left -= label_offset * 0.6

        ax.text(p.a - p.L * 0.02, y_left, f'{Q_at_a_left:.2f}', fontsize=9, color='blue', ha='right', va=va_left)
        ax.text(p.a + p.L * 0.02, y_right, f'{Q_at_a_right:.2f}', fontsize=9, color='blue', ha='left', va=va_right)

        # Подпись в x=L
        y_pos, va = get_label_y(Q_at_L, label_offset)
        ax.text(p.L - p.L * 0.02, y_pos, f'{Q_at_L:.2f}', fontsize=9, color='blue', ha='right', va=va)

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

        # Знаки в ЦЕНТРЕ каждой области
        # Минимальная ширина области для показа знака (достаточно большая чтобы знак поместился)
        min_width_for_sign = p.L * 0.15

        # Область 1: от 0 до a (трапеция)
        center_x1 = p.a / 2
        center_y1 = (Q_at_0 + Q_at_a_left) / 2 * 0.5
        if p.a > min_width_for_sign:
            if Q_at_0 > 0 and Q_at_a_left > 0:
                ax.text(center_x1, center_y1, '+', fontsize=16, ha='center', va='center',
                        fontweight='bold', color='blue', alpha=0.8)
            elif Q_at_0 < 0 and Q_at_a_left < 0:
                ax.text(center_x1, center_y1, '−', fontsize=16, ha='center', va='center',
                        fontweight='bold', color='blue', alpha=0.8)

        # Область 2: от a до L
        if Q_at_a_right * Q_at_L < 0:  # Q меняет знак - есть пересечение с нулём
            x_zero = p.a + (0 - Q_at_a_right) * (p.L - p.a) / (Q_at_L - Q_at_a_right)
            # Пунктир рисуется в plot_task2 как соединяющая линия между Q и M

            if Q_at_a_right > 0:
                pos_width = x_zero - p.a
                neg_width = p.L - x_zero
            else:
                pos_width = p.L - x_zero
                neg_width = x_zero - p.a

            # Знак + в положительной части (только если область достаточно большая)
            if Q_at_a_right > 0 and pos_width > min_width_for_sign:
                # Центроид треугольника: x = (a + a + x_zero)/3 = (2a + x_zero)/3
                center_x_pos = (2 * p.a + x_zero) / 3
                center_y_pos = Q_at_a_right / 3
                ax.text(center_x_pos, center_y_pos, '+', fontsize=16, ha='center', va='center',
                        fontweight='bold', color='blue', alpha=0.8)

            # Знак − в отрицательной части (только если область достаточно большая)
            if Q_at_L < 0 and neg_width > min_width_for_sign:
                # Центроид треугольника: x = (x_zero + L + L)/3 = (x_zero + 2L)/3
                center_x_neg = (x_zero + 2 * p.L) / 3
                center_y_neg = Q_at_L / 3
                ax.text(center_x_neg, center_y_neg, '−', fontsize=16, ha='center', va='center',
                        fontweight='bold', color='blue', alpha=0.8)
        else:
            # Q не меняет знак - один знак для всей области
            width2 = p.L - p.a
            if width2 > min_width_for_sign:
                center_x2 = (p.a + p.L) / 2
                center_y2 = (Q_at_a_right + Q_at_L) / 2 * 0.5
                if Q_at_a_right > 0 or Q_at_L > 0:
                    ax.text(center_x2, center_y2, '+', fontsize=16, ha='center', va='center',
                            fontweight='bold', color='blue', alpha=0.8)
                elif Q_at_a_right < 0 or Q_at_L < 0:
                    ax.text(center_x2, center_y2, '−', fontsize=16, ha='center', va='center',
                            fontweight='bold', color='blue', alpha=0.8)

        # Пунктиры рисуются как сквозные линии в plot_task2

        Q_max = max(max(Q1), max(Q2))
        Q_min = min(min(Q1), min(Q2))
        # Увеличиваем отступы для подписей, которые теперь вынесены за эпюру
        y_margin = max(abs(Q_max), abs(Q_min)) * 0.25 + label_offset
        ax.set_xlim(xlim)
        ax.set_ylim(Q_min - y_margin, Q_max + y_margin)

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
        ax.text(r.x_max + p.L * 0.03, r.M_max + 2, f'{r.M_max:.2f}', fontsize=9, color='red', ha='left')

        # Значение в точке a (сдвигаем влево чтобы не налезало на максимум)
        M_a = solver.M(p.a)
        # Если точка a близка к максимуму, сдвигаем подпись влево
        if abs(p.a - r.x_max) < p.L * 0.1:
            ha_align = 'right'
            x_offset = -p.L * 0.02
        else:
            ha_align = 'center'
            x_offset = 0
        ax.text(p.a + x_offset, M_a, f'{M_a:.2f}', fontsize=9, color='red', ha=ha_align,
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

        # Пунктиры рисуются как сквозные линии в plot_task2

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

        # 4 подграфика без info панели - схема повыше
        gs = self.fig.add_gridspec(4, 1, height_ratios=[1.5, 0.8, 0.8, 0.8], hspace=0.35)

        ax_scheme = self.fig.add_subplot(gs[0])
        ax_N = self.fig.add_subplot(gs[1])
        ax_sigma = self.fig.add_subplot(gs[2])
        ax_dl = self.fig.add_subplot(gs[3])

        # Единый xlim для всех графиков - ПУНКТИРНОЕ ЕДИНСТВО
        xlim = (0, p.L)

        # --- Схема стержня (с тем же xlim, векторы RA и F3 с clip_on=False) ---
        self._draw_rod_scheme(ax_scheme, p, r, xlim)

        # --- Эпюра N(x) (стандартный xlim) ---
        self._draw_N_diagram(ax_N, solver, xlim)

        # --- Эпюра σ(x) (стандартный xlim) ---
        self._draw_sigma_diagram(ax_sigma, solver, xlim)

        # --- Эпюра Δl(x) (стандартный xlim) ---
        self._draw_delta_l_diagram(ax_dl, solver, xlim)

        # tight_layout с отступами для векторов RA (слева) и F3 (справа)
        # Увеличиваем отступы для надёжного отображения стрелок
        self.fig.tight_layout(rect=[0.1, 0, 0.92, 1])

        # Сквозные пунктирные линии через все графики
        from matplotlib.lines import Line2D
        axes = [ax_scheme, ax_N, ax_sigma, ax_dl]

        # Функция для рисования РОВНОГО сквозного пунктира
        def draw_through_line(x_pos):
            # Получаем x в координатах фигуры (одинаковый для всех осей)
            x_fig = ax_N.transData.transform((x_pos, 0))[0]
            x_fig = self.fig.transFigure.inverted().transform((x_fig, 0))[0]

            # Получаем y границы всех осей в координатах фигуры
            y_top = ax_scheme.get_position().y1
            y_bottom = ax_dl.get_position().y0

            # Рисуем одну ровную вертикальную линию через всю фигуру
            line = Line2D([x_fig, x_fig], [y_bottom, y_top],
                         transform=self.fig.transFigure,
                         color='gray', linestyle='--', alpha=0.7, linewidth=1)
            self.fig.add_artist(line)

        # Пунктир на x=0 (левая граница)
        draw_through_line(0)
        # Пунктир на x=L1 (граница 1-2 участков)
        draw_through_line(p.L1)
        # Пунктир на x=L1+L2 (граница 2-3 участков)
        draw_through_line(p.L1 + p.L2)
        # Пунктир на x=L (правая граница)
        draw_through_line(p.L)

        self.draw()

    def _draw_rod_scheme(self, ax, p, r, xlim):
        """Рисование схемы ступенчатого стержня"""
        L = p.L
        L1, L2, L3 = p.L1, p.L2, p.L3

        # Высоты участков (пропорционально площадям) - в относительных единицах
        max_A = max(p.A1, p.A2, p.A3)
        base_h = 0.25
        h1 = base_h * p.A1 / max_A + 0.08
        h2 = base_h * p.A2 / max_A + 0.08
        h3 = base_h * p.A3 / max_A + 0.08
        max_h = max(h1, h2, h3)

        # Участки
        ax.add_patch(Rectangle((0, -h1/2), L1, h1,
                                facecolor='lightblue', edgecolor='black', linewidth=1.5))
        ax.add_patch(Rectangle((L1, -h2/2), L2, h2,
                                facecolor='lightgreen', edgecolor='black', linewidth=1.5))
        ax.add_patch(Rectangle((L1 + L2, -h3/2), L3, h3,
                                facecolor='lightyellow', edgecolor='black', linewidth=1.5))

        # Подписи площадей выше участков
        ax.text(L1/2, h1/2 + 0.05, f'$A_1$={p.A1}', fontsize=8, ha='center', va='bottom')
        ax.text(L1 + L2/2, h2/2 + 0.05, f'$A_2$={p.A2}', fontsize=8, ha='center', va='bottom')
        ax.text(L1 + L2 + L3/2, h3/2 + 0.05, f'$A_3$={p.A3}', fontsize=8, ha='center', va='bottom')

        # Заделка - вертикальная линия на x=0 со штриховкой (clip_on=False для видимости)
        wall_height = max_h + 0.15
        # Вертикальная линия заделки на x=0
        ax.plot([0, 0], [-wall_height/2, wall_height/2], 'k-', linewidth=3, clip_on=False)
        # Штриховка заделки - от линии влево
        hatch_len = L * 0.03
        for i in range(10):
            y_pos = -wall_height/2 + i * wall_height / 9
            ax.plot([0, -hatch_len], [y_pos, y_pos - 0.03], 'k-', linewidth=1.5, clip_on=False)
        ax.text(-hatch_len/2, -wall_height/2 - 0.08, 'A', fontsize=10, ha='center', fontweight='bold', clip_on=False)

        # Силы - начинаются РОВНО на границах участков
        arrow_len = L * 0.08

        # F1 вправо - начинается РОВНО на границе L1
        ax.annotate('', xy=(L1 + arrow_len, 0), xytext=(L1, 0),
                    arrowprops=dict(arrowstyle='->', color='blue', lw=2.5))
        ax.text(L1 + arrow_len/2, max_h/2 + 0.12, f'$F_1$={p.F1}', fontsize=9, ha='center', color='blue')

        # F2 влево - начинается РОВНО на границе L1+L2
        ax.annotate('', xy=(L1 + L2 - arrow_len, 0), xytext=(L1 + L2, 0),
                    arrowprops=dict(arrowstyle='->', color='red', lw=2.5))
        ax.text(L1 + L2 - arrow_len/2, max_h/2 + 0.12, f'$F_2$={p.F2}', fontsize=9, ha='center', color='red')

        # Реакция RA - начинается на заделке (x=0) и идёт ВЛЕВО
        # Используем FancyArrowPatch для надёжного отображения за пределами xlim
        ra_arrow_len = L * 0.08
        ra_arrow = FancyArrowPatch((0, 0), (-ra_arrow_len, 0),
                                   arrowstyle='->', mutation_scale=15,
                                   color='green', linewidth=3, clip_on=False)
        ax.add_patch(ra_arrow)
        ra_val = abs(r.RA)
        ra_str = f'{ra_val:.0f}' if ra_val == int(ra_val) else f'{ra_val:.1f}'
        ax.text(-ra_arrow_len/2, max_h/2 + 0.12, f'$R_A$={ra_str}', fontsize=9, ha='center', color='green', fontweight='bold', clip_on=False)

        # F3 вправо - начинается на правой границе 3-го участка (x=L) и идёт ВПРАВО
        f3_arrow = FancyArrowPatch((L, 0), (L + arrow_len, 0),
                                   arrowstyle='->', mutation_scale=15,
                                   color='blue', linewidth=2.5, clip_on=False)
        ax.add_patch(f3_arrow)
        ax.text(L + arrow_len/2, max_h/2 + 0.12, f'$F_3$={p.F3}', fontsize=9, ha='center', color='blue', clip_on=False)

        # Размер L
        y_dim = -max_h/2 - 0.15
        ax.annotate('', xy=(L, y_dim), xytext=(0, y_dim),
                    arrowprops=dict(arrowstyle='<->', color='dimgray', lw=0.8))
        ax.text(L/2, y_dim + 0.05, f'L={L:.2f}м', fontsize=8, ha='center', color='dimgray')

        # Длины участков сверху
        y_len = max_h/2 + 0.28
        ax.text(L1/2, y_len, f'$L_1$={L1:.2f}', fontsize=7, ha='center', color='gray')
        ax.text(L1 + L2/2, y_len, f'$L_2$={L2:.2f}', fontsize=7, ha='center', color='gray')
        ax.text(L1 + L2 + L3/2, y_len, f'$L_3$={L3:.2f}', fontsize=7, ha='center', color='gray')

        # Пунктиры рисуются как сквозные линии в plot_task3

        # xlim передается из plot_task3, расширенный для показа RA и F3
        ax.set_xlim(xlim)
        ax.set_ylim(-max_h/2 - 0.35, max_h/2 + 0.5)
        ax.axis('off')
        ax.set_title(f'Задача 3. Вариант {p.N}', fontsize=12, fontweight='bold', pad=15)

    def _draw_N_diagram(self, ax, solver, xlim):
        """Рисование эпюры продольных сил N(x)"""
        p = solver.params
        r = solver.results

        ax.axhline(y=0, color='black', linewidth=1.5)

        # Рисуем каждый участок ОТДЕЛЬНО (без вертикальных линий на внутренних границах)
        # Участок 1: от 0 до L1
        ax.fill_between([0, p.L1], [r.N1, r.N1], 0, alpha=0.3, color='blue')
        ax.plot([0, p.L1], [r.N1, r.N1], 'b-', linewidth=2)  # Горизонтальная линия
        ax.plot([0, 0], [0, r.N1], 'b-', linewidth=2)  # Вертикальная только на x=0

        # Участок 2: от L1 до L1+L2
        ax.fill_between([p.L1, p.L1 + p.L2], [r.N2, r.N2], 0, alpha=0.3, color='blue')
        ax.plot([p.L1, p.L1 + p.L2], [r.N2, r.N2], 'b-', linewidth=2)

        # Участок 3: от L1+L2 до L
        ax.fill_between([p.L1 + p.L2, p.L], [r.N3, r.N3], 0, alpha=0.3, color='blue')
        ax.plot([p.L1 + p.L2, p.L], [r.N3, r.N3], 'b-', linewidth=2)
        ax.plot([p.L, p.L], [0, r.N3], 'b-', linewidth=2)  # Вертикальная только на x=L

        # Подписи (абсолютные значения - минус не нужен, т.к. видно по положению)
        # Форматирование: убираем .0 для целых чисел
        def fmt(val):
            return f'{abs(val):.0f}' if abs(val) == int(abs(val)) else f'{abs(val):.1f}'

        # Для отрицательных - выносим к правому краю участка, чтобы не накладывались на ось
        # Для положительных - по центру сверху
        if r.N1 >= 0:
            ax.text(p.L1/2, r.N1, fmt(r.N1), fontsize=9, color='blue', ha='center', va='bottom')
        else:
            ax.text(p.L1 - p.L*0.02, r.N1/2, fmt(r.N1), fontsize=9, color='blue', ha='right', va='center')

        if r.N2 >= 0:
            ax.text(p.L1 + p.L2/2, r.N2, fmt(r.N2), fontsize=9, color='blue', ha='center', va='bottom')
        else:
            ax.text(p.L1 + p.L2 - p.L*0.02, r.N2/2, fmt(r.N2), fontsize=9, color='blue', ha='right', va='center')

        if r.N3 >= 0:
            ax.text(p.L1 + p.L2 + p.L3/2, r.N3, fmt(r.N3), fontsize=9, color='blue', ha='center', va='bottom')
        else:
            ax.text(p.L - p.L*0.02, r.N3/2, fmt(r.N3), fontsize=9, color='blue', ha='right', va='center')

        # Знаки
        if abs(r.N1) > 0.5:
            ax.text(p.L1/2, r.N1/2, '+' if r.N1 > 0 else '−', fontsize=12, ha='center', va='center')
        if abs(r.N2) > 0.5:
            ax.text(p.L1 + p.L2/2, r.N2/2, '+' if r.N2 > 0 else '−', fontsize=12, ha='center', va='center')
        if abs(r.N3) > 0.5:
            ax.text(p.L1 + p.L2 + p.L3/2, r.N3/2, '+' if r.N3 > 0 else '−', fontsize=12, ha='center', va='center')

        # Пунктиры рисуются как сквозные линии в plot_task3

        ax.set_xlim(xlim)
        ax.set_ylabel('N, кН', fontsize=9)
        ax.set_title('Эпюра N(x)', fontsize=10, pad=2)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='both', labelsize=8)

    def _draw_sigma_diagram(self, ax, solver, xlim):
        """Рисование эпюры напряжений σ(x)"""
        p = solver.params
        r = solver.results

        ax.axhline(y=0, color='black', linewidth=1.5)

        # Рисуем каждый участок ОТДЕЛЬНО (без вертикальных линий на внутренних границах)
        # Участок 1: от 0 до L1
        ax.fill_between([0, p.L1], [r.sigma1, r.sigma1], 0, alpha=0.3, color='green')
        ax.plot([0, p.L1], [r.sigma1, r.sigma1], 'g-', linewidth=2)
        ax.plot([0, 0], [0, r.sigma1], 'g-', linewidth=2)  # Вертикальная только на x=0

        # Участок 2: от L1 до L1+L2
        ax.fill_between([p.L1, p.L1 + p.L2], [r.sigma2, r.sigma2], 0, alpha=0.3, color='green')
        ax.plot([p.L1, p.L1 + p.L2], [r.sigma2, r.sigma2], 'g-', linewidth=2)

        # Участок 3: от L1+L2 до L
        ax.fill_between([p.L1 + p.L2, p.L], [r.sigma3, r.sigma3], 0, alpha=0.3, color='green')
        ax.plot([p.L1 + p.L2, p.L], [r.sigma3, r.sigma3], 'g-', linewidth=2)
        ax.plot([p.L, p.L], [0, r.sigma3], 'g-', linewidth=2)  # Вертикальная только на x=L

        # Подписи (абсолютные значения - минус не нужен, т.к. видно по положению)
        # Форматирование: убираем .0 для целых чисел
        def fmt(val):
            return f'{abs(val):.0f}' if abs(val) == int(abs(val)) else f'{abs(val):.1f}'

        # Для отрицательных - выносим к правому краю участка, чтобы не накладывались на ось
        # Для положительных - по центру сверху
        if r.sigma1 >= 0:
            ax.text(p.L1/2, r.sigma1, fmt(r.sigma1), fontsize=9, color='green', ha='center', va='bottom')
        else:
            ax.text(p.L1 - p.L*0.02, r.sigma1/2, fmt(r.sigma1), fontsize=9, color='green', ha='right', va='center')

        if r.sigma2 >= 0:
            ax.text(p.L1 + p.L2/2, r.sigma2, fmt(r.sigma2), fontsize=9, color='green', ha='center', va='bottom')
        else:
            ax.text(p.L1 + p.L2 - p.L*0.02, r.sigma2/2, fmt(r.sigma2), fontsize=9, color='green', ha='right', va='center')

        if r.sigma3 >= 0:
            ax.text(p.L1 + p.L2 + p.L3/2, r.sigma3, fmt(r.sigma3), fontsize=9, color='green', ha='center', va='bottom')
        else:
            ax.text(p.L - p.L*0.02, r.sigma3/2, fmt(r.sigma3), fontsize=9, color='green', ha='right', va='center')

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

        # Пунктиры рисуются как сквозные линии в plot_task3

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

        # Вычисляем min/max для позиционирования
        dl_min = min(dl_data)
        dl_max = max(dl_data)

        # Подписи значений на границах - немного выше точек
        offset = abs(dl_max) * 0.08 + 0.003  # Небольшое смещение вверх
        ax.text(p.L1, solver._dl1 + offset, f'{solver._dl1:.4f}', fontsize=8, color='purple', ha='center', va='bottom')
        ax.text(p.L1 + p.L2, solver._dl2 + offset, f'{solver._dl2:.4f}', fontsize=8, color='purple', ha='center', va='bottom')
        ax.text(p.L, solver._dl3 + offset, f'{solver._dl3:.4f}', fontsize=8, color='purple', ha='center', va='bottom')

        # Точка пересечения с нулём
        if r.x0 is not None:
            ax.plot(r.x0, 0, 'ko', markersize=5)
            ax.axvline(x=r.x0, color='gray', linestyle='--', alpha=0.5)
            ax.text(r.x0, -0.01, f'$x_0$={r.x0:.3f}', fontsize=7, color='black', ha='center', va='top')

        # ОДИН знак посередине всей эпюры (если вся в верхней или нижней полуплоскости)
        # Знак ставится в центре по X и Y относительно реальной высоты эпюры

        # Интерполируем значение эпюры в заданной точке x
        def get_dl_at_x(x_target):
            for i in range(len(x_data) - 1):
                if x_data[i] <= x_target <= x_data[i + 1]:
                    # Линейная интерполяция
                    t = (x_target - x_data[i]) / (x_data[i + 1] - x_data[i]) if x_data[i + 1] != x_data[i] else 0
                    return dl_data[i] + t * (dl_data[i + 1] - dl_data[i])
            return dl_data[-1]

        if dl_min >= 0:  # Вся эпюра в верхней полуплоскости
            # Центр по X = L/2, центр по Y = половина высоты эпюры в этой точке
            x_center = p.L / 2
            y_at_center = get_dl_at_x(x_center)
            ax.text(x_center, y_at_center / 2, '+', fontsize=14, ha='center', va='center',
                    fontweight='bold', color='purple', alpha=0.7)
        elif dl_max <= 0:  # Вся эпюра в нижней полуплоскости
            x_center = p.L / 2
            y_at_center = get_dl_at_x(x_center)
            ax.text(x_center, y_at_center / 2, '−', fontsize=14, ha='center', va='center',
                    fontweight='bold', color='purple', alpha=0.7)
        else:  # Эпюра пересекает ноль - знаки в разных областях
            if r.x0 is not None:
                # До x0 и после x0
                if solver._dl1 > 0:
                    # Положительная часть от 0 до x0
                    x_pos = r.x0 / 2
                    y_pos = get_dl_at_x(x_pos) / 2
                    ax.text(x_pos, y_pos, '+', fontsize=14, ha='center', va='center',
                            fontweight='bold', color='purple', alpha=0.7)
                    # Отрицательная часть от x0 до L
                    x_neg = (r.x0 + p.L) / 2
                    y_neg = get_dl_at_x(x_neg) / 2
                    ax.text(x_neg, y_neg, '−', fontsize=14, ha='center', va='center',
                            fontweight='bold', color='purple', alpha=0.7)
                else:
                    # Отрицательная часть от 0 до x0
                    x_neg = r.x0 / 2
                    y_neg = get_dl_at_x(x_neg) / 2
                    ax.text(x_neg, y_neg, '−', fontsize=14, ha='center', va='center',
                            fontweight='bold', color='purple', alpha=0.7)
                    # Положительная часть от x0 до L
                    x_pos = (r.x0 + p.L) / 2
                    y_pos = get_dl_at_x(x_pos) / 2
                    ax.text(x_pos, y_pos, '+', fontsize=14, ha='center', va='center',
                            fontweight='bold', color='purple', alpha=0.7)

        # Пунктиры рисуются как сквозные линии в plot_task3

        ax.set_xlim(xlim)
        ax.set_xlabel('x, м', fontsize=9)
        ax.set_ylabel('Δl, мм', fontsize=9)
        ax.set_title('Эпюра Δl(x)', fontsize=10, pad=2)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='both', labelsize=8)
