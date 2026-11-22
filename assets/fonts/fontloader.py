"""Загрузчик офлайн-шрифтов с фолбэком по глифам.

Зачем: ни один шрифт не покрывает всё, что нужно игре.
Например JetBrains Mono (основной «терминальный») не содержит эмодзи,
а OpenMoji содержит эмодзи, но не содержит кириллицу.

Решение: основной шрифт + список фолбэк-шрифтов. При рендере каждый символ
берётся из первого шрифта, у которого он есть. Результат кэшируется.

Зависимостей нет (кроме pygame), весь код — чистый Python.
"""

from __future__ import annotations

from pathlib import Path

import pygame

FONTS_DIR = Path(__file__).resolve().parent

# ── Шрифты, которые лежат в репозитории ──────────────────────────────────
# Порядок в цепочке фолбэка важен: первый, у кого есть глиф, и рисует.
MAIN_FONTS = {
    'jetbrains': 'JetBrainsMono-Regular.ttf',
    'jetbrains_bold': 'JetBrainsMono-Bold.ttf',
    'noto_mono': 'NotoSansMono-Regular.ttf',
    'noto_sans': 'NotoSans-Regular.ttf',
    'plex_mono': 'IBMPlexMono-Regular.ttf',
}
FALLBACK_FONTS = {
    'symbols': 'NotoSansSymbols2-Regular.ttf',
    'emoji': 'OpenMoji-black-glyf.ttf',
}

# Символы, которые не рисуются сами по себе:
# U+FE0E/U+FE0F — вариативные селекторы (текстовый/эмодзи вид),
# U+200D — zero-width joiner, U+200B..U+200D — нулевые пробелы/пробел-склейка.
_INVISIBLE = frozenset('\ufe0e\ufe0f\u200b\u200c\u200d')

# Основная цепочка: терминальный моноширинный → символы → эмодзи
DEFAULT_CHAIN = ['jetbrains', 'symbols', 'emoji']
BOLD_CHAIN = ['jetbrains_bold', 'symbols', 'emoji']


class RenderedText(pygame.Surface):
    """Отрендеренная строка: растр в реальных пикселях, габариты — в логических.

    book.render рендерит текст в размере окна (без последующего
    масштабирования картинки), поэтому возвращает не обычную Surface,
    а подкласс с переопределёнными get_width/get_height → логические.
    При этом буфер остаётся в размере окна, и обычный
    pygame.Surface.blit на него просто кладёт пиксели (для тестов minigames),
    а Canvas распознаёт его по маркеру и не масштабирует.
    """

    is_rendered_text = True

    def __init__(self, real: pygame.Surface, scale_x: float, scale_y: float):
        w, h = real.get_size()
        # HD-буфер — реальный размер
        super().__init__((w, h), pygame.SRCALPHA)
        super().blit(real, (0, 0))
        self._sx = scale_x or 1.0
        self._sy = scale_y or 1.0
        self._lw = round(w / self._sx) if self._sx else w
        self._lh = round(h / self._sy) if self._sy else h

    @property
    def real(self) -> pygame.Surface:
        # совместимость: canvas ждёт .real
        return self

    def get_width(self) -> int:  # type: ignore[override]
        return self._lw

    def get_height(self) -> int:  # type: ignore[override]
        return self._lh

    def get_size(self) -> tuple[int, int]:  # type: ignore[override]
        return (self._lw, self._lh)

    def copy(self) -> 'RenderedText':  # type: ignore[override]
        w, h = pygame.Surface.get_size(self)
        hd = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.Surface.blit(hd, self, (0, 0))
        rt = RenderedText.__new__(RenderedText)
        pygame.Surface.__init__(rt, (w, h), pygame.SRCALPHA)
        pygame.Surface.blit(rt, hd, (0, 0))
        rt._sx = self._sx
        rt._sy = self._sy
        rt._lw = self._lw
        rt._lh = self._lh
        return rt

    def subsurface(self, rect) -> 'RenderedText':  # type: ignore[override]
        """Кроп в логических координатах (обрезка длинных строк)."""
        x, y, w, h = rect
        rw, rh = pygame.Surface.get_size(self)
        x0 = max(0, round(x * self._sx))
        y0 = max(0, round(y * self._sy))
        x1 = min(rw, max(x0 + 1, round((x + w) * self._sx)))
        y1 = min(rh, max(y0 + 1, round((y + h) * self._sy)))
        cw, ch = x1 - x0, y1 - y0
        hd_crop = pygame.Surface((cw, ch), pygame.SRCALPHA)
        pygame.Surface.blit(hd_crop, self, (0, 0), (x0, y0, cw, ch))
        rt = RenderedText.__new__(RenderedText)
        pygame.Surface.__init__(rt, (cw, ch), pygame.SRCALPHA)
        pygame.Surface.blit(rt, hd_crop, (0, 0))
        rt._sx = self._sx
        rt._sy = self._sy
        rt._lw = max(1, round(cw / self._sx)) if self._sx else cw
        rt._lh = max(1, round(ch / self._sy)) if self._sy else ch
        rt._lw = min(self._lw - x, rt._lw)
        rt._lh = min(self._lh - y, rt._lh)
        return rt


class FontBook:
    """Кэш pygame.Font + рендер строки с фолбэком по глифам."""

    #: сколько готовых поверхностей держим в памяти
    CACHE_LIMIT = 3000

    def __init__(self, pygame_module):
        self.pg = pygame_module
        self.render_scale = 1.0   # ставит Screen: пикселей окна на логический
        self._fonts: dict[tuple[str, int], object] = {}
        self._fonts_hd: dict[tuple[str, int], object] = {}
        self._coverage: dict[str, set[int]] = {}
        self._cache: dict[tuple, object] = {}
        self._cache_order: list[tuple] = []

    # ── создание шрифтов ────────────────────────────────────────────────
    def clear_cache(self) -> None:
        """Сбросить кэш (нужно после смены темы, если цвета больше не нужны)."""
        self._cache.clear()
        self._cache_order.clear()

    def font(self, name: str, size: int):
        key = (name, size)
        if key not in self._fonts:
            path = FONTS_DIR / MAIN_FONTS.get(name, FALLBACK_FONTS.get(name, name))
            if not path.exists():
                raise FileNotFoundError(f'шрифт не найден: {path}')
            self._fonts[key] = self.pg.font.Font(str(path), size)
        return self._fonts[key]

    def _font_hd(self, name: str, size: int):
        """Шрифт в реальном размере окна — для рендера без ресемплинга."""
        real = max(1, round(size * self.render_scale))
        key = (name, real)
        if key not in self._fonts_hd:
            path = FONTS_DIR / MAIN_FONTS.get(name, FALLBACK_FONTS.get(name, name))
            self._fonts_hd[key] = self.pg.font.Font(str(path), real)
        return self._fonts_hd[key]

    # ── покрытие глифов ─────────────────────────────────────────────────
    def covers(self, name: str, ch: str) -> bool:
        """Есть ли у шрифта глиф для символа (по ширине + запасному тесту)."""
        if name not in self._coverage:
            path = FONTS_DIR / MAIN_FONTS.get(name, FALLBACK_FONTS.get(name, name))
            self._coverage[name] = _read_codepoints(path)
        return ord(ch) in self._coverage[name]

    # ── рендер с фолбэком ───────────────────────────────────────────────
    def render(self, text: str, size: int, color, chain=None):
        """Рендерит строку, подставляя недостающие глифы из фолбэков.

        Результат кэшируется: интерфейс перерисовывает одни и те же
        подписи каждый кадр, а рендер шрифта — самая дорогая операция.
        Растр создаётся сразу в размере окна (render_scale) — текст
        остаётся чётким при любом масштабе окна.
        """
        chain = chain or DEFAULT_CHAIN
        key = (text, size, tuple(color), tuple(chain), round(self.render_scale, 3))
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        surf = self._render_uncached(text, size, color, chain)
        self._cache[key] = surf
        self._cache_order.append(key)
        if len(self._cache_order) > self.CACHE_LIMIT:
            old = self._cache_order.pop(0)
            self._cache.pop(old, None)
        return surf

    def _render_uncached(self, text, size, color, chain):
        pg = self.pg
        main = self._font_hd(chain[0], size)
        main_h = max(1, main.get_height())

        # разбиваем на куски «подряд идущие символы одного шрифта»
        chunks: list[list[str]] = []
        for ch in text:
            owner = next((n for n in chain if self.covers(n, ch)), chain[0])
            if chunks and chunks[-1][0] == owner:
                chunks[-1][1] += ch
            else:
                chunks.append([owner, ch])

        surfaces = []
        for owner, part in chunks:
            # вариативные селекторы (U+FE0F и др.) невидимы и дают
            # «Text has zero width» — выкидываем их перед рендером
            part = ''.join(c for c in part if c not in _INVISIBLE)
            if not part:
                continue
            font = self._font_hd(owner, size)
            surfaces.append(font.render(part, True, color))

        if not surfaces:
            return RenderedText(pg.Surface((0, main_h), pg.SRCALPHA),
                                self.render_scale, self.render_scale)

        total_w = sum(s.get_width() for s in surfaces)
        out = pg.Surface((total_w, main_h), pg.SRCALPHA)
        x = 0
        for s in surfaces:
            # выравниваем по базовой линии «на глаз»: по низу
            out.blit(s, (x, main_h - s.get_height()))
            x += s.get_width()
        return RenderedText(out, self.render_scale, self.render_scale)

    def size(self, text: str, size: int, chain=None) -> tuple[int, int]:
        """Ширина/высота строки с учётом фолбэков (для верстки)."""
        chain = chain or DEFAULT_CHAIN
        main = self.font(chain[0], size)
        w = 0
        for ch in text:
            owner = next((n for n in chain if self.covers(n, ch)), chain[0])
            w += self.font(owner, size).size(ch)[0]
        return w, max(1, main.get_height())


# ── разбор cmap без зависимостей ────────────────────────────────────────
def _read_codepoints(path: Path) -> set[int]:
    """Возвращает набор кодпоинтов, для которых в шрифте есть глиф.

    Читает таблицу cmap напрямую (форматы 4 и 12). Работает без fontTools.
    """
    import struct

    data = Path(path).read_bytes()
    if len(data) < 12 or data[:4] not in (b'\x00\x01\x00\x00', b'OTTO', b'true'):
        return set()

    num = struct.unpack('>H', data[4:6])[0]
    tables: dict[str, int] = {}
    for i in range(num):
        off = 12 + i * 16
        try:
            tag = data[off:off + 4].decode('latin-1')
        except UnicodeDecodeError:
            continue
        tables[tag] = struct.unpack('>II', data[off + 8:off + 16])[0]

    if 'cmap' not in tables:
        return set()

    base = tables['cmap']
    count = struct.unpack('>H', data[base + 2:base + 4])[0]
    cps: set[int] = set()

    for i in range(count):
        pid, eid, off = struct.unpack('>HHI', data[base + 4 + i * 8:base + 12 + i * 8])
        sub = base + off
        if sub + 2 > len(data):
            continue
        fmt = struct.unpack('>H', data[sub:sub + 2])[0]

        if fmt == 4 and (pid, eid) in ((3, 1), (0, 3)):
            seg_x2 = struct.unpack('>H', data[sub + 6:sub + 8])[0]
            seg = seg_x2 // 2
            ends = sub + 14
            starts = ends + seg_x2 + 2
            for j in range(seg):
                e = struct.unpack('>H', data[ends + 2 * j:ends + 2 * j + 2])[0]
                s = struct.unpack('>H', data[starts + 2 * j:starts + 2 * j + 2])[0]
                if s == 0xFFFF:
                    continue
                if e - s < 3000:          # защита от битых таблиц
                    cps.update(range(s, e + 1))
        elif fmt == 12:
            groups = struct.unpack('>I', data[sub + 12:sub + 16])[0]
            for j in range(groups):
                s, e, _ = struct.unpack('>III', data[sub + 16 + j * 12:sub + 28 + j * 12])
                if e - s < 3000:
                    cps.update(range(s, e + 1))

    return cps


if __name__ == '__main__':
    import pygame

    pygame.init()
    pygame.font.init()
    book = FontBook(pygame)

    sample = 'SECURITY EXPLOIT KIT ◆ ✓ ⚠ ⏱ ⚡ 💵 🎉 ╔═╗ ██ Привет'
    print('цепочка:', DEFAULT_CHAIN)
    print('размер строки:', book.size(sample, 20))
    surf = book.render(sample, 20, (0, 255, 0))
    print('отрендерено:', surf.get_size())

    out = Path('/tmp/fontdemo/fallback.png')
    out.parent.mkdir(exist_ok=True, parents=True)
    big = pygame.Surface((max(900, surf.get_width() + 40), 220))
    big.fill((8, 10, 8))
    big.blit(book.render(sample, 26, (0, 255, 0)).real, (20, 20))
    big.blit(book.render('Мини-игра: 🪨 Камень ✂️ Ножницы 📄 Бумага', 26, (255, 204, 0)).real, (20, 70))
    big.blit(book.render('Атака на github → ✓ Защита обойдена ⏱ 25 сек', 26, (0, 200, 255)).real, (20, 120))
    big.blit(book.render('♻ Сбросить профиль │ 👤 Анон │ 💵 $1234', 26, (200, 140, 255)).real, (20, 170))
    pygame.image.save(big, str(out))
    print('картинка:', out)
