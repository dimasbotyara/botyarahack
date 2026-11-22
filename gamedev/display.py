"""Расчёт размера окна: авто-подбор под монитор и режимы из настроек.

Вся вёрстка считается в логических координатах LOGICAL_W × LOGICAL_H,
а окно получает масштаб (scale). Здесь только арифметика — pygame не нужен,
поэтому модуль легко тестируется без дисплея.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import config


@dataclass(frozen=True)
class WindowSize:
    """Итоговый размер окна и масштаб отрисовки."""

    width: int
    height: int
    scale: float
    mode: str          # 'auto' или выбранный пресет ('0.75', '1.0', …)

    @property
    def is_auto(self) -> bool:
        return self.mode == 'auto'

    def describe(self) -> str:
        return f'{self.width}×{self.height} ({self.scale * 100:.0f}%)'


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def compute_size(screen_w: int, screen_h: int,
                 mode: str = config.WINDOW_SCALE_DEFAULT) -> WindowSize:
    """Подбирает размер окна под монитор screen_w × screen_h.

    mode='auto'  — максимальный масштаб, влезающий в экран (с полями)
    mode='0.75'  — фиксированная доля логического размера
    Результат всегда влезает в экран и не меньше MIN_SCALE.
    """
    logical_w = config.LOGICAL_W
    logical_h = config.LOGICAL_H

    if mode == 'auto' or mode is None:
        fit_w = screen_w * config.FIT_W / logical_w
        fit_h = screen_h * config.FIT_H / logical_h
        scale = min(fit_w, fit_h, config.AUTO_MAX_SCALE)
        scale = _clamp(scale, config.MIN_SCALE, config.MAX_SCALE)
        mode = 'auto'
    else:
        try:
            scale = float(mode)
        except (TypeError, ValueError):
            scale = 1.0
        scale = _clamp(scale, config.MIN_SCALE, config.MAX_SCALE)

    width = int(logical_w * scale)
    height = int(logical_h * scale)

    # страховка: даже при странном мониторе окно не должно вылезти за экран
    if width > screen_w:
        scale = screen_w / logical_w
        width, height = int(logical_w * scale), int(logical_h * scale)
    if height > screen_h:
        scale = screen_h / logical_h
        width, height = int(logical_w * scale), int(logical_h * scale)

    return WindowSize(width=width, height=height, scale=round(scale, 4), mode=mode)


def normalize_mode(mode: str | None) -> str:
    """Приводит значение из файла настроек к известному пресету."""
    valid = {key for key, _label in config.WINDOW_PRESETS}
    if mode in valid:
        return mode
    return config.WINDOW_SCALE_DEFAULT


def available_modes() -> list[tuple[str, str]]:
    """Список (значение, подпись) для меню настроек."""
    return list(config.WINDOW_PRESETS)
