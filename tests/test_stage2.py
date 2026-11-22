"""Тесты Этапа 2: симуляция взлома и живой лог.

Запуск:  python3 tests/test_stage2.py
"""
import ast
import os
import random as _r
import sys
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from gamedev import gamedata  # noqa: E402
from gamedev.attack import Attack, LogLine, mode_params  # noqa: E402

DATA_ATTRS = ('target_list', 'stupid_messages', 'fake_errors',
              'scan_messages', 'data_messages')


def _legacy_lists():
    tree = ast.parse((REPO / 'legacy' / 'hacker-app.py').read_text(encoding='utf-8'))
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'HackersTerminal':
            for fn in node.body:
                if isinstance(fn, ast.FunctionDef) and fn.name == '__init__':
                    for st in ast.walk(fn):
                        if (isinstance(st, ast.Assign)
                                and isinstance(st.targets[0], ast.Attribute)
                                and st.targets[0].attr in DATA_ATTRS):
                            out[st.targets[0].attr] = ast.literal_eval(st.value)
    return out


def _run(attack, limit=900.0, step=0.1):
    t = 0.0
    while not attack.finished and t < limit:
        attack.update(step)
        t += step
    return t


def _attack(mode='normal', targets=('a / a.com',), chance=0, seed=1, calc=True):
    return Attack(targets=list(targets), params=mode_params(mode),
                  minigame_chance=chance, show_calculations=calc,
                  rng=_r.Random(seed))


# ─────────────────── игровые данные ───────────────────
def test_gamedata_matches_legacy():
    legacy = _legacy_lists()
    for new, old in (('TARGETS', 'target_list'),
                     ('STUPID_MESSAGES', 'stupid_messages'),
                     ('FAKE_ERRORS', 'fake_errors'),
                     ('SCAN_TEMPLATES', 'scan_messages'),
                     ('DATA_TEMPLATES', 'data_messages')):
        assert getattr(gamedata, new) == legacy[old], f'{new} разъехались с legacy'
    assert len(gamedata.TARGETS) == 81


# ─────────────────── движок атаки ───────────────────
def test_attack_runs_to_completion():
    a = _attack(targets=['a / a.com', 'b / b.com'], seed=11)
    _run(a)
    assert a.finished, 'симуляция не завершилась'
    assert a.progress == 100
    assert a.completed == 2 and a.failed == 0
    assert a.money > 0


def test_attack_interrupt_stops_output():
    a = _attack()
    a.update(0.5)
    a.drain()
    a.finished = True                 # как при нажатии СТОП
    for _ in range(20):
        a.update(0.1)
    assert a.drain() == [], 'после прерывания движок продолжает писать'


def test_pause_changes_nothing():
    a = _attack()
    a.update(1.0)
    a.drain()
    before = (a.progress, a.phase, a.idx)
    # «пауза» — просто не вызываем update; состояние и вывод не меняются
    after = (a.progress, a.phase, a.idx)
    assert before == after, 'пауза (без вызова update) всё равно что-то меняет'
    assert a.drain() == [], 'на паузе движок продолжает писать'


def test_modes_change_pace_and_detail():
    stealth, normal, aggressive = (mode_params(m) for m in
                                   ('stealth', 'normal', 'aggressive'))
    assert stealth.delay_mult > normal.delay_mult > aggressive.delay_mult
    assert stealth.log_detail == 'low' and aggressive.log_detail == 'high'
    assert stealth.scan_count < normal.scan_count < aggressive.scan_count
    assert stealth.exploit_count < aggressive.exploit_count


def test_skills_speed_up_attack():
    base = mode_params('normal')
    skilled = mode_params('normal', {'hacking_speed': 6, 'minigame_difficulty': 5,
                                     'stealth': 5})
    assert skilled.delay_mult < base.delay_mult, 'навык скорости не влияет'
    assert skilled.minigame_mult < base.minigame_mult


def test_calc_setting_respected():
    def calc_lines(show):
        a = _attack(seed=4, calc=show)
        _run(a, limit=300)
        return sum(1 for ln in a.drain() if ln.kind == 'calc')

    assert calc_lines(False) == 0
    assert calc_lines(True) > 0


def test_single_frame_output_capped():
    """Один гигантский dt не должен выдавать тысячи строк разом."""
    a = _attack(mode='stealth', seed=9)
    a.update(500.0)                   # «зависли на 8 минут»
    assert len(a.drain()) < 40, 'за кадр вывалилась куча строк'


def test_own_address_easter_egg():
    a = _attack(targets=['127.0.0.1 / localhost'], seed=5)
    a.update(0.1)
    text = ' '.join(ln.text for ln in a.drain())
    assert 'сам себя' in text, 'пасхалка про localhost потерялась'


def test_failed_minigame_counts_as_failure():
    """При провале защиты цель не засчитывается успешной (баг legacy исправлен)."""
    a = _attack(targets=['a / a.com'], chance=100, seed=1)
    _run(a, limit=300)
    assert a.completed + a.failed == 1
    if a.failed:
        assert a.completed == 0
        assert 'пропущена' in ' '.join(ln.text for ln in a.drain())


# ─────────────────── лог ───────────────────
def _fontbook():
    import pygame
    from assets.fonts.fontloader import FontBook

    if not pygame.font.get_init():
        pygame.font.init()
    return pygame, FontBook(pygame)


def test_log_wraps_long_lines():
    import pygame
    from gamedev.logpanel import LogView

    pygame, book = _fontbook()
    log = LogView(pygame.Rect(0, 0, 300, 300), book, font_size=12)
    log.append([LogLine('слово ' * 60, 'info')])
    log._rewrap()
    assert len(log._wrapped) > 1, 'длинная строка не переносится'


def test_log_scroll_clamped_and_autoscroll():
    import pygame
    from gamedev.logpanel import LogView

    pygame, book = _fontbook()
    log = LogView(pygame.Rect(0, 0, 300, 100), book, font_size=12)
    for i in range(200):
        log.append([LogLine(f'строка {i}', 'info')])
    log._rewrap()

    log.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_HOME))
    assert log.scroll == max(0, len(log._wrapped) - log.visible_rows)
    assert log.autoscroll is False

    for _ in range(50):               # крутим колесо далеко за конец
        log.handle(pygame.event.Event(pygame.MOUSEWHEEL, y=-10))
    assert log.scroll == 0, 'прокрутка ниже конца'
    assert log.autoscroll is True


def test_wheel_direction():
    """Колесо вниз — к новым строкам, вверх — к старым (иначе лог «крутится назад»)."""
    import pygame
    from gamedev.logpanel import LogView

    pygame, book = _fontbook()
    log = LogView(pygame.Rect(0, 0, 300, 100), book)
    for i in range(100):
        log.append([LogLine(f'строка {i}', 'info')])

    log.handle(pygame.event.Event(pygame.MOUSEWHEEL, y=1))       # колесо вверх
    assert log.scroll > 0, 'колесо вверх не листает к старым строкам'
    assert log.autoscroll is False

    for _ in range(100):
        log.handle(pygame.event.Event(pygame.MOUSEWHEEL, y=-1))  # колесо вниз
    assert log.scroll == 0 and log.autoscroll is True


def test_log_caps_length():
    import pygame
    from gamedev.logpanel import LogView, MAX_LINES

    pygame, book = _fontbook()
    log = LogView(pygame.Rect(0, 0, 300, 300), book)
    for i in range(MAX_LINES + 500):
        log.append([LogLine(str(i), 'info')])
    assert len(log.lines) == MAX_LINES, 'лог растёт без предела'


def test_new_lines_keep_autoscroll():
    import pygame
    from gamedev.logpanel import LogView

    pygame, book = _fontbook()
    log = LogView(pygame.Rect(0, 0, 300, 100), book)
    for i in range(100):
        log.append([LogLine(f'строка {i}', 'info')])
    assert log.autoscroll and log.scroll == 0


# ─────────────────── связка с приложением ───────────────────
def test_app_attack_toggle_and_pause():
    import pygame
    from gamedev.app import App

    app = App()
    app.toggle_attack()
    assert app.attack is not None
    app._pump_attack(0.5)
    assert len(app.log.lines) > 8, 'лог не пополняется во время атаки'

    app.paused = True
    before = len(app.log.lines)
    app._pump_attack(1.0)
    assert len(app.log.lines) == before, 'на паузе лог продолжает расти'

    app.paused = False
    app.toggle_attack()               # СТОП
    assert app.attack is None
    pygame.quit()


def test_app_log_survives_theme_switch():
    import pygame
    from gamedev.app import App

    app = App()
    app.toggle_attack()
    app._pump_attack(1.0)
    count = len(app.log.lines)
    app._on_theme_change('ocean')
    app.draw()
    assert len(app.log.lines) == count, 'смена темы теряет лог'
    pygame.quit()


if __name__ == '__main__':
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith('test_')]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f'  ✓ {name}')
        except AssertionError as e:
            failed += 1
            print(f'  ✗ {name}: {e}')
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f'  ✗ {name}: {type(e).__name__}: {e}')
    print(f'\n{len(tests) - failed}/{len(tests)} тестов прошло')
    sys.exit(1 if failed else 0)
