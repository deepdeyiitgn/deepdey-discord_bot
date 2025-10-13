"""Motivational responder: Reply to user messages with AI-powered motivation."""
import discord
from discord.ext import commands
from discord import app_commands
import json
import random
from pathlib import Path
from utils.helper import async_load_json
import google.generativeai as genai
from typing import Optional


# Load Gemini config
CONFIG_PATH = Path(__file__).parent.parent / 'config.json'

# Pre-defined responses for when Gemini is not available
MOTIVATION_RESPONSES = {
    'demotivated': [
        "Remember why you started! Every small step counts. 💪",
        "You've got this! Take a deep breath and keep pushing forward. ⭐",
        "Don't give up now - your future self will thank you! 🌟",
        "It's okay to feel down, but remember your goals. You can do this! 🎯"
    ],
    'tired': [
        "Take a short break, recharge, and come back stronger! 🔋",
        "Remember to rest if you need to, but don't quit! 💪",
        "Small progress is still progress. Keep going! ⚡",
        "You've come so far - don't stop now! 🌟"
    ],
    'stressed': [
        "Take it one step at a time. You've got this! 🍃",
        "Breathe deeply and focus on what you can control. ✨",
        "You're stronger than you think. Keep pushing! 💪",
        "Every challenge makes you stronger. You can handle this! 🌟"
    ],
    'confused': [
        "Break it down into smaller pieces. One concept at a time! 📚",
        "Don't be afraid to ask for help - that's how we learn! 🤝",
        "You'll get there! Keep working through it step by step. 💡",
        "Confusion is the first step to understanding. Keep going! 🧩"
    ]
}

class Motivation(commands.Cog):
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
            self.gemini = False  # Fall back to pre-defined responses

    def _get_preset_response(self, content: str) -> Optional[str]:
        """Get a pre-defined response based on message content."""
        content = content.lower()
        for key, responses in MOTIVATION_RESPONSES.items():
            if key in content:
                return random.choice(responses)
        return None

    async def _get_gemini_response(self, content: str) -> Optional[str]:
        """Get an AI-generated response using Gemini."""
        if not self.gemini or not self.model:
            return None
            
        try:
            prompt = f"""As a supportive study buddy, generate a brief motivational response (1-2 sentences) to this message: "{content}"
            
            Keep it:
            - Personal and empathetic
            - Focused on academic motivation
            - Positive but realistic
            - Short and impactful
            
            Include 1-2 relevant emojis. Respond directly without any prefixes."""

            response = await self.model.generate_content(prompt)
            return response.text if response else None
        except Exception:
            return None

    @commands.Listener()
    async def on_message(self, message: discord.Message):
        """Listen for messages that might need motivation."""
        # Skip bot messages and commands
        if message.author.bot or message.content.startswith('!'):
            return
            
        # Look for common phrases indicating need for motivation
        triggers = ['demotivated', 'tired of studying', 'cant focus', 
                   'give up', 'too hard', 'confused', 'stressed']
        
        content = message.content.lower()
        if not any(t in content for t in triggers):
            return
            
        # Try Gemini first, fall back to preset
        response = await self._get_gemini_response(message.content)
        if not response:
            response = self._get_preset_response(message.content)
            
        if response:
            await message.reply(response, mention_author=True)

    @commands.hybrid_command(name='motivate')
    async def motivate(self, ctx, *, message: str = None):
        """Get a motivational response: !motivate [situation]"""
        if not message:
            await ctx.send("Tell me what's troubling you, and I'll help motivate you!")
            return
            
        response = await self._get_gemini_response(message)
        if not response:
            response = self._get_preset_response(message)
        if not response:
            response = random.choice(MOTIVATION_RESPONSES['demotivated'])
            
        await ctx.send(response)




async def setup(bot: commands.Bot):
    await bot.add_cog(Motivation(bot))