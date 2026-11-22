"""Симуляция взлома: пошаговый автомат вместо потоков со sleep.

В tkinter-версии симуляция крутилась в отдельном потоке и спала
`time.sleep()`. Здесь всё иначе: движок вызывается каждый кадр с dt,
накапливает время и выдаёт события. Отсюда бесплатно получаем:

  * паузу (dt просто не передаётся);
  * мгновенное прерывание (никого не надо убивать — потоков нет);
  * одинаковую скорость на 30 и 144 Гц;
  * предсказуемый тест: проматываем время и проверяем, что получилось.

Модуль не знает про pygame — только логика и данные.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from . import gamedata

# ── типы строк лога (ключи цветов из темы) ──────────────────────────────
LOG_COLORS = {
    'info': 'fg_main',
    'success': 'accent',
    'warning': 'warning',
    'error': 'error',
    'header': 'info',
    'stupid': 'magic',
    'data': 'data',
    'fast': 'fg_dim',
    'calc': 'muted',
    'minigame': 'alert',
    'timestamp': 'muted',
}

PORTS = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 993, 995, 1433, 1521,
         3306, 3389, 5432, 5900, 6379, 8080, 8443, 9200, 27017]
SERVICES = ['HTTP', 'SSH', 'FTP', 'SMTP', 'DNS', 'MySQL', 'PostgreSQL',
            'Redis', 'MongoDB', 'RDP', 'nginx', 'Apache', 'IIS', 'Node.js']
PORT_STATES = ['OPEN', 'OPEN', 'OPEN', 'CLOSED', 'FILTERED']
STATUS_WORDS = {'OPEN': 'OPEN', 'CLOSED': 'CLOSED', 'FILTERED': 'FILTERED'}


@dataclass
class LogLine:
    """Одна строка лога: текст + тип (тип → цвет) + время."""
    text: str
    kind: str = 'info'
    clock: str = ''


@dataclass
class ModeParams:
    """Скорость и подробность для режима атаки (как в legacy)."""
    delay_mult: float = 1.0
    minigame_mult: float = 1.0
    log_detail: str = 'medium'
    mode: str = 'normal'

    @property
    def scan_count(self) -> int:
        return {'low': 10, 'medium': 20, 'high': 35}[self.log_detail]

    @property
    def exploit_count(self) -> int:
        return {'low': 4, 'medium': 7, 'high': 12}[self.log_detail]

    @property
    def data_count(self) -> int:
        return {'low': 5, 'medium': 10, 'high': 18}[self.log_detail]


def mode_params(mode: str, skills: dict | None = None) -> ModeParams:
    """Параметры режима + поправки от прокачанных навыков."""
    if mode == 'stealth':
        p = ModeParams(2.0, 0.3, 'low', mode)
    elif mode == 'aggressive':
        p = ModeParams(0.3, 2.0, 'high', mode)
    else:
        p = ModeParams(1.0, 1.0, 'medium', mode)

    skills = skills or {}
    speed_lvl = max(0, skills.get('hacking_speed', 1) - 1)
    p.delay_mult *= max(0.4, 1.0 - 0.08 * speed_lvl)
    diff_lvl = max(0, skills.get('minigame_difficulty', 1) - 1)
    p.minigame_mult *= max(0.5, 1.0 - 0.06 * diff_lvl)
    stealth_lvl = max(0, skills.get('stealth', 1) - 1)
    p.minigame_mult *= (1.0 - 0.05 * stealth_lvl)
    return p


# ── фазы одной цели ─────────────────────────────────────────────────────
PHASES = ['recon', 'scan', 'minigame', 'exploit', 'access', 'extract', 'done']


@dataclass
class Attack:
    """Прогон по списку целей; шагает по фазам и копит вывод в лог."""

    targets: list[str]
    params: ModeParams
    minigame_chance: int = 20
    show_calculations: bool = True
    rng: random.Random = field(default_factory=random.Random)

    # состояние
    idx: int = 0
    phase: str = 'recon'
    started: bool = False
    finished: bool = False
    progress: float = 0.0
    status: str = 'Ожидание'
    completed: int = 0
    failed: int = 0
    stolen_gb: float = 0.0
    money: int = 0
    # мини-игра: движок ждёт её исхода, а рисует и опрашивает её приложение
    minigame: object = None

    _ip: str = '0.0.0.0'
    _wait: float = 0.0
    _substep: int = 0
    _lines: list[LogLine] = field(default_factory=list)

    # ── служебное ───────────────────────────────────────────────────────
    def _log(self, text: str, kind: str = 'info') -> None:
        self._lines.append(LogLine(text, kind))

    def drain(self) -> list[LogLine]:
        """Забрать накопленные строки (лог сам решает, куда их девать)."""
        out, self._lines = self._lines, []
        return out

    @property
    def current_target(self) -> str:
        return self.targets[self.idx] if self.idx < len(self.targets) else ''

    @property
    def current_name(self) -> str:
        return self.current_target.split(' / ')[0].upper()

    # ── генераторы фейкового текста ─────────────────────────────────────
    def _calc(self) -> str:
        a, b = self.rng.randint(1, 1000), self.rng.randint(-100, 500)
        ops = [('+', a + b), ('-', a - b), ('×', a * b)]
        if b:
            ops.append(('÷', round(a / b, 2)))
        op, res = self.rng.choice(ops)
        return f'    [{a} {op} {b} = {res}]'

    def _hex(self) -> str:
        return ''.join(self.rng.choice('0123456789abcdef') for _ in range(32))

    def _scan_line(self) -> str:
        port = self.rng.choice(PORTS)
        state = self.rng.choice(PORT_STATES)
        service = self.rng.choice(SERVICES)
        template = self.rng.choice(gamedata.SCAN_TEMPLATES)
        try:
            return template.format(port=port, status=state, service=service,
                                   ip=self._ip, hops=0, size=0, count=0)
        except (KeyError, IndexError):
            return f'Порт {port}: {state} ({service})'

    def _data_line(self) -> str:
        template = self.rng.choice(gamedata.DATA_TEMPLATES)
        try:
            return template.format(size=self.rng.randint(100, 999999),
                                   count=self.rng.randint(50, 50000),
                                   mb=self.rng.randint(10, 500),
                                   port=self.rng.choice(PORTS),
                                   service=self.rng.choice(SERVICES),
                                   status='OPEN', ip=self._ip, hops=0)
        except (KeyError, IndexError):
            return 'Данные извлечены'

    # ── шаги ────────────────────────────────────────────────────────────
    def _begin_target(self) -> None:
        self._wait = 0.0
        self._substep = 0
        self.phase = 'recon'
        self.minigame = None
        self._ip = '.'.join(str(self.rng.randint(1, 255)) for _ in range(3)) + \
            f'.{self.rng.randint(1, 254)}'

        target = self.current_target
        self._log('', 'info')
        self._log('─' * 40, 'info')
        self._log(f'  ◆ [{self.idx + 1}/{len(self.targets)}] {target}', 'header')
        self._log('─' * 40, 'info')
        self.status = f'Атакую {self.current_name}'

        if '127.0.0.1' in target or 'localhost' in target:
            self._log('', 'info')
            self._log('  🤔 Ты взламываешь сам себя!', 'warning')
            self._log('  🤔 Это... интересная стратегия', 'warning')

    def _set_progress(self, value: float) -> None:
        self.progress = max(0.0, min(100.0, value))

    def update(self, dt: float) -> None:
        """Продвинуть симуляцию на dt секунд."""
        if self.finished:
            return
        if self.minigame:
            return                        # ждём исхода мини-игры
        if not self.started:
            self.started = True
            if not self.targets:
                self.targets = [self.rng.choice(gamedata.TARGETS)]
            self._log('', 'info')
            self._log('═' * 50, 'header')
            self._log(f'  АТАКА НА {len(self.targets)} ЦЕЛЬ(ЕЙ) '
                      f'[{self.params.mode.upper()}]', 'header')
            self._log('═' * 50, 'header')
            self._begin_target()

        self._wait -= dt
        # не больше 12 микрошагов за кадр: на медленном ПК лог не «зальётся»
        for _ in range(12):
            if self._wait > 0 or self.finished:
                break
            self._advance()

    def _advance(self) -> None:
        """Один микрошаг текущей фазы (может сгенерировать несколько строк)."""
        p = self.params
        total = len(self.targets)
        base = (self.idx / total) * 100
        per_target = 100 / total

        if self.phase == 'recon':
            if self._substep == 0:
                self._log('', 'info')
                self._log('  [1/5] Разведка', 'warning')
                self._log(f'  DNS: {self.current_name} → {self._ip}', 'info')
                self._substep = 1
                self._wait = 0.3 * p.delay_mult
            elif self._substep == 1:
                if self.show_calculations:
                    for _ in range(self.rng.randint(2, 4)):
                        self._log(self._calc(), 'calc')
                self._substep = 2
                self._wait = 0.02 * p.delay_mult
            elif self._substep == 2:
                hops = self.rng.randint(8, 20)
                self._log(f'  Traceroute: {hops} hops', 'info')
                self._set_progress(base + per_target * 0.10)
                self.phase = 'scan'
                self._substep = 0
                self._wait = 0.15 * p.delay_mult
            return

        if self.phase == 'scan':
            if self._substep == 0:
                self._log('', 'info')
                self._log('  [2/5] Сканирование', 'warning')
                self._substep = 1
                self._wait = 0.0
                return
            count = p.scan_count
            if self._substep <= count:
                self._log(f'    {self._scan_line()}', 'fast')
                if self.show_calculations and self.rng.random() < 0.2:
                    self._log(self._calc(), 'calc')
                self._substep += 1
                self._wait = self.rng.uniform(0.01, 0.06) * p.delay_mult
                return
            found = self.rng.randint(3, 10)
            self._log(f'  ✓ Найдено {found} портов', 'success')
            self._set_progress(base + per_target * 0.25)
            self.phase = 'minigame'
            self._substep = 0
            self._wait = 0.1 * p.delay_mult
            return

        if self.phase == 'minigame':
            chance = max(0, min(100, self.minigame_chance * p.minigame_mult))
            if self._substep == 0:
                self._substep = 1
                if self.rng.randint(1, 100) <= chance:
                    self._log('', 'info')
                    self._log('  ⚠ ЗАЩИТА ОБНАРУЖЕНА — требуется обход!', 'minigame')
                    self.minigame = True     # сигнал приложению: запускай игру
                    return                   # ждём resolve_minigame()
                # защиты нет — идём дальше без игры
                self.phase = 'exploit'
                self._substep = 0
                self._wait = 0.1 * p.delay_mult
                return
            # здесь ждём, пока приложение не подставит исход в minigame_won
            return

        if self.phase == 'exploit':
            if self._substep == 0:
                self._log('', 'info')
                self._log('  [3/5] Эксплуатация', 'warning')
                self._substep = 1
                self._wait = 0.0
                return
            if self._substep <= p.exploit_count:
                self._log(f'    {self.rng.choice(gamedata.STUPID_MESSAGES)}', 'stupid')
                if self.show_calculations:
                    for _ in range(self.rng.randint(1, 3)):
                        self._log(self._calc(), 'calc')
                if self.rng.random() < 0.2:
                    self._log(f'    {self.rng.choice(gamedata.FAKE_ERRORS)}', 'error')
                    self._log('    ✓ Обход!', 'success')
                if p.log_detail == 'high' and self.rng.random() < 0.4:
                    for _ in range(self.rng.randint(5, 10)):
                        self._log(f'      0x{self._hex()}', 'fast')
                self._substep += 1
                self._wait = self.rng.uniform(0.2, 0.5) * p.delay_mult
                return
            self._set_progress(base + per_target * 0.55)
            self.phase = 'access'
            self._substep = 0
            self._wait = 0.0
            return

        if self.phase == 'access':
            if self._substep == 0:
                self._log('', 'info')
                self._log('  [4/5] Получение доступа', 'warning')
                self._substep = 1
                self._wait = 0.0
                return
            messages = [f'Shell → {self._ip}:4444', 'Привилегии: root',
                        'Файловая система: ДА', 'База данных: ДА']
            if self._substep <= len(messages):
                self._log(f'    ✓ {messages[self._substep - 1]}', 'success')
                self._substep += 1
                self._wait = 0.2 * p.delay_mult
                return
            self._set_progress(base + per_target * 0.75)
            self.phase = 'extract'
            self._substep = 0
            self._wait = 0.0
            return

        if self.phase == 'extract':
            if self._substep == 0:
                self._log('', 'info')
                self._log('  [5/5] Извлечение данных', 'warning')
                self._substep = 1
                self._wait = 0.0
                return
            if self._substep <= p.data_count:
                self._log(f'    ↓ {self._data_line()}', 'data')
                if self.show_calculations and self.rng.random() < 0.3:
                    self._log(self._calc(), 'calc')
                self._substep += 1
                self._wait = self.rng.uniform(0.01, 0.1) * p.delay_mult
                return
            self._log('', 'info')
            self._log(f'  ✓ {self.current_name} ВЗЛОМАН!', 'success')
            gb = round(self.rng.uniform(0.5, 50), 1)
            self._log(f'  ✓ Данные: {gb:.1f} GB', 'success')
            self.completed += 1
            self.stolen_gb += gb
            self._finish_target(skipped=False)
            return

    minigame_won: bool | None = None

    def resolve_minigame(self, won: bool) -> None:
        """Приложение сообщает исход мини-игры."""
        self.minigame = None
        if won:
            self._log('  ✓ Защита обойдена!', 'success')
            self.phase = 'exploit'
            self._substep = 0
            self._wait = 0.2 * self.params.delay_mult
        else:
            self._log('  ✗ Провал! Цель ускользнула...', 'error')
            self.failed += 1
            self._finish_target(skipped=True)

    def _finish_target(self, skipped: bool) -> None:
        self.phase = 'done'          # иначе update застрянет в ожидании мини-игры
        total = len(self.targets)
        base = (self.idx / total) * 100
        if skipped:
            self._log(f'  ↩ {self.current_name}: защита не пройдена, цель пропущена',
                      'error')
        self._set_progress(min(base + 100 / total, 99))
        self.idx += 1
        self._substep = 0
        self._wait = 0.25 * self.params.delay_mult
        if self.idx >= total:
            self._finalize()
        else:
            self._begin_target()          # выставит phase = 'recon'

    def _finalize(self) -> None:
        total = len(self.targets)
        self.finished = True
        self._set_progress(100)
        self._log('', 'info')
        self._log('═' * 50, 'header')
        self._log('  ЗАВЕРШЕНО!', 'header')
        self._log(f'  Успешно: {self.completed}/{total}', 'success')
        if self.failed:
            self._log(f'  Провалено: {self.failed}/{total}', 'error')
        self._log('═' * 50, 'header')
        if self.completed:
            self.money = self.rng.randint(50, 200) * self.completed
            self._log('', 'info')
            self._log(f'  ЗАРАБОТАНО: ${self.money}', 'success')
            self._log(f'  ОПЫТ: +{self.completed} SP', 'data')
            self._log('', 'info')
            self._log('  Украдено:', 'success')
            self._log(f'    • Данных: {self.stolen_gb:.1f} GB', 'data')
            self._log(f'    • Паролей: {self.rng.randint(1000, 999999)}', 'data')
            self._log(f'    • Котиков: {self.rng.randint(1, 42)} 🐱', 'data')
        self.status = f'Взломано {self.completed}, провалено {self.failed}'
