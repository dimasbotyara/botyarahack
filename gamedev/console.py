"""Консоль отладки: те же команды, что в tkinter-версии.

Нужна, чтобы быстро проверить тему, режим или конкретную мини-игру,
не проходя весь взлом. Команды повторяют legacy:

    help                      справка
    minigame <name>           запустить мини-игру (maze, wire, ...)
    theme <name>              сменить тему
    mode <stealth|normal|aggressive>
    chance <10-100>           шанс мини-игры
    status                    текущее состояние
    clear                     очистить вывод
"""

from __future__ import annotations

from dataclasses import dataclass, field

GAME_ALIASES = {
    'rps': 'Камень-Ножницы-Бумага',
    'tictactoe': 'Крестики-Нолики',
    'simon': 'Последовательность',
    'wire': 'Бомба',
    'type': 'Набор кода',
    'maze': 'Лабиринт',
    'safe': 'Сейф',
    'math': 'Математика',
}

HELP = [
    'Команды:',
    '  help                       — эта справка',
    '  minigame <имя>             — запустить мини-игру',
    '    rps, tictactoe, simon, wire, type, maze, safe, math',
    '  theme <имя>                — сменить тему',
    '    matrix, cyberpunk, blood, ocean, retro',
    '  mode <имя>                 — режим атаки',
    '    stealth, normal, aggressive',
    '  chance <10-100>            — шанс мини-игры',
    '  status                     — состояние системы',
    '  clear                      — очистить вывод',
]


@dataclass
class Console:
    """Состояние консоли: история ввода и вывод."""

    open: bool = False
    input: str = ''
    output: list[str] = field(default_factory=lambda: [
        'Debug Console v2.0 (pygame)',
        "Введите 'help' для списка команд",
        '',
    ])
    scroll: int = 0
    execute_ready: bool = False         # Enter нажат — приложение выполнит
    game_started: str | None = None    # приложение читает и сбрасывает

    VISIBLE = 14

    def print(self, text: str = '') -> None:
        self.output.append(text)
        del self.output[:-500]
        self.scroll = 0

    def type_char(self, ch: str) -> None:
        if len(self.input) < 80:
            self.input += ch

    def backspace(self) -> None:
        self.input = self.input[:-1]

    def execute(self, app) -> None:
        """Выполнить введённую команду; app даёт доступ к состоянию."""
        cmd = self.input.strip()
        self.input = ''
        if not cmd:
            return
        self.print(f'> {cmd}')
        parts = cmd.lower().split()
        name, args = parts[0], parts[1:]

        if name == 'help':
            for line in HELP:
                self.print(line)
        elif name == 'minigame' and args:
            alias = args[0]
            if alias in GAME_ALIASES:
                self.game_started = GAME_ALIASES[alias]
                self.print(f'Запускаю: {GAME_ALIASES[alias]}')
            else:
                self.print(f'Неизвестная игра: {alias}')
        elif name == 'theme' and args:
            if args[0] in app.theme_keys:
                app._on_theme_change(args[0])
                self.print(f'Тема: {args[0]} (применена)')
            else:
                self.print(f'Неизвестная тема: {args[0]}')
        elif name == 'mode' and args:
            if args[0] in ('stealth', 'normal', 'aggressive'):
                app.set_mode(args[0])
                self.print(f'Режим: {args[0]}')
            else:
                self.print(f'Неизвестный режим: {args[0]}')
        elif name == 'chance' and args:
            try:
                value = max(10, min(100, int(args[0])))
            except ValueError:
                self.print('Ошибка: нужно число 10–100')
            else:
                app.settings.minigame_chance = value
                app.chance_slider.value = value
                self.print(f'Шанс мини-игры: {value}%')
        elif name == 'status':
            p = app.player
            lines = [
                f'Тема: {app.settings.theme}',
                f'Режим: {app.settings.attack_mode}',
                f'Шанс мини-игры: {app.settings.minigame_chance}%',
                f'Взлом идёт: {"да" if app.attack else "нет"}',
                f'Профиль: {p.name or "Анон"}, ${p.money}, SP {p.skill_points}',
                f'Окно: {app.size_info.describe()}',
            ]
            for line in lines:
                self.print(line)
        elif name == 'clear':
            self.output.clear()
        else:
            self.print(f'Неизвестная команда: {name}')

    def handle_key(self, event) -> bool:
        """Обработать клавишу; True — консоль забрала событие."""
        import pygame

        if event.key == pygame.K_RETURN:
            self.execute_ready = True
        elif event.key == pygame.K_BACKSPACE:
            self.backspace()
        elif event.key == pygame.K_PAGEUP:
            self.scroll += 5
        elif event.key == pygame.K_PAGEDOWN:
            self.scroll = max(0, self.scroll - 5)
        elif event.unicode and event.unicode.isprintable():
            self.type_char(event.unicode)
        return True
