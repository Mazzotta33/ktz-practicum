"""Teaching state machine. Wrong answers never mutate the mathematical plan."""
from transport import Builder


class Lesson:
    def __init__(self, problem):
        problem.validate_balance()
        self.original = problem
        self.problem = problem
        self.accepted_potentials = None
        self.builder = Builder(self.problem)
        self.state = None
        self.phase = 'cell'
        self.selected = set()
        self.entering = None
        self.errors = 0
        self.history = []
        self.seen = set()
        self.added = []
        self._complete_initial()

    def _complete_initial(self):
        if not self.builder.candidates:
            self.state, self.added = self.builder.finish()
            self.phase = 'basis'
            if self.added:
                self.history.append('Дополнение базиса нулевыми клетками: ' + self.cells_text(self.added))

    @staticmethod
    def cells_text(cells):
        return ', '.join(f'({i+1}, {j+1})' for i, j in sorted(cell for cell in cells if cell is not None))

    def check(self, answer=None):
        """Returns (accepted, feedback); only accepted answers advance the lesson."""
        previous_phase = self.phase
        try:
            self._answer(answer)
        except (ValueError, TypeError):
            self.errors += 1
            return False, 'Ошибка ответа.'
        self.selected.clear()
        self.history.append({'amount': 'Объём принят.', 'basis': 'Начальный план принят.',
                             'potentials': 'Потенциалы приняты.', 'optimal': 'Действие принято.',
                             'enter': 'Клетка принята.', 'cycle': 'Цикл принят.',
                             'theta': 'Значение принято.', 'pivot': 'Переход выполнен.'}.get(previous_phase, 'Клетка принята.'))
        return True, ''

    def _answer(self, answer):
        p = self.problem
        if self.phase == 'cell':
            if len(self.selected) != 1: raise ValueError('Выберите одну клетку в рабочей таблице.')
            cell = next(iter(self.selected))
            if cell not in self.builder.candidates:
                raise ValueError('Нужен минимальный тариф среди строк с запасом и столбцов со спросом.')
            self.entering = cell
            self.phase = 'amount'
            return
        if self.phase == 'amount':
            if type(answer) is not int: raise ValueError('Введите целый объём перевозки.')
            self.builder.allocate(self.entering, answer)
            self.phase = 'cell'
            self._complete_initial()
            return
        if self.phase == 'basis':
            self.phase = 'potentials'
            return
        if self.phase == 'potentials':
            u, v = answer
            if len(u) != p.m or len(v) != p.n:
                raise ValueError(f'Нужно {p.m} значений u и {p.n} значений v.')
            if any(type(x) is not int for x in u+v): raise ValueError('Потенциалы должны быть целыми.')
            if any(v[j]-u[i] != p.costs[i][j] for i,j in self.state.basis):
                raise ValueError('Для каждой базисной клетки должно выполняться v[j] − u[i] = c[i,j]. Проверьте также клетки 0*.')
            self.accepted_potentials = (tuple(u), tuple(v))
            self.phase = 'optimal'
            return
        if self.phase == 'optimal':
            correct = not self.state.improving()
            if answer is not correct:
                raise ValueError('План оптимален, если положительных оценок нет. Сравнивайте δ с нулём.')
            self.phase = 'done' if correct else 'enter'
            return
        if self.phase == 'enter':
            if len(self.selected) != 1: raise ValueError('Выберите одну небазисную клетку.')
            cell = next(iter(self.selected))
            if cell not in self.state.entering_candidates():
                rule = 'первую по номеру строке, затем столбцу, с δ > 0 (правило Бланда)' if self.state.uses_bland else 'клетку с максимальной положительной δ'
                raise ValueError('Выберите ' + rule + '.')
            self.entering = cell
            self.phase = 'cycle'
            return
        if self.phase == 'cycle':
            expected = set(self.state.cycle(self.entering)) - {self.entering}
            if self.selected != expected:
                raise ValueError('Отметьте все остальные вершины замкнутого цикла по базису. Не отмечайте входящую клетку повторно.')
            self.phase = 'theta'
            return
        if self.phase == 'theta':
            if type(answer) is not int or answer != self.state.theta(self.entering):
                raise ValueError('θ — минимум объёмов в минусовых клетках. Нулевая базисная клетка может дать θ = 0.')
            self.phase = 'pivot'
            return
        if self.phase == 'pivot':
            if self.state.basis in self.seen:
                raise ValueError('Повтор базиса: остановлено для предотвращения цикла. Начните новую задачу.')
            if self.state.iteration >= 10000:
                raise ValueError('Достигнут лимит итераций. Начните новую задачу.')
            new, leaving = self.state.pivot(self.entering)
            self.seen.add(self.state.basis)
            self.state = new
            self.accepted_potentials = None
            self.phase = 'potentials'
            return
        raise ValueError('Решение уже завершено.')
