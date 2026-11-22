"""Настройки: чтение/запись JSON с валидацией каждого поля.

Файл: ~/.hacker_settings.json — тот же, что у tkinter-версии,
поэтому настройки переносятся между версиями без потерь.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from pathlib import Path

from . import config
from .display import normalize_mode

SETTINGS_PATH = Path.home() / '.hacker_settings.json'

VALID_THEMES = tuple(config.THEMES)
VALID_MODES = ('stealth', 'normal', 'aggressive')


@dataclass
class Settings:
    theme: str = 'matrix'
    minigame_chance: int = 20
    glitch_enabled: bool = True
    show_calculations: bool = True
    attack_mode: str = 'normal'
    window_scale: str = config.WINDOW_SCALE_DEFAULT
    smooth_scaling: bool = True   # плавное масштабирование интерфейса
    vsync: bool = True
    sound: bool = True

    # ── валидация ────────────────────────────────────────────────────
    def normalized(self) -> 'Settings':
        """Возвращает копию с исправленными полями (мусор → дефолт)."""
        return Settings(
            theme=self.theme if self.theme in VALID_THEMES else 'matrix',
            minigame_chance=_clamp_int(self.minigame_chance, 10, 100, 20),
            glitch_enabled=bool(self.glitch_enabled),
            show_calculations=bool(self.show_calculations),
            attack_mode=self.attack_mode if self.attack_mode in VALID_MODES else 'normal',
            window_scale=normalize_mode(self.window_scale),
            smooth_scaling=bool(self.smooth_scaling),
            vsync=bool(self.vsync),
            sound=bool(self.sound),
        )

    @property
    def window_mode_label(self) -> str:
        for key, label in config.WINDOW_PRESETS:
            if key == self.window_scale:
                return label
        return 'Авто (по монитору)'

    # ── ввод/вывод ───────────────────────────────────────────────────
    @classmethod
    def from_dict(cls, data: dict) -> 'Settings':
        if not isinstance(data, dict):
            return cls()
        defaults = cls()
        s = cls(
            theme=data.get('theme', defaults.theme),
            minigame_chance=data.get('minigame_chance', defaults.minigame_chance),
            glitch_enabled=data.get('glitch_enabled', defaults.glitch_enabled),
            show_calculations=data.get('show_calculations', defaults.show_calculations),
            attack_mode=data.get('attack_mode', defaults.attack_mode),
            window_scale=data.get('window_scale', defaults.window_scale),
            smooth_scaling=data.get('smooth_scaling', defaults.smooth_scaling),
            vsync=data.get('vsync', defaults.vsync),
            sound=data.get('sound', defaults.sound),
        )
        return s.normalized()

    @classmethod
    def load(cls, path: Path | None = None) -> 'Settings':
        path = Path(path) if path else SETTINGS_PATH
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return cls.from_dict(json.load(f))
        except (OSError, ValueError):
            return cls()

    def save(self, path: Path | None = None) -> bool:
        path = Path(path) if path else SETTINGS_PATH
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.normalized()), f, indent=2, ensure_ascii=False)
            return True
        except OSError:
            return False


def _clamp_int(value, lo: int, hi: int, default: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return default
    return max(lo, min(hi, int(value)))
