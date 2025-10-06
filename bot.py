"""studybot - Main bot runner

This file loads environment variables, sets up the Bot with intents,
loads cogs, and runs the bot. Designed for discord.py v2+.
"""
import asyncio
import sys
import os
import time
import datetime
from pathlib import Path
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord import app_commands
from utils.chat_logger import ChatLogger
from utils.mod_logger import ModLogger


BASE_DIR = Path(__file__).parent


def get_prefix(bot, message):
    load_dotenv(BASE_DIR / '.env')
    # Default to ! if no prefix set in .env
    return os.getenv('PREFIX', '!')


intents = discord.Intents.all()


class StudyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=get_prefix,
            intents=intents,
            case_insensitive=True,
            help_command=None
        )
        self.start_time = None
        self.bg_task = None
        self.chat_logger = ChatLogger()
        self.mod_logger = ModLogger()

    async def setup_hook(self):
        # Called after the bot is logged in but before connect finishes; good for setup
        await load_cogs()
        try:
            print('Syncing application (slash) commands...')
            # This will sync all loaded slash/hybrid commands to Discord
            synced = await self.tree.sync()
            print(f'Slash commands synced: {len(synced)} commands')
            
            # Force sync for each guild to ensure all commands are available
            for guild in self.guilds:
                try:
                    await self.tree.sync(guild=guild)
                except Exception as e:
                    print(f'Error syncing commands for guild {guild.id}: {e}')
            
            print('Guild-specific command sync complete.')
        except Exception as e:
            print(f'Error in setup: {e}')
            
    async def on_message(self, message):
        # Log all messages
        if not message.author.bot:
            # Log user message
            self.chat_logger.log_message(
                message.author.name,
                message.content,
                message.channel,
                message.guild
            )
        elif message.author == self.user:
            # Log bot's own messages
            self.chat_logger.log_message(
                self.user.name,
                message.content,
                message.channel,
                message.guild,
                is_bot=True
            )
        
        await super().on_message(message)
        
    async def on_member_ban(self, guild, user):
        # Log member bans
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            self.mod_logger.log_action(
                entry.user.name,
                "ban",
                user.name,
                entry.reason
            )
            
    async def on_member_kick(self, guild, user):
        # Log member kicks
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
            self.mod_logger.log_action(
                entry.user.name,
                "kick",
                user.name,
                entry.reason
            )
            
    async def on_member_timeout(self, guild, user):
        # Log member timeouts
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
                if entry.target == user and entry.changes.timeout:
                    self.mod_logger.log_action(
                        entry.user.name,
                        "timeout",
                        user.name,
                        entry.reason
                    )
        except Exception as e:
            print(f'Error logging timeout: {e}')
        if not self.bg_task:
            self.bg_task = self.loop.create_task(self.status_update_task())

    async def on_ready(self):
        print(f'\n{self.user} is ready!')
        print(f'Using prefix: !')
        print('--------------------')
        self.start_time = time.time()  # Set the start time when bot becomes ready
        # Always start the status update task when the bot is ready
        if not self.bg_task:
            self.bg_task = self.loop.create_task(self.status_update_task())

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param.name}")
        else:
            print(f'Error in command {getattr(ctx, "command", None)}: {error}')
            try:
                await ctx.send(f'Error executing command: {error}')
            except Exception:
                pass

    async def on_command(self, ctx):
        print(f'Command executed: {ctx.command} by {ctx.author} in {ctx.guild}')
        await self.chat_logger.log_command(ctx)

    @commands.hybrid_command(name='sync', description='Sync slash commands (Admin only)')
    @commands.has_permissions(administrator=True)
    async def sync_commands(self, ctx):
        """Sync all slash commands to Discord"""
        try:
            print('Syncing application (slash) commands...')
            synced = await self.tree.sync()
            await ctx.send(f'Successfully synced {len(synced)} commands!')
            print('Slash commands synced.')
        except Exception as e:
            print('Failed to sync app commands:', e)
            await ctx.send(f'Failed to sync commands: {str(e)}')

    async def status_update_task(self):
        await self.wait_until_ready()
        # Timers:
        # - ping_refresh every 7s (updates ping/uptime text)
        # - swap activities every 3s (changes presence between ping and credit)
        # - terminal log every 15s
        ping_activity = discord.Game(name="Ping: 0ms | Uptime: 0:00:00")
        credit_activity = discord.Game(name="Made With 🩷 Deep | deepdeyiitk.com")

        last_ping_refresh = time.monotonic() - 7
        last_terminal_log = time.monotonic() - 15
        show_ping = True

        while not self.is_closed():
            try:
                now = time.monotonic()

                # Refresh ping/uptime every 7 seconds
                if now - last_ping_refresh >= 7:
                    latency = round(self.latency * 1000) if self.latency is not None else 0
                    uptime_secs = int(time.time() - (self.start_time or time.time()))
                    uptime = str(datetime.timedelta(seconds=uptime_secs))
                    ping_activity = discord.Game(name=f"Ping: {latency}ms | Uptime: {uptime}")
                    last_ping_refresh = now

                # Set presence depending on toggle
                if show_ping:
                    await self.change_presence(activity=ping_activity)
                else:
                    await self.change_presence(activity=credit_activity)

                # Terminal logging every 15 seconds (log same status)
                if now - last_terminal_log >= 15:
                    # use the current ping_activity name for logging
                    try:
                        log_text = ping_activity.name
                    except Exception:
                        log_text = "Ping: N/A | Uptime: N/A | Made With 🩷 Deep | deepdeyiitk.com"
                    print(f"[STATUS LOG] {log_text}")
                    last_terminal_log = now

                # flip the activity and wait 3 seconds before next swap
                show_ping = not show_ping
                await asyncio.sleep(3)

            except Exception as e:
                print(f"Error in status update task: {e}")
                await asyncio.sleep(3)


bot = StudyBot()

# Optional: configure logging channel id via env
LOG_CHANNEL_ID = None


@bot.event
async def on_connect():
    # Called when the connection to Discord is made
    bot.start_time = time.time()
    print(f"Bot connected to Discord at {datetime.datetime.now()}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        print(f"[BOT] {message.author}: {message.content}")
        bot.chat_logger.log_message(message.author, message.content, message.channel, message.guild, "BOT")
    else:
        print(f"[USER] {message.author}: {message.content}")
        bot.chat_logger.log_message(message.author, message.content, message.channel, message.guild, "USER")
    await bot.process_commands(message)

@bot.event
async def on_command(ctx):
    print(f"[COMMAND] {ctx.author} used {ctx.command} in {ctx.channel}")
    bot.chat_logger.log_command(ctx, ctx.command.name)

@bot.event
async def on_command_completion(ctx):
    print(f"[COMMAND COMPLETED] {ctx.command} by {ctx.author}")
    bot.chat_logger.log_message(ctx.author, f"Completed command: {ctx.command}", ctx.channel, ctx.guild, "COMMAND_COMPLETE")

@bot.event
async def on_command_error(ctx, error):
    print(f"[ERROR] {ctx.command}: {str(error)}")
    bot.chat_logger.log_error(error, f"Command: {ctx.command} by {ctx.author} in {ctx.channel}")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    # set a friendly presence
    try:
        await bot.change_presence(activity=discord.Game(name="Deep Dey - The FUTURE IITIAN 🎯"))
    except Exception:
        pass
    # record launch time
    if not hasattr(bot, 'launch_time'):
        import datetime
        bot.launch_time = datetime.datetime.utcnow()
    print("Bot is ready.")


@bot.event
async def on_command_error(ctx, error):
    # Generic error handler for commands
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.CheckFailure):
        await ctx.send("You don't have permission to use that command.")
        return
    await ctx.send(f'Error: {error}')
    raise error


async def load_cogs():
    # Load all cogs in the cogs package
    for file in (BASE_DIR / 'cogs').glob('*.py'):
        if file.name.startswith('_'):
            continue
        ext = f"cogs.{file.stem}"
        try:
            await bot.load_extension(ext)
            print(f"Loaded extension {ext}")
        except Exception as e:
            print(f"Failed to load extension {ext}: {e}")


async def main():
    load_dotenv(BASE_DIR / '.env')
    token = os.getenv('DISCORD_TOKEN')

    if not token:
        print('\nERROR: DISCORD_TOKEN not found in environment.\nPlease create a .env file in the project root with:')
        print('DISCORD_TOKEN=your_bot_token_here')
        print('PREFIX=!')
        print("You can also set the environment variables directly.")
        return 1

    print(f"Starting bot with prefix '!' and syncing commands...")
    try:
        # Use `async with bot` to ensure the bot is closed properly on exit
        async with bot:
            await bot.start(token)
    except Exception as e:
        print(f"Error starting bot: {e}")
        return 1


if __name__ == '__main__':
    try:
        ret = asyncio.run(main())
        if isinstance(ret, int) and ret != 0:
            sys.exit(ret)
    except KeyboardInterrupt:
        print('Shutting down...')
    except Exception as e:
        print('Unhandled exception during startup:', e)
        raise
