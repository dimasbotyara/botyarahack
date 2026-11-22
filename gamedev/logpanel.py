"""Живой лог: цветные строки, прокрутка, перенос длинных строк.

Отличия от tkinter-версии:
  * прокрутка колесом и клавишами, автоскролл только когда ты внизу
    (в старой версии лог всегда прыгал в конец и «дёргался»);
  * кэш отрендеренных строк — можно держать тысячи строк без тормозов;
  * перенос длинных строк по словам, а не по символам.
"""

from __future__ import annotations

from collections import OrderedDict

import pygame

from .attack import LogLine, LOG_COLORS

MAX_LINES = 4000          # дальше старые строки уходят в архив
LINE_STEP = 18            # межстрочный интервал в логических пикселях
CACHE_SIZE = 1200         # отрендеренных строк в кэше


class LogView:
    """Прокручиваемый лог внутри прямоугольника."""

    def __init__(self, rect: pygame.Rect, book, font_size: int = 12):
        self.rect = rect
        self.book = book
        self.font_size = font_size
        self.lines: list[LogLine] = []
        self.scroll = 0            # сколько строк прокручено от конца
        self._wrapped: list[tuple[LogLine, str]] = []
        self._cache: OrderedDict[tuple[str, tuple, int], pygame.Surface] = OrderedDict()
        self._char_w = 7           # уточняется при первом переносе
        self._dirty_wrap = True
        self.visible_rows = max(1, (rect.height - 16) // LINE_STEP)
        self.autoscroll = True

    def resize(self, rect: pygame.Rect) -> None:
        self.rect = rect
        self.visible_rows = max(1, (rect.height - 16) // LINE_STEP)
        self._dirty_wrap = True
        self._rewrap()

    # ── данные ──────────────────────────────────────────────────────────
    def append(self, lines: list[LogLine]) -> None:
        if not lines:
            return
        self.lines.extend(lines)
        if len(self.lines) > MAX_LINES:
            del self.lines[:len(self.lines) - MAX_LINES]
        self._dirty_wrap = True
        self._rewrap()
        if self.autoscroll:
            self.scroll = 0

    def clear(self) -> None:
        self.lines.clear()
        self._wrapped.clear()
        self._cache.clear()
        self.scroll = 0
        self.autoscroll = True

    def _rewrap(self) -> None:
        """Разбить строки по ширине панели (словами, как wrap=WORD в tk)."""
        if not self._dirty_wrap:
            return
        width = self.rect.width - 24
        self._char_w = max(1, self.book.font('jetbrains', self.font_size).size('M')[0])
        per_line = max(8, width // self._char_w)

        wrapped: list[tuple[LogLine, str]] = []
        for line in self.lines:
            text = line.text
            if not text:
                wrapped.append((line, ''))
                continue
            if len(text) <= per_line:
                wrapped.append((line, text))
                continue
            # мягкий перенос по словам
            rest = text
            while rest:
                if len(rest) <= per_line:
                    wrapped.append((line, rest))
                    break
                chunk = rest[:per_line]
                cut = chunk.rfind(' ')
                if cut < per_line // 2:      # нет пробела — режем по символам
                    cut = per_line
                wrapped.append((line, rest[:cut]))
                rest = rest[cut:].lstrip(' ') if cut < per_line else rest[cut:]
        self._wrapped = wrapped
        self._dirty_wrap = False
        max_scroll = max(0, len(wrapped) - self.visible_rows)
        self.scroll = min(self.scroll, max_scroll)

    # ── взаимодействие ──────────────────────────────────────────────────
    def handle(self, event) -> bool:
        if event.type == pygame.MOUSEWHEEL:
            # y>0 — колесо от себя (вверх, к старым строкам), y<0 — вниз
            self._scroll_by(event.y * 3)
            return True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_PAGEUP:
                self._scroll_by(self.visible_rows)
                return True
            if event.key == pygame.K_PAGEDOWN:
                self._scroll_by(-self.visible_rows)
                return True
            if event.key == pygame.K_END:
                self.scroll, self.autoscroll = 0, True
                return True
            if event.key == pygame.K_HOME:
                self.scroll = max(0, len(self._wrapped) - self.visible_rows)
                self.autoscroll = False
                return True
        return False

    def _scroll_by(self, rows: int) -> None:
        """rows > 0 — вверх, к старым строкам (scroll растёт)."""
        self._rewrap()
        max_scroll = max(0, len(self._wrapped) - self.visible_rows)
        self.scroll = max(0, min(max_scroll, self.scroll + rows))
        self.autoscroll = self.scroll == 0

    # ── отрисовка ───────────────────────────────────────────────────────
    def _surface(self, book, text: str, color: tuple, size: int) -> pygame.Surface:
        key = (text, color, size)
        surf = self._cache.get(key)
        if surf is not None:
            self._cache.move_to_end(key)
            return surf
        surf = book.render(text, size, color)
        self._cache[key] = surf
        if len(self._cache) > CACHE_SIZE:
            self._cache.popitem(last=False)
        return surf

    def draw(self, surf, theme, book) -> None:
        self._rewrap()
        r = self.rect
        inner = r.inflate(-2, -2)
        pygame.draw.rect(surf, theme['bg_dark'], inner)

        # видимый срез строк: прокрутка отсчитывается от конца
        total = len(self._wrapped)
        end = total - self.scroll
        start = max(0, end - self.visible_rows)
        visible = self._wrapped[start:end]

        x0 = r.x + 10
        y = r.y + 8
        # подложка под текст, чтобы матрица не мешала читать
        clip_prev = surf.get_clip()
        surf.set_clip(inner)
        for line, text in visible:
            if text:
                color = theme[LOG_COLORS.get(line.kind, 'fg_main')]
                img = self._surface(book, text, color, self.font_size)
                if img.get_width() > inner.width - 8:
                    img = img.subsurface((0, 0, max(1, inner.width - 8),
                                          img.get_height())).copy()
                surf.blit(img, (x0, y))
            y += LINE_STEP
        surf.set_clip(clip_prev)

        # полоса прокрутки
        if total > self.visible_rows:
            track = pygame.Rect(r.right - 6, r.y + 4, 3, r.height - 8)
            pygame.draw.rect(surf, theme['bg_medium'], track)
            frac = self.visible_rows / total
            h = max(14, int(track.height * frac))
            max_scroll = total - self.visible_rows
            pos = 1.0 - (self.scroll / max_scroll if max_scroll else 0.0)
            top = track.y + int((track.height - h) * pos)
            pygame.draw.rect(surf, theme['fg_dim'], (track.x, top, track.width, h))

        # индикатор «ты не внизу»
        if self.scroll and total > self.visible_rows:
            badge = book.render(f'↓ {self.scroll}', 8, theme['bg_dark'])
            pad = 6
            box = pygame.Rect(r.right - badge.get_width() - pad * 2 - 10,
                              r.bottom - 20, badge.get_width() + pad * 2, 15)
            pygame.draw.rect(surf, theme['warning'], box)
            surf.blit(badge, (box.x + pad, box.y + 1))
