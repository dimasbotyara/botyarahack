"""Карта атак: сетка и затухающие «удары» по точкам.

В legacy точка мигала через `after()` и кольцо расходилось в 7 шагов.
Здесь у каждой точки есть время жизни, поэтому анимация идёт сама
и не зависит от частоты кадров.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame

PING_LIFETIME = 1.6       # секунд до полного затухания


@dataclass
class Ping:
    x: float                  # в долях ширины 0..1
    y: float
    age: float = 0.0

    @property
    def alive(self) -> bool:
        return self.age < PING_LIFETIME

    @property
    def progress(self) -> float:
        return min(1.0, self.age / PING_LIFETIME)


class AttackMap:
    """Панель карты: сетка + точки ударов."""

    def __init__(self, rect: pygame.Rect, seed: int | None = None):
        self.rect = rect
        self.pings: list[Ping] = []
        self.rng = random.Random(seed)

    def strike(self, x: float | None = None, y: float | None = None) -> None:
        """Ударить по точке (по умолчанию — случайной)."""
        self.pings.append(Ping(self.rng.random() if x is None else x,
                               self.rng.random() if y is None else y))
        if len(self.pings) > 40:
            del self.pings[:len(self.pings) - 40]

    def update(self, dt: float) -> None:
        for ping in self.pings:
            ping.age += dt
        self.pings = [p for p in self.pings if p.alive]

    def draw(self, surf, theme, book) -> None:
        r = self.rect
        pygame.draw.rect(surf, theme['matrix_bg'], r)

        # сетка
        step = 22
        for x in range(r.x + step, r.right, step):
            pygame.draw.line(surf, theme['bg_medium'], (x, r.y + 1), (x, r.bottom - 1))
        for y in range(r.y + step, r.bottom, step):
            pygame.draw.line(surf, theme['bg_medium'], (r.x + 1, y), (r.right - 1, y))
        pygame.draw.rect(surf, theme['border'], r, 1)

        for ping in self.pings:
            px = int(r.x + 6 + ping.x * (r.width - 12))
            py = int(r.y + 6 + ping.y * (r.height - 12))
            t = ping.progress
            # ядро гаснет, кольцо расходится — как в legacy, но плавнее
            core_alpha = int(255 * (1 - t))
            radius = 2 + int(14 * math.sqrt(t))
            ring = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
            color = theme['warning'] if t < 0.5 else theme['fg_dim']
            pygame.draw.circle(ring, (*color, core_alpha), (radius + 1, radius + 1),
                               radius, 1)
            surf.blit(ring, (px - radius - 1, py - radius - 1))
            dot = pygame.Surface((7, 7), pygame.SRCALPHA)
            pygame.draw.circle(dot, (*theme['error'], core_alpha), (4, 4), 3)
            surf.blit(dot, (px - 3, py - 3))

        if not self.pings:
            hint = book.render('► ожидание ударов', 8, theme['muted'])
            surf.blit(hint, (r.x + 8, r.bottom - 16))
