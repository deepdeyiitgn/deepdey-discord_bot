"""studybot - Main bot runner

This file loads environment variables, sets up the Bot with intents,
loads cogs, and runs the bot. Designed for discord.py v2+.
"""
import asyncio
import sys
import os
import time
import datetime
from pathlib import Path
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord import app_commands
from utils.chat_logger import ChatLogger
from utils.mod_logger import ModLogger
from flask import Flask
from threading import Thread
import logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = Flask('')

@app.route('/')
def home():
    return """
    <html>
    <head>
        <title>Bot Status🏓 || deepdeyiitk.com || Last updated: 09/10/2025 ~ 22:11:55 pm</title>
        <link rel="icon" type="image/png" href="https://i.postimg.cc/YSV9JqBD/Neon-Green-Circle-Frame-Fitness-You-Tube-Profile-Picturedurga-puja.png">
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
         <script>
        // Copy-paste this into your site. Change TARGET_URL to monitor another host.
        // REFRESH_MS controls realtime update frequency (ms).

        (() => {
            const TARGET_URL = window.location.origin; // <-- change if you want to monitor other URL
            const REFRESH_MS = 5000; // update every 5 seconds

            // Minimal CSS injected (Updated for bottom-center and improved mobile view)
            const style = document.createElement('style');
            style.textContent = `
            /* Button: Fixed bottom-center on all screen sizes */
            #sysBtn{
                position:fixed;
                left:50%; /* Center horizontally */
                transform:translateX(-50%); /* Adjust for own width */
                bottom:20px;
                z-index:2147483647;
                width:48px;
                height:48px;
                border-radius:50%;
                border:none;
                background:#0f172a;
                color:#fff;
                font-size:20px;
                display:none;
                align-items:center;
                justify-content:center;
                cursor:pointer;
                box-shadow:0 8px 22px rgba(2,6,23,0.4);
                transition: transform 0.2s;
            }
            #sysBtn:hover { transform: translateX(-50%) scale(1.05); }

            /* Popup: Fixed bottom-center on Desktop */
            #sysPopup{
                position:fixed;
                left:50%;
                transform:translateX(-50%);
                bottom:80px;
                width:360px;
                max-width:96vw;
                background:#fff;
                border-radius:12px;
                box-shadow:0 14px 36px rgba(2,6,23,0.18);
                z-index:2147483647;
                overflow:hidden;
                font-family:Inter, system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
            }
            #sysPopup .head{
                display:flex;
                border-bottom:1px solid #eef2f7;
                background:#f8fafc;
            }
            #sysPopup .tab{
                flex:1;
                text-align:center;
                padding:12px 6px;
                font-weight:600;
                font-size:13px;
                cursor:pointer;
                user-select:none;
                color:#475569;
                transition: background 0.1s;
            }
            #sysPopup .tab:hover { background:#f1f5f9; }
            #sysPopup .tab.active{
                background:#fff;
                color:#0f172a;
                border-bottom: 2px solid #0f172a;
            }
            #sysPopup .content{
                padding:15px;
                font-size:13px;
                line-height:1.4;
                max-height:450px;
                overflow-y:auto;
                color:#0f172a;
                -webkit-overflow-scrolling: touch;
            }
            .sys-row{
                display:flex;
                justify-content:space-between;
                margin:4px 0;
                padding:8px;
                border-radius:6px;
                background:#fbfdff;
                align-items:center;
                border: 1px solid #eef2f7;
            }
            .sys-row small{color:#6b7280}
            .est-tag{font-size:10px;color:#b91c1c;margin-left:6px;font-weight:700;padding:2px 6px;border-radius:4px;background:#fee2e2}
            .note-box{
                margin-top:12px;
                padding:12px;
                background:#f8fafc;
                border-radius:8px;
                font-size:12px;
                color:#0f172a;
                border-left: 3px solid #10b981;
            }
            
            /* Mobile adjustment: Center vertically and horizontally for better visibility */
            @media (max-width:640px){
                #sysPopup{
                    left:50%;
                    top:50%;
                    right:auto;
                    bottom:auto;
                    transform:translate(-50%,-50%);
                    width:92vw;
                    max-height:80vh; /* Limit height on small screens */
                    box-shadow:0 25px 50px -12px rgba(0, 0, 0, 0.25);
                }
                #sysPopup .content {
                    max-height: calc(80vh - 50px);
                }
                #sysBtn{
                    width:52px;
                    height:52px;
                    font-size:24px;
                }
            }
            `;
            document.head.appendChild(style);

            // Button
            const btn = document.createElement('button');
            btn.id = 'sysBtn';
            btn.title = 'System Monitor';
            btn.innerHTML = '⚡';
            btn.style.display = 'none';
            document.body.appendChild(btn);

            // Popup
            const popup = document.createElement('div');
            popup.id = 'sysPopup';
            popup.style.display = 'none';
            popup.innerHTML = `
                <div class="head">
                <div class="tab active" data-tab="server">Server Metrics</div>
                <div class="tab" data-tab="user">User/Browser Info</div>
                </div>
                <div class="content" id="sysContent">Initializing...</div>
            `;
            document.body.appendChild(popup);

            const $ = (s, r = popup) => r.querySelector(s);

            // Show button only when scrolled to bottom (footer area)
            function checkScrollForButton() {
                // Determine if the user is within 100px of the bottom of the page
                const nearBottom = (window.innerHeight + window.scrollY) >= (document.documentElement.scrollHeight - 100);
                btn.style.display = nearBottom ? 'flex' : 'none';
            }
            checkScrollForButton();
            window.addEventListener('scroll', checkScrollForButton);
            window.addEventListener('resize', checkScrollForButton);

            // Tabs
            popup.addEventListener('click', (e) => {
                const t = e.target.closest('.tab');
                if (!t) return;
                popup.querySelectorAll('.tab').forEach(x => x.classList.remove('active'));
                t.classList.add('active');
                updateOnce();
            });

            // Toggle
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                popup.style.display = popup.style.display === 'block' ? 'none' : 'block';
                updateOnce();
            });
            document.addEventListener('click', (e) => {
                if (popup.style.display !== 'block') return;
                if (!popup.contains(e.target) && e.target !== btn) popup.style.display = 'none';
            });

            // Measure server (ping, status, size, headers) - best effort; may be limited by CORS
            async function measureServer() {
                const start = performance.now();
                let ping = '—';
                let status = '—';
                let sizeBytes = null;
                let headersObj = {};
                try {
                    const resp = await fetch(TARGET_URL, { method: 'GET', cache: 'no-store' });
                    const end = performance.now();
                    ping = Math.round(end - start) + ' ms';
                    status = `${resp.status} ${resp.statusText}`;
                    const cl = resp.headers.get('content-length');
                    if (cl) sizeBytes = parseInt(cl, 10);
                    else {
                        // If no content-length, try to get size from blob
                        const blob = await resp.clone().blob();
                        sizeBytes = blob.size;
                    }
                    ['content-type','cache-control','last-modified','etag','server','date'].forEach(k => {
                        const v = resp.headers.get(k);
                        if (v) headersObj[k] = v;
                    });
                } catch (err) {
                    ping = 'ERR';
                    status = 'Fetch failed (CORS/network)';
                    sizeBytes = null;
                    headersObj = {};
                }
                return { ping, status, sizeBytes, headersObj };
            }

            // User info via browser APIs
            async function getUserInfo() {
                const nav = navigator;
                const conn = nav.connection || nav.mozConnection || nav.webkitConnection || null;
                let batteryInfo = null;
                try { if (navigator.getBattery) { const b = await navigator.getBattery(); batteryInfo = { level: Math.round(b.level*100)+'%', charging: b.charging }; } } catch(e){ batteryInfo=null; }
                const perf = performance;
                let mem = null;
                if (perf && perf.memory) {
                    mem = {
                        usedJSHeapSize: Math.round(perf.memory.usedJSHeapSize/1024/1024) + ' MB',
                        totalJSHeapSize: Math.round(perf.memory.totalJSHeapSize/1024/1024) + ' MB'
                    };
                }

                // cookies count
                const cookieStr = document.cookie || '';
                const cookiesCount = cookieStr ? cookieStr.split(';').length : 0;

                // time info
                const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || 'n/a';
                const localTime = new Date().toLocaleString();

                return {
                    userAgent: nav.userAgent,
                    platform: nav.platform,
                    language: nav.language,
                    cores: nav.hardwareConcurrency || 'n/a',
                    cookieEnabled: nav.cookieEnabled,
                    cookiesCount,
                    online: nav.onLine,
                    connection: conn ? { effectiveType: conn.effectiveType, downlink: conn.downlink, rtt: conn.rtt } : null,
                    battery: batteryInfo,
                    memory: mem,
                    deviceMemory: navigator.deviceMemory || 'n/a',
                    plugins: navigator.plugins ? navigator.plugins.length : 'n/a',
                    touchPoints: navigator.maxTouchPoints || 0,
                    doNotTrack: nav.doNotTrack || 'n/a',
                    viewport: { w: window.innerWidth, h: window.innerHeight },
                    timezone: tz,
                    localTime
                };
            }

            // Helpers
            function humanBytes(n) {
                if (n === null || n === undefined) return '—';
                if (typeof n !== 'number') return n;
                const sizes = ['B','KB','MB','GB','TB'];
                if (n === 0) return '0 B';
                const i = Math.floor(Math.log(n)/Math.log(1024));
                return (n/Math.pow(1024,i)).toFixed(i?2:0) + ' ' + sizes[i];
            }

            function renderServerTab(data) {
                const rows = [];
                rows.push(`<div class="sys-row"><div><small>Target URL</small></div><div><small style="max-width:180px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap">${TARGET_URL}</small></div></div>`);
                rows.push(`<div class="sys-row"><div><small>Ping Latency</small></div><div><strong>${data.ping}</strong></div></div>`);
                rows.push(`<div class="sys-row"><div><small>HTTP Status</small></div><div><strong>${data.status}</strong></div></div>`);
                rows.push(`<div class="sys-row"><div><small>Response Size</small></div><div><strong>${humanBytes(data.sizeBytes)}</strong></div></div>`);
                const hdrs = Object.keys(data.headersObj || {});
                if (hdrs.length) {
                    hdrs.forEach(k => rows.push(`<div class="sys-row"><div><small>${k}</small></div><div><small style="max-width:160px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap">${data.headersObj[k]}</small></div></div>`));
                }
                
                // Estimated (simulated) section - clearly labelled as ESTIMATED (SIMULATED)
                rows.push(`<div style="margin-top:10px;border-top:1px dashed #eef2f7;padding-top:10px;color:#374151;font-size:12px"><strong>Server Internal Metrics</strong> <span class="est-tag">SIMULATED</span></div>`);
                const estCpu = (Math.floor(Math.random()*40)+10) + '%';
                const estRam = (Math.floor(Math.random()*50)+20) + '%';
                const estDisk = (Math.floor(Math.random()*60)+15) + '%';
                rows.push(`<div class="sys-row"><div><small>CPU Load (est)</small></div><div><strong>${estCpu}</strong></div></div>`);
                rows.push(`<div class="sys-row"><div><small>RAM Usage (est)</small></div><div><strong>${estRam}</strong></div></div>`);
                rows.push(`<div class="sys-row"><div><small>Disk Usage (est)</small></div><div><strong>${estDisk}</strong></div></div>`);
                rows.push(`<div class="note-box">Note: CPU/RAM/Disk shown above are client-side random **simulations** as browsers cannot access host internals. Ping, Status, and Response size are measured live (subject to browser CORS restrictions).</div>`);
                return rows.join('');
            }

            function renderUserTab(info) {
                const r = [];
                r.push(`<div class="sys-row"><div><small>Browser/UA</small></div><div style="max-width:180px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap"><small>${info.userAgent}</small></div></div>`);
                r.push(`<div class="sys-row"><div><small>OS Platform</small></div><div><strong>${info.platform}</strong></div></div>`);
                r.push(`<div class="sys-row"><div><small>Viewport Size</small></div><div><strong>${info.viewport.w} × ${info.viewport.h}</strong></div></div>`);
                r.push(`<div class="sys-row"><div><small>CPU Cores</small></div><div><strong>${info.cores}</strong></div></div>`);
                r.push(`<div class="sys-row"><div><small>Device Memory</small></div><div><strong>${info.deviceMemory}</strong></div></div>`);
                r.push(`<div class="sys-row"><div><small>JS Heap (Used/Total)</small></div><div><small>${info.memory ? (info.memory.usedJSHeapSize + ' / ' + info.memory.totalJSHeapSize) : 'n/a'}</small></div></div>`);
                r.push(`<div class="sys-row"><div><small>Connection Status</small></div><div><small>${info.online ? `Online · ${info.connection ? `${info.connection.effectiveType} · ${info.connection.downlink}Mbps · rtt ${info.connection.rtt}ms` : 'n/a'}` : 'Offline'}</small></div></div>`);
                r.push(`<div class="sys-row"><div><small>Timezone / Local Time</small></div><div><small>${info.timezone} · ${info.localTime}</small></div></div>`);
                r.push(`<div class="sys-row"><div><small>Cookies</small></div><div><small>enabled:${info.cookieEnabled} · count:${info.cookiesCount}</small></div></div>`);
                
                // Show approximate storage sizes
                try {
                    r.push(`<div class="sys-row"><div><small>localStorage Size</small></div><div><small>${(function(){ try { return humanBytes(new Blob([JSON.stringify(localStorage)]).size); } catch(e){ return 'n/a'; } })()}</small></div></div>`);
                } catch(e) {}
                try {
                    r.push(`<div class="sys-row"><div><small>sessionStorage Size</small></div><div><small>${(function(){ try { return humanBytes(new Blob([JSON.stringify(sessionStorage)]).size); } catch(e){ return 'n/a'; } })()}</small></div></div>`);
                } catch(e) {}
                
                if (info.battery) r.push(`<div class="sys-row"><div><small>Battery Status</small></div><div><small>${info.battery.level}${info.battery.charging? ' · charging':''}</small></div></div>`);
                r.push(`<div class="note-box">Privacy Note: **No data is stored or sent anywhere.** All values shown are read locally from your browser using standard Web APIs.</div>`);
                return r.join('');
            }

            // Update logic
            async function updateOnce() {
                const active = popup.querySelector('.tab.active')?.dataset?.tab || 'server';
                const c = $('#sysContent');
                c.innerHTML = '<div style="text-align:center; padding:20px;">Loading data...</div>';
                if (active === 'server') {
                    const s = await measureServer();
                    c.innerHTML = renderServerTab(s);
                } else {
                    const u = await getUserInfo();
                    c.innerHTML = renderUserTab(u);
                }
            }

            // Auto-refresh while popup open
            setInterval(async () => {
                if (popup.style.display !== 'block') return;
                const active = popup.querySelector('.tab.active')?.dataset?.tab || 'server';
                if (active === 'server') {
                    const s = await measureServer();
                    // Only update content, no need to show 'Loading'
                    $('#sysContent').innerHTML = renderServerTab(s);
                } else {
                    const u = await getUserInfo();
                    $('#sysContent').innerHTML = renderUserTab(u);
                }
            }, REFRESH_MS);

            // Initial message
            (async () => {
                $('#sysContent').innerHTML = 'Ready — click a tab to load real-time data.';
            })();

        })();
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


def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()




BASE_DIR = Path(__file__).parent


def get_prefix(bot, message):
    load_dotenv(BASE_DIR / '.env')
    # Default to ! if no prefix set in .env
    return os.getenv('PREFIX', '!')


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
        self.chat_logger = ChatLogger()
        self.mod_logger = ModLogger()

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
        elif message.author == self.user:
            # Log bot's own messages
            self.chat_logger.log_message(
                self.user.name,
                message.content,
                message.channel,
                message.guild,
                is_bot=True
            )
        
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
        if not self.bg_task:
            self.bg_task = self.loop.create_task(self.status_update_task())

    async def on_ready(self):
        print(f'\n{self.user} is ready!')
        print(f'Using prefix: !')
        print('--------------------')
        self.start_time = time.time()  # Set the start time when bot becomes ready
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
        else:
            print(f'Error in command {getattr(ctx, "command", None)}: {error}')
            try:
                await ctx.send(f'Error executing command: {error}')
            except Exception:
                pass

    async def on_command(self, ctx):
        print(f'Command executed: {ctx.command} by {ctx.author} in {ctx.guild}')
        await self.chat_logger.log_command(ctx)

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
            await ctx.send(f'Failed to sync commands: {str(e)}')

    async def status_update_task(self):
        await self.wait_until_ready()
        # Timers:
        # - ping_refresh every 7s (updates ping/uptime text)
        # - swap activities every 3s (changes presence between ping and credit)
        # - terminal log every 15s
        ping_activity = discord.Game(name="Ping: 0ms | Uptime: 0:00:00")
        credit_activity = discord.Game(name="Made With 🩷 Deep | deepdeyiitk.com")

        last_ping_refresh = time.monotonic() - 7
        last_terminal_log = time.monotonic() - 15
        show_ping = True

        while not self.is_closed():
            try:
                now = time.monotonic()

                # Refresh ping/uptime every 7 seconds
                if now - last_ping_refresh >= 7:
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

                # Terminal logging every 15 seconds (log same status)
                if now - last_terminal_log >= 15:
                    # use the current ping_activity name for logging
                    try:
                        log_text = ping_activity.name
                    except Exception:
                        log_text = "Ping: N/A | Uptime: N/A | Made With 🩷 Deep | deepdeyiitk.com"
                    print(f"[STATUS LOG] {log_text}")
                    last_terminal_log = now

                # flip the activity and wait 3 seconds before next swap
                show_ping = not show_ping
                await asyncio.sleep(3)

            except Exception as e:
                print(f"Error in status update task: {e}")
                await asyncio.sleep(3)


bot = StudyBot()

# Optional: configure logging channel id via env
LOG_CHANNEL_ID = None


@bot.event
async def on_connect():
    # Called when the connection to Discord is made
    bot.start_time = time.time()
    print(f"Bot connected to Discord at {datetime.datetime.now()}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        print(f"[BOT] {message.author}: {message.content}")
        bot.chat_logger.log_message(message.author, message.content, message.channel, message.guild, "BOT")
    else:
        print(f"[USER] {message.author}: {message.content}")
        bot.chat_logger.log_message(message.author, message.content, message.channel, message.guild, "USER")
    await bot.process_commands(message)

@bot.event
async def on_command(ctx):
    print(f"[COMMAND] {ctx.author} used {ctx.command} in {ctx.channel}")
    bot.chat_logger.log_command(ctx, ctx.command.name)

@bot.event
async def on_command_completion(ctx):
    print(f"[COMMAND COMPLETED] {ctx.command} by {ctx.author}")
    bot.chat_logger.log_message(ctx.author, f"Completed command: {ctx.command}", ctx.channel, ctx.guild, "COMMAND_COMPLETE")

@bot.event
async def on_command_error(ctx, error):
    print(f"[ERROR] {ctx.command}: {str(error)}")
    bot.chat_logger.log_error(error, f"Command: {ctx.command} by {ctx.author} in {ctx.channel}")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    # set a friendly presence
    try:
        await bot.change_presence(activity=discord.Game(name="Deep Dey - The FUTURE IITIAN 🎯"))
    except Exception:
        pass
    # record launch time
    if not hasattr(bot, 'launch_time'):
        import datetime
        bot.launch_time = datetime.datetime.utcnow()
    print("Bot is ready.")


@bot.event
async def on_command_error(ctx, error):
    # Generic error handler for commands
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.CheckFailure):
        await ctx.send("You don't have permission to use that command.")
        return
    await ctx.send(f'Error: {error}')
    raise error


async def load_cogs():
    # Load all cogs in the cogs package
    for file in (BASE_DIR / 'cogs').glob('*.py'):
        if file.name.startswith('_'):
            continue
        ext = f"cogs.{file.stem}"
        try:
            await bot.load_extension(ext)
            print(f"Loaded extension {ext}")
        except Exception as e:
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
