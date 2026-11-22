"""Виртуальный экран: вёрстка в логических координатах, вывод в окно.

Почему так: старый интерфейс жёстко занимал 1350×850 и на маленьком
мониторе не влезал. Теперь всё рисуется в логической системе
LOGICAL_W × LOGICAL_H, а где именно — зависит от режима масштабирования
(переключатель «Плавное масштабирование» в настройках, по умолчанию
включено):

* плавное (smooth=True) — Canvas рисует СРАЗУ в реальные пиксели окна:
  координаты переводятся на лету, шрифты растреризуются в размере окна.
  Никакого растягивания картинки — текст и линии чёткие, как будто
  интерфейс изначально был под это окно;

* быстрое (smooth=False) — растр в логическом размере 1152×726, на окно
  растягивается ближайшим соседом: дёшево и «по-пиксельному», но с
  лесенкой на нецелых масштабах.
"""

from __future__ import annotations

import pygame

from . import config
from .canvas import Canvas, install_hooks


class Screen:
    """Логическая поверхность + вывод в окно."""

    def __init__(self, window: pygame.Surface, logical_size=None,
                 smooth: bool = True, book=None):
        install_hooks()
        self.window = window
        self.logical_w = logical_size[0] if logical_size else config.LOGICAL_W
        self.logical_h = logical_size[1] if logical_size else config.LOGICAL_H
        self.book = book
        self._smooth = smooth
        self._scratch: pygame.Surface | None = None
        self.surface: Canvas | None = None
        self.rebuild()

    # ── режим ─────────────────────────────────────────────────────────
    @property
    def smooth(self) -> bool:
        return self._smooth

    @smooth.setter
    def smooth(self, value: bool) -> None:
        if bool(value) != self._smooth:
            self._smooth = bool(value)
            self.rebuild()

    def rebuild(self) -> None:
        """Пересоздаёт холст (смена размера окна или режима)."""
        if self._smooth:
            target = self.window
        else:
            self._scratch = pygame.Surface(
                (self.logical_w, self.logical_h)).convert()
            target = self._scratch
        self.surface = Canvas(target, self.logical_w, self.logical_h)
        if self.book is not None:
            self.book.render_scale = self.surface.sx

    # ── масштаб ──────────────────────────────────────────────────────
    @property
    def scale(self) -> float:
        return self.window.get_width() / self.logical_w

    def to_window(self, pos: tuple[float, float]) -> tuple[int, int]:
        """Логические координаты → координаты окна (для мыши/кликов)."""
        s = self.scale
        return (int(pos[0] * s), int(pos[1] * s))

    def to_logical(self, pos: tuple[float, float]) -> tuple[int, int]:
        """Координаты окна → логические (для попадания по кнопкам)."""
        s = self.scale or 1.0
        return (int(pos[0] / s), int(pos[1] / s))

    # ── вывод ────────────────────────────────────────────────────────
    def blit_to_window(self):
        """Показывает нарисованный кадр.

        В плавном режиме кадр уже нарисован прямо в окне — показывать
        нечего. Быстрый режим растягивает логический растр ближайшим
        соседом.
        """
        if self._smooth:
            return
        pygame.transform.scale(self.surface.real, self.window.get_size(),
                               self.window)
