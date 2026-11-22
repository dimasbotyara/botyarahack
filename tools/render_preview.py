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
