"""Виртуальный экран: вёрстка в логических координатах, вывод с масштабом.

Почему так: старый интерфейс жёстко занимал 1350×850 и на маленьком
мониторе не влезал. Теперь всё рисуется в виртуальную поверхность
LOGICAL_W × LOGICAL_H, а на экран уже масштабируется целиком под размер
окна — вёрстка не ломается ни на 800×600, ни на 4K.

Масштабирование бывает двух видов (переключатель «Плавное
масштабирование» в настройках, по умолчанию включено):

* плавное (smooth=True) — суперсемплинг: кадр сначала дублируется на
  промежуточный холст SUPERSAMPLE×, а затем мягко сводится к размеру
  окна. Пиксели интерфейса остаются чёткими, а края не ползут
  ступеньками — выглядит как качественное масштабирование, а не
  растянутая картинка;
* быстрое (smooth=False) — ближайший сосед: максимальная скорость и
  абсолютно «пиксельный» вид, но со ступенчатыми краями.
"""

from __future__ import annotations

import pygame

from . import config


class Screen:
    """Логическая поверхность + масштабирование в окно."""

    SUPERSAMPLE = 2.5       # множитель промежуточного холста (суперсемплинг)

    def __init__(self, window: pygame.Surface, logical_size=None,
                 smooth: bool = True):
        self.window = window
        self.logical_w = logical_size[0] if logical_size else config.LOGICAL_W
        self.logical_h = logical_size[1] if logical_size else config.LOGICAL_H
        self.surface = pygame.Surface((self.logical_w, self.logical_h)).convert()
        self.smooth = smooth
        self._scaled: pygame.Surface | None = None   # кадр под размер окна
        self._super: pygame.Surface | None = None    # промежуточный холст

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
        """Масштабирует логическую поверхность на окно.

        Рабочие поверхности кэшируются по размеру окна. При масштабе
        1:1 копируем напрямую, без ресемплинга.
        """
        size = self.window.get_size()
        if size == (self.logical_w, self.logical_h):
            self.window.blit(self.surface, (0, 0))
            return
        if self._scaled is None or self._scaled.get_size() != size:
            self._scaled = pygame.Surface(size).convert()
        if self.smooth:
            mid = (round(self.logical_w * self.SUPERSAMPLE),
                   round(self.logical_h * self.SUPERSAMPLE))
            if self._super is None or self._super.get_size() != mid:
                self._super = pygame.Surface(mid).convert()
            pygame.transform.scale(self.surface, mid, self._super)
            pygame.transform.smoothscale(self._super, size, self._scaled)
        else:
            pygame.transform.scale(self.surface, size, self._scaled)
        self.window.blit(self._scaled, (0, 0))
