"""Тесты мини-игр: логика побед/поражений и отрисовка.

Запуск:  python3 tests/test_minigames.py
"""
import os
import random
import sys
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import pygame  # noqa: E402

from gamedev.minigames import (  # noqa: E402
    GAMES, MathGame, Maze, Minigame, RockPaperScissors, SafeCrack, SimonSays,
    TicTacToe, TypeCode, WireDefuse, make_game)


def _surf_book():
    pygame.init()
    from assets.fonts.fontloader import FontBook
    from gamedev.theme import Theme
    return pygame.Surface((1350, 850)), FontBook(pygame), Theme('matrix')


# ─────────────────── общий каркас ───────────────────
def test_all_games_render():
    """Каждая игра рисуется целиком без исключений."""
    surf, book, theme = _surf_book()
    for name, _ in GAMES:
        g = make_game('target / target.com', random.Random(1), name=name)
        for _ in range(20):
            g.update(0.1)
        surf.fill((0, 0, 0))
        g.draw(surf, 1350, 850, theme, book)
    pygame.quit()


def test_make_game_by_name_and_random():
    g = make_game('a.com', random.Random(1), name='Лабиринт')
    assert isinstance(g, Maze)
    seen = {type(make_game('a.com', random.Random(i))).__name__ for i in range(60)}
    assert len(seen) == len(GAMES), 'случайный выбор не покрывает все игры'


def test_game_result_freezes_updates():
    g = Maze(target='t', rng=random.Random(1))
    g.result = True
    g.result_text = 'ok'
    before = g.elapsed
    g.update(1.0)
    assert g.elapsed == before, 'после исхода игра продолжает тикать'
    assert g.finished > 0


# ─────────────────── лабиринт ───────────────────
def test_maze_is_solvable():
    """Каждый сгенерированный лабиринт проходим (BFS от старта до выхода)."""
    from collections import deque

    for seed in range(25):
        g = Maze(target='t', rng=random.Random(seed))
        assert g.maze[1][1] == 0, 'старт в стене'
        assert g.maze[8][8] == 3, 'выход не там'
        seen = {(1, 1)}
        q = deque([(1, 1)])
        while q:
            r, c = q.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (r + dr, c + dc)
                if n in seen or not (0 <= n[0] < 10 and 0 <= n[1] < 10):
                    continue
                if g.maze[n[0]][n[1]] == 1:
                    continue
                seen.add(n)
                q.append(n)
        assert (8, 8) in seen, f'лабиринт {seed} непроходим'


def test_maze_games_differ():
    a = Maze(target='t', rng=random.Random(1)).maze
    b = Maze(target='t', rng=random.Random(2)).maze
    assert a != b, 'лабиринт всегда одинаковый'


def test_maze_walls_block_and_exit_wins():
    g = Maze(target='t', rng=random.Random(3))
    g.pos = (0, 0)
    g.move(-1, 0)                                     # за границу
    assert g.pos == (0, 0)
    g.pos = (1, 1)
    before = g.moves
    g.move(0, 0) if False else None
    # идём в стену, если она есть рядом
    for dr, dc in ((1, 0), (0, 1), (-1, 0), (0, -1)):
        r, c = g.pos
        if g.maze[r + dr][c + dc] == 1:
            g.move(dr, dc)
            assert g.pos == (r, c), 'прошли сквозь стену'
            break
    g.pos = (8, 7)
    g.move(0, 1)
    assert g.result is True, 'выход не сработал'


# ─────────────────── бомба ───────────────────
def test_bomb_correct_wire_wins():
    g = WireDefuse(target='t', rng=random.Random(2))
    g.cut_wire(g.correct)
    assert g.result is True


def test_bomb_wrong_wire_loses():
    g = WireDefuse(target='t', rng=random.Random(2))
    wrong = (g.correct + 1) % 5
    g.cut_wire(wrong)
    assert g.result is False


def test_bomb_timeout_loses():
    g = WireDefuse(target='t', rng=random.Random(1))
    g.update(g.time_limit + 0.1)
    assert g.result is False


# ─────────────────── набор кода ───────────────────
def test_typecode_exact_match_wins():
    g = TypeCode(target='t', rng=random.Random(4))
    g.typed = g.code
    g.submit()
    assert g.result is True


def test_typecode_wrong_keeps_attempts_counting():
    g = TypeCode(target='t', rng=random.Random(4))
    for _ in range(3):
        g.typed = 'заведомо неверно'
        g.submit()
    assert g.result is False
    assert g.attempts == 0


def test_typecode_typing_events():
    g = TypeCode(target='t', rng=random.Random(5))
    for ch in 'abc':
        g.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a, unicode=ch))
    assert g.typed == 'abc'
    g.handle(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE, unicode=''))
    assert g.typed == 'ab'


# ─────────────────── сейф ───────────────────
def test_safe_guess_wins():
    g = SafeCrack(target='t', rng=random.Random(6))
    g.typed = str(g.secret)
    g.submit()
    assert g.result is True


def test_safe_narrows_range():
    g = SafeCrack(target='t', rng=random.Random(6))
    g.secret = 70
    g.typed = '50'
    g.submit()
    assert g.lo == 51, 'нижняя граница не сдвинулась'
    g.typed = '80'
    g.submit()
    assert g.hi == 79, 'верхняя граница не сдвинулась'


def test_safe_runs_out_of_attempts():
    g = SafeCrack(target='t', rng=random.Random(6))
    g.secret = 100
    for _ in range(7):
        g.typed = '1'
        g.submit()
    assert g.result is False


# ─────────────────── математика ───────────────────
def test_math_five_answers_win():
    g = MathGame(target='t', rng=random.Random(7))
    for _ in range(5):
        g.typed = str(g.answer)
        g.submit()
    assert g.result is True
    assert g.solved == 5


def test_math_problems_are_correct():
    """Ответ всегда совпадает с примером — иначе игра нечестная."""
    for seed in range(40):
        g = MathGame(target='t', rng=random.Random(seed))
        for _ in range(10):
            text = g.problem.rstrip('?').replace('=', '').replace('−', '-').replace('×', '*').replace('÷', '/')
            a, op, b = text.split()
            expected = {'+': int(a) + int(b), '-': int(a) - int(b),
                        '*': int(a) * int(b), '/': int(a) // int(b)}[op]
            assert expected == g.answer, f'{g.problem} → {g.answer}, а должно {expected}'
            g.problem, g.answer = g._generate()


# ─────────────────── саймон ───────────────────
def test_simon_sequence_grows_and_wins():
    g = SimonSays(target='t', rng=random.Random(8))
    for _ in range(2000):
        g.update(0.05)
        if not g.showing and not g.next_round and g.sequence:
            for idx in g.sequence[g.input_len:]:
                g.press(idx)
            if g.result is not None:
                break
    assert g.result is True, 'последовательность не удалось повторить'
    assert len(g.sequence) == 3


def test_simon_wrong_press_loses():
    g = SimonSays(target='t', rng=random.Random(8))
    for _ in range(300):
        g.update(0.05)
        if not g.showing and g.sequence and not g.next_round:
            break
    wrong = (g.sequence[0] + 1) % 4
    g.press(wrong)
    assert g.result is False


# ─────────────────── крестики-нолики ───────────────────
def test_tic_tac_toe_win_detected():
    g = TicTacToe(target='t', rng=random.Random(9))
    # бот не должен мешать: замораживаем его ходы
    g.bot_delay = 99
    g.player_move(0)
    g.bot_delay = 99
    g.player_move(1)
    g.bot_delay = 99
    g.player_move(2)
    assert g.result is True, 'три в ряд не засчитаны'
    assert g.win_line == (0, 1, 2)


def test_tic_tac_toe_bot_moves():
    g = TicTacToe(target='t', rng=random.Random(10))
    g.player_move(4)
    g.bot_delay = 0.01
    g.tick(0.05)
    assert g.board.count('O') == 1, 'бот не сходил'


def test_tic_tac_toe_cell_click():
    surf, book, theme = _surf_book()
    g = TicTacToe(target='t', rng=random.Random(11))
    surf.fill((0, 0, 0))
    g.draw(surf, 1350, 850, theme, book)
    cell = g.cell_rect(4)
    g.handle(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                pos=cell.center))
    assert g.board[4] == 'X', 'клик по клетке не поставил X'
    pygame.quit()


# ─────────────────── камень-ножницы-бумага ───────────────────
def test_rps_bot_mostly_loses():
    """Бот задуман «тупым»: в большинстве раундов он проигрывает игроку."""
    wins = 0
    trials = 400
    g = RockPaperScissors(target='t', rng=random.Random(12))
    for _ in range(trials):
        g.player_score = g.bot_score = 0
        g.reveal = 0
        g.result = None
        g.play('камень')
        if g.player_score:
            wins += 1
    assert wins / trials > 0.7, f'бот выигрывает слишком часто: {wins / trials:.0%}'


def test_rps_two_wins_finish_game():
    g = RockPaperScissors(target='t', rng=random.Random(13))
    for _ in range(20):
        if g.result is not None:
            break
        g.reveal = 0
        g.play('камень')
    assert g.result is not None, 'игра не завершилась'


if __name__ == '__main__':
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith('test_')]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f'  ✓ {name}')
        except AssertionError as e:
            failed += 1
            print(f'  ✗ {name}: {e}')
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f'  ✗ {name}: {type(e).__name__}: {e}')
    print(f'\n{len(tests) - failed}/{len(tests)} тестов прошло')
    sys.exit(1 if failed else 0)
