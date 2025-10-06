"""Chat logging utility for StudyBot"""
import datetime
import os
from pathlib import Path

class ChatLogger:
    def __init__(self, log_dir='logs'):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.current_log_file = None
        self.setup_new_log_file()

    def setup_new_log_file(self):
        """Create a new log file with the current date"""
        date_str = datetime.datetime.now().strftime('%Y-%m-%d')
        self.current_log_file = self.log_dir / f'chat_log_{date_str}.txt'
        
        # Create log file if it doesn't exist
        if not self.current_log_file.exists():
            self.current_log_file.touch()

    def log_message(self, author, content, channel=None, guild=None, message_type="MESSAGE", is_bot=False):
        """Log a chat message with timestamp and metadata"""
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Format the message based on whether it's a user message or bot response
        if is_bot:
            log_entry = f"{author}: {content} {{{timestamp}}}\n"
        else:
            log_entry = f"{author}: {content} {{{timestamp}}}\n"
        
        # Check if we need to create a new log file (date changed)
        if not self.current_log_file.stem.endswith(datetime.datetime.now().strftime('%Y-%m-%d')):
            self.setup_new_log_file()
        
        # Append the log entry to the current log file
        with open(self.current_log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)

    def log_command(self, ctx, command_name):
        """Log a command usage"""
        self.log_message(
            ctx.author, 
            f"Used command: {command_name} {ctx.message.content}",
            ctx.channel,
            ctx.guild,
            "COMMAND"
        )

    def log_error(self, error, context=None):
        """Log an error"""
        self.log_message(
            "SYSTEM",
            f"Error: {str(error)} | Context: {context}",
            message_type="ERROR"
        )