import unittest
import random
import test_oracle as independent
from transport import Problem, Builder, State, initial, solve
from lesson import Lesson
from presets import PRESETS

class TransportTests(unittest.TestCase):
    def test_manual_optima(self):
        for problem, expected in zip(list(PRESETS.values())[:5], [1370,830,1620,1240,830]):
            with self.subTest(expected=expected):
                result = solve(problem)
                result.validate()
                self.assertEqual(result.cost, expected)
                self.assertFalse(result.improving())

    def test_zero_theta_changes_basis_without_changing_flow(self):
        p = Problem(((0,0,10),(0,5,0)), (5,5), (5,0,5))
        s = State(p, ((5,0,0),(0,0,5)), frozenset({(0,0),(0,1),(1,1),(1,2)}))
        s.validate()
        self.assertEqual(s.entering_candidates(), [(1,0)])
        self.assertEqual(s.theta((1,0)), 0)
        new, leaving = s.pivot((1,0))
        self.assertEqual(leaving, (1,1))
        self.assertEqual(new.plan, s.plan)
        self.assertNotEqual(new.basis, s.basis)
        self.assertTrue(new.bland)
        self.assertFalse(new.improving())

    def test_large_costs_and_large_integers(self):
        p = Problem(((1000,200),(300,9000)), (10**12,10**12), (10**12,10**12))
        self.assertEqual(solve(p).cost, 500*10**12)

    def test_zero_total_and_single_dimension(self):
        for p in [Problem(((100,),),(0,),(0,)), Problem(((2,3,4),),(6,),(1,2,3)),
                  Problem(((2,),(3,),(4,)),(1,2,3),(6,)),
                  Problem(((1,2),(3,4)),(0,0),(0,0))]:
            result = solve(p)
            result.validate()
            self.assertFalse(result.improving())

    def test_wrong_answers_and_shifted_potentials(self):
        p = Problem(((1,2),(3,4)), (5,5), (5,5))
        lesson=Lesson(p)
        lesson.selected={(0,1)}
        self.assertFalse(lesson.check()[0])
        self.assertEqual(lesson.builder.plan, [[0,0],[0,0]])
        self.assertEqual(lesson.errors,1)
        while lesson.phase=='cell':
            lesson.selected={lesson.builder.candidates[0]}
            self.assertTrue(lesson.check()[0])
            self.assertFalse(lesson.check(-1)[0])
            self.assertTrue(lesson.check(lesson.builder.amount(lesson.entering))[0])
        self.assertEqual(lesson.phase,'basis')
        lesson.check()
        u,v=lesson.state.potentials()
        self.assertTrue(lesson.check(([x+7 for x in u],[x+7 for x in v]))[0])

    def test_full_lesson(self):
        lesson=Lesson(next(iter(PRESETS.values())))
        steps=0
        while lesson.phase!='done':
            phase=lesson.phase
            answer=None
            if phase=='cell': lesson.selected={lesson.builder.candidates[0]}
            elif phase=='amount': answer=lesson.builder.amount(lesson.entering)
            elif phase=='potentials': answer=lesson.state.potentials()
            elif phase=='optimal': answer=not lesson.state.improving()
            elif phase=='enter': lesson.selected={lesson.state.entering_candidates()[0]}
            elif phase=='cycle': lesson.selected=set(lesson.state.cycle(lesson.entering))-{lesson.entering}
            elif phase=='theta': answer=lesson.state.theta(lesson.entering)
            accepted, text=lesson.check(answer)
            self.assertTrue(accepted,text)
            steps+=1
            self.assertLess(steps,200)
        self.assertEqual(lesson.state.cost,1370)
        self.assertEqual(lesson.errors,0)

    def test_random_problems_against_independent_min_cost_flow(self):
        rng=random.Random(20261102)
        for trial in range(400):
            m,n=rng.randint(1,5),rng.randint(1,5)
            p=Problem(tuple(tuple(rng.randrange(0,201) for _ in range(n)) for _ in range(m)),
                      tuple(rng.randrange(0,15) for _ in range(m)),tuple(rng.randrange(0,15) for _ in range(n))).balanced()
            result=solve(p,limit=1000)
            reference=independent.solve(list(p.supply),list(p.demand),[list(row) for row in p.costs])
            with self.subTest(trial=trial):
                self.assertEqual(result.cost,reference['objective'])
                result.validate()

    def test_reject_invalid_problem(self):
        for args in [(((1,),),(-1,),(1,)), (((1,2),),(1,),(1,)), (((1.5,),),(1,),(1,))]:
            with self.assertRaises(ValueError): Problem(*args)


if __name__=='__main__': unittest.main()
