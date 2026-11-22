"""Анимированные фоны главного меню — 10 штук, все уважают тему.

Каждый фон рисует на логической поверхности W×H тему-цветами,
поэтому в Matrix-теме он зелёный, в Cyberpunk — розово-голубой и т.д.
Переключение — авто каждые 10 c + по пробелу/стрелкам.

Фоны:
  0 Matrix Rain      (классика, вертикальные глифы)
  1 Circuit Grid     (сетка + бегущий импульс)
  2 Hex Field        (шестиугольники, пульс)
  3 Particle Network (точки + связи)
  4 Wave Lines       (синусоиды стопкой)
  5 Starfield        (звёзды дрейфуют, мерцают)
  6 Binary Rain      (0/1 дождь, шире матрикса)
  7 Radar Sweep      (концентрические круги + зачистка)
  8 Circuit Traces   (L-трассы, вспышки)
  9 Diagonal Flow    (диагональные полосы + глитч)

Все эффекты — только pygame.Primitive, без тяжёлых шрифтов.
"""

from __future__ import annotations

import math
import random

import pygame


NAMES = [
    "MATRIX",
    "CIRCUIT GRID",
    "HEX FIELD",
    "PARTICLE NET",
    "WAVE LINES",
    "STARFIELD",
    "BINARY RAIN",
    "RADAR SWEEP",
    "CIRCUIT TRACES",
    "DIAGONAL FLOW",
]


class MenuBackground:
    def __init__(self, W: int, H: int, seed: int = 1337):
        self.W = W
        self.H = H
        self.rng = random.Random(seed)
        self.t = 0.0
        self.idx = 0
        self.switch_timer = 0.0
        self.switch_interval = 11.0  # секунд на фон
        self.fade = 0.0  # 0..1 переход между фонами (для мягкости)
        self._prev_idx = 0

        # --- общее состояние для всех фонов (инициализируем лениво) ---
        # Matrix / Binary
        self.cols = 32
        self.col_w = max(10, W // self.cols)
        self.n_cols = max(1, W // self.col_w)
        self.drops = [self.rng.randint(-200, H) for _ in range(self.n_cols)]
        self.speeds = [self.rng.uniform(22, 90) for _ in range(self.n_cols)]
        self.chars = [self.rng.choice("01") if i % 2 == 0 else self.rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for i in range(self.n_cols)]

        # Circuit grid
        self.grid_offset = 0.0
        self.pulses = [{"x": self.rng.randint(0, W), "y": self.rng.randint(0, H), "p": self.rng.random()} for _ in range(8)]

        # Hex
        self.hex_phase = 0.0

        # Particles
        self.particles = []
        for _ in range(28):
            self.particles.append({
                "x": self.rng.uniform(0, W),
                "y": self.rng.uniform(0, H),
                "vx": self.rng.uniform(-30, 30),
                "vy": self.rng.uniform(-25, 25),
                "r": self.rng.uniform(2, 4.5),
                "tw": self.rng.uniform(0, 6.28),
            })

        # Waves
        self.wave_layers = 5

        # Stars
        self.stars = []
        for _ in range(120):
            self.stars.append({
                "x": self.rng.uniform(0, W),
                "y": self.rng.uniform(0, H),
                "s": self.rng.uniform(0.7, 2.4),
                "v": self.rng.uniform(8, 28),
                "a": self.rng.uniform(0, 6.28),
            })

        # Radar
        self.radar_angle = 0.0
        self.radar_rings = 4

        # Traces
        self.traces = []
        for _ in range(14):
            self.traces.append(self._new_trace())

        # Diagonal
        self.diag_offset = 0.0

    def _new_trace(self):
        # L-образная трасса: старт -> поворот -> конец
        x = self.rng.randint(40, self.W - 40)
        y = self.rng.randint(40, self.H - 120)
        length = self.rng.randint(60, 180)
        horiz = self.rng.choice([True, False])
        return {
            "x": x, "y": y,
            "len": length,
            "horiz": horiz,
            "t": self.rng.uniform(0, 2.5),
            "speed": self.rng.uniform(0.8, 1.8),
            "active": self.rng.random() < 0.6,
        }

    # ── управление ────────────────────────────────────────────────────
    def update(self, dt: float):
        self.t += dt
        self.switch_timer += dt
        if self.switch_timer > self.switch_interval:
            self.prev_switch()

            # actually next
            self.switch_timer = 0
            self._prev_idx = self.idx
            self.idx = (self.idx + 1) % len(NAMES)
            self.fade = 1.0  # на один кадр можно было бы блендить

        # анимация общих параметров
        self.grid_offset = (self.grid_offset + dt * 40) % 48
        self.hex_phase += dt * 0.9
        self.radar_angle = (self.radar_angle + dt * 0.9) % (2 * math.pi)
        self.diag_offset = (self.diag_offset + dt * 55) % 80

        # particles
        for p in self.particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["tw"] += dt * 2.0
            if p["x"] < -10:
                p["x"] = self.W + 10
            if p["x"] > self.W + 10:
                p["x"] = -10
            if p["y"] < -10:
                p["y"] = self.H + 10
            if p["y"] > self.H + 10:
                p["y"] = -10

        # drops (matrix/binary)
        for i in range(self.n_cols):
            self.drops[i] += self.speeds[i] * dt
            if self.drops[i] > self.H + 40:
                self.drops[i] = self.rng.randint(-140, -10)
                self.speeds[i] = self.rng.uniform(22, 90)

        # traces
        for tr in self.traces:
            tr["t"] += dt * tr["speed"]
            if tr["t"] > 3.5:
                tr.update(self._new_trace())
                tr["t"] = 0

        # stars drift
        for s in self.stars:
            s["y"] += s["v"] * dt
            s["a"] += dt * 3.0
            if s["y"] > self.H + 5:
                s["y"] = -5
                s["x"] = self.rng.uniform(0, self.W)

        # уменьшаем fade
        if self.fade > 0:
            self.fade = max(0.0, self.fade - dt * 3.0)

    def next(self):
        self._prev_idx = self.idx
        self.idx = (self.idx + 1) % len(NAMES)
        self.switch_timer = 0
        self.fade = 0.7

    def prev(self):
        self._prev_idx = self.idx
        self.idx = (self.idx - 1) % len(NAMES)
        self.switch_timer = 0
        self.fade = 0.7

    def prev_switch(self):
        # placeholder for compatibility
        pass

    @property
    def name(self) -> str:
        return NAMES[self.idx]

    # ── отрисовка ─────────────────────────────────────────────────────
    def draw(self, surf: pygame.Surface, theme) -> None:
        # фон — matrix_bg или bg_dark (у cyberpunk они отличаются)
        bg = theme["matrix_bg"] if "matrix_bg" in theme.colors else theme["bg_dark"]
        surf.fill(bg)

        # лёгкая виньетка / затемнение по краям
        # выбираем цвета под тему
        accent = theme["accent"]
        fg = theme["fg_main"]
        dim = theme["fg_dim"]
        border = theme["border"]
        matrix_fg = theme.get("matrix_fg", dim)

        # делегируем
        fn = [
            self._draw_matrix,
            self._draw_circuit_grid,
            self._draw_hex,
            self._draw_particles,
            self._draw_waves,
            self._draw_starfield,
            self._draw_binary,
            self._draw_radar,
            self._draw_traces,
            self._draw_diagonal,
        ][self.idx]

        # клип не нужен — рисуем на всю поверхность
        fn(surf, theme, accent, fg, dim, border, matrix_fg)

        # тонкий бордер-сетка поверх (общий для всех)
        # рисуем очень прозрачную рамку 8px — чисто декоративно
        # уже тема даёт accent, поэтому делаем «техно-рамку»
        col = _fade(border, 0.9)
        # вертикальные/горизонтальные штрихи по краям
        _draw_corner_brackets(surf, self.W, self.H, accent)

    # ── 0 MATRIX (классика, но шире) ──────────────────────────────────
    def _draw_matrix(self, surf, theme, accent, fg, dim, border, matrix_fg):
        for i in range(self.n_cols):
            x = i * self.col_w + self.col_w // 2
            y = int(self.drops[i])
            # голова — accent
            _dot(surf, x, y, 3, accent)
            # хвост 6 точек с затуханием
            for k in range(1, 7):
                ty = y - k * 14
                if ty < -20 or ty > self.H + 20:
                    continue
                alpha = 1.0 - k / 7.0
                col = _blend(matrix_fg, accent, alpha * 0.6)
                col = _fade(col, 0.55 + alpha * 0.45)
                _dot(surf, x, ty, max(1, 3 - k // 3), col)
                # глиф как крошечный квадратик — дешево, но узнаваемо
                if self.rng.random() < 0.02:  # не каждый кадр
                    pass

    # ── 1 CIRCUIT GRID ────────────────────────────────────────────────
    def _draw_circuit_grid(self, surf, theme, accent, fg, dim, border, matrix_fg):
        # сетка 48px
        step = 48
        off = int(self.grid_offset) % step
        grid_col = _fade(border, 0.7)
        for x in range(-step + off, self.W + step, step):
            pygame.draw.line(surf, grid_col, (x, 0), (x, self.H), 1)
        for y in range(-step + off, self.H + step, step):
            pygame.draw.line(surf, grid_col, (0, y), (self.W, y), 1)

        # точки узлов
        for x in range(0, self.W, step):
            for y in range(0, self.H, step):
                cx = x + off % step - step // 2
                cy = y + off % step - step // 2
                if 0 <= cx < self.W and 0 <= cy < self.H:
                    pygame.draw.circle(surf, _fade(dim, 0.5), (cx, cy), 2)

        # бегущие импульсы — маленькие яркие точки по линиям
        for p in self.pulses:
            p["p"] = (p["p"] + 0.018) % 1.0
            # по X
            px = int((p["x"] + self.t * 70) % self.W)
            py = p["y"]
            _dot(surf, px, py, 4, accent)
            _dot(surf, px, py, 7, _fade(accent, 0.22))
            # по Y
            px2 = p["y"]  # reuse
            py2 = int((p["y"] + self.t * 55) % self.H)
            _dot(surf, px2 % self.W, py2, 3, fg)

    # ── 2 HEX FIELD ──────────────────────────────────────────────────
    def _draw_hex(self, surf, theme, accent, fg, dim, border, matrix_fg):
        # пасека из шестиугольников
        size = 34
        h = size * math.sqrt(3)
        cols = int(self.W / (size * 1.5)) + 2
        rows = int(self.H / h) + 2
        pulse = 0.5 + 0.5 * math.sin(self.hex_phase * 1.6)
        for r in range(rows):
            for c in range(cols):
                cx = c * size * 1.5 + (size if r % 2 else 0) + 14
                cy = r * h + 24
                if cx < -size or cx > self.W + size or cy < -size or cy > self.H + size:
                    continue
                # дальность от центра — влияет на яркость
                dist = math.hypot(cx - self.W * 0.5, cy - self.H * 0.5)
                nd = 1.0 - min(1.0, dist / (self.W * 0.75))
                # пульс
                bright = 0.25 + nd * 0.55 + pulse * nd * 0.25
                col = _fade(dim, 0.45 + bright * 0.6)
                if (c + r) % 7 == int(self.t * 0.7) % 7:
                    col = accent
                    # подсветка
                    _hexagon(surf, cx, cy, size - 2, col, 2)
                    _hexagon(surf, cx, cy, size - 8, _fade(accent, 0.18), 0)
                else:
                    _hexagon(surf, cx, cy, size - 3, col, 1)

    # ── 3 PARTICLE NETWORK ────────────────────────────────────────────
    def _draw_particles(self, surf, theme, accent, fg, dim, border, matrix_fg):
        # связи
        for i, a in enumerate(self.particles):
            for b in self.particles[i + 1:]:
                d = math.hypot(a["x"] - b["x"], a["y"] - b["y"])
                if d < 150:
                    alpha = 1.0 - d / 150.0
                    # чем ближе — ярче
                    col = _fade(dim, 0.25 + alpha * 0.75)
                    if alpha > 0.65:
                        col = _blend(col, accent, 0.4)
                    pygame.draw.line(surf, col, (a["x"], a["y"]), (b["x"], b["y"]), 1)
        # точки
        for p in self.particles:
            tw = 0.7 + 0.3 * math.sin(p["tw"])
            col = _blend(fg, accent, 0.35 + tw * 0.15)
            _dot(surf, int(p["x"]), int(p["y"]), int(p["r"] * tw + 1), col)
            _dot(surf, int(p["x"]), int(p["y"]), int(p["r"] * 3), _fade(col, 0.12))

    # ── 4 WAVE LINES ──────────────────────────────────────────────────
    def _draw_waves(self, surf, theme, accent, fg, dim, border, matrix_fg):
        base_y = self.H * 0.5
        for layer in range(self.wave_layers):
            off = layer * 28 - self.wave_layers * 14
            freq = 0.014 + layer * 0.003
            amp = 44 - layer * 5 + 10 * math.sin(self.t * 0.6 + layer)
            col = [dim, dim, fg, accent, fg][layer % 5]
            col = _fade(col, 0.85 - layer * 0.1)
            if layer == self.wave_layers // 2:
                col = accent
            pts = []
            step = 12
            for x in range(-20, self.W + 24, step):
                y = base_y + off + math.sin(x * freq + self.t * (0.9 + layer * 0.2)) * amp
                # второй гармоник
                y += math.sin(x * freq * 2.1 - self.t * 0.7) * (amp * 0.22)
                pts.append((x, y))
            if len(pts) > 1:
                for i in range(len(pts) - 1):
                    pygame.draw.line(surf, col, pts[i], pts[i+1], 1)
                # мягкое свечение — копия с размытием (имитация толщиной 2)
                if layer == 2:
                    for i in range(len(pts) - 1):
                        pygame.draw.line(surf, _fade(col, 0.18), (pts[i][0], pts[i][1] + 1), (pts[i+1][0], pts[i+1][1] + 1), 1)
        # горизонтальная центральная линия-акцент
        pygame.draw.line(surf, _fade(accent, 0.55), (0, int(base_y)), (self.W, int(base_y)), 1)

    # ── 5 STARFIELD ───────────────────────────────────────────────────
    def _draw_starfield(self, surf, theme, accent, fg, dim, border, matrix_fg):
        # градиент сверху вниз (имитация)
        for y in range(0, self.H, 6):
            alpha = y / self.H
            col = _blend(theme["bg_dark"], theme["matrix_bg"], 0.5 + alpha * 0.25)
            pygame.draw.line(surf, col, (0, y), (self.W, y))
        for s in self.stars:
            tw = 0.6 + 0.4 * math.sin(s["a"] + self.t * 2.0)
            col = _blend(fg, accent, tw * 0.35)
            # более крупные звёзды — акцент
            r = s["s"] * (0.8 + tw * 0.6)
            pygame.draw.circle(surf, col, (int(s["x"]), int(s["y"])), max(1, int(r)))
            if r > 1.6:
                # крошечное свечение
                pygame.draw.circle(surf, _fade(col, 0.14), (int(s["x"]), int(s["y"])), int(r * 2.2))
        # пару «пролетающих» метеоров
        for i in range(2):
            mx = (self.t * (80 + i * 30) + i * 300) % (self.W + 200) - 100
            my = 90 + i * 120 + math.sin(self.t * 0.8 + i) * 40
            col = accent if i == 0 else fg
            pygame.draw.line(surf, col, (mx, my), (mx - 34, my + 10), 2)
            pygame.draw.line(surf, _fade(col, 0.18), (mx, my), (mx - 56, my + 17), 4)

    # ── 6 BINARY RAIN (0/1) ───────────────────────────────────────────
    def _draw_binary(self, surf, theme, accent, fg, dim, border, matrix_fg):
        # похож на матрицу, но «тяжёлые» 0/1 блоками
        for i in range(self.n_cols):
            x = i * self.col_w
            y = int(self.drops[i])
            # столбец — 5 символов друг над другом
            for k in range(5):
                ty = y - k * 18
                if ty < -30 or ty > self.H + 30:
                    continue
                ch = "1" if (i + k + int(self.t * 2)) % 2 == 0 else "0"
                # цвет: голова — accent, дальше — fg/dim
                if k == 0:
                    col = accent
                elif k == 1:
                    col = fg
                else:
                    col = _fade(matrix_fg if matrix_fg != dim else dim, 0.9 - k * 0.13)
                # рисуем как квадратик с буквой — дёшево, но читаемо на всех темах
                # вместо шрифта — крошечный rect + точка
                pygame.draw.rect(surf, _fade(col, 0.22), (x + 2, ty, self.col_w - 6, 12))
                pygame.draw.rect(surf, col, (x + self.col_w // 2 - 4, ty + 2, 8, 8), 1)
                # точка внутри как «1/0» намёк
                if ch == "1":
                    pygame.draw.line(surf, col, (x + self.col_w // 2, ty + 3), (x + self.col_w // 2, ty + 9), 2)
                else:
                    pygame.draw.circle(surf, col, (x + self.col_w // 2, ty + 6), 3, 1)

    # ── 7 RADAR SWEEP ─────────────────────────────────────────────────
    def _draw_radar(self, surf, theme, accent, fg, dim, border, matrix_fg):
        cx, cy = self.W // 2, self.H // 2 + 6
        max_r = int(min(self.W, self.H) * 0.44)
        # концентрические круги
        for n in range(1, self.radar_rings + 1):
            r = int(max_r * n / self.radar_rings)
            col = _fade(dim, 0.55) if n % 2 == 0 else _fade(border, 0.9)
            pygame.draw.circle(surf, col, (cx, cy), r, 1)
            # лёгкий пульс на одном из колец
            if n == 2:
                pulse = 0.5 + 0.5 * math.sin(self.t * 2.2)
                pygame.draw.circle(surf, _fade(accent, 0.18 + pulse * 0.15), (cx, cy), int(r * (0.96 + pulse * 0.04)), 1)
        # оси
        pygame.draw.line(surf, _fade(dim, 0.5), (cx - max_r, cy), (cx + max_r, cy), 1)
        pygame.draw.line(surf, _fade(dim, 0.5), (cx, cy - max_r), (cx, cy + max_r), 1)
        # луч-зачистка
        end_x = cx + int(math.cos(self.radar_angle) * max_r)
        end_y = cy + int(math.sin(self.radar_angle) * max_r)
        pygame.draw.line(surf, accent, (cx, cy), (end_x, end_y), 2)
        # след за лучом — полупрозрачный «шлейф»
        for i in range(1, 18):
            a = self.radar_angle - i * 0.05
            alpha = 1.0 - i / 18.0
            ex = cx + int(math.cos(a) * max_r)
            ey = cy + int(math.sin(a) * max_r)
            pygame.draw.line(surf, _fade(accent, alpha * 0.14), (cx, cy), (ex, ey), 1)
        # центр
        _dot(surf, cx, cy, 4, accent)
        _dot(surf, cx, cy, 9, _fade(accent, 0.18))
        # пару «контактов»-блипов
        for i in range(5):
            ang = (i * 1.1 + self.t * 0.3) % (2 * math.pi)
            dist = (max_r * (0.35 + (i % 3) * 0.18) + math.sin(self.t * 1.2 + i) * 14)
            bx = cx + int(math.cos(ang) * dist)
            by = cy + int(math.sin(ang) * dist)
            bright = 0.6 + 0.4 * math.sin(self.t * 2.0 + i)
            _dot(surf, bx, by, 3, fg if bright < 0.8 else accent)
            _dot(surf, bx, by, 7, _fade(accent if bright > 0.8 else fg, 0.16))

    # ── 8 CIRCUIT TRACES ──────────────────────────────────────────────
    def _draw_traces(self, surf, theme, accent, fg, dim, border, matrix_fg):
        # базовая плата — тёмная с сеткой точек
        for x in range(20, self.W, 40):
            for y in range(20, self.H, 40):
                pygame.draw.circle(surf, _fade(border, 0.8), (x, y), 1)
        for tr in self.traces:
            x, y, length = tr["x"], tr["y"], tr["len"]
            t = tr["t"]
            prog = min(1.0, max(0.0, t / 1.6))
            # L-трасса
            if tr["horiz"]:
                mid_x = x + length
                mid_y = y
                end_y = y + length // 2
                # фон трасы
                pygame.draw.line(surf, _fade(border, 0.65), (x, y), (mid_x, mid_y), 2)
                pygame.draw.line(surf, _fade(border, 0.65), (mid_x, mid_y), (mid_x, end_y), 2)
                # бегущий огонь по трассе
                if prog > 0:
                    if prog < 0.55:
                        fx = x + (mid_x - x) * (prog / 0.55)
                        fy = y
                    else:
                        fx = mid_x
                        fy = mid_y + (end_y - mid_y) * ((prog - 0.55) / 0.45)
                    _dot(surf, int(fx), int(fy), 4, accent)
                    _dot(surf, int(fx), int(fy), 9, _fade(accent, 0.18))
            else:
                mid_y = y + length
                mid_x = x
                end_x = x + length // 2
                pygame.draw.line(surf, _fade(border, 0.65), (x, y), (mid_x, mid_y), 2)
                pygame.draw.line(surf, _fade(border, 0.65), (mid_x, mid_y), (end_x, mid_y), 2)
                if prog > 0:
                    if prog < 0.55:
                        fx = x
                        fy = y + (mid_y - y) * (prog / 0.55)
                    else:
                        fx = mid_x + (end_x - mid_x) * ((prog - 0.55) / 0.45)
                        fy = mid_y
                    _dot(surf, int(fx), int(fy), 4, accent)
                    _dot(surf, int(fx), int(fy), 9, _fade(accent, 0.18))
            # вспышка в начале/конце когда активна
            if tr["active"] and prog > 0.85:
                _dot(surf, x, y, 2, fg)

    # ── 9 DIAGONAL FLOW ──────────────────────────────────────────────
    def _draw_diagonal(self, surf, theme, accent, fg, dim, border, matrix_fg):
        # диагональные полосы
        stripe_w = 28
        gap = 52
        off = int(self.diag_offset) % (stripe_w + gap)
        col1 = _fade(accent, 0.14)
        col2 = _fade(fg, 0.09)
        for s in range(-self.H, self.W + self.H, stripe_w + gap):
            x0 = s + off
            # диагональ 45° — рисуем полигон
            pts = [(x0, 0), (x0 + stripe_w, 0), (x0 + stripe_w - self.H, self.H), (x0 - self.H, self.H)]
            pygame.draw.polygon(surf, col1 if (s // (stripe_w + gap)) % 2 == 0 else col2, pts)
        # глитч-полоски — яркие тонкие линии поперёк
        for i in range(5):
            y = (int(self.t * (30 + i * 12)) + i * 110) % self.H
            pygame.draw.line(surf, _fade(accent, 0.45 + (i % 2) * 0.2), (0, y), (self.W, y), 1)
            if i % 2 == 0:
                # короткий сдвиг
                shift = int(8 * math.sin(self.t * 3 + i))
                pygame.draw.line(surf, accent, (self.W // 3 + shift, y), (self.W // 2 + shift, y), 2)
        # центр — «шум»
        for _ in range(22):
            x = int((self.rng.random() * self.W + self.t * 40) % self.W)
            y = self.rng.randint(0, self.H)
            pygame.draw.circle(surf, _fade(dim, 0.45), (x, y), 1)


# ── helpers ───────────────────────────────────────────────────────────
def _fade(color, alpha: float) -> tuple:
    """alpha 0..1 → затемнение."""
    if isinstance(alpha, float) and alpha <= 1.0:
        return tuple(int(c * alpha) for c in color)
    return tuple(int(c * alpha / 255) for c in color)


def _blend(a, b, t: float):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def _dot(surf, x, y, r, color):
    # Canvas не имеет set_at — используем pygame.draw, который захучен для Canvas
    # r<=1 рисуем точкой 1px, иначе кружком
    pygame.draw.circle(surf, color, (int(x), int(y)), max(1, int(r)))


def _hexagon(surf, cx, cy, size, color, width):
    pts = []
    for k in range(6):
        ang = math.pi / 3 * k - math.pi / 6  # flat-top
        pts.append((cx + size * math.cos(ang), cy + size * math.sin(ang)))
    pygame.draw.polygon(surf, color, pts, width)


def _draw_corner_brackets(surf, W, H, accent):
    """4 уголка по краям экрана — техно-рамка."""
    l = 22
    t = 2
    col = _fade(accent, 0.75)
    # top-left
    pygame.draw.line(surf, col, (10, 10), (10 + l, 10), t)
    pygame.draw.line(surf, col, (10, 10), (10, 10 + l), t)
    # top-right
    pygame.draw.line(surf, col, (W - 10, 10), (W - 10 - l, 10), t)
    pygame.draw.line(surf, col, (W - 10, 10), (W - 10, 10 + l), t)
    # bottom-left
    pygame.draw.line(surf, col, (10, H - 10), (10 + l, H - 10), t)
    pygame.draw.line(surf, col, (10, H - 10), (10, H - 10 - l), t)
    # bottom-right
    pygame.draw.line(surf, col, (W - 10, H - 10), (W - 10 - l, H - 10), t)
    pygame.draw.line(surf, col, (W - 10, H - 10), (W - 10, H - 10 - l), t)
