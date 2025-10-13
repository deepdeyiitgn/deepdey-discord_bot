"""Simple test runner for activity DB helpers.
Run with: python tests/test_activity.py
This script initializes the DB in the repository `data/studybot.db` and performs a few writes/reads.
"""
import os
import sys
import asyncio
import time

# allow running tests from repo root
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.db import DB, DB_PATH

async def run():
    print('Initializing DB...')
    await DB.init_db()
    now = int(time.time())
    # compute week start
    from cogs.activity import week_start_for_ts
    ws = week_start_for_ts(now)
    gid = 999999999
    # clean previous test rows for cleanliness
    await DB.execute('DELETE FROM activity_messages WHERE guild_id = ?', (gid,))
    await DB.execute('DELETE FROM activity_voice WHERE guild_id = ?', (gid,))
    print('Inserting test message counts...')
    await DB.add_weekly_message(gid, 111, ws, 5)
    await DB.add_weekly_message(gid, 222, ws, 3)
    await DB.add_weekly_message(gid, 333, ws, 8)
    print('Inserting test voice seconds...')
    await DB.add_weekly_voice_seconds(gid, 111, ws, 120)  # 2 minutes
    await DB.add_weekly_voice_seconds(gid, 333, ws, 3600) # 1 hour

    rows = await DB.get_weekly_activity(gid, ws, limit=10)
    print('Rows:', rows)
    assert any(r[0] == 333 for r in rows), 'User 333 should be present'
    # user 333 should top due to 8 msgs + 3600s
    top = rows[0]
    print('Top:', top)
    print('All good. Test complete.')

if __name__ == '__main__':
    asyncio.run(run())
