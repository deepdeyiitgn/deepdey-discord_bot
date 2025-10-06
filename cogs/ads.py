import discord
from discord.ext import commands
from discord import app_commands
from pathlib import Path
from typing import Optional
import random
import datetime

BASE_DIR = Path(__file__).parent.parent

STUDY_TIPS = [
    {
        'title': '🎯 Pomodoro Technique',
        'description': 'Study for 25 minutes, take a 5-minute break. After 4 rounds, take a longer 15-30 minute break.',
        'link': 'https://todoist.com/productivity-methods/pomodoro-technique'
    },
    {
        'title': '📚 Active Recall',
        'description': 'Test yourself frequently. Create flashcards, practice problems, or teach concepts to others.',
        'link': 'https://www.youtube.com/watch?v=ukLnPbIffxE'
    },
    {
        'title': '🧠 Mind Mapping',
        'description': 'Create visual connections between related concepts to better understand and remember them.',
        'link': 'https://www.mindmeister.com/blog/mind-mapping-guide/'
    },
    {
        'title': '⏰ Spaced Repetition',
        'description': 'Review material at increasing intervals to optimize long-term retention.',
        'link': 'https://ncase.me/remember/'
    },
    {
        'title': '📝 Cornell Note-Taking',
        'description': 'Divide your notes into questions, notes, and summary sections for better organization.',
        'link': 'http://lsc.cornell.edu/how-to-study/taking-notes/cornell-note-taking-system/'
    }
]

PROMOTIONAL_AD = (
    "Sponsored by Deep Dey - The FUTURE IITIAN 🎯\n"
    "YouTube: https://www.youtube.com/channel/UCrh1Mx5CTTbbkgW5O6iS2Tw/\n"
    "Website: https://www.deepdeyiitk.com\n"
    "Bot website: https://bots.deepdeyiitk.com\n"
    "Apps: https://apps.deepdeyiitk.com\n"
    "Instagram: https://www.instagram.com/deepdey.official/\n"
    "Discord: @deepdey.official\n"
    "Owner: Deep Dey"
)

DEFAULT_AD = PROMOTIONAL_AD  # For backwards compatibility


class AdsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.message_counter = {}  # Format: {channel_id: count}
        self._last_ad = {}  # Format: {channel_id: timestamp}
        self._fallback_store = {}  # Fallback storage for settings
        self._db_available = False
        self.active_channels = set()  # Channels where commands were used
        self.ad_task = None

    async def cog_load(self):
        """Start the timed advertisement task when the cog loads"""
        self.ad_task = self.bot.loop.create_task(self.timed_sponsor_task())

    async def cog_unload(self):
        """Cancel the timed advertisement task when the cog unloads"""
        if self.ad_task:
            self.ad_task.cancel()

    async def timed_sponsor_task(self):
        """Task that sends sponsor messages every 5 minutes in active channels"""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                current_time = datetime.datetime.now()
                channels_to_remove = set()

                for channel_id in self.active_channels.copy():
                    channel = self.bot.get_channel(channel_id)
                    if channel is None:
                        channels_to_remove.add(channel_id)
                        continue

                    if channel_id in self._last_ad:
                        time_diff = (current_time - self._last_ad[channel_id]).total_seconds()
                        if time_diff >= 300:  # 5 minutes = 300 seconds
                            await self.send_sponsor_message(channel)
                            self._last_ad[channel_id] = current_time

                # Remove invalid channels
                self.active_channels -= channels_to_remove

            except Exception as e:
                print(f"Error in timed sponsor task: {e}")

            await asyncio.sleep(60)  # Check every minute

    async def send_sponsor_message(self, channel, ad_text=None):
        """Send the sponsor message to the specified channel"""
        try:
            if ad_text is None:
                ad_text = PROMOTIONAL_AD
            embed = discord.Embed(
                title="🎯 Study Resources",
                description="Join our learning community!",
                color=discord.Color.gold()
            )
            lines = ad_text.split('\n')
            for line in lines:
                if ':' in line:
                    name, value = line.split(':', 1)
                    embed.add_field(name=name.strip(), value=value.strip(), inline=False)
                else:
                    embed.description += f"\n{line}"
            embed.set_footer(text="Sponsored Message")
            await channel.send(embed=embed)
        except Exception as e:
            print(f"Error sending sponsor message: {e}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Only process messages sent by the bot itself
        if message.author != self.bot.user:
            return
        if not message.guild:
            return
            
        # Ignore command messages and sponsor messages themselves
        if message.content.startswith(('!ads', '.ads', '/ads')) or \
           (message.embeds and any('Sponsored Message' in embed.footer.text for embed in message.embeds if embed.footer)):
            return

        channel_id = message.channel.id
        now = datetime.datetime.now()
        
        # Cooldown: don't send ad more than once every 30 seconds per channel
        if channel_id in self._last_ad:
            if (now - self._last_ad[channel_id]).total_seconds() < 30:
                return

        # Increment message counter for this channel
        self.message_counter[channel_id] = self.message_counter.get(channel_id, 0) + 1
        print(f"Bot message count in {message.channel.name}: {self.message_counter[channel_id]}")  # Debug log
        
        if self.message_counter[channel_id] >= 3:
            print(f"Sending sponsor message in {message.channel.name}")  # Debug log
            self.message_counter[channel_id] = 0
            self._last_ad[channel_id] = now
            await self.send_sponsor_message(message.channel)


    async def _get_kv(self, key: str):
        """Get a value from DB or fallback store."""
        return self._fallback_store.get(key)

    async def _set_kv(self, key: str, value: str):
        """Set a value in DB or fallback store."""
        self._fallback_store[key] = value


    @commands.hybrid_command(name="ads", description="Show sponsor message")
    async def ads(self, ctx):
        """Show sponsor message (prefix or slash)"""
        # Add channel to active channels list
        self.active_channels.add(ctx.channel.id)
        
        await self.send_sponsor_message(ctx.channel)
        if hasattr(ctx, 'message'):
            try:
                await ctx.message.add_reaction('✅')
            except Exception:
                pass
        elif isinstance(ctx, discord.Interaction):
            await ctx.response.send_message("Sponsor message sent!", ephemeral=True)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Track which channels are using commands"""
        self.active_channels.add(ctx.channel.id)
        self._last_ad[ctx.channel.id] = datetime.datetime.now()


async def setup(bot: commands.Bot):
    await bot.add_cog(AdsCog(bot))
