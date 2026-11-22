"""Список целей: выбор кликом, очередь атаки с номерами, поиск.

Логика очереди повторяет legacy: клик по цели добавляет её в очередь
с номером, повторный клик убирает, номера пересчитываются. Добавлено:
поиск по строке и прокрутка — в старом списке из 81 цели приходилось
скроллить вручную.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import gamedata


@dataclass
class TargetList:
    items: list[str] = field(default_factory=lambda: list(gamedata.TARGETS))
    queue: dict[str, int] = field(default_factory=dict)   # цель → номер
    click_count: int = 0
    filter_text: str = ''
    scroll: int = 0
    hover: int = -1

    # ── выбор ───────────────────────────────────────────────────────────
    def visible(self) -> list[tuple[int, str]]:
        """(индекс в items, подпись с номером очереди) — с учётом поиска."""
        needle = self.filter_text.strip().lower()
        out = []
        for i, name in enumerate(self.items):
            if needle and needle not in name.lower():
                continue
            order = self.queue.get(name)
            out.append((i, f'[{order}] {name}' if order else name))
        return out

    def toggle(self, name: str) -> None:
        """Клик по цели: поставить в очередь или убрать из неё."""
        if name in self.queue:
            del self.queue[name]
            self._renumber()
        else:
            self.click_count += 1
            self.queue[name] = self.click_count

    def _renumber(self) -> None:
        ordered = sorted(self.queue.items(), key=lambda kv: kv[1])
        self.queue = {name: i + 1 for i, (name, _) in enumerate(ordered)}
        self.click_count = len(self.queue)

    def clear(self) -> None:
        self.queue.clear()
        self.click_count = 0

    def selected(self) -> list[str]:
        """Цели в порядке кликов."""
        return [name for name, _ in sorted(self.queue.items(), key=lambda kv: kv[1])]

    def add_custom(self, text: str) -> str | None:
        text = text.strip()
        if not text:
            return None
        if '/' not in text:
            text = f'{text} / {text}'
        if text not in self.items:
            self.items.append(text)
        return text

    # ── поиск ───────────────────────────────────────────────────────────
    def type_char(self, ch: str) -> None:
        self.filter_text += ch
        self.scroll = 0

    def backspace(self) -> None:
        self.filter_text = self.filter_text[:-1]
        self.scroll = 0

    # ── прокрутка ───────────────────────────────────────────────────────
    def scroll_by(self, rows: int, page: int) -> None:
        rows_total = len(self.visible())
        self.scroll = max(0, min(max(0, rows_total - page), self.scroll + rows))
