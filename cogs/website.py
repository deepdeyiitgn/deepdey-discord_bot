"""Website stats and API endpoints for Discord bot."""

import discord
from discord.ext import commands
from discord import app_commands
import time
import json
from pathlib import Path
from flask import Flask, jsonify
import threading
import asyncio
from datetime import datetime, timedelta
import logging
from utils import db


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
stats = {
    'uptime_start': time.time(),
    'commands_used': 0,
    'study_sessions': 0,
    'total_study_minutes': 0,
    'active_users': 0
}

class Website(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._load_stats()
        self.update_stats.start()
        
        # Start Flask server in a separate thread
        thread = threading.Thread(target=self._run_flask)
        thread.daemon = True
        thread.start()

    def _load_stats(self):
        """Load previous stats if available."""
        stats_path = Path(__file__).parent.parent / 'data' / 'website_stats.json'
        if stats_path.exists():
            try:
                saved_stats = json.loads(stats_path.read_text())
                stats.update(saved_stats)
                stats['uptime_start'] = time.time()  # Reset uptime
            except Exception as e:
                logger.error(f"Failed to load stats: {e}")

    def _save_stats(self):
        """Save current stats to file."""
        stats_path = Path(__file__).parent.parent / 'data' / 'website_stats.json'
        try:
            stats_path.write_text(json.dumps(stats))
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")

    def _run_flask(self):
        """Run the Flask server."""
        @app.route('/api/stats')
        def get_stats():
            return jsonify({
                'uptime': int(time.time() - stats['uptime_start']),
                'commands_used': stats['commands_used'],
                'study_sessions': stats['study_sessions'],
                'total_study_minutes': stats['total_study_minutes'],
                'active_users': stats['active_users'],
                'latency': round(self.bot.latency * 1000)  # in ms
            })

        @app.route('/api/leaderboard')
        def get_leaderboard():
            # Get study time leaderboard from DB
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                leaderboard = loop.run_until_complete(
                    db.DB.get_leaderboard(limit=10)
                )
                
                formatted = []
                for entry in leaderboard:
                    user = self.bot.get_user(entry['user_id'])
                    if user:
                        formatted.append({
                            'user': user.display_name,
                            'minutes': entry['total_minutes']
                        })
                        
                return jsonify(formatted)
            finally:
                loop.close()

        @app.route('/api/activity')
        def get_activity():
            # Get daily activity stats
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Get last 7 days of logs
                week_ago = datetime.now() - timedelta(days=7)
                logs = loop.run_until_complete(
                    db.DB.fetchall(
                        'SELECT DATE(ts, "unixepoch") as date, COUNT(*) as count FROM study_logs WHERE ts >= ? GROUP BY date',
                        (week_ago.timestamp(),)
                    )
                )
                
                activity = {
                    str(log['date']): log['count']
                    for log in logs
                }
                
                return jsonify(activity)
            finally:
                loop.close()

        @app.route('/api/subjects')
        def get_subjects():
            # Get subject distribution
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                logs = loop.run_until_complete(
                    db.DB.fetchall(
                        'SELECT topic, SUM(minutes) as total FROM study_logs GROUP BY topic'
                    )
                )
                
                subjects = {
                    log['topic'] or 'Unknown': log['total']
                    for log in logs
                }
                
                return jsonify(subjects)
            finally:
                loop.close()

        try:
            app.run(host='0.0.0.0', port=5000)
        except Exception as e:
            logger.error(f"Flask server error: {e}")

    @tasks.loop(minutes=5)
    async def update_stats(self):
        """Update website statistics periodically."""
        try:
            # Get total study sessions
            stats['study_sessions'] = await db.DB.fetchone(
                'SELECT COUNT(*) as count FROM study_logs'
            )['count']
            
            # Get total minutes studied
            stats['total_study_minutes'] = await db.DB.fetchone(
                'SELECT SUM(minutes) as total FROM study_logs'
            )['total'] or 0
            
            # Get active users (studied in last 24h)
            day_ago = int(time.time() - (24 * 60 * 60))
            stats['active_users'] = await db.DB.fetchone(
                'SELECT COUNT(DISTINCT user_id) as count FROM study_logs WHERE ts >= ?',
                (day_ago,)
            )['count']
            
            # Save updated stats
            self._save_stats()
            
        except Exception as e:
            logger.error(f"Failed to update stats: {e}")

    @update_stats.before_loop
    async def before_update_stats(self):
        await self.bot.wait_until_ready()

    def cog_unload(self):
        """Clean up when cog is unloaded."""
        self.update_stats.cancel()
        self._save_stats()


async def setup(bot):
    # Create stats directory if needed
    stats_dir = Path(__file__).parent.parent / 'data'
    stats_dir.mkdir(exist_ok=True)
    
    await bot.add_cog(Website(bot))