"""Music cog

Features:
- /join -> bot joins the caller's voice channel and starts playing a fixed Spotify playlist (public URL).
- /leave -> bot leaves voice channel and stops playback.
- /restart -> owner/admin only: reload playlist, clear caches, reconnect audio.

Implementation notes:
- Spotify API is NOT used. The cog scrapes the public Spotify playlist page to extract track titles (best-effort), then uses yt-dlp to search YouTube for each track and stream audio via ffmpeg.
- Dependencies: yt-dlp, PyNaCl, ffmpeg must be installed on host.
"""
from __future__ import annotations

import asyncio
import re
import html
from typing import List, Optional
from discord.ext import commands
import discord
import yt_dlp
import os
import aiohttp
import time
from discord import Embed
from discord.utils import get

YTM_PLAYLIST = os.getenv('YTM_PLAYLIST', 'https://music.youtube.com/playlist?list=PLmbqRMXb-lI7n-UPclxr35tyZivDiEnbr')


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_client: Optional[discord.VoiceClient] = None
        self.queue: List[str] = []  # list of YT URLs or yt-dlp queries
        self.current = None
        self._player_task = None
        self._playlist_cache = []
        self.loop_mode = False
        self.volume = 0.15
        # per-guild announcement channel and now-playing message/tasks
        self._announce_channel = {}  # guild_id -> TextChannel where join/start invoked
        self._announce_channel_secondary = {}  # guild_id -> secondary channel (matching voice name)
        self._now_playing_message = {}  # guild_id -> Message
        self._now_playing_task = {}  # guild_id -> asyncio.Task
        self._track_start_time = {}
        self._track_duration = {}

    async def cog_load(self):
        # pre-load playlist
        await self._load_ytm_playlist()

    async def _load_ytm_playlist(self):
        """Use yt-dlp to extract playlist entries from YouTube Music playlist URL.
        Stores a list of direct webpage_url entries in _playlist_cache and queue.
        """
        try:
            ytdl_opts = {'quiet': True, 'extract_flat': True}
            ytdl = yt_dlp.YoutubeDL(ytdl_opts)
            info = ytdl.extract_info(YTM_PLAYLIST, download=False)
            entries = info.get('entries', []) if info else []
            urls: List[str] = []
            for e in entries:
                # flat entries might have 'url' (video id) or 'webpage_url'
                if not e:
                    continue
                url = e.get('url') or e.get('webpage_url')
                if url and not url.startswith('http'):
                    # if url is a video id, build full watch URL
                    url = f'https://www.youtube.com/watch?v={url}'
                if url:
                    urls.append(url)
            # limit to first 100
            self._playlist_cache = urls[:100]
            # prepare initial queue as direct urls
            self.queue = list(self._playlist_cache)
            print(f'[MUSIC] Loaded YTM playlist with {len(self._playlist_cache)} entries')
        except Exception as e:
            print(f'[MUSIC] Failed to load YTM playlist: {e}')

    async def _announce_now_playing(self, guild: discord.Guild, info: dict):
        """Send an embed with now-playing info to the stored announce channels and start updater task."""
        guild_id = guild.id
        title = info.get('title') or 'Unknown'
        url = info.get('webpage_url') or info.get('url') or (f"https://www.youtube.com/watch?v={info.get('id')}")
        thumbnail = info.get('thumbnail')
        duration = info.get('duration')
        is_live = info.get('is_live', False)

        embed = Embed(title=title, url=url)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        if is_live:
            embed.add_field(name='Duration', value='Live', inline=True)
        else:
            embed.add_field(name='Duration', value=self._format_duration(duration), inline=True)
        embed.add_field(name='Now Playing', value=title, inline=False)
        embed.set_footer(text='Starting...')

        sent_msgs = []
        # primary announce channel
        chan = self._announce_channel.get(guild_id)
        if chan:
            try:
                m = await chan.send(embed=embed)
                sent_msgs.append(m)
                self._now_playing_message[guild_id] = m
            except Exception as e:
                print(f'[MUSIC] Failed to send now-playing to primary channel: {e}')
        # secondary announce channel (text channel with same name as voice)
        sec = self._announce_channel_secondary.get(guild_id)
        if sec and sec != chan:
            try:
                m2 = await sec.send(embed=embed)
                sent_msgs.append(m2)
            except Exception as e:
                print(f'[MUSIC] Failed to send now-playing to secondary channel: {e}')

        # start updater task to edit messages with elapsed time
        # stop previous task if exists
        if self._now_playing_task.get(guild_id):
            try:
                self._now_playing_task[guild_id].cancel()
            except Exception:
                pass

        # store start time and duration
        self._track_start_time[guild_id] = time.time()
        self._track_duration[guild_id] = duration

        async def updater():
            try:
                while True:
                    await asyncio.sleep(5)
                    elapsed = int(time.time() - self._track_start_time.get(guild_id, time.time()))
                    dur = self._track_duration.get(guild_id)
                    if dur:
                        progress = f"{self._format_duration(elapsed)} / {self._format_duration(dur)}"
                    else:
                        progress = f"{self._format_duration(elapsed)}"
                    for m in sent_msgs:
                        try:
                            new_embed = m.embeds[0]
                            new_embed.set_field_at(0, name='Duration', value=progress, inline=True)
                            new_embed.set_footer(text=f'Elapsed: {self._format_duration(elapsed)}')
                            await m.edit(embed=new_embed)
                        except Exception:
                            pass
                    # stop if not playing anymore
                    if not self.voice_client or not self.voice_client.is_playing():
                        break
            except asyncio.CancelledError:
                return

        task = self.bot.loop.create_task(updater())
        self._now_playing_task[guild_id] = task

    def _format_duration(self, seconds: Optional[int]) -> str:
        if not seconds:
            return 'Unknown'
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h:
            return f'{h}:{m:02d}:{s:02d}'
        return f'{m:02d}:{s:02d}'

    def _ensure_player(self):
        if not self._player_task or self._player_task.done():
            print('[MUSIC] Starting player loop...')
            self._player_task = self.bot.loop.create_task(self._player_loop())

    async def _player_loop(self):
        ytdl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'default_search': 'auto',
        }
        ytdl = yt_dlp.YoutubeDL(ytdl_opts)

        print('[MUSIC] Player loop started.')
        while True:
            if not self.queue:
                print('[MUSIC] Queue is empty, waiting...')
                await asyncio.sleep(3)
                continue
            item = self.queue.pop(0)
            print(f'[MUSIC] Now processing: {item}')
            try:
                info = ytdl.extract_info(item, download=False)
                if not info:
                    print('[MUSIC] No info returned from ytdl')
                    continue
                if 'entries' in info:
                    info = info['entries'][0]
                # choose a stream URL compatible with ffmpeg
                url = info.get('url') or info.get('webpage_url') or info.get('direct_url')
                if not url and info.get('id'):
                    url = f"https://www.youtube.com/watch?v={info.get('id')}"
                # announce now playing to channels
                try:
                    guild = None
                    if self.voice_client and self.voice_client.channel:
                        guild = self.voice_client.channel.guild
                    if guild:
                        await self._announce_now_playing(guild, info)
                except Exception as e:
                    print(f'[MUSIC] Failed to announce now playing: {e}')
                print(f'[MUSIC] Streaming from URL: {url}')
                if self.voice_client is None or not self.voice_client.is_connected():
                    print('[MUSIC] Voice client not connected, waiting...')
                    await asyncio.sleep(2)
                    continue
                # build ffmpeg source with volume control
                player = discord.FFmpegPCMAudio(url, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5')
                audio = discord.PCMVolumeTransformer(player, volume=self.volume)
                self.voice_client.play(audio)
                self.current = item
                # wait until finished
                while self.voice_client.is_playing() or self.voice_client.is_paused():
                    await asyncio.sleep(1)
                print('[MUSIC] Track finished.')
                # loop handling
                if self.loop_mode and self.current:
                    print('[MUSIC] Loop mode enabled, re-queueing current track')
                    self.queue.insert(0, self.current)
            except Exception as e:
                print(f'[MUSIC] Player error: {e}')
                await asyncio.sleep(1)

    @commands.hybrid_command(name='join', description='Join voice channel and start playing the default playlist')
    async def join(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send('You must be in a voice channel to summon the bot.')
            return
        channel = ctx.author.voice.channel
        try:
            if self.voice_client is None or not self.voice_client.is_connected():
                self.voice_client = await channel.connect()
            else:
                await self.voice_client.move_to(channel)
        except Exception as e:
            print(f'[MUSIC] Error connecting to voice: {e}')
            self.voice_client = ctx.voice_client or self.voice_client
        await ctx.send('Joined voice channel and starting playback...')
        # record announce channel for this guild (primary)
        try:
            self._announce_channel[ctx.guild.id] = ctx.channel
            # try to find a text channel with same name as voice channel (secondary)
            txt = get(ctx.guild.text_channels, name=channel.name)
            if txt:
                self._announce_channel_secondary[ctx.guild.id] = txt
        except Exception:
            pass
        # ensure playlist loaded
        await self._load_ytm_playlist()
        print(f'[MUSIC] Playlist cache: {self._playlist_cache}')
        print(f'[MUSIC] Queue: {self.queue}')
        self._ensure_player()

    @commands.hybrid_command(name='leave', description='Stop the music and leave voice channel')
    async def leave(self, ctx: commands.Context):
        try:
            if self.voice_client:
                await self.voice_client.disconnect()
                self.voice_client = None
            await ctx.send('Left voice channel.')
        except Exception as e:
            await ctx.send(f'Could not leave: {e}')

    @commands.hybrid_command(name='stop', description='Stop playback and clear the queue')
    async def stop(self, ctx: commands.Context):
        if self.voice_client:
            try:
                if self.voice_client.is_playing() or self.voice_client.is_paused():
                    self.voice_client.stop()
                self.queue = []
                await ctx.send('Stopped playback and cleared queue.')
            except Exception as e:
                await ctx.send(f'Could not stop: {e}')
        else:
            await ctx.send('Not connected to a voice channel.')

    @commands.hybrid_command(name='skip', description='Skip the current track')
    async def skip(self, ctx: commands.Context):
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
            await ctx.send('Skipped current track.')
        else:
            await ctx.send('No track is currently playing.')

    @commands.hybrid_command(name='loop', description='Toggle loop mode for current track')
    async def loop(self, ctx: commands.Context):
        self.loop_mode = not self.loop_mode
        await ctx.send(f'Loop mode set to {self.loop_mode}')

    @commands.hybrid_command(name='volume', description='Set playback volume (0.0 - 2.0)')
    async def volume_cmd(self, ctx: commands.Context, vol: float):
        if vol < 0.0 or vol > 2.0:
            await ctx.send('Volume must be between 0.0 and 2.0')
            return
        self.volume = vol
        # if currently playing, adjust volume
        try:
            if self.voice_client and getattr(self.voice_client.source, 'volume', None) is not None:
                self.voice_client.source.volume = vol
        except Exception:
            pass
        await ctx.send(f'Set volume to {vol}')

    @commands.hybrid_command(name='restart', description='Reload files, clear caches, and reload playlist (Admin only)')
    @commands.is_owner()
    async def restart(self, ctx: commands.Context):
        # clear caches
        self.queue = []
        self._playlist_cache = []
        # reload playlist
        await self._load_ytm_playlist()
        await ctx.send('Restarted music cog and reloaded playlist cache.')

    @commands.hybrid_command(name='start', description='Start or resume music playback from the default playlist only')
    async def start(self, ctx: commands.Context):
        """Start or resume music playback from the default playlist. User-provided URLs or search queries are not allowed."""
        # ensure user is in voice
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send('You must be in a voice channel to start the bot.')
            return
        channel = ctx.author.voice.channel
        try:
            if self.voice_client is None or not self.voice_client.is_connected():
                self.voice_client = await channel.connect()
            else:
                await self.voice_client.move_to(channel)
        except Exception as e:
            print(f'[MUSIC] Error connecting/moving to voice in start(): {e}')
            self.voice_client = ctx.voice_client or self.voice_client

        # Only allow playback from the default playlist
        if not self._playlist_cache:
            await self._load_ytm_playlist()
        if not self.queue:
            if self._playlist_cache and self._playlist_cache[0].startswith('http'):
                self.queue = list(self._playlist_cache)
            else:
                self.queue = [f"ytsearch1:{t}" for t in self._playlist_cache]
        await ctx.send('Starting playback from the default playlist. Adding custom songs or URLs is disabled.')

        # if playback was paused, resume
        try:
            if self.voice_client and self.voice_client.is_paused():
                self.voice_client.resume()
                await ctx.send('Resumed playback')
        except Exception:
            pass

        # ensure player loop is running
        self._ensure_player()

    @commands.hybrid_command(name='loop', description='Set loop mode: off, track, or queue')
    async def loop(self, ctx: commands.Context, mode: Optional[str] = None):
        """Set loop mode. Usage: /loop [off|track|queue]. If no mode given, reply with current."""
        if mode is None:
            await ctx.send(f'Current loop mode: {self.loop_mode}')
            return
        m = mode.lower().strip()
        if m not in ('off', 'track', 'queue'):
            await ctx.send('Invalid mode. Choose one of: off, track, queue')
            return
        self.loop_mode = m
        await ctx.send(f'Loop mode set to {self.loop_mode}')


async def setup(bot):
    cog = Music(bot)
    await bot.add_cog(cog)
