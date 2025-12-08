"""
Задача 3: Продольная сила. Эпюры N(x), σ(x) и деформация

Схема:
- Прямолинейный стержень длины L
- Слева жёсткая заделка (опора A)
- Правый конец свободен
- Три участка с площадями A1, A2, A3
- Три осевые силы F1 (вправо), F2 (влево), F3 (вправо)

Требуется:
- Определить реакцию RA
- Построить эпюры N(x), σ(x), Δl(x)
- Определить полное удлинение Δl(L)
- Если Δl(x) пересекает ноль - найти x0
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple, List, Optional


@dataclass
class Task3Params:
    """Параметры задачи 3"""
    N: int          # Номер варианта
    R: int          # Индекс R
    K: int          # Индекс K
    S: int          # Индекс S
    L: float        # Полная длина, м
    L1: float       # Длина участка 1, м
    L2: float       # Длина участка 2, м
    L3: float       # Длина участка 3, м
    A1: float       # Площадь участка 1, см²
    A2: float       # Площадь участка 2, см²
    A3: float       # Площадь участка 3, см²
    E: float        # Модуль упругости, ГПа
    F1: float       # Сила 1 (вправо), кН
    F2: float       # Сила 2 (влево), кН
    F3: float       # Сила 3 (вправо), кН


@dataclass
class Task3Results:
    """Результаты расчёта задачи 3"""
    params: Task3Params
    RA: float           # Реакция в заделке, кН
    N1: float           # Продольная сила на участке 1, кН
    N2: float           # Продольная сила на участке 2, кН
    N3: float           # Продольная сила на участке 3, кН
    sigma1: float       # Напряжение на участке 1, МПа
    sigma2: float       # Напряжение на участке 2, МПа
    sigma3: float       # Напряжение на участке 3, МПа
    delta_l_total: float  # Полное удлинение, мм
    x0: Optional[float]   # Точка пересечения Δl(x) с нулём, м


class Task3Solver:
    """Решатель задачи 3 - ступенчатый стержень"""

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
        self._k1 = None  # Коэффициент деформации участка 1
        self._k2 = None  # Коэффициент деформации участка 2
        self._k3 = None  # Коэффициент деформации участка 3
        self._dl1 = None  # Удлинение в конце участка 1
        self._dl2 = None  # Удлинение в конце участка 2
        self._dl3 = None  # Удлинение в конце участка 3

    def _calculate_params(self) -> Task3Params:
        """Вычисление параметров по номеру варианта"""
        N = self.N

        # Индексы
        R = 1 + ((N - 1) % 7)
        K = 1 + ((N - 1) // 7)
        S = 1 + ((N - 1) % 5)

        # Геометрия
        L = 1.60 + 0.04 * (K - 1) + 0.02 * (R - 1)
        L1 = 0.30 * L
        L2 = 0.40 * L
        L3 = 0.30 * L

        # Площади сечений
        A1 = 4 + S
        A2 = 5 + R
        A3 = 6 + K

        # Модуль упругости
        E = 190 + 2 * K

        # Силы
        F1 = 18 + R + K
        F2 = 11 + S + K
        F3 = 7 + R

        return Task3Params(
            N=N, R=R, K=K, S=S,
            L=L, L1=L1, L2=L2, L3=L3,
            A1=A1, A2=A2, A3=A3,
            E=E, F1=F1, F2=F2, F3=F3
        )

    def solve(self) -> Task3Results:
        """Решение задачи"""
        p = self.params

        # Реакция в заделке (из условия равновесия ΣX = 0)
        # RA + F1 - F2 + F3 = 0 (если RA направлена вправо)
        # RA = -F1 + F2 - F3
        RA = -p.F1 + p.F2 - p.F3

        # Продольные силы на участках (метод сечений, идём справа)
        # Участок 3: N3 = F3 (справа только F3)
        # Участок 2: N3 = F3 - F2 (справа F3 и F2)
        # Участок 1: N1 = F3 - F2 + F1 = -RA
        N3 = p.F3
        N2 = p.F3 - p.F2
        N1 = p.F3 - p.F2 + p.F1  # = -RA

        # Напряжения σ = N / A (кН/см² -> МПа: умножаем на 10)
        # N в кН, A в см², σ в МПа
        # 1 кН/см² = 10 МПа
        sigma1 = N1 / p.A1 * 10  # МПа
        sigma2 = N2 / p.A2 * 10  # МПа
        sigma3 = N3 / p.A3 * 10  # МПа

        # Деформации Δl = N * L / (E * A)
        # N в кН, L в м, E в ГПа, A в см²
        # Нужно привести к мм
        # k = N / (E * A) - коэффициент (безразмерный при правильных единицах)
        # Δl = k * L * 1000 (мм)

        # Коэффициент: [кН] / ([ГПа] * [см²])
        # = [кН] / ([10^9 Па] * [10^-4 м²])
        # = [кН] / ([10^5 кН/м²])
        # = [10^-5 м] = [0.01 мм]
        # Поэтому k = 10 * N / (E * A) даёт мм/м

        self._k1 = 10 * N1 / (p.E * p.A1)  # мм/м
        self._k2 = 10 * N2 / (p.E * p.A2)  # мм/м
        self._k3 = 10 * N3 / (p.E * p.A3)  # мм/м

        # Удлинения на границах участков
        self._dl1 = self._k1 * p.L1  # мм
        self._dl2 = self._dl1 + self._k2 * p.L2  # мм
        self._dl3 = self._dl2 + self._k3 * p.L3  # мм

        # Поиск точки пересечения Δl(x) = 0
        x0 = self._find_zero_crossing()

        self.results = Task3Results(
            params=p,
            RA=RA,
            N1=N1, N2=N2, N3=N3,
            sigma1=sigma1, sigma2=sigma2, sigma3=sigma3,
            delta_l_total=self._dl3,
            x0=x0
        )
        return self.results

    def _find_zero_crossing(self) -> Optional[float]:
        """Поиск точки пересечения эпюры Δl(x) с нулём"""
        p = self.params

        # Проверяем переход через ноль между участками
        # Участок 2: если dl1 и dl2 имеют разные знаки
        if self._dl1 * self._dl2 < 0 and self._k2 != 0:
            # Δl(x) = dl1 + k2 * (x - L1) = 0
            # x = L1 - dl1/k2
            return p.L1 + (-self._dl1) / self._k2

        # Участок 3: если dl2 и dl3 имеют разные знаки
        if self._dl2 * self._dl3 < 0 and self._k3 != 0:
            # Δl(x) = dl2 + k3 * (x - L1 - L2) = 0
            return p.L1 + p.L2 + (-self._dl2) / self._k3

        return None

    def N(self, x: float) -> float:
        """Продольная сила N(x)"""
        if not self.results:
            self.solve()
        p = self.params
        r = self.results

        if x <= p.L1:
            return r.N1
        elif x <= p.L1 + p.L2:
            return r.N2
        else:
            return r.N3

    def sigma(self, x: float) -> float:
        """Напряжение σ(x) в МПа"""
        if not self.results:
            self.solve()
        p = self.params
        r = self.results

        if x <= p.L1:
            return r.sigma1
        elif x <= p.L1 + p.L2:
            return r.sigma2
        else:
            return r.sigma3

    def delta_l(self, x: float) -> float:
        """Абсолютное удлинение Δl(x) в мм"""
        if not self.results:
            self.solve()
        p = self.params

        if x <= p.L1:
            return self._k1 * x
        elif x <= p.L1 + p.L2:
            return self._dl1 + self._k2 * (x - p.L1)
        else:
            return self._dl2 + self._k3 * (x - p.L1 - p.L2)

    def get_N_data(self) -> Tuple[List[float], List[float]]:
        """Получить данные для эпюры N(x) - ступенчатая функция"""
        if not self.results:
            self.solve()
        p = self.params
        r = self.results

        # Для ступенчатой эпюры нужны точки на границах
        x = [0, p.L1, p.L1, p.L1 + p.L2, p.L1 + p.L2, p.L]
        N = [r.N1, r.N1, r.N2, r.N2, r.N3, r.N3]

        return x, N

    def get_sigma_data(self) -> Tuple[List[float], List[float]]:
        """Получить данные для эпюры σ(x) - ступенчатая функция"""
        if not self.results:
            self.solve()
        p = self.params
        r = self.results

        x = [0, p.L1, p.L1, p.L1 + p.L2, p.L1 + p.L2, p.L]
        sigma = [r.sigma1, r.sigma1, r.sigma2, r.sigma2, r.sigma3, r.sigma3]

        return x, sigma

    def get_delta_l_data(self, num_points: int = 100) -> Tuple[np.ndarray, np.ndarray]:
        """Получить данные для эпюры Δl(x) - кусочно-линейная функция"""
        if not self.results:
            self.solve()
        p = self.params

        # Точки на границах участков + промежуточные
        x1 = np.linspace(0, p.L1, num_points // 3)
        x2 = np.linspace(p.L1, p.L1 + p.L2, num_points // 3)
        x3 = np.linspace(p.L1 + p.L2, p.L, num_points // 3)

        dl1 = np.array([self.delta_l(x) for x in x1])
        dl2 = np.array([self.delta_l(x) for x in x2])
        dl3 = np.array([self.delta_l(x) for x in x3])

        x = np.concatenate([x1, x2, x3])
        dl = np.concatenate([dl1, dl2, dl3])

        return x, dl

    def get_key_points_N(self) -> List[Tuple[float, float, str]]:
        """Ключевые точки для подписей на эпюре N"""
        if not self.results:
            self.solve()
        p = self.params
        r = self.results

        return [
            (p.L1 / 2, r.N1, f"{r.N1:.1f}"),
            (p.L1 + p.L2 / 2, r.N2, f"{r.N2:.1f}"),
            (p.L1 + p.L2 + p.L3 / 2, r.N3, f"{r.N3:.1f}"),
        ]

    def get_key_points_sigma(self) -> List[Tuple[float, float, str]]:
        """Ключевые точки для подписей на эпюре σ"""
        if not self.results:
            self.solve()
        p = self.params
        r = self.results

        return [
            (p.L1 / 2, r.sigma1, f"{r.sigma1:.1f}"),
            (p.L1 + p.L2 / 2, r.sigma2, f"{r.sigma2:.1f}"),
            (p.L1 + p.L2 + p.L3 / 2, r.sigma3, f"{r.sigma3:.1f}"),
        ]

    def get_key_points_delta_l(self) -> List[Tuple[float, float, str]]:
        """Ключевые точки для подписей на эпюре Δl"""
        if not self.results:
            self.solve()
        p = self.params

        points = [
            (p.L1, self._dl1, f"{self._dl1:.4f}"),
            (p.L1 + p.L2, self._dl2, f"{self._dl2:.4f}"),
            (p.L, self._dl3, f"{self._dl3:.4f}"),
        ]

        # Добавляем точку пересечения с нулём, если есть
        if self.results.x0 is not None:
            points.append((self.results.x0, 0, f"x₀={self.results.x0:.3f}"))

        return points
