"""Главная сцена pygame-версии (Этап 2: живой лог, матрица, симуляция).

Что уже есть:
  * окно нужного размера (авто-подбор под монитор, смена из настроек);
  * тема применяется на лету;
  * лог с цветными строками, прокруткой и переносом по словам;
  * симуляция взлома — пошаговый автомат, с паузами и прерыванием;
  * режимы атаки (стелс / норм / агрессив) меняют темп и подробность;
  * прогресс, статус и счётчики внизу.

Размер окна меняется только в настройках (RESIZABLE не включаем).
"""

from __future__ import annotations

import datetime as _dt
import random
import sys

import pygame

from . import config, gamedata
from .attack import Attack, LogLine, mode_params
from .background import MatrixRain
from .display import compute_size
from .logpanel import LogView
from .screen import Screen
from .settings import Settings
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
        self.attack: Attack | None = None
        self.paused = False
        self.toasts: list[tuple[str, float, str]] = []

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
                   on_click=self._show_history),
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
        self.attack = Attack(
            targets=targets,
            params=mode_params(self.settings.attack_mode),
            minigame_chance=self.settings.minigame_chance,
            show_calculations=self.settings.show_calculations,
            rng=random.Random())

    def _pick_targets(self) -> list[str]:
        """Пока целей нет — берём случайную (Этап 3 даст выбор)."""
        if getattr(self, 'selected_targets', None):
            return list(self.selected_targets)
        target = random.choice(gamedata.TARGETS)
        self.log_line('⚠ Цель не выбрана, атакую случайную', 'warning')
        return [target]

    def _pump_attack(self, dt: float) -> None:
        if self.attack is None:
            return
        if not self.paused:
            self.attack.update(dt)
        self.log.append(self.attack.drain())

        if self.attack.finished:
            a = self.attack
            self.log_line(f'  Итог: {a.completed} успешно, {a.failed} провалено', 'header')
            if a.money:
                self.log_line(f'  Заработано: ${a.money}', 'success')
            self.attack = None

    # ── настройки ───────────────────────────────────────────────────────
    def _on_theme_change(self, key: str) -> None:
        self.settings.theme = key
        self.theme = Theme(key)          # применяется сразу, без рестарта

    def _on_size_change(self, key: str) -> None:
        self.settings.window_scale = key
        self.apply_window_size()
        self._resize_log()

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

    def _show_history(self) -> None:
        self.log_line('📜 История атак — Этап 3', 'warning')

    # ── главный цикл ─────────────────────────────────────────────────────
    def run(self) -> int:
        while self.running:
            dt = self.clock.tick(self.FPS) / 1000.0
            self.time += dt
            self.handle_events()
            self.matrix.update(dt)
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
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.menu_open:
                        self.menu_open = False
                    elif self.attack:
                        self.toggle_attack()
                    else:
                        self.running = False
                    continue
                if event.key == pygame.K_m and not self.menu_open:
                    self.open_menu()
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
            else:
                if self.log.rect.collidepoint(self._logical(event)):
                    if self.log.handle(event):
                        continue
                for b in self.header_buttons:
                    b.handle(self._menu_event(event))
                for b in self.mode_buttons:
                    b.handle(self._menu_event(event))
                self.attack_btn.handle(self._menu_event(event))

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

        self.screen.blit_to_window()

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

        left = Panel(rect=pygame.Rect(LEFT_X, PANEL_TOP, LEFT_W, height), title='◆ ЦЕЛИ')
        center = Panel(rect=pygame.Rect(CENTER_X, PANEL_TOP, CENTER_W, height),
                       title='◆ КАРТА АТАК / ПРОФИЛЬ')
        right = Panel(rect=pygame.Rect(RIGHT_X, PANEL_TOP, W - RIGHT_X - 8, height),
                      title='◆ EXPLOIT LOG')
        for p in (left, center, right):
            p.draw(surf, theme, book)

        for rect, text in ((left.rect, '► список целей — этап 3'),
                           (center.rect, '► карта атак и профиль — этап 3')):
            img = book.render(text, 9, theme['fg_dim'])
            surf.blit(img, (rect.x + 12, rect.y + 40))

        # кнопка атаки (внутри левой панели)
        self.attack_btn.text = '⏹ СТОП' if self.attack else '◆ ВЗЛОМАТЬ ◆'
        self.attack_btn.draw(surf, theme, book)

        # сам лог
        self.log.draw(surf, theme, book)

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
        if self.paused:
            status = '⏸ ПАУЗА — ' + status
        img = book.render(f'СТАТУС: {status}', 10, theme['fg_main'])
        surf.blit(img, (16, top + 32))

        info = book.render(
            f'окно: {self.size_info.describe()}  │  монитор: {self.monitor[0]}×{self.monitor[1]}'
            f'  │  тема: {self.theme.name}', 8, theme['fg_dim'])
        surf.blit(info, (16, top + 48))

        hint = book.render(
            'ВЗЛОМАТЬ — старт/стоп  │  SPACE — пауза  │  M — настройки  │  ESC — выход',
            8, theme['muted'])
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
