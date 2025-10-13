"""Simple Gemini reply cog

Listens for non-command messages and replies using Google Gemini 2.5 Flash
via the Google Generative Language REST API. Reads API key and model from
environment variables GEMINI_API_KEY and GEMINI_MODEL (default: `models/gemini-2.5-flash`).

Notes:
- This implementation performs a single-turn text completion and replies in-channel.
- It ignores messages that start with the bot prefix or are from bots.
- Ensure GEMINI_API_KEY is set in your .env file.
"""
import os
import json
import aiohttp
import asyncio
from discord.ext import commands
import discord
from pathlib import Path
from dotenv import load_dotenv
from utils.db import DB

BASE_DIR = Path(__file__).parents[1]
load_dotenv(BASE_DIR / '.env')

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'models/gemini-2.5-flash')
# The base endpoint for the Generative Language API (REST)
GEMINI_ENDPOINT = os.getenv('GEMINI_ENDPOINT', 'https://generativelanguage.googleapis.com/v1beta2/models')

# Default prefix; keep in sync with bot.get_prefix environment default
DEFAULT_PREFIX = os.getenv('PREFIX', '!')

HEADERS = {
    'Content-Type': 'application/json',
}

if GEMINI_API_KEY:
    HEADERS['Authorization'] = f'Bearer {GEMINI_API_KEY}'


class GeminiReply(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    async def is_enabled_for_channel(self, guild_id: int, channel_id: int) -> bool:
        """Return True if Gemini is enabled for the given guild/channel.

        Behavior:
        - returns False if not enabled for the guild
        - if enabled and channel whitelist is empty or missing -> enabled for all channels
        - if whitelist exists and non-empty -> enabled only if channel_id is in the list
        """
        if not guild_id:
            return False
        key_en = f'gemini_enabled_{guild_id}'
        key_ch = f'gemini_channels_{guild_id}'
        try:
            val = await DB.get_kv(key_en)
            if not val or val != '1':
                return False
            chs = await DB.get_kv(key_ch)
            if not chs:
                return True
            import json as _json
            try:
                lst = _json.loads(chs)
            except Exception:
                lst = []
            if not lst:
                return True
            return int(channel_id) in [int(x) for x in lst]
        except Exception:
            return False

    async def explain_questions(self, questions_text: str) -> str:
        """Ask Gemini to explain the provided questions text and return the explanation."""
        system = (
            "You are StudyBot's helpful assistant. Keep replies short and focused on study help. "
            "When explaining questions give concise step-by-step answers and a short final summary. "
            "Always be polite and assume the user is a student. Bot: StudyBot. Owner: Deep Dey."
        )
        prompt = f"{system}\n\nPlease explain the following questions and provide step-by-step solutions where applicable:\n{questions_text}\nKeep the explanation brief (max ~120 tokens)."
        return await self._call_gemini(prompt)

    def cog_unload(self):
        try:
            asyncio.create_task(self.session.close())
        except Exception:
            pass

    async def _call_gemini(self, prompt: str, max_tokens: int = 120) -> str:
        """Call Gemini API with typing indicator and response limiting.
        
        Args:
            prompt: The text prompt to send to Gemini
            max_tokens: Maximum tokens in response (default 120 for concise replies)
            
        Returns:
            Generated response text
        """
        if not GEMINI_API_KEY:
            return "(Gemini API key not configured)"
        
        url = f"{GEMINI_ENDPOINT}/{GEMINI_MODEL}:generateText"
        
        # System prompt to ensure consistent bot behavior
        system_prompt = (
            "You are StudyBot, Deep Dey's educational Discord bot. "
            "Keep replies focused, encouraging and related to studying. "
            "Key traits: friendly, professional, study-focused. "
            "Never generate harmful, inappropriate or non-educational content. "
            "For questions, provide clear step-by-step explanations. "
            "End responses with a brief key takeaway or study tip."
        )
        
        # Combine system prompt with user prompt
        full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nStudyBot:"
        
        payload = {
            "prompt": {
                "text": full_prompt
            },
            "parameters": {
                "maxOutputTokens": max_tokens,
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95
            },
            "maxOutputTokens": 120,
            "temperature": 0.45,
        }
        try:
            async with self.session.post(url, headers=HEADERS, json=payload, timeout=30) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    return f"(Gemini API error {resp.status}: {text})"
                data = await resp.json()
                # Response format may vary; attempt to extract generated text
                if 'candidates' in data and isinstance(data['candidates'], list) and data['candidates']:
                    text = data['candidates'][0].get('content', '') or ''
                    # Trim to a safe length (keep it short)
                    if len(text) > 800:
                        text = text[:800].rsplit('\n', 1)[0] + '...'
                    return text
                # fallback
                return json.dumps(data)
        except Exception as e:
            return f"(Error calling Gemini API: {e})"

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore messages from bots, DMs, and messages without content
        if (not message.author or message.author.bot or 
            not message.guild or not message.content):
            return

        content = message.content.strip()
        
        # Check if it's a command using bot context
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return
            
        # Also ignore anything that looks like a command
        if content.startswith(DEFAULT_PREFIX) or content.startswith('/'):
            return
            
        # Ignore bot mentions unless it's a direct conversation
        if self.bot.user and content.startswith(f"<@{self.bot.user.id}>"):
            content = content.replace(f"<@{self.bot.user.id}>", "").strip()
            if not content:  # Just a mention with no content
                return

        # Check guild/channel settings before generating a reply
        guild_id = message.guild.id if message.guild else None
        channel_id = message.channel.id if message.channel else None
        try:
            if not await self.is_enabled_for_channel(guild_id, channel_id):
                return
        except Exception:
            # if settings check fails, avoid replying
            print("[GEMINI] Settings check failed; skipping reply")
            return

        # Build system prompt for study context
        system = (
            "You are StudyBot, an educational AI assistant. "
            "Keep replies focused on academics and learning. "
            "Be concise (2-3 sentences), encouraging, and include a brief study tip. "
            "Bot: StudyBot. Owner: Deep Dey."
        )
        prompt = f"{system}\n\nUser: {content}\nAssistant:"

        # Process with typing indicator
        async with message.channel.typing():
            try:
                # Log interaction
                print(f"[GEMINI] Message from {message.author}: {content[:100]}")
                
                # Get response from Gemini
                reply = await self._call_gemini(prompt, max_tokens=120)
                
                # Clean and format response
                if not isinstance(reply, str):
                    reply = str(reply)
                
                if len(reply) > 1000:
                    reply = reply[:1000].rsplit('\n', 1)[0] + '...'
                    
            except Exception as e:
                print(f"[GEMINI] Error processing message: {e}")
                return
        try:
            async with message.channel.typing():
                # Log to terminal
                print(f"[GEMINI] Prompt for {message.author}: {content[:200]}")
                reply = await self._call_gemini(prompt)
                # Limit reply size to avoid huge messages
                if not isinstance(reply, str):
                    reply = str(reply)
                if len(reply) > 1000:
                    reply = reply[:1000].rsplit('\n', 1)[0] + '...'
                await message.channel.send(reply)
                print(f"[GEMINI] Reply sent to {message.author}")
        except Exception as e:
            print(f"[GEMINI] Failed to send reply: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(GeminiReply(bot))
