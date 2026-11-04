"""КТЗ · Практикум. Offline Windows desktop application (Python/Tk)."""
import ctypes
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from transport import Problem
from lesson import Lesson
from presets import PRESETS

BG = '#f3f5f9'
INK = '#17243b'
MUTED = '#66758d'
NAVY = '#12233c'
BLUE = '#315fea'
GREEN = '#087f69'
LINE = '#dce3ee'
FONT = 'Segoe UI'


def label(parent, text='', size=11, color=INK, bold=False, bg='white', **kw):
    return tk.Label(parent, text=text, font=(FONT,size,'bold' if bold else 'normal'),
                    fg=color, bg=bg, **kw)


class ScrollArea(tk.Frame):
    def __init__(self, parent, bg='white'):
        super().__init__(parent,bg=bg)
        self.canvas=tk.Canvas(self,bg=bg,highlightthickness=0)
        self.inner=tk.Frame(self.canvas,bg=bg)
        self.canvas.create_window(0,0,anchor='nw',window=self.inner)
        self.v=ttk.Scrollbar(self,orient='vertical',command=self.canvas.yview)
        self.h=ttk.Scrollbar(self,orient='horizontal',command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.v.set,xscrollcommand=self.h.set)
        self.canvas.grid(row=0,column=0,sticky='nsew')
        self.v.grid(row=0,column=1,sticky='ns')
        self.h.grid(row=1,column=0,sticky='ew')
        self.rowconfigure(0,weight=1);self.columnconfigure(0,weight=1)
        self.inner.bind('<Configure>',lambda e:self.canvas.configure(scrollregion=self.canvas.bbox('all')))


class Matrix(tk.Frame):
    W,H=92,68
    def __init__(self,parent,click):
        super().__init__(parent,bg='white')
        self.click=click
        self.canvas=tk.Canvas(self,bg='white',highlightthickness=0)
        self.xbar=ttk.Scrollbar(self,orient='horizontal',command=self.canvas.xview)
        self.ybar=ttk.Scrollbar(self,orient='vertical',command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.xbar.set,yscrollcommand=self.ybar.set)
        self.canvas.grid(row=0,column=0,sticky='nsew')
        self.ybar.grid(row=0,column=1,sticky='ns')
        self.xbar.grid(row=1,column=0,sticky='ew')
        self.columnconfigure(0,weight=1);self.rowconfigure(0,weight=1)
        self.canvas.bind('<Button-1>',self._click)
        self.problem=None

    def _click(self,event):
        if not self.problem:return
        j=int(self.canvas.canvasx(event.x)//self.W)-1
        i=int(self.canvas.canvasy(event.y)//self.H)-1
        if 0<=i<self.problem.m and 0<=j<self.problem.n:self.click((i,j))

    def draw(self,lesson,original=False):
        self.problem=p=lesson.problem
        c=self.canvas;c.delete('all')
        w,h=self.W,self.H
        state=lesson.state
        basis=state.basis if state else lesson.builder.basis
        plan=state.plan if state else lesson.builder.plan
        longest=max(len(str(value)) for value in (*p.supply,*p.demand,
                    *(x for row in p.costs for x in row),*(x for row in plan for x in row)))
        self.W=max(92,12*longest+24)
        w=self.W
        a=p.supply if state or original else lesson.builder.a
        b=p.demand if state or original else lesson.builder.b
        deltas=state.deltas() if state and lesson.phase in ('optimal','enter','cycle','theta','pivot','done') and not original else None
        cycle=state.cycle(lesson.entering) if state and lesson.phase in ('theta','pivot') and not original else []
        signs={cell:('+' if k%2==0 else '−') for k,cell in enumerate(cycle)}
        for i in range(p.m+2):
            for j in range(p.n+2):
                x,y=j*w,i*h
                fill='white'
                if i in (0,p.m+1) or j in (0,p.n+1):fill='#f5f7fb'
                cell=(i-1,j-1)
                if not original and cell in basis:fill='#edf5ff'
                if not original and cell in lesson.selected:fill='#d8e5ff'
                if cell in signs:fill='#e0f5ef' if signs[cell]=='+' else '#fff0e2'
                c.create_rectangle(x,y,x+w,y+h,fill=fill,outline=LINE)
                text=''
                if i==0 and j==0:text='u / v'
                elif i==0 and 1<=j<=p.n:text=f'B{j}' + (' · Ф' if p.dummy_col and j==p.n else '')
                elif j==0 and 1<=i<=p.m:text=f'A{i}'+(' · Ф' if p.dummy_row and i==p.m else '')
                elif i==0 and j==p.n+1:text='Запас'
                elif j==0 and i==p.m+1:text='Спрос'
                elif j==p.n+1 and 1<=i<=p.m:text=str(a[i-1])
                elif i==p.m+1 and 1<=j<=p.n:text=str(b[j-1])
                elif i==p.m+1 and j==p.n+1:text=str(sum(a))
                elif 1<=i<=p.m and 1<=j<=p.n:
                    cost=p.costs[i-1][j-1]
                    if original:
                        c.create_text(x+w/2,y+h/2,text=str(cost),font=(FONT,13),fill=INK)
                    else:
                        c.create_text(x+9,y+12,anchor='w',text='c',font=(FONT,9),fill=MUTED)
                        c.create_text(x+22,y+12,anchor='w',text=str(cost),font=(FONT,9),fill=BLUE)
                        value=plan[i-1][j-1]
                        shown=(str(value) if value else '0*') if cell in basis else '·'
                        c.create_text(x+w/2,y+37,text=shown,font=(FONT,15,'bold'),fill=INK if cell in basis else '#bdc7d6')
                        if deltas is not None:
                            d=deltas[i-1][j-1]
                            c.create_text(x+w-7,y+h-10,anchor='e',text=f'δ {d}',font=(FONT,9,'bold'),fill=GREEN if d>0 else MUTED)
                        if cell in signs:c.create_text(x+w-12,y+15,text=signs[cell],font=(FONT,16,'bold'),fill=GREEN if signs[cell]=='+' else '#b66c24')
                        if cell in lesson.selected or (lesson.phase in ('amount','cycle') and cell==lesson.entering):
                            c.create_rectangle(x+2,y+2,x+w-2,y+h-2,outline=BLUE,width=3)
                if text:c.create_text(x+w/2,y+h/2,text=text,font=(FONT,10,'bold'),fill=INK,width=w-6)
        if not original and lesson.accepted_potentials is not None:
            u,v=lesson.accepted_potentials
            for i,val in enumerate(u):c.create_text(w/2,(i+1)*h+53,text=f'u = {val}',font=(FONT,9),fill=MUTED)
            for j,val in enumerate(v):c.create_text((j+1)*w+w/2,53,text=f'v = {val}',font=(FONT,9),fill=MUTED)
        c.configure(scrollregion=(0,0,(p.n+2)*w,(p.m+2)*h))


class App:
    def __init__(self,root):
        self.root=root
        self.lesson=None
        self.feedback=''
        self.feedback_ok=True
        self.entries=[]
        root.title('КТЗ · Практикум')
        icon=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent))/'icon.ico'
        if icon.exists():
            try:root.iconbitmap(str(icon))
            except tk.TclError:pass
        root.geometry('1280x850');root.minsize(1050,720)
        root.configure(bg=BG)
        style=ttk.Style(root);style.theme_use('clam')
        style.configure('.',font=(FONT,11))
        style.configure('TButton',padding=(14,10),background='#edf1f8',foreground=INK,borderwidth=0)
        style.map('TButton',background=[('active','#e0e7f3')])
        style.configure('Primary.TButton',background=BLUE,foreground='white',padding=(16,11))
        style.map('Primary.TButton',background=[('active','#244ed1'),('disabled','#9bafd9')])
        style.configure('TEntry',padding=7,fieldbackground='white',bordercolor=LINE)
        style.configure('TCombobox',padding=7,fieldbackground='white')
        style.configure('TNotebook',background=BG,borderwidth=0)
        style.configure('TNotebook.Tab',padding=(8,10),background=BG,font=(FONT,10))
        style.map('TNotebook.Tab',background=[('selected','white')],foreground=[('selected',BLUE)])
        self.sidebar=tk.Frame(root,bg=NAVY,width=220)
        self.sidebar.pack(side='left',fill='y');self.sidebar.pack_propagate(False)
        label(self.sidebar,'КТЗ',size=28,bold=True,color='white',bg=NAVY).pack(anchor='w',padx=25,pady=(27,0))
        label(self.sidebar,'П Р А К Т И К У М',size=9,color='#93a8c6',bg=NAVY).pack(anchor='w',padx=27,pady=(0,32))
        label(self.sidebar,'МЕТОД ПОТЕНЦИАЛОВ',size=8,color='#8298b6',bg=NAVY).pack(anchor='w',padx=25,pady=(0,14))
        self.nav=[]
        for title in ['01   Исходные данные','02   Начальный план','03   Потенциалы','04   Оптимальность','05   Цикл и θ','06   Результат']:
            item=label(self.sidebar,title,size=11,color='#aabbd2',bg=NAVY,anchor='w',padx=15,pady=13)
            item.pack(fill='x',padx=10,pady=3);self.nav.append(item)
        label(self.sidebar,'Лабораторная работа № 1\n\nПошаговое решение.\nПроверка на каждом этапе.',size=10,color='#93a8c6',bg=NAVY,justify='left').pack(side='bottom',anchor='w',padx=25,pady=28)
        self.main=tk.Frame(root,bg=BG);self.main.pack(side='left',fill='both',expand=True)
        self.header=tk.Frame(self.main,bg=BG);self.header.pack(fill='x',padx=28,pady=(24,16))
        label(self.header,'Транспортная задача',size=23,bold=True,bg=BG).pack(side='left')
        self.new_button=ttk.Button(self.header,text='Новая задача',command=self.setup)
        self.body=tk.Frame(self.main,bg=BG);self.body.pack(fill='both',expand=True,padx=28,pady=(0,22))
        self.setup()

    def activate_nav(self,index):
        for k,item in enumerate(self.nav):item.configure(bg='#253e61' if k==index else NAVY,fg='white' if k==index else '#aabbd2')

    def clear(self):
        for widget in self.body.winfo_children():widget.destroy()

    def setup(self):
        if self.lesson and self.lesson.phase!='done':
            self._confirm_reset()
            return
        self._setup()

    def _confirm_reset(self):
        dialog=tk.Toplevel(self.root);dialog.withdraw();dialog.title('Новая задача');dialog.transient(self.root)
        dialog.configure(bg='white');dialog.resizable(False,False)
        label(dialog,'Начать новую задачу?',size=16,bold=True).pack(padx=28,pady=(25,12))
        label(dialog,'Текущий учебный сеанс будет завершён.\nИсходные файлы приложения не изменяются.',justify='left').pack(padx=28,pady=(0,20))
        buttons=tk.Frame(dialog,bg='white');buttons.pack(padx=24,pady=(0,24))
        ttk.Button(buttons,text='Продолжить решение',command=dialog.destroy).pack(side='left',padx=5)
        ttk.Button(buttons,text='Новая задача',style='Primary.TButton',command=lambda:(dialog.destroy(),self._setup())).pack(side='left',padx=5)
        dialog.update_idletasks()
        x=self.root.winfo_rootx()+(self.root.winfo_width()-dialog.winfo_reqwidth())//2
        y=self.root.winfo_rooty()+(self.root.winfo_height()-dialog.winfo_reqheight())//2
        dialog.geometry(f'{x:+d}{y:+d}')
        dialog.deiconify();dialog.grab_set()

    def _setup(self):
        self.lesson=None;self.clear();self.activate_nav(0);self.new_button.pack_forget()
        label(self.body,'Начните с условий задачи',size=15,bold=True,bg=BG).pack(anchor='w')
        label(self.body,'Введите тарифы, запасы и спрос. Можно загрузить учебный пример или составить свой.',color=MUTED,bg=BG).pack(anchor='w',pady=(5,18))
        bar=tk.Frame(self.body,bg='white',padx=16,pady=16);bar.pack(fill='x',pady=(0,12))
        self.preset=ttk.Combobox(bar,values=list(PRESETS),state='readonly',width=34)
        self.preset.current(0);self.preset.grid(row=0,column=0,padx=(0,8),sticky='w')
        ttk.Button(bar,text='Загрузить',command=self.load_preset).grid(row=0,column=1,padx=(0,20))
        label(bar,'Строки').grid(row=0,column=2,padx=(0,5))
        self.rows=ttk.Spinbox(bar,from_=1,to=30,width=3);self.rows.set('4');self.rows.grid(row=0,column=3,padx=(0,10))
        label(bar,'Столбцы').grid(row=0,column=4,padx=(0,5))
        self.cols=ttk.Spinbox(bar,from_=1,to=30,width=3);self.cols.set('3');self.cols.grid(row=0,column=5,padx=(0,8))
        ttk.Button(bar,text='Создать таблицу',command=self.create_empty).grid(row=0,column=6)
        self.editor=ScrollArea(self.body);self.editor.pack(fill='both',expand=True)
        self.setup_note=label(self.body,'',bg=BG,color=MUTED,anchor='w',justify='left',wraplength=890)
        self.setup_note.pack(fill='x',pady=12)
        footer=tk.Frame(self.body,bg=BG);footer.pack(fill='x')
        ttk.Button(footer,text='Проверить баланс',command=self.check_balance).pack(side='left')
        self.dummy_button=ttk.Button(footer,text='Добавить фиктивную вершину',command=self.add_dummy)
        ttk.Button(footer,text='Приступить к решению →',style='Primary.TButton',command=self.start).pack(side='right')
        self.load_preset()

    def load_preset(self):
        p=PRESETS[self.preset.get()]
        self.rows.set(str(p.m));self.cols.set(str(p.n))
        self.edit_problem(p)
        note='Проверьте баланс. При необходимости добавьте фиктивную строку или столбец и заполните её объём и тарифы.'
        if 'Вариант 3' in self.preset.get():
            note='Последняя строка — фиктивный поставщик на 30. Тариф 100 штрафует нехватку у предприятий 1 и 4, как в методичке; это не абсолютный запрет маршрута.'
        self.setup_note.configure(text=note,fg=MUTED)

    def create_empty(self):
        try:
            m,n=int(self.rows.get()),int(self.cols.get())
            if not(1<=m<=30 and 1<=n<=30):raise ValueError()
            self.edit_problem(Problem(tuple((0,)*n for _ in range(m)),(0,)*m,(0,)*n))
            self.setup_note.configure(text='Введите тарифы в центральную матрицу, запасы справа, спрос снизу.',fg=MUTED)
        except ValueError:self.setup_note.configure(text='Размерность: целые числа от 1 до 30.',fg='#b33c41')

    def edit_problem(self,p):
        self.dummy_button.pack_forget()
        for widget in self.editor.inner.winfo_children():widget.destroy()
        self.edit_shape=p.m,p.n;self.edit_source=p
        frame=self.editor.inner
        label(frame,'Тариф cᵢⱼ',size=10,color=MUTED).grid(row=0,column=0,padx=16,pady=15)
        for j in range(p.n):label(frame,f'B{j+1}'+(' · фикт.' if p.dummy_col and j==p.n-1 else ''),bold=True).grid(row=0,column=j+1,pady=15)
        label(frame,'Запас aᵢ',bold=True,color=GREEN).grid(row=0,column=p.n+1,padx=12)
        self.cost_entries=[];self.supply_entries=[];self.demand_entries=[]
        def entry(value,i,j,vector=False):
            e=ttk.Entry(frame,width=8,justify='center');e.insert(0,str(value));e.grid(row=i,column=j,padx=4,pady=5,ipady=4)
            return e
        for i in range(p.m):
            label(frame,f'A{i+1}'+(' · фикт.' if p.dummy_row and i==p.m-1 else ''),bold=True).grid(row=i+1,column=0,padx=14)
            self.cost_entries.append([entry(p.costs[i][j],i+1,j+1) for j in range(p.n)])
            self.supply_entries.append(entry(p.supply[i],i+1,p.n+1,True))
        label(frame,'Спрос bⱼ',bold=True,color=GREEN).grid(row=p.m+1,column=0,padx=14,pady=12)
        self.demand_entries=[entry(p.demand[j],p.m+1,j+1,True) for j in range(p.n)]

    def read_problem(self):
        costs=tuple(tuple(int(e.get().strip()) for e in row) for row in self.cost_entries)
        a=tuple(int(e.get().strip()) for e in self.supply_entries)
        b=tuple(int(e.get().strip()) for e in self.demand_entries)
        if any(abs(x)>10**12 for x in (*a,*b,*(x for row in costs for x in row))):
            raise ValueError('Максимальное значение в интерфейсе — 1 000 000 000 000.')
        return Problem(costs,a,b,self.edit_source.dummy_row,self.edit_source.dummy_col)

    def setup_error(self,error):
        message=str(error)
        if 'invalid literal' in message:
            message='Заполните все ячейки целыми неотрицательными числами.'
        self.setup_note.configure(text=message,fg='#b33c41')

    def check_balance(self):
        self.dummy_button.pack_forget()
        try:
            p=self.read_problem()
            if not (p.dummy_row or p.dummy_col) and sum(p.supply)!=sum(p.demand):
                side='столбец' if sum(p.supply)>sum(p.demand) else 'строку'
                self.dummy_button.configure(text=f'Добавить фиктивный {side}' if side=='столбец' else 'Добавить фиктивную строку')
                self.dummy_button.pack(side='left',padx=8)
            self.validate_editor(p)
            self.setup_note.configure(text='Баланс и тарифы фиктивной вершины верны. Можно приступить к решению.',fg=GREEN)
        except ValueError as error:self.setup_error(error)

    def add_dummy(self):
        try:
            p=self.read_problem()
            if p.dummy_row or p.dummy_col:
                raise ValueError('Фиктивная вершина уже добавлена. Исправьте её объём и тарифы.')
            diff=sum(p.supply)-sum(p.demand)
            if not diff:raise ValueError('Задача уже сбалансирована; фиктивная вершина не нужна.')
            if diff>0:
                p=Problem(tuple(row+(0,) for row in p.costs),p.supply,p.demand+(0,),dummy_col=True)
            else:
                p=Problem(p.costs+((0,)*p.n,),p.supply+(0,),p.demand,dummy_row=True)
            self.edit_problem(p)
            target=self.demand_entries[-1] if diff>0 else self.supply_entries[-1]
            target.delete(0,'end');target.focus_set()
            self.setup_note.configure(text=f'Введите объём фиктивной вершины ({abs(diff)}) и проверьте тарифы. Затем нажмите «Проверить баланс».',fg=MUTED)
        except ValueError as error:self.setup_error(error)

    def validate_editor(self,p):
        p.validate_balance()
        if p.dummy_row:
            expected=self.edit_source.costs[-1]
            if p.costs[-1]!=expected:
                raise ValueError(f'Тарифы фиктивной строки должны быть {expected}; сохраните штрафы по условию задачи.')
        if p.dummy_col:
            expected=tuple(row[-1] for row in self.edit_source.costs)
            if tuple(row[-1] for row in p.costs)!=expected:
                raise ValueError(f'Тарифы фиктивного столбца должны быть {expected}.')

    def start(self):
        try:
            p=self.read_problem()
            self.validate_editor(p)
            self.lesson=Lesson(p)
        except ValueError as error:
            self.setup_error(error);return
        self.feedback='Условия приняты. Баланс проверен.'
        self.feedback_ok=True
        self.show_lesson()

    def show_lesson(self):
        self.clear();self.new_button.pack(side='right')
        self.summary=tk.Frame(self.body,bg=BG);self.summary.pack(fill='x',pady=(0,15))
        self.stat_labels=[]
        for title in ['СТОИМОСТЬ ПЛАНА','ИТЕРАЦИЯ','ОШИБКИ / ПОДСКАЗКИ']:
            card=tk.Frame(self.summary,bg='white',padx=18,pady=12);card.pack(side='left',fill='x',expand=True,padx=(0,10))
            label(card,title,size=8,color=MUTED).pack(anchor='w')
            val=label(card,'',size=20,bold=True);val.pack(anchor='w');self.stat_labels.append(val)
        self.workspace=tk.Frame(self.body,bg=BG);self.workspace.pack(fill='both',expand=True)
        self.workspace.columnconfigure(0,weight=1);self.workspace.columnconfigure(1,weight=0,minsize=350)
        self.workspace.rowconfigure(0,weight=1)
        left=tk.Frame(self.workspace,bg='white');left.grid(row=0,column=0,sticky='nsew',padx=(0,14))
        self.notebook=ttk.Notebook(left);self.notebook.pack(fill='both',expand=True)
        gridtab=tk.Frame(self.notebook,bg='white');originaltab=tk.Frame(self.notebook,bg='white');historytab=tk.Frame(self.notebook,bg='white')
        self.notebook.add(gridtab,text='Рабочая таблица');self.notebook.add(originaltab,text='Исходные данные');self.notebook.add(historytab,text='Журнал')
        self.matrix=Matrix(gridtab,self.select);self.matrix.pack(fill='both',expand=True,padx=12,pady=12)
        label(gridtab,'Синее число — тариф c    ·    тёмное число — объём    ·    0* — нулевая базисная клетка\nδᵢⱼ = vⱼ − uᵢ − cᵢⱼ; δ > 0 — возможность улучшения; Ф — фиктивная вершина',size=9,color=MUTED,justify='left',anchor='w').pack(fill='x',padx=14,pady=(0,13))
        self.original_matrix=Matrix(originaltab,lambda cell:None);self.original_matrix.pack(fill='both',expand=True,padx=12,pady=12)
        self.log=tk.Text(historytab,bg='white',fg=INK,font=(FONT,11),wrap='word',relief='flat',padx=15,pady=15)
        logbar=ttk.Scrollbar(historytab,command=self.log.yview);self.log.configure(yscrollcommand=logbar.set)
        logbar.pack(side='right',fill='y');self.log.pack(fill='both',expand=True)
        question_scroll=ScrollArea(self.workspace)
        question_scroll.grid(row=0,column=1,sticky='nsew')
        question_scroll.grid_propagate(False)
        self.question=tk.Frame(question_scroll.inner,bg='white',padx=20,pady=20)
        self.question.pack(fill='both',expand=True)
        self.refresh()

    def select(self,cell):
        if self.lesson.phase not in ('cell','enter','cycle'):return
        if self.lesson.phase=='cycle':
            if cell in self.lesson.selected:self.lesson.selected.remove(cell)
            else:self.lesson.selected.add(cell)
        else:self.lesson.selected={cell}
        self.matrix.draw(self.lesson)
        self.selection.configure(text='Выбрано: '+self.lesson.cells_text(self.lesson.selected))

    def refresh(self):
        l=self.lesson;phase=l.phase
        step=1 if phase in ('cell','amount','basis') else 2 if phase=='potentials' else 3 if phase=='optimal' else 5 if phase=='done' else 4
        self.activate_nav(step)
        self.stat_labels[0].configure(text=str(l.state.cost) if l.state else 'строится')
        self.stat_labels[1].configure(text=str(l.state.iteration) if l.state else '0')
        self.stat_labels[2].configure(text=f'{l.errors} / {l.hints}')
        self.matrix.draw(l);self.original_matrix.draw(l,True)
        self.log.configure(state='normal');self.log.delete('1.0','end')
        for k,item in enumerate(l.history,1):self.log.insert('end',f'{k:02d}   {item}\n\n')
        self.log.configure(state='disabled');self.log.see('end')
        for widget in self.question.winfo_children():widget.destroy()
        titles={'cell':'Минимальный тариф','amount':'Объём перевозки','basis':'Начальный план готов','potentials':'Рассчитайте потенциалы','optimal':'План оптимален?','enter':'Входящая клетка','cycle':'Постройте цикл','theta':'Определите θ','pivot':'Переход к новому плану','done':'Решение завершено'}
        label(self.question,f'ШАГ {step+1:02d}',size=9,bold=True,color=BLUE).pack(anchor='w')
        label(self.question,titles[phase],size=17,bold=True,wraplength=285,justify='left').pack(anchor='w',pady=(9,14))
        instructions={
            'cell':'Выберите в таблице клетку с минимальным тарифом c среди строк с оставшимся запасом и столбцов с оставшимся спросом. При равенстве допустима любая.',
            'amount':f'Клетка {l.cells_text([l.entering])}. Введите максимально возможный объём: минимум оставшегося запаса и спроса.',
            'basis':'Для расчёта потенциалов нужно m+n−1 независимых базисных клеток. Если положительных перевозок меньше, базис дополнен клетками с точным нулевым объёмом (0*).',
            'potentials':'Для каждой базисной клетки, включая 0*: vⱼ − uᵢ = cᵢⱼ. Можно начать с u₁ = 0. Введите числа через пробел; любой согласованный общий сдвиг принимается.',
            'optimal':'Оценки показаны внизу каждой клетки: δᵢⱼ = vⱼ − uᵢ − cᵢⱼ. План оптимален, если положительных оценок нет.',
            'enter':('Действует правило Бланда для защиты от циклов: выберите небазисную клетку с δ > 0, первую по номеру строки, затем столбца.' if l.state and l.state.uses_bland else 'Выберите небазисную клетку с максимальной положительной оценкой δ. При равенстве допустима любая.'),
            'cycle':'Входящая клетка уже выделена. Отметьте кликами все ОСТАЛЬНЫЕ вершины замкнутого цикла по базису. Переходы идут попеременно по строкам и столбцам; клетки 0* тоже участвуют.',
            'theta':'Знаки цикла показаны в таблице. θ равна минимуму перевозок на вершинах со знаком «−». При вырожденности θ может быть равна нулю.',
            'pivot':'После подтверждения объёмы изменятся на ±θ. Одна минусовая клетка с минимальным объёмом покинет базис; при равенстве — первая по номеру.',
            'done':'Все оценки неположительны. План удовлетворяет запасам и спросу, а его стоимость минимальна. Исходные данные и история решения доступны во вкладках.'}
        label(self.question,instructions[phase],size=11,color=MUTED,wraplength=285,justify='left').pack(anchor='w')
        if l.state and l.state.degenerate:
            label(self.question,'ВЫРОЖДЕННЫЙ ПЛАН · 0*',size=9,bold=True,color=GREEN,bg='#e2f3ed',padx=8,pady=8).pack(anchor='w',pady=(14,0))
        self.selection=label(self.question,'Выбрано: —',size=10,color=BLUE,wraplength=285,justify='left')
        if phase in ('cell','enter','cycle'):self.selection.pack(anchor='w',pady=(16,4))
        self.answer=None;self.u_entry=None;self.v_entry=None
        if phase in ('amount','theta'):
            label(self.question,'Ваш ответ',size=10,bold=True).pack(anchor='w',pady=(18,5))
            self.answer=ttk.Entry(self.question,width=22,font=(FONT,15));self.answer.pack(fill='x');self.answer.bind('<Return>',lambda e:self.check())
        if phase=='potentials':
            for title,attr in [('u — потенциалы строк','u_entry'),('v — потенциалы столбцов','v_entry')]:
                label(self.question,title,size=10,bold=True).pack(anchor='w',pady=(14,4))
                entry=ttk.Entry(self.question);entry.pack(fill='x');setattr(self,attr,entry)
            self.v_entry.bind('<Return>',lambda e:self.check())
        buttons=tk.Frame(self.question,bg='white');buttons.pack(fill='x',pady=(18,8))
        if phase=='optimal':
            ttk.Button(buttons,text='Да',style='Primary.TButton',command=lambda:self.check(True)).pack(side='left',expand=True,fill='x',padx=(0,6))
            ttk.Button(buttons,text='Нет',command=lambda:self.check(False)).pack(side='left',expand=True,fill='x')
        elif phase!='done':
            text='Показать новый план →' if phase=='pivot' else 'К потенциалам →' if phase=='basis' else 'Проверить ответ'
            ttk.Button(buttons,text=text,style='Primary.TButton',command=self.check).pack(fill='x')
        else:ttk.Button(buttons,text='Решить другую задачу',style='Primary.TButton',command=self._setup).pack(fill='x')
        self.feedback_label=label(self.question,'Результат последней проверки\n\n'+self.feedback,size=10,color=GREEN if self.feedback_ok else '#b33c41',bg='#edf7f2' if self.feedback_ok else '#fff0f0',wraplength=265,justify='left',anchor='w',padx=10,pady=10)
        self.feedback_label.pack(fill='x',pady=(0,12))
        if phase not in ('done','basis','pivot'):ttk.Button(self.question,text='Подсказка',command=self.hint).pack(fill='x',pady=(0,8))
        self.hint_label=label(self.question,'',size=10,color='#2454a6',bg='#edf4ff',wraplength=265,justify='left',anchor='w',padx=10,pady=10)

    def check(self,answer=None):
        try:
            if self.lesson.phase in ('amount','theta'):answer=int(self.answer.get().strip())
            elif self.lesson.phase=='potentials':
                answer=([int(x) for x in self.u_entry.get().replace(';',' ').replace(',',' ').split()],
                        [int(x) for x in self.v_entry.get().replace(';',' ').replace(',',' ').split()])
        except ValueError:
            self.lesson.errors+=1
            self.feedback='Введите целые числа. Потенциалы разделяйте пробелами.';self.feedback_ok=False
            self.update_feedback();return
        accepted,feedback=self.lesson.check(answer)
        self.feedback,self.feedback_ok=feedback,accepted
        if accepted:self.refresh()
        else:self.update_feedback()

    def update_feedback(self):
        self.stat_labels[2].configure(text=f'{self.lesson.errors} / {self.lesson.hints}')
        self.feedback_label.configure(text='Результат последней проверки\n\n'+self.feedback,fg=GREEN if self.feedback_ok else '#b33c41',bg='#edf7f2' if self.feedback_ok else '#fff0f0')

    def hint(self):
        self.hint_label.configure(text='Подсказка\n\n'+self.lesson.hint())
        self.hint_label.pack(fill='x',pady=(0,12))
        self.stat_labels[2].configure(text=f'{self.lesson.errors} / {self.lesson.hints}')


def main():
    if sys.platform=='win32':
        try:ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError,OSError):pass
    root=tk.Tk()
    if '--smoke-test' in sys.argv:root.withdraw()
    app=App(root)
    if '--smoke-test' in sys.argv:
        root.update_idletasks()
        app.check_balance()
        app.add_dummy()
        app.demand_entries[-1].insert(0,'90')
        app.start()
        root.update_idletasks()
        assert app.lesson is not None
        assert app.lesson.problem.n==4
        root.destroy()
        print('Tk startup, problem editor, balancing and lesson rendering: OK')
    else:root.mainloop()


if __name__=='__main__':main()
