"""Тесты без реального Tk: tkinter подменяется заглушками.

Проверяем то, что важно для исправленных багов:
  1. модуль импортируется, все 8 мини-игр наследуются от MinigameBase;
  2. _flash_attack_point существует и вызывается из симуляции;
  3. провал мини-игры = провал цели (не засчитывается успех);
  4. навыки hacking_speed / minigame_difficulty / stealth реально влияют;
  5. delete_player_data вызывается (кнопка сброса);
  6. горячая смена темы пересобирает UI;
  7. битый файл настроек не обнуляет всё;
  8. нет голых except и нет дублированных методов.
"""
import ast
import io
import sys
import types
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
SRC_PATH = REPO / 'legacy' / 'hacker-app.py'
SRC = SRC_PATH.read_text(encoding='utf-8')
TREE = ast.parse(SRC)


# ───────────────────────── статические проверки ──────────────────────────
def test_module_parses_without_tabs_or_crlf():
    raw = SRC_PATH.read_bytes()
    assert b'\r' not in raw, 'в файле остались CR'
    # табы допустимы только внутри ASCII-арта
    for node in ast.walk(TREE):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if '\t' in node.value:
                assert '█' in node.value or '___' in node.value, 'таб вне ASCII-арта'


def test_no_bare_except():
    bad = [n.lineno for n in ast.walk(TREE) if isinstance(n, ast.ExceptHandler) and n.type is None]
    assert bad == [], f'голые except в строках {bad}'


def test_minigames_inherit_base():
    classes = {n.name: n for n in TREE.body if isinstance(n, ast.ClassDef)}
    games = ['RockPaperScissorsGame', 'TicTacToeGame', 'SimonSaysGame', 'WireDefuseGame',
             'TypeCodeGame', 'MazeGame', 'SafeCrackGame', 'MathGame']
    assert 'MinigameBase' in classes
    for g in games:
        bases = [ast.unparse(b) for b in classes[g].bases]
        assert bases == ['MinigameBase'], (g, bases)


def test_no_duplicated_methods_in_minigames():
    classes = {n.name: n for n in TREE.body if isinstance(n, ast.ClassDef)}
    for name, cls in classes.items():
        names = [n.name for n in cls.body if isinstance(n, ast.FunctionDef)]
        assert len(names) == len(set(names)), f'{name}: дубли методов'
    # _center_window/_on_win/_on_lose должны быть только в базе
    for meth in ('_center_window', '_on_win', '_on_lose'):
        owners = [n for n, c in classes.items()
                  if any(isinstance(m, ast.FunctionDef) and m.name == meth for m in c.body)]
        assert owners == ['MinigameBase'], (meth, owners)


def test_unused_imports_removed():
    imports = {a.name for n in TREE.body if isinstance(n, ast.Import) for a in n.names}
    for gone in ('math', 'collections'):
        assert gone not in imports, f'{gone} всё ещё импортируется'
    assert 'from datetime import datetime, timedelta' not in SRC


def test_flash_attack_point_defined_and_used():
    assert 'def _flash_attack_point' in SRC
    cls = next(n for n in TREE.body if isinstance(n, ast.ClassDef) and n.name == 'HackersTerminal')
    methods = {n.name for n in cls.body if isinstance(n, ast.FunctionDef)}
    assert '_flash_attack_point' in methods
    assert 'self._flash_attack_point(' in SRC


def test_delete_player_data_is_called():
    calls = [n for n in ast.walk(TREE)
             if isinstance(n, ast.Attribute) and n.attr == 'delete_player_data'
             and isinstance(n.ctx, ast.Load)]
    assert calls, 'delete_player_data по-прежнему никем не вызывается'


def test_theme_hot_swap_and_validation():
    assert 'def _rebuild_ui' in SRC
    assert 'apply_theme(force_rebuild=True)' in SRC
    assert 'применится при перезапуске' not in SRC
    # load_settings валидирует поля по одному
    assert 'def _default_player_data' in SRC
    assert "if theme_name not in THEMES" in SRC


def test_skills_are_used_in_simulation():
    assert "skills.get('hacking_speed'" in SRC
    assert "skills.get('minigame_difficulty'" in SRC
    assert "skills.get('stealth'" in SRC
    assert "'detect_chance'" in SRC or 'detect_chance' in SRC


def test_failure_is_counted():
    assert "self.player_data['hacks_failed'] += failed" in SRC
    assert 'цель пропущена' in SRC


# ─────────────────────── динамика с заглушкой tkinter ─────────────────────
class _FakeWidget:
    def __init__(self, *a, **kw):
        self._kw = dict(kw)
        self._children = []
        self._exists = True

    # всё, что вызывается на виджетах
    def pack(self, *a, **kw): return self
    def grid(self, *a, **kw): return self
    def place(self, *a, **kw): return self
    def bind(self, *a, **kw): return self
    def unbind(self, *a, **kw): return self
    def configure(self, *a, **kw): self._kw.update(kw); return self
    config = configure
    def cget(self, k):
        v = self._kw.get(k)
        return v if v is not None else '0'
    def insert(self, *a, **kw): return None
    def delete(self, *a, **kw): return None
    def see(self, *a, **kw): return None
    def tag_config(self, *a, **kw): return None
    def itemconfigure(self, *a, **kw): return None
    def coords(self, *a, **kw): return None
    def create_line(self, *a, **kw): return 1
    def create_oval(self, *a, **kw): return 2
    def create_rectangle(self, *a, **kw): return 3
    def after(self, ms, fn=None, *a):
        return 'after-id'
    def after_cancel(self, *a): return None
    def update_idletasks(self): return None
    def winfo_exists(self): return self._exists
    def winfo_width(self): return 260
    def winfo_height(self): return 110
    def winfo_screenwidth(self): return 1920
    def winfo_screenheight(self): return 1080
    def destroy(self): self._exists = False
    def focus_set(self): return None
    def grab_set(self): return None
    def protocol(self, *a): return None
    def title(self, *a): return None
    def geometry(self, *a): return None
    def resizable(self, *a): return None
    def withdraw(self): return None
    def deiconify(self): return None
    def overrideredirect(self, *a): return None
    def pack_propagate(self, *a): return None
    def curselection(self): return ()
    def selection_clear(self, *a): return None
    def selection_set(self, *a): return None
    def size(self): return 0
    def get(self, *a, **kw): return '' if not a else []
    def set(self, *a, **kw): return None
    def yview(self, *a): return None
    def heading(self, *a, **kw): return None
    def column(self, *a, **kw): return None
    def quit(self): return None


class _FakeVar:
    def __init__(self, value=None, **kw):
        self._v = value

    def get(self): return self._v
    def set(self, v): self._v = v


def _install_fake_tk():
    tk = types.ModuleType('tkinter')
    tk.BOTH, tk.X, tk.Y, tk.LEFT, tk.RIGHT, tk.END = 'both', 'x', 'y', 'left', 'right', 'end'
    tk.TOP, tk.BOTTOM, tk.HORIZONTAL, tk.NORMAL, tk.DISABLED = 'top', 'bottom', 'h', 'normal', 'disabled'
    tk.WORD, tk.EXTENDED = 'word', 'extended'
    for cls in ('Tk', 'Toplevel', 'Frame', 'Label', 'Button', 'Entry', 'Text', 'Canvas',
                'Listbox', 'Scrollbar', 'Radiobutton', 'Checkbutton', 'Scale', 'Menu'):
        setattr(tk, cls, type(cls, (_FakeWidget,), {}))
    for var in ('StringVar', 'IntVar', 'DoubleVar', 'BooleanVar'):
        setattr(tk, var, type(var, (_FakeVar,), {}))
    tk.TclError = type('TclError', (Exception,), {})

    subs = {}
    for name in ('ttk', 'scrolledtext', 'messagebox', 'filedialog'):
        m = types.ModuleType('tkinter.' + name)
        subs[name] = m
    subs['ttk'].Progressbar = type('Progressbar', (_FakeWidget,), {})
    subs['ttk'].Style = lambda *a, **kw: mock.MagicMock()
    subs['ttk'].Treeview = type('Treeview', (_FakeWidget,), {})
    subs['scrolledtext'].ScrolledText = type('ScrolledText', (_FakeWidget,), {})
    subs['messagebox'].showinfo = lambda *a, **kw: None
    subs['messagebox'].showwarning = lambda *a, **kw: None
    subs['messagebox'].showerror = lambda *a, **kw: None
    subs['messagebox'].askyesno = lambda *a, **kw: True
    subs['filedialog'].asksaveasfilename = lambda *a, **kw: ''

    tk.ttk, tk.scrolledtext, tk.messagebox, tk.filedialog = (
        subs['ttk'], subs['scrolledtext'], subs['messagebox'], subs['filedialog'])
    sys.modules['tkinter'] = tk
    for k, v in subs.items():
        sys.modules['tkinter.' + k] = v
    return tk


def _load_app_module():
    fake = _install_fake_tk()
    mod = types.ModuleType('hacker_app')
    mod.__file__ = str(SRC_PATH)
    exec(compile(SRC, str(SRC_PATH), 'exec'), mod.__dict__)
    return mod, fake


def test_dynamic_simulation_counts_failure():
    """Провал мини-игры не должен засчитывать цель как взломанную."""
    mod, tk = _load_app_module()
    FakeHT = mod.HackersTerminal

    app = FakeHT.__new__(FakeHT)          # без __init__ (там splash и темы)
    app.root = tk.Tk()
    app.theme = mod.THEMES['matrix']
    app.attack_mode = 'normal'
    app.minigame_chance = 100
    app.show_calculations = False
    app.is_hacking = True
    app.glitch_enabled = False
    app.minigame_event = mock.MagicMock()
    app.player_data = FakeHT._default_player_data()
    app.attack_history = []
    app.target_order = {}
    app.log_lines = []

    # логи и прогресс — без реальных виджетов
    app._do_log = lambda msg, t: app.log_lines.append(msg)
    app._do_status = lambda t: None
    app._do_progress = lambda v, t=None: None
    app._do_matrix = lambda line: None
    app.save_player_data = lambda: None
    app.save_history = lambda: None
    app._update_balance_display = lambda: None
    app._flash_attack_point = lambda x, y: app.log_lines.append('FLASH')
    app._generate_calc = lambda: 'calc'
    app._generate_scan = lambda: 'scan'
    app._generate_data = lambda: 'data'
    app._generate_hex = lambda: 'hex'
    app.target_listbox = tk.Listbox()
    app.target_listbox.curselection = lambda: (0,)
    app.target_listbox.get = lambda i: 'test / test.com'
    app.target_list = ['test / test.com']
    app._trigger_minigame = lambda name: False      # всегда проигрываем
    app.safe_call = lambda fn, *a: fn(*a)          # синхронно

    import time as _t
    with mock.patch.object(mod.time, 'sleep', lambda *_: None):
        app.hacking_simulation()

    assert app.player_data['hacks_completed'] == 0, 'провал засчитан как успех!'
    assert app.player_data['hacks_failed'] == 1, app.player_data['hacks_failed']
    assert any('FLASH' in l for l in app.log_lines), 'карта не мигала'
    assert any('цель пропущена' in l for l in app.log_lines)


def test_dynamic_skills_affect_params():
    mod, tk = _load_app_module()
    FakeHT = mod.HackersTerminal
    app = FakeHT.__new__(FakeHT)
    app.theme = mod.THEMES['matrix']
    app.attack_mode = 'normal'
    app.player_data = FakeHT._default_player_data()

    base = app._get_mode_params()

    app.player_data['skills']['hacking_speed'] = 6
    app.player_data['skills']['minigame_difficulty'] = 6
    app.player_data['skills']['stealth'] = 6
    buffed = app._get_mode_params()

    assert buffed['delay_mult'] < base['delay_mult'], 'скорость взлома не работает'
    assert buffed['minigame_mult'] < base['minigame_mult'], 'легкость мини-игр не работает'
    assert 'detect_chance' in buffed and buffed['detect_chance'] < base['detect_chance']


def test_dynamic_flash_and_map():
    mod, tk = _load_app_module()
    FakeHT = mod.HackersTerminal
    app = FakeHT.__new__(FakeHT)
    app.theme = mod.THEMES['matrix']
    app.root = tk.Tk()
    app.map_canvas = tk.Canvas(width=260, height=110)
    app._draw_map_grid()
    app._flash_attack_point(50, 40)          # не должно падать
    app.map_canvas = None
    app._flash_attack_point(50, 40)          # и без карты тоже


def test_dynamic_theme_rebuild():
    mod, tk = _load_app_module()
    FakeHT = mod.HackersTerminal
    app = FakeHT.__new__(FakeHT)
    app.theme = mod.THEMES['matrix']
    app.root = tk.Tk()
    app.attack_mode = 'normal'
    app.player_data = FakeHT._default_player_data()
    # «до» перерисовки интерфейс уже существует
    app.main_frame = tk.Frame()
    app.log_text = tk.Text()
    app.log_text.get = lambda *a: 'старый лог'
    app.target_listbox = tk.Listbox()
    app.target_listbox.curselection = lambda: ()
    app.progress_percent = tk.Label()
    app.progress_percent.cget = lambda k: '100%'
    app.target_list = ['a / a.com']
    app.target_order = {}
    app.click_count = 0
    app.mode_var = tk.StringVar('normal')
    app.progress_var = tk.DoubleVar(100.0)
    app.status_var = tk.StringVar('ok')
    app.selected_var = tk.StringVar('Выбрано: 0')
    app.status_labels = []
    created = []

    # минимальный create_widgets-двойник, чтобы не рисовать весь UI
    def fake_create_widgets():
        created.append(1)
        app.main_frame = tk.Frame()
        app.log_text = tk.Text()
        app.log_text.insert = lambda *a: None
        app.log_text.get = lambda *a: 'старый лог'
        app.log_text.see = lambda *a: None
        app.target_listbox = tk.Listbox()
        app.target_listbox.size = lambda: 0
        app.progress_percent = tk.Label()
        app.progress_percent.cget = lambda k: '100%'
        app.selected_var = tk.StringVar('')
        app.status_labels = []
    app.create_widgets = fake_create_widgets
    app.main_frame = tk.Frame()

    app.apply_theme(force_rebuild=True)
    assert created, 'интерфейс не пересобран при смене темы'


def test_dynamic_reset_profile():
    mod, tk = _load_app_module()
    FakeHT = mod.HackersTerminal
    app = FakeHT.__new__(FakeHT)
    app.player_data = FakeHT._default_player_data()
    app.player_data['money'] = 9999
    app._update_balance_display = lambda: None
    app.delete_player_data()
    assert app.player_data['money'] == 0


if __name__ == '__main__':
    import traceback
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith('test_')]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f'  ✓ {name}')
        except Exception as e:
            failed += 1
            print(f'  ✗ {name}: {type(e).__name__}: {e}')
            traceback.print_exc(limit=2)
    print(f'\n{len(tests) - failed}/{len(tests)} тестов прошло')
    sys.exit(1 if failed else 0)
