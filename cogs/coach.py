"""Weekly Coach cog: Weekly study analysis and personalized feedback."""
import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
from pathlib import Path
import time
from datetime import datetime, timedelta
import google.generativeai as genai
from utils import db


CONFIG_PATH = Path(__file__).parent.parent / 'config.json'

# Mock feedback for when Gemini is unavailable
MOCK_FEEDBACK = """📊 Weekly Study Report

Time per subject:
- Physics: 6h 40m
- Chemistry: 3h 20m
- Math: 8h 10m

Analysis:
- Strong focus on Math this week! 💪
- Chemistry needs more attention
- Good overall consistency

Next week targets:
1. Increase Chemistry study time by 2h
2. Maintain current Math momentum
3. Try to balance subject distribution

Keep up the great work! 🌟"""


class WeeklyCoach(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.gemini = None
        self.model = None
        self.weekly_analysis.start()

    def cog_unload(self):
        self.weekly_analysis.cancel()
        
    async def cog_load(self):
        try:
            config = json.loads(CONFIG_PATH.read_text())
            if 'gemini_api_key' in config:
                genai.configure(api_key=config['gemini_api_key'])
                self.model = genai.GenerativeModel('gemini-pro')
                self.gemini = True
        except Exception:
            self.gemini = False

    async def _generate_report(self, user_id: int) -> str:
        """Generate a weekly study report and analysis."""
        if not self.gemini or not self.model:
            return MOCK_FEEDBACK
            
        try:
            # Get this week's logs
            week_ago = int(time.time() - (7 * 24 * 60 * 60))
            logs = await db.DB.get_user_logs(user_id, since_ts=week_ago)
            
            # Get previous week's logs for comparison
            two_weeks_ago = int(time.time() - (14 * 24 * 60 * 60))
            prev_logs = await db.DB.get_user_logs(user_id, since_ts=two_weeks_ago)
            prev_logs = [l for l in prev_logs if l['ts'] < week_ago]
            
            # Aggregate current week by subject
            current_week = {}
            for log in logs:
                topic = log['topic'].lower() if log['topic'] else 'unknown'
                minutes = log['minutes']
                if topic in current_week:
                    current_week[topic] += minutes
                else:
                    current_week[topic] = minutes
                    
            # Aggregate previous week
            prev_week = {}
            for log in prev_logs:
                topic = log['topic'].lower() if log['topic'] else 'unknown'
                minutes = log['minutes']
                if topic in prev_week:
                    prev_week[topic] += minutes
                else:
                    prev_week[topic] = minutes
            
            # Get progress updates
            progress = await db.DB.get_progress(user_id, None)
            progress_data = {p['subject'].lower(): p['percent'] for p in progress}
            
            # Format data for Gemini
            context = ["Weekly Study Analysis\n"]
            
            context.append("This week's study time:")
            for subj, mins in current_week.items():
                hrs = mins // 60
                remaining_mins = mins % 60
                context.append(f"- {subj}: {hrs}h {remaining_mins}m")
            
            context.append("\nCompared to last week:")
            for subj in set(current_week.keys()) | set(prev_week.keys()):
                curr = current_week.get(subj, 0)
                prev = prev_week.get(subj, 0)
                diff = curr - prev
                if diff > 0:
                    context.append(f"- {subj}: +{diff} minutes")
                elif diff < 0:
                    context.append(f"- {subj}: {diff} minutes")
                else:
                    context.append(f"- {subj}: no change")
            
            context.append("\nCurrent progress:")
            for subj, pct in progress_data.items():
                context.append(f"- {subj}: {pct}% complete")
            
            prompt = f"""Based on this student's weekly data:

{'\n'.join(context)}

Generate a concise weekly report with:
1. Time breakdown (formatted as hours and minutes)
2. Brief analysis of changes and patterns
3. 2-3 specific targets for next week
4. One encouraging comment

Format with clear sections and include relevant emojis. Keep it motivational but realistic."""

            response = await self.model.generate_content(prompt)
            return response.text if response else MOCK_FEEDBACK
        except Exception:
            return MOCK_FEEDBACK

    @tasks.loop(hours=24)
    async def weekly_analysis(self):
        """Send weekly reports every Sunday."""
        await self.bot.wait_until_ready()
        
        # Only run on Sundays
        if datetime.now().weekday() != 6:  # 6 = Sunday
            return
            
        # Get all users with study logs in the last week
        week_ago = int(time.time() - (7 * 24 * 60 * 60))
        logs = await db.DB.fetchall('SELECT DISTINCT user_id FROM study_logs WHERE ts >= ?', (week_ago,))
        
        for row in logs:
            user_id = row['user_id']
            try:
                # Try to DM the user
                user = self.bot.get_user(user_id)
                if not user:
                    continue
                    
                report = await self._generate_report(user_id)
                
                embed = discord.Embed(
                    title="📊 Your Weekly Study Analysis",
                    description=report,
                    color=discord.Color.blue()
                )
                embed.set_footer(text=datetime.now().strftime("%B %d, %Y"))
                
                await user.send(embed=embed)
            except Exception:
                continue  # Skip if can't DM

    @weekly_analysis.before_loop
    async def before_weekly_analysis(self):
        await self.bot.wait_until_ready()
        
        # Wait until next Sunday
        now = datetime.now()
        days_ahead = 6 - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_sunday = now.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=days_ahead)
        await asyncio.sleep((next_sunday - now).total_seconds())

    @commands.hybrid_command(name='report')
    async def report(self, ctx):
        """Get your weekly study report now"""
        async with ctx.typing():
            report = await self._generate_report(ctx.author.id)
            
            embed = discord.Embed(
                title="📊 Your Weekly Study Analysis",
                description=report,
                color=discord.Color.blue()
            )
            embed.set_footer(text=datetime.now().strftime("%B %d, %Y"))
            
            await ctx.send(embed=embed)




async def setup(bot: commands.Bot):
    await bot.add_cog(WeeklyCoach(bot))