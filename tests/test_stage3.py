"""Тесты Этапа 3: профиль, список целей, карта атак, окно навыков.

Запуск:  python3 tests/test_stage3.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from gamedev.profile import MAX_LEVEL, Player, skill_cost  # noqa: E402
from gamedev.targets import TargetList  # noqa: E402


def _tmp(name: str) -> Path:
    return Path(tempfile.mkdtemp()) / name


# ─────────────────── профиль ───────────────────
def test_player_roundtrip():
    path = _tmp('p.json')
    p = Player(name='NEO', money=500, hacks_completed=7, data_stolen_gb=12.5)
    p.skills['hacking_speed'] = 4
    assert p.save(path)
    loaded = Player.load(path)
    assert loaded.name == 'NEO'
    assert loaded.money == 500
    assert loaded.hacks_completed == 7
    assert abs(loaded.data_stolen_gb - 12.5) < 0.01
    assert loaded.skills['hacking_speed'] == 4


def test_profile_compatible_with_legacy():
    """Файл профиля общий с tkinter-версией — все её поля должны читаться."""
    path = _tmp('legacy.json')
    path.write_text(json.dumps({
        'name': 'Анон', 'money': 100, 'total_earned': 300,
        'hacks_completed': 5, 'hacks_failed': 2, 'data_stolen_gb': 33.3,
        'skill_points': 6,
        'skills': {'hacking_speed': 2, 'minigame_difficulty': 3,
                   'earning_rate': 1, 'stealth': 5},
    }, ensure_ascii=False), encoding='utf-8')
    p = Player.load(path)
    assert (p.money, p.total_earned, p.skill_points) == (100, 300, 6)
    assert p.skills == {'hacking_speed': 2, 'minigame_difficulty': 3,
                        'earning_rate': 1, 'stealth': 5}


def test_profile_survives_garbage():
    for raw in ('{не json', '[]', 'null', '{"money": "много", "skills": "нет"}'):
        path = _tmp('bad.json')
        path.write_text(raw, encoding='utf-8')
        p = Player.load(path)            # не должно падать
        assert isinstance(p.money, int) and p.money >= 0
        assert set(p.skills) == {'hacking_speed', 'minigame_difficulty',
                                'earning_rate', 'stealth'}


def test_levels_clamped():
    p = Player.from_dict({'skills': {'hacking_speed': 999, 'stealth': -5}})
    assert p.skills['hacking_speed'] == MAX_LEVEL
    assert p.skills['stealth'] == 1


def test_skill_cost_matches_legacy_formula():
    # legacy: int(100 * cost_mult * level)
    assert skill_cost('earning_rate', 1) == 150      # множитель 1.5
    assert skill_cost('earning_rate', 3) == 450
    assert skill_cost('hacking_speed', 2) == 200


def test_upgrade_rules():
    p = Player(money=1000, skill_points=2)
    assert p.can_upgrade('hacking_speed')
    assert p.upgrade('hacking_speed')
    assert p.skills['hacking_speed'] == 2
    assert p.skill_points == 1
    assert p.money == 900

    p.skill_points = 0
    assert not p.can_upgrade('hacking_speed'), 'прокачка без SP прошла'
    assert not p.upgrade('hacking_speed')

    rich = Player(money=0, skill_points=9)
    assert not rich.can_upgrade('stealth'), 'прокачка без денег прошла'

    maxed = Player(money=10 ** 6, skill_points=9)
    maxed.skills['stealth'] = MAX_LEVEL
    assert not maxed.can_upgrade('stealth'), 'прокачались выше максимума'


def test_apply_result_uses_earning_skill():
    base = Player()
    earned_base = base.apply_result(2, 1, 10.0, base_reward=100)
    assert earned_base == 100
    assert base.skill_points == 2
    assert base.hacks_completed == 2 and base.hacks_failed == 1

    rich = Player()
    rich.skills['earning_rate'] = 5
    earned_rich = rich.apply_result(2, 0, 10.0, base_reward=100)
    assert earned_rich > earned_base, 'навык дохода не влияет'


def test_skill_bar_length():
    p = Player()
    p.skills['stealth'] = 3
    assert len(p.bar('stealth')) == MAX_LEVEL
    assert p.bar('stealth').count('█') == 3


# ─────────────────── цели ───────────────────
def test_target_queue_order():
    t = TargetList()
    t.toggle(t.items[5])
    t.toggle(t.items[1])
    t.toggle(t.items[9])
    assert t.selected() == [t.items[5], t.items[1], t.items[9]], 'порядок кликов потерян'


def test_target_toggle_removes_and_renumbers():
    t = TargetList()
    for i in (0, 3, 6):
        t.toggle(t.items[i])
    t.toggle(t.items[3])                     # убираем среднюю
    assert t.selected() == [t.items[0], t.items[6]]
    assert t.queue[t.items[6]] == 2, 'номера не пересчитались'
    assert t.click_count == 2


def test_target_search_filters_but_keeps_queue():
    t = TargetList()
    t.toggle(t.items[0])
    for ch in 'git':
        t.type_char(ch)
    visible = t.visible()
    assert visible, 'поиск ничего не нашёл'
    assert all('git' in name for _, name in
               ((i, t.items[i]) for i, _ in visible))
    assert t.selected() == [t.items[0]], 'поиск сбросил очередь'

    t.backspace()
    assert t.filter_text == 'gi'
    t.filter_text = ''
    assert len(t.visible()) == len(t.items)


def test_target_add_custom():
    t = TargetList()
    before = len(t.items)
    added = t.add_custom('мой-сервер')
    assert added == 'мой-сервер / мой-сервер'
    assert len(t.items) == before + 1
    assert t.add_custom('   ') is None
    t.add_custom('мой-сервер / мой-сервер')   # повтор — без дубля
    assert len(t.items) == before + 1


def test_target_scroll_clamped():
    t = TargetList()
    t.scroll_by(-100, 20)
    assert t.scroll == 0
    t.scroll_by(10_000, 20)
    assert t.scroll == len(t.items) - 20


# ─────────────────── карта атак ───────────────────
def test_map_pings_expire():
    import pygame
    from gamedev.attackmap import AttackMap, PING_LIFETIME

    m = AttackMap(pygame.Rect(0, 0, 200, 100), seed=1)
    for _ in range(5):
        m.strike()
    assert len(m.pings) == 5
    m.update(PING_LIFETIME / 2)
    assert len(m.pings) == 5, 'удары гаснут слишком быстро'
    m.update(PING_LIFETIME)
    assert m.pings == [], 'удары не гаснут'


def test_map_ping_cap():
    import pygame
    from gamedev.attackmap import AttackMap

    m = AttackMap(pygame.Rect(0, 0, 200, 100), seed=1)
    for _ in range(200):
        m.strike()
    assert len(m.pings) <= 40, 'точки копятся без предела'


# ─────────────────── связка с приложением ───────────────────
def _app():
    import pygame
    from gamedev.app import App

    app = App()
    app.typing_name = False
    return pygame, app


def test_app_attacks_selected_targets_in_order():
    pygame, app = _app()
    names = [app.targets.items[2], app.targets.items[0]]
    for n in names:
        app.targets.toggle(n)
    app.toggle_attack()
    assert app.attack is not None
    assert app.attack.targets == names, 'атака пошла не в порядке кликов'
    pygame.quit()


def test_app_result_goes_to_profile():
    pygame, app = _app()
    app.player = Player(name='T')            # без записи на диск
    app.targets.toggle(app.targets.items[0])
    app.toggle_attack()
    app.attack.completed, app.attack.failed = 2, 0
    app.attack.stolen_gb = 5.0
    app.attack.money = 400
    app.player.save = lambda *a, **k: True   # не трогаем домашнюю папку
    app.attack.finished = True
    app._pump_attack(0.1)
    assert app.player.hacks_completed >= 2, 'итог атаки не записан в профиль'
    assert app.player.skill_points >= 2
    assert app.attack is None
    pygame.quit()


def test_app_click_toggles_target():
    pygame, app = _app()
    app.draw()                                # чтобы посчиталась геометрия
    row = app.targets_rect
    pos = (row.x + 20, row.y + 6)
    name = app._target_at(pos)
    assert name, 'клик по первой строке не нашёл цель'
    app.targets.toggle(name)
    assert app.targets.queue.get(name) == 1
    pygame.quit()


def test_app_skills_window_opens_and_buys():
    pygame, app = _app()
    app.player = Player(money=1000, skill_points=1)
    app.draw()
    app.skills_open = True
    app.draw()                                # считает кнопки
    btn = app.skill_buttons['hacking_speed']
    app._handle_skills(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, button=1,
        pos=app.screen.to_window(btn.center)))
    assert app.player.skills['hacking_speed'] == 2, 'навык не купился кликом'
    pygame.quit()


def test_app_name_prompt_required_before_attack():
    pygame, app = _app()
    app.typing_name = True
    app.toggle_attack()
    assert app.attack is None, 'атака стартовала без имени'
    app.name_input = 'Тринити'
    app._submit_name()
    assert app.player.name == 'Тринити'
    assert app.typing_name is False
    pygame.quit()


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
