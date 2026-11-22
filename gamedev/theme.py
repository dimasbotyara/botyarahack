"""Работа с темами: hex → RGB, кэш цветов."""

from __future__ import annotations

from . import config


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    """'#00ff00' → (0, 255, 0)."""
    value = value.lstrip('#')
    if len(value) == 3:
        value = ''.join(c * 2 for c in value)
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


class Theme:
    """Тема с цветами в ready-to-use RGB."""

    def __init__(self, key: str):
        self.key = key if key in config.THEMES else 'matrix'
        raw = config.THEMES[self.key]
        self.name = raw['name']
        self._raw = raw
        self.colors = {k: hex_to_rgb(v) for k, v in raw.items() if k != 'name'}

    def __getitem__(self, key: str) -> tuple[int, int, int]:
        return self.colors.get(key, (255, 0, 255))

    def get(self, key: str, default=(255, 255, 255)) -> tuple[int, int, int]:
        return self.colors.get(key, default)

    def dim(self, color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
        """Затемняет/осветляет цвет (factor 0..1)."""
        return tuple(max(0, min(255, int(c * factor))) for c in color)

    @staticmethod
    def all_themes() -> list[tuple[str, str]]:
        return [(k, v['name']) for k, v in config.THEMES.items()]
