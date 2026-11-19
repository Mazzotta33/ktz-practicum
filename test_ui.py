"""Tk widget construction/rendering checks, without mouse/keyboard injection."""
import unittest
import tkinter as tk
import tempfile
from pathlib import Path
from types import SimpleNamespace
from app import App
from lesson import Lesson
from presets import PRESETS
from variant_files import load_variant, save_variant
from transport import Problem


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
                    self.assertNotIn('План оптимален?',texts)
                    if phase=='potentials':
                        entries=app.matrix.potential_entries
                        self.assertEqual(len(entries),app.lesson.problem.m+app.lesson.problem.n)
                        for e in entries:e.insert(0,'999')
                        app.check()
                        self.assertEqual(app.lesson.phase,'potentials')
                        self.assertEqual(app.feedback,'Ошибка ответа.')
                        app.zoom.set(50);app.change_zoom()
                        self.assertTrue(all(e.get()=='999' for e in app.matrix.potential_entries))
                        app.zoom.set(150);app.change_zoom()
                        u,v=app.lesson.state.potentials()
                        for e,value in zip(app.matrix.potential_entries,u+v):
                            e.delete(0,'end');e.insert(0,str(value))
                        app.check()
                        self.assertEqual(app.lesson.phase,'optimal')
                        app.zoom.set(100);app.change_zoom()
                        continue
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

    def test_manual_balance_and_scaled_selection(self):
        root=tk.Tk();root.withdraw()
        try:
            app=App(root)
            app.edit_problem(Problem(((1,),),(2,),(5,)))
            app.check_balance()
            self.assertEqual(app.setup_note.cget('text'),'Ошибка баланса или исходных данных.')
            app.add_dummy('col')  # Student may choose the wrong side; no automatic correction.
            app.demand_entries[-1].insert(0,'3')
            app.start();self.assertIsNone(app.lesson)
            app.edit_problem(Problem(((1,),),(2,),(5,)))
            app.add_dummy('row')
            self.assertEqual(app.supply_entries[-1].get(),'')
            self.assertEqual(app.setup_note.cget('text'),'')
            app.supply_entries[-1].insert(0,'3')
            app.start();self.assertIsNotNone(app.lesson)
            for zoom in (50,100,150):
                app.zoom.set(zoom);app.change_zoom()
                m=app.matrix
                m.canvas.xview_moveto(0);m.canvas.yview_moveto(0)
                m._click(SimpleNamespace(x=1.5*m.W,y=1.5*m.H))
                self.assertEqual(app.lesson.selected,{(0,0)})
        finally:root.destroy()

    def test_variant_files(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'вариант.json'
            for problem in PRESETS.values():
                save_variant(path,problem)
                self.assertEqual(load_variant(path),problem)
            path.write_text('{"costs": [[-1]], "supply": [5], "demand": [5]}',encoding='utf-8')
            with self.assertRaises(ValueError):load_variant(path)


if __name__=='__main__':unittest.main()
