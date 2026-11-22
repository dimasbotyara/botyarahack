"""История атак: запись, сохранение и сводка.

Формат файла совпадает с tkinter-версией (`~/.hacker_history.json`),
поэтому история общая для обеих версий. Храним последние 100 атак.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

HISTORY_PATH = Path.home() / '.hacker_history.json'
KEEP = 100


def load(path: Path | None = None) -> list[dict]:
    path = path or HISTORY_PATH
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []
    if not isinstance(data, list):
        return []
    clean = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        clean.append({
            'date': str(entry.get('date', ''))[:19],
            'targets': _int(entry.get('targets')),
            'completed': _int(entry.get('completed')),
            'failed': _int(entry.get('failed')),
            'mode': str(entry.get('mode', 'normal')),
        })
    return clean[-KEEP:]


def save(entries: list[dict], path: Path | None = None) -> bool:
    path = path or HISTORY_PATH
    try:
        path.write_text(json.dumps(entries[-KEEP:], ensure_ascii=False),
                        encoding='utf-8')
        return True
    except OSError:
        return False


def add(entries: list[dict], targets: int, completed: int, failed: int,
        mode: str, path: Path | None = None) -> list[dict]:
    """Дописать атаку в историю и сохранить."""
    entries.append({
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'targets': targets, 'completed': completed, 'failed': failed,
        'mode': mode,
    })
    del entries[:-KEEP]
    save(entries, path)
    return entries


def summary(entries: list[dict]) -> dict:
    return {
        'attacks': len(entries),
        'targets': sum(e['targets'] for e in entries),
        'completed': sum(e['completed'] for e in entries),
        'failed': sum(e['failed'] for e in entries),
    }


def _int(value) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0
