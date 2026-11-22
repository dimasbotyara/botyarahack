"""Тесты Этапа 1 (каркас pygame): размеры окна, настройки, вёрстка.

Запуск:  python3 tests/test_gamedev.py
Требует pygame (в песочнице — venv, см. requirements.txt).
"""
import json
import os
import struct
import sys
import tempfile
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import ast  # noqa: E402

from gamedev import config  # noqa: E402
from gamedev.display import compute_size, normalize_mode, available_modes  # noqa: E402
from gamedev.settings import Settings  # noqa: E402


# ─────────────────── конфиг не разъехался с legacy ───────────────────
def _legacy_values():
    src = (REPO / 'legacy' / 'hacker-app.py').read_text(encoding='utf-8')
    tree = ast.parse(src)
    out = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name):
            if n.targets[0].id in ('THEMES', 'ASCII_LOGOS'):
                out[n.targets[0].id] = ast.literal_eval(n.value)
    return out


def test_config_matches_legacy():
    legacy = _legacy_values()
    assert config.THEMES == legacy['THEMES'], 'THEMES разъехались с legacy'
    assert str(config.ASCII_LOGOS) == str(legacy['ASCII_LOGOS']), 'ASCII_LOGOS разъехались'


def test_all_themes_have_same_keys():
    keys = {frozenset(t) for t in config.THEMES.values()}
    assert len(keys) == 1, 'у тем разный набор ключей'
    assert len(next(iter(keys))) == 21


# ─────────────────── размер окна: авто и пресеты ───────────────────
def test_auto_fits_every_monitor():
    monitors = [(800, 600), (1024, 768), (1280, 720), (1366, 768), (1440, 900),
                (1920, 1080), (2560, 1440), (3440, 1440), (3840, 2160)]
    for w, h in monitors:
        size = compute_size(w, h, 'auto')
        assert size.width <= w and size.height <= h, f'{w}x{h}: окно вылезло ({size.describe()})'
        assert size.width >= config.LOGICAL_W * config.MIN_SCALE
        assert size.is_auto


def test_presets_never_overflow():
    for key, _label in config.WINDOW_PRESETS:
        for w, h in [(800, 600), (1024, 768), (1366, 768), (1920, 1080)]:
            size = compute_size(w, h, key)
            assert size.width <= w, f'{key} на {w}x{h} шире экрана'
            assert size.height <= h, f'{key} на {w}x{h} выше экрана'


def test_auto_scales_up_on_big_screens():
    small = compute_size(1366, 768, 'auto')
    big = compute_size(3840, 2160, 'auto')
    assert big.scale > small.scale, 'на 4K должно быть крупнее'
    assert big.scale <= config.AUTO_MAX_SCALE, 'авто-режим не должен раздуваться'


def test_aspect_ratio_kept():
    logical_ratio = config.LOGICAL_W / config.LOGICAL_H
    for w, h in [(800, 600), (1366, 768), (1920, 1080), (3840, 2160)]:
        size = compute_size(w, h, 'auto')
        assert abs(size.width / size.height - logical_ratio) < 0.01, 'пропорции поехали'


def test_normalize_mode():
    for bad in ('', None, 'abc', '99', 0.75, '-1'):
        assert normalize_mode(bad) == 'auto'
    for key, _ in config.WINDOW_PRESETS:
        assert normalize_mode(key) == key
    assert len(available_modes()) == len(config.WINDOW_PRESETS)


# ─────────────────── настройки: сохранение и валидация ───────────────────
def test_settings_roundtrip(tmp_path=None):
    d = Path(tempfile.mkdtemp())
    path = d / 's.json'
    s = Settings(theme='ocean', minigame_chance=55, window_scale='0.75',
                 attack_mode='stealth', smooth_scaling=False)
    assert s.save(path)
    loaded = Settings.load(path)
    assert loaded.theme == 'ocean'
    assert loaded.minigame_chance == 55
    assert loaded.window_scale == '0.75'
    assert loaded.attack_mode == 'stealth'
    assert loaded.smooth_scaling is False


def test_settings_survive_garbage():
    d = Path(tempfile.mkdtemp())
    path = d / 'bad.json'
    path.write_text('{"theme": "нет-такой", "minigame_chance": "много", '
                    '"window_scale": "гигантский", "attack_mode": 42}', encoding='utf-8')
    s = Settings.load(path)
    assert s.theme == 'matrix'
    assert s.minigame_chance == 20
    assert s.window_scale == 'auto'
    assert s.attack_mode == 'normal'


def test_settings_broken_json():
    d = Path(tempfile.mkdtemp())
    path = d / 'broken.json'
    path.write_text('{не json', encoding='utf-8')
    s = Settings.load(path)          # не должно падать
    assert s.theme == 'matrix'


def test_chance_clamped():
    for raw, expected in ((-50, 10), (0, 10), (5, 10), (20, 20), (100, 100), (999, 100)):
        s = Settings(minigame_chance=raw).normalized()
        assert s.minigame_chance == expected, (raw, s.minigame_chance)


def test_settings_compatible_with_legacy_keys():
    """Файл настроек общий с tkinter-версией — старые поля не должны теряться."""
    legacy = {'theme': 'blood', 'minigame_chance': 40, 'glitch_enabled': False,
              'show_calculations': False, 'attack_mode': 'aggressive'}
    s = Settings.from_dict(legacy)
    assert s.theme == 'blood'
    assert s.minigame_chance == 40
    assert s.glitch_enabled is False
    assert s.attack_mode == 'aggressive'
    assert s.window_scale == 'auto'      # новое поле — дефолт
    assert s.smooth_scaling is True      # плавное масштабирование — по умолчанию вкл


def test_smooth_scaling_on_by_default():
    s = Settings()
    assert s.smooth_scaling is True, 'плавное масштабирование должно быть включено'
    s = Settings(smooth_scaling=False).normalized()
    assert s.smooth_scaling is False


# ─────────────────── окно: только из настроек ───────────────────
def test_window_not_manually_resizable():
    """RESIZABLE не должен включаться — размер только через настройки."""
    tree = ast.parse((REPO / 'gamedev' / 'app.py').read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        # pygame.RESIZABLE как аргумент set_mode(...) | флаг
        if isinstance(node, ast.Attribute) and node.attr == 'RESIZABLE':
            raise AssertionError('окно можно тянуть мышью — так не договаривались')
        if isinstance(node, ast.Name) and node.id == 'RESIZABLE':
            raise AssertionError('окно можно тянуть мышью — так не договаривались')
    funcs = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    assert 'apply_window_size' in funcs, 'смена размера из настроек должна применяться'


def test_app_boots_and_renders():
    import pygame
    from gamedev.app import App

    app = App()
    assert app.window.get_width() > 0
    assert app.size_info.width <= app.monitor[0] + 1

    app.draw()
    frame = app.screen.surface.copy()
    assert frame.get_size() == app.window.get_size()

    # на кадре не должно быть «пустого» экрана: панели и текст рисуются
    w, h = frame.get_size()
    colors = {tuple(frame.get_at((x, y)))[:3]
              for x in range(0, w, 37)
              for y in range(0, h, 41)}
    assert len(colors) > 3, 'кадр подозрительно одноцветный'

    # меню открывается и рисуется
    app.open_menu()
    app.draw()
    assert len(app.menu_widgets) == 6
    pygame.quit()


def test_theme_switch_recolors_immediately():
    import pygame
    from gamedev.app import App

    app = App()
    app.draw()
    before = tuple(app.screen.surface.get_at((5, 5)))[:3]
    app._on_theme_change('blood')
    app.draw()
    after = tuple(app.screen.surface.get_at((5, 5)))[:3]
    assert before != after, 'тема не применилась сразу'
    assert app.theme.key == 'blood'
    pygame.quit()


def test_size_change_applies_new_window():
    import pygame
    from gamedev.app import App

    app = App()
    old = app.window.get_size()
    app._on_size_change('0.6')
    new = app.window.get_size()
    assert new != old
    assert new[0] <= app.monitor[0] and new[1] <= app.monitor[1]
    pygame.quit()


# ─────────────────── плавное масштабирование ───────────────────
def test_screen_smooth_scaling_modes():
    """Плавное рисует сразу в окно, быстрое — через логический растр."""
    import pygame
    from gamedev.screen import Screen
    from assets.fonts.fontloader import FontBook

    pygame.display.init()
    pygame.font.init()

    # плавное: холст совпадает с окном
    win = pygame.display.set_mode((4, 4))
    book = FontBook(pygame)
    scr = Screen(win, logical_size=(2, 2), smooth=True, book=book)
    assert scr.surface.get_size() == (2, 2), 'Canvas отдаёт логический размер'
    assert scr.surface.real.get_size() == (4, 4), 'плавный режим — холст = окно'
    scr.surface.fill((0, 0, 0))
    scr.surface.fill((255, 255, 255), pygame.Rect(0, 0, 1, 1))
    # без blit_to_window уже видно в окне — резкие пиксели, без размытия
    colors = {tuple(win.get_at((x, y)))[:3] for x in range(4) for y in range(4)}
    assert (255, 255, 255) in colors and (0, 0, 0) in colors
    assert colors <= {(255, 255, 255), (0, 0, 0)}, f'плавный режим размыл: {colors}'

    # быстрый: логический растр + nearest upscale
    win2 = pygame.display.set_mode((4, 4))
    scr2 = Screen(win2, logical_size=(2, 2), smooth=False, book=book)
    assert scr2.surface.real.get_size() == (2, 2), 'быстрый — растр логический'
    scr2.surface.fill((0, 0, 0))
    scr2.surface.fill((255, 255, 255), pygame.Rect(0, 0, 1, 1))
    scr2.surface.fill((255, 255, 255), pygame.Rect(1, 1, 1, 1))
    # до blit_to_window окно ещё чёрное
    scr2.blit_to_window()
    colors = {tuple(win2.get_at((x, y)))[:3] for x in range(4) for y in range(4)}
    assert colors <= {(255, 255, 255), (0, 0, 0)}, f'быстрый размыл: {colors}'
    # плавный после переключения снова совпадает с окном
    scr2.smooth = True
    assert scr2.surface.real.get_size() == (4, 4)
    pygame.quit()


def test_canvas_scales_coordinates():
    """Canvas переводит логические координаты в реальные без щелей."""
    import pygame
    from gamedev.canvas import Canvas

    pygame.display.init()
    real = pygame.Surface((4, 4))
    real.fill((0, 0, 0))
    cv = Canvas(real, 2, 2)
    assert cv.get_size() == (2, 2)
    assert cv.sx == 2.0 and cv.sy == 2.0
    # прямоугольник 1×1 логический → 2×2 реальных
    cv.fill((255, 255, 255), pygame.Rect(0, 0, 1, 1))
    assert tuple(real.get_at((0, 0)))[:3] == (255, 255, 255)
    assert tuple(real.get_at((1, 1)))[:3] == (255, 255, 255)
    assert tuple(real.get_at((2, 0)))[:3] == (0, 0, 0)
    assert tuple(real.get_at((0, 2)))[:3] == (0, 0, 0)
    # get_at через Canvas тоже масштабируется
    assert tuple(cv.get_at((0, 0)))[:3] == (255, 255, 255)
    assert tuple(cv.get_at((1, 0)))[:3] == (0, 0, 0)
    pygame.quit()


def test_glyph_rendered_in_window_size():
    """book.render отдаёт растр в размере окна, логические габариты совпадают."""
    import pygame
    from gamedev.screen import Screen
    from assets.fonts.fontloader import FontBook

    pygame.display.init()
    pygame.font.init()
    win = pygame.display.set_mode((2304, 1452))  # 2× логического
    book = FontBook(pygame)
    scr = Screen(win, smooth=True, book=book)  # scale 2.0
    assert book.render_scale == 2.0
    txt = book.render('Привет', 14, (0, 255, 0))
    # логическая ширина близка к book.size (разный хинтинг на HD даёт погрешность)
    logical = book.size('Привет', 14)[0]
    assert abs(txt.get_width() - logical) <= 4, f'логическая ширина уплыла: {txt.get_width()} vs {logical}'
    # HD-растр больше логического (2×)
    import pygame as _pg
    assert _pg.Surface.get_width(txt) >= txt.get_width() * 1.8
    # subsurface/copy делегируют и сохраняют масштаб
    cut = txt.subsurface((0, 0, txt.get_width(), txt.get_height()))
    assert cut.get_width() == txt.get_width()
    assert _pg.Surface.get_width(cut) > 0
    # при другом масштабе — другой растр (кэш по scale)
    win2 = _pg.display.set_mode((1152, 726))
    scr2 = Screen(win2, smooth=True, book=book)
    assert book.render_scale == 1.0
    txt2 = book.render('Привет', 14, (0, 255, 0))
    assert _pg.Surface.get_width(txt2) < _pg.Surface.get_width(txt)
    _pg.quit()


def test_smooth_toggle_applies_live():
    import pygame
    from gamedev.app import App

    app = App()
    assert app.screen.smooth is True
    app._on_smooth_change(False)
    assert app.settings.smooth_scaling is False
    assert app.screen.smooth is False, 'переключатель должен действовать сразу'
    app.open_menu()
    assert app.smooth_cb.checked is False
    app._on_smooth_change(True)
    assert app.screen.smooth is True
    pygame.quit()


# ─────────────────── оверлеи и общий кэш без set_alpha ───────────────────
def test_no_set_alpha_in_game_code():
    """set_alpha + blit даёт чёрные квадраты поверх текста на части платформ.

    Затемнение оверлеев идёт через dim_surface (BLEND_RGB_MULT),
    яркость глифов — через цвет. Вызовов set_alpha в коде игры нет.
    """
    for path in sorted((REPO / 'gamedev').glob('*.py')):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == 'set_alpha':
                raise AssertionError(
                    f'{path.name}:{node.lineno}: set_alpha должен быть выключен')


def test_rain_does_not_mutate_font_cache():
    """Дождь рисует глифы из общего кэша FontBook — менять их нельзя."""
    import pygame
    from gamedev.app import App

    app = App()
    sample = app.book.render('X', 13, (0, 204, 0))
    before = sample.get_alpha()
    for _ in range(30):
        app.matrix.update(1 / 60)
        app.matrix.draw(app.screen.surface, app.theme, app.book)
    fresh = app.book.render('X', 13, (0, 204, 0))
    assert fresh is sample, 'кэш должен вернуть ту же поверхность'
    assert fresh.get_alpha() == before, \
        'матричный дождь испортил общий кэш шрифтов (set_alpha)'
    pygame.quit()


def test_click_outside_menu_closes_it():
    import pygame
    from gamedev.app import App

    app = App()
    app.typing_name = False
    app.open_menu()

    # клик внутри оверлея — меню остаётся
    inside = app.screen.to_window(app.menu_rect.center)
    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {'pos': inside, 'button': 1}))
    app.handle_events()
    assert app.menu_open, 'клик внутри оверлея не должен закрывать меню'

    # клик за пределами — закрывает
    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {'pos': (2, 2), 'button': 1}))
    app.handle_events()
    assert not app.menu_open, 'клик за пределами оверлея должен закрывать меню'
    pygame.quit()


def test_click_outside_history_closes_it():
    import pygame
    from gamedev.app import App

    app = App()
    app.typing_name = False
    app.history_open = True
    app.history_entries = []

    inside = app.screen.to_window(app._history_rect().center)
    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {'pos': inside, 'button': 1}))
    app.handle_events()
    assert app.history_open, 'клик внутри истории не должен закрывать её'

    pygame.event.post(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {'pos': (2, 2), 'button': 1}))
    app.handle_events()
    assert not app.history_open, 'клик за пределами истории должен закрывать её'
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
