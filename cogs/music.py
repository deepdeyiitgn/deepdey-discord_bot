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

SPOTIFY_PLAYLIST = os.getenv('SPOTIFY_PLAYLIST', 'https://open.spotify.com/playlist/5buBzYC8SdrQAWLsBrskbN?si=66e143950a4c4f47')


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_client: Optional[discord.VoiceClient] = None
        self.queue: List[str] = []  # list of YT URLs or yt-dlp queries
        self.current = None
        self._player_task = None
        self._playlist_cache = []

    async def cog_load(self):
        # pre-load playlist
        await self._load_spotify_playlist()

    async def _fetch_spotify_playlist_page(self, url: str) -> str:
        # fetch public playlist web page
        async with aiohttp.ClientSession() as s:
            async with s.get(url) as r:
                return await r.text()

    async def _parse_spotify_tracks(self, html_text: str) -> List[str]:
        # naive parse: look for track titles in the page
        # This is best-effort and may break if Spotify changes markup.
        titles = []
        try:
            # find pattern """">Track Name</span> or json blocks
            # fallback: get text between aria-label="Track"
            for m in re.finditer(r'"name"\s*:\s*"([^"]+)"', html_text):
                t = html.unescape(m.group(1))
                titles.append(t)
        except Exception:
            pass
        return titles

    async def _load_spotify_playlist(self):
        try:
            page = await self._fetch_spotify_playlist_page(SPOTIFY_PLAYLIST)
            titles = await self._parse_spotify_tracks(page)
            # store cache of titles
            self._playlist_cache = titles[:50]
            # prepare initial queue as ytsearch queries
            self.queue = [f"ytsearch1:{t}" for t in self._playlist_cache]
        except Exception as e:
            print(f'[MUSIC] Failed to load playlist: {e}')

    def _ensure_player(self):
        if not self._player_task:
            self._player_task = self.bot.loop.create_task(self._player_loop())

    async def _player_loop(self):
        ytdl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'default_search': 'ytsearch',
        }
        ytdl = yt_dlp.YoutubeDL(ytdl_opts)

        while True:
            if not self.queue:
                await asyncio.sleep(3)
                continue
            item = self.queue.pop(0)
            try:
                info = ytdl.extract_info(item, download=False)
                if 'entries' in info:
                    info = info['entries'][0]
                url = info.get('url') or info.get('webpage_url')
                source = discord.FFmpegPCMAudio(url)
                if self.voice_client is None or not self.voice_client.is_connected():
                    await asyncio.sleep(2)
                    continue
                self.voice_client.play(source)
                # wait until finished
                while self.voice_client.is_playing() or self.voice_client.is_paused():
                    await asyncio.sleep(1)
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
            self.voice_client = await channel.connect()
        except Exception:
            # already connected or failed
            self.voice_client = ctx.voice_client or self.voice_client
        await ctx.send('Joined voice channel and starting playback...')
        # ensure playlist loaded
        await self._load_spotify_playlist()
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

    @commands.hybrid_command(name='restart', description='Reload files, clear caches, and reload playlist (Admin only)')
    @commands.is_owner()
    async def restart(self, ctx: commands.Context):
        # clear caches
        self.queue = []
        self._playlist_cache = []
        # reload playlist
        await self._load_spotify_playlist()
        await ctx.send('Restarted music cog and reloaded playlist cache.')


async def setup(bot):
    cog = Music(bot)
    await bot.add_cog(cog)
