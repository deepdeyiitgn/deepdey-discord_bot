"""Mod action logging utility for StudyBot"""
import datetime
from pathlib import Path

class ModLogger:
    def __init__(self, log_file='logs/mod_actions.log'):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(exist_ok=True)
        if not self.log_file.exists():
            self.log_file.touch()

    def log_action(self, moderator, action, target=None, reason=None):
        """Log a moderator action
        Args:
            moderator: The moderator who performed the action
            action: The action performed (kick, ban, mute, etc.)
            target: The user who was targeted by the action
            reason: The reason for the action
        """
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Format the mod action log entry
        if target:
            log_entry = f"{moderator}: {action} on {target}"
        else:
            log_entry = f"{moderator}: {action}"
            
        if reason:
            log_entry += f" - Reason: {reason}"
            
        log_entry += f" {{{timestamp}}}\n"
        
        # Append the log entry to the mod actions file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)