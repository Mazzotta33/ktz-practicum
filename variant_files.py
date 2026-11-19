"""Portable, editable JSON variants; no executable code is loaded."""
import json
from pathlib import Path
from transport import Problem


def load_variant(path):
    data = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if not isinstance(data, dict):
        raise ValueError('Неверный формат варианта.')
    problem = Problem(tuple(tuple(row) for row in data['costs']),
                      tuple(data['supply']), tuple(data['demand']),
                      data.get('dummy_row', False), data.get('dummy_col', False))
    if problem.m > 30 + int(problem.dummy_row) or problem.n > 30 + int(problem.dummy_col):
        raise ValueError('Недопустимая размерность варианта.')
    if any(x > 10**12 for x in (*problem.supply, *problem.demand,
                               *(x for row in problem.costs for x in row))):
        raise ValueError('Слишком большие значения в варианте.')
    if type(problem.dummy_row) is not bool or type(problem.dummy_col) is not bool:
        raise ValueError('Неверный признак фиктивной вершины.')
    if problem.dummy_row and problem.dummy_col:
        raise ValueError('В варианте две фиктивные вершины.')
    return problem


def save_variant(path, problem):
    data = dict(costs=problem.costs, supply=problem.supply, demand=problem.demand,
                dummy_row=problem.dummy_row, dummy_col=problem.dummy_col)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
