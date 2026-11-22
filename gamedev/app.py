"""Главная сцена pygame-версии (Этап 1: каркас).

Что уже есть:
  * окно нужного размера (авто-подбор под монитор, смена из настроек);
  * тема применяется на лету;
  * фон-«матрица», шапка, панели-заглушки будущих блоков;
  * меню ESC: тема, размер окна, прочие настройки — всё сохраняется в файл.

Изменять размер окна мышью нельзя (RESIZABLE не включаем) — только
через настройки, как и просили.
"""

from __future__ import annotations

import sys

import pygame

from . import config
from .background import MatrixRain
from .display import compute_size
from .screen import Screen
from .settings import Settings
from .theme import Theme
from .widgets import Button, Checkbox, Dropdown, Label, Panel, Slider


class App:
    """Главный цикл каркаса."""

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
        self._build_main_ui()
        self._build_menu_ui()

    # ── сборка интерфейса ────────────────────────────────────────────────
    def _build_main_ui(self) -> None:
        W, H = config.LOGICAL_W, config.LOGICAL_H
        self.header_buttons = [
            Button(rect=pygame.Rect(W - 150, 12, 60, 24), text='⚙ Настройки',
                   size=9, on_click=self.open_menu),
            Button(rect=pygame.Rect(W - 82, 12, 50, 24), text='📜', size=9),
        ]
        self.status_lights = [('DARKNET', True), ('TOR', True), ('VPN', False), ('CRYPTO', True)]

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
                   text='✖ Закрыть', size=10, on_click=lambda: setattr(self, 'menu_open', False)),
        ]

    # ── реакции на настройки ─────────────────────────────────────────────
    def _on_theme_change(self, key: str) -> None:
        self.settings.theme = key
        self.theme = Theme(key)          # применяется сразу, без рестарта

    def _on_size_change(self, key: str) -> None:
        self.settings.window_scale = key
        self.apply_window_size()

    def _on_chance_change(self, value: int) -> None:
        self.settings.minigame_chance = int(value)

    def _on_glitch_change(self, value: bool) -> None:
        self.settings.glitch_enabled = value

    def _on_calc_change(self, value: bool) -> None:
        self.settings.show_calculations = value

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

    # ── главный цикл ─────────────────────────────────────────────────────
    def run(self) -> int:
        while self.running:
            dt = self.clock.tick(self.FPS) / 1000.0
            self.time += dt
            self.handle_events()
            self.matrix.update(dt)
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
                    else:
                        self.running = False
                elif event.key == pygame.K_F11 and self.menu_open:
                    self.save_and_close()
                continue

            if self.menu_open:
                # сначала открытый выпадающий список (он рисуется поверх)
                if self.theme_dd.open and self.theme_dd.handle(self._menu_event(event)):
                    continue
                if self.size_dd.open and self.size_dd.handle(self._menu_event(event)):
                    continue
                for w in self.menu_widgets:
                    w.handle(self._menu_event(event))
                for b in self.menu_buttons:
                    b.handle(self._menu_event(event))
            else:
                for b in self.header_buttons:
                    b.handle(event)

    def _menu_event(self, event):
        """Перевод координат окна в логические для меню."""
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
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
        self._draw_placeholder_panels(surf, W, H)
        self._draw_footer(surf, W, H)

        if self.menu_open:
            self._draw_menu(surf, W, H)

        self.screen.blit_to_window()

    def _draw_header(self, surf, W: int) -> None:
        theme, book = self.theme, self.book
        t = book.render(f'◆ {config.TITLE}', 16, theme['fg_main'], chain=['jetbrains_bold', 'symbols', 'emoji'])
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

        for b in self.header_buttons:
            b.draw(surf, theme, book)

        pygame.draw.line(surf, theme['border'], (8, 46), (W - 8, 46))

    def _draw_placeholder_panels(self, surf, W: int, H: int) -> None:
        theme, book = self.theme, self.book
        top = 56
        bottom = H - 74
        height = bottom - top

        left = Panel(rect=pygame.Rect(8, top, 300, height), title='◆ ЦЕЛИ')
        center = Panel(rect=pygame.Rect(316, top, 300, height), title='◆ КАРТА АТАК / ПРОФИЛЬ')
        right = Panel(rect=pygame.Rect(624, top, W - 632, height), title='◆ EXPLOIT LOG')
        for p in (left, center, right):
            p.draw(surf, theme, book)

        hints = [
            (left.rect, '► список целей появится на этапе 3'),
            (center.rect, '► карта атак и профиль — этап 3'),
            (right.rect, '► живой лог и матрица — этап 2'),
        ]
        for rect, text in hints:
            img = book.render(text, 9, theme['fg_dim'])
            surf.blit(img, (rect.x + 12, rect.y + 40))

        # заготовка под кнопки атаки (внутри левой панели)
        btn = pygame.Rect(left.rect.x + 12, left.rect.bottom - 52, left.rect.width - 24, 36)
        pygame.draw.rect(surf, theme['danger_bg'], btn)
        pygame.draw.rect(surf, theme['error'], btn, 1)
        lbl = book.render('◆ ВЗЛОМАТЬ ◆', 12, theme['error'], chain=['jetbrains_bold', 'symbols', 'emoji'])
        surf.blit(lbl, (btn.centerx - lbl.get_width() // 2,
                        btn.centery - lbl.get_height() // 2))

    def _draw_footer(self, surf, W: int, H: int) -> None:
        theme, book = self.theme, self.book
        pygame.draw.line(surf, theme['border'], (8, H - 66), (W - 8, H - 66))
        status = book.render('СТАТУС: каркас pygame — Этап 1', 10, theme['fg_main'])
        surf.blit(status, (16, H - 56))

        info = book.render(
            f'окно: {self.size_info.describe()}  │  монитор: {self.monitor[0]}×{self.monitor[1]}  │  '
            f'тема: {self.theme.name}', 9, theme['fg_dim'])
        surf.blit(info, (16, H - 36))

        hint = book.render('ESC — выход  │  ⚙ — настройки  │  размер окна меняется только в настройках',
                           9, theme['muted'])
        surf.blit(hint, (16, H - 20))

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

        # ── строка 1: тема и размер окна ──
        self._menu_caption(surf, 'Тема', self.theme_dd.rect)
        self._menu_caption(surf, 'Размер окна', self.size_dd.rect)

        # ── строка 2: шанс мини-игры (слева), предпросмотр размера (справа) ──
        self._menu_caption(surf, f'Шанс мини-игры: {self.settings.minigame_chance}%',
                           self.chance_slider.rect)
        preview = book.render(f'→ окно: {self.size_info.describe()}', 10, theme['muted'])
        surf.blit(preview, (self.size_dd.rect.x, self.chance_slider.rect.y - 6))
        mon = book.render(f'   монитор: {self.monitor[0]}×{self.monitor[1]}', 9, theme['muted'])
        surf.blit(mon, (self.size_dd.rect.x, self.chance_slider.rect.y + 10))

        # ── строка 3: чекбоксы ──
        self._menu_caption(surf, 'Эффекты', self.glitches_cb.rect.x,
                           y=self.glitches_cb.rect.y - 24)

        # ── порядок отрисовки важен: списки рисуем ПОСЛЕДНИМИ,
        #    чтобы раскрытый список не оказался под слайдером/чекбоксами
        dropdowns = [self.theme_dd, self.size_dd]
        for w in self.menu_widgets:
            if w not in dropdowns:
                w.draw(surf, theme, book)
        for b in self.menu_buttons:
            b.draw(surf, theme, book)
        for w in dropdowns:
            w.draw(surf, theme, book)

        # подсказка внизу панели
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
