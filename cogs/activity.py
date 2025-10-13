"""Activity tracking cog

Features:
- Track per-guild per-user message counts and voice seconds aggregated by week.
- Admin `/activity setup` to configure role, channels to monitor (comma-separated ids), reset weekday (0=Mon), reset hour (0-23).
- Weekly processor task that computes top 5 active users and assigns the configured role, removing it from users who dropped out.
- `/activity report` to manually trigger a report and /activity config to view current config.

Notes:
- Requires `manage_roles` and `manage_nicknames` permissions for role/nick changes.
- Uses `utils.db.DB` helpers added earlier.
"""
from discord.ext import commands, tasks
from discord import app_commands
import discord
from utils.db import DB
import asyncio
import time
import datetime
import json
from typing import Optional, List

WEEK_SECONDS = 7 * 24 * 60 * 60


def week_start_for_ts(ts: int) -> int:
    # start of ISO week (Monday) in unix seconds
    dt = datetime.datetime.utcfromtimestamp(ts)
    # find Monday
    start = dt - datetime.timedelta(days=dt.weekday())
    start = datetime.datetime(start.year, start.month, start.day)
    return int(start.replace(tzinfo=datetime.timezone.utc).timestamp())


class Activity(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._voice_times = {}  # (guild_id, user_id) -> join_timestamp
        self.weekly_task.start()

    async def cog_unload(self):
        self.weekly_task.cancel()

    # ----------------- Tracking listeners -----------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        guild_id = message.guild.id
        user_id = message.author.id
        ws = week_start_for_ts(int(time.time()))
        try:
            await DB.add_weekly_message(guild_id, user_id, ws, 1)
        except Exception as e:
            print(f"Error adding weekly message for {user_id} in {guild_id}: {e}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        # Track join/leave to measure total voice seconds
        try:
            guild_id = member.guild.id
            user_id = member.id
            key = (guild_id, user_id)
            now_ts = int(time.time())
            if before.channel is None and after.channel is not None:
                # joined
                self._voice_times[key] = now_ts
            elif before.channel is not None and after.channel is None:
                # left
                join_ts = self._voice_times.pop(key, None)
                if join_ts:
                    secs = now_ts - join_ts
                    ws = week_start_for_ts(join_ts)
                    await DB.add_weekly_voice_seconds(guild_id, user_id, ws, secs)
            else:
                # moved channels or mute/unmute don't change tracking for now
                pass
        except Exception as e:
            print(f"Voice tracking error: {e}")

    # ----------------- Admin configuration commands -----------------
    @commands.hybrid_group(name='activity', description='Activity tracking commands')
    @commands.has_permissions(administrator=True)
    async def activity(self, ctx):
        if isinstance(ctx, discord.Interaction):
            await ctx.response.defer(ephemeral=True)
        # group root
        if not isinstance(ctx, discord.Interaction):
            await ctx.send('Use subcommands: setup, config, report')

    @activity.command(name='setup')
    @app_commands.describe(role='Role to assign to top active members', channels='Comma-separated channel IDs to monitor (optional)', reset_weekday='Weekday to reset/compute (0=Monday)', reset_hour='Hour of day (0-23) to compute and reset')
    async def activity_setup(self, ctx, role: discord.Role, channels: Optional[str] = None, reset_weekday: int = 0, reset_hour: int = 0):
        """Configure activity role and channels"""
        guild_id = ctx.guild.id
        role_id = role.id
        # store channel ids as JSON list
        channel_ids = None
        if channels:
            try:
                ids = [int(x.strip()) for x in channels.split(',') if x.strip()]
                channel_ids = json.dumps(ids)
            except Exception:
                await ctx.send('Failed to parse channel IDs. Provide comma-separated numeric IDs.')
                return
        try:
            await DB.set_activity_config(guild_id, role_id, channel_ids, int(reset_weekday) % 7, int(reset_hour) % 24)
            await ctx.send('Activity configuration saved.')
        except Exception as e:
            await ctx.send(f'Failed to save config: {e}')

    @activity.command(name='config')
    async def activity_config(self, ctx):
        cfg = await DB.get_activity_config(ctx.guild.id)
        if not cfg:
            await ctx.send('No activity configuration found. Use /activity setup to configure.')
            return
        msg = f"Role ID: {cfg.get('role_id')}\nChannels: {cfg.get('channel_ids')}\nReset weekday: {cfg.get('reset_weekday')}\nReset hour: {cfg.get('reset_hour')}\nLast processed week: {cfg.get('last_processed_week')}"
        await ctx.send(msg)

    @activity.command(name='report')
    async def activity_report(self, ctx, weeks_ago: int = 0):
        """Show top active users for this week or previous weeks"""
        now = int(time.time())
        ws = week_start_for_ts(now - weeks_ago * WEEK_SECONDS)
        rows = await DB.get_weekly_activity(ctx.guild.id, ws, limit=20)
        if not rows:
            await ctx.send('No activity recorded for that week yet.')
            return
        lines = []
        for uid, msgs, secs, score in rows:
            try:
                member = ctx.guild.get_member(uid) or await self.bot.fetch_user(uid)
                name = getattr(member, 'display_name', str(uid))
            except Exception:
                name = str(uid)
            lines.append(f"{name}: {int(msgs)} messages, {int(secs)}s voice (score {score:.1f})")
        await ctx.send('\n'.join(lines[:20]))

    # ----------------- Weekly processor -----------------
    @tasks.loop(minutes=30)
    async def weekly_task(self):
        # check all guild configs and process if reset time passed
        try:
            configs = await DB.get_all_activity_configs()
            now = datetime.datetime.utcnow()
            now_ts = int(now.timestamp())
            for cfg in configs:
                try:
                    guild_id = int(cfg['guild_id'])
                    role_id = cfg.get('role_id')
                    channel_ids = cfg.get('channel_ids')
                    reset_weekday = int(cfg.get('reset_weekday') or 0)
                    reset_hour = int(cfg.get('reset_hour') or 0)
                    last_processed = cfg.get('last_processed_week')

                    # compute this week's start and compare with last_processed
                    # determine the week_start for the most recent reset boundary
                    # find most recent datetime that matches reset_weekday/reset_hour <= now
                    today = now.date()
                    # build a date at reset_hour UTC for the current week's reset_weekday
                    # find the date of this week's reset day
                    delta_days = (now.weekday() - reset_weekday) % 7
                    reset_date = now - datetime.timedelta(days=delta_days)
                    reset_dt = datetime.datetime(reset_date.year, reset_date.month, reset_date.day, reset_hour, tzinfo=datetime.timezone.utc)
                    reset_ts = int(reset_dt.timestamp())
                    # If now is before today's reset time, move reset to previous week
                    if now_ts < reset_ts:
                        reset_dt = reset_dt - datetime.timedelta(weeks=1)
                        reset_ts = int(reset_dt.timestamp())
                    ws = week_start_for_ts(reset_ts)

                    if last_processed and int(last_processed) >= ws:
                        continue  # already processed

                    # compute top users for ws
                    top = await DB.get_weekly_activity(guild_id, ws, limit=20)
                    # take top 5
                    top5 = [t[0] for t in top[:5]]

                    guild = self.bot.get_guild(guild_id)
                    if not guild:
                        continue
                    role = guild.get_role(role_id) if role_id else None

                    # assign role to top5 and remove from others who have role but not in top5
                    if role:
                        # build current role members
                        current_members = [m.id for m in role.members]
                        to_add = [uid for uid in top5 if uid not in current_members]
                        to_remove = [mid for mid in current_members if mid not in top5]
                        for uid in to_add:
                            try:
                                member = guild.get_member(uid)
                                if member:
                                    await member.add_roles(role, reason='Weekly active role assignment')
                            except Exception as e:
                                print(f"Failed to add role to {uid} in guild {guild_id}: {e}")
                        for uid in to_remove:
                            try:
                                member = guild.get_member(uid)
                                if member:
                                    await member.remove_roles(role, reason='Weekly active role removal')
                            except Exception as e:
                                print(f"Failed to remove role from {uid} in guild {guild_id}: {e}")

                    # send a short announcement in the first configured channel if provided
                    if channel_ids:
                        try:
                            ids = json.loads(channel_ids)
                            if ids:
                                ch = guild.get_channel(ids[0])
                                if ch and ch.permissions_for(guild.me).send_messages:
                                    text = '**Weekly Top Active Members**\n'
                                    for pos, uid in enumerate(top5, start=1):
                                        member = guild.get_member(uid)
                                        name = member.display_name if member else str(uid)
                                        text += f"{pos}. {name}\n"
                                    await ch.send(text)
                        except Exception as e:
                            print(f"Failed to announce weekly active for guild {guild_id}: {e}")

                    # update last_processed_week
                    await DB.update_last_processed_week(guild_id, ws)

                except Exception as e:
                    print(f"Error processing activity config: {e}")
        except Exception as e:
            print(f"Error in weekly_task: {e}")

    @weekly_task.before_loop
    async def before_weekly(self):
        await self.bot.wait_until_ready()

    # provide a manual start for the task
    @commands.hybrid_command(name='activity_run', description='Manually trigger weekly activity processing (Admin only)')
    @commands.has_permissions(administrator=True)
    async def activity_run(self, ctx):
        await ctx.send('Triggering weekly activity processing...')
        await self.weekly_task()


async def setup(bot: commands.Bot):
    cog = Activity(bot)
    await bot.add_cog(cog)
