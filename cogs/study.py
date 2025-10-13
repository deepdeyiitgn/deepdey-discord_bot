"""
Study cog: /log and /logs view commands to record study sessions and view history.

Features:
- Log study sessions
- View study logs
- Track streaks and progress
"""
import discord
from discord.ext import commands
from discord import app_commands
import time
from datetime import datetime, date
from utils import db


class Study(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name='log')
    async def log(self, ctx, *, args: str = ''):
        """Log a study session: !log subject:math time:120 topic:integration"""
        # parse simple key:value pairs from args
        parts = { }
        for token in args.split():
            if ':' in token:
                k, v = token.split(':', 1)
                parts[k.lower()] = v
        subject = parts.get('subject', '')
        time_str = parts.get('time', '')
        topic = parts.get('topic', '')
        minutes = 0
        try:
            if time_str.endswith('h'):
                minutes = int(float(time_str[:-1]) * 60)
            elif time_str.endswith('m'):
                minutes = int(float(time_str[:-1]))
            else:
                minutes = int(float(time_str))
        except Exception:
            await ctx.send('Could not parse time. Use `time:30` or `time:1.5h` or `time:30m`.')
            return

        # Log the study session
        ts = int(time.time())
        await db.DB.add_study_log(ctx.author.id, minutes, ts, topic)

        # Update streak
        today = date.today().isoformat()
        streak = await db.DB.get_streak(ctx.author.id)
        if not streak:
            # First time studying
            await db.DB.set_streak(ctx.author.id, 1, today)
            streak_msg = "🎉 First day of your study streak!"
        else:
            last_date = datetime.fromisoformat(streak['last_date']).date()
            if last_date < date.today():
                # Studying on a new day
                if (date.today() - last_date).days == 1:
                    # Consecutive day
                    await db.DB.set_streak(ctx.author.id, streak['count'] + 1, today)
                    streak_msg = f"🔥 {streak['count'] + 1} day streak!"
                else:
                    # Streak broken
                    await db.DB.set_streak(ctx.author.id, 1, today)
                    streak_msg = "Starting a new streak today! 💪"
            else:
                streak_msg = f"Current streak: {streak['count']} days 🔥"
"""
Study cog: log and logs commands, simple focus session, streaks and leaderboard helpers.
This is a cleaned, single-version implementation to avoid duplicated code and unterminated strings.
"""
import time
import asyncio
import datetime
import json
from typing import Optional, Dict, Any
from pathlib import Path

import discord
from discord.ext import commands
from discord import app_commands

from utils.db import DB


def _now_ts() -> int:
    return int(datetime.datetime.utcnow().timestamp())


class Study(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_focus: Dict[int, Dict[str, Any]] = {}

    @commands.hybrid_command(name='log')
    async def log(self, ctx, *, args: str = ''):
        """Log a study session: !log subject:math time:120 topic:integration"""
        parts = {}
        for token in args.split():
            if ':' in token:
                k, v = token.split(':', 1)
                parts[k.lower()] = v
        subject = parts.get('subject', '')
        time_str = parts.get('time', '')
        topic = parts.get('topic', '')
        minutes = 0
        try:
            if time_str.endswith('h'):
                minutes = int(float(time_str[:-1]) * 60)
            elif time_str.endswith('m'):
                minutes = int(float(time_str[:-1]))
            else:
                minutes = int(float(time_str))
        except Exception:
            await ctx.send('Could not parse time. Use `time:30` or `time:1.5h` or `time:30m`.')
            return

        ts = _now_ts()
        await DB.add_study_log(ctx.author.id, minutes, ts, topic)
        # update streak/leaderboard (best-effort)
        try:
            guild_id = ctx.guild.id if ctx.guild else None
            if guild_id:
                await DB.increment_leaderboard(guild_id, ctx.author.id, minutes)
        except Exception:
            pass

        await ctx.send(f'Logged {minutes} minutes for {subject or "(no subject)"} — topic: {topic}')

    @commands.hybrid_command(name='logs')
    async def logs(self, ctx, action: str = None):
        """View logs: !logs view"""
        if action == 'view':
            rows = await DB.get_user_logs(ctx.author.id)
            if not rows:
                await ctx.send('No study logs found.')
                return
            lines = []
            total = 0
            for r in rows[:10]:
                ts = int(r['ts'])
                minutes = int(r['minutes'])
                topic = r.get('topic') or ''
                total += minutes
                lines.append(f'- {minutes} min — {topic} — <t:{ts}:f>')
            lines.append(f'**Total minutes:** {total}')
            await ctx.send('\n'.join(lines))
            return
        await ctx.send('Usage: logs view')


async def setup(bot: commands.Bot):
    await DB.init_db()
    await bot.add_cog(Study(bot))

    async def _update_streak(self, user_id: int):
        # simple streak: if user logged something today, increment if yesterday logged
        today = datetime.date.today()
        val = await DB.get_streak(user_id)
        if val:
            try:
                count = int(val.get('count', 0))
                last_date = val.get('last_date', '')
            except Exception:
                count = 0
                last_date = ''
        else:
            count = 0
            last_date = ''

        if last_date == today.isoformat():
            return
        yesterday = (today - datetime.timedelta(days=1)).isoformat()
        if last_date == yesterday:
            count = count + 1
        else:
            count = 1
        last_date = today.isoformat()
        await DB.set_streak(user_id, count, last_date)

    # ------------------ Log command ------------------
    @commands.hybrid_command(name='log', description='Log study hours or minutes')
    @app_commands.describe(subject='Subject name', time='Time in minutes or like 2h', topic='Optional topic')
    async def log(self, ctx: commands.Context, subject: str, time: str, topic: Optional[str] = None):
        # parse time (support 2h or 30m or minutes int)
        minutes = 0
        t = time.lower()
        try:
            if t.endswith('h'):
                minutes = int(float(t[:-1]) * 60)
            elif t.endswith('m'):
                minutes = int(float(t[:-1]))
            else:
                minutes = int(float(t))
        except Exception:
            await ctx.send('Could not parse time. Use formats like 2h, 30m, or minutes (e.g., 45).')
            return

        await self._add_log(ctx.author.id, minutes, topic or subject)
        await ctx.send(f'✅ Logged {minutes} minutes for {subject}.')

    # ------------------ Streak ------------------
    @commands.hybrid_command(name='streak', description='Show your study streak')
    async def streak(self, ctx: commands.Context):
        key = self._streak_key(ctx.author.id)
        val = await DB.get_kv(key)
        if not val:
            await ctx.send('No streak yet. Start logging your study to build a streak!')
            return
        try:
            obj = json.loads(val)
        except Exception:
            await ctx.send('No streak data found.')
            return
        await ctx.send(f"🔥 Your current streak: {obj.get('count',0)} days")

    # ------------------ Leaderboard ------------------
    @commands.hybrid_command(name='leaderboard', description='Show top study users this week')
    async def leaderboard(self, ctx: commands.Context):
        # collect study logs for last 7 days for this guild (best-effort: scan data folder keys)
        guild_id = ctx.guild.id if ctx.guild else 0
        # Simple approach: iterate users found in data files by reading DB keys is not supported,
        # so maintain a guild leaderboard key with entries {user_id: total_minutes}
        rows = await DB.get_leaderboard(guild_id, limit=10)
        if not rows:
            await ctx.send('No leaderboard data yet.')
            return
        lines = []
        for row in rows:
            try:
                uid = int(row['user_id']) if 'user_id' in row.keys() else int(row[0])
                mins = int(row['minutes']) if 'minutes' in row.keys() else int(row[1])
            except Exception:
                continue
            try:
                member = await self._fetch_member(ctx.guild, uid) if ctx.guild else None
                name = member.display_name if member else str(uid)
            except Exception:
                name = str(uid)
            lines.append(f"{name}: {mins}m")
        await ctx.send('\n'.join(lines) if lines else 'No entries yet.')

    async def _fetch_member(self, guild: discord.Guild, user_id: int) -> Optional[discord.Member]:
        try:
            return guild.get_member(user_id) or await guild.fetch_member(user_id)
        except Exception:
            return None

    # ------------------ Doubt Collector ------------------
    @commands.hybrid_command(name='doubt', description='Submit a doubt for mentors/mods to review')
    @app_commands.describe(question='Your doubt/question text')
    async def doubt(self, ctx: commands.Context, *, question: str):
        guild_id = ctx.guild.id if ctx.guild else 0
        await DB.add_doubt(guild_id=guild_id, user_id=ctx.author.id, question=question, ts=_now_ts())
        await ctx.send('✉️ Doubt submitted! Mentors and mods will review it soon.')

    # ------------------ Reminders ------------------
    @commands.hybrid_command(name='remind', description='Schedule a reminder (HH:MM or relative, e.g., 10m)')
    @app_commands.describe(time='Time like 18:00 or relative like 10m', message='Reminder message')
    async def remind(self, ctx: commands.Context, time: str, *, message: str):
        user_id = ctx.author.id
        guild_id = ctx.guild.id if ctx.guild else None
        channel_id = ctx.channel.id if ctx.guild else None

        # parse time
        remind_ts = None
        t = time.strip().lower()
        try:
            if t.endswith('m'):
                mins = int(t[:-1])
                remind_ts = _now_ts() + mins * 60
            elif ':' in t:
                parts = t.split(':')
                h = int(parts[0])
                m = int(parts[1])
                now = datetime.datetime.utcnow()
                target = datetime.datetime(now.year, now.month, now.day, h, m)
                if target.timestamp() <= now.timestamp():
                    # schedule next day
                    target = target + datetime.timedelta(days=1)
                remind_ts = int(target.timestamp())
            else:
                # try minutes as integer
                mins = int(t)
                remind_ts = _now_ts() + mins * 60
        except Exception:
            await ctx.send('Could not parse time. Use HH:MM or 10m or minutes integer.')
            return

        await DB.add_reminder(user_id=user_id, guild_id=guild_id, channel_id=channel_id, message=message, remind_at=remind_ts)
        await ctx.send(f'✅ Reminder scheduled for <t:{remind_ts}:f>')

    # ------------------ Motivate (uses Gemini when available) ------------------
    @commands.hybrid_command(name='motivate', description='Get an AI motivational reply (uses Gemini if configured)')
    @app_commands.describe(prompt='Optional context about how you feel')
    async def motivate(self, ctx: commands.Context, *, prompt: Optional[str] = None):
        text = (prompt or '').strip() or f"Motivate me to study, I'm {ctx.author.display_name}."
        # Attempt to use gemini cog if loaded
        gemini = None
        for cog_name, cog in self.bot.cogs.items():
            if cog_name.lower().startswith('gemini'):
                gemini = cog
                break

        reply = None
        if gemini and hasattr(gemini, 'explain_questions'):
            try:
                reply = await gemini.explain_questions(text)
            except Exception as e:
                print(f'[STUDY] Gemini call failed: {e}')

        if not reply:
            # Fallback simple motivational message
            reply = f"Keep going {ctx.author.display_name}! Even 5 minutes counts. Set small goals and celebrate progress. 💪"

        await ctx.send(reply)

    # ------------------ Background checker ------------------
    async def _focus_checker(self):
        try:
            while True:
                now = _now_ts()
                to_notify = []
                for uid, sess in list(self.active_focus.items()):
                    if sess.get('ends_at', 0) <= now:
                        to_notify.append((uid, sess))
                for uid, sess in to_notify:
                    try:
                        # notify in channel
                        gid = sess.get('guild_id')
                        ch_id = sess.get('channel_id')
                        channel = None
                        if gid and ch_id:
                            guild = self.bot.get_guild(gid)
                            if guild:
                                channel = guild.get_channel(ch_id) or await self.bot.fetch_channel(ch_id)
                        if channel:
                            await channel.send(f'<@{uid}> 🛎️ Focus session complete! Great job.')
                        user = await self.bot.fetch_user(uid)
                        try:
                            await user.send('✅ Your focus session has ended. Well done!')
                        except Exception:
                            pass
                        # credit to logs
                        await self._add_log(uid, sess.get('duration', 25), 'focus')
                    except Exception as e:
                        print(f'[STUDY] Error notifying user {uid}: {e}')
                    # cleanup
                    try:
                        self.active_focus.pop(uid, None)
                    except Exception:
                        pass
                    setattr(self.bot, 'active_focus_sessions', self.active_focus)

                await asyncio.sleep(5)
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f'[STUDY] focus checker crashed: {e}')

    async def _reminder_dispatcher(self):
        try:
            while True:
                now = _now_ts()
                rows = await DB.get_pending_reminders(now)
                for r in rows:
                    try:
                        # send to user or channel
                        if r.get('channel_id') and r.get('guild_id'):
                            try:
                                ch = await self.bot.fetch_channel(int(r['channel_id']))
                                await ch.send(f"⏰ Reminder: {r['message']}")
                            except Exception:
                                pass
                        else:
                            try:
                                user = await self.bot.fetch_user(int(r['user_id']))
                                await user.send(f"⏰ Reminder: {r['message']}")
                            except Exception:
                                pass
                        await DB.mark_reminder_sent(int(r['id']))
                    except Exception as e:
                        print(f'[STUDY] Reminder dispatch error: {e}')
                await asyncio.sleep(10)
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f'[STUDY] reminders dispatcher crashed: {e}')

    # ------------------ Study Partner Mode ------------------
    @commands.hybrid_command(name='partner', description='Start or stop Study Partner mode in a channel')
    @app_commands.describe(action='start or stop', duration='duration in minutes (start only)')
    async def partner(self, ctx: commands.Context, action: str, duration: Optional[int] = 25):
        action = (action or '').lower()
        channel_id = ctx.channel.id
        user_id = ctx.author.id

        if action == 'start':
            ends_at = _now_ts() + int(duration) * 60
            interval = 5  # send partner pings every 5 minutes
            self.active_partners[channel_id] = {
                'owner': user_id,
                'ends_at': ends_at,
                'interval_mins': interval,
                'next_ping_ts': _now_ts() + interval * 60
            }
            setattr(self.bot, 'active_partner_sessions', self.active_partners)
            await ctx.send(f'🤝 Study Partner started for {duration} minutes. I will check in every {interval} minutes.')
        elif action == 'stop':
            sess = self.active_partners.pop(channel_id, None)
            setattr(self.bot, 'active_partner_sessions', self.active_partners)
            if sess:
                # credit approximate minutes to owner's log
                elapsed = max(1, int((min(_now_ts(), sess.get('ends_at', 0)) - (_now_ts() - sess.get('interval_mins',5)*60)) // 60))
                try:
                    await DB.add_study_log(user_id=sess.get('owner'), minutes=elapsed, ts=_now_ts(), topic='partner', guild_id=ctx.guild.id if ctx.guild else None)
                    if ctx.guild and ctx.guild.id:
                        await DB.increment_leaderboard(ctx.guild.id, sess.get('owner'), elapsed)
                except Exception:
                    pass
                await ctx.send('🛑 Study Partner stopped. Good job!')
            else:
                await ctx.send('No Study Partner session active in this channel.')
        else:
            await ctx.send('Usage: /partner start [duration_minutes] OR /partner stop')

    async def _partner_checker(self):
        try:
            while True:
                now = _now_ts()
                to_end = []
                for ch_id, sess in list(self.active_partners.items()):
                    # check for pings
                    if sess.get('next_ping_ts', 0) <= now and now < sess.get('ends_at', 0):
                        try:
                            ch = self.bot.get_channel(ch_id) or await self.bot.fetch_channel(ch_id)
                            if ch:
                                await ch.send(f"📣 Study Partner check-in: keep focus! {sess.get('owner')} — {int((sess.get('ends_at')-now)/60)}m left")
                        except Exception:
                            pass
                        # schedule next ping
                        sess['next_ping_ts'] = now + sess.get('interval_mins', 5) * 60
                    # check for session end
                    if sess.get('ends_at', 0) <= now:
                        to_end.append((ch_id, sess))

                for ch_id, sess in to_end:
                    try:
                        ch = self.bot.get_channel(ch_id) or await self.bot.fetch_channel(ch_id)
                        if ch:
                            await ch.send(f"✅ Study Partner session ended. Great work everyone!")
                        # credit owner's minutes (duration)
                        duration_mins = max(1, int((sess.get('ends_at') - (_now_ts() - sess.get('interval_mins',5)*60)) // 60))
                        try:
                            await DB.add_study_log(user_id=sess.get('owner'), minutes=duration_mins, ts=_now_ts(), topic='partner', guild_id=ch.guild.id if ch and ch.guild else None)
                            if ch and ch.guild:
                                await DB.increment_leaderboard(ch.guild.id, sess.get('owner'), duration_mins)
                        except Exception:
                            pass
                    except Exception:
                        pass
                    # remove
                    try:
                        self.active_partners.pop(ch_id, None)
                    except Exception:
                        pass
                    setattr(self.bot, 'active_partner_sessions', self.active_partners)

                await asyncio.sleep(10)
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f'[STUDY] partner checker crashed: {e}')

        # ------------------ Smart Quotes / MOTD ------------------
        async def _daily_quote_task(self):
            # Runs every minute; at configured hour sends a quote once per guild per day
            import os
            quote_hour = int(os.getenv('QUOTE_HOUR', '6'))
            quotes_path = Path(__file__).parent.parent / 'data' / 'quotes.json'
            quotes = []
            try:
                if quotes_path.exists():
                    with open(quotes_path, 'r', encoding='utf-8') as f:
                        quotes = json.load(f)
            except Exception:
                quotes = []

            try:
                while True:
                    now = datetime.datetime.utcnow()
                    if now.hour == quote_hour and now.minute == 0:
                        today = now.date().isoformat()
                        for guild in list(self.bot.guilds):
                            try:
                                key = f'last_quote_{guild.id}'
                                last = await DB.get_kv(key)
                                if last == today:
                                    continue
                                # pick a quote
                                q = None
                                if quotes:
                                    import random
                                    q = random.choice(quotes)
                                    text = q.get('text') if isinstance(q, dict) else str(q)
                                else:
                                    text = "Keep going — consistency beats talent. 🔥"

                                # find a suitable channel: announcements or first text channel
                                channel = None
                                for ch in guild.text_channels:
                                    if ch.name.lower().startswith('announce') or ch.name.lower().startswith('general'):
                                        channel = ch
                                        break
                                if not channel and guild.text_channels:
                                    channel = guild.text_channels[0]
                                if channel and channel.permissions_for(guild.me).send_messages:
                                    try:
                                        await channel.send(f"📢 Quote of the day: {text}")
                                    except Exception:
                                        pass
                                await DB.set_kv(key, today)
                            except Exception:
                                pass
                        # sleep 61 seconds to avoid double-send within the same minute
                        await asyncio.sleep(61)
                    await asyncio.sleep(20)
            except asyncio.CancelledError:
                return
            except Exception as e:
                print(f'[STUDY] daily quote task crashed: {e}')

        # ------------------ Focus Room (text-guard) ------------------
        @commands.hybrid_command(name='focusroom', description='Start or stop a Focus Room in this channel (text-guard or voice-guard)')
        @app_commands.describe(action='start or stop', duration='duration in minutes (start only)', mode='text or voice')
        async def focusroom(self, ctx: commands.Context, action: str, duration: Optional[int] = 25, mode: Optional[str] = 'text'):
            action = (action or '').lower()
            ch_id = ctx.channel.id
            user_id = ctx.author.id
            mode = (mode or 'text').lower()

            if action == 'start':
                ends_at = _now_ts() + int(duration) * 60
                self.active_focusrooms = getattr(self, 'active_focusrooms', {})
                self.active_focusrooms[ch_id] = {'owner': user_id, 'ends_at': ends_at, 'mode': mode}
                setattr(self.bot, 'active_focusrooms', self.active_focusrooms)
                if mode == 'voice':
                    # attempt to server-mute all members in the caller's voice channel
                    if not ctx.author.voice or not ctx.author.voice.channel:
                        await ctx.send('You are not in a voice channel. Join a voice channel to start voice Focus Room.')
                        return
                    voice_ch = ctx.author.voice.channel
                    muted = []
                    if not ctx.guild.me.guild_permissions.mute_members:
                        await ctx.send('Bot lacks permission to mute members. Please grant Mute Members permission.')
                        return
                    for m in voice_ch.members:
                        try:
                            # skip bots
                            if m.bot:
                                continue
                            await m.edit(mute=True)
                            muted.append(m.id)
                        except Exception:
                            pass
                    # track who we muted
                    self.active_voice_focusrooms = getattr(self, 'active_voice_focusrooms', {})
                    self.active_voice_focusrooms[voice_ch.id] = {'muted': muted, 'ends_at': ends_at}
                    setattr(self.bot, 'active_voice_focusrooms', self.active_voice_focusrooms)
                    await ctx.send(f'🔕 Voice Focus Room started for {duration} minutes in {voice_ch.name}. Participants were muted.')
                else:
                    await ctx.send(f'🔕 Focus Room started for {duration} minutes in this channel. Please avoid chat messages.')
            elif action == 'stop':
                self.active_focusrooms = getattr(self, 'active_focusrooms', {})
                sess = self.active_focusrooms.pop(ch_id, None)
                setattr(self.bot, 'active_focusrooms', self.active_focusrooms)
                if sess:
                    # if voice mode, unmute members we muted
                    if sess.get('mode') == 'voice':
                        self.active_voice_focusrooms = getattr(self, 'active_voice_focusrooms', {})
                        # try to find voice channel by owner
                        for vc_id, info in list(self.active_voice_focusrooms.items()):
                            muted = info.get('muted', [])
                            for uid in muted:
                                try:
                                    member = ctx.guild.get_member(uid) or await ctx.guild.fetch_member(uid)
                                    await member.edit(mute=False)
                                except Exception:
                                    pass
                            try:
                                self.active_voice_focusrooms.pop(vc_id, None)
                            except Exception:
                                pass
                        setattr(self.bot, 'active_voice_focusrooms', self.active_voice_focusrooms)
                    await ctx.send('🔔 Focus Room stopped. Good job!')
                else:
                    await ctx.send('No active Focus Room in this channel.')
            else:
                await ctx.send('Usage: /focusroom start [duration_minutes] OR /focusroom stop')

        @commands.Cog.listener()
        async def on_message(self, message: discord.Message):
            # Keep existing study behavior but add focusroom guard warnings
            if message.author.bot:
                return
            ch_id = message.channel.id
            active = getattr(self, 'active_focusrooms', {})
            if active and ch_id in active:
                sess = active.get(ch_id)
                if sess and sess.get('ends_at', 0) > _now_ts():
                    try:
                        # warn and optionally delete message if permitted
                        await message.channel.send(f'<@{message.author.id}> Please avoid chatting in the Focus Room. Your message was noted.')
                        if message.channel.permissions_for(message.guild.me).manage_messages:
                            try:
                                await message.delete()
                            except Exception:
                                pass
                    except Exception:
                        pass
                    return

            # allow other cogs/bot to process message
            return

        # ------------------ Progress tracker ------------------
        @commands.hybrid_command(name='progress', description='Update or view progress for a subject')
        @app_commands.describe(action='update or view', subject='Subject name (update only)', percent='Percent complete (update only)')
        async def progress(self, ctx: commands.Context, action: str, subject: Optional[str] = None, percent: Optional[int] = None):
            action = (action or '').lower()
            user_id = ctx.author.id
            guild_id = ctx.guild.id if ctx.guild else 0
            if action == 'update':
                if not subject or percent is None:
                    await ctx.send('Usage: /progress update subject:<name> percent:<0-100>')
                    return
                try:
                    await DB.set_progress(user_id, guild_id, subject, int(percent))
                    await ctx.send(f'✅ Progress for {subject} updated to {percent}%')
                except Exception as e:
                    await ctx.send(f'Failed to update progress: {e}')
            elif action == 'view':
                rows = await DB.get_progress(user_id, guild_id)
                if not rows:
                    await ctx.send('No progress tracked yet.')
                    return
                lines = [f"{r['subject']}: {r['percent']}%" for r in rows]
                await ctx.send('\n'.join(lines))
            else:
                await ctx.send('Usage: /progress update|view')


async def setup(bot: commands.Bot):
    await bot.add_cog(Study(bot))
