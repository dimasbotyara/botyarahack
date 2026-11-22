"""Фоновые эффекты: падающая «матрица» из DATA STREAM старого интерфейса."""

from __future__ import annotations

import random
import string

import pygame

from .theme import Theme

CHARS = string.ascii_letters + string.digits + 'абвгдежзиклмнопрстуфхцчшщыьэюя'


class MatrixRain:
    """Столбцы символов, медленно стекающие вниз."""

    def __init__(self, width: int, height: int, columns: int = 34, seed: int | None = None):
        self.width = width
        self.height = height
        self.rng = random.Random(seed)
        self.font_size = 13
        self.col_width = max(10, width // columns)
        self.n_cols = max(1, width // self.col_width)
        self.drops = [self.rng.randrange(0, height) for _ in range(self.n_cols)]
        self.speeds = [self.rng.uniform(0.4, 1.6) for _ in range(self.n_cols)]
        self.glyphs = [self._random_char() for _ in range(self.n_cols)]
        self._tick = 0.0

    def _random_char(self) -> str:
        return self.rng.choice(CHARS)

    def update(self, dt: float) -> None:
        self._tick += dt
        if self._tick < 0.06:
            return
        self._tick = 0.0
        for i in range(self.n_cols):
            self.drops[i] += self.speeds[i] * self.col_width
            if self.drops[i] > self.height + self.col_width:
                self.drops[i] = self.rng.randrange(-200, 0)
                self.speeds[i] = self.rng.uniform(0.4, 1.6)
            if self.rng.random() < 0.3:
                self.glyphs[i] = self._random_char()

    def draw(self, surf: pygame.Surface, theme: Theme, book, alpha: int = 120) -> None:
        """Рисует столбцы (неярко — это фон)."""
        # осветляем базовый цвет темы, иначе на почти чёрном фоне не видно
        head = _lighten(theme['matrix_fg'], 2.4)
        tail = _lighten(theme['matrix_fg'], 1.2)
        for i in range(self.n_cols):
            x = i * self.col_width
            y = int(self.drops[i])
            # «голова» — поярче
            img = book.render(self.glyphs[i], self.font_size, head)
            img.set_alpha(min(255, alpha + 80))
            surf.blit(img, (x, y))
            # хвост — на пару символов вверх
            for k in range(1, 7):
                ty = y - k * self.font_size
                if ty < -self.font_size:
                    break
                ch = self.rng.choice(CHARS)
                fade = max(25, alpha - k * 14)
                timg = book.render(ch, self.font_size, tail)
                timg.set_alpha(fade)
                surf.blit(timg, (x, ty))


def _lighten(color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    """Умножает яркость цвета с потолком 255 — «подсветка» для матрицы."""
    return tuple(min(255, int(c * factor)) for c in color)
