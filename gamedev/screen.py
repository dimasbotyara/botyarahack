"""Виртуальный экран: вёрстка в логических координатах, вывод с масштабом.

Почему так: старый интерфейс жёстко занимал 1350×850 и на маленьком
мониторе не влезал. Теперь всё рисуется в виртуальную поверхность
LOGICAL_W × LOGICAL_H, а на экран уже масштабируется целиком под размер
окна — вёрстка не ломается ни на 800×600, ни на 4K.
"""

from __future__ import annotations

import pygame

from . import config


class Screen:
    """Логическая поверхность + масштабирование в окно."""

    def __init__(self, window: pygame.Surface, logical_size=None):
        self.window = window
        self.logical_w = logical_size[0] if logical_size else config.LOGICAL_W
        self.logical_h = logical_size[1] if logical_size else config.LOGICAL_H
        self.surface = pygame.Surface((self.logical_w, self.logical_h)).convert()
        self._smooth = True

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

    # ── отрисовка ────────────────────────────────────────────────────
    def blit_to_window(self):
        """Растягивает логическую поверхность на окно."""
        if self.window.get_size() == (self.logical_w, self.logical_h):
            self.window.blit(self.surface, (0, 0))
        else:
            pygame.transform.smoothscale(
                self.surface, self.window.get_size(), self.window)
