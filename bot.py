"""studybot - Main bot runner

This file loads environment variables, sets up the Bot with intents,
loads cogs, and runs the bot. Designed for discord.py v2+.
"""
import asyncio
import sys
import os
import time
import datetime
from dotenv import load_dotenv
from pathlib import Path
import discord
from discord.ext import commands
from utils.config import DISCORD_TOKEN, PREFIX  # Import from config module
try:
  from discord import app_commands
except Exception:
  # Fallback shim so the project can import even if discord.app_commands is incompatible
  class _AppCommandsShim:
    def describe(self, **kwargs):
      def decorator(func):
        return func
      return decorator

  app_commands = _AppCommandsShim()
from utils.chat_logger import ChatLogger
from utils.mod_logger import ModLogger
from utils.db import DB, DB_PATH
from flask import Flask
from threading import Thread
import logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)
import sqlite3
import json

app = Flask('')

@app.route('/')
def home():
    return """
    <html>
    <head>
        <title>Bot Status🏓 || deepdeyiitk.com || Last updated: 09/10/2025 ~ 22:11:55 pm</title>
        <link rel="icon" type="image/png" href="https://i.postimg.cc/YSV9JqBD/Neon-Green-Circle-Frame-Fitness-You-Tube-Profile-Picturedurga-puja.png">
        <div>
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
        '2025-09-26': { day: 4, title: 'Happy Navaratri! Day 4', message: 'May the creative energy of Maa Kushmanda bless your world with happiness, health, and abundance. Stay joyful!', blessing: 'Maa Kushmanda, worshipped on Day 4, is believed to be the creator of the universe. She bestows good health and wealth.', image: 'https://images.pexels.com/photos/17585093/pexels-photo-17585093/free-photo-of-a-statue-of-a-goddess-in-a-temple.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1' },
        '2025-09-27': { day: 5, title: 'Blessed Navaratri! Day 5', message: 'Feel the warmth of Maa Skandamata\'s love. May she shower you and your loved ones with boundless affection and care.', blessing: 'Day 5 honours Maa Skandamata, the mother of Lord Kartikeya. She symbolizes the pure, selfless love of a mother.', image: 'https://images.pexels.com/photos/17585093/pexels-photo-17585093/free-photo-of-a-statue-of-a-goddess-in-a-temple.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1' },
        '2025-09-28': { day: 6, title: 'Divine Navaratri! Day 6', message: 'May the fierce and benevolent Maa Katyayani empower you to conquer all challenges with courage and conviction. Jai Mata Di!', blessing: 'Maa Katyayani, worshipped on Day 6, is the warrior goddess who grants strength to overcome life\'s obstacles.', image: 'https://images.pexels.com/photos/17585093/pexels-photo-17585093/free-photo-of-a-statue-of-a-goddess-in-a-temple.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1' },
        '2025-09-29': { day: 7, title: 'Shubho Maha Saptami!', message: 'As the dhak beats echo, may your heart be filled with immense joy. Wishing you a vibrant start to Durga Puja celebrations!', blessing: 'Maha Saptami marks the formal beginning of Durga Puja. The Goddess is invoked into the idols, bringing her divine presence to the pandals.', image: 'https://images.pexels.com/photos/17585116/pexels-photo-17585116/free-photo-of-a-statue-of-a-god-with-many-arms.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1' },
        '2025-09-30': { day: 8, title: 'Shubho Maha Ashtami!', message: 'May the divine power of Maa Durga bless you with strength and fortitude. Wishing you a spiritually profound Maha Ashtami!', blessing: 'Maha Ashtami celebrates Maa Durga\'s victory over evil. It is the day of the powerful Sandhi Puja, a highlight of the festival.', image: 'https://images.pexels.com/photos/17585116/pexels-photo-17585116/free-photo-of-a-statue-of-a-god-with-many-arms.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1' },
        '2025-10-01': { day: 9, title: 'Shubho Maha Navami!', message: 'On this auspicious Maha Navami, may all your prayers be answered and your life be filled with prosperity and success!', blessing: 'Maha Navami is the culminating day of worship, celebrating the final victory of the Goddess. Grand aartis and rituals are performed.', image: 'https://images.pexels.com/photos/17585116/pexels-photo-17585116/free-photo-of-a-statue-of-a-god-with-many-arms.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1' },
        '2025-10-02': { day: 10, title: 'Happy Vijayadashami!', message: 'May the victory of good over evil inspire you towards a life of truth and courage. Shubho Bijoya and Happy Dussehra to you and your family!', blessing: 'Vijayadashami, or Dussehra, celebrates triumph and new beginnings. It is a day of joy, feasting, and exchanging heartfelt greetings.', image: 'https://images.pexels.com/photos/17585116/pexels-photo-17585116/free-photo-of-a-statue-of-a-god-with-many-arms.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1' }
      };
      const postDussehraDate = new Date('2025-10-02T00:00:00');
      // --- End Configuration ---
      
      const popupOverlay = document.getElementById('festive-popup-overlay');
      const popup = document.getElementById('festive-popup');
      const closeBtn = document.getElementById('close-popup-btn');
      const titleEl = document.getElementById('popup-title');
      const messageEl = document.getElementById('popup-message');
      const countdownEl = document.getElementById('countdown-timer');
      const stopwatchEl = document.getElementById('stopwatch');
      const flowersBtn = document.getElementById('generate-flowers-btn');
      const blessedBtn = document.getElementById('get-blessed-btn');
      const blessingOverlay = document.getElementById('blessing-popup-overlay');
      const blessingTitle = document.getElementById('blessing-title');
      const blessingMessage = document.getElementById('blessing-message');
      const closeBlessingBtn = document.getElementById('close-blessing-btn');

      let intervalId;

      const today = new Date();
      // Use this for testing any date: const today = new Date('2025-09-28');
      const todayString = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0') + '-' + String(today.getDate()).padStart(2, '0');
      
      const currentData = festiveData[todayString];

      function showMainPopup() {
        if (sessionStorage.getItem('festivePopupShown')) return;

        if (currentData) {
          setupPopupContent(currentData);
          popupOverlay.style.display = 'flex';
          startCountdown();
          sessionStorage.setItem('festivePopupShown', 'true');
        } else if (today >= postDussehraDate) {
          setupStopwatchPopup();
          popupOverlay.style.display = 'flex';
          startStopwatch();
          sessionStorage.setItem('festivePopupShown', 'true');
        }
      }
      
      function setupPopupContent(data) {
        titleEl.textContent = data.title;
        messageEl.textContent = data.message;
        popup.style.backgroundImage = `linear-gradient(rgba(0,0,0,0.65), rgba(0,0,0,0.65)), url('${data.image}')`;
        blessedBtn.style.display = 'inline-flex';
        countdownEl.style.display = 'inline-block';
        stopwatchEl.style.display = 'none';
      }

      function setupStopwatchPopup() {
        titleEl.textContent = 'It will happen again next year! 🌸';
        messageEl.textContent = '✨ Victory of Good Over Evil, Light Over Darkness, and Love Over Hatred. May this Vijaya Dashami remind us that every ending carries the seed of a new beginning — every goodbye, a promise of return.';
                                 
                                   
        popup.style.backgroundImage = `linear-gradient(rgba(0,0,0,0.65), rgba(0,0,0,0.65)), url('https://i.postimg.cc/Y9CkRzsq/65155711dce8135d31068666-1695897361989.jpg')`;
        blessedBtn.style.display = 'none';
        countdownEl.style.display = 'none';
        stopwatchEl.style.display = 'inline-block';
      }

      function closeMainPopup() {
        popup.style.animation = 'zoomOut 0.4s forwards';
        setTimeout(() => {
          popupOverlay.style.display = 'none';
          popup.style.animation = 'zoomIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
        }, 400);
      }

      function startCountdown() {
        if(intervalId) clearInterval(intervalId);
        intervalId = setInterval(() => {
          const now = new Date();
          const nextDay = new Date(now);
          nextDay.setDate(now.getDate() + 1);
          nextDay.setHours(0, 0, 0, 0);
          const diff = nextDay - now;
          const h = Math.floor(diff / (1000*60*60));
          const m = Math.floor((diff % (1000*60*60)) / (1000*60));
          const s = Math.floor((diff % (1000*60)) / 1000);
          countdownEl.innerHTML = `Next day begins in: ${String(h).padStart(2,'0')}h ${String(m).padStart(2,'0')}m ${String(s).padStart(2,'0')}s`;
        }, 1000);
      }

      function startStopwatch() {
        if(intervalId) clearInterval(intervalId);
        intervalId = setInterval(() => {
          const diff = new Date() - postDussehraDate;
          const d = Math.floor(diff / (1000*60*60*24));
          const h = Math.floor((diff % (1000*60*60*24)) / (1000*60*60));
          const m = Math.floor((diff % (1000*60*60)) / (1000*60));
          const s = Math.floor((diff % (1000*60)) / 1000);
          stopwatchEl.innerHTML = `Time since Dussehra: ${d}d ${h}h ${m}m ${s}s`;
        }, 1000);
      }
      
      flowersBtn.addEventListener('click', () => {
        for (let i = 0; i < 30; i++) {
          const petal = document.createElement('div');
          petal.className = 'flower-petal';
          petal.style.left = Math.random() * 100 + 'vw';
          petal.style.animationDuration = Math.random() * 3 + 4 + 's';
          petal.style.animationDelay = Math.random() * 2 + 's';
          petal.style.backgroundColor = `hsl(${Math.random() * 60 + 300}, 100%, 70%)`;
          petal.style.transform = `rotate(${Math.random() * 360}deg)`;
          document.getElementById('festive-popup-container').appendChild(petal);
          setTimeout(() => petal.remove(), 7000);
        }
      });
      
      blessedBtn.addEventListener('click', () => {
        if (currentData) {
            blessingTitle.textContent = currentData.title;
            blessingMessage.textContent = currentData.blessing;
            blessingOverlay.style.display = 'flex';
        }
      });
      
      closeBtn.addEventListener('click', closeMainPopup);
      closeBlessingBtn.addEventListener('click', () => blessingOverlay.style.display = 'none');
      
      // Initialize the popup
      showMainPopup();
    });
  </script>
</div>

</div>
        
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #0d1117;
                color: #c9d1d9;
                text-align: center;
                padding-top: 40px;
            }
            a {
                color: #58a6ff;
                text-decoration: none;
                font-weight: bold;
            }
            a:hover {
                text-decoration: underline;
            }
            .container {
                border: 1px solid #30363d;
                border-radius: 10px;
                display: inline-block;
                padding: 20px 30px;
                background-color: #161b22;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>✅ Bot is Alive!</h2>
            <p><a href="https://bots.deepdeyiitk.com" target="_blank" style="color: inherit; text-decoration: none;">Made With 🩷 Deep</a></p>
            <p>Support: <a href="https://www.instagram.com/deepdey.official/" target="_blank">@deepdey.official</a></p>
            <p id="ping">⚡ Ping: 0ms</p>
            <p id="uptime">⏱️ Uptime: 0:00:00</p>
        </div>

        <script>
            async function updateStats() {
                try {
                    const res = await fetch('/stats');
                    const data = await res.json();
                    document.getElementById('ping').innerText = "⚡ Ping: " + data.ping + "ms";
                    document.getElementById('uptime').innerText = "⏱️ Uptime: " + data.uptime;
                } catch(e) {
                    console.log("Failed to fetch stats:", e);
                }
            }
            setInterval(updateStats, 1000); // update every 1 sec
            updateStats();
        </script>
    
    </body>
    </html>
    """

@app.route('/stats')
def stats():
    try:
        current_time = time.time()
        uptime_secs = int(current_time - bot.start_time) if hasattr(bot, "start_time") and bot.start_time else 0
        latency = round(bot.latency * 1000, 2) if hasattr(bot, "latency") else 0
        return {"uptime": str(datetime.timedelta(seconds=uptime_secs)), "ping": latency}
    except Exception as e:
        return {"uptime": "N/A", "ping": 0}


@app.route('/api/active_focus')
def api_active_focus():
  # Return the bot's active focus sessions for website display
  from flask import request
  token = request.args.get('token') or request.headers.get('Authorization')
  if not token or token != os.getenv('API_TOKEN'):
    return json.dumps({'error': 'unauthorized'})
  try:
    sessions = getattr(bot, 'active_focus_sessions', {}) or {}
    # Convert keys to strings for JSON safety
    serializable = {str(k): v for k, v in sessions.items()}
    return json.dumps({'active_focus': serializable})
  except Exception:
    return json.dumps({'active_focus': {}})


@app.route('/api/leaderboard/<int:guild_id>')
def api_leaderboard(guild_id: int):
  # Read leaderboard from sqlite DB directly (synchronous) since Flask here is sync
  from flask import request
  token = request.args.get('token') or request.headers.get('Authorization')
  if not token or token != os.getenv('API_TOKEN'):
    return json.dumps({'error': 'unauthorized'})
  try:
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.execute('SELECT user_id, minutes FROM leaderboard WHERE guild_id = ? ORDER BY minutes DESC LIMIT 20', (guild_id,))
    rows = [{'user_id': r[0], 'minutes': r[1]} for r in cur.fetchall()]
    conn.close()
    return json.dumps({'leaderboard': rows})
  except Exception as e:
    return json.dumps({'leaderboard': [], 'error': str(e)})


@app.route('/api/analytics')
def api_analytics():
  # simple analytics - requires API_TOKEN in query or env
  from flask import request
  token = request.args.get('token') or os.getenv('API_TOKEN')
  if not token or token != os.getenv('API_TOKEN'):
    return json.dumps({'error': 'unauthorized'})
  try:
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.execute('SELECT COUNT(DISTINCT user_id) as users, SUM(minutes) as total_minutes FROM study_logs')
    row = cur.fetchone()
    cur2 = conn.execute('SELECT topic, SUM(minutes) as total FROM study_logs GROUP BY topic ORDER BY total DESC LIMIT 10')
    top = [{'topic': r[0], 'minutes': r[1]} for r in cur2.fetchall()]
    conn.close()
    return json.dumps({'users': row[0] or 0, 'total_minutes': row[1] or 0, 'top_subjects': top})
  except Exception as e:
    return json.dumps({'error': 'failed', 'detail': str(e)})


@app.route('/api/weekly/<int:guild_id>')
def api_weekly(guild_id: int):
  # weekly aggregates for the given guild (requires token)
  from flask import request
  token = request.args.get('token') or request.headers.get('Authorization')
  if not token or token != os.getenv('API_TOKEN'):
    return (json.dumps({'error': 'unauthorized'}), 401, {'Content-Type': 'application/json'})
  try:
    import sqlite3, time
    now = int(time.time())
    week_ago = now - 7*24*60*60
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.execute('SELECT user_id, SUM(minutes) as total FROM study_logs WHERE ts >= ? AND guild_id = ? GROUP BY user_id ORDER BY total DESC', (week_ago, guild_id))
    rows = [{'user_id': r[0], 'minutes': r[1]} for r in cur.fetchall()]
    conn.close()
    return (json.dumps({'weekly': rows}), 200, {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'})
  except Exception as e:
    return (json.dumps({'weekly': [], 'error': str(e)}), 500, {'Content-Type': 'application/json'})


def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()


# Line ~405: GLOBAL VARIABLE DEFINITION
BASE_DIR = Path(__file__).parent

# --- GLOBAL CONFIGURATION (FIXED) ---
load_dotenv(BASE_DIR / '.env')

# 1. LOG_CHANNEL_ID (For Discord operations): Hardcoded per user request (no .env)
LOG_CHANNEL_ID = 1426420958222352496

# 2. LOG_FILE_DIR (For File Loggers): This must be a string/Path.
LOG_FILE_DIR = str(BASE_DIR / 'log_files')

# Load PREFIX once globally
GLOBAL_PREFIX = os.getenv('PREFIX', '!')
# ----------------------------

# Line ~414: PASTE THE PREFIX FUNCTION HERE, AFTER GLOBAL_PREFIX IS DEFINED
def get_prefix(bot, message):
    # This now correctly uses the globally defined variable
    return GLOBAL_PREFIX


intents = discord.Intents.all()


class StudyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=get_prefix,
            intents=intents,
            case_insensitive=True,
            help_command=None
        )
        self.start_time = None
        self.bg_task = None
        
        # FIX: ChatLogger and ModLogger likely require only a file path (string) for file logging.
        self.chat_logger = ChatLogger(LOG_FILE_DIR)
        self.mod_logger = ModLogger(LOG_FILE_DIR)

    async def setup_hook(self):
        # Called after the bot is logged in but before connect finishes; good for setup
        await load_cogs()
        try:
            print('Syncing application (slash) commands...')
            # This will sync all loaded slash/hybrid commands to Discord
            synced = await self.tree.sync()
            print(f'Slash commands synced: {len(synced)} commands')
            
            # Force sync for each guild to ensure all commands are available
            for guild in self.guilds:
                try:
                    await self.tree.sync(guild=guild)
                except Exception as e:
                    print(f'Error syncing commands for guild {guild.id}: {e}')
            
            print('Guild-specific command sync complete.')
        except Exception as e:
            print(f'Error in setup: {e}')
            
    async def on_message(self, message):
        # Log all messages
        if not message.author.bot:
            # Log user message
            self.chat_logger.log_message(
                message.author.name,
                message.content,
                message.channel,
                message.guild
            )
            print(f"[USER] {message.author}: {message.content}") # Added terminal print
        elif message.author == self.user:
            # Log bot's own messages
            self.chat_logger.log_message(
                self.user.name,
                message.content,
                message.channel,
                message.guild,
                is_bot=True
            )
            print(f"[BOT] {message.author}: {message.content}") # Added terminal print
        
        await super().on_message(message)
        
    async def on_member_ban(self, guild, user):
        # Log member bans
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            self.mod_logger.log_action(
                entry.user.name,
                "ban",
                user.name,
                entry.reason
            )
            
    async def on_member_kick(self, guild, user):
        # Log member kicks
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
            self.mod_logger.log_action(
                entry.user.name,
                "kick",
                user.name,
                entry.reason
            )
            
    async def on_member_timeout(self, guild, user):
        # Log member timeouts
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
                if entry.target == user and entry.changes.timeout:
                    self.mod_logger.log_action(
                        entry.user.name,
                        "timeout",
                        user.name,
                        entry.reason
                    )
        except Exception as e:
            print(f'Error logging timeout: {e}')
        # This part of the logic seems misplaced, but I will keep it near the original to avoid breaking things.
        if not self.bg_task:
            self.bg_task = self.loop.create_task(self.status_update_task())
    
    async def on_ready(self):
        # This is the single, correct on_ready handler for the bot.
        print(f'\n{self.user} is ready!')
        print(f'Using prefix: !')
        print('--------------------')
        self.start_time = time.time()  # Set the start time when bot becomes ready
        
        # Set a friendly presence (this will be immediately overridden by the rotating task)
        try:
            await self.change_presence(activity=discord.Game(name="Deep Dey - The FUTURE IITIAN 🎯"))
        except Exception:
            pass
            
        # Always start the status update task when the bot is ready
        if not self.bg_task:
            self.bg_task = self.loop.create_task(self.status_update_task())

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found errors
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: {error.param.name}")
        elif isinstance(error, commands.CheckFailure): # Added to handle checks from the global handler
             await ctx.send("You don't have permission to use that command.")
        else:
            print(f'Error in command {getattr(ctx, "command", None)}: {error}')
            try:
                await ctx.send(f'Error executing command: {error}')
            except Exception:
                pass
            raise error # Re-raise for traceback

    async def on_command(self, ctx):
        print(f'Command executed: {ctx.command} by {ctx.author} in {ctx.guild}')
        await self.chat_logger.log_command(ctx)

    async def on_command_completion(self, ctx):
        print(f"[COMMAND COMPLETED] {ctx.command} by {ctx.author}")
        self.chat_logger.log_message(ctx.author, f"Completed command: {ctx.command}", ctx.channel, ctx.guild, "COMMAND_COMPLETE")


    @commands.hybrid_command(name='sync', description='Sync slash commands (Admin only)')
    @commands.has_permissions(administrator=True)
    async def sync_commands(self, ctx):
        """Sync all slash commands to Discord"""
        try:
            print('Syncing application (slash) commands...')
            synced = await self.tree.sync()
            await ctx.send(f'Successfully synced {len(synced)} commands!')
            print('Slash commands synced.')
        except Exception as e:
            print('Failed to sync app commands:', e)
            try:
                await ctx.send(f'Failed to sync commands: {str(e)}')
            except Exception:
                pass

    async def status_update_task(self):
        await self.wait_until_ready()
        # Timers:
        # - ping_refresh every 15s (updates ping/uptime text)
        # - swap activities every 4s (changes presence between ping and credit)
        # - terminal log every 60s
        ping_activity = discord.Game(name="Ping: 0ms | Uptime: 0:00:00")
        credit_activity = discord.Game(name="Made With 🩷 Deep | deepdeyiitk.com")

        last_ping_refresh = time.monotonic() - 15  # Initialize to ensure immediate refresh
        last_terminal_log = time.monotonic() - 60
        show_ping = True

        while not self.is_closed():
            try:
                now = time.monotonic()

                # Refresh ping/uptime every 15 seconds
                if now - last_ping_refresh >= 15:
                    latency = round(self.latency * 1000) if self.latency is not None else 0
                    uptime_secs = int(time.time() - (self.start_time or time.time()))
                    uptime = str(datetime.timedelta(seconds=uptime_secs))
                    ping_activity = discord.Game(name=f"Ping: {latency}ms | Uptime: {uptime}")
                    last_ping_refresh = now

                # Set presence depending on toggle
                if show_ping:
                    await self.change_presence(activity=ping_activity)
                else:
                    await self.change_presence(activity=credit_activity)

                # Terminal logging every 60 seconds (log same status)
                if now - last_terminal_log >= 60:
                    # use the current ping_activity name for logging
                    try:
                        log_text = ping_activity.name
                    except Exception:
                        log_text = "Ping: N/A | Uptime: N/A | Made With 🩷 Deep | deepdeyiitk.com"
                    print(f"[STATUS LOG] {log_text}")
                    last_terminal_log = now

                # flip the activity and wait 4 seconds before next swap (THIS CONTROLS THE SPEED)
                show_ping = not show_ping
                await asyncio.sleep(4) 

            except Exception as e:
                print(f"Error in status update task: {e}")
                await asyncio.sleep(4)


bot = StudyBot()
# Expose the configured log channel on the bot instance so cogs can use it
bot.LOG_CHANNEL_ID = LOG_CHANNEL_ID
# Expose active focus sessions (populated by cogs/study.py) for website sync
bot.active_focus_sessions = {}


@bot.event
async def on_connect():
    # Called when the connection to Discord is made
    bot.start_time = time.time()
    print(f"Bot connected to Discord at {datetime.datetime.now()}")


async def load_cogs():
    # ADDED DIAGNOSTIC PRINT
    print("Attempting to load cogs from the 'cogs' directory...") 
    
    # Load all cogs in the cogs package
    for file in (BASE_DIR / 'cogs').glob('*.py'):
        if file.name.startswith('_'):
            continue
        ext = f"cogs.{file.stem}"
        try:
            await bot.load_extension(ext)
            print(f"Loaded extension {ext}")
        except Exception as e:
            # THIS PRINT IS CRITICAL: it will show exactly which file failed and why.
            print(f"Failed to load extension {ext}: {e}")


async def main():
    load_dotenv(BASE_DIR / '.env')
    token = os.getenv('DISCORD_TOKEN')

    if not token:
        print('\nERROR: DISCORD_TOKEN not found in environment.\nPlease create a .env file in the project root with:')
        print('DISCORD_TOKEN=your_bot_token_here')
        print('PREFIX=!')
        print("You can also set the environment variables directly.")
        return 1

    print(f"Starting bot with prefix '!' and syncing commands...")
    try:
        # Ensure DB initialized before bot starts
        try:
            await DB.init_db()
        except Exception as e:
            print(f'Warning: DB init failed: {e}')

        # Use `async with bot` to ensure the bot is closed properly on exit
        async with bot:
            await bot.start(token)
    except Exception as e:
        print(f"Error starting bot: {e}")
        return 1


if __name__ == '__main__':
    try:
        keep_alive()  # Start tiny Flask server to keep bot awake
        ret = asyncio.run(main())
        if isinstance(ret, int) and ret != 0:
            sys.exit(ret)
    except KeyboardInterrupt:
        print('Shutting down...')
    except Exception as e:
        print('Unhandled exception during startup:', e)
        raise
