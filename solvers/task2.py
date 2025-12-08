"""
Задача 2: Балка на опорах. Эпюры Q(x) и M(x)

Схема:
- Балка длины L
- Слева шарнирно-неподвижная опора A
- Справа шарнирно-подвижная опора B
- Равномерно распределённая нагрузка q по всей длине (вниз)
- Сосредоточенная сила F в сечении x = a (вниз)

Требуется:
- Найти реакции RA, RB
- Построить эпюры Q(x) и M(x)
- Определить xmax и Mmax
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple, List


@dataclass
class Task2Params:
    """Параметры задачи 2"""
    N: int          # Номер варианта
    R: int          # Индекс R
    K: int          # Индекс K
    S: int          # Индекс S
    L: float        # Длина балки, м
    a: float        # Позиция силы F, м
    q: float        # Распределённая нагрузка, кН/м
    F: float        # Сосредоточенная сила, кН


@dataclass
class Task2Results:
    """Результаты расчёта задачи 2"""
    params: Task2Params
    RA: float       # Реакция в опоре A, кН
    RB: float       # Реакция в опоре B, кН
    x_max: float    # Координата максимального момента, м
    M_max: float    # Максимальный момент, кН·м
    max_loc: str    # Где находится максимум


class Task2Solver:
    """Решатель задачи 2 - балка на двух опорах"""

    # Таблицы коэффициентов
    ALPHA_R = [0.22, 0.27, 0.31, 0.36, 0.41, 0.46, 0.53]
    XI_S = [-0.02, -0.01, 0.0, 0.01, 0.02]
    U_R = [0, 1, 1, 2, 2, 3, 3]
    V_R = [3, 5, 7, 9, 11, 13, 15]

    def __init__(self, N: int):
        """
        Инициализация решателя.

        Args:
            N: Номер варианта (1-35)
        """
        if not 1 <= N <= 35:
            raise ValueError(f"Номер варианта должен быть от 1 до 35, получено: {N}")

        self.N = N
        self.params = self._calculate_params()
        self.results = None

    def _calculate_params(self) -> Task2Params:
        """Вычисление параметров по номеру варианта"""
        N = self.N

        # Индексы
        R = 1 + ((N - 1) % 7)
        K = 1 + ((N - 1) // 7)
        S = 1 + ((N - 1) % 5)

        # Коэффициенты из таблиц
        alpha_R = self.ALPHA_R[R - 1]
        xi_S = self.XI_S[S - 1]
        u_R = self.U_R[R - 1]
        v_R = self.V_R[R - 1]

        # Параметры задачи
        L = 5.00 + 0.10 * (K - 1) + 0.02 * (R - 1)
        a = L * (alpha_R + xi_S)
        q = 9 + (K - 1) + u_R
        F = 14 + 2 * (K - 1) + v_R

        return Task2Params(N=N, R=R, K=K, S=S, L=L, a=a, q=q, F=F)

    def solve(self) -> Task2Results:
        """Решение задачи - нахождение реакций и максимального момента"""
        p = self.params

        # Реакции опор (из условий равновесия)
        # ΣMA = 0: RB * L - q * L * L/2 - F * a = 0
        # ΣY = 0: RA + RB - q * L - F = 0
        RB = (p.q * p.L * p.L / 2 + p.F * p.a) / p.L
        RA = p.q * p.L + p.F - RB

        # Поиск максимального момента
        x_max, M_max, max_loc = self._find_max_moment(RA, RB)

        self.results = Task2Results(
            params=p,
            RA=RA,
            RB=RB,
            x_max=x_max,
            M_max=M_max,
            max_loc=max_loc
        )
        return self.results

    def _calc_M(self, x: float, RA: float) -> float:
        """Внутренний расчёт момента (без проверки results)"""
        p = self.params
        if x <= p.a:
            return RA * x - p.q * x**2 / 2
        else:
            return RA * x - p.q * x**2 / 2 - p.F * (x - p.a)

    def _find_max_moment(self, RA: float, RB: float) -> Tuple[float, float, str]:
        """Поиск координаты и значения максимального момента"""
        p = self.params

        # Кандидаты на экстремум:
        # 1. Точка где Q(x) = 0 на первом участке: x1 = RA/q
        # 2. Точка где Q(x) = 0 на втором участке: x2 = (RA - F)/q
        # 3. Граничные точки: 0, a, L
        x1 = RA / p.q
        x2 = (RA - p.F) / p.q

        candidates = set()
        for x in [x1, x2, p.a, 0, p.L]:
            if 0 <= x <= p.L:
                candidates.add(round(x, 12))

        candidates = sorted(candidates)

        # Вычисляем моменты во всех кандидатах (используем внутренний метод)
        moments = [self._calc_M(x, RA) for x in candidates]

        # Находим максимум по абсолютному значению
        idx = max(range(len(candidates)), key=lambda i: abs(moments[i]))
        x_max = candidates[idx]
        M_max = moments[idx]

        # Определяем расположение максимума
        eps = 1e-6
        if abs(x_max - p.a) < eps:
            loc = "граница"
        elif x_max < p.a:
            loc = "1 участок"
        else:
            loc = "2 участок"

        return x_max, M_max, loc

    def Q(self, x: float) -> float:
        """
        Поперечная сила Q(x).

        Участок 1 (0 ≤ x ≤ a): Q = RA - q*x
        Участок 2 (a < x ≤ L): Q = RA - q*x - F
        """
        p = self.params
        if not self.results:
            self.solve()
        RA = self.results.RA

        if x <= p.a:
            return RA - p.q * x
        else:
            return RA - p.q * x - p.F

    def M(self, x: float) -> float:
        """
        Изгибающий момент M(x).

        Участок 1 (0 ≤ x ≤ a): M = RA*x - q*x²/2
        Участок 2 (a < x ≤ L): M = RA*x - q*x²/2 - F*(x-a)
        """
        p = self.params
        if not self.results:
            self.solve()
        RA = self.results.RA

        if x <= p.a:
            return RA * x - p.q * x**2 / 2
        else:
            return RA * x - p.q * x**2 / 2 - p.F * (x - p.a)

    def get_Q_data(self, num_points: int = 200) -> Tuple[np.ndarray, np.ndarray]:
        """Получить данные для эпюры Q(x)"""
        p = self.params
        if not self.results:
            self.solve()

        # Разбиваем на два участка для корректного отображения скачка
        x1 = np.linspace(0, p.a, num_points // 2)
        x2 = np.linspace(p.a, p.L, num_points // 2)

        Q1 = np.array([self.Q(x) for x in x1])
        Q2 = np.array([self.Q(x) for x in x2])

        # Добавляем точку скачка
        x = np.concatenate([x1, [p.a], x2])
        Q = np.concatenate([Q1, [self.Q(p.a - 1e-9)], Q2])

        return x, Q

    def get_M_data(self, num_points: int = 200) -> Tuple[np.ndarray, np.ndarray]:
        """Получить данные для эпюры M(x)"""
        p = self.params
        if not self.results:
            self.solve()

        x1 = np.linspace(0, p.a, num_points // 2)
        x2 = np.linspace(p.a, p.L, num_points // 2)

        M1 = np.array([self.M(x) for x in x1])
        M2 = np.array([self.M(x) for x in x2])

        x = np.concatenate([x1, x2])
        M = np.concatenate([M1, M2])

        return x, M

    def get_key_points_Q(self) -> List[Tuple[float, float, str]]:
        """Получить ключевые точки для подписей на эпюре Q"""
        p = self.params
        if not self.results:
            self.solve()

        points = []
        # Начало (x=0)
        Q0 = self.Q(0)
        points.append((0, Q0, f"{Q0:.2f}"))

        # Перед силой F
        Q_a_left = self.Q(p.a - 1e-9)
        points.append((p.a, Q_a_left, f"{Q_a_left:.2f}"))

        # После силы F
        Q_a_right = self.Q(p.a + 1e-9)
        points.append((p.a, Q_a_right, f"{Q_a_right:.2f}"))

        # Конец (x=L)
        Q_L = self.Q(p.L)
        points.append((p.L, Q_L, f"{Q_L:.2f}"))

        return points

    def get_key_points_M(self) -> List[Tuple[float, float, str]]:
        """Получить ключевые точки для подписей на эпюре M"""
        p = self.params
        if not self.results:
            self.solve()

        points = []

        # Максимум
        x_max = self.results.x_max
        M_max = self.results.M_max
        points.append((x_max, M_max, f"{M_max:.2f}"))

        # В точке приложения силы (если не совпадает с максимумом)
        if abs(x_max - p.a) > 0.01:
            M_a = self.M(p.a)
            points.append((p.a, M_a, f"{M_a:.2f}"))

        return points
