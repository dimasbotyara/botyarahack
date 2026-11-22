"""Главная сцена pygame-версии (Этап 3: цели, карта атак, профиль).

Что уже есть:
  * окно нужного размера (авто-подбор под монитор, смена из настроек);
  * тема применяется на лету;
  * лог с цветными строками, прокруткой и переносом по словам;
  * симуляция взлома — пошаговый автомат, с паузами и прерыванием;
  * режимы атаки (стелс / норм / агрессив) меняют темп и подробность;
  * список целей с очередью атаки, поиском и добавлением своих;
  * карта атак с затухающими точками ударов;
  * профиль игрока, навыки за SP и деньги;
  * прогресс, статус и счётчики внизу.

Размер окна меняется только в настройках (RESIZABLE не включаем).
"""

from __future__ import annotations

import datetime as _dt
import random
import sys

import pygame

from . import config, gamedata, history
from .attack import Attack, LogLine, mode_params
from .attackmap import AttackMap
from .console import Console
from .background import MatrixRain
from .display import compute_size
from .logpanel import LogView
from .minigames import Minigame, make_game
from .profile import MAX_LEVEL, SKILLS, Player, skill_cost
from .screen import Screen
from .settings import Settings
from .targets import TargetList
from .theme import Theme
from .widgets import Button, Checkbox, Dropdown, Label, Panel, Slider

# ── геометрия Этапа 2 ───────────────────────────────────────────────────
HEADER_H = 46
FOOTER_H = 74
PANEL_TOP = 56
LEFT_X, LEFT_W = 8, 300
CENTER_X, CENTER_W = 316, 300
RIGHT_X = 624


class App:
    """Главный цикл: интерфейс + симуляция."""

    FPS = 60

    def __init__(self):
        pygame.init()
        pygame.display.set_caption(config.TITLE)

        self.settings = Settings.load()
        self.theme = Theme(self.settings.theme)
        self.book = None          # заполним после pygame.font.init()

        info = pygame.display.Info()
        self.monitor = (info.current_w, info.current_h)
        size = compute_size(*self.monitor, mode=self.settings.window_scale)
        self.window = pygame.display.set_mode((size.width, size.height))
        self.size_info = size

        from assets.fonts.fontloader import FontBook
        self.book = FontBook(pygame)

        self.screen = Screen(self.window)
        self.clock = pygame.time.Clock()
        self.running = True
        self.time = 0.0
        self.matrix = MatrixRain(config.LOGICAL_W, config.LOGICAL_H, seed=7)

        self.menu_open = False
        self.skills_open = False
        self.attack: Attack | None = None
        self.paused = False
        self.attack_started = 0.0

        self.player = Player.load()
        self.targets = TargetList()
        self.map = AttackMap(pygame.Rect(CENTER_X + 10, PANEL_TOP + 30,
                                         CENTER_W - 20, 108), seed=3)
        self.typing_name = not bool(self.player.name)
        self.name_input = ''
        self.search_active = False
        self.skills_hover = False
        self.name_rect = pygame.Rect(0, 0, 0, 0)
        self.minigame: Minigame | None = None
        self.history_open = False
        self.console = Console()
        self.theme_keys = [k for k, _ in Theme.all_themes()]
        self.history_entries = history.load()
        self.history_scroll = 0
        self.minigame_rng = random.Random()
        self.glitch_timer = random.uniform(2.0, 5.0)
        self.glitch_shift = 0
        self.glitch_hold = 0.0

        self._build_main_ui()
        self._build_menu_ui()
        self._build_log()
        self._welcome()

    # ── сборка интерфейса ────────────────────────────────────────────────
    def _build_main_ui(self) -> None:
        W, H = config.LOGICAL_W, config.LOGICAL_H
        self.header_buttons = [
            Button(rect=pygame.Rect(W - 150, 12, 60, 24), text='⚙ Настройки',
                   size=9, on_click=self.open_menu),
            Button(rect=pygame.Rect(W - 82, 12, 50, 24), text='📜', size=9,
                   on_click=self._toggle_history),
        ]
        self.status_lights = [('DARKNET', True), ('TOR', True), ('VPN', False),
                              ('CRYPTO', True)]

        # режимы атаки — как радиокнопки в legacy
        self.mode_buttons: list[Button] = []
        modes = [('🐢 Стелс', 'stealth'), ('⚡ Норм', 'normal'), ('🔥 Агрессив', 'aggressive')]
        x = 16 + 24 + self._text_width(f'◆ {config.TITLE}', 16) + 24 + 4 * 80 + 20
        for label, key in modes:
            btn = Button(rect=pygame.Rect(x, 12, 76, 26), text=label, size=9,
                         on_click=lambda k=key: self.set_mode(k))
            self.mode_buttons.append(btn)
            x += 80

        # кнопка атаки
        self.attack_btn = Button(
            rect=pygame.Rect(LEFT_X + 12, H - FOOTER_H - 58, LEFT_W - 24, 36),
            text='◆ ВЗЛОМАТЬ ◆', size=12, accent=True, on_click=self.toggle_attack)

    def _text_width(self, text: str, size: int) -> int:
        return self.book.size(text, size, chain=['jetbrains_bold', 'symbols', 'emoji'])[0]

    def _build_log(self) -> None:
        W, H = config.LOGICAL_W, config.LOGICAL_H
        rect = pygame.Rect(RIGHT_X + 10, PANEL_TOP + 30,
                           W - RIGHT_X - 20, H - FOOTER_H - PANEL_TOP - 42)
        self.log = LogView(rect, self.book, font_size=12)

    def _resize_log(self) -> None:
        W, H = config.LOGICAL_W, config.LOGICAL_H
        self.log.resize(pygame.Rect(RIGHT_X + 10, PANEL_TOP + 30,
                                    W - RIGHT_X - 20,
                                    H - FOOTER_H - PANEL_TOP - 42))

    def _build_menu_ui(self) -> None:
        """Меню настроек: тема, размер окна, чекбоксы, слайдер."""
        W, H = config.LOGICAL_W, config.LOGICAL_H
        panel_w, panel_h = 580, 520
        px, py = (W - panel_w) // 2, (H - panel_h) // 2
        self.menu_rect = pygame.Rect(px, py, panel_w, panel_h)

        x0, x1 = px + 30, px + 300
        row1 = py + 88          # подпись + выпадающие списки
        row2 = row1 + 92        # предпросмотр размера + шанс мини-игры
        row3 = row2 + 74        # чекбоксы

        self.theme_dd = Dropdown(
            rect=pygame.Rect(x0, row1, 230, 26),
            options=Theme.all_themes(),
            value=self.settings.theme,
            on_change=self._on_theme_change)

        self.size_dd = Dropdown(
            rect=pygame.Rect(x1, row1, 230, 26),
            options=config.WINDOW_PRESETS,
            value=self.settings.window_scale,
            on_change=self._on_size_change)

        self.chance_slider = Slider(
            rect=pygame.Rect(x0, row2, 230, 20),
            value=self.settings.minigame_chance,
            on_change=self._on_chance_change)

        self.glitches_cb = Checkbox(
            rect=pygame.Rect(x1, row3, 230, 20), text='Глитч-эффекты',
            checked=self.settings.glitch_enabled,
            on_change=self._on_glitch_change)

        self.calc_cb = Checkbox(
            rect=pygame.Rect(x1, row3 + 32, 230, 20), text='Показывать расчёты',
            checked=self.settings.show_calculations,
            on_change=self._on_calc_change)

        y = py + panel_h - 46
        self.menu_widgets = [self.theme_dd, self.size_dd, self.chance_slider,
                             self.glitches_cb, self.calc_cb]
        self.menu_buttons = [
            Button(rect=pygame.Rect(px + panel_w - 140, y, 110, 28),
                   text='💾 Сохранить', size=10, accent=True,
                   on_click=self.save_and_close),
            Button(rect=pygame.Rect(px + 30, y, 100, 28),
                   text='✖ Закрыть', size=10,
                   on_click=lambda: setattr(self, 'menu_open', False)),
        ]

    # ── лог ─────────────────────────────────────────────────────────────
    def _welcome(self) -> None:
        stamp = self._stamp()
        lines = [
            LogLine('═' * 50, 'header', stamp),
            LogLine('  SECURITY EXPLOIT KIT v' + config.VERSION, 'header', stamp),
            LogLine('═' * 50, 'header', stamp),
            LogLine('', 'info', stamp),
            LogLine('  Все модули загружены', 'success', stamp),
            LogLine('  Режимы: 🐢Стелс | ⚡Норм | 🔥Агрессив', 'info', stamp),
            LogLine('  Выбери цели слева и жми ВЗЛОМАТЬ', 'info', stamp),
            LogLine('', 'info', stamp),
        ]
        p = self.player
        lines += [
            LogLine('═' * 50, 'header', stamp),
            LogLine('  ТВОЙ ПРОФИЛЬ', 'header', stamp),
            LogLine('═' * 50, 'header', stamp),
            LogLine(f'  Хакер: {p.name or "Анон"}', 'data', stamp),
            LogLine(f'  Баланс: ${p.money}', 'data', stamp),
            LogLine(f'  Взломов: {p.hacks_completed}  провалов: {p.hacks_failed}',
                    'info', stamp),
            LogLine(f'  Данных добыто: {p.data_stolen_gb:.1f} GB', 'info', stamp),
            LogLine('═' * 50, 'header', stamp),
            LogLine('', 'info', stamp),
        ]
        self.log.append(lines)

    @staticmethod
    def _stamp() -> str:
        return _dt.datetime.now().strftime('%H:%M:%S')

    def log_line(self, text: str, kind: str = 'info') -> None:
        self.log.append([LogLine(text, kind, self._stamp())])

    # ── атака ───────────────────────────────────────────────────────────
    def set_mode(self, key: str) -> None:
        self.settings.attack_mode = key
        self.log_line(f'  Режим: {key.upper()}', 'warning')

    def toggle_attack(self) -> None:
        if self.attack and not self.attack.finished:
            self.attack.finished = True       # мгновенное прерывание
            self.log_line('', 'info')
            self.log_line('⚠ ПРЕРВАНО!', 'error')
            self.attack = None
            self.paused = False
            return

        targets = self._pick_targets()
        if self.typing_name:
            self.log_line('⚠ Сначала введи имя хакера', 'warning')
            return
        self.attack = Attack(
            targets=targets,
            params=mode_params(self.settings.attack_mode, self.player.skills),
            minigame_chance=self.settings.minigame_chance,
            show_calculations=self.settings.show_calculations,
            rng=random.Random())
        self.attack_started = self.time
        self.paused = False

    def _pick_targets(self) -> list[str]:
        """Цели в порядке кликов; если очередь пуста — случайная."""
        chosen = self.targets.selected()
        if chosen:
            return chosen
        target = random.choice(self.targets.items or gamedata.TARGETS)
        self.log_line('⚠ Цель не выбрана, атакую случайную', 'warning')
        return [target]

    def _pump_glitch(self, dt: float) -> None:
        """Редкие сдвиги картинки — как «глитч» в старой версии.

        В tkinter это было мигание фона лога; здесь — сдвиг полос
        по горизонтали, заметнее и без дёрганья всего окна.
        """
        if not self.settings.glitch_enabled:
            self.glitch_shift = 0
            return
        self.glitch_timer -= dt
        if self.glitch_timer <= 0:
            # короткая вспышка раз в 4–9 секунд
            self.glitch_timer = random.uniform(4.0, 9.0)
            self.glitch_shift = random.choice([3, 5, 8])
            self.glitch_hold = random.uniform(0.05, 0.12)
        elif self.glitch_shift:
            self.glitch_hold -= dt
            if self.glitch_hold <= 0:
                self.glitch_shift = 0

    RESULT_PAUSE = 1.1        # секунд показать «победа/провал» перед закрытием

    def _pump_minigame(self, dt: float) -> None:
        """Обновить мини-игру и вернуть исход в движок, когда он готов."""
        if self.minigame is not None:
            self.minigame.update(dt)
            if self.minigame.result is not None and \
                    self.minigame.finished >= self.RESULT_PAUSE:
                self._close_minigame()
            return
        if self.console.game_started:
            name = self.console.game_started
            self.console.game_started = None
            self.minigame = make_game('debug / console', rng=self.minigame_rng,
                                      name=name)
            return
        if self.attack is not None and self.attack.minigame:
            self.minigame = make_game(self.attack.current_target,
                                      rng=self.minigame_rng)
            self.log_line(f'  ⚠ ИГРА: {self.minigame.title.split(":")[0].strip()}', 'minigame')

    def _close_minigame(self) -> None:
        """Мини-игра закончилась — сообщаем движку и убираем окно."""
        if self.minigame is None:
            return
        won = bool(self.minigame.result)
        self.minigame = None
        if self.attack is not None and self.attack.minigame:
            self.attack.resolve_minigame(won)

    def _pump_attack(self, dt: float) -> None:
        if self.attack is None:
            return
        if not self.paused:
            self.attack.update(dt)
        self.log.append(self.attack.drain())

        # удары по карте — по одному за новый фрагмент вывода
        if self.attack.phase in ('scan', 'exploit', 'extract') and \
                random.random() < dt * 2.5:
            self.map.strike()

        if self.attack.finished:
            a = self.attack
            self.log_line(f'  Итог: {a.completed} успешно, {a.failed} провалено', 'header')
            if a.completed or a.failed:
                earned = self.player.apply_result(a.completed, a.failed,
                                                  a.stolen_gb, a.money)
                self.player.save()
                if earned:
                    self.log_line(f'  Зачислено: ${earned} (баланс ${self.player.money})',
                                  'success')
                self.log_line(f'  SP: +{a.completed} (всего {self.player.skill_points})',
                              'data')
            if a.money:
                self.log_line(f'  Заработано: ${a.money}', 'success')
            self.history_entries = history.add(
                self.history_entries, len(a.targets), a.completed, a.failed,
                self.settings.attack_mode)
            self.attack = None

    # ── настройки ───────────────────────────────────────────────────────
    def _on_theme_change(self, key: str) -> None:
        self.settings.theme = key
        self.theme = Theme(key)          # применяется сразу, без рестарта

    def _on_size_change(self, key: str) -> None:
        self.settings.window_scale = key
        self.apply_window_size()
        self._resize_log()
        if hasattr(self, 'left_rect'):
            self._layout_panels(config.LOGICAL_W, config.LOGICAL_H)
            self.attack_btn.rect = pygame.Rect(
                LEFT_X + 12, config.LOGICAL_H - FOOTER_H - 58, LEFT_W - 24, 36)

    def _on_chance_change(self, value: int) -> None:
        self.settings.minigame_chance = int(value)

    def _on_glitch_change(self, value: bool) -> None:
        self.settings.glitch_enabled = value

    def _on_calc_change(self, value: bool) -> None:
        self.settings.show_calculations = value
        if self.attack:
            self.attack.show_calculations = value

    def apply_window_size(self) -> None:
        """Пересчитывает и применяет размер окна (только через настройки)."""
        info = pygame.display.Info()
        self.monitor = (info.current_w, info.current_h)
        self.size_info = compute_size(*self.monitor, mode=self.settings.window_scale)
        self.window = pygame.display.set_mode(
            (self.size_info.width, self.size_info.height))
        self.screen = Screen(self.window)

    def open_menu(self) -> None:
        self.menu_open = True
        self.theme_dd.value = self.settings.theme
        self.size_dd.value = self.settings.window_scale
        self.chance_slider.value = self.settings.minigame_chance
        self.glitches_cb.checked = self.settings.glitch_enabled
        self.calc_cb.checked = self.settings.show_calculations

    def save_and_close(self) -> None:
        self.settings.save()
        self.menu_open = False

    def _toggle_history(self) -> None:
        self.history_open = not self.history_open
        if self.history_open:
            self.history_entries = history.load()
            self.history_scroll = 0

    def _export_log(self) -> None:
        """Сохранить лог в файл рядом с профилем (без диалогов)."""
        from pathlib import Path as _Path

        stamp = _dt.datetime.now().strftime('%Y%m%d_%H%M%S')
        path = _Path.home() / f'botyarahack_log_{stamp}.txt'
        try:
            path.write_text('\n'.join(ln.text for ln in self.log.lines),
                            encoding='utf-8')
            self.log_line(f'💾 Лог сохранён: {path}', 'success')
        except OSError as exc:
            self.log_line(f'⚠ Не удалось сохранить лог: {exc}', 'error')

    # ── главный цикл ─────────────────────────────────────────────────────
    def run(self) -> int:
        while self.running:
            dt = self.clock.tick(self.FPS) / 1000.0
            self.time += dt
            self.handle_events()
            self.matrix.update(dt)
            self.map.update(dt)
            self._pump_glitch(dt)
            self._pump_minigame(dt)
            self._pump_attack(min(dt, 0.1))
            self.draw()
            pygame.display.flip()
        pygame.quit()
        return 0

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue

            # ── ввод имени при первом запуске ──
            if self.typing_name and not self.menu_open:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self._submit_name()
                    elif event.key == pygame.K_BACKSPACE:
                        self.name_input = self.name_input[:-1]
                    elif event.unicode and event.unicode.isprintable() and \
                            len(self.name_input) < 20:
                        self.name_input += event.unicode
                continue

            if self.minigame is not None:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.minigame.lose('СДАЛСЯ')
                elif event.type == pygame.KEYDOWN or \
                        event.type == pygame.MOUSEBUTTONDOWN:
                    ev = self._menu_event(event)
                    self.minigame.handle(ev)
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.console.open:
                        self.console.open = False
                    elif self.history_open:
                        self.history_open = False
                    elif self.skills_open:
                        self.skills_open = False
                    elif self.menu_open:
                        self.menu_open = False
                    elif self.search_active and self.targets.filter_text:
                        self.targets.filter_text = ''
                    elif self.search_active:
                        self.search_active = False
                    elif self.attack:
                        self.toggle_attack()
                    else:
                        self.running = False
                    continue

                if self.console.open:
                    self.console.handle_key(event)
                    if self.console.execute_ready:
                        self.console.execute_ready = False
                        self.console.execute(self)
                    continue
                if self.history_open:
                    if event.key in (pygame.K_UP, pygame.K_DOWN):
                        step = 1 if event.key == pygame.K_UP else -1
                        self.history_scroll = max(
                            0, self.history_scroll + step)
                    continue
                if self.skills_open:
                    continue
                if self.search_active:
                    if event.key == pygame.K_BACKSPACE:
                        self.targets.backspace()
                    elif event.key == pygame.K_RETURN:
                        self.search_active = False
                    elif event.key == pygame.K_DOWN:
                        self.targets.scroll_by(1, self._target_rows())
                    elif event.key == pygame.K_UP:
                        self.targets.scroll_by(-1, self._target_rows())
                    elif event.unicode and event.unicode.isprintable():
                        self.targets.type_char(event.unicode)
                    continue

                if event.key == pygame.K_m and not self.menu_open:
                    self.open_menu()
                    continue
                if event.key in (pygame.K_F1, pygame.K_BACKQUOTE) and \
                        not self.menu_open:
                    self.console.open = not self.console.open
                    continue
                if event.key == pygame.K_h and not self.menu_open:
                    self.history_open = not self.history_open
                    if self.history_open:
                        self.history_entries = history.load()
                        self.history_scroll = 0
                    continue
                if event.key == pygame.K_F12 and not self.menu_open:
                    self._export_log()
                    continue
                if event.key == pygame.K_SPACE and self.attack and not self.menu_open:
                    self.paused = not self.paused
                    self.log_line('⏸ Пауза' if self.paused else '▶ Продолжаю', 'warning')
                    continue
                if event.key == pygame.K_F11 and self.menu_open:
                    self.save_and_close()
                    continue
                if not self.menu_open and self.log.handle(event):
                    continue

            if self.menu_open:
                if self.theme_dd.open and self.theme_dd.handle(self._menu_event(event)):
                    continue
                if self.size_dd.open and self.size_dd.handle(self._menu_event(event)):
                    continue
                for w in self.menu_widgets:
                    w.handle(self._menu_event(event))
                for b in self.menu_buttons:
                    b.handle(self._menu_event(event))
                continue

            if self.skills_open:
                self._handle_skills(event)
                continue

            # ── обычный режим ──
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = self._logical(event)
                if self.search_rect.collidepoint(pos):
                    self.search_active = True
                    continue
                if self.skills_rect.collidepoint(pos):
                    self.skills_open = True
                    continue
                name = self._target_at(pos)
                if name:
                    self.targets.toggle(name)
                    order = self.targets.queue.get(name)
                    if order:
                        self.log_line(f'  + В очередь [{order}]: {name}', 'success')
                    else:
                        self.log_line(f'  − Из очереди: {name}', 'warning')
                    continue
            if event.type == pygame.MOUSEWHEEL and self._logical(event) != (-1, -1):
                if self.targets_rect.collidepoint(self._logical(event)):
                    self.targets.scroll_by(-event.y * 2, self._target_rows())
                    continue
            if event.type == pygame.MOUSEMOTION:
                self.skills_hover = self.skills_rect.collidepoint(self._logical(event))

            if self.log.rect.collidepoint(self._logical(event)):
                if self.log.handle(event):
                    continue
            for b in self.header_buttons:
                b.handle(self._menu_event(event))
            for b in self.mode_buttons:
                b.handle(self._menu_event(event))
            self.attack_btn.handle(self._menu_event(event))

    # ── ввод имени ──────────────────────────────────────────────────────
    def _submit_name(self) -> None:
        name = self.name_input.strip() or 'Анон'
        self.player.name = name
        self.player.save()
        self.typing_name = False
        self.log_line(f"▶ Хакер '{name}' в сети", 'success')

    # ── цели ────────────────────────────────────────────────────────────
    def _target_rows(self) -> int:
        return max(1, (self.targets_rect.height - 4) // self.ROW_H)

    def _target_at(self, pos) -> str | None:
        """Какая цель под курсором (с учётом прокрутки и поиска)."""
        r = self.targets_rect
        if not r.inflate(-2, -2).collidepoint(pos):
            return None
        y = pos[1] - (r.y + 2)
        row = y // self.ROW_H
        if row < 0 or row >= self._target_rows():
            return None
        visible = self.targets.visible()
        index = self.targets.scroll + row
        if index >= len(visible):
            return None
        return self.targets.items[visible[index][0]]

    # ── навыки ──────────────────────────────────────────────────────────
    def _handle_skills(self, event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self._logical(event)
            for sid, btn in self.skill_buttons.items():
                if btn.collidepoint(pos):
                    if self.player.upgrade(sid):
                        self.player.save()
                        self.log_line(f'  ▲ Навык {sid} → {self.player.skills[sid]}',
                                      'success')
                    else:
                        self.log_line('  ⚠ Не хватает SP или денег', 'warning')
                    return
            if not self.skills_modal.collidepoint(pos):
                self.skills_open = False

    def _logical(self, event):
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN,
                          pygame.MOUSEBUTTONUP):
            return self.screen.to_logical(event.pos)
        return (-1, -1)

    def _menu_event(self, event):
        """Перевод координат окна в логические."""
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN,
                          pygame.MOUSEBUTTONUP):
            attrs = dict(event.__dict__)
            attrs['pos'] = self.screen.to_logical(event.pos)
            return pygame.event.Event(event.type, attrs)
        return event

    # ── отрисовка ────────────────────────────────────────────────────────
    def draw(self) -> None:
        surf = self.screen.surface
        W, H = config.LOGICAL_W, config.LOGICAL_H
        surf.fill(self.theme['bg_dark'])
        self.matrix.draw(surf, self.theme, self.book)

        self._draw_header(surf, W)
        self._draw_panels(surf, W, H)
        self._draw_footer(surf, W, H)

        if self.menu_open:
            self._draw_menu(surf, W, H)
        if self.skills_open:
            self._draw_skills(surf, W, H)
        if self.history_open:
            self._draw_history(surf, W, H)
        if self.console.open:
            self._draw_console(surf, W, H)
        if self.minigame is not None:
            self.minigame.draw(surf, W, H, self.theme, self.book)
        if self.typing_name:
            self._draw_name_prompt(surf, W, H)

        self.screen.blit_to_window()
        if self.glitch_shift:
            self._apply_glitch()

    def _apply_glitch(self) -> None:
        """Сдвинуть несколько случайных полос на уже нарисованном окне."""
        win = self.window
        h = win.get_height()
        for _ in range(3):
            band_h = random.randint(4, 22)
            y = random.randint(0, max(1, h - band_h))
            try:
                band = win.subsurface(pygame.Rect(0, y, win.get_width(), band_h)).copy()
            except ValueError:
                return
            win.blit(band, (self.glitch_shift, y))

    def _draw_header(self, surf, W: int) -> None:
        theme, book = self.theme, self.book
        t = book.render(f'◆ {config.TITLE}', 16, theme['fg_main'],
                        chain=['jetbrains_bold', 'symbols', 'emoji'])
        surf.blit(t, (16, 14))

        x = 16 + t.get_width() + 24
        for name, on in self.status_lights:
            box = pygame.Rect(x, 12, 74, 26)
            pygame.draw.rect(surf, theme['bg_medium'], box)
            pygame.draw.rect(surf, theme['border'], box, 1)
            dot = theme['fg_main'] if on else theme['error']
            pygame.draw.circle(surf, dot, (box.x + 10, box.centery), 3)
            lbl = book.render(name, 7, theme['fg_dim'])
            surf.blit(lbl, (box.x + 20, box.centery - lbl.get_height() // 2))
            x += box.width + 6

        # активный режим подсвечен
        for btn in self.mode_buttons:
            active = self.settings.attack_mode == self._mode_of(btn)
            btn.accent = active
            btn.draw(surf, theme, book)

        for b in self.header_buttons:
            b.draw(surf, theme, book)

        pygame.draw.line(surf, theme['border'], (8, HEADER_H), (W - 8, HEADER_H))

    def _mode_of(self, btn: Button) -> str:
        for label, key in [('🐢', 'stealth'), ('⚡', 'normal'), ('🔥', 'aggressive')]:
            if btn.text.startswith(label):
                return key
        return 'normal'

    def _draw_panels(self, surf, W: int, H: int) -> None:
        theme, book = self.theme, self.book
        bottom = H - FOOTER_H
        height = bottom - PANEL_TOP

        if not hasattr(self, 'left_rect'):
            self._layout_panels(W, H)

        for p in (self.left_panel, self.center_panel, self.right_panel):
            p.draw(surf, theme, book)

        self._draw_targets(surf)
        self._draw_map_and_profile(surf)
        self.log.draw(surf, theme, book)

        # кнопка атаки (внутри левой панели)
        self.attack_btn.text = '⏹ СТОП' if self.attack else '◆ ВЗЛОМАТЬ ◆'
        self.attack_btn.accent = not self.attack
        self.attack_btn.draw(surf, theme, book)

    def _layout_panels(self, W: int, H: int) -> None:
        """Пересчитать геометрию панелей (один раз и при смене размера)."""
        bottom = H - FOOTER_H
        height = bottom - PANEL_TOP
        self.left_rect = pygame.Rect(LEFT_X, PANEL_TOP, LEFT_W, height)
        self.center_rect = pygame.Rect(CENTER_X, PANEL_TOP, CENTER_W, height)
        self.right_rect = pygame.Rect(RIGHT_X, PANEL_TOP, W - RIGHT_X - 8, height)
        self.left_panel = Panel(rect=self.left_rect, title='◆ ЦЕЛИ')
        self.center_panel = Panel(rect=self.center_rect, title='◆ КАРТА АТАК')
        self.right_panel = Panel(rect=self.right_rect, title='◆ EXPLOIT LOG')

        # поле поиска и список целей внутри левой панели
        self.search_rect = pygame.Rect(self.left_rect.x + 10, self.left_rect.y + 32,
                                       self.left_rect.width - 20, 24)
        list_top = self.search_rect.bottom + 6
        # оставляем 20 px под строку «в очереди / всего»
        list_bottom = self.attack_btn.rect.y - 28
        self.targets_rect = pygame.Rect(self.left_rect.x + 10, list_top,
                                        self.left_rect.width - 20,
                                        max(40, list_bottom - list_top))

        # карта и профиль в средней панели
        self.map.rect = pygame.Rect(self.center_rect.x + 10, self.center_rect.y + 32,
                                    self.center_rect.width - 20, 108)
        self.skills_rect = pygame.Rect(self.center_rect.x + 10,
                                       self.center_rect.bottom - 40,
                                       self.center_rect.width - 20, 30)

    # ── цели ────────────────────────────────────────────────────────────
    ROW_H = 19

    def _draw_targets(self, surf) -> None:
        theme, book = self.theme, self.book

        # поиск
        box = self.search_rect
        pygame.draw.rect(surf, theme['bg_medium'], box)
        pygame.draw.rect(surf, theme['accent'] if self.search_active else theme['border'],
                         box, 1)
        text = self.targets.filter_text or '🔍 поиск…'
        color = theme['fg_main'] if self.targets.filter_text else theme['muted']
        img = book.render(text, 9, color)
        surf.blit(img, (box.x + 6, box.centery - img.get_height() // 2))
        if self.search_active and int(self.time * 2) % 2 == 0:
            cx = box.x + 6 + img.get_width() + 1
            pygame.draw.line(surf, theme['accent'], (cx, box.y + 5), (cx, box.bottom - 5))

        # список
        r = self.targets_rect
        pygame.draw.rect(surf, theme['bg_dark'], r)
        pygame.draw.rect(surf, theme['border'], r, 1)
        rows = max(1, (r.height - 4) // self.ROW_H)
        visible = self.targets.visible()
        self.targets.scroll = max(0, min(max(0, len(visible) - rows), self.targets.scroll))

        clip = surf.get_clip()
        surf.set_clip(r.inflate(-2, -2))
        for i, (idx, label) in enumerate(visible[self.targets.scroll:
                                                 self.targets.scroll + rows]):
            row = pygame.Rect(r.x + 1, r.y + 2 + i * self.ROW_H, r.width - 2, self.ROW_H)
            name = self.targets.items[idx]
            queued = name in self.targets.queue
            if queued:
                pygame.draw.rect(surf, theme['bg_light'], row)
            order_text = f'{self.targets.queue[name]}. ' if queued else '   '
            color = theme['accent'] if queued else theme['fg_main']
            img = book.render(order_text + label.split('] ', 1)[-1], 9, color)
            surf.blit(img, (row.x + 5, row.y + 3))
        surf.set_clip(clip)

        # счётчик очереди — в полосе между списком и кнопкой
        count = len(self.targets.queue)
        stat = book.render(f'в очереди: {count}', 9,
                           theme['accent'] if count else theme['fg_dim'])
        surf.blit(stat, (r.x + 1, r.bottom + 4))
        total = book.render(f'всего: {len(self.targets.items)}', 8, theme['muted'])
        surf.blit(total, (r.right - total.get_width() - 1, r.bottom + 5))

    # ── карта и профиль ─────────────────────────────────────────────────
    def _draw_map_and_profile(self, surf) -> None:
        theme, book = self.theme, self.book
        self.map.draw(surf, theme, book)

        p = self.player
        y = self.map.rect.bottom + 8
        x = self.center_rect.x + 12
        rows = [
            (f'👤 {p.name or "Анон"}', 'fg_main', 11),
            (f'💵 ${p.money}', 'accent', 11),
            (f'Взломов: {p.hacks_completed}  провалов: {p.hacks_failed}', 'fg_dim', 9),
            (f'Данных: {p.data_stolen_gb:.1f} GB', 'fg_dim', 9),
            (f'SP: {p.skill_points}  ▲ {sum(p.skills.values()) - 4} ур.', 'warning', 10),
        ]
        for text, color, size in rows:
            img = book.render(text, size, theme[color])
            surf.blit(img, (x, y))
            y += img.get_height() + 3

        # кнопка навыков
        btn = self.skills_rect
        pygame.draw.rect(surf, theme['bg_medium'], btn)
        pygame.draw.rect(surf, theme['accent'] if self.skills_hover else theme['border'],
                         btn, 1)
        img = book.render('⚡ НАВЫКИ', 10, theme['accent'],
                          chain=['jetbrains_bold', 'symbols', 'emoji'])
        surf.blit(img, (btn.centerx - img.get_width() // 2,
                        btn.centery - img.get_height() // 2))

    def _draw_footer(self, surf, W: int, H: int) -> None:
        theme, book = self.theme, self.book
        top = H - FOOTER_H
        pygame.draw.line(surf, theme['border'], (8, top), (W - 8, top))

        # прогресс-бар
        a = self.attack
        value = a.progress if a else 0
        bar = pygame.Rect(16, top + 12, W - 32, 14)
        pygame.draw.rect(surf, theme['bg_medium'], bar)
        fill = bar.copy()
        fill.width = int(bar.width * value / 100)
        pygame.draw.rect(surf, theme['accent'], fill)
        pygame.draw.rect(surf, theme['border'], bar, 1)

        pct = book.render(f'{int(value)}%', 9, theme['fg_main'])
        surf.blit(pct, (bar.right - pct.get_width() - 4, bar.y + 1))

        status = a.status if a else 'Ожидание'
        if self.minigame is not None:
            status = f'МИНИ-ИГРА · {self.minigame.title.split(":")[-1].strip()}'
        if self.paused:
            status = '⏸ ПАУЗА — ' + status
        img = book.render(f'СТАТУС: {status}', 10, theme['fg_main'])
        surf.blit(img, (16, top + 32))

        info = book.render(
            f'окно: {self.size_info.describe()}  │  монитор: {self.monitor[0]}×{self.monitor[1]}'
            f'  │  тема: {self.theme.name}', 8, theme['fg_dim'])
        surf.blit(info, (16, top + 48))

        hint = book.render(
            'ВЗЛОМАТЬ — старт/стоп │ SPACE — пауза │ H — история │ M — настройки │ '
            'F1 — консоль │ F12 — экспорт лога │ ESC — выход', 8, theme['muted'])
        surf.blit(hint, (16, top + 60))

    def _draw_menu(self, surf, W: int, H: int) -> None:
        """Меню настроек: строгая сетка строк, подписи не наезжают."""
        theme, book = self.theme, self.book
        dim = pygame.Surface((W, H))
        dim.fill((0, 0, 0))
        dim.set_alpha(170)
        surf.blit(dim, (0, 0))

        r = self.menu_rect
        pygame.draw.rect(surf, theme['bg_dark'], r)
        pygame.draw.rect(surf, theme['accent'], r, 1)
        title = book.render('⚙ НАСТРОЙКИ', 16, theme['fg_main'],
                            chain=['jetbrains_bold', 'symbols', 'emoji'])
        surf.blit(title, (r.x + 24, r.y + 16))
        pygame.draw.line(surf, theme['border'], (r.x + 1, r.y + 52), (r.right - 1, r.y + 52))

        self._menu_caption(surf, 'Тема', self.theme_dd.rect)
        self._menu_caption(surf, 'Размер окна', self.size_dd.rect)

        self._menu_caption(surf, f'Шанс мини-игры: {self.settings.minigame_chance}%',
                           self.chance_slider.rect)
        preview = book.render(f'→ окно: {self.size_info.describe()}', 10, theme['muted'])
        surf.blit(preview, (self.size_dd.rect.x, self.chance_slider.rect.y - 6))
        mon = book.render(f'   монитор: {self.monitor[0]}×{self.monitor[1]}', 9, theme['muted'])
        surf.blit(mon, (self.size_dd.rect.x, self.chance_slider.rect.y + 10))

        self._menu_caption(surf, 'Эффекты', self.glitches_cb.rect.x,
                           y=self.glitches_cb.rect.y - 24)

        dropdowns = [self.theme_dd, self.size_dd]
        for w in self.menu_widgets:
            if w not in dropdowns:
                w.draw(surf, theme, book)
        for b in self.menu_buttons:
            b.draw(surf, theme, book)
        for w in dropdowns:
            w.draw(surf, theme, book)

        hint = book.render('Размер окна меняется только здесь — мышью тянуть нельзя',
                           9, theme['fg_dim'])
        surf.blit(hint, (r.x + 24, r.bottom - 78))

    # ── история атак ────────────────────────────────────────────────────
    def _draw_history(self, surf, W: int, H: int) -> None:
        theme, book = self.theme, self.book
        dim = pygame.Surface((W, H))
        dim.fill((0, 0, 0))
        dim.set_alpha(180)
        surf.blit(dim, (0, 0))

        w, h = 760, 500
        r = pygame.Rect((W - w) // 2, (H - h) // 2, w, h)
        pygame.draw.rect(surf, theme['bg_dark'], r)
        pygame.draw.rect(surf, theme['accent'], r, 1)

        title = book.render('📜 ИСТОРИЯ АТАК', 16, theme['fg_main'],
                            chain=['jetbrains_bold', 'symbols', 'emoji'])
        surf.blit(title, (r.x + 24, r.y + 16))
        hint = book.render('H или ESC — закрыть', 9, theme['muted'])
        surf.blit(hint, (r.right - hint.get_width() - 24, r.y + 22))
        pygame.draw.line(surf, theme['border'], (r.x + 1, r.y + 50),
                         (r.right - 1, r.y + 50))

        cols = ['Дата', 'Целей', 'Успех', 'Провал', 'Режим']
        xs = [r.x + 24, r.x + 320, r.x + 410, r.x + 500, r.x + 600]
        for x, name in zip(xs, cols):
            surf.blit(book.render(name, 9, theme['fg_dim']), (x, r.y + 60))
        pygame.draw.line(surf, theme['border'], (r.x + 16, r.y + 76),
                         (r.right - 16, r.y + 76))

        entries = list(reversed(self.history_entries))
        rows = max(1, (r.height - 150) // 20)
        self.history_scroll = max(0, min(max(0, len(entries) - rows),
                                         self.history_scroll))
        y = r.y + 84
        if not entries:
            surf.blit(book.render('пока пусто — проведи первую атаку', 10,
                                  theme['muted']), (r.x + 24, y))
        for e in entries[self.history_scroll:self.history_scroll + rows]:
            color = theme['accent'] if e['completed'] else theme['fg_dim']
            if e['failed']:
                color = theme['warning']
            values = [e['date'], str(e['targets']), str(e['completed']),
                      str(e['failed']), e['mode']]
            for x, value in zip(xs, values):
                surf.blit(book.render(value, 9, color), (x, y))
            y += 20

        s = history.summary(self.history_entries)
        foot = (f"Атак: {s['attacks']}   целей: {s['targets']}   "
                f"успешно: {s['completed']}   провалено: {s['failed']}")
        img = book.render(foot, 10, theme['fg_main'])
        surf.blit(img, (r.x + 24, r.bottom - 34))

    # ── консоль отладки ─────────────────────────────────────────────────
    def _draw_console(self, surf, W: int, H: int) -> None:
        theme, book = self.theme, self.book
        dim = pygame.Surface((W, H))
        dim.fill((0, 0, 0))
        dim.set_alpha(190)
        surf.blit(dim, (0, 0))

        w, h = 820, 460
        r = pygame.Rect((W - w) // 2, (H - h) // 2, w, h)
        pygame.draw.rect(surf, (0, 0, 0), r)
        pygame.draw.rect(surf, theme['accent'], r, 1)

        title = book.render('🖥 DEBUG CONSOLE', 14, theme['accent'],
                            chain=['jetbrains_bold', 'symbols', 'emoji'])
        surf.blit(title, (r.x + 18, r.y + 12))
        hint = book.render('F1 / ` — закрыть   ·   help — команды', 9, theme['muted'])
        surf.blit(hint, (r.right - hint.get_width() - 18, r.y + 16))

        # вывод
        out = pygame.Rect(r.x + 14, r.y + 44, r.width - 28, r.height - 96)
        pygame.draw.rect(surf, (0, 0, 0), out)
        pygame.draw.rect(surf, theme['border'], out, 1)
        lines = self.console.output
        rows = self.console.VISIBLE
        end = len(lines) - self.console.scroll
        start = max(0, end - rows)
        y = out.y + 6
        for line in lines[start:max(0, end)]:
            img = book.render(line[:110], 10, theme['accent'])
            surf.blit(img, (out.x + 8, y))
            y += 15

        # ввод
        field = pygame.Rect(r.x + 14, out.bottom + 10, r.width - 28, 30)
        pygame.draw.rect(surf, (0, 0, 0), field)
        pygame.draw.rect(surf, theme['accent'], field, 1)
        prompt = book.render('>', 12, theme['accent'],
                             chain=['jetbrains_bold', 'symbols'])
        surf.blit(prompt, (field.x + 8, field.centery - prompt.get_height() // 2))
        text = book.render(self.console.input, 11, theme['fg_main'])
        surf.blit(text, (field.x + 26, field.centery - text.get_height() // 2))
        if int(self.time * 2) % 2 == 0:
            cx = field.x + 28 + text.get_width()
            pygame.draw.line(surf, theme['accent'], (cx, field.y + 7),
                             (cx, field.bottom - 7))

    # ── окно навыков ────────────────────────────────────────────────────
    SKILL_LABELS = {
        'hacking_speed': ('🚀 Скорость взлома', 'ускоряет симуляцию'),
        'minigame_difficulty': ('🎮 Лёгкость мини-игр', 'проще мини-игры'),
        'earning_rate': ('💰 Доход', 'больше денег за взлом'),
        'stealth': ('👻 Скрытность', 'дольше не палят'),
    }

    def _draw_skills(self, surf, W: int, H: int) -> None:
        theme, book = self.theme, self.book
        dim = pygame.Surface((W, H))
        dim.fill((0, 0, 0))
        dim.set_alpha(170)
        surf.blit(dim, (0, 0))

        w, h = 560, 420
        r = pygame.Rect((W - w) // 2, (H - h) // 2, w, h)
        self.skills_modal = r
        pygame.draw.rect(surf, theme['bg_dark'], r)
        pygame.draw.rect(surf, theme['accent'], r, 1)

        title = book.render('⚡ НАВЫКИ ХАКЕРА', 16, theme['fg_main'],
                            chain=['jetbrains_bold', 'symbols', 'emoji'])
        surf.blit(title, (r.x + 24, r.y + 16))
        sp = book.render(f'Доступно SP: {self.player.skill_points}', 11, theme['accent'])
        surf.blit(sp, (r.right - sp.get_width() - 24, r.y + 20))
        pygame.draw.line(surf, theme['border'], (r.x + 1, r.y + 52), (r.right - 1, r.y + 52))

        self.skill_buttons = {}
        y = r.y + 64
        for sid, (name, desc) in self.SKILL_LABELS.items():
            level = self.player.skills[sid]
            cost = skill_cost(sid, level)
            row = pygame.Rect(r.x + 16, y, r.width - 32, 76)
            pygame.draw.rect(surf, theme['bg_medium'], row)
            pygame.draw.rect(surf, theme['border'], row, 1)

            surf.blit(book.render(name, 11, theme['fg_main'],
                                  chain=['jetbrains_bold', 'symbols', 'emoji']),
                      (row.x + 12, row.y + 10))
            surf.blit(book.render(desc, 8, theme['fg_dim']), (row.x + 12, row.y + 28))
            bar = self.player.bar(sid)
            surf.blit(book.render(f'{bar} ур. {level}/{MAX_LEVEL}', 9, theme['accent']),
                      (row.x + 12, row.y + 44))

            btn = pygame.Rect(row.right - 132, row.y + 22, 118, 32)
            self.skill_buttons[sid] = btn
            can = self.player.can_upgrade(sid)
            if level >= MAX_LEVEL:
                label, color, border = 'MAX', theme['accent'], theme['border']
            else:
                label = f'▲ ${cost} + 1 SP'
                color = theme['warning'] if can else theme['muted']
                border = theme['accent'] if can else theme['border']
            pygame.draw.rect(surf, theme['bg_dark'], btn)
            pygame.draw.rect(surf, border, btn, 1)
            img = book.render(label, 9, color)
            surf.blit(img, (btn.centerx - img.get_width() // 2,
                            btn.centery - img.get_height() // 2))
            y += 84

        hint = book.render('Клик по кнопке — купить уровень.  ESC — закрыть', 9, theme['muted'])
        surf.blit(hint, (r.x + 24, r.bottom - 24))

    # ── ввод имени ──────────────────────────────────────────────────────
    def _draw_name_prompt(self, surf, W: int, H: int) -> None:
        theme, book = self.theme, self.book
        dim = pygame.Surface((W, H))
        dim.fill((0, 0, 0))
        dim.set_alpha(190)
        surf.blit(dim, (0, 0))

        box = pygame.Rect((W - 520) // 2, (H - 200) // 2, 520, 200)
        pygame.draw.rect(surf, theme['bg_dark'], box)
        pygame.draw.rect(surf, theme['accent'], box, 1)

        t1 = book.render('👤 ПРЕДСТАВЬСЯ, ХАКЕР', 18, theme['fg_main'],
                         chain=['jetbrains_bold', 'symbols', 'emoji'])
        surf.blit(t1, (box.centerx - t1.get_width() // 2, box.y + 26))

        field = pygame.Rect(box.x + 60, box.y + 78, box.width - 120, 40)
        pygame.draw.rect(surf, theme['bg_medium'], field)
        pygame.draw.rect(surf, theme['accent'], field, 1)
        text = self.name_input or ''
        img = book.render(text, 16, theme['fg_main'])
        surf.blit(img, (field.x + 12, field.centery - img.get_height() // 2))
        if int(self.time * 2) % 2 == 0:
            cx = field.x + 12 + img.get_width() + 2
            pygame.draw.line(surf, theme['accent'], (cx, field.y + 8),
                             (cx, field.bottom - 8))

        hint = book.render('Введи имя и нажми Enter', 9, theme['muted'])
        surf.blit(hint, (box.centerx - hint.get_width() // 2, box.bottom - 34))

    def _menu_caption(self, surf, text: str, rect_or_x, y: int | None = None) -> None:
        """Подпись над виджетом (или на заданной высоте y)."""
        theme, book = self.theme, self.book
        if y is None:
            x, y = rect_or_x.x, rect_or_x.y - 22
        else:
            x = rect_or_x
        img = book.render(text, 10, theme['fg_dim'])
        surf.blit(img, (x, y))


def main() -> int:
    return App().run()


if __name__ == '__main__':
    sys.exit(main())
