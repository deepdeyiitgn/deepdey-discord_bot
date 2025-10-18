"""Website stats and API endpoints for Discord bot."""

import discord
from discord.ext import commands, tasks
from discord import app_commands
import time
import json
from pathlib import Path
from flask import jsonify
# Import 'app' from web_server to add routes to it
from utils.web_server import app, keep_alive
import asyncio
from datetime import datetime, timedelta
import logging
from utils import db # Assuming db.py exists in utils for database operations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

website_bot = None # Global variable to hold the bot instance for Flask routes

stats = {
    'uptime_start': time.time(),
    'commands_used': 0,
    'study_sessions': 0,
    'total_study_minutes': 0,
    'active_users': 0
}

# --- Flask Routes ---
# These routes are added to the 'app' imported from web_server.py

# Route to provide ping and uptime for the status page
@app.route('/stats')
def stats_json():
    if not website_bot:
        return jsonify({'ping': 0, 'uptime': '0:00:00'})
    try:
        # Calculate ping (latency)
        ping = round(website_bot.latency * 1000) if hasattr(website_bot, 'latency') else 0

        # Calculate uptime
        uptime_seconds = int(time.time() - stats.get('uptime_start', time.time())) # Use get with default
        # Format uptime string H:MM:SS
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}:{minutes:02d}:{seconds:02d}"

        return jsonify({'ping': ping, 'uptime': uptime_str})
    except Exception as e:
        logger.error(f"Failed to build /stats response: {e}")
        return jsonify({'ping': 0, 'uptime': '0:00:00'})


# Route for music status used by the web page
@app.route('/api/music/status')
def music_status():
    """Get current music playback status."""
    if not website_bot:
        return jsonify({'error': 'Bot not ready'})
    try:
        music_cog = website_bot.get_cog('Music')
        if not music_cog:
            return jsonify({'error': 'Music cog not loaded'})

        status = {
            'playing': False,
            'current_track': 'N/A',
            'volume': 0,
        }

        if hasattr(music_cog, 'voice_client') and music_cog.voice_client and music_cog.voice_client.is_connected():
            if music_cog.voice_client.is_playing() or music_cog.voice_client.is_paused():
                status['playing'] = True
                status['volume'] = music_cog.volume
                guild_id = music_cog.voice_client.guild.id
                current_info = music_cog.current_track_info.get(guild_id)
                if current_info:
                    track_title = current_info.get('title')
                    status['current_track'] = track_title if track_title else 'Loading info...'
                else:
                    status['current_track'] = 'Loading info...' # Or set to Radio Stream if using that version

        return jsonify(status)
    except Exception as e:
        logger.error(f"Error in /api/music/status: {e}")
        return jsonify({'error': str(e)})

# Other API routes (stats, leaderboard, etc.) - ensure they are defined as needed
@app.route('/api/stats')
def get_stats():
    # ... (Implementation as provided previously)
    if not website_bot: return jsonify({})
    try:
        ping = round(website_bot.latency * 1000) if hasattr(website_bot, 'latency') else 0
        return jsonify({
            'uptime': int(time.time() - stats['uptime_start']),
            'commands_used': stats.get('commands_used', 0),
            'study_sessions': stats.get('study_sessions', 0),
            'total_study_minutes': stats.get('total_study_minutes', 0),
            'active_users': stats.get('active_users', 0),
            'latency': ping
        })
    except Exception as e:
        logger.error(f"Failed to build /api/stats response: {e}")
        return jsonify({})

# Helper functions for async DB calls in Flask context
async def _fetch_db_data(query, params=()):
    return await db.DB.fetchall(query, params)
async def _fetch_db_one(query, params=()):
     return await db.DB.fetchone(query, params)
def run_async_in_flask(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

@app.route('/api/leaderboard')
def get_leaderboard():
    # ... (Implementation as provided previously, using run_async_in_flask)
    if not website_bot: return jsonify([])
    try:
        leaderboard_data = run_async_in_flask(db.DB.get_leaderboard(limit=10))
        formatted = []
        for entry in leaderboard_data:
            user = website_bot.get_user(entry['user_id'])
            if user:
                formatted.append({ 'user': user.display_name, 'minutes': entry.get('total_minutes', 0) })
        return jsonify(formatted)
    except Exception as e:
        logger.error(f"Failed to build /api/leaderboard response: {e}")
        return jsonify([])

@app.route('/api/activity')
def get_activity():
    # ... (Implementation as provided previously, using run_async_in_flask)
     if not website_bot: return jsonify({})
     try:
        week_ago = datetime.now() - timedelta(days=7)
        logs = run_async_in_flask(
            _fetch_db_data(
                'SELECT DATE(ts, "unixepoch") as date, COUNT(*) as count FROM study_logs WHERE ts >= ? GROUP BY date',
                (week_ago.timestamp(),)
            )
        )
        activity = {str(log['date']): log['count'] for log in logs}
        return jsonify(activity)
     except Exception as e:
        logger.error(f"Failed to build /api/activity response: {e}")
        return jsonify({})

@app.route('/api/subjects')
def get_subjects():
    # ... (Implementation as provided previously, using run_async_in_flask)
    if not website_bot: return jsonify({})
    try:
        logs = run_async_in_flask(
            _fetch_db_data('SELECT topic, SUM(minutes) as total FROM study_logs GROUP BY topic')
        )
        subjects = {log['topic'] or 'Unknown': log['total'] for log in logs}
        return jsonify(subjects)
    except Exception as e:
        logger.error(f"Failed to build /api/subjects response: {e}")
        return jsonify({})


# --- Website Cog Class ---

class Website(commands.Cog):
    def __init__(self, bot):
        global website_bot
        self.bot = bot
        website_bot = bot # Set the global bot instance
        self._load_stats()
        # Make sure the task loop starts only after bot is ready
        # self.update_stats.start() # Start moved to before_loop

        # Start the keep_alive Flask server thread
        try:
            keep_alive()
        except Exception as e:
            logger.error(f"Failed to start keep_alive thread: {e}")

    def _load_stats(self):
        """Load previous stats from file, if available."""
        stats_path = Path(__file__).parent.parent / 'data' / 'website_stats.json'
        stats['uptime_start'] = time.time() # Always reset uptime start on load
        if stats_path.exists():
            try:
                with open(stats_path, 'r') as f:
                    saved_stats = json.load(f)
                    # Update only existing keys, don't overwrite uptime_start
                    for key in stats:
                        if key in saved_stats and key != 'uptime_start':
                            stats[key] = saved_stats[key]
                logger.info("Loaded previous website stats.")
            except Exception as e:
                logger.error(f"Failed to load stats: {e}")


    def _save_stats(self):
        """Save current stats to file."""
        stats_path = Path(__file__).parent.parent / 'data' / 'website_stats.json'
        try:
            stats_path.parent.mkdir(parents=True, exist_ok=True)
            with open(stats_path, 'w') as f:
                # Ensure uptime_start is not saved as it resets on load
                stats_to_save = stats.copy()
                if 'uptime_start' in stats_to_save:
                    del stats_to_save['uptime_start']
                json.dump(stats_to_save, f)
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")

    def cog_unload(self):
        """Clean up when cog is unloaded."""
        self.update_stats.cancel()
        self._save_stats()
        logger.info("Website cog unloaded and stats saved.")

    # --- Task Loop (Correctly Indented) ---
    @tasks.loop(minutes=5)
    async def update_stats(self):
        """Update website statistics periodically from the database."""
        try:
            # Check if DB is available (important!)
            if not hasattr(db, 'DB') or not db.DB.is_connected(): # Example check
                 logger.warning("DB not connected, skipping stats update.")
                 return

            row_sessions = await _fetch_db_one('SELECT COUNT(*) as count FROM study_logs')
            stats['study_sessions'] = row_sessions['count'] if row_sessions else 0

            row_minutes = await _fetch_db_one('SELECT SUM(minutes) as total FROM study_logs')
            stats['total_study_minutes'] = row_minutes['total'] if row_minutes and row_minutes['total'] else 0

            day_ago = int(time.time() - (24 * 60 * 60))
            row_active = await _fetch_db_one(
                'SELECT COUNT(DISTINCT user_id) as count FROM study_logs WHERE ts >= ?',
                (day_ago,)
            )
            stats['active_users'] = row_active['count'] if row_active else 0

            self._save_stats()

        except Exception as e:
            logger.error(f"Failed to update stats: {e}", exc_info=True)


    @update_stats.before_loop
    async def before_update_stats(self):
        """Wait until the bot is ready before starting the loop."""
        await self.bot.wait_until_ready()
        logger.info("Website cog update loop starting.")
        # Start the loop here after bot is ready
        self.update_stats.start()


# --- Setup Function ---
async def setup(bot):
    """Adds the Website cog to the bot."""
    stats_dir = Path(__file__).parent.parent / 'data'
    stats_dir.mkdir(exist_ok=True)

    await bot.add_cog(Website(bot))
    logger.info("Website cog loaded.")