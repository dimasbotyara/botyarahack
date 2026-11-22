"""Рендер кадров pygame-интерфейса в PNG — без живого окна.

Нужен для двух вещей:
  1) проверить вёрстку в CI/песочнице (нет дисплея);
  2) быстро посмотреть, как выглядит интерфейс, не запуская игру.

Запуск:
    python3 tools/render_preview.py [--out assets/preview]
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def render(out_dir: Path) -> list[Path]:
    import pygame

    from gamedev import config
    from gamedev.app import App

    out_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []

    app = App()
    # Превью всегда в 1× — без масштаба окна, чтобы артефакты сжатия не
    # портили картинку. В игре масштаб задаёт окно, здесь фиксируем его.
    from gamedev.screen import Screen
    app.window = pygame.display.set_mode((config.LOGICAL_W, config.LOGICAL_H))
    app.screen = Screen(app.window, smooth=True, book=app.book)
    # dummy-монитор 1024×768 резал бы окно — фиксируем 1× вручную
    from gamedev.display import WindowSize
    app.size_info = WindowSize(width=config.LOGICAL_W, height=config.LOGICAL_H, scale=1.0, mode='1.0')

    # кадр 1: главный экран, тёмная базовая тема
    app.time = 1.5
    app.draw()
    frame = app.screen.surface.copy()
    p = out_dir / 'stage1-main-matrix.png'
    pygame.image.save(frame, str(p))
    saved.append(p)

    # кадр 2: окно настроек поверх
    app.open_menu()
    app.draw()
    p = out_dir / 'stage1-settings.png'
    pygame.image.save(app.screen.surface.copy(), str(p))
    saved.append(p)

    # кадр 3: открытый список тем (проверяем, что выпадашка поверх панелей)
    app.theme_dd.open = True
    app.draw()
    p = out_dir / 'stage1-settings-dropdown.png'
    pygame.image.save(app.screen.surface.copy(), str(p))
    saved.append(p)

    # кадр 4: другая тема — проверяем, что перекрашивается всё
    app.theme_dd.open = False
    app._on_theme_change('cyberpunk')
    app.menu_open = False
    app.draw()
    p = out_dir / 'stage1-main-cyberpunk.png'
    pygame.image.save(app.screen.surface.copy(), str(p))
    saved.append(p)

    # кадр 5: маленькое окно (эмулируем компактный режим)
    app._on_theme_change('ocean')
    app.settings.window_scale = '0.6'
    app.apply_window_size()
    app.draw()
    p = out_dir / 'stage1-small-window.png'
    pygame.image.save(app.screen.surface.copy(), str(p))
    saved.append(p)

    # ── Этап 2: живой лог во время атаки ──
    app._on_theme_change('matrix')
    app.settings.window_scale = '0.75'
    app.apply_window_size()
    app.log.clear()
    app._welcome()
    app.set_mode('aggressive')
    app.attack = __import__('gamedev.attack', fromlist=['Attack']).Attack(
        targets=['github / github.com', 'nasa / nasa.gov'],
        params=__import__('gamedev.attack', fromlist=['mode_params'])
        .mode_params('aggressive'),
        minigame_chance=70, show_calculations=True,
        rng=__import__('random').Random(3))
    for _ in range(300):
        app.attack.update(0.1)
    app.log.append(app.attack.drain())
    app.draw()
    p = out_dir / 'stage2-attack-log.png'
    pygame.image.save(app.screen.surface.copy(), str(p))
    saved.append(p)

    # кадр 7: пауза посреди атаки
    app.paused = True
    app.draw()
    p = out_dir / 'stage2-paused.png'
    pygame.image.save(app.screen.surface.copy(), str(p))
    saved.append(p)

    # ── Этап 3: цели с очередью, карта, профиль ──
    app.paused = False
    app.attack = None
    app.typing_name = False
    app.player.name = 'NEO'
    app.player.money = 2450
    app.player.hacks_completed = 17
    app.player.hacks_failed = 3
    app.player.data_stolen_gb = 214.6
    app.player.skill_points = 4
    app.player.skills['hacking_speed'] = 3
    app.log.clear()
    app._welcome()
    app.settings.attack_mode = 'normal'
    for name in ('github / github.com', 'nasa / nasa.gov', 'vk / vk.ru'):
        app.targets.toggle(name)
    for _ in range(6):
        app.map.strike()
    for _ in range(40):
        app.map.update(0.12)
    app.draw()
    p = out_dir / 'stage3-targets-map-profile.png'
    pygame.image.save(app.screen.surface.copy(), str(p))
    saved.append(p)

    # кадр 9: окно навыков
    app.skills_open = True
    app.draw()
    p = out_dir / 'stage3-skills.png'
    pygame.image.save(app.screen.surface.copy(), str(p))
    saved.append(p)

    # кадр 10: поиск по целям
    app.skills_open = False
    app.search_active = True
    app.targets.type_char('git')
    app.draw()
    p = out_dir / 'stage3-target-search.png'
    pygame.image.save(app.screen.surface.copy(), str(p))
    saved.append(p)

    # ── Этап 4: мини-игры ──
    app.search_active = False
    app.targets.filter_text = ''
    app.settings.window_scale = '0.8'
    app.apply_window_size()
    app._resize_log()
    app._layout_panels(config.LOGICAL_W, config.LOGICAL_H)
    app.attack_btn.rect = pygame.Rect(
        8 + 12, config.LOGICAL_H - 74 - 58, 300 - 24, 36)

    from gamedev.minigames import make_game
    import random as _random

    app.attack = __import__('gamedev.attack', fromlist=['Attack']).Attack(
        targets=['github / github.com'],
        params=__import__('gamedev.attack', fromlist=['mode_params'])
        .mode_params('normal'),
        minigame_chance=100, show_calculations=True, rng=_random.Random(5))
    for _ in range(400):
        app.attack.update(0.05)
        if app.attack.minigame:
            break
    app.log.append(app.attack.drain())

    for name, fname in [('Лабиринт', 'stage4-maze'),
                        ('Бомба', 'stage4-bomb'),
                        ('Набор кода', 'stage4-typecode'),
                        ('Сейф', 'stage4-safe')]:
        app.minigame = make_game('github / github.com', _random.Random(7), name=name)
        for _ in range(15):
            app.minigame.update(0.08)
        if name == 'Набор кода':
            app.minigame.typed = app.minigame.code[:5] + 'x'
        if name == 'Сейф':
            app.minigame.typed = '42'
            app.minigame.history = [77, 23]
            app.minigame.lo, app.minigame.hi = 24, 76
        app.draw()
        p = out_dir / f'{fname}.png'
        pygame.image.save(app.screen.surface.copy(), str(p))
        saved.append(p)

    # ── Этап 5: история атак и консоль ──
    app.minigame = None
    app.attack = None
    for i in range(8):
        app.history_entries = __import__(
            'gamedev.history', fromlist=['add']).add(
            app.history_entries, targets=3, completed=2 + (i % 2),
            failed=i % 3, mode=['stealth', 'normal', 'aggressive'][i % 3])
    app.history_open = True
    app.draw()
    p = out_dir / 'stage5-history.png'
    pygame.image.save(app.screen.surface.copy(), str(p))
    saved.append(p)

    app.history_open = False
    app.console.open = True
    for cmd in ('status', 'theme cyberpunk', 'mode aggressive'):
        app.console.input = cmd
        app.console.execute(app)
    app.draw()
    p = out_dir / 'stage5-console.png'
    pygame.image.save(app.screen.surface.copy(), str(p))
    saved.append(p)

    # кадр: победа в мини-игре (чистый лабиринт с исходом)
    app.minigame = make_game('github / github.com', _random.Random(7), name='Лабиринт')
    for _ in range(15):
        app.minigame.update(0.08)
    app.minigame.result = True
    app.minigame.result_text = '🎉 ВЫХОД НАЙДЕН за 14 ходов'
    app.draw()
    p = out_dir / 'stage4-maze-win.png'
    pygame.image.save(app.screen.surface.copy(), str(p))
    saved.append(p)

    print(f'окно: {app.size_info.describe()}, монитор: {app.monitor}')
    pygame.quit()
    return saved


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=str(ROOT / 'assets' / 'preview'))
    args = ap.parse_args()
    for path in render(Path(args.out)):
        print('  сохранено:', path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)
    return 0


if __name__ == '__main__':
    sys.exit(main())
