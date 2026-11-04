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
        self.hints = 0
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
        try:
            text = self._answer(answer)
        except (ValueError, TypeError) as error:
            self.errors += 1
            return False, str(error)
        self.selected.clear()
        self.history.append(text)
        return True, text

    def _answer(self, answer):
        p = self.problem
        if self.phase == 'cell':
            if len(self.selected) != 1: raise ValueError('Выберите одну клетку в рабочей таблице.')
            cell = next(iter(self.selected))
            if cell not in self.builder.candidates:
                raise ValueError('Нужен минимальный тариф среди строк с запасом и столбцов со спросом.')
            self.entering = cell
            self.phase = 'amount'
            return f'Верно: выбран минимальный тариф {p.costs[cell[0]][cell[1]]}, клетка {self.cells_text([cell])}.'
        if self.phase == 'amount':
            if type(answer) is not int: raise ValueError('Введите целый объём перевозки.')
            self.builder.allocate(self.entering, answer)
            self.phase = 'cell'
            self._complete_initial()
            return f'Назначено {answer} в клетку {self.cells_text([self.entering])}.'
        if self.phase == 'basis':
            self.phase = 'potentials'
            return ('Базис содержит m+n−1 независимых клеток. 0* — нулевая базисная перевозка; это не пустая клетка.'
                    if self.state.degenerate else 'Начальный невырожденный опорный план построен.')
        if self.phase == 'potentials':
            u, v = answer
            if len(u) != p.m or len(v) != p.n:
                raise ValueError(f'Нужно {p.m} значений u и {p.n} значений v.')
            if any(type(x) is not int for x in u+v): raise ValueError('Потенциалы должны быть целыми.')
            if any(v[j]-u[i] != p.costs[i][j] for i,j in self.state.basis):
                raise ValueError('Для каждой базисной клетки должно выполняться v[j] − u[i] = c[i,j]. Проверьте также клетки 0*.')
            self.accepted_potentials = (tuple(u), tuple(v))
            self.phase = 'optimal'
            return 'Потенциалы верны. Рассчитаны оценки δ = v − u − c. Общий сдвиг потенциалов допустим.'
        if self.phase == 'optimal':
            correct = not self.state.improving()
            if answer is not correct:
                raise ValueError('План оптимален, если положительных оценок нет. Сравнивайте δ с нулём.')
            self.phase = 'done' if correct else 'enter'
            return f'Оптимальный план найден. Минимальная стоимость: {self.state.cost}.' if correct else 'Есть положительные оценки: план можно улучшить.'
        if self.phase == 'enter':
            if len(self.selected) != 1: raise ValueError('Выберите одну небазисную клетку.')
            cell = next(iter(self.selected))
            if cell not in self.state.entering_candidates():
                rule = 'первую по номеру строке, затем столбцу, с δ > 0 (правило Бланда)' if self.state.uses_bland else 'клетку с максимальной положительной δ'
                raise ValueError('Выберите ' + rule + '.')
            self.entering = cell
            self.phase = 'cycle'
            return f'Входящая клетка {self.cells_text([cell])} выбрана верно.'
        if self.phase == 'cycle':
            expected = set(self.state.cycle(self.entering)) - {self.entering}
            if self.selected != expected:
                raise ValueError('Отметьте все остальные вершины замкнутого цикла по базису. Не отмечайте входящую клетку повторно.')
            self.phase = 'theta'
            return 'Цикл верен. Знаки чередуются; входящая клетка имеет знак «+».'
        if self.phase == 'theta':
            if type(answer) is not int or answer != self.state.theta(self.entering):
                raise ValueError('θ — минимум объёмов в минусовых клетках. Нулевая базисная клетка может дать θ = 0.')
            self.phase = 'pivot'
            return f'θ = {answer}. ' + ('Перевозки сохранятся, но одна нулевая клетка покинет базис.' if answer == 0 else 'Прибавьте θ на плюсовых и вычтите на минусовых вершинах.')
        if self.phase == 'pivot':
            if self.state.basis in self.seen:
                raise ValueError('Повтор базиса: остановлено для предотвращения цикла. Начните новую задачу.')
            if self.state.iteration >= 10000:
                raise ValueError('Достигнут лимит итераций. Начните новую задачу.')
            new, leaving = self.state.pivot(self.entering)
            self.seen.add(self.state.basis)
            previous = self.state.cost
            self.state = new
            self.accepted_potentials = None
            self.phase = 'potentials'
            return f'Итерация {new.iteration}: из базиса вышла {self.cells_text([leaving])}. Стоимость: {previous} → {new.cost}.'
        raise ValueError('Решение уже завершено.')

    def hint(self):
        self.hints += 1
        if self.phase == 'cell': return 'Подходящие минимальные тарифы: ' + self.cells_text(self.builder.candidates)
        if self.phase == 'amount': return f'Минимум остатка запаса и спроса: {self.builder.amount(self.entering)}.'
        if self.phase == 'potentials':
            u,v=self.state.potentials()
            return f'При u₁ = 0: u = {u}; v = {v}.'
        if self.phase == 'optimal': return 'Положительных оценок: ' + str(len(self.state.improving()))
        if self.phase == 'enter': return 'Подходящие клетки: ' + self.cells_text(self.state.entering_candidates())
        if self.phase == 'cycle': return 'Цикл: ' + self.cells_text(self.state.cycle(self.entering))
        if self.phase == 'theta': return f'Минимальный минусовой объём: {self.state.theta(self.entering)}.'
        return 'Следуйте инструкции текущего этапа.'
