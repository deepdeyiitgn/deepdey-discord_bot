"""Web server integration for keeping the bot alive on Render"""
from flask import Flask
from threading import Thread
import logging

# Disable Flask's default logging to reduce noise
logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    """Run the Flask server in a separate thread"""
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """Start the Flask server in a daemon thread"""
    server = Thread(target=run, daemon=True)
    server.start()