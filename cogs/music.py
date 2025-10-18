"""Music cog

Features:
- /join -> bot joins the caller's voice channel and starts playing a fixed Spotify playlist (public URL).
- /leave -> bot leaves voice channel and stops playback.
- /restart -> owner/admin only: reload playlist, clear caches, reconnect audio.

Implementation notes:
- Spotify API is NOT used. The cog scrapes the public Spotify playlist page to extract track titles (best-effort), then uses yt-dlp to search YouTube for each track and stream audio via ffmpeg.
- Dependencies: yt-dlp, PyNaCl, ffmpeg must be installed on host.
"""

# music.py
from __future__ import annotations

import asyncio
import os
import time
from typing import List, Optional

import discord
import yt_dlp
from discord import Embed
from discord.ext import commands
from discord.utils import get

# Updated with your new playlist URL
YTM_PLAYLIST = os.getenv('YTM_PLAYLIST', 'https://www.youtube.com/playlist?list=PLmbqRMXb-lI4cd56TptqtNCn9Ibe9fLmO')

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_client: Optional[discord.VoiceClient] = None
        self.queue: List[str] = []
        self._player_task = None
        self._playlist_cache = []
        self.volume = 0.15

        self._announce_channel = {}
        self._announce_channel_secondary = {}
        self._now_playing_task = {}
        self._track_start_time = {}
        self._track_duration = {}
        self.current_track_info = {}

    async def cog_load(self):
        print(f'[MUSIC] Cog loaded. Attempting to pre-load playlist from: {YTM_PLAYLIST}')
        await self._load_ytm_playlist()
        if not self._playlist_cache:
            print('[MUSIC] Warning: Playlist cache is empty. Ensure URL is valid and cookies are set correctly.')
        else:
            self.queue = list(self._playlist_cache)

    async def _load_ytm_playlist(self):
        """Loads the YouTube playlist using the secure cookies file from Render's secret path."""
        cookies_path = '/etc/secrets/cookies.txt'

        try:
            if not os.path.exists(cookies_path):
                print(f"[MUSIC] CRITICAL ERROR: Secret cookies file not found at {cookies_path}.")
                return

            print(f'[MUSIC] Attempting playlist extraction with secret cookies from {cookies_path}...')
            ytdl_opts = {
                'quiet': True,
                'extract_flat': False,
                'cachedir': False,
                'noplaylist': False,
                'force_generic_extractor': False,
                'cookies': cookies_path
            }
            ytdl = yt_dlp.YoutubeDL(ytdl_opts)

            info = await asyncio.to_thread(ytdl.extract_info, YTM_PLAYLIST, download=False)

            entries = info.get('entries', []) if info else []
            urls = [e.get('webpage_url') for e in entries if e and e.get('webpage_url')]
            self._playlist_cache = urls[:100] # Limiting to 100 tracks for stability
            print(f'[MUSIC] Successfully loaded {len(self._playlist_cache)} entries from {YTM_PLAYLIST}')

        except Exception as e:
            print(f'[MUSIC] Failed to load YTM playlist: {e}')
            self._playlist_cache = []

    def _build_now_playing_embed(self, info: dict) -> discord.Embed:
        title = info.get('title', 'Unknown Title')
        url = info.get('webpage_url')
        thumbnail = info.get('thumbnail')
        duration = info.get('duration')
        artist = info.get('uploader', 'Unknown Artist')

        embed = Embed(title=title, url=url, color=discord.Color.green())
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)

        embed.add_field(name="Artist/Channel", value=artist, inline=True)
        embed.add_field(name="Duration", value=self._format_duration(duration), inline=True)
        embed.add_field(name="Progress", value="Starting...", inline=False)
        return embed

    async def _announce_now_playing(self, guild: discord.Guild, info: dict):
        guild_id = guild.id
        embed = self._build_now_playing_embed(info)

        if guild_id in self._now_playing_task:
            self._now_playing_task[guild_id].cancel()

        sent_msgs = []
        channels_to_send = [ch for ch in [self._announce_channel.get(guild_id), self._announce_channel_secondary.get(guild_id)] if ch]
        channels_to_send = list(dict.fromkeys(channels_to_send))

        for channel in channels_to_send:
            try:
                m = await channel.send(embed=embed)
                sent_msgs.append(m)
            except Exception as e:
                print(f"[MUSIC] Failed to send now-playing message to channel {channel.id}: {e}")

        if not sent_msgs:
            return

        self._track_start_time[guild_id] = time.time()
        self._track_duration[guild_id] = info.get('duration')

        async def updater():
            try:
                while True:
                    await asyncio.sleep(5)
                    elapsed = int(time.time() - self._track_start_time.get(guild_id, 0))
                    dur = self._track_duration.get(guild_id)

                    if not self.voice_client or not (self.voice_client.is_playing() or self.voice_client.is_paused()):
                        break

                    progress = f"{self._format_duration(elapsed)} / {self._format_duration(dur)}" if dur else "Live"

                    for m in sent_msgs:
                        try:
                            new_embed = m.embeds[0]
                            # Check if embed has enough fields before trying to set field at index 2
                            if len(new_embed.fields) > 2:
                                new_embed.set_field_at(2, name="Progress", value=progress, inline=False)
                                await m.edit(embed=new_embed)
                            else:
                                # Handle cases where the embed might be different (e.g., first creation)
                                print(f"[MUSIC] Warning: Embed for message {m.id} has fewer than 3 fields.")

                        except (discord.NotFound, IndexError):
                            sent_msgs.remove(m) # Remove if message deleted or embed structure issue
                        except Exception as e:
                            print(f"[MUSIC] Error updating now-playing message {m.id}: {e}")
            except asyncio.CancelledError:
                for m in sent_msgs:
                    try:
                        new_embed = m.embeds[0]
                        new_embed.set_footer(text="Playback has ended.")
                        new_embed.color = discord.Color.red()
                        await m.edit(embed=new_embed)
                    except Exception:
                        pass # Ignore errors during cleanup

        self._now_playing_task[guild_id] = self.bot.loop.create_task(updater())

    def _format_duration(self, seconds: Optional[int]) -> str:
        if seconds is None: return 'N/A'
        try:
            seconds = int(seconds)
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            return f'{h}:{m:02d}:{s:02d}' if h else f'{m:02d}:{s:02d}'
        except (ValueError, TypeError):
             return 'N/A'


    def _ensure_player(self):
        if not self._player_task or self._player_task.done():
            self._player_task = self.bot.loop.create_task(self._player_loop())

    async def _player_loop(self):
        ytdl_opts = {'format': 'bestaudio/best', 'noplaylist': True, 'quiet': True, 'default_search': 'auto', 'cachedir': False}
        # Use cookies file for yt-dlp instance used in the player loop as well
        cookies_path = '/etc/secrets/cookies.txt'
        if os.path.exists(cookies_path):
            ytdl_opts['cookies'] = cookies_path
        else:
             print("[MUSIC] Player loop: Cookie file not found, continuing without cookies.")

        ytdl = yt_dlp.YoutubeDL(ytdl_opts)

        while True:
            try:
                if not self.queue:
                    if self._playlist_cache:
                        self.queue = list(self._playlist_cache)
                    else:
                        # If cache is also empty, wait and maybe try reloading
                        print("[MUSIC] Queue and cache empty, waiting...")
                        await asyncio.sleep(15)
                        if not self._playlist_cache: # Try reloading if still empty
                             await self._load_ytm_playlist()
                        continue

                item_url = self.queue.pop(0)

                if not self.voice_client or not self.voice_client.is_connected():
                    self.queue.insert(0, item_url) # Re-add to front
                    print("[MUSIC] Voice client disconnected, waiting to reconnect...")
                    await asyncio.sleep(10)
                    continue

                print(f"[MUSIC] Processing: {item_url}")
                info = await asyncio.to_thread(ytdl.extract_info, item_url, download=False)

                # Handle potential playlist entries if noplaylist=True failed
                if 'entries' in info and info.get('entries'):
                     info = info['entries'][0]
                elif not info:
                    print(f"[MUSIC] Failed to get info for {item_url}")
                    continue # Skip this item

                stream_url = info.get('url')
                if not stream_url:
                     print(f"[MUSIC] No stream URL found for {item_url}")
                     continue # Skip this item

                guild = self.voice_client.channel.guild
                self.current_track_info[guild.id] = info

                title = info.get('title', 'Unknown Title')
                artist = info.get('uploader', 'Unknown Artist')
                activity = discord.Activity(type=discord.ActivityType.listening, name=f"🎵 {title} ~ {artist} ✨")
                try:
                    await self.bot.change_presence(activity=activity)
                except Exception as e:
                    print(f"[MUSIC] Failed to change presence: {e}")


                await self._announce_now_playing(guild, info)

                player = discord.FFmpegPCMAudio(stream_url, before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin', options='-vn')
                audio_source = discord.PCMVolumeTransformer(player, volume=self.volume)

                self.voice_client.play(audio_source, after=lambda e: print(f'[MUSIC] Player error: {e}') if e else None)

                while self.voice_client.is_playing() or self.voice_client.is_paused():
                    await asyncio.sleep(1)

                print(f"[MUSIC] Finished playing: {title}")
                # Clear activity after song finishes
                try:
                     # Set a default activity when nothing is playing, or clear it
                     default_activity = discord.Activity(type=discord.ActivityType.listening, name="Music!")
                     await self.bot.change_presence(activity=default_activity)
                except Exception as e:
                     print(f"[MUSIC] Failed to clear presence: {e}")

            except yt_dlp.utils.DownloadError as e:
                 print(f"[MUSIC] DownloadError in player loop for {item_url}: {e}")
                 # Check for specific YouTube errors like age restriction or unavailability
                 if "confirm your age" in str(e):
                     print("[MUSIC] Age restricted video skipped.")
                 elif "Video unavailable" in str(e):
                     print("[MUSIC] Video unavailable skipped.")
                 elif "confirm you.re not a bot" in str(e):
                      print("[MUSIC] CRITICAL: YouTube bot detection triggered again in player loop. Cookies might be invalid.")
                      # Consider stopping or trying to reload playlist/cookies after multiple failures
                 else:
                     print("[MUSIC] General download error, skipping track.")
                 await asyncio.sleep(2) # Short delay before next track

            except Exception as e:
                print(f'[MUSIC] Unexpected player loop error: {e}')
                try:
                    # Reset presence on unexpected error
                     default_activity = discord.Activity(type=discord.ActivityType.listening, name="Music!")
                     await self.bot.change_presence(activity=default_activity)
                except Exception as presence_e:
                     print(f"[MUSIC] Failed to reset presence on error: {presence_e}")
                await asyncio.sleep(10) # Longer delay on unexpected errors


    @commands.hybrid_command(name='start', description='Starts the music bot in your voice channel.')
    async def start(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send('You must be in a voice channel to use this command.')
        channel = ctx.author.voice.channel

        # Check if playlist cache is empty, try loading again if needed
        if not self._playlist_cache:
            await ctx.send("Playlist is currently empty, attempting to load...")
            await self._load_ytm_playlist()
            if not self._playlist_cache:
                 return await ctx.send("Failed to load playlist. Please check logs and ensure cookies are valid.")
            self.queue = list(self._playlist_cache) # Load queue if successful


        if self.voice_client is None or not self.voice_client.is_connected():
            try:
                self.voice_client = await channel.connect()
            except Exception as e:
                return await ctx.send(f"Failed to connect to voice channel: {e}")
        else:
            try:
                await self.voice_client.move_to(channel)
            except Exception as e:
                 return await ctx.send(f"Failed to move to voice channel: {e}")

        await ctx.send(f'Joined **{channel.name}** and started playback. The playlist will loop forever.')

        self._announce_channel[ctx.guild.id] = ctx.channel
        voice_chat_channel = get(ctx.guild.text_channels, name=channel.name)
        if voice_chat_channel:
            self._announce_channel_secondary[ctx.guild.id] = voice_chat_channel

        self._ensure_player()

    @commands.hybrid_command(name='leave', description='Stops music and disconnects the bot (Bot Owner only).')
    async def leave(self, ctx: commands.Context):
        if not ctx.author.id == self.bot.owner_id:
            return await ctx.send("Only my owner can make me leave the voice channel.")

        if self.voice_client:
             # Stop player and cancel updater task
            if self.voice_client.is_playing() or self.voice_client.is_paused():
                self.voice_client.stop()
            if ctx.guild.id in self._now_playing_task:
                 self._now_playing_task[ctx.guild.id].cancel()
                 del self._now_playing_task[ctx.guild.id] # Clean up task entry

            await self.voice_client.disconnect()
            self.voice_client = None
            try:
                await self.bot.change_presence(activity=None) # Clear activity on leave
            except Exception as e:
                 print(f"[MUSIC] Failed to clear presence on leave: {e}")
            await ctx.send('Disconnected by owner.')
        else:
             await ctx.send("Not connected to a voice channel.")


    @commands.hybrid_command(name='pause', description='Pauses the music (Bot Owner only).')
    async def pause(self, ctx: commands.Context):
        if not ctx.author.id == self.bot.owner_id:
            return await ctx.send("Only my owner can pause the music.")

        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()
            await ctx.send("⏸️ Music paused.")
            # Optionally change presence to indicate paused state
            # await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Paused"))
        elif self.voice_client and self.voice_client.is_paused():
             await ctx.send("Music is already paused.")
        else:
             await ctx.send("Not playing anything to pause.")


    @commands.hybrid_command(name='resume', description='Resumes the music (Bot Owner only).')
    async def resume(self, ctx: commands.Context):
        if not ctx.author.id == self.bot.owner_id:
            return await ctx.send("Only my owner can resume the music.")

        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()
            await ctx.send("▶️ Music resumed.")
            # Restore playing presence
            info = self.current_track_info.get(ctx.guild.id)
            if info:
                 title = info.get('title', 'Unknown Title')
                 artist = info.get('uploader', 'Unknown Artist')
                 activity = discord.Activity(type=discord.ActivityType.listening, name=f"🎵 {title} ~ {artist} ✨")
                 try:
                    await self.bot.change_presence(activity=activity)
                 except Exception as e:
                    print(f"[MUSIC] Failed to restore presence on resume: {e}")

        elif self.voice_client and self.voice_client.is_playing():
             await ctx.send("Music is already playing.")
        else:
             await ctx.send("Nothing is paused to resume.")


    @commands.hybrid_command(name='skip', description='Skips the current track.')
    async def skip(self, ctx: commands.Context):
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop() # stop() triggers the 'after' callback in play(), which starts the next song in the loop
            await ctx.send('Skipped to the next track. ⏩')
        else:
            await ctx.send("Not playing anything to skip.")


    @commands.hybrid_command(name='volume', description='Sets the music volume (0-200).')
    async def volume_cmd(self, ctx: commands.Context, vol: int):
        if not (0 <= vol <= 200):
            return await ctx.send('Volume must be between 0 and 200.')

        self.volume = vol / 100.0
        # Adjust volume if currently playing
        if self.voice_client and self.voice_client.source:
             # Ensure the source is a PCMVolumeTransformer
            if isinstance(self.voice_client.source, discord.PCMVolumeTransformer):
                self.voice_client.source.volume = self.volume
                await ctx.send(f'Volume set to {vol}%.')
            else:
                 await ctx.send("Cannot change volume for the current audio source.")
        elif self.voice_client:
             # If connected but not playing, just set the value for the next track
             await ctx.send(f'Volume set to {vol}%. It will apply to the next track.')
        else:
             await ctx.send("Not connected to a voice channel.")


    @commands.hybrid_command(name='nowplaying', description='Shows details about the currently playing song.')
    async def nowplaying(self, ctx: commands.Context):
        # Use guild ID safely
        guild_id = ctx.guild.id if ctx.guild else None
        if not guild_id:
            return await ctx.send("This command can only be used in a server.")

        info = self.current_track_info.get(guild_id)

        if not self.voice_client or not (self.voice_client.is_playing() or self.voice_client.is_paused()) or not info:
            return await ctx.send('Not playing anything right now.')

        embed = self._build_now_playing_embed(info)

        # Calculate and update progress before sending
        elapsed = int(time.time() - self._track_start_time.get(guild_id, 0))
        dur = self._track_duration.get(guild_id)
        progress = f"{self._format_duration(elapsed)} / {self._format_duration(dur)}" if dur else "Live Stream / Unknown Duration"
        # Check if embed has enough fields before setting
        if len(embed.fields) > 2:
            embed.set_field_at(2, name="Progress", value=progress, inline=False)
        else:
             embed.add_field(name="Progress", value=progress, inline=False) # Add if missing


        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Music(bot))