#!/usr/bin/env python3
"""Универсальный запуск: старый tkinter или новый pygame.

    python3 run.py            # новая pygame-версия (по умолчанию)
    python3 run.py pygame     # то же самое
    python3 run.py legacy     # старый tkinter-интерфейс из legacy/
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run_pygame():
    try:
        import pygame  # noqa: F401
    except ImportError:
        print('Нужен pygame:  python3 -m venv .venv && .venv/bin/pip install pygame')
        print('(подробнее — requirements.txt)')
        return 1
    from gamedev.app import main
    return main()


def run_legacy():
    import runpy
    sys.argv = [str(ROOT / 'legacy' / 'hacker-app.py')]
    runpy.run_path(str(ROOT / 'legacy' / 'hacker-app.py'), run_name='__main__')
    return 0


def main():
    what = sys.argv[1].lower() if len(sys.argv) > 1 else 'pygame'
    if what == 'legacy':
        return run_legacy()
    if what in ('pygame', 'new', ''):
        return run_pygame()
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
