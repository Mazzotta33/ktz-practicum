"""Exact integer transportation simplex; basis membership is independent of flow."""
from dataclasses import dataclass
from collections import deque

Cell = tuple[int, int]


@dataclass(frozen=True)
class Problem:
    costs: tuple[tuple[int, ...], ...]
    supply: tuple[int, ...]
    demand: tuple[int, ...]
    dummy_row: bool = False
    dummy_col: bool = False

    def __post_init__(self):
        m, n = len(self.supply), len(self.demand)
        if not (1 <= m <= 31 and 1 <= n <= 31):
            raise ValueError('Допустимо от 1 до 30 строк и столбцов (+ фиктивная вершина).')
        if len(self.costs) != m or any(len(row) != n for row in self.costs):
            raise ValueError('Размеры матрицы и векторов не совпадают.')
        values = [*self.supply, *self.demand, *(x for row in self.costs for x in row)]
        if any(type(x) is not int or x < 0 for x in values):
            raise ValueError('Введите неотрицательные целые числа.')

    @property
    def m(self): return len(self.supply)

    @property
    def n(self): return len(self.demand)

    def balanced(self):
        diff = sum(self.supply) - sum(self.demand)
        if diff > 0:
            return Problem(tuple(row + (0,) for row in self.costs), self.supply,
                           self.demand + (diff,), self.dummy_row, True)
        if diff < 0:
            return Problem(self.costs + ((0,) * self.n,), self.supply + (-diff,),
                           self.demand, True, self.dummy_col)
        return self


class Builder:
    """Least-cost allocation; ties are allowed and selected by the student."""
    def __init__(self, problem):
        self.problem = problem
        if sum(problem.supply) != sum(problem.demand):
            raise ValueError('Сначала сбалансируйте задачу.')
        self.a, self.b = list(problem.supply), list(problem.demand)
        self.plan = [[0] * problem.n for _ in range(problem.m)]
        self.basis = set()

    @property
    def candidates(self):
        cells = [(i, j) for i in range(self.problem.m) for j in range(self.problem.n)
                 if self.a[i] > 0 and self.b[j] > 0]
        if not cells: return []
        minimum = min(self.problem.costs[i][j] for i, j in cells)
        return [cell for cell in cells if self.problem.costs[cell[0]][cell[1]] == minimum]

    def amount(self, cell):
        i, j = cell
        return min(self.a[i], self.b[j])

    def allocate(self, cell, value):
        if cell not in self.candidates:
            raise ValueError('Выберите клетку с минимальным тарифом среди оставшихся строк и столбцов.')
        if value != self.amount(cell):
            raise ValueError('Объём равен минимуму оставшегося запаса и спроса.')
        i, j = cell
        self.plan[i][j] += value
        self.basis.add(cell)
        self.a[i] -= value
        self.b[j] -= value

    def finish(self):
        if self.candidates:
            raise ValueError('Начальный план ещё не достроен.')
        # Positive allocations form a forest. Complete it to a spanning tree
        # without inventing epsilon shipments or introducing cycles.
        p = self.problem
        parent = list(range(p.m + p.n))
        def root(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        def join(i, j):
            a, b = root(i), root(p.m + j)
            if a == b: return False
            parent[a] = b
            return True
        basis = set(self.basis)
        for i, j in sorted(basis):
            if not join(i, j): raise ValueError('Базис содержит цикл.')
        added = []
        for i in range(p.m):
            for j in range(p.n):
                if join(i, j):
                    basis.add((i, j))
                    added.append((i, j))
        state = State(p, tuple(tuple(row) for row in self.plan), frozenset(basis))
        state.validate()
        return state, added


@dataclass(frozen=True)
class State:
    problem: Problem
    plan: tuple[tuple[int, ...], ...]
    basis: frozenset[Cell]
    iteration: int = 0
    bland: bool = False

    @property
    def cost(self):
        return sum(self.plan[i][j] * self.problem.costs[i][j]
                   for i in range(self.problem.m) for j in range(self.problem.n))

    @property
    def degenerate(self):
        return any(self.plan[i][j] == 0 for i, j in self.basis)

    def potentials(self):
        p = self.problem
        u, v = [None] * p.m, [None] * p.n
        u[0] = 0
        q = deque([(0, 0)])
        while q:
            side, index = q.popleft()
            for i, j in sorted(self.basis):
                if side == 0 and i == index and v[j] is None:
                    v[j] = p.costs[i][j] + u[i]
                    q.append((1, j))
                if side == 1 and j == index and u[i] is None:
                    u[i] = v[j] - p.costs[i][j]
                    q.append((0, i))
        if None in u or None in v:
            raise ValueError('Базис несвязен.')
        return u, v

    def deltas(self):
        u, v = self.potentials()
        return tuple(tuple(v[j] - u[i] - self.problem.costs[i][j]
                           for j in range(self.problem.n)) for i in range(self.problem.m))

    def improving(self):
        d = self.deltas()
        return [(i, j) for i in range(self.problem.m) for j in range(self.problem.n)
                if (i, j) not in self.basis and d[i][j] > 0]

    @property
    def uses_bland(self): return self.bland or self.degenerate

    def entering_candidates(self):
        cells = self.improving()
        if not cells: return []
        if self.uses_bland: return [min(cells)]
        d = self.deltas()
        maximum = max(d[i][j] for i, j in cells)
        return [cell for cell in cells if d[cell[0]][cell[1]] == maximum]

    def cycle(self, entering):
        if entering in self.basis:
            raise ValueError('Входящая клетка должна быть небазисной.')
        p = self.problem
        start, end = entering[0], p.m + entering[1]
        graph = [[] for _ in range(p.m + p.n)]
        for i, j in sorted(self.basis):
            graph[i].append((p.m + j, (i, j)))
            graph[p.m + j].append((i, (i, j)))
        previous = {start: None}
        q = deque([start])
        while q and end not in previous:
            node = q.popleft()
            for neighbor, cell in graph[node]:
                if neighbor not in previous:
                    previous[neighbor] = (node, cell)
                    q.append(neighbor)
        if end not in previous: raise ValueError('Не найден путь по базису.')
        path, node = [], end
        while node != start:
            node, cell = previous[node]
            path.append(cell)
        return [entering] + path

    def theta(self, entering):
        return min(self.plan[i][j] for i, j in self.cycle(entering)[1::2])

    def pivot(self, entering):
        if entering not in self.entering_candidates():
            raise ValueError('Клетка не соответствует текущему правилу выбора.')
        cycle = self.cycle(entering)
        theta = self.theta(entering)
        leaving = min(cell for cell in cycle[1::2] if self.plan[cell[0]][cell[1]] == theta)
        plan = [list(row) for row in self.plan]
        for k, (i, j) in enumerate(cycle):
            plan[i][j] += theta if k % 2 == 0 else -theta
        basis = (self.basis | {entering}) - {leaving}
        new = State(self.problem, tuple(tuple(row) for row in plan), frozenset(basis),
                    self.iteration + 1, self.uses_bland or theta == 0)
        new.validate()
        return new, leaving

    def validate(self):
        p = self.problem
        if len(self.plan) != p.m or any(len(row) != p.n for row in self.plan):
            raise ValueError('Некорректный размер плана.')
        if len(self.basis) != p.m + p.n - 1:
            raise ValueError('Базис должен содержать m+n−1 клеток.')
        if any(not (0 <= i < p.m and 0 <= j < p.n) for i, j in self.basis):
            raise ValueError('Клетка базиса за пределами матрицы.')
        if any(type(x) is not int or x < 0 for row in self.plan for x in row):
            raise ValueError('Перевозки должны быть неотрицательными целыми.')
        if any(self.plan[i][j] and (i, j) not in self.basis
               for i in range(p.m) for j in range(p.n)):
            raise ValueError('Положительная перевозка вне базиса.')
        if tuple(map(sum, self.plan)) != p.supply:
            raise ValueError('Нарушен баланс запасов.')
        if tuple(sum(self.plan[i][j] for i in range(p.m)) for j in range(p.n)) != p.demand:
            raise ValueError('Нарушен баланс спроса.')
        u, v = self.potentials()
        if any(v[j] - u[i] != p.costs[i][j] for i, j in self.basis):
            raise ValueError('Базис содержит зависимые клетки.')


def initial(problem):
    builder = Builder(problem.balanced())
    while builder.candidates:
        cell = builder.candidates[0]
        builder.allocate(cell, builder.amount(cell))
    return builder.finish()[0]


def solve(problem, limit=10000):
    state = initial(problem)
    seen = set()
    while state.improving():
        if state.basis in seen:
            raise RuntimeError('Повтор базиса: нарушена защита от циклов.')
        if state.iteration >= limit:
            raise RuntimeError('Превышен лимит итераций.')
        seen.add(state.basis)
        state, _ = state.pivot(state.entering_candidates()[0])
    return state
