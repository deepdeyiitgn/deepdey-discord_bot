import os
import sys

# allow running tests from repo root
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pytest
from utils.db import DB


@pytest.mark.asyncio
async def test_db_init_and_log():
    await DB.init_db()
    await DB.add_study_log(user_id=12345, minutes=30, ts=1630000000, topic='testing', guild_id=1)
    rows = await DB.get_user_logs(12345)
    assert any(int(r['minutes']) == 30 for r in rows)