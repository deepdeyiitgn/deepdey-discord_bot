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
        prompt = (
            "Please explain the following questions and provide step-by-step solutions where applicable:\n"
            + questions_text
            + "\nPlease keep explanations clear and concise."
        )
        return await self._call_gemini(prompt)

    def cog_unload(self):
        try:
            asyncio.create_task(self.session.close())
        except Exception:
            pass

    async def _call_gemini(self, prompt: str) -> str:
        if not GEMINI_API_KEY:
            return "(Gemini API key not configured)"
        url = f"{GEMINI_ENDPOINT}/{GEMINI_MODEL}:generateText"
        payload = {
            "prompt": {
                "text": prompt
            },
            "maxOutputTokens": 256,
            "temperature": 0.7,
        }
        try:
            async with self.session.post(url, headers=HEADERS, json=payload, timeout=30) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    return f"(Gemini API error {resp.status}: {text})"
                data = await resp.json()
                # Response format may vary; attempt to extract generated text
                if 'candidates' in data and isinstance(data['candidates'], list) and data['candidates']:
                    return data['candidates'][0].get('content', '')
                # fallback
                return json.dumps(data)
        except Exception as e:
            return f"(Error calling Gemini API: {e})"

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore bots and messages without author
        if not message.author or message.author.bot:
            return

        content = (message.content or '').strip()
        if not content:
            return

        # Ignore commands starting with the configured prefix or bot mention
        if content.startswith(DEFAULT_PREFIX):
            return
        if self.bot.user and content.startswith(f"<@{self.bot.user.id}>"):
            return

        # Optional: ignore messages that look like commands (start with /) - slash commands are interactions
        if content.startswith('/'):
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

        # Call Gemini to generate a reply and send it
        prompt = f"User: {content}\nAssistant:"  # simple persona
        # Log to terminal
        print(f"[GEMINI] Prompt for {message.author}: {content[:200]}")
        reply = await self._call_gemini(prompt)
        # Avoid sending extremely long replies
        if len(reply) > 1900:
            reply = reply[:1900] + '...'
        try:
            await message.channel.send(reply)
            print(f"[GEMINI] Reply sent to {message.author}")
        except Exception as e:
            print(f"[GEMINI] Failed to send reply: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(GeminiReply(bot))
