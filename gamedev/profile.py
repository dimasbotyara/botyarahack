"""Профиль игрока: деньги, опыт, навыки.

Файл тот же, что у tkinter-версии (`~/.hacker_profile.json`), поэтому
прогресс не теряется при переключении между старой и новой версией.
Мусор в файле не должен ломать запуск — всё чинится при загрузке.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

PROFILE_PATH = Path.home() / '.hacker_profile.json'

SKILLS = {
    'hacking_speed': ('🚀 Скорость взлома', 'Ускоряет симуляцию', 1.0),
    'minigame_difficulty': ('🎮 Лёгкость мини-игр', 'Проще мини-игры', 1.0),
    'earning_rate': ('💰 Доход', 'Больше денег', 1.5),
    'stealth': ('👻 Скрытность', 'Дольше не палят', 1.2),
}

MAX_LEVEL = 10


def skill_cost(skill_id: str, level: int) -> int:
    """Стоимость следующего уровня — как в legacy: 100 × множитель × уровень."""
    return int(100 * SKILLS[skill_id][2] * level)


@dataclass
class Player:
    name: str = ''
    money: int = 0
    total_earned: int = 0
    hacks_completed: int = 0
    hacks_failed: int = 0
    data_stolen_gb: float = 0.0
    skill_points: int = 0
    skills: dict = field(default_factory=lambda: {
        'hacking_speed': 1, 'minigame_difficulty': 1,
        'earning_rate': 1, 'stealth': 1,
    })

    # ── загрузка/сохранение ─────────────────────────────────────────────
    @classmethod
    def load(cls, path: Path | None = None) -> 'Player':
        path = path or PROFILE_PATH
        try:
            raw = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(raw, dict):
                raise ValueError('не словарь')
        except (OSError, ValueError):
            return cls()
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw: dict) -> 'Player':
        player = cls()
        for key in ('name', 'money', 'total_earned', 'hacks_completed',
                    'hacks_failed', 'data_stolen_gb', 'skill_points'):
            if key in raw:
                setattr(player, key, raw[key])
        skills = raw.get('skills')
        if isinstance(skills, dict):
            for key in player.skills:
                if key in skills:
                    player.skills[key] = skills[key]
        # чиним типы: файл мог быть отредактирован руками
        player.money = max(0, _int(player.money))
        player.total_earned = max(0, _int(player.total_earned))
        player.hacks_completed = max(0, _int(player.hacks_completed))
        player.hacks_failed = max(0, _int(player.hacks_failed))
        player.skill_points = max(0, _int(player.skill_points))
        player.data_stolen_gb = max(0.0, _float(player.data_stolen_gb))
        player.name = str(player.name or '')[:32]
        for key in player.skills:
            player.skills[key] = max(1, min(MAX_LEVEL, _int(player.skills[key])))
        return player

    def to_dict(self) -> dict:
        return {
            'name': self.name, 'money': self.money,
            'total_earned': self.total_earned,
            'hacks_completed': self.hacks_completed,
            'hacks_failed': self.hacks_failed,
            'data_stolen_gb': round(self.data_stolen_gb, 2),
            'skill_points': self.skill_points,
            'skills': dict(self.skills),
        }

    def save(self, path: Path | None = None) -> bool:
        path = path or PROFILE_PATH
        try:
            path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False),
                            encoding='utf-8')
            return True
        except OSError:
            return False              # профиль — не повод падать

    # ── игровые действия ────────────────────────────────────────────────
    def apply_result(self, completed: int, failed: int, stolen_gb: float,
                     base_reward: int = 0) -> int:
        """Записать итог атаки. Возвращает начисленные деньги."""
        multiplier = 1 + (self.skills.get('earning_rate', 1) - 1) * 0.15
        earned = int(base_reward * multiplier)
        self.hacks_completed += completed
        self.hacks_failed += failed
        self.data_stolen_gb += stolen_gb
        self.skill_points += completed
        self.money += earned
        self.total_earned += earned
        return earned

    def can_upgrade(self, skill_id: str) -> bool:
        level = self.skills.get(skill_id, 1)
        return (level < MAX_LEVEL and self.skill_points >= 1
                and self.money >= skill_cost(skill_id, level))

    def upgrade(self, skill_id: str) -> bool:
        if not self.can_upgrade(skill_id):
            return False
        level = self.skills[skill_id]
        self.skill_points -= 1
        self.money -= skill_cost(skill_id, level)
        self.skills[skill_id] = level + 1
        return True

    def bar(self, skill_id: str) -> str:
        level = self.skills.get(skill_id, 1)
        return '█' * level + '░' * (MAX_LEVEL - level)


def _int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
