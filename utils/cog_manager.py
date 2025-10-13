"""Cog loading order and management"""
from typing import List, Dict
from pathlib import Path

# Define cog dependencies and loading order
COG_ORDER = [
    # Core functionality first
    'owner',
    'admin',
    
    # Database dependent cogs
    'study',
    'progress',
    'reminders',
    'todo',
    
    # Feature cogs
    'activity',
    'announcements',
    'autoreply',
    'extras',
    'games',
    'gemini_reply',
    'media',
    'misc',
    'music',
    'quotes',
    'reactions',
]

# Optional cogs that won't stop the bot if they fail to load
OPTIONAL_COGS = {
    'gemini_reply',  # Requires API key
    'music',         # Requires additional dependencies
}