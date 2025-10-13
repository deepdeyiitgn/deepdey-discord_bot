"""Study Suggestion cog: AI-powered study recommendations."""
import discord
from discord.ext import commands
from discord import app_commands
import json
from pathlib import Path
import time
from datetime import datetime, timedelta
import google.generativeai as genai
from utils import db


CONFIG_PATH = Path(__file__).parent.parent / 'config.json'

# Mock suggestions for when Gemini is unavailable
MOCK_SUGGESTIONS = [
    "I notice you've spent more time on Physics lately. Consider balancing with some Chemistry practice!",
    "Your Math progress seems lower this week. A focused Math session could help catch up.",
    "You've been consistent with Chemistry. Maybe try some integrated Physics-Chemistry problems?",
    "Your study patterns show good focus. Try increasing session length by 5-10 minutes.",
    "Regular short breaks improve retention. Remember the 5-minute break after each session!"
]


class StudyGuide(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.gemini = None
        self.model = None
        
    async def cog_load(self):
        try:
            config = json.loads(CONFIG_PATH.read_text())
            if 'gemini_api_key' in config:
                genai.configure(api_key=config['gemini_api_key'])
                self.model = genai.GenerativeModel('gemini-pro')
                self.gemini = True
        except Exception:
            self.gemini = False

    async def _analyze_study_pattern(self, user_id: int) -> str:
        """Analyze study logs and progress to make suggestions."""
        if not self.gemini or not self.model:
            import random
            return random.choice(MOCK_SUGGESTIONS)
            
        try:
            # Get recent logs (last 7 days)
            week_ago = int(time.time() - (7 * 24 * 60 * 60))
            logs = await db.DB.get_user_logs(user_id, since_ts=week_ago)
            
            # Aggregate by subject
            subjects = {}
            for log in logs:
                topic = log['topic'].lower() if log['topic'] else 'unknown'
                minutes = log['minutes']
                if topic in subjects:
                    subjects[topic]['minutes'] += minutes
                    subjects[topic]['sessions'] += 1
                else:
                    subjects[topic] = {'minutes': minutes, 'sessions': 1}
            
            # Get progress in each subject
            progress = await db.DB.get_progress(user_id, None)
            progress_data = {p['subject'].lower(): p['percent'] for p in progress}
            
            # Build context for Gemini
            context = ["Study pattern analysis:\n"]
            context.append("Recent activity (7 days):")
            for subj, data in subjects.items():
                context.append(f"- {subj}: {data['minutes']} minutes in {data['sessions']} sessions")
            
            context.append("\nProgress tracking:")
            for subj, pct in progress_data.items():
                context.append(f"- {subj}: {pct}% complete")
            
            prompt = f"""Based on this student's data:

{'\n'.join(context)}

Provide ONE specific, actionable study suggestion that:
1. Addresses any subject imbalances
2. Considers current progress
3. Maintains engagement and motivation

Keep it conversational and encouraging, max 2-3 sentences. Include a relevant emoji."""

            response = await self.model.generate_content(prompt)
            return response.text if response else random.choice(MOCK_SUGGESTIONS)
        except Exception:
            import random
            return random.choice(MOCK_SUGGESTIONS)

    @commands.hybrid_command(name='suggest')
    async def suggest(self, ctx):
        """Get a personalized study suggestion"""
        async with ctx.typing():
            suggestion = await self._analyze_study_pattern(ctx.author.id)
            await ctx.send(f"📝 Study Suggestion:\n{suggestion}")




async def setup(bot: commands.Bot):
    await bot.add_cog(StudyGuide(bot))