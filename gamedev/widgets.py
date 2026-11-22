"""Виджеты pygame в терминальном стиле старого интерфейса.

Все координаты — логические (см. gamedev/screen.py).
Виджеты не знают про темы напрямую: цвет приходит из Theme.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import pygame

from .theme import Theme


@dataclass
class Widget:
    rect: pygame.Rect
    visible: bool = True
    hovered: bool = False
    active: bool = False

    def contains(self, pos) -> bool:
        return self.visible and self.rect.collidepoint(pos)

    def handle(self, event) -> bool:
        return False

    def draw(self, surf, theme: Theme, book) -> None:
        pass


@dataclass
class Label(Widget):
    text: str = ''
    size: int = 10
    color_key: str = 'fg_main'
    bold: bool = False

    def draw(self, surf, theme: Theme, book) -> None:
        if not self.visible:
            return
        chain = ['jetbrains_bold', 'symbols', 'emoji'] if self.bold else None
        img = book.render(self.text, self.size, theme[self.color_key], chain=chain)
        surf.blit(img, (self.rect.x, self.rect.y))


@dataclass
class Button(Widget):
    text: str = ''
    size: int = 10
    on_click: Callable[[], None] | None = None
    accent: bool = False
    _pressed: bool = False

    def handle(self, event) -> bool:
        if not self.visible:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.contains(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.contains(event.pos):
                self._pressed = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._pressed and self.contains(event.pos):
                self._pressed = False
                if self.on_click:
                    self.on_click()
                return True
            self._pressed = False
        return False

    def draw(self, surf, theme: Theme, book) -> None:
        if not self.visible:
            return
        bg_key = 'bg_light' if self.hovered else 'bg_medium'
        if self._pressed:
            bg_key = 'bg_dark'
        pygame.draw.rect(surf, theme[bg_key], self.rect)
        border = theme['accent'] if (self.hovered or self.accent) else theme['border']
        pygame.draw.rect(surf, border, self.rect, 1)

        color = theme['accent'] if self.accent else theme['fg_main']
        img = book.render(self.text, self.size, color)
        surf.blit(img, (self.rect.centerx - img.get_width() // 2,
                        self.rect.centery - img.get_height() // 2))


@dataclass
class Panel(Widget):
    """Рамка с заголовком — как «◆ ЦЕЛИ» в старом интерфейсе."""

    title: str = ''
    bg_key: str = 'bg_dark'

    def draw(self, surf, theme: Theme, book) -> None:
        if not self.visible:
            return
        pygame.draw.rect(surf, theme[self.bg_key], self.rect)
        pygame.draw.rect(surf, theme['border'], self.rect, 1)
        if self.title:
            img = book.render(self.title, 12, theme['fg_main'])
            surf.blit(img, (self.rect.x + 8, self.rect.y + 6))
            pygame.draw.line(surf, theme['border'],
                             (self.rect.x + 1, self.rect.y + 24),
                             (self.rect.right - 1, self.rect.y + 24))


@dataclass
class Dropdown(Widget):
    """Выпадающий список: (значение, подпись)[]."""

    options: list = field(default_factory=list)
    value: str = ''
    open: bool = False
    on_change: Callable[[str], None] | None = None
    _hover_index: int = -1

    ROW_H = 22

    def _rows(self) -> list[pygame.Rect]:
        rows = []
        for i in range(len(self.options)):
            rows.append(pygame.Rect(self.rect.x,
                                    self.rect.bottom + i * self.ROW_H,
                                    self.rect.width, self.ROW_H))
        return rows

    def _label_for(self, value: str) -> str:
        for key, label in self.options:
            if key == value:
                return label
        return str(value)

    def handle(self, event) -> bool:
        if not self.visible:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.contains(event.pos)
            if self.open:
                self._hover_index = -1
                for i, r in enumerate(self._rows()):
                    if r.collidepoint(event.pos):
                        self._hover_index = i
                        break
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.contains(event.pos):
                self.open = not self.open
                return True
            if self.open:
                for i, r in enumerate(self._rows()):
                    if r.collidepoint(event.pos):
                        self.value = self.options[i][0]
                        self.open = False
                        if self.on_change:
                            self.on_change(self.value)
                        return True
                self.open = False
        return False

    def draw(self, surf, theme: Theme, book) -> None:
        if not self.visible:
            return
        # сама «кнопка»
        bg = theme['bg_light'] if self.hovered else theme['bg_medium']
        pygame.draw.rect(surf, bg, self.rect)
        pygame.draw.rect(surf, theme['accent'] if self.open else theme['border'],
                         self.rect, 1)
        img = book.render(self._label_for(self.value), 11, theme['fg_main'])
        surf.blit(img, (self.rect.x + 8, self.rect.centery - img.get_height() // 2))
        # стрелка
        ax, ay = self.rect.right - 14, self.rect.centery - 2
        pygame.draw.polygon(surf, theme['fg_dim'],
                            [(ax - 4, ay - 2), (ax + 4, ay - 2), (ax, ay + 3)])

        if not self.open:
            return
        # список поверх всего
        rows = self._rows()
        total_h = self.ROW_H * len(rows)
        panel = pygame.Rect(self.rect.x, self.rect.bottom, self.rect.width, total_h)
        pygame.draw.rect(surf, theme['bg_dark'], panel)
        pygame.draw.rect(surf, theme['border'], panel, 1)
        for i, r in enumerate(rows):
            if i == self._hover_index:
                pygame.draw.rect(surf, theme['bg_light'], r)
            if self.options[i][0] == self.value:
                pygame.draw.rect(surf, theme['accent'], r, 1)
            img = book.render(self.options[i][1], 11, theme['fg_main'])
            surf.blit(img, (r.x + 8, r.centery - img.get_height() // 2))


@dataclass
class Checkbox(Widget):
    text: str = ''
    checked: bool = False
    on_change: Callable[[bool], None] | None = None

    def handle(self, event) -> bool:
        if not self.visible:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.contains(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.contains(event.pos):
                self.checked = not self.checked
                if self.on_change:
                    self.on_change(self.checked)
                return True
        return False

    def draw(self, surf, theme: Theme, book) -> None:
        if not self.visible:
            return
        box = pygame.Rect(self.rect.x, self.rect.y, 16, 16)
        pygame.draw.rect(surf, theme['bg_medium'], box)
        pygame.draw.rect(surf, theme['accent'] if self.hovered else theme['border'],
                         box, 1)
        if self.checked:
            pygame.draw.line(surf, theme['accent'], (box.x + 3, box.y + 8), (box.x + 7, box.y + 12), 2)
            pygame.draw.line(surf, theme['accent'], (box.x + 7, box.y + 12), (box.x + 13, box.y + 4), 2)
        img = book.render(self.text, 11, theme['fg_main'])
        surf.blit(img, (box.right + 8, self.rect.centery - img.get_height() // 2))


@dataclass
class Slider(Widget):
    """Горизонтальный слайдер для чисел (например, шанс мини-игры)."""

    min_value: int = 10
    max_value: int = 100
    value: int = 20
    on_change: Callable[[int], None] | None = None
    _dragging: bool = False

    def _knob_x(self) -> int:
        span = max(1, self.max_value - self.min_value)
        frac = (self.value - self.min_value) / span
        return int(self.rect.x + 8 + frac * (self.rect.width - 16))

    def handle(self, event) -> bool:
        if not self.visible:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.contains(event.pos)
            if self._dragging:
                self._set_from_mouse(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.contains(event.pos):
                self._dragging = True
                self._set_from_mouse(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._dragging:
                self._dragging = False
                return True
        return False

    def _set_from_mouse(self, x: int) -> None:
        left, width = self.rect.x + 8, self.rect.width - 16
        frac = max(0.0, min(1.0, (x - left) / max(1, width)))
        self.value = int(round(self.min_value + frac * (self.max_value - self.min_value)))
        if self.on_change:
            self.on_change(self.value)

    def draw(self, surf, theme: Theme, book) -> None:
        if not self.visible:
            return
        mid = self.rect.centery
        track = pygame.Rect(self.rect.x + 8, mid - 2, self.rect.width - 16, 4)
        pygame.draw.rect(surf, theme['bg_medium'], track)
        filled = pygame.Rect(track.x, track.y, max(0, self._knob_x() - track.x), 4)
        pygame.draw.rect(surf, theme['accent'], filled)
        kx = self._knob_x()
        r = 6 if (self.hovered or self._dragging) else 5
        pygame.draw.circle(surf, theme['accent'], (kx, mid), r)
        pygame.draw.circle(surf, theme['bg_dark'], (kx, mid), max(1, r - 2))
