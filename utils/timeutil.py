"""Time utilities with Asia/Kolkata timezone support"""
import datetime
import pytz

def get_kolkata_time():
    """Get current time in Asia/Kolkata timezone"""
    tz = pytz.timezone('Asia/Kolkata')
    return datetime.datetime.now(tz)

def format_time(dt):
    """Format datetime object for display"""
    return dt.strftime("%I:%M %p")

def format_date(dt):
    """Format date for display"""
    return dt.strftime("%d %B, %Y")

def format_datetime(dt):
    """Format full datetime for display"""
    return dt.strftime("%d %B, %Y %I:%M %p IST")