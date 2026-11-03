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
            visited=set()
            for problem in [next(iter(PRESETS.values())), list(PRESETS.values())[-1]]:
                app.lesson=Lesson(problem)
                app.show_lesson()
                while True:
                    root.update_idletasks()
                    phase=app.lesson.phase;visited.add(phase)
                    self.assertTrue(app.matrix.canvas.find_all())
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
