"""AI Mentor cog: Generate personalized study plans using Gemini."""
import discord
from discord.ext import commands
from discord import app_commands
import json
from pathlib import Path
from datetime import datetime, timedelta
import google.generativeai as genai
from utils import db


CONFIG_PATH = Path(__file__).parent.parent / 'config.json'

# Mock study plan for when Gemini is unavailable
MOCK_PLAN = """Here's your 5-day Chemistry study plan:

Day 1: Atomic Structure (2h)
- Review Bohr model
- Practice electron configuration
- Solve quantum number problems

Day 2: Chemical Bonding (2h)
- Ionic vs Covalent bonds
- VSEPR Theory practice
- Lewis structures

Day 3: Thermodynamics (2.5h)
- Laws of thermodynamics
- Enthalpy calculations
- Hess's Law problems

Day 4: Kinetics (2h)
- Rate laws
- Activation energy
- Reaction mechanisms

Day 5: Review & Practice (3h)
- Past paper questions
- Concept mapping
- Problem solving
"""


class Mentor(commands.Cog):
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

    async def _generate_plan(self, user_id: int, subject: str, days: int) -> str:
        """Generate a study plan using Gemini or fall back to mock."""
        if not self.gemini or not self.model:
            return MOCK_PLAN.replace('5-day', f'{days}-day').replace('Chemistry', subject)
            
        try:
            # Get user's study logs for context
            logs = await db.DB.get_user_logs(user_id)
            total_minutes = sum(log['minutes'] for log in logs)
            
            # Get progress in this subject
            progress = await db.DB.get_progress(user_id, None)
            subject_progress = 0
            for p in progress:
                if p['subject'].lower() == subject.lower():
                    subject_progress = p['percent']
                    break
                    
            prompt = f"""Generate a {days}-day study plan for {subject}.

Context:
- Student has studied {total_minutes} total minutes
- Current progress in {subject}: {subject_progress}%
- Plan should be structured by day
- Include estimated time per topic
- Focus on fundamentals if progress < 30%
- Include practice problems
- Add short breaks

Format the response as:
Day 1: Topic (time)
- Subtopic 1
- Activity
- Practice

[continue for each day]

Keep it focused and achievable."""

            response = await self.model.generate_content(prompt)
            return response.text if response else MOCK_PLAN
        except Exception:
            return MOCK_PLAN

    @commands.hybrid_command(name='mentor')
    async def mentor(self, ctx, action: str = None, subject: str = None, days: int = 5):
        """Get a study plan: !mentor plan <subject> [days=5]"""
        if not action or action != 'plan' or not subject:
            await ctx.send('Usage: !mentor plan <subject> [days=5]')
            return
            
        if days < 1 or days > 14:
            await ctx.send('Please choose a duration between 1 and 14 days.')
            return
            
        async with ctx.typing():
            plan = await self._generate_plan(ctx.author.id, subject, days)
            
            embed = discord.Embed(
                title=f"📚 {days}-Day {subject} Study Plan",
                description=plan,
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Generated for {ctx.author.name}")
            
            await ctx.send(embed=embed)




async def setup(bot: commands.Bot):
    await bot.add_cog(Mentor(bot))