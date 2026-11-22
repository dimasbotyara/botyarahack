"""Проверка офлайн-шрифтов: покрытие символов игры и фолбэк-рендер.

Запуск:  python3 tests/test_fonts.py
(нужен pygame; в песочнице ставится в venv — см. README)
"""
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FONTS = REPO / 'assets' / 'fonts'
sys.path.insert(0, str(FONTS))

from fontloader import FontBook, DEFAULT_CHAIN, MAIN_FONTS, FALLBACK_FONTS, _read_codepoints  # noqa: E402


def game_symbols():
    """Все не-ASCII символы, реально встречающиеся в игре."""
    src = (REPO / 'legacy' / 'hacker-app.py').read_text(encoding='utf-8')
    return sorted({ch for ch in src if ord(ch) > 127})


def test_all_fonts_present_and_valid():
    expected = list(MAIN_FONTS.values()) + list(FALLBACK_FONTS.values())
    for name in expected:
        path = FONTS / name
        assert path.exists(), f'нет шрифта: {name}'
        assert path.stat().st_size > 50_000, f'подозрительно маленький: {name}'
        head = path.read_bytes()[:4]
        assert head in (b'\x00\x01\x00\x00', b'OTTO', b'true'), f'не TrueType/OpenType: {name}'


def test_licenses_present():
    for lic in ('JetBrainsMono-OFL.txt', 'Noto-LICENSE.txt',
                'OpenMoji-LICENSE.txt', 'IBMPlex-OFL.txt'):
        p = FONTS / lic
        assert p.exists(), f'нет файла лицензии: {lic}'
        assert len(p.read_text(encoding='utf-8', errors='ignore')) > 100


def test_chain_covers_every_game_symbol():
    used = game_symbols()
    assert len(used) > 100, 'символы игры не собрались'
    union = set()
    for key in DEFAULT_CHAIN:
        union |= _read_codepoints(FONTS / (MAIN_FONTS.get(key) or FALLBACK_FONTS[key]))
    missing = [ch for ch in used if ord(ch) not in union]
    assert missing == [], f'не покрыты символы: {"".join(missing)}'


def test_cyrillic_in_main_font():
    cps = _read_codepoints(FONTS / MAIN_FONTS['jetbrains'])
    cyr = [chr(c) for c in range(0x0410, 0x0450)]
    missing = [ch for ch in cyr if ord(ch) not in cps]
    assert missing == [], f'в основном шрифте нет кириллицы: {missing}'


def test_box_drawing_in_main_font():
    """Псевдографика нужна для ASCII-арта и рамок."""
    cps = _read_codepoints(FONTS / MAIN_FONTS['jetbrains'])
    for ch in '█╔╗╚╝═║░─│':
        assert ord(ch) in cps, f'нет псевдографики: {ch}'


def test_emoji_in_fallback_only():
    main = _read_codepoints(FONTS / MAIN_FONTS['jetbrains'])
    emoji = _read_codepoints(FONTS / FALLBACK_FONTS['emoji'])
    for ch in '💵🎉🔐💣🧮💀👤🐱':
        assert ord(ch) not in main, f'{ch} неожиданно есть в основном шрифте'
        assert ord(ch) in emoji, f'эмодзи {ch} нет в OpenMoji'


def test_render_with_fallback():
    import os
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    import pygame
    pygame.init()
    pygame.font.init()
    book = FontBook(pygame)

    samples = [
        'SECURITY EXPLOIT KIT v5.0.0',
        '◆ ЦЕЛИ │ Взломано 3, провалено 1',
        '⚠ ЗАЩИТА: Бомба! ⏱ 25 сек ⚡',
        'Мини-игра: 🪨 Камень ✂️ Ножницы 📄 Бумага',
        '♻ Сбросить профиль │ 👤 Анон │ 💵 $1234',
        '██╗  ██╗ █████╗  ██████╗',
    ]
    for text in samples:
        surf = book.render(text, 20, (0, 255, 0))
        assert surf.get_width() > 0, f'нулевая ширина: {text!r}'
        assert surf.get_height() > 0
        w, h = book.size(text, 20)
        assert w > 0 and h > 0

    # вариативные селекторы не должны ронять рендер
    book.render('✂️ ⚠️ ♻️', 20, (255, 255, 255))
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
