"""Мини-игры: восемь штук, все на общем каркасе.

Отличия от tkinter-версии:
  * ни одного `window.after()` — всё на dt, поэтому анимация одинаковая
    на 30 и 144 Гц, а пауза игры ничего не ломает;
  * игры возвращают результат через `result` (True/False), а не через
    колбэки с задержками;
  * лабиринт каждый раз новый (в legacy был один и тот же);
  * у бомбы видно, какой провод уже режется;
  * в наборе кода подсвечивается, какой символ разошёлся;
  * крестики-нолики: бот иногда думает, но всё ещё проигрывает.

Координаты — логические. Игры рисуются в модальном окне поверх сцены.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

import pygame

from .theme import Theme

MODAL_W, MODAL_H = 640, 520


@dataclass
class Minigame:
    """База: заголовок, подсказка, таймер, результат."""

    title: str = 'МИНИ-ИГРА'
    hint: str = ''
    target: str = ''
    time_limit: float = 0.0

    result: bool | None = None
    result_text: str = ''
    finished: float = 0.0          # сколько секунд прошло после исхода
    elapsed: float = 0.0
    rng: random.Random = field(default_factory=random.Random)

    # ── жизненный цикл ──────────────────────────────────────────────────
    def update(self, dt: float) -> None:
        if self.result is not None:
            self.finished += dt
            return
        self.elapsed += dt
        if self.time_limit and self.elapsed >= self.time_limit:
            self.lose('⏱ ВРЕМЯ ВЫШЛО')
            return
        self.tick(dt)

    def tick(self, dt: float) -> None:
        """Игровая логика конкретной игры."""

    def handle(self, event) -> None:
        """Клавиши и клики (координаты уже логические)."""

    def win(self, text: str = 'ВЗЛОМ УДАЛСЯ') -> None:
        self.result = True
        self.result_text = text

    def lose(self, text: str = 'ПРОВАЛ') -> None:
        self.result = False
        self.result_text = text

    @property
    def time_left(self) -> float:
        return max(0.0, self.time_limit - self.elapsed)

    # ── отрисовка ───────────────────────────────────────────────────────
    def modal_rect(self, W: int, H: int) -> pygame.Rect:
        return pygame.Rect((W - MODAL_W) // 2, (H - MODAL_H) // 2, MODAL_W, MODAL_H)

    def draw(self, surf, W: int, H: int, theme: Theme, book) -> None:
        dim = pygame.Surface((W, H))
        dim.fill((0, 0, 0))
        dim.set_alpha(200)
        surf.blit(dim, (0, 0))

        r = self.modal_rect(W, H)
        pygame.draw.rect(surf, theme['bg_dark'], r)
        pygame.draw.rect(surf, theme['alert'], r, 2)

        t = book.render(self.title, 17, theme['alert'],
                        chain=['jetbrains_bold', 'symbols', 'emoji'])
        surf.blit(t, (r.x + 22, r.y + 16))
        if self.target:
            sub = book.render(self.target, 9, theme['fg_dim'])
            surf.blit(sub, (r.x + 22, r.y + 40))

        # таймер справа
        if self.time_limit:
            urgent = self.time_left <= max(3.0, self.time_limit * 0.25)
            color = theme['error'] if urgent else theme['fg_main']
            left = book.render(f'⏱ {int(self.time_left + 0.99)}', 14, color,
                               chain=['jetbrains_bold', 'symbols', 'emoji'])
            surf.blit(left, (r.right - left.get_width() - 22, r.y + 16))

        pygame.draw.line(surf, theme['border'], (r.x + 1, r.y + 60),
                         (r.right - 1, r.y + 60))

        if self.hint:
            h = book.render(self.hint, 10, theme['fg_dim'])
            surf.blit(h, (r.x + 22, r.y + 68))

        self.paint(surf, r, theme, book)

        if self.result is not None:
            # содержимое гасим полностью: иначе текст игры просвечивает
            # сквозь надпись исхода и получается каша
            overlay = pygame.Surface((r.width, r.height))
            overlay.fill(theme['bg_dark'])
            surf.blit(overlay, r.topleft)
            pygame.draw.rect(surf, theme['alert'] if self.result else theme['error'],
                             r, 2)
            color = theme['accent'] if self.result else theme['error']
            img = book.render(self.result_text, 22, color,
                              chain=['jetbrains_bold', 'symbols', 'emoji'])
            surf.blit(img, (r.centerx - img.get_width() // 2,
                            r.centery - img.get_height() // 2))
            sub = book.render('продолжаем…', 9, theme['muted'])
            surf.blit(sub, (r.centerx - sub.get_width() // 2, r.centery + 26))

    def paint(self, surf, r: pygame.Rect, theme: Theme, book) -> None:
        """Отрисовка содержимого игры."""


# ═══════════════════════════════════════════════════════════════════════
# 1. Камень-ножницы-бумага
# ═══════════════════════════════════════════════════════════════════════
CHOICES = [('камень', '🪨'), ('ножницы', '✂'), ('бумага', '📄')]
BEATS = {'камень': 'ножницы', 'ножницы': 'бумага', 'бумага': 'камень'}


@dataclass
class RockPaperScissors(Minigame):
    title: str = '⚠ АНТИВИРУС: КАМЕНЬ-НОЖНИЦЫ-БУМАГА'
    hint: str = 'Победи антивирус дважды. Бот слегка предсказуем 😉'
    rounds_to_win: int = 2
    time_limit: float = 60.0
    player_score: int = 0
    bot_score: int = 0
    reveal: float = 0.0
    last_player: str = ''
    last_bot: str = ''
    message: str = 'Твой ход'

    def play(self, choice: str) -> None:
        if self.result is not None or self.reveal > 0:
            return
        # как в legacy: 10% — контрит, 10% — ничья, 80% — проигрывает
        roll = self.rng.random()
        if roll < 0.10:
            bot = {v: k for k, v in BEATS.items()}[choice]
        elif roll < 0.20:
            bot = choice
        else:
            bot = BEATS[choice]

        self.last_player, self.last_bot = choice, bot
        self.reveal = 1.2
        if bot == choice:
            self.message = '— Ничья'
        elif BEATS[choice] == bot:
            self.player_score += 1
            self.message = '✓ Раунд твой'
        else:
            self.bot_score += 1
            self.message = '✗ Раунд антивируса'

        if self.result is None:
            if self.player_score >= self.rounds_to_win:
                self.result = True
                self.result_text = '🎉 АНТИВИРУС ПОБЕЖДЁН'
            elif self.bot_score >= self.rounds_to_win:
                self.result = False
                self.result_text = '💀 АНТИВИРУС ПОБЕДИЛ'

    def tick(self, dt: float) -> None:
        if self.reveal > 0:
            self.reveal -= dt

    def handle(self, event) -> None:
        if event.type == pygame.KEYDOWN:
            keys = {pygame.K_1: 'камень', pygame.K_2: 'ножницы', pygame.K_3: 'бумага'}
            if event.key in keys:
                self.play(keys[event.key])
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, (name, _) in enumerate(CHOICES):
                if self.button_rect(i).collidepoint(event.pos):
                    self.play(name)

    def button_rect(self, i: int) -> pygame.Rect:
        return pygame.Rect(self._modal.x + 40 + i * 190, self._modal.bottom - 150, 170, 70)

    def paint(self, surf, r, theme, book) -> None:
        self._modal = r
        score = book.render(f'Ты: {self.player_score}   антивирус: {self.bot_score}',
                            16, theme['fg_main'],
                            chain=['jetbrains_bold', 'symbols', 'emoji'])
        surf.blit(score, (r.centerx - score.get_width() // 2, r.y + 120))

        if self.reveal > 0:
            you = dict(CHOICES)[self.last_player]
            bot = dict(CHOICES)[self.last_bot]
            box = pygame.Rect(r.x + 120, r.y + 180, r.width - 240, 110)
            pygame.draw.rect(surf, theme['bg_medium'], box)
            pygame.draw.rect(surf, theme['border'], box, 1)
            a = book.render(you, 40, theme['accent'], chain=['emoji'])
            b = book.render(bot, 40, theme['error'], chain=['emoji'])
            surf.blit(a, (box.x + 60, box.centery - a.get_height() // 2))
            surf.blit(b, (box.right - 60 - b.get_width(),
                          box.centery - b.get_height() // 2))
            vs = book.render('VS', 14, theme['fg_dim'],
                             chain=['jetbrains_bold', 'symbols'])
            surf.blit(vs, (box.centerx - vs.get_width() // 2,
                           box.centery - vs.get_height() // 2))

        msg = book.render(self.message, 12, theme['warning'])
        surf.blit(msg, (r.centerx - msg.get_width() // 2, r.y + 310))

        for i, (name, icon) in enumerate(CHOICES):
            b = self.button_rect(i)
            pygame.draw.rect(surf, theme['bg_medium'], b)
            pygame.draw.rect(surf, theme['border'], b, 1)
            img = book.render(icon, 24, theme['fg_main'], chain=['emoji'])
            surf.blit(img, (b.x + 14, b.centery - img.get_height() // 2))
            label = book.render(f'{i + 1}. {name}', 11, theme['fg_main'])
            surf.blit(label, (b.x + 48, b.centery - label.get_height() // 2))


# ═══════════════════════════════════════════════════════════════════════
# 2. Крестики-нолики
# ═══════════════════════════════════════════════════════════════════════
WINS = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6)]


@dataclass
class TicTacToe(Minigame):
    title: str = '⚠ ФАЙРВОЛЛ: КРЕСТИКИ-НОЛИКИ'
    hint: str = 'Ты — X, файрволл — O. Ничья тоже считается победой'
    time_limit: float = 90.0
    board: list = field(default_factory=lambda: [''] * 9)
    bot_delay: float = 0.0
    message: str = 'Твой ход'
    win_line: tuple = ()

    def handle(self, event) -> None:
        if self.result is not None or self.bot_delay > 0:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i in range(9):
                if self.cell_rect(i).collidepoint(event.pos) and not self.board[i]:
                    self.player_move(i)
                    return

    def player_move(self, idx: int) -> None:
        self.board[idx] = 'X'
        line = self._winner('X')
        if line:
            self.win_line = line
            self.result = True
            self.result_text = '🎉 ФАЙРВОЛЛ ПРОБИТ'
            return
        if '' not in self.board:
            self.result = True
            self.result_text = 'Ничья — но защита снята'
            return
        self.bot_delay = 0.45
        self.message = 'файрволл думает…'

    def tick(self, dt: float) -> None:
        if self.bot_delay > 0 and self.result is None:
            self.bot_delay -= dt
            if self.bot_delay <= 0:
                self.bot_move()

    def bot_move(self) -> None:
        empty = [i for i, v in enumerate(self.board) if not v]
        if not empty:
            return
        # 35% умных ходов: иногда выигрывает, иногда блокирует
        move = None
        if self.rng.random() < 0.35:
            move = self._find('O') or self._find('X')
        if move is None:
            move = self.rng.choice(empty)
        self.board[move] = 'O'

        line = self._winner('O')
        if line:
            self.win_line = line
            self.result = False
            self.result_text = '💀 ФАЙРВОЛЛ ВЫСТОЯЛ'
            return
        if '' not in self.board:
            self.result = True
            self.result_text = 'Ничья — но защита снята'
            return
        self.message = 'Твой ход'

    def _find(self, mark: str) -> int | None:
        for i, v in enumerate(self.board):
            if v:
                continue
            self.board[i] = mark
            won = self._winner(mark)
            self.board[i] = ''
            if won:
                return i
        return None

    def _winner(self, mark: str):
        for a, b, c in WINS:
            if self.board[a] == self.board[b] == self.board[c] == mark:
                return (a, b, c)
        return ()

    def cell_rect(self, i: int) -> pygame.Rect:
        size = 96
        ox = self._modal.centerx - size * 3 // 2
        oy = self._modal.y + 150
        return pygame.Rect(ox + (i % 3) * (size + 6), oy + (i // 3) * (size + 6),
                           size, size)

    def paint(self, surf, r, theme, book) -> None:
        self._modal = r
        for i in range(9):
            c = self.cell_rect(i)
            pygame.draw.rect(surf, theme['bg_medium'], c)
            mark = self.board[i]
            if mark:
                color = theme['accent'] if mark == 'X' else theme['error']
                img = book.render(mark, 46, color,
                                  chain=['jetbrains_bold', 'symbols'])
                surf.blit(img, (c.centerx - img.get_width() // 2,
                                c.centery - img.get_height() // 2))
            elif self.win_line:
                pass
            if not mark and self.result is None and self.bot_delay <= 0:
                pygame.draw.rect(surf, theme['border'], c, 1)

        # линия победы
        if self.win_line:
            a, _, c = self.win_line
            ra, rc = self.cell_rect(a), self.cell_rect(c)
            color = theme['accent'] if self.board[a] == 'X' else theme['error']
            pygame.draw.line(surf, color, ra.center, rc.center, 3)

        msg = book.render(self.message, 11, theme['fg_dim'])
        surf.blit(msg, (r.centerx - msg.get_width() // 2, r.bottom - 52))


# ═══════════════════════════════════════════════════════════════════════
# 3. Саймон: повтори последовательность
# ═══════════════════════════════════════════════════════════════════════
SIMON_COLORS = ['#ff4444', '#44ff88', '#4488ff', '#ffcc00']
SIMON_DIM = ['#551616', '#165522', '#162255', '#554416']


@dataclass
class SimonSays(Minigame):
    title: str = '⚠ ШИФРОВАНИЕ: ПОВТОРИ КОД'
    hint: str = 'Смотри последовательность и повтори её. Три раунда.'
    time_limit: float = 90.0
    rounds_to_win: int = 3
    sequence: list = field(default_factory=list)
    input_len: int = 0
    round: int = 0
    showing: bool = False
    lit: int = -1
    flash: float = 0.0
    phase: float = 0.0        # таймер между вспышками
    step: int = 0
    message: str = 'Приготовься…'

    next_round: bool = True
    _started: bool = False

    def __post_init__(self):
        self.phase = 0.8

    def tick(self, dt: float) -> None:
        self.phase -= dt
        if self.flash > 0:
            self.flash -= dt
            if self.flash <= 0:
                self.lit = -1

        if self.next_round and self.phase <= 0:
            self.next_round = False
            self.round += 1
            self.sequence.append(self.rng.randint(0, 3))
            self.input_len = 0
            self.showing = True
            self.step = 0
            self.message = 'Запоминай…'
            self.phase = 0.35           # пауза перед первой вспышкой
            return

        if self.showing and self.phase <= 0:
            if self.lit >= 0:
                self.lit = -1
                self.phase = 0.18
                return
            if self.step >= len(self.sequence):
                self.showing = False
                self.message = 'Твой ход'
                return
            self.lit = self.sequence[self.step]
            self.step += 1
            self.flash = 0.4
            self.phase = 0.5
            return

    def press(self, idx: int) -> None:
        if self.showing or self.result is not None or self.next_round:
            return
        self.lit, self.flash = idx, 0.16
        if idx != self.sequence[self.input_len]:
            self.result = False
            self.result_text = '💀 КОД НЕ СОВПАЛ'
            return
        self.input_len += 1
        if self.input_len == len(self.sequence):
            if self.round >= self.rounds_to_win:
                self.result = True
                self.result_text = '🎉 КАНАЛ РАСШИФРОВАН'
            else:
                self.message = '✓ Верно!'
                self.next_round = True
                self.phase = 0.6

    def handle(self, event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i in range(4):
                if self.pad_rect(i).collidepoint(event.pos):
                    self.press(i)
                    return
        elif event.type == pygame.KEYDOWN:
            keys = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3}
            if event.key in keys:
                self.press(keys[event.key])

    def pad_rect(self, i: int) -> pygame.Rect:
        size = 130
        ox = self._modal.centerx - size - 8
        oy = self._modal.y + 130
        return pygame.Rect(ox + (i % 2) * (size + 16), oy + (i // 2) * (size + 16),
                           size, size)

    def paint(self, surf, r, theme, book) -> None:
        self._modal = r
        info = book.render(f'Раунд {min(self.round, self.rounds_to_win)}'
                           f' / {self.rounds_to_win}', 12, theme['warning'])
        surf.blit(info, (r.centerx - info.get_width() // 2, r.y + 98))

        for i in range(4):
            pad = self.pad_rect(i)
            color = SIMON_COLORS[i] if self.lit == i else SIMON_DIM[i]
            pygame.draw.rect(surf, _hex(color), pad)
            pygame.draw.rect(surf, theme['border'], pad, 1)
            num = book.render(str(i + 1), 12, theme['bg_dark'])
            surf.blit(num, (pad.x + 8, pad.y + 6))

        msg = book.render(self.message, 11, theme['fg_dim'])
        surf.blit(msg, (r.centerx - msg.get_width() // 2, r.bottom - 52))


def _hex(value: str) -> tuple[int, int, int]:
    value = value.lstrip('#')
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


# ═══════════════════════════════════════════════════════════════════════
# 4. Бомба: перережь провод
# ═══════════════════════════════════════════════════════════════════════
WIRES = [('КРАСНЫЙ', '#ff4444', '#ffdddd'),
         ('СИНИЙ', '#4488ff', '#ddeeff'),
         ('ЗЕЛЁНЫЙ', '#44ff88', '#ddffe8'),
         ('ЖЁЛТЫЙ', '#ffcc00', '#fff8dd'),
         ('БЕЛЫЙ', '#dddddd', '#111111')]


@dataclass
class WireDefuse(Minigame):
    title: str = '⚠ БОМБА: ПЕРЕРЕЖЬ ПРОВОД'
    hint: str = 'Режь провод из подсказки. Ошибка — взрыв.'
    time_limit: float = 25.0
    correct: int = 0
    cut: int = -1
    cut_anim: float = 0.0
    message: str = ''

    def __post_init__(self):
        self.correct = self.rng.randint(0, 4)

    def cut_wire(self, idx: int) -> None:
        if self.result is not None:
            return
        self.cut = idx
        self.cut_anim = 0.0
        if idx == self.correct:
            self.result = True
            self.result_text = '🎉 БОМБА ОБЕЗВРЕЖЕНА'
        else:
            self.result = False
            self.result_text = '💥 НЕ ТОТ ПРОВОД'

    def tick(self, dt: float) -> None:
        if self.cut >= 0:
            self.cut_anim += dt

    def handle(self, event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i in range(5):
                if self.wire_rect(i).collidepoint(event.pos):
                    self.cut_wire(i)
                    return
        elif event.type == pygame.KEYDOWN:
            if pygame.K_1 <= event.key <= pygame.K_5:
                self.cut_wire(event.key - pygame.K_1)

    def wire_rect(self, i: int) -> pygame.Rect:
        return pygame.Rect(self._modal.x + 60, self._modal.y + 118 + i * 44,
                           self._modal.width - 120, 36)

    LABEL_W = 120          # слева под номер и название провода

    def paint(self, surf, r, theme, book) -> None:
        self._modal = r
        for i, (name, color, fg) in enumerate(WIRES):
            row = self.wire_rect(i)
            rgb = _hex(color)
            cut_here = self.cut == i
            # подпись слева, провод — справа от неё
            label = book.render(f'{i + 1}. {name}', 10, theme['fg_main'])
            surf.blit(label, (row.x, row.centery - label.get_height() // 2))
            wx0 = row.x + self.LABEL_W
            wx1 = row.right
            gap = int(min(26, self.cut_anim * 120)) if cut_here else 0
            y = row.centery
            mid = (wx0 + wx1) // 2
            pygame.draw.line(surf, rgb, (wx0, y), (mid - 10 - gap, y), 6)
            pygame.draw.line(surf, rgb, (mid + 10 + gap, y), (wx1, y), 6)
            pygame.draw.circle(surf, _hex(fg), (wx0, y), 4)
            pygame.draw.circle(surf, _hex(fg), (wx1, y), 4)
            # «контакт» посередине — куда бьёт курсор
            pygame.draw.rect(surf, theme['border'], (mid - 5, y - 12, 10, 24), 1)

        box = pygame.Rect(r.x + 60, r.bottom - 108, r.width - 120, 62)
        pygame.draw.rect(surf, theme['bg_medium'], box)
        pygame.draw.rect(surf, theme['accent'], box, 1)
        h1 = book.render('💡 ПОДСКАЗКА', 9, theme['accent'],
                         chain=['jetbrains_bold', 'symbols', 'emoji'])
        surf.blit(h1, (box.centerx - h1.get_width() // 2, box.y + 8))
        h2 = book.render(f'Режь {WIRES[self.correct][0]}!', 18, theme['accent'],
                         chain=['jetbrains_bold', 'symbols'])
        surf.blit(h2, (box.centerx - h2.get_width() // 2, box.y + 26))


# ═══════════════════════════════════════════════════════════════════════
# 5. Набор кода
# ═══════════════════════════════════════════════════════════════════════
CODE_PARTS = ['sudo', 'chmod', '777', 'cat', 'grep', 'awk', 'echo', 'curl',
              'wget', 'python3']


@dataclass
class TypeCode(Minigame):
    title: str = '⚠ АУТЕНТИФИКАЦИЯ: НАБЕРИ КОД'
    hint: str = 'Введи строку точно. 3 попытки, опечатки подсвечиваются.'
    time_limit: float = 40.0
    attempts: int = 3
    code: str = ''
    typed: str = ''
    message: str = ''

    def __post_init__(self):
        parts = self.rng.sample(CODE_PARTS, self.rng.randint(3, 4))
        self.code = ' '.join(parts)

    def submit(self) -> None:
        if self.result is not None:
            return
        if self.typed.strip() == self.code:
            self.result = True
            self.result_text = '🎉 ДОСТУП РАЗРЕШЁН'
            return
        self.attempts -= 1
        wrong = self._first_diff()
        self.typed = ''
        if self.attempts <= 0:
            self.result = False
            self.result_text = '💀 ДОСТУП ЗАПРЕЩЁН'
        else:
            self.message = f'✗ Ошибка в символе {wrong + 1}. Осталось: {self.attempts}'

    def _first_diff(self) -> int:
        for i, ch in enumerate(self.typed):
            if i >= len(self.code) or ch != self.code[i]:
                return i
        return min(len(self.typed), len(self.code))

    def handle(self, event) -> None:
        if event.type != pygame.KEYDOWN or self.result is not None:
            return
        if event.key == pygame.K_RETURN:
            self.submit()
        elif event.key == pygame.K_BACKSPACE:
            self.typed = self.typed[:-1]
        elif event.unicode and event.unicode.isprintable():
            if len(self.typed) < len(self.code) + 8:
                self.typed += event.unicode

    def paint(self, surf, r, theme, book) -> None:
        self._modal = r
        # образец кода
        box = pygame.Rect(r.x + 40, r.y + 112, r.width - 80, 64)
        pygame.draw.rect(surf, theme['bg_medium'], box)
        pygame.draw.rect(surf, theme['border'], box, 1)
        code_img = book.render(self.code, 20, theme['accent'],
                               chain=['jetbrains_bold', 'symbols'])
        surf.blit(code_img, (box.centerx - code_img.get_width() // 2,
                             box.centery - code_img.get_height() // 2))

        # строка ввода
        field = pygame.Rect(r.x + 40, r.y + 200, r.width - 80, 52)
        pygame.draw.rect(surf, theme['bg_dark'], field)
        pygame.draw.rect(surf, theme['accent'], field, 1)
        x = field.x + 12
        for i, ch in enumerate(self.typed):
            ok = i < len(self.code) and ch == self.code[i]
            color = theme['fg_main'] if ok else theme['error']
            img = book.render(ch, 20, color, chain=['jetbrains_bold', 'symbols'])
            surf.blit(img, (x, field.centery - img.get_height() // 2))
            x += img.get_width() + 1
        if int(self.elapsed * 2) % 2 == 0:
            pygame.draw.line(surf, theme['accent'], (x + 2, field.y + 12),
                             (x + 2, field.bottom - 12))

        info = book.render(f'Попытки: {self.attempts}', 11, theme['warning'])
        surf.blit(info, (r.centerx - info.get_width() // 2, field.bottom + 20))
        if self.message:
            msg = book.render(self.message, 11, theme['error'])
            surf.blit(msg, (r.centerx - msg.get_width() // 2, field.bottom + 46))
        tip = book.render('Enter — отправить', 9, theme['muted'])
        surf.blit(tip, (r.centerx - tip.get_width() // 2, r.bottom - 44))


# ═══════════════════════════════════════════════════════════════════════
# 6. Лабиринт
# ═══════════════════════════════════════════════════════════════════════
MAZE_N = 10


@dataclass
class Maze(Minigame):
    title: str = '⚠ ПРОКСИ-ЛАБИРИНТ'
    hint: str = 'Доведи точку до выхода. Стрелки или WASD.'
    maze: list = field(default_factory=list)
    pos: tuple = (0, 0)
    moves: int = 0
    trail: list = field(default_factory=list)
    time_limit: float = 0.0

    def __post_init__(self):
        self.maze = self._generate()
        self.pos = (1, 1)
        self.trail = [self.pos]

    def _generate(self) -> list[list[int]]:
        """Случайный лабиринт «идеальный»: ровно один путь, выход гарантирован.

        Клетки с обеими нечётными координатами — комнаты, между ними рубим
        проходы. Выход ставим на комнату в правом нижнем углу, а не на
        произвольную клетку (иначе он мог оказаться внутри стены).
        """
        n = MAZE_N
        grid = [[1] * n for _ in range(n)]
        start = (1, 1)
        grid[1][1] = 0
        stack = [start]
        while stack:
            r, c = stack[-1]
            options = []
            for dr, dc in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                nr, nc = r + dr, c + dc
                if 0 < nr < n and 0 < nc < n and grid[nr][nc] == 1:
                    options.append((nr, nc, dr, dc))
            if not options:
                stack.pop()
                continue
            nr, nc, dr, dc = self.rng.choice(options)
            grid[r + dr // 2][c + dc // 2] = 0
            grid[nr][nc] = 0
            stack.append((nr, nc))

        # 9-я строка/столбец — рамка-стена, поэтому дальняя комната это (8, 8)
        grid[MAZE_N - 2][MAZE_N - 2] = 3
        return grid

    def move(self, dr: int, dc: int) -> None:
        if self.result is not None:
            return
        r, c = self.pos
        nr, nc = r + dr, c + dc
        if not (0 <= nr < MAZE_N and 0 <= nc < MAZE_N):
            return
        if self.maze[nr][nc] == 1:
            return
        self.pos = (nr, nc)
        self.moves += 1
        self.trail.append(self.pos)
        if len(self.trail) > 120:
            del self.trail[0]
        if self.maze[nr][nc] == 3:
            self.result = True
            self.result_text = f'🎉 ВЫХОД НАЙДЕН за {self.moves} ходов'

    def handle(self, event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        keys = {pygame.K_UP: (-1, 0), pygame.K_w: (-1, 0),
                pygame.K_DOWN: (1, 0), pygame.K_s: (1, 0),
                pygame.K_LEFT: (0, -1), pygame.K_a: (0, -1),
                pygame.K_RIGHT: (0, 1), pygame.K_d: (0, 1)}
        if event.key in keys:
            self.move(*keys[event.key])

    def paint(self, surf, r, theme, book) -> None:
        self._modal = r
        cell = 34
        ox = r.centerx - cell * MAZE_N // 2
        oy = r.y + 100
        for row in range(MAZE_N):
            for col in range(MAZE_N):
                x, y = ox + col * cell, oy + row * cell
                v = self.maze[row][col]
                if v == 1:
                    color = theme['bg_light']
                elif v == 3:
                    color = theme['info']
                else:
                    color = theme['bg_dark']
                pygame.draw.rect(surf, color, (x, y, cell - 1, cell - 1))

        # след
        for i, (tr, tc) in enumerate(self.trail[-40:]):
            alpha = int(40 + 120 * (i / max(1, len(self.trail[-40:]))))
            dot = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(dot, (*theme['accent'], alpha), (4, 4), 3)
            surf.blit(dot, (ox + tc * cell + cell // 2 - 4,
                            oy + tr * cell + cell // 2 - 4))

        pr, pc = self.pos
        cx = ox + pc * cell + cell // 2
        cy = oy + pr * cell + cell // 2
        glow = int(4 + 2 * abs(((self.elapsed * 3) % 2) - 1))
        pygame.draw.circle(surf, theme['accent'], (cx, cy), cell // 3 + glow)
        pygame.draw.circle(surf, theme['fg_main'], (cx, cy), cell // 3)

        info = book.render(f'Ходов: {self.moves}   выход: 🔵', 11, theme['fg_dim'],
                           chain=['jetbrains', 'symbols', 'emoji'])
        surf.blit(info, (r.centerx - info.get_width() // 2, oy + cell * MAZE_N + 12))


# ═══════════════════════════════════════════════════════════════════════
# 7. Сейф
# ═══════════════════════════════════════════════════════════════════════
@dataclass
class SafeCrack(Minigame):
    title: str = '⚠ СЕЙФ: УГАДАЙ КОД'
    hint: str = 'Число от 1 до 100. Семь попыток, диапазон сужается.'
    time_limit: float = 0.0
    secret: int = 0
    attempts: int = 7
    typed: str = ''
    lo: int = 1
    hi: int = 100
    history: list = field(default_factory=list)
    message: str = 'Введи число'

    def __post_init__(self):
        self.secret = self.rng.randint(1, 100)

    def submit(self) -> None:
        if self.result is not None:
            return
        try:
            guess = int(self.typed)
        except ValueError:
            self.message = '⚠ Нужно число'
            return
        self.typed = ''
        if not 1 <= guess <= 100:
            self.message = '⚠ Только 1–100'
            return
        self.attempts -= 1
        if guess == self.secret:
            self.result = True
            self.result_text = f'🎉 СЕЙФ ОТКРЫТ (код {self.secret})'
            return
        self.history.append(guess)
        if guess < self.secret:
            self.lo = max(self.lo, guess + 1)
            self.message = f'↑ Больше (больше {guess})'
        else:
            self.hi = min(self.hi, guess - 1)
            self.message = f'↓ Меньше (меньше {guess})'
        if self.attempts <= 0:
            self.result = False
            self.result_text = f'💀 НЕ УГАДАЛ (было {self.secret})'

    def handle(self, event) -> None:
        if event.type != pygame.KEYDOWN or self.result is not None:
            return
        if event.key == pygame.K_RETURN:
            self.submit()
        elif event.key == pygame.K_BACKSPACE:
            self.typed = self.typed[:-1]
        elif event.unicode and event.unicode.isdigit() and len(self.typed) < 3:
            self.typed += event.unicode

    def paint(self, surf, r, theme, book) -> None:
        self._modal = r
        field = pygame.Rect(r.centerx - 110, r.y + 130, 220, 64)
        pygame.draw.rect(surf, theme['bg_medium'], field)
        pygame.draw.rect(surf, theme['accent'], field, 2)
        img = book.render(self.typed or '??', 30, theme['accent'],
                          chain=['jetbrains_bold', 'symbols'])
        surf.blit(img, (field.centerx - img.get_width() // 2,
                        field.centery - img.get_height() // 2))

        msg = book.render(self.message, 13, theme['warning'])
        surf.blit(msg, (r.centerx - msg.get_width() // 2, field.bottom + 18))

        rng = book.render(f'Диапазон: {self.lo} — {self.hi}', 12, theme['fg_main'])
        surf.blit(rng, (r.centerx - rng.get_width() // 2, field.bottom + 48))

        # шкала
        bar = pygame.Rect(r.x + 80, field.bottom + 84, r.width - 160, 12)
        pygame.draw.rect(surf, theme['bg_medium'], bar)
        span = max(1, 100)
        x0 = bar.x + int((self.lo - 1) / span * bar.width)
        x1 = bar.x + int(self.hi / span * bar.width)
        pygame.draw.rect(surf, theme['accent'], (x0, bar.y, max(4, x1 - x0), bar.height))
        pygame.draw.rect(surf, theme['border'], bar, 1)

        left = book.render(f'Попыток: {self.attempts}', 12,
                           theme['error'] if self.attempts <= 2 else theme['fg_dim'])
        surf.blit(left, (r.x + 40, r.y + 84))

        if self.history:
            hist = '  '.join(str(g) for g in self.history)
            h = book.render(f'Было: {hist}', 10, theme['muted'])
            surf.blit(h, (r.centerx - h.get_width() // 2, r.bottom - 46))


# ═══════════════════════════════════════════════════════════════════════
# 8. Математика
# ═══════════════════════════════════════════════════════════════════════
@dataclass
class MathGame(Minigame):
    title: str = '⚠ КРИПТОЗАЩИТА: РЕШИ ПРИМЕРЫ'
    hint: str = 'Пять примеров, 45 секунд. Ошибка — новый пример.'
    time_limit: float = 45.0
    needed: int = 5
    solved: int = 0
    problem: str = ''
    answer: int = 0
    typed: str = ''
    message: str = ''

    def __post_init__(self):
        self.problem, self.answer = self._generate()

    def _generate(self) -> tuple[str, int]:
        op = self.rng.choice(['add', 'sub', 'mul', 'div'])
        if op == 'add':
            a, b = self.rng.randint(10, 99), self.rng.randint(1, 9)
            return f'{a} + {b} = ?', a + b
        if op == 'sub':
            a, b = self.rng.randint(10, 99), self.rng.randint(1, 9)
            return f'{a} − {b} = ?', a - b
        if op == 'mul':
            a, b = self.rng.randint(2, 9), self.rng.choice([2, 3, 4, 5, 10])
            return f'{a} × {b} = ?', a * b
        b = self.rng.choice([2, 3, 4, 5, 10])
        result = self.rng.randint(1, max(1, 50 // b))
        return f'{result * b} ÷ {b} = ?', result

    def submit(self) -> None:
        if self.result is not None:
            return
        try:
            value = int(self.typed)
        except ValueError:
            return
        self.typed = ''
        if value == self.answer:
            self.solved += 1
            self.message = '✓ Верно'
            if self.solved >= self.needed:
                self.result = True
                self.result_text = '🎉 КРИПТОЗАЩИТА ПРОБИТА'
                return
            self.problem, self.answer = self._generate()
        else:
            self.message = f'✗ Было {self.answer}'
            self.problem, self.answer = self._generate()

    def handle(self, event) -> None:
        if event.type != pygame.KEYDOWN or self.result is not None:
            return
        if event.key == pygame.K_RETURN:
            self.submit()
        elif event.key == pygame.K_BACKSPACE:
            self.typed = self.typed[:-1]
        elif event.unicode and (event.unicode.isdigit() or
                                (event.unicode == '-' and not self.typed)):
            if len(self.typed) < 5:
                self.typed += event.unicode

    def paint(self, surf, r, theme, book) -> None:
        self._modal = r
        prog = book.render(f'Решено: {self.solved} / {self.needed}', 12, theme['warning'])
        surf.blit(prog, (r.centerx - prog.get_width() // 2, r.y + 94))

        box = pygame.Rect(r.x + 70, r.y + 130, r.width - 140, 90)
        pygame.draw.rect(surf, theme['bg_medium'], box)
        pygame.draw.rect(surf, theme['border'], box, 1)
        problem = book.render(self.problem, 32, theme['accent'],
                              chain=['jetbrains_bold', 'symbols'])
        surf.blit(problem, (box.centerx - problem.get_width() // 2,
                            box.centery - problem.get_height() // 2))

        field = pygame.Rect(r.centerx - 100, r.y + 246, 200, 56)
        pygame.draw.rect(surf, theme['bg_dark'], field)
        pygame.draw.rect(surf, theme['accent'], field, 1)
        img = book.render(self.typed or '_', 26, theme['fg_main'],
                          chain=['jetbrains_bold', 'symbols'])
        surf.blit(img, (field.centerx - img.get_width() // 2,
                        field.centery - img.get_height() // 2))

        if self.message:
            msg = book.render(self.message, 11,
                              theme['accent'] if '✓' in self.message else theme['error'])
            surf.blit(msg, (r.centerx - msg.get_width() // 2, field.bottom + 16))
        tip = book.render('Enter — ответ', 9, theme['muted'])
        surf.blit(tip, (r.centerx - tip.get_width() // 2, r.bottom - 40))


# ═══════════════════════════════════════════════════════════════════════
# фабрика
# ═══════════════════════════════════════════════════════════════════════
GAMES = [
    ('Камень-Ножницы-Бумага', RockPaperScissors),
    ('Крестики-Нолики', TicTacToe),
    ('Последовательность', SimonSays),
    ('Бомба', WireDefuse),
    ('Набор кода', TypeCode),
    ('Лабиринт', Maze),
    ('Сейф', SafeCrack),
    ('Математика', MathGame),
]


def make_game(target: str, rng: random.Random | None = None,
              name: str | None = None) -> Minigame:
    """Создать случайную (или указанную по имени) мини-игру для цели."""
    rng = rng or random.Random()
    if name:
        title, cls = next((t, c) for t, c in GAMES if t == name)
    else:
        title, cls = rng.choice(GAMES)
    return cls(target=target, rng=rng)
