"""Utility helpers for studybot.

Functions:
 - async_load_json / async_save_json: lightweight async-friendly JSON persistence
 - parse_time: parse simple time strings like '10m', '2h', '1d', '30s'
"""
import json
import asyncio
from pathlib import Path
from typing import Any, Dict


async def async_load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(None, path.read_text)
    try:
        return json.loads(data)
    except Exception:
        return default


async def async_save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    loop = asyncio.get_running_loop()
    text = json.dumps(data, ensure_ascii=False, indent=2)
    await loop.run_in_executor(None, path.write_text, text)


def parse_time(timestr: str) -> int:
    """Parse a time string like '10m', '2h', '1d', '30s' into seconds.

    Returns seconds (int). Raises ValueError on invalid format.
    """
    timestr = timestr.strip().lower()
    if timestr.isdigit():
        return int(timestr)
    unit = timestr[-1]
    num = timestr[:-1]
    if not num.isdigit():
        raise ValueError('Invalid time number')
    num = int(num)
    if unit == 's':
        return num
    if unit == 'm':
        return num * 60
    if unit == 'h':
        return num * 3600
    if unit == 'd':
        return num * 86400
    raise ValueError('Invalid time unit')
import json
from pathlib import Path

def load_json(path):
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding='utf-8'))

def save_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2), encoding='utf-8')
