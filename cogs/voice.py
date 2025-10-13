"""Voice command recognition and processing system."""
import discord
from discord.ext import commands
import asyncio
import json
from pathlib import Path
import speech_recognition as sr
from pydub import AudioSegment
import io
import wave
import tempfile
import logging


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Command mapping
VOICE_COMMANDS = {
    'start timer': '/focus',
    'end timer': '/cancel',
    'start study': '/log',
    'show stats': '/stats',
    'show progress': '/progress view'
}

class VoiceCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.recognizer = sr.Recognizer()
        self.listening = {}  # {channel_id: bool}

    @commands.hybrid_command(name='voiceon')
    @commands.has_permissions(manage_channels=True)
    async def voiceon(self, ctx):
        """Enable voice command recognition in current channel."""
        if not ctx.author.voice:
            await ctx.send("You must be in a voice channel!")
            return
            
        channel = ctx.author.voice.channel
        
        if channel.id in self.listening:
            await ctx.send("Voice commands are already enabled here!")
            return
            
        # Check bot permissions
        permissions = channel.permissions_for(ctx.guild.me)
        if not permissions.connect:
            await ctx.send("I need permission to join voice channels!")
            return
            
        try:
            await channel.connect()
            self.listening[channel.id] = True
            
            embed = discord.Embed(
                title="🎙️ Voice Commands Enabled",
                description=(
                    "Voice commands are now active in this channel.\n"
                    "Supported commands:\n"
                    "- 'start timer'\n"
                    "- 'end timer'\n"
                    "- 'start study'\n"
                    "- 'show stats'\n"
                    "- 'show progress'"
                ),
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
            # Start listening
            await self._listen_to_channel(channel)
            
        except Exception as e:
            logger.error(f"Failed to enable voice commands: {e}")
            await ctx.send("Failed to enable voice commands!")

    @commands.hybrid_command(name='voiceoff')
    @commands.has_permissions(manage_channels=True)
    async def voiceoff(self, ctx):
        """Disable voice command recognition."""
        if not ctx.author.voice:
            await ctx.send("You must be in a voice channel!")
            return
            
        channel = ctx.author.voice.channel
        
        if channel.id not in self.listening:
            await ctx.send("Voice commands are not enabled here!")
            return
            
        # Stop listening and disconnect
        if ctx.voice_client:
            del self.listening[channel.id]
            await ctx.voice_client.disconnect()
            
        embed = discord.Embed(
            title="Voice Commands Disabled",
            description="Voice command recognition has been turned off.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

    async def _listen_to_channel(self, channel):
        """Continuously listen to voice channel for commands."""
        while channel.id in self.listening:
            try:
                # Get voice client
                voice_client = channel.guild.voice_client
                if not voice_client:
                    break
                    
                # Create sink to receive audio
                sink = discord.sinks.MP3Sink()
                voice_client.start_recording(
                    sink,
                    self._recording_finished,
                    channel
                )
                
                # Record for 5 seconds
                await asyncio.sleep(5)
                voice_client.stop_recording()
                
            except Exception as e:
                logger.error(f"Error in voice listening: {e}")
                await asyncio.sleep(1)

    async def _recording_finished(self, sink, channel):
        """Process recorded audio for commands."""
        try:
            # Get recorded audio
            for user_id, audio in sink.audio_data.items():
                # Convert to WAV format
                with tempfile.NamedTemporaryFile(suffix='.wav') as temp_wav:
                    audio_segment = AudioSegment.from_mp3(
                        io.BytesIO(audio.file.read())
                    )
                    audio_segment.export(temp_wav.name, format='wav')
                    
                    # Recognize speech
                    with sr.AudioFile(temp_wav.name) as source:
                        audio_data = self.recognizer.record(source)
                        try:
                            text = self.recognizer.recognize_google(audio_data)
                            
                            # Check for commands
                            text = text.lower()
                            for trigger, command in VOICE_COMMANDS.items():
                                if trigger in text:
                                    # Get user and create mock message
                                    user = self.bot.get_user(user_id)
                                    if user:
                                        # Create context
                                        ctx = await self.bot.get_context(
                                            type(
                                                'MockMessage',
                                                (),
                                                {
                                                    'author': user,
                                                    'channel': channel,
                                                    'guild': channel.guild,
                                                    'content': command
                                                }
                                            )
                                        )
                                        
                                        # Process command
                                        await self.bot.process_commands(ctx)
                                        break
                                        
                        except sr.UnknownValueError:
                            pass  # Speech not recognized
                        except sr.RequestError as e:
                            logger.error(f"Speech recognition error: {e}")
                            
        except Exception as e:
            logger.error(f"Error processing recording: {e}")


async def setup(bot):
    # Check if required packages are available
    try:
        import speech_recognition
        import pydub
        await bot.add_cog(VoiceCommands(bot))
    except ImportError:
        logger.warning(
            "Voice commands disabled: Required packages not installed. "
            "Install: speech_recognition, pydub"
        )