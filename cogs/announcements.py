"""Announcements cog

Features:
 - Scheduled announcements with configurable channel and interval
 - Daily motivational message
 - Admin-only commands to manage announcements
"""
import discord
from discord.ext import commands, tasks
from discord import Embed
from discord import app_commands
from pathlib import Path
from utils.helper import async_load_json, async_save_json
import asyncio
import datetime
import os


DATA_PATH = Path(__file__).parent.parent / 'data' / 'announcements.json'
ANNOUNCEMENTS_DIR = Path(__file__).parent.parent / 'announcements'


class Announcements(commands.Cog):

    async def announcement_file_autocomplete(self, interaction: discord.Interaction, current: str):
        # Suggest .txt files in the announcements folder
        files = [f.stem for f in ANNOUNCEMENTS_DIR.glob('*.txt')]
        return [app_commands.Choice(name=f, value=f) for f in files if current.lower() in f.lower()][:25]
    """Cog to manage scheduled announcements"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = {}
        self.announcement_loop.start()

    async def cog_load(self):
        self.config = await async_load_json(DATA_PATH, default={'channels': {}, 'daily': ''})

    def cog_unload(self):
        self.announcement_loop.cancel()

    @tasks.loop(minutes=15)
    async def announcement_loop(self):
        # Runs every 15 minutes and checks configs with next_run times
        await self.bot.wait_until_ready()
        configs = await async_load_json(DATA_PATH, default={'channels': {}, 'daily': ''})
        now = datetime.datetime.utcnow()
        for guild_id, conf in configs.get('channels', {}).items():
            ch_id = conf.get('channel_id')
            interval = conf.get('interval_minutes', 60)
            last = conf.get('last_sent')
            msg = conf.get('message', 'Study time!')
            if not ch_id:
                continue
            send = False
            if last is None:
                send = True
            else:
                last_dt = datetime.datetime.fromisoformat(last)
                delta = (now - last_dt).total_seconds()
                if delta >= interval * 60:
                    send = True
            if send:
                try:
                    channel = self.bot.get_channel(ch_id)
                    if channel:
                        embed = discord.Embed(
                            title="📢 Scheduled Announcement",
                            description=msg,
                            color=discord.Color.blue(),
                            timestamp=now
                        )
                        embed.set_footer(text=f"Next announcement in {interval} minutes")
                        await channel.send(embed=embed)
                        conf['last_sent'] = now.isoformat()
                except Exception as e:
                    print(f"Error sending announcement: {e}")
        await async_save_json(DATA_PATH, configs)

    @tasks.loop(hours=24)
    async def daily_motivation(self):
        await self.bot.wait_until_ready()
        cfg = await async_load_json(DATA_PATH, default={'channels': {}, 'daily': ''})
        if not cfg.get('daily'):
            return
        for guild_id, conf in cfg.get('channels', {}).items():
            ch_id = conf.get('channel_id')
            try:
                channel = self.bot.get_channel(ch_id)
                if channel:
                    await channel.send(cfg['daily'])
            except Exception:
                pass

    @commands.hybrid_group(name='announce', invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def announce(self, ctx):
        """Announcements management group"""
        await ctx.send('Use subcommands: set, remove, list, daily')

    @announce.command(name='set')
    @app_commands.describe(
        interval='How often to post the announcement in minutes',
        message='The announcement message to post',
        title='Optional custom title for the announcement',
        color='Optional color for the announcement (e.g. RED, BLUE, GREEN)'
    )
    @commands.has_permissions(administrator=True)
    async def announce_set(self, ctx, interval: int, message: str, title: str = None, color: str = None):
        """Set an announcement in this channel every <interval> minutes with <message>"""
        cfg = await async_load_json(DATA_PATH, default={'channels': {}, 'daily': ''})
        guild_cfg = cfg.setdefault('channels', {}).setdefault(str(ctx.guild.id), {})
        
        # Validate interval
        if interval < 5:
            await ctx.send("❌ Interval must be at least 5 minutes!")
            return
        
        # Format config
        guild_cfg['channel_id'] = ctx.channel.id
        guild_cfg['interval_minutes'] = interval
        guild_cfg['message'] = message
        guild_cfg['title'] = title or "📢 Scheduled Announcement"
        
        # Parse color
        if color:
            try:
                color_value = getattr(discord.Color, color.lower())()
                guild_cfg['color'] = color_value.value
            except AttributeError:
                await ctx.send(f"⚠️ Invalid color '{color}'. Using default blue.")
                guild_cfg['color'] = discord.Color.blue().value
        else:
            guild_cfg['color'] = discord.Color.blue().value
            
        await async_save_json(DATA_PATH, cfg)
        
        # Show preview
        preview = discord.Embed(
            title=guild_cfg['title'],
            description=message,
            color=discord.Color(guild_cfg['color']),
            timestamp=datetime.datetime.utcnow()
        )
        preview.set_footer(text=f"Next announcement in {interval} minutes")
        
        await ctx.send("✅ Announcement set! Here's how it will look:", embed=preview)
        
    @announce.command(name='preview')
    @commands.has_permissions(administrator=True)
    async def announce_preview(self, ctx):
        """Preview the current announcement for this server"""
        cfg = await async_load_json(DATA_PATH, default={'channels': {}, 'daily': ''})
        guild_cfg = cfg.get('channels', {}).get(str(ctx.guild.id), {})
        
        if not guild_cfg:
            await ctx.send("❌ No announcement configured for this server!")
            return
            
        preview = discord.Embed(
            title=guild_cfg.get('title', "📢 Scheduled Announcement"),
            description=guild_cfg.get('message', 'No message set'),
            color=discord.Color(guild_cfg.get('color', discord.Color.blue().value)),
            timestamp=datetime.datetime.utcnow()
        )
        preview.set_footer(text=f"Next announcement in {guild_cfg.get('interval_minutes', 60)} minutes")
        
        await ctx.send("📝 Current announcement preview:", embed=preview)
        
    @announce.command(name='send')
    @app_commands.describe(
        channel='The channel to send the announcement to',
        message='The announcement message',
        title='Optional custom title',
        color='Optional color (e.g. RED, BLUE, GREEN)'
    )
    @commands.has_permissions(administrator=True)
    async def announce_send(self, ctx, channel: discord.TextChannel, message: str, title: str = None, color: str = None):
        """Send a one-time custom announcement"""
        # Parse color
        try:
            color_value = getattr(discord.Color, (color or 'blue').lower())()
        except AttributeError:
            await ctx.send(f"⚠️ Invalid color '{color}'. Using default blue.")
            color_value = discord.Color.blue()
            
        # Create and send announcement
        embed = discord.Embed(
            title=title or "📢 Announcement",
            description=message,
            color=color_value,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=f"Sent by {ctx.author.display_name}")
        
        try:
            await channel.send(embed=embed)
            await ctx.send("✅ Announcement sent!")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to send messages in that channel!")
        except Exception as e:
            await ctx.send(f"❌ Failed to send announcement: {e}")
        await ctx.send(f'Announcement set every {interval}m in this channel.')

    @announce.command(name='file')
    @app_commands.describe(
        channel='The channel to send the announcement to',
        filename='The name of the announcement file to send (without .txt extension)',
        title='Optional custom title',
        color='Optional color (e.g. RED, BLUE, GREEN)'
    )
    @app_commands.autocomplete(filename=announcement_file_autocomplete)
    @commands.has_permissions(administrator=True)
    async def announce_file(self, ctx, channel: discord.TextChannel, filename: str, title: str = None, color: str = None):
        """Send the contents of an announcement file to the specified channel"""
        file_path = ANNOUNCEMENTS_DIR / f"{filename}.txt"
        
        if not file_path.exists():
            await ctx.send(f"❌ Announcement file '{filename}' not found!")
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                message = f.read().strip()
        except Exception as e:
            await ctx.send(f"❌ Error reading announcement file: {e}")
            return
            
        # Parse color
        try:
            color_value = getattr(discord.Color, (color or 'blue').lower())()
        except AttributeError:
            await ctx.send(f"⚠️ Invalid color '{color}'. Using default blue.")
            color_value = discord.Color.blue()
            
        # Create and send announcement
        embed = discord.Embed(
            title=title or f"📢 {filename.title()} Announcement",
            description=message,
            color=color_value,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=f"Sent by {ctx.author.display_name}")
        
        try:
            await channel.send(embed=embed)
            await ctx.send("✅ Announcement sent!")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to send messages in that channel!")
        except Exception as e:
            await ctx.send(f"❌ Failed to send announcement: {e}")

    @announce.command(name='remove')
    @app_commands.describe(
        reason='Optional reason for removing the announcement'
    )
    @commands.has_permissions(administrator=True)
    async def announce_remove(self, ctx, *, reason: str = None):
        """Remove announcement for this guild"""
        cfg = await async_load_json(DATA_PATH, default={'channels': {}, 'daily': ''})
        if str(ctx.guild.id) in cfg.get('channels', {}):
            cfg['channels'].pop(str(ctx.guild.id), None)
            await async_save_json(DATA_PATH, cfg)
            await ctx.send(f'Announcement removed{f" - {reason}" if reason else "."}')
        else:
            await ctx.send('No announcement set.')

    @announce.command(name='daily')
    @app_commands.describe(
        message='The daily motivational message to send'
    )
    @commands.has_permissions(administrator=True)
    async def announce_daily(self, ctx, *, message: str):
        """Set a daily motivational message for all announcement channels"""
        cfg = await async_load_json(DATA_PATH, default={'channels': {}, 'daily': ''})
        cfg['daily'] = message
        await async_save_json(DATA_PATH, cfg)
        if not self.daily_motivation.is_running():
            self.daily_motivation.start()
        await ctx.send('Daily motivational message set.')

    @announce.command(name='list')
    @commands.has_permissions(administrator=True)
    async def announce_list(self, ctx):
        """List current announcement settings and available announcement files"""
        # Show current settings
        cfg = await async_load_json(DATA_PATH, default={'channels': {}, 'daily': ''})
        guild_cfg = cfg.get('channels', {}).get(str(ctx.guild.id))
            
        embed = discord.Embed(title='Announcement Settings', color=discord.Color.blue())
        
        # Add scheduled announcement details if set
        if guild_cfg:
            embed.add_field(
                name='Scheduled Announcement',
                value='**Interval:** {interval_minutes} minutes\n**Message:** {message}\n**Channel:** <#{channel_id}>'.format(
                    interval_minutes=guild_cfg.get('interval_minutes', 'Not set'),
                    message=guild_cfg.get('message', 'Not set'),
                    channel_id=guild_cfg.get('channel_id', 'Not set')
                ),
                inline=False
            )

        # Add daily message if set
        if cfg.get('daily'):
            embed.add_field(
                name='Daily Message',
                value=cfg['daily'],
                inline=False
            )

        # List available announcement files
        files = []
        try:
            for file in ANNOUNCEMENTS_DIR.glob('*.txt'):
                files.append(f'📄 {file.stem}')
        except Exception as e:
            print(f"Error listing announcement files: {e}")
            
        if files:
            embed.add_field(
                name='📂 Available Announcements',
                value='\n'.join(files),
                inline=False
            )
        else:
            embed.add_field(
                name='📂 Available Announcements',
                value='No announcement files found.',
                inline=False
            )
            
        embed.set_footer(text='Use /announce file to send a file-based announcement')
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    cog = Announcements(bot)
    await cog.cog_load()
    await bot.add_cog(cog)
