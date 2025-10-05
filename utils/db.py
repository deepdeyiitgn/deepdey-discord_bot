"""Simple async SQLite helper using aiosqlite for small key/value and configs.

This helper exposes init_db(), get_kv(), set_kv(), and close_db(). It's minimal
and safe for the cogs to use for small persistent settings.
"""
from pathlib import Path
from typing import Optional


def _ensure_aiosqlite():
    try:
        import aiosqlite
        return aiosqlite
    except Exception as e:
        raise ImportError('aiosqlite is required for DB operations. Please install with `pip install aiosqlite`.') from e

DB_PATH = Path(__file__).parent.parent / 'data' / 'studybot.db'


class DB:
    _conn: Optional[object] = None

    @classmethod
    async def init_db(cls):
        if cls._conn:
            return
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        aiosqlite = _ensure_aiosqlite()
        cls._conn = await aiosqlite.connect(str(DB_PATH))
        await cls._conn.execute('''
            CREATE TABLE IF NOT EXISTS kv (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        await cls._conn.commit()

    @classmethod
    async def get_kv(cls, key: str) -> Optional[str]:
        if not cls._conn:
            await cls.init_db()
        async with cls._conn.execute('SELECT value FROM kv WHERE key = ?', (key,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else None

    @classmethod
    async def set_kv(cls, key: str, value: str) -> None:
        if not cls._conn:
            await cls.init_db()
        await cls._conn.execute('REPLACE INTO kv(key, value) VALUES(?, ?)', (key, value))
        await cls._conn.commit()

    @classmethod
    async def close_db(cls):
        if cls._conn:
            await cls._conn.close()
            cls._conn = None
