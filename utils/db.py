"""Simple async SQLite helper using aiosqlite for small key/value and configs.

This helper exposes init_db(), get_kv(), set_kv(), and close_db(). It's minimal
and safe for the cogs to use for small persistent settings.
"""
from pathlib import Path
from typing import Optional, Any, List, Tuple
import time


def _ensure_aiosqlite():
    try:
        import aiosqlite
        return aiosqlite
    except Exception as e:
        raise ImportError('aiosqlite is required for DB operations. Please install with `pip install aiosqlite`.') from e

DB_PATH = Path(__file__).parent.parent / 'data' / 'studybot.db'


class DB:
    """Async SQLite helper with small migrations and convenience methods.

    The project previously used a simple key/value table. This class keeps
    `get_kv`/`set_kv` for backward compatibility but also creates structured
    tables for logs, leaderboards, doubts, reminders, progress and users.
    """
    _conn: Optional[Any] = None

    @classmethod
    async def init_db(cls):
        if cls._conn:
            return
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        aiosqlite = _ensure_aiosqlite()
        cls._conn = await aiosqlite.connect(str(DB_PATH))
        cls._conn.row_factory = aiosqlite.Row

        # Create tables
        await cls._conn.execute('''
            CREATE TABLE IF NOT EXISTS kv (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        await cls._conn.execute('''
            CREATE TABLE IF NOT EXISTS study_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                guild_id INTEGER,
                minutes INTEGER NOT NULL,
                topic TEXT,
                ts INTEGER NOT NULL
            )
        ''')

        await cls._conn.execute('''
            CREATE TABLE IF NOT EXISTS streaks (
                user_id INTEGER PRIMARY KEY,
                count INTEGER DEFAULT 0,
                last_date TEXT
            )
        ''')

        await cls._conn.execute('''
            CREATE TABLE IF NOT EXISTS leaderboard (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                minutes INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, user_id)
            )
        ''')

        await cls._conn.execute('''
            CREATE TABLE IF NOT EXISTS doubts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                question TEXT,
                ts INTEGER,
                resolved INTEGER DEFAULT 0
            )
        ''')

        await cls._conn.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                guild_id INTEGER,
                channel_id INTEGER,
                message TEXT,
                remind_at INTEGER,
                sent INTEGER DEFAULT 0
            )
        ''')

        await cls._conn.execute('''
            CREATE TABLE IF NOT EXISTS doubt_threads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doubt_id INTEGER,
                guild_id INTEGER,
                channel_id INTEGER,
                thread_id INTEGER,
                created_ts INTEGER,
                claimed_by INTEGER,
                closed INTEGER DEFAULT 0,
                FOREIGN KEY(doubt_id) REFERENCES doubts(id)
            )
        ''')

        await cls._conn.execute('''
            CREATE TABLE IF NOT EXISTS progress (
                user_id INTEGER,
                guild_id INTEGER,
                subject TEXT,
                percent INTEGER,
                PRIMARY KEY (user_id, guild_id, subject)
            )
        ''')

        # Activity tracking: message and voice activity aggregated by week (unix week start timestamp)
        await cls._conn.execute('''
            CREATE TABLE IF NOT EXISTS activity_messages (
                guild_id INTEGER,
                user_id INTEGER,
                week_start INTEGER,
                messages INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, user_id, week_start)
            )
        ''')

        await cls._conn.execute('''
            CREATE TABLE IF NOT EXISTS activity_voice (
                guild_id INTEGER,
                user_id INTEGER,
                week_start INTEGER,
                seconds INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, user_id, week_start)
            )
        ''')

        # Activity configuration per guild: role_id, tracked_channel_ids (JSON), reset_day (0-6 weekday), reset_hour (0-23), last_processed_week
        await cls._conn.execute('''
            CREATE TABLE IF NOT EXISTS activity_config (
                guild_id INTEGER PRIMARY KEY,
                role_id INTEGER,
                channel_ids TEXT,
                reset_weekday INTEGER DEFAULT 0,
                reset_hour INTEGER DEFAULT 0,
                last_processed_week INTEGER
            )
        ''')

        # Quizzes / Tests
        await cls._conn.execute('''
            CREATE TABLE IF NOT EXISTS quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                title TEXT,
                config TEXT,
                creator_id INTEGER,
                created_at INTEGER
            )
        ''')

        await cls._conn.execute('''
            CREATE TABLE IF NOT EXISTS quiz_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER,
                question_json TEXT
            )
        ''')

        await cls._conn.execute('''
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER,
                user_id INTEGER,
                score REAL,
                details TEXT,
                ts INTEGER
            )
        ''')

        # Question options (for multiple choice)
        await cls._conn.execute('''
            CREATE TABLE IF NOT EXISTS question_options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER,
                option_index INTEGER,
                option_text TEXT,
                is_correct INTEGER DEFAULT 0
            )
        ''')

        # Quiz sessions (per user playthrough)
        await cls._conn.execute('''
            CREATE TABLE IF NOT EXISTS quiz_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER,
                user_id INTEGER,
                started_at INTEGER,
                finished_at INTEGER,
                current_index INTEGER DEFAULT 0,
                score REAL DEFAULT 0,
                state TEXT DEFAULT 'running'
            )
        ''')

        # Responses recorded during a session
        await cls._conn.execute('''
            CREATE TABLE IF NOT EXISTS quiz_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                question_id INTEGER,
                selected_index INTEGER,
                answer_text TEXT,
                correct INTEGER DEFAULT 0,
                time_taken INTEGER,
                ts INTEGER
            )
        ''')

        # Matches and game results
        await cls._conn.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                game_type TEXT,
                metadata TEXT,
                created_at INTEGER
            )
        ''')

        await cls._conn.execute('''
            CREATE TABLE IF NOT EXISTS match_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER,
                user_id INTEGER,
                result TEXT
            )
        ''')

        # Economy
        await cls._conn.execute('''
            CREATE TABLE IF NOT EXISTS wallets (
                guild_id INTEGER,
                user_id INTEGER,
                balance INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, user_id)
            )
        ''')

        await cls._conn.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                guild_id INTEGER,
                user_id INTEGER,
                item_id TEXT,
                qty INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, user_id, item_id)
            )
        ''')

        # Achievements
        await cls._conn.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                guild_id INTEGER,
                user_id INTEGER,
                achv_key TEXT,
                meta TEXT,
                ts INTEGER,
                PRIMARY KEY (guild_id, user_id, achv_key)
            )
        ''')

        # Todos
        await cls._conn.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                title TEXT,
                due_ts INTEGER,
                completed INTEGER DEFAULT 0,
                created_ts INTEGER
            )
        ''')

        # Generic archives/logs
        await cls._conn.execute('''
            CREATE TABLE IF NOT EXISTS archives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                event_type TEXT,
                payload TEXT,
                ts INTEGER
            )
        ''')

        await cls._conn.commit()

    @classmethod
    async def execute(cls, query: str, params: Tuple = ()):  # convenience wrapper
        if not cls._conn:
            await cls.init_db()
        cur = await cls._conn.execute(query, params)
        await cls._conn.commit()
        return cur

    @classmethod
    async def fetchone(cls, query: str, params: Tuple = ()):  # returns row or None
        if not cls._conn:
            await cls.init_db()
        async with cls._conn.execute(query, params) as cur:
            return await cur.fetchone()

    @classmethod
    async def fetchall(cls, query: str, params: Tuple = ()):  # returns list
        if not cls._conn:
            await cls.init_db()
        async with cls._conn.execute(query, params) as cur:
            return await cur.fetchall()

    # Backwards compatible KV
    @classmethod
    async def get_kv(cls, key: str) -> Optional[str]:
        row = await cls.fetchone('SELECT value FROM kv WHERE key = ?', (key,))
        return row['value'] if row else None

    @classmethod
    async def set_kv(cls, key: str, value: str) -> None:
        await cls.execute('REPLACE INTO kv(key, value) VALUES(?, ?)', (key, value))

    # Study logs
    @classmethod
    async def add_study_log(cls, user_id: int, minutes: int, ts: int, topic: str = '', guild_id: Optional[int] = None):
        await cls.execute(
            'INSERT INTO study_logs(user_id, guild_id, minutes, topic, ts) VALUES(?, ?, ?, ?, ?)',
            (user_id, guild_id, minutes, topic, ts)
        )

    @classmethod
    async def get_user_logs(cls, user_id: int, since_ts: Optional[int] = None) -> List[Any]:
        if since_ts:
            rows = await cls.fetchall('SELECT * FROM study_logs WHERE user_id = ? AND ts >= ? ORDER BY ts DESC', (user_id, since_ts))
        else:
            rows = await cls.fetchall('SELECT * FROM study_logs WHERE user_id = ? ORDER BY ts DESC', (user_id,))
        return rows

    # Leaderboard helpers
    @classmethod
    async def increment_leaderboard(cls, guild_id: int, user_id: int, minutes: int):
        if guild_id is None:
            return
        # Try update, else insert
        await cls.execute('INSERT INTO leaderboard(guild_id, user_id, minutes) VALUES(?, ?, ?) ON CONFLICT(guild_id, user_id) DO UPDATE SET minutes = minutes + excluded.minutes', (guild_id, user_id, minutes))

    @classmethod
    async def get_leaderboard(cls, guild_id: int, limit: int = 10) -> List[Tuple[int, int]]:
        rows = await cls.fetchall('SELECT user_id, minutes FROM leaderboard WHERE guild_id = ? ORDER BY minutes DESC LIMIT ?', (guild_id, limit))
        return rows

    # Doubts
    @classmethod
    async def add_doubt(cls, guild_id: int, user_id: int, question: str, ts: int):
        cur = await cls.execute('INSERT INTO doubts(guild_id, user_id, question, ts) VALUES(?, ?, ?, ?)', (guild_id, user_id, question, ts))
        # return last inserted id
        row = await cls.fetchone('SELECT last_insert_rowid() as id')
        return int(row['id']) if row else None

    @classmethod
    async def get_doubts(cls, guild_id: int, unresolved_only: bool = True):
        if unresolved_only:
            return await cls.fetchall('SELECT * FROM doubts WHERE guild_id = ? AND resolved = 0 ORDER BY ts DESC', (guild_id,))
        return await cls.fetchall('SELECT * FROM doubts WHERE guild_id = ? ORDER BY ts DESC', (guild_id,))

    # Doubt thread helpers
    @classmethod
    async def link_doubt_thread(cls, doubt_id: int, guild_id: int, channel_id: int, thread_id: int, created_ts: int):
        await cls.execute('INSERT INTO doubt_threads(doubt_id, guild_id, channel_id, thread_id, created_ts) VALUES(?, ?, ?, ?, ?)', (doubt_id, guild_id, channel_id, thread_id, created_ts))

    @classmethod
    async def claim_doubt_thread(cls, thread_id: int, claimer_id: int):
        await cls.execute('UPDATE doubt_threads SET claimed_by = ? WHERE thread_id = ?', (claimer_id, thread_id))

    @classmethod
    async def close_doubt_thread(cls, thread_id: int):
        await cls.execute('UPDATE doubt_threads SET closed = 1 WHERE thread_id = ?', (thread_id,))

    @classmethod
    async def get_doubt_by_thread(cls, thread_id: int):
        return await cls.fetchone('SELECT dt.*, d.user_id as asker_id, d.question FROM doubt_threads dt JOIN doubts d ON dt.doubt_id = d.id WHERE dt.thread_id = ?', (thread_id,))

    # Reminders
    @classmethod
    async def add_reminder(cls, user_id: int, guild_id: Optional[int], channel_id: Optional[int], message: str, remind_at: int):
        await cls.execute('INSERT INTO reminders(user_id, guild_id, channel_id, message, remind_at) VALUES(?, ?, ?, ?, ?)', (user_id, guild_id, channel_id, message, remind_at))

    @classmethod
    async def get_pending_reminders(cls, until_ts: int):
        return await cls.fetchall('SELECT * FROM reminders WHERE sent = 0 AND remind_at <= ? ORDER BY remind_at ASC', (until_ts,))

    @classmethod
    async def mark_reminder_sent(cls, reminder_id: int):
        await cls.execute('UPDATE reminders SET sent = 1 WHERE id = ?', (reminder_id,))

    # Progress
    @classmethod
    async def set_progress(cls, user_id: int, guild_id: int, subject: str, percent: int):
        await cls.execute('REPLACE INTO progress(user_id, guild_id, subject, percent) VALUES(?, ?, ?, ?)', (user_id, guild_id, subject, percent))

    @classmethod
    async def get_progress(cls, user_id: int, guild_id: int):
        return await cls.fetchall('SELECT subject, percent FROM progress WHERE user_id = ? AND guild_id = ?', (user_id, guild_id))

    # ------------------ Analytics helpers ------------------
    @classmethod
    async def total_users_with_logs(cls) -> int:
        row = await cls.fetchone('SELECT COUNT(DISTINCT user_id) as cnt FROM study_logs')
        return int(row['cnt']) if row else 0

    @classmethod
    async def total_study_minutes(cls) -> int:
        row = await cls.fetchone('SELECT SUM(minutes) as total FROM study_logs')
        return int(row['total']) if row and row['total'] is not None else 0

    @classmethod
    async def top_subjects(cls, limit: int = 5):
        rows = await cls.fetchall('SELECT topic, SUM(minutes) as total FROM study_logs GROUP BY topic ORDER BY total DESC LIMIT ?', (limit,))
        return rows

    # Streak helpers for compatibility with cog logic
    @classmethod
    async def get_streak(cls, user_id: int):
        row = await cls.fetchone('SELECT count, last_date FROM streaks WHERE user_id = ?', (user_id,))
        return dict(row) if row else None

    @classmethod
    async def set_streak(cls, user_id: int, count: int, last_date: str):
        await cls.execute('REPLACE INTO streaks(user_id, count, last_date) VALUES(?, ?, ?)', (user_id, count, last_date))

    @classmethod
    async def close_db(cls):
        if cls._conn:
            await cls._conn.close()
            cls._conn = None

    # ------------------ Activity helpers ------------------
    @classmethod
    async def add_weekly_message(cls, guild_id: int, user_id: int, week_start: int, count: int = 1):
        await cls.execute('''
            INSERT INTO activity_messages(guild_id, user_id, week_start, messages)
            VALUES(?, ?, ?, ?)
            ON CONFLICT(guild_id, user_id, week_start) DO UPDATE SET messages = messages + excluded.messages
        ''', (guild_id, user_id, week_start, count))

    @classmethod
    async def add_weekly_voice_seconds(cls, guild_id: int, user_id: int, week_start: int, seconds: int):
        await cls.execute('''
            INSERT INTO activity_voice(guild_id, user_id, week_start, seconds)
            VALUES(?, ?, ?, ?)
            ON CONFLICT(guild_id, user_id, week_start) DO UPDATE SET seconds = seconds + excluded.seconds
        ''', (guild_id, user_id, week_start, seconds))

    @classmethod
    async def get_weekly_activity(cls, guild_id: int, week_start: int, limit: int = 10):
        # Return combined score (simple sum of normalized values) - for now sum messages + seconds/60
        rows = await cls.fetchall('''
            SELECT m.user_id as user_id, COALESCE(m.messages,0) as messages, COALESCE(v.seconds,0) as seconds
            FROM (
                SELECT user_id, messages FROM activity_messages WHERE guild_id = ? AND week_start = ?
            ) m
            LEFT JOIN (
                SELECT user_id, seconds FROM activity_voice WHERE guild_id = ? AND week_start = ?
            ) v ON m.user_id = v.user_id
            UNION
            SELECT v.user_id as user_id, COALESCE(m2.messages,0) as messages, v.seconds as seconds
            FROM (
                SELECT user_id, seconds FROM activity_voice WHERE guild_id = ? AND week_start = ?
            ) v
            LEFT JOIN (
                SELECT user_id, messages FROM activity_messages WHERE guild_id = ? AND week_start = ?
            ) m2 ON v.user_id = m2.user_id
        ''', (guild_id, week_start, guild_id, week_start, guild_id, week_start))
        # aggregate by user
        agg = {}
        for r in rows:
            uid = int(r['user_id'])
            msgs = int(r['messages'] or 0)
            secs = int(r['seconds'] or 0)
            if uid not in agg:
                agg[uid] = {'messages': 0, 'seconds': 0}
            agg[uid]['messages'] += msgs
            agg[uid]['seconds'] += secs
        # compute simple score: messages + (seconds/60)
        scored = [(uid, data['messages'], data['seconds'], data['messages'] + data['seconds']/60) for uid, data in agg.items()]
        scored.sort(key=lambda x: x[3], reverse=True)
        return scored[:limit]

    @classmethod
    async def set_activity_config(cls, guild_id: int, role_id: Optional[int], channel_ids: Optional[str], reset_weekday: int = 0, reset_hour: int = 0):
        await cls.execute('REPLACE INTO activity_config(guild_id, role_id, channel_ids, reset_weekday, reset_hour) VALUES(?, ?, ?, ?, ?)', (guild_id, role_id, channel_ids, reset_weekday, reset_hour))

    @classmethod
    async def get_activity_config(cls, guild_id: int):
        row = await cls.fetchone('SELECT * FROM activity_config WHERE guild_id = ?', (guild_id,))
        return dict(row) if row else None

    @classmethod
    async def get_all_activity_configs(cls):
        return await cls.fetchall('SELECT * FROM activity_config')

    @classmethod
    async def update_last_processed_week(cls, guild_id: int, week_start: int):
        await cls.execute('UPDATE activity_config SET last_processed_week = ? WHERE guild_id = ?', (week_start, guild_id))

    # ------------------ Extended platform tables ------------------
    # Quizzes and Tests
    @classmethod
    async def create_quiz(cls, guild_id: int, title: str, config_json: str, creator_id: int):
        cur = await cls.execute('INSERT INTO quizzes(guild_id, title, config, creator_id, created_at) VALUES(?, ?, ?, ?, ?)', (guild_id, title, config_json, creator_id, int(time.time())))
        return cur.lastrowid

    @classmethod
    async def add_quiz_question(cls, quiz_id: int, question_json: str):
        cur = await cls.execute('INSERT INTO quiz_questions(quiz_id, question_json) VALUES(?, ?)', (quiz_id, question_json))
        return cur.lastrowid

    @classmethod
    async def add_question_option(cls, question_id: int, option_index: int, option_text: str, is_correct: bool = False):
        await cls.execute('INSERT INTO question_options(question_id, option_index, option_text, is_correct) VALUES(?, ?, ?, ?)', (question_id, option_index, option_text, int(bool(is_correct))))

    @classmethod
    async def get_question_options(cls, question_id: int):
        return await cls.fetchall('SELECT option_index, option_text, is_correct FROM question_options WHERE question_id = ? ORDER BY option_index ASC', (question_id,))

    @classmethod
    async def get_quiz(cls, quiz_id: int):
        row = await cls.fetchone('SELECT * FROM quizzes WHERE id = ?', (quiz_id,))
        return dict(row) if row else None

    @classmethod
    async def get_quiz_questions(cls, quiz_id: int):
        return await cls.fetchall('SELECT * FROM quiz_questions WHERE quiz_id = ? ORDER BY id ASC', (quiz_id,))

    @classmethod
    async def list_quizzes(cls, guild_id: Optional[int] = None):
        if guild_id:
            return await cls.fetchall('SELECT * FROM quizzes WHERE guild_id = ? ORDER BY created_at DESC', (guild_id,))
        return await cls.fetchall('SELECT * FROM quizzes ORDER BY created_at DESC')

    # Quiz session helpers
    @classmethod
    async def start_quiz_session(cls, quiz_id: int, user_id: int):
        cur = await cls.execute('INSERT INTO quiz_sessions(quiz_id, user_id, started_at) VALUES(?, ?, ?)', (quiz_id, user_id, int(time.time())))
        return cur.lastrowid

    @classmethod
    async def record_quiz_response(cls, session_id: int, question_id: int, selected_index: int, answer_text: str, correct: int, time_taken: int):
        await cls.execute('INSERT INTO quiz_responses(session_id, question_id, selected_index, answer_text, correct, time_taken, ts) VALUES(?, ?, ?, ?, ?, ?, ?)', (session_id, question_id, selected_index, answer_text, int(bool(correct)), int(time_taken), int(time.time())))

    @classmethod
    async def finish_quiz_session(cls, session_id: int, final_score: float):
        await cls.execute('UPDATE quiz_sessions SET finished_at = ?, score = ?, state = ? WHERE id = ?', (int(time.time()), final_score, 'finished', session_id))

    @classmethod
    async def get_quiz_session(cls, session_id: int):
        row = await cls.fetchone('SELECT * FROM quiz_sessions WHERE id = ?', (session_id,))
        return dict(row) if row else None

    @classmethod
    async def get_quiz_responses(cls, session_id: int):
        return await cls.fetchall('SELECT * FROM quiz_responses WHERE session_id = ? ORDER BY ts ASC', (session_id,))

    @classmethod
    async def grade_quiz_session(cls, session_id: int):
        # Fetch session and its responses, compute score based on question_options if available
        session = await cls.get_quiz_session(session_id)
        if not session:
            return None
        quiz_id = session['quiz_id']
        responses = await cls.get_quiz_responses(session_id)
        if not responses:
            final_score = 0.0
        else:
            correct = 0
            total = 0
            for r in responses:
                total += 1
                # If response row includes correct flag, use it; else look up option
                if 'correct' in r.keys() and r['correct'] is not None:
                    if int(r['correct']):
                        correct += 1
                else:
                    # attempt to determine from question_options
                    qid = int(r['question_id'])
                    sel = int(r['selected_index']) if r['selected_index'] is not None else None
                    if sel is not None:
                        opts = await cls.fetchall('SELECT is_correct FROM question_options WHERE question_id = ? AND option_index = ?', (qid, sel))
                        if opts and int(opts[0]['is_correct']):
                            correct += 1
            final_score = (correct / total) * 100.0 if total > 0 else 0.0

        # update session and record attempt
        await cls.finish_quiz_session(session_id, final_score)
        # record quiz_attempt
        await cls.record_quiz_attempt(session['quiz_id'], session['user_id'], final_score, '{}')
        return final_score

    @classmethod
    async def record_quiz_attempt(cls, quiz_id: int, user_id: int, score: float, details_json: str):
        await cls.execute('INSERT INTO quiz_attempts(quiz_id, user_id, score, details, ts) VALUES(?, ?, ?, ?, ?)', (quiz_id, user_id, score, details_json, int(time.time())))

    @classmethod
    async def get_quiz_leaderboard(cls, quiz_id: int, limit: int = 10):
        rows = await cls.fetchall('SELECT user_id, MAX(score) as best FROM quiz_attempts WHERE quiz_id = ? GROUP BY user_id ORDER BY best DESC LIMIT ?', (quiz_id, limit))
        return rows

    # Games / Matches
    @classmethod
    async def create_match(cls, guild_id: int, game_type: str, metadata_json: str):
        await cls.execute('INSERT INTO matches(guild_id, game_type, metadata, created_at) VALUES(?, ?, ?, ?)', (guild_id, game_type, metadata_json, int(time.time())))

    @classmethod
    async def record_match_result(cls, match_id: int, user_id: int, result_json: str):
        await cls.execute('INSERT INTO match_results(match_id, user_id, result) VALUES(?, ?, ?)', (match_id, user_id, result_json))

    @classmethod
    async def get_match_results(cls, match_id: int):
        return await cls.fetchall('SELECT user_id, result FROM match_results WHERE match_id = ?', (match_id,))

    # Economy: wallets and inventory
    @classmethod
    async def ensure_wallet(cls, guild_id: int, user_id: int):
        await cls.execute('INSERT INTO wallets(guild_id, user_id, balance) VALUES(?, ?, 0) ON CONFLICT(guild_id, user_id) DO NOTHING', (guild_id, user_id))

    @classmethod
    async def add_balance(cls, guild_id: int, user_id: int, amount: int):
        await cls.execute('INSERT INTO wallets(guild_id, user_id, balance) VALUES(?, ?, ?) ON CONFLICT(guild_id, user_id) DO UPDATE SET balance = balance + excluded.balance', (guild_id, user_id, amount))

    @classmethod
    async def get_balance(cls, guild_id: int, user_id: int):
        row = await cls.fetchone('SELECT balance FROM wallets WHERE guild_id = ? AND user_id = ?', (guild_id, user_id))
        return int(row['balance']) if row else 0

    @classmethod
    async def add_inventory_item(cls, guild_id: int, user_id: int, item_id: str, qty: int = 1):
        await cls.execute('INSERT INTO inventory(guild_id, user_id, item_id, qty) VALUES(?, ?, ?, ?) ON CONFLICT(guild_id, user_id, item_id) DO UPDATE SET qty = qty + excluded.qty', (guild_id, user_id, item_id, qty))

    @classmethod
    async def get_inventory(cls, guild_id: int, user_id: int):
        return await cls.fetchall('SELECT item_id, qty FROM inventory WHERE guild_id = ? AND user_id = ?', (guild_id, user_id))

    # Achievements
    @classmethod
    async def award_achievement(cls, guild_id: int, user_id: int, achv_key: str, meta_json: str = None):
        await cls.execute('INSERT INTO achievements(guild_id, user_id, achv_key, meta, ts) VALUES(?, ?, ?, ?, ?) ON CONFLICT(guild_id, user_id, achv_key) DO NOTHING', (guild_id, user_id, achv_key, meta_json, int(time.time())))

    @classmethod
    async def get_achievements(cls, guild_id: int, user_id: int):
        return await cls.fetchall('SELECT achv_key, meta, ts FROM achievements WHERE guild_id = ? AND user_id = ?', (guild_id, user_id))

    # Todos / tasks
    @classmethod
    async def create_todo(cls, guild_id: int, user_id: int, title: str, due_ts: int = None):
        await cls.execute('INSERT INTO todos(guild_id, user_id, title, due_ts, completed, created_ts) VALUES(?, ?, ?, ?, 0, ?)', (guild_id, user_id, title, due_ts, int(time.time())))

    @classmethod
    async def list_todos(cls, guild_id: int, user_id: int, include_completed: bool = False):
        if include_completed:
            return await cls.fetchall('SELECT * FROM todos WHERE guild_id = ? AND user_id = ? ORDER BY created_ts DESC', (guild_id, user_id))
        return await cls.fetchall('SELECT * FROM todos WHERE guild_id = ? AND user_id = ? AND completed = 0 ORDER BY created_ts DESC', (guild_id, user_id))

    @classmethod
    async def complete_todo(cls, todo_id: int):
        await cls.execute('UPDATE todos SET completed = 1 WHERE id = ?', (todo_id,))

    # Generic archives / logs
    @classmethod
    async def archive_event(cls, guild_id: int, event_type: str, payload_json: str):
        await cls.execute('INSERT INTO archives(guild_id, event_type, payload, ts) VALUES(?, ?, ?, ?)', (guild_id, event_type, payload_json, int(time.time())))

