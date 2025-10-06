"""
Gemini AI integration cog for StudyBot.
Handles non-command message responses using Google's Gemini API.
"""
from discord.ext import commands
import discord
import aiohttp
import json
import os
from pathlib import Path
import aiosqlite

class GeminiCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.model = os.getenv('GEMINI_MODEL', 'gemini-pro')
        self.db_path = Path(__file__).parent.parent / 'data' / 'studybot.db'
        self.session = None
        self.enabled = True  # Global toggle
        self.enabled_channels = set()  # Set of channel IDs where Gemini is enabled
        
    async def cog_load(self):
        """Called when the cog is loaded. Sets up API session and database."""
        # Create aiohttp session for API calls
        self.session = aiohttp.ClientSession()
        
        # Ensure database is initialized
        await self.init_db()
        
        # Load saved settings
        await self.load_settings()

    async def cog_unload(self):
        """Called when the cog is unloaded. Cleanup resources."""
        if self.session:
            await self.session.close()

    async def init_db(self):
        """Initialize database tables for Gemini settings."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS gemini_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS gemini_channels (
                    channel_id INTEGER PRIMARY KEY
                )
            ''')
            await db.commit()

    async def load_settings(self):
        """Load settings from database."""
        async with aiosqlite.connect(self.db_path) as db:
            # Load global toggle
            async with db.execute("SELECT value FROM gemini_settings WHERE key = 'enabled'") as cursor:
                row = await cursor.fetchone()
                if row:
                    self.enabled = row[0].lower() == 'true'
            
            # Load enabled channels
            async with db.execute("SELECT channel_id FROM gemini_channels") as cursor:
                rows = await cursor.fetchall()
                self.enabled_channels = {row[0] for row in rows}
                
    async def save_enabled_state(self, enabled: bool):
        """Save the global enabled state to the database."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO gemini_settings (key, value) VALUES (?, ?)",
                ('enabled', str(enabled).lower())
            )
            await db.commit()
        self.enabled = enabled
        
    async def add_enabled_channel(self, channel_id: int):
        """Add a channel to the enabled channels list."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO gemini_channels (channel_id) VALUES (?)",
                (channel_id,)
            )
            await db.commit()
        self.enabled_channels.add(channel_id)
        
    async def remove_enabled_channel(self, channel_id: int):
        """Remove a channel from the enabled channels list."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM gemini_channels WHERE channel_id = ?",
                (channel_id,)
            )
            await db.commit()
        self.enabled_channels.discard(channel_id)
        
    def is_channel_enabled(self, channel_id: int) -> bool:
        """Check if Gemini responses are enabled for a channel."""
        return self.enabled and (channel_id in self.enabled_channels)
        
    async def get_gemini_response(self, prompt: str) -> tuple[bool, str]:
        """Get a response from the Gemini API.
        
        Args:
            prompt: The user's message to send to Gemini
            
        Returns:
            tuple[bool, str]: (success, response/error message)
        """
        if not self.api_key:
            return False, "Gemini API key not configured. Please set the GEMINI_API_KEY environment variable."
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        
        try:
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            
            async with self.session.post(url, headers=headers, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return False, f"API Error ({response.status}): {error_text}"
                    
                result = await response.json()
                
                try:
                    generated_text = result["candidates"][0]["content"]["parts"][0]["text"]
                    return True, generated_text.strip()
                except (KeyError, IndexError) as e:
                    print(f"Raw response: {json.dumps(result, indent=2)}")
                    return False, f"Failed to parse API response: {str(e)}"
                    
        except aiohttp.ClientError as e:
            return False, f"API request failed: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
            
    @commands.hybrid_group(name="gemini", description="Manage Gemini AI integration")
    @commands.has_permissions(manage_messages=True)
    async def gemini(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            status = "enabled" if self.enabled else "disabled"
            channel_count = len(self.enabled_channels)
            await ctx.send(
                f"Gemini AI is currently {status} globally.\n"
                f"Active in {channel_count} channels.\n"
                "Use `gemini toggle` to enable/disable globally.\n"
                "Use `gemini channel add/remove` to manage channels."
            )
            
    @gemini.command(name="toggle", description="Toggle Gemini responses globally")
    async def gemini_toggle(self, ctx: commands.Context):
        self.enabled = not self.enabled
        await self.save_enabled_state(self.enabled)
        status = "enabled" if self.enabled else "disabled"
        await ctx.send(f"Gemini responses are now {status} globally.")
        
    @gemini.command(name="add", description="Enable Gemini responses in a channel")
    async def gemini_add(self, ctx: commands.Context, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        if channel.id in self.enabled_channels:
            await ctx.send(f"Gemini is already enabled in {channel.mention}!")
            return
            
        await self.add_enabled_channel(channel.id)
        await ctx.send(f"Enabled Gemini responses in {channel.mention}.")
        
    @gemini.command(name="remove", description="Disable Gemini responses in a channel")
    async def gemini_remove(self, ctx: commands.Context, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        if channel.id not in self.enabled_channels:
            await ctx.send(f"Gemini is not enabled in {channel.mention}!")
            return
            
        await self.remove_enabled_channel(channel.id)
        await ctx.send(f"Disabled Gemini responses in {channel.mention}.")
        
    @gemini.command(name="list", description="List channels with Gemini enabled")
    async def gemini_list(self, ctx: commands.Context):
        if not self.enabled_channels:
            await ctx.send("Gemini is not enabled in any channels.")
            return
            
        channels = []
        for channel_id in self.enabled_channels:
            channel = self.bot.get_channel(channel_id)
            if channel:
                channels.append(f"- {channel.mention}")
                
        if not channels:
            await ctx.send("All configured channels are no longer accessible.")
            return
            
        enabled = "enabled" if self.enabled else "disabled"
        message = f"Gemini is {enabled} globally.\nEnabled in channels:\n" + "\n".join(channels)
        await ctx.send(message)
        
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore bot messages (including our own)
        if message.author.bot:
            return
            
        # Ignore messages with commands
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return
            
        # Check if this channel should get Gemini responses
        if not self.is_channel_enabled(message.channel.id):
            return
            
        # Get response from Gemini
        success, response = await self.get_gemini_response(message.content)
        
        if not success:
            # Log the error but don't notify the user
            print(f"Gemini error: {response}")
            return
            
        # Send the response
        try:
            await message.reply(response)
        except discord.HTTPException as e:
            print(f"Failed to send Gemini response: {e}")
            try:
                # Try sending as a regular message if reply fails
                await message.channel.send(response)
            except discord.HTTPException:
                pass  # Give up if both attempts fail

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(GeminiCog(bot))