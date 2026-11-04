"""Tk widget construction/rendering checks, without mouse/keyboard injection."""
import unittest
import tkinter as tk
from app import App
from lesson import Lesson
from presets import PRESETS


class RenderingTests(unittest.TestCase):
    def test_all_lesson_screens(self):
        root=tk.Tk();root.withdraw()
        try:
            app=App(root)
            app.start()
            self.assertIsNone(app.lesson)
            app.check_balance()
            app.add_dummy()
            app.demand_entries[-1].insert(0,'89')
            app.start()
            self.assertIsNone(app.lesson)
            app.demand_entries[-1].delete(0,'end')
            app.demand_entries[-1].insert(0,'90')
            app.start()
            self.assertIsNotNone(app.lesson)
            visited=set()
            for problem in [next(iter(PRESETS.values())), list(PRESETS.values())[-1]]:
                app.lesson=Lesson(problem.balanced())
                app.show_lesson()
                while True:
                    root.update_idletasks()
                    phase=app.lesson.phase;visited.add(phase)
                    self.assertTrue(app.matrix.canvas.find_all())
                    texts=[app.matrix.canvas.itemcget(item,'text')
                           for item in app.matrix.canvas.find_all()
                           if app.matrix.canvas.type(item)=='text']
                    shown=[text for text in texts if text.startswith(('u = ', 'v = '))]
                    expected=[]
                    if app.lesson.accepted_potentials is not None:
                        u,v=app.lesson.accepted_potentials
                        expected=[f'u = {value}' for value in u]+[f'v = {value}' for value in v]
                    self.assertCountEqual(shown,expected)
                    if phase=='done':break
                    answer=None;l=app.lesson
                    if phase=='cell':l.selected={l.builder.candidates[0]}
                    elif phase=='amount':answer=l.builder.amount(l.entering)
                    elif phase=='potentials':answer=l.state.potentials()
                    elif phase=='optimal':answer=not l.state.improving()
                    elif phase=='enter':l.selected={l.state.entering_candidates()[0]}
                    elif phase=='cycle':l.selected=set(l.state.cycle(l.entering))-{l.entering}
                    elif phase=='theta':answer=l.state.theta(l.entering)
                    self.assertTrue(l.check(answer)[0])
                    app.refresh()
            self.assertEqual(visited,{'cell','amount','basis','potentials','optimal','enter','cycle','theta','pivot','done'})
        finally:root.destroy()


if __name__=='__main__':unittest.main()
