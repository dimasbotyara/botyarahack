"""Слоты сохранений: 5 слотов на режим (пока один режим — песочница)."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime

from .profile import Player

SAVES_DIR = Path.home() / '.botyarahack' / 'saves'
# fallback to old single profile path for migration

MODES = ['sandbox']  # пока один, легко добавить второй
SLOTS = 5

@dataclass
class SlotInfo:
    mode: str
    slot: int  # 1..5
    exists: bool
    name: str = ''
    money: int = 0
    level: int = 0
    date: str = ''

def _slot_path(mode: str, slot: int) -> Path:
    return SAVES_DIR / mode / f'slot_{slot}.json'

def _ensure_dir():
    SAVES_DIR.mkdir(parents=True, exist_ok=True)
    for m in MODES:
        (SAVES_DIR / m).mkdir(parents=True, exist_ok=True)

def list_slots(mode: str = 'sandbox') -> list[SlotInfo]:
    _ensure_dir()
    out = []
    for i in range(1, SLOTS+1):
        p = _slot_path(mode, i)
        if p.exists():
            try:
                raw = json.loads(p.read_text(encoding='utf-8'))
                pl = raw.get('player', {})
                out.append(SlotInfo(mode=mode, slot=i, exists=True,
                                    name=pl.get('name','') or '—',
                                    money=pl.get('money',0),
                                    level=sum(pl.get('skills', {}).values())-4 if pl.get('skills') else 0,
                                    date=raw.get('date','')))
            except Exception:
                out.append(SlotInfo(mode=mode, slot=i, exists=False))
        else:
            out.append(SlotInfo(mode=mode, slot=i, exists=False))
    return out

def load_slot(mode: str, slot: int) -> dict | None:
    p = _slot_path(mode, slot)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return None

def save_slot(mode: str, slot: int, player: Player, extra: dict | None = None) -> bool:
    _ensure_dir()
    p = _slot_path(mode, slot)
    data = {
        'mode': mode,
        'slot': slot,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'player': player.to_dict(),
    }
    if extra:
        data.update(extra)
    try:
        p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
        return True
    except OSError:
        return False

def delete_slot(mode: str, slot: int) -> bool:
    p = _slot_path(mode, slot)
    try:
        if p.exists():
            p.unlink()
        return True
    except OSError:
        return False
