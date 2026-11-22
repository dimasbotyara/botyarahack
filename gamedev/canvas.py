"""Холст в логических координатах поверх окна в реальном размере.

Зачем: раньше игра рисовалась в растр 1152×726 и растягивалась на окно.
После такого масштабирования шрифты мылятся, а тонкие линии и пиксели
видно «лесенкой» — потому что увеличен низкокачественный растр.

Теперь Canvas рисует СРАЗУ в реальные пиксели окна: он переводит
каждую координату из логической системы (1152×726) в координаты
поверхности-цели, а FontBook рендерит текст в размере окна
(см. RenderedText в assets/fonts/fontloader.py). Картинка совпадает с
той, что была бы при отрисовке «в один пиксель», — ресемплинга нет.

Рисующий код не меняется: он по-прежнему работает в логических
координатах и вызывает привычные surf.blit / pygame.draw.*. Для этого:

* Canvas умеет blit / fill / set_clip / get_clip / get_at;
* функции pygame.draw (rect, line, circle, polygon) при импорте модуля
  оборачиваются хуками, которые масштабируют координаты для Canvas и
  пропускают вызовы для обычных поверхностей без изменений.
"""

from __future__ import annotations

import pygame


class Canvas:
    """Логические координаты → реальные пиксели поверхности-цели."""

    def __init__(self, target: pygame.Surface, logical_w: int, logical_h: int):
        self.real = target
        self.logical_w = int(logical_w)
        self.logical_h = int(logical_h)
        self.sx = target.get_width() / self.logical_w
        self.sy = target.get_height() / self.logical_h

    # ── перевод координат ─────────────────────────────────────────────
    def _pt(self, pos) -> tuple[int, int]:
        return (round(pos[0] * self.sx), round(pos[1] * self.sy))

    def _rect(self, rect) -> pygame.Rect:
        """Масштабирует прямоугольник по краям — стыки без щелей."""
        r = pygame.Rect(rect)
        x0, y0 = round(r.x * self.sx), round(r.y * self.sy)
        x1, y1 = round(r.right * self.sx), round(r.bottom * self.sy)
        return pygame.Rect(x0, y0, x1 - x0, y1 - y0)

    # ── размеры (логические — вёрстка ничего не знает о масштабе) ─────
    def get_width(self) -> int:
        return self.logical_w

    def get_height(self) -> int:
        return self.logical_h

    def get_size(self) -> tuple[int, int]:
        return (self.logical_w, self.logical_h)

    # ── отрисовка ─────────────────────────────────────────────────────
    def blit(self, img, pos, area=None):
        """Кладёт картинку в логических координатах.

        RenderedText (результат book.render) уже отрисован в размере
        окна и кладётся как есть; обычные поверхности (кольца, точки,
        подложки) масштабируются здесь же.
        """
        if getattr(img, 'is_rendered_text', False):
            # RenderedText — HD-растр, класть без масштаба, координаты ×scale
            self.real.blit(img, self._pt(pos), area and self._rect(area))
            return
        if not isinstance(img, pygame.Surface):
            # совместимость со старой обёрткой (если вдруг)
            self.real.blit(getattr(img, 'real', img), self._pt(pos))
            return
        w = max(1, round(img.get_width() * self.sx))
        h = max(1, round(img.get_height() * self.sy))
        if area is not None:
            area = self._rect(area)
        if (w, h) != img.get_size():
            img = pygame.transform.smoothscale(img, (w, h))
        self.real.blit(img, self._pt(pos), area)

    def fill(self, color, rect=None, special_flags=0):
        if rect is None:
            self.real.fill(color, special_flags=special_flags)
        else:
            self.real.fill(color, self._rect(rect), special_flags)

    def get_at(self, pos) -> pygame.Color:
        return self.real.get_at(self._pt(pos))

    def copy(self) -> pygame.Surface:
        return self.real.copy()

    # ── обрезка (для списков с прокруткой) ────────────────────────────
    def set_clip(self, rect) -> None:
        self.real.set_clip(None if rect is None else self._rect(rect))

    def get_clip(self) -> pygame.Rect:
        r = self.real.get_clip()
        return pygame.Rect(round(r.x / self.sx), round(r.y / self.sy),
                           round(r.w / self.sx), round(r.h / self.sy))

    def subsurface(self, rect) -> pygame.Surface:
        return self.real.subsurface(self._rect(rect))


# ── хуки pygame.draw: координаты для Canvas масштабируются ────────────
_hooks_installed = False


def install_hooks() -> None:
    """Оборачивает pygame.draw.* один раз при первом импорте/создании."""
    global _hooks_installed
    if _hooks_installed:
        return
    _hooks_installed = True

    _rect = pygame.draw.rect
    _line = pygame.draw.line
    _circle = pygame.draw.circle
    _polygon = pygame.draw.polygon

    def draw_rect(target, color, rect, width=0, **kw):
        if isinstance(target, Canvas):
            w = max(1, round(width * target.sx)) if width else 0
            return _rect(target.real, color, target._rect(rect), w, **kw)
        return _rect(target, color, rect, width, **kw)

    def draw_line(target, color, start_pos, end_pos, width=1, **kw):
        if isinstance(target, Canvas):
            w = max(1, round(width * min(target.sx, target.sy))) if width > 1 else width
            return _line(target.real, color, target._pt(start_pos),
                         target._pt(end_pos), w, **kw)
        return _line(target, color, start_pos, end_pos, width, **kw)

    def draw_circle(target, color, center, radius, width=0, **kw):
        if isinstance(target, Canvas):
            r = max(1, round(radius * min(target.sx, target.sy))) if radius else 0
            w = max(1, round(width * target.sx)) if width else 0
            return _circle(target.real, color, target._pt(center), r, w, **kw)
        return _circle(target, color, center, radius, width, **kw)

    def draw_polygon(target, color, points, width=0, **kw):
        if isinstance(target, Canvas):
            w = max(1, round(width * target.sx)) if width else 0
            return _polygon(target.real, color, [target._pt(p) for p in points],
                            w, **kw)
        return _polygon(target, color, points, width, **kw)

    pygame.draw.rect = draw_rect
    pygame.draw.line = draw_line
    pygame.draw.circle = draw_circle
    pygame.draw.polygon = draw_polygon


install_hooks()
