"""Website stats and API endpoints for Discord bot."""

import discord
from discord.ext import commands, tasks
from discord import app_commands
import time
import json
from pathlib import Path
from flask import jsonify
from utils.web_server import app, keep_alive
import asyncio
from datetime import datetime, timedelta
import logging
from utils import db


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

website_bot = None

stats = {
    'uptime_start': time.time(),
    'commands_used': 0,
    'study_sessions': 0,
    'total_study_minutes': 0,
    'active_users': 0
}

# Module-level Flask routes so they are registered on import. These use the
# shared `app` from utils.web_server and the `website_bot` global which is set
# when the Website cog is initialized.
@app.route('/api/music/status')
def music_status():
    """Get current music playback status."""
    try:
        music_cog = website_bot.get_cog('Music')
        if not music_cog:
            return jsonify({'error': 'Music cog not loaded'})

        status = {
            'playing': False,
            'current_track': None,
            'volume': 0,
            'loop_mode': 'off'
        }

        if music_cog.voice_client and music_cog.voice_client.is_playing():
            status['playing'] = True
            status['volume'] = music_cog.volume
            status['loop_mode'] = music_cog.loop_mode
            if music_cog.current:
                status['current_track'] = music_cog.current

        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/')
def root():
    return '''<html>
    <head>
        <title>Bot Status🏓 || deepdeyiitk.com || Last updated: 09/10/2025 ~ 22:11:55 pm</title>
        <link rel="icon" type="image/png" href="https://i.postimg.cc/YSV9JqBD/Neon-Green-Circle-Frame-Fitness-You-Tube-Profile-Picturedurga-puja.png">
        <!-- Music Player Status Container -->
        <style>
        #music-status {
            background: linear-gradient(45deg, #1a1a1a, #2d2d2d);
            border-radius: 10px;
            padding: 20px;
            margin: 20px auto;
            max-width: 400px;
            color: #fff;
            font-family: 'Poppins', sans-serif;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        .music-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }
        .music-icon {
            font-size: 24px;
            margin-right: 10px;
        }
        .music-title {
            font-size: 20px;
            font-weight: 600;
            margin: 0;
        }
        .music-details {
            background: rgba(255,255,255,0.1);
            border-radius: 8px;
            padding: 15px;
        }
        .music-track {
            font-size: 16px;
            margin-bottom: 10px;
        }
        .music-controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 10px;
            font-size: 14px;
            color: #a0a0a0;
        }
        .status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 5px;
        }
        .status-dot.playing {
            background: #4CAF50;
            animation: pulse 1.5s infinite;
        }
        .status-dot.stopped {
            background: #f44336;
        }
        @keyframes pulse {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.2); opacity: 0.7; }
            100% { transform: scale(1); opacity: 1; }
        }
        </style>
        <script>
        function updateMusicStatus() {
            fetch('/api/music/status')
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('music-status');
                    if (data.error) {
                        container.innerHTML = `<div class="music-header">
                            <span class="music-icon">🎵</span>
                            <h3 class="music-title">Music Player</h3>
                        </div>
                        <div class="music-details">
                            <div class="music-track">Not available</div>
                        </div>`;
                        return;
                    }

                    const trackName = data.current_track || 'No track playing';
                    const statusDot = data.playing ? 
                        '<span class="status-dot playing"></span>' :
                        '<span class="status-dot stopped"></span>';
                    
                    container.innerHTML = `
                        <div class="music-header">
                            <span class="music-icon">🎵</span>
                            <h3 class="music-title">Music Player</h3>
                        </div>
                        <div class="music-details">
                            <div class="music-track">${trackName}</div>
                            <div class="music-controls">
                                <span>${statusDot}${data.playing ? 'Playing' : 'Stopped'}</span>
                                <span>Volume: ${Math.round(data.volume * 100)}%</span>
                                <span>Loop: ${data.loop_mode}</span>
                            </div>
                        </div>
                    `;
                })
                .catch(error => console.error('Error:', error));
        }

        // Update every 5 seconds
        setInterval(updateMusicStatus, 5000);
        // Initial update
        document.addEventListener('DOMContentLoaded', updateMusicStatus);
        </script>
        <div>
        <!-- Music Status Container -->
        <div id="music-status">
            <div class="music-header">
                <span class="music-icon">🎵</span>
                <h3 class="music-title">Music Player</h3>
            </div>
            <div class="music-details">
                <div class="music-track">Loading...</div>
            </div>
        </div>
        <!-- Diwali Popup HTML, CSS, and JS merged -->
<style>
.diwali-popup-content {
  background: linear-gradient(135deg, #2c1810 0%, #1a0f0a 100%);
  padding: 40px;
  border-radius: 20px;
  position: relative;
  max-width: 500px;
  text-align: center;
  border: 2px solid #ff9933;
  box-shadow: 0 0 50px rgba(255, 153, 51, 0.3), inset 0 0 30px rgba(255, 153, 51, 0.2);
  animation: glowPulse 2s infinite alternate;
}
@keyframes glowPulse {
  0% { box-shadow: 0 0 50px rgba(255, 153, 51, 0.3), inset 0 0 30px rgba(255, 153, 51, 0.2); }
  100% { box-shadow: 0 0 70px rgba(255, 153, 51, 0.4), inset 0 0 40px rgba(255, 153, 51, 0.3); }
}
.close-diwali-popup {
  position: absolute;
  top: 15px;
  right: 15px;
  background: none;
  border: none;
  color: #ff9933;
  font-size: 24px;
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 1;
}
.close-diwali-popup:hover {
  transform: scale(1.2);
  color: #ffb366;
}
.diwali-title {
  color: #ff9933;
  font-size: 36px;
  margin: 20px 0;
  text-shadow: 0 0 10px rgba(255, 153, 51, 0.5);
  font-family: 'Poppins', sans-serif;
  animation: titleGlow 2s infinite alternate;
}
@keyframes titleGlow {
  0% { text-shadow: 0 0 10px rgba(255, 153, 51, 0.5); }
  100% { text-shadow: 0 0 20px rgba(255, 153, 51, 0.8); }
}
.diwali-message {
  color: #ffb366;
  font-size: 18px;
  margin: 20px 0;
  line-height: 1.6;
  font-family: 'Poppins', sans-serif;
}
.diya-container {
  position: relative;
  width: 100px;
  height: 100px;
  margin: 0 auto;
}
.flame {
  position: absolute;
  top: 25%;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  height: 30px;
  background: linear-gradient(to bottom,rgba(255,255,255,0.8) 0%,rgba(255,204,0,0.8) 60%,rgba(255,153,51,0.4) 100%);
  border-radius: 50% 50% 50% 50% / 60% 60% 40% 40%;
  animation: flicker 1s infinite alternate;
  filter: blur(2px);
}
@keyframes flicker {
  0%, 100% { transform: translateX(-50%) scale(1); opacity: 1; }
  50% { transform: translateX(-50%) scale(0.8); opacity: 0.8; }
}
.diwali-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-top: 20px;
  color: #ffb366;
  font-family: 'Poppins', sans-serif;
}
.diwali-logo {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  animation: logoSpin 4s infinite alternate;
}
@keyframes logoSpin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
/* Lighting wire */
#lighting-wire svg circle {
  filter: drop-shadow(0 0 8px #fff) brightness(1.2);
  animation: lightBlink 1.5s infinite alternate;
}
@keyframes lightBlink {
  0% { opacity: 1; }
  100% { opacity: 0.7; }
}
/* Skyshot and lantern styles */
.skyshot {
  transition: box-shadow 0.2s;
}
.blast-particle {
  box-shadow: 0 0 12px #FFD700;
}
.lantern-real {
  pointer-events: none;
}
</style>
<div class="diwali-popup-content" style="position:relative;">
  <button class="close-diwali-popup">&times;</button>
  <!-- Festive Lighting Wire -->
  <div id="lighting-wire" style="position:absolute;top:0;left:0;width:100%;height:48px;pointer-events:none;z-index:10;">
    <svg width="100%" height="48" viewBox="0 0 500 48" style="overflow:visible;">
      <path d="M10,20 Q250,-10 490,20" stroke="#8B4513" stroke-width="4" fill="none"/>
      <g>
        <circle cx="40" cy="16" r="8" fill="#FFD700"/>
        <circle cx="90" cy="12" r="7" fill="#FF9933"/>
        <circle cx="140" cy="18" r="8" fill="#4CAF50"/>
        <circle cx="190" cy="10" r="7" fill="#E91E63"/>
        <circle cx="240" cy="14" r="8" fill="#FFC107"/>
        <circle cx="290" cy="12" r="7" fill="#FF0000"/>
        <circle cx="340" cy="18" r="8" fill="#FFD700"/>
        <circle cx="390" cy="10" r="7" fill="#4CAF50"/>
        <circle cx="440" cy="16" r="8" fill="#FF9933"/>
      </g>
    </svg>
  </div>
  <div class="diya-container">
    <svg viewBox="0 0 100 100" width="100" height="100">
      <path d="M50 70 C20 70 20 40 50 40 C80 40 80 70 50 70" fill="#CD853F"/>
      <ellipse cx="50" cy="40" rx="15" ry="5" fill="#8B4513"/>
    </svg>
    <div class="flame"></div>
  </div>
  <h2 class="diwali-title">Happy Diwali! 🪔</h2>
  <div class="diwali-decoration">
    <svg viewBox="0 0 100 20" width="100%" height="40">
      <pattern id="rangoli" patternUnits="userSpaceOnUse" width="20" height="20">
        <circle cx="10" cy="10" r="3" fill="#ff9933"/>
        <circle cx="10" cy="10" r="6" fill="none" stroke="#ff9933" stroke-width="0.5"/>
      </pattern>
      <rect width="100" height="20" fill="url(#rangoli)"/>
    </svg>
  </div>
  <p class="diwali-message">
    May the festival of lights brighten your studies and illuminate your path to success! <br><br>
    Study with joy, learn with passion! ✨
  </p>
  <div id="diwali-timer" style="font-size:1.2rem;color:#FFD700;margin:12px 0;"></div>
  <div class="diwali-footer">
    <img src="https://i.postimg.cc/MHYsLfPz/Neon-Green-Circle-Frame-Fitness-You-Tube-Profile-Picturedurga-puja.png" alt="StudyBot Logo" class="diwali-logo">
    <span>~ StudyBot Team</span>
  </div>
  <div id="popup-skyshot" style="position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:100;"></div>
  <div id="popup-lantern" style="position:absolute;left:0;width:100%;height:100%;top:0;pointer-events:none;z-index:101;"></div>
</div>
<script>
// Diwali dates (2025-2045)
const diwaliDates = [
  '2025-10-20', '2026-11-08', '2027-10-29', '2028-10-17', '2029-11-05',
  '2030-10-26', '2031-11-14', '2032-11-02', '2033-10-22', '2034-11-10',
  '2035-10-30', '2036-10-19', '2037-11-07', '2038-10-27', '2039-10-17',
  '2040-11-04', '2041-10-25', '2042-11-12', '2043-11-01', '2044-10-20', '2045-11-08'
];
function getNextDiwali(now) {
  for (let i = 0; i < diwaliDates.length; i++) {
    const d = new Date(diwaliDates[i] + 'T00:00:00');
    if (d > now) return {date: d, idx: i};
  }
  return null;
}
let timerState = 'diwali';
let timerIdx = null;
let timerEnd = null;
const timerEl = document.getElementById('diwali-timer');
function updateTimer() {
  const now = new Date();
  let next = getNextDiwali(now);
  if (!next) {
    timerEl.textContent = 'No upcoming Diwali dates.';
    return;
  }
  timerIdx = next.idx;
  let diwaliDate = next.date;
  let diff = diwaliDate - now;
  let days = Math.floor(diff / (1000*60*60*24));
  let hours = Math.floor((diff % (1000*60*60*24)) / (1000*60*60));
  let mins = Math.floor((diff % (1000*60*60)) / (1000*60));
  let secs = Math.floor((diff % (1000*60)) / 1000);
  if (diff > 0 && diff < 1000*60*60*24*31) {
    timerState = 'diwali';
    timerEl.textContent = `Diwali will start in: ${days}d ${hours}h ${mins}m ${secs}s`;
    timerEnd = diwaliDate;
  } else {
    timerState = 'upcoming';
    timerEl.textContent = `Upcoming Diwali will be: ${diwaliDate.toDateString()}`;
    timerEnd = diwaliDate;
  }
}
updateTimer();
let timerInterval = setInterval(() => {
  updateTimer();
  if (timerState === 'diwali' && timerEnd) {
    const now = new Date();
    if (now >= timerEnd) {
      clearInterval(timerInterval);
      timerEl.textContent = 'Diwali is here! 🎉';
      setTimeout(() => {
        setTimeout(() => {
          timerIdx = timerIdx + 1;
          if (timerIdx < diwaliDates.length) {
            timerState = 'upcoming';
            timerEnd = new Date(diwaliDates[timerIdx] + 'T00:00:00');
            timerEl.textContent = `Upcoming Diwali will be: ${timerEnd.toDateString()}`;
            timerInterval = setInterval(updateTimer, 1000);
          } else {
            timerEl.textContent = 'No upcoming Diwali dates.';
          }
        }, 3*24*60*60*1000);
      }, 2000);
    }
  }
}, 1000);
// Skyshot and lantern animation for popup
function launchSkyshot(target, width, height) {
  const shot = document.createElement('div');
  shot.className = 'skyshot';
  const x = Math.random() * width * 0.8 + width * 0.1;
  shot.style.left = x + 'px';
  shot.style.bottom = '0px';
  shot.style.position = 'absolute';
  shot.style.width = '6px';
  shot.style.height = '60px';
  shot.style.background = 'linear-gradient(to top, #FFD700 0%, #ff9933 100%)';
  shot.style.borderRadius = '3px';
  shot.style.opacity = '0.8';
  shot.style.zIndex = '9999';
  target.appendChild(shot);
  let t = 0;
  const duration = 60 + Math.random()*40;
  const interval = setInterval(() => {
    t += 4;
    shot.style.bottom = t + 'px';
    if (t > height * (0.5 + Math.random()*0.3)) {
      clearInterval(interval);
      createBlast(x, t, target);
      shot.remove();
    }
  }, 12);
}
function createBlast(x, y, target) {
  for (let i = 0; i < 18; i++) {
    const p = document.createElement('div');
    p.className = 'blast-particle';
    p.style.position = 'absolute';
    p.style.left = x + 'px';
    p.style.bottom = y + 'px';
    p.style.width = '8px';
    p.style.height = '8px';
    p.style.borderRadius = '50%';
    p.style.background = `hsl(${Math.random()*60+30},100%,60%)`;
    p.style.opacity = '0.9';
    p.style.zIndex = '9999';
    target.appendChild(p);
    const angle = (i/18)*2*Math.PI;
    const dist = 60 + Math.random()*40;
    let step = 0;
    const blastInterval = setInterval(() => {
      step += 1.5;
      p.style.left = (x + Math.cos(angle)*dist*step/20) + 'px';
      p.style.bottom = (y + Math.sin(angle)*dist*step/20) + 'px';
      p.style.opacity = (1-step/20).toFixed(2);
      if (step > 20) {
        clearInterval(blastInterval);
        p.remove();
      }
    }, 18);
  }
}
function launchLantern(target, width, height) {
  const lantern = document.createElement('div');
  lantern.className = 'lantern-real';
  lantern.style.position = 'absolute';
  lantern.style.left = (Math.random()*80+10)*(width/100)+'px';
  lantern.style.bottom = '0px';
  lantern.style.width = '32px';
  lantern.style.height = '48px';
  lantern.style.zIndex = '9999';
  lantern.innerHTML = `<svg width="32" height="48" viewBox="0 0 32 48"><ellipse cx="16" cy="24" rx="14" ry="20" fill="url(#lg)"/><defs><linearGradient id="lg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#FFD700"/><stop offset="100%" stop-color="#ff9933"/></linearGradient></defs><ellipse cx="16" cy="40" rx="6" ry="4" fill="#fff" opacity="0.7"/><rect x="14" y="44" width="4" height="4" rx="2" fill="#FFD700"/></svg>`;
  target.appendChild(lantern);
  let t = 0;
  const floatHeight = height * (0.7 + Math.random()*0.2);
  const interval = setInterval(() => {
    t += 2.5;
    lantern.style.bottom = t + 'px';
    lantern.style.opacity = (1-t/floatHeight).toFixed(2);
    if (t > floatHeight) {
      clearInterval(interval);
      lantern.remove();
    }
  }, 22);
}
let popupSkyshotInterval = setInterval(() => launchSkyshot(document.getElementById('popup-skyshot'), document.getElementById('popup-skyshot').offsetWidth, document.getElementById('popup-skyshot').offsetHeight), 1800);
let popupLanternInterval = setInterval(() => launchLantern(document.getElementById('popup-lantern'), document.getElementById('popup-lantern').offsetWidth, document.getElementById('popup-lantern').offsetHeight), 2200);
document.querySelector('.close-diwali-popup').addEventListener('click', function() {
  clearInterval(timerInterval);
  clearInterval(popupSkyshotInterval);
  clearInterval(popupLanternInterval);
  document.querySelector('.diwali-popup-content').remove();
});
</script>
        </div>
         <div>
  
  <div id="festive-popup-container">
  <div id="festive-popup-overlay">
    <div id="festive-popup">
      <button id="close-popup-btn" title="Close">&times;</button>
      <h2 id="popup-title"></h2>
      <p id="popup-message"></p>
      <div id="countdown-timer"></div>
      <div id="stopwatch" style="display:none;"></div>
      <div class="popup-buttons">
        <button class="popup-btn" id="generate-flowers-btn">🌸 Shower Flowers</button>
        <button class="popup-btn" id="get-blessed-btn">🙏 Receive Blessings</button>
      </div>
    </div>
  </div>

  <div id="blessing-popup-overlay">
    <div id="blessing-popup">
      <h3 id="blessing-title"></h3>
      <p id="blessing-message"></p>
      <button class="popup-btn" id="close-blessing-btn">Close</button>
    </div>
  </div>

  <style>
    @import url('https://fonts.googleapis.com/css2?family=Lobster&family=Poppins:wght@400;600&display=swap');

    #festive-popup-overlay, #blessing-popup-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background-color: rgba(0, 0, 0, 0.75);
      z-index: 99999; /* Highest z-index to stay on top */
      display: none;
      justify-content: center;
      align-items: center;
      padding: 15px;
      box-sizing: border-box;
    }

    #festive-popup, #blessing-popup {
      position: relative;
      background-size: cover;
      background-position: center;
      padding: 30px 40px;
      border-radius: 20px;
      text-align: center;
      color: white;
      font-family: 'Poppins', sans-serif;
      max-width: 95%;
      width: 600px;
      box-shadow: 0 10px 40px rgba(255,152,0,0.5);
      border: 2px solid #ff9800;
      animation: zoomIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
      transform-origin: center;
    }
    
    #blessing-popup {
        background: #fff;
        color: #333;
    }

    @keyframes zoomIn {
      from { opacity: 0; transform: scale(0.8); }
      to { opacity: 1; transform: scale(1); }
    }

    @keyframes zoomOut {
      from { opacity: 1; transform: scale(1); }
      to { opacity: 0; transform: scale(0.8); }
    }

    #festive-popup h2 {
      font-family: 'Lobster', cursive;
      font-size: clamp(2rem, 6vw, 2.8rem);
      margin-bottom: 15px;
      text-shadow: 3px 3px 10px rgba(0,0,0,0.8);
      color: #FFD700; /* Gold color */
    }

    #festive-popup p {
      font-size: clamp(1rem, 3vw, 1.2rem);
      margin-bottom: 20px;
      text-shadow: 2px 2px 8px rgba(0,0,0,0.8);
      line-height: 1.6;
    }

    #countdown-timer, #stopwatch {
      font-size: clamp(1.2rem, 4vw, 1.5rem);
      font-weight: 600;
      margin-top: 25px;
      background-color: rgba(0, 0, 0, 0.6);
      padding: 12px;
      border-radius: 10px;
      display: inline-block;
    }

    .popup-buttons {
      margin-top: 30px;
      display: flex;
      justify-content: center;
      flex-wrap: wrap;
      gap: 10px;
    }

    .popup-btn {
      background: linear-gradient(45deg, #ff9800, #f57c00);
      color: white;
      border: none;
      padding: 12px 25px;
      border-radius: 50px;
      cursor: pointer;
      font-size: 1rem;
      font-weight: 600;
      transition: all 0.3s ease;
      text-transform: uppercase;
      box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }

    .popup-btn:hover {
      transform: translateY(-3px);
      box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    
    #blessing-popup h3 {
      font-family: 'Lobster', cursive;
      font-size: 2rem;
      color: #f57c00;
    }

    #blessing-popup p {
      font-size: 1.1rem;
      color: #555;
    }

    #close-popup-btn {
      position: absolute;
      top: 10px;
      right: 15px;
      background: transparent;
      border: none;
      color: white;
      font-size: 2.5rem;
      cursor: pointer;
      text-shadow: 2px 2px 5px rgba(0,0,0,0.8);
      line-height: 1;
    }

    .flower-petal {
      position: fixed; /* Use fixed to fall over the whole page */
      top: -20px;
      width: 15px;
      height: 15px;
      background-color: #ffeb3b;
      border-radius: 50% 0;
      animation: fall linear infinite;
      z-index: 100000;
    }

    @keyframes fall {
      to {
        transform: translateY(105vh) rotate(720deg);
        opacity: 0;
      }
    }
  </style>

  <script>
    document.addEventListener('DOMContentLoaded', function() {
      // --- Configuration ---
      const festiveData = {
        '2025-09-23': { day: 1, title: 'Happy Navaratri! Day 1', message: 'May the divine grace of Maa Shailaputri bring you unparalleled strength, peace, and prosperity. Wishing you a joyous start to Navaratri!', blessing: 'On Day 1, we worship Maa Shailaputri, the daughter of the Himalayas. She embodies purity and unwavering determination.', image: 'https://images.pexels.com/photos/17585093/pexels-photo-17585093/free-photo-of-a-statue-of-a-goddess-in-a-temple.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1' },
        '2025-09-24': { day: 2, title: 'Shubh Navaratri! Day 2', message: 'Let the blessings of Maa Brahmacharini guide your spirit towards devotion and inner calm. Have a spiritually uplifting day!', blessing: 'Maa Brahmacharini, worshipped on Day 2, represents asceticism and devotion. She grants her devotees wisdom and tranquility.', image: 'https://images.pexels.com/photos/17585093/pexels-photo-17585093/free-photo-of-a-statue-of-a-goddess-in-a-temple.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1' },
        '2025-09-25': { day: 3, title: 'Joyous Navaratri! Day 3', message: 'May the radiant glow of Maa Chandraghanta fill your life with courage, grace, and serenity. Wishing you a blessed day!', blessing: 'Day 3 is for Maa Chandraghanta. Adorned with a crescent moon, she is the symbol of bravery and dispels all evils.', image: 'https://images.pexels.com/photos/17585093/pexels-photo-17585093/free-photo-of-a-statue-of-a-goddess-in-a-temple.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1' },
*** End of newString
    def __init__(self, bot):
        global website_bot
        self.bot = bot
        website_bot = bot
        self._load_stats()
        self.update_stats.start()
        
        # Ensure the shared Flask server is running
        try:
            keep_alive()
        except Exception:
            pass

    def _load_stats(self):
        """Load previous stats if available."""
        stats_path = Path(__file__).parent.parent / 'data' / 'website_stats.json'
        if stats_path.exists():
            try:
                saved_stats = json.loads(stats_path.read_text())
                stats.update(saved_stats)
                stats['uptime_start'] = time.time()  # Reset uptime
            except Exception as e:
                logger.error(f"Failed to load stats: {e}")

    def _save_stats(self):
        """Save current stats to file."""
        stats_path = Path(__file__).parent.parent / 'data' / 'website_stats.json'
        try:
            stats_path.write_text(json.dumps(stats))
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")

    def _run_flask(self):
        """Run the Flask server."""
        # Keep running the shared app; routes are defined at module level.
        try:
            app.run(host='0.0.0.0', port=int(__import__('os').environ.get('PORT', '5000')))
        except Exception as e:
            logger.error(f"Flask server error: {e}")


# Module-level API endpoints that need access to the running bot. They read
# `website_bot` which is set in Website.__init__ when the cog loads.
@app.route('/stats')
def stats_json():
    try:
        ping = 0
        uptime = 0
        if website_bot and hasattr(website_bot, 'latency'):
            ping = round(website_bot.latency * 1000)
        uptime = int(time.time() - stats['uptime_start'])
        return jsonify({'ping': ping, 'uptime': f"{uptime//3600}:{(uptime%3600)//60:02d}:{uptime%60:02d}"})
    except Exception as e:
        logger.error(f"Failed to build /stats response: {e}")
        return jsonify({'ping': 0, 'uptime': '0:00:00'})

@app.route('/api/stats')
def get_stats():
    try:
        ping = 0
        if website_bot and hasattr(website_bot, 'latency'):
            ping = round(website_bot.latency * 1000)
        return jsonify({
            'uptime': int(time.time() - stats['uptime_start']),
            'commands_used': stats['commands_used'],
            'study_sessions': stats['study_sessions'],
            'total_study_minutes': stats['total_study_minutes'],
            'active_users': stats['active_users'],
            'latency': ping
        })
    except Exception as e:
        logger.error(f"Failed to build /api/stats response: {e}")
        return jsonify({})

@app.route('/api/leaderboard')
def get_leaderboard():
    # Get study time leaderboard from DB
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        leaderboard = loop.run_until_complete(
            db.DB.get_leaderboard(limit=10)
        )
        
        formatted = []
        for entry in leaderboard:
            user = website_bot.get_user(entry['user_id']) if website_bot else None
            if user:
                formatted.append({
                    'user': user.display_name,
                    'minutes': entry.get('total_minutes', 0)
                })
                
        return jsonify(formatted)
    finally:
        loop.close()

@app.route('/api/activity')
def get_activity():
    # Get daily activity stats
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Get last 7 days of logs
        week_ago = datetime.now() - timedelta(days=7)
        logs = loop.run_until_complete(
            db.DB.fetchall(
                'SELECT DATE(ts, "unixepoch") as date, COUNT(*) as count FROM study_logs WHERE ts >= ? GROUP BY date',
                (week_ago.timestamp(),)
            )
        )
        
        activity = {
            str(log['date']): log['count']
            for log in logs
        }
        
        return jsonify(activity)
    finally:
        loop.close()

@app.route('/api/subjects')
def get_subjects():
    # Get subject distribution
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        logs = loop.run_until_complete(
            db.DB.fetchall(
                'SELECT topic, SUM(minutes) as total FROM study_logs GROUP BY topic'
            )
        )
        
        subjects = {
            log['topic'] or 'Unknown': log['total']
            for log in logs
        }
        
        return jsonify(subjects)
    finally:
        loop.close()

    @tasks.loop(minutes=5)
    async def update_stats(self):
        """Update website statistics periodically."""
        try:
            # Get total study sessions
            row = await db.DB.fetchone('SELECT COUNT(*) as count FROM study_logs')
            stats['study_sessions'] = row['count'] if row else 0

            # Get total minutes studied
            row = await db.DB.fetchone('SELECT SUM(minutes) as total FROM study_logs')
            stats['total_study_minutes'] = row['total'] if row and row['total'] else 0

            # Get active users (studied in last 24h)
            day_ago = int(time.time() - (24 * 60 * 60))
            row = await db.DB.fetchone(
                'SELECT COUNT(DISTINCT user_id) as count FROM study_logs WHERE ts >= ?',
                (day_ago,)
            )
            stats['active_users'] = row['count'] if row else 0
            
            # Save updated stats
            self._save_stats()
            
        except Exception as e:
            logger.error(f"Failed to update stats: {e}")

    @update_stats.before_loop
    async def before_update_stats(self):
        await self.bot.wait_until_ready()

    def cog_unload(self):
        """Clean up when cog is unloaded."""
        self.update_stats.cancel()
        self._save_stats()


async def setup(bot):
    # Create stats directory if needed
    stats_dir = Path(__file__).parent.parent / 'data'
    stats_dir.mkdir(exist_ok=True)
    
    await bot.add_cog(Website(bot))