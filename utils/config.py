"""Configuration management for the bot with environment variable validation"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
env_path = Path(__file__).parents[1] / '.env'
load_dotenv(env_path)

def get_required_env(key: str) -> str:
    """Get a required environment variable or raise an error"""
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Missing required environment variable: {key}")
    return value

def get_optional_env(key: str, default: str = None) -> str:
    """Get an optional environment variable with a default value"""
    return os.getenv(key, default)

# Required Configuration
DISCORD_TOKEN = get_required_env('DISCORD_TOKEN')
PREFIX = get_optional_env('PREFIX', '!')

# Optional Gemini Configuration 
GEMINI_API_KEY = get_optional_env('GEMINI_API_KEY')
GEMINI_MODEL = get_optional_env('GEMINI_MODEL', 'models/gemini-2.5-flash')
GEMINI_ENDPOINT = get_optional_env('GEMINI_ENDPOINT', 
                                 'https://generativelanguage.googleapis.com/v1beta2/models')