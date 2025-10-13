# Deployment Guide

## Render Setup

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Configure the following settings:
   - Name: study-bot (or your preferred name)
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python bot.py`

## Environment Variables

Set these in Render's environment variables section:

- `DISCORD_TOKEN` - Your Discord bot token
- `GEMINI_API_KEY` - Your Gemini API key (optional)
- `TZ` - Set to your timezone (e.g., 'Asia/Kolkata')
- `PORT` - Port for web server (default: 5000)

## Additional Notes

1. Make sure your `requirements.txt` is up to date
2. The bot uses SQLite by default. For production, consider switching to PostgreSQL
3. Set up proper logging in production
4. Configure auto-deploy if desired
5. Monitor your service after deployment

## Useful Commands

```bash
# Start bot locally
python bot.py

# Update requirements
pip freeze > requirements.txt

# Check logs on Render
# Use Render dashboard
```

## Troubleshooting

1. If bot doesn't start:
   - Check logs in Render dashboard
   - Verify environment variables
   - Ensure all dependencies are in requirements.txt

2. If website endpoints don't work:
   - Check if PORT environment variable is set
   - Verify Flask server is running
   - Check Render logs for errors

3. Database issues:
   - Ensure write permissions in data directory
   - Check disk space on Render
   - Consider backing up data regularly