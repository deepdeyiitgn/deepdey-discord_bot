import discord
from discord.ext import commands, tasks
from discord import app_commands
import qrcode
import aiohttp
import asyncio
import os
import tempfile
from PIL import Image
from pyzbar.pyzbar import decode

# --- CONFIG ---
API_URL = "https://quick-link-url-shortener.vercel.app/api/v1/st"
API_KEY = os.getenv("QUICKLINK_API_KEY")  # set this in .env

class QuickLink(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cleanup_temp.start()

    # --- 🧹 Auto delete temp files every 5 mins ---
    @tasks.loop(minutes=5)
    async def cleanup_temp(self):
        for f in os.listdir(tempfile.gettempdir()):
            path = os.path.join(tempfile.gettempdir(), f)
            if f.startswith("qr_") and os.path.isfile(path):
                try:
                    os.remove(path)
                except:
                    pass

    # --- QR GENERATOR ---
    @app_commands.command(name="qrgen", description="Generate a QR code (text, link, wifi, email, whatsapp, etc.)")
    @app_commands.describe(
        qrtype="Type of QR you want to create",
        data1="Primary data (like text or SSID or email)",
        data2="Optional data (like password, subject, message)",
        data3="Optional data (for wifi security or body text)"
    )
    @app_commands.choices(
        qrtype=[
            app_commands.Choice(name="text", value="text"),
            app_commands.Choice(name="link", value="link"),
            app_commands.Choice(name="wifi", value="wifi"),
            app_commands.Choice(name="email", value="email"),
            app_commands.Choice(name="phone", value="phone"),
            app_commands.Choice(name="whatsapp", value="whatsapp"),
            app_commands.Choice(name="upi", value="upi"),
            app_commands.Choice(name="message", value="message"),
        ]
    )
    async def qrgen(self, interaction: discord.Interaction, qrtype: app_commands.Choice[str], data1: str, data2: str = None, data3: str = None):
        await interaction.response.defer()
        qr_data = None

        if qrtype.value == "text":
            qr_data = data1
        elif qrtype.value == "link":
            qr_data = data1
        elif qrtype.value == "wifi":
            qr_data = f"WIFI:T:{data3 or 'WPA'};S:{data1};P:{data2};;"
        elif qrtype.value == "email":
            qr_data = f"mailto:{data1}?subject={data2 or ''}&body={data3 or ''}"
        elif qrtype.value == "phone":
            qr_data = f"tel:{data1}"
        elif qrtype.value == "whatsapp":
            qr_data = f"https://wa.me/{data1}?text={data2 or ''}"
        elif qrtype.value == "upi":
            qr_data = f"upi://pay?pa={data1}&pn={data2 or ''}&am={data3 or ''}"
        elif qrtype.value == "message":
            qr_data = f"SMSTO:{data1}:{data2 or ''}"

        temp_path = os.path.join(tempfile.gettempdir(), f"qr_{interaction.id}.png")
        qr_img = qrcode.make(qr_data)
        qr_img.save(temp_path)

        file = discord.File(temp_path, filename="qr.png")
        embed = discord.Embed(title="✅ QR Code Generated", color=0x00ff99)
        embed.add_field(name="Type", value=qrtype.name)
        embed.add_field(name="Encoded Data", value=f"```{qr_data}```", inline=False)
        embed.set_image(url="attachment://qr.png")

        await interaction.followup.send(embed=embed, file=file)

    # --- QR SCANNER ---
    @app_commands.command(name="qrscan", description="Scan and decode a QR image.")
    async def qrscan(self, interaction: discord.Interaction):
        await interaction.response.send_message("📸 Please upload your QR image within **60 seconds**.", ephemeral=True)

        def check(m):
            return m.author == interaction.user and m.attachments

        try:
            msg = await self.bot.wait_for("message", timeout=60, check=check)
        except asyncio.TimeoutError:
            return await interaction.followup.send("⏰ Time out! You didn’t send any image.", ephemeral=True)

        img_bytes = await msg.attachments[0].read()
        temp_path = os.path.join(tempfile.gettempdir(), f"qr_{interaction.id}.png")
        with open(temp_path, "wb") as f:
            f.write(img_bytes)

        # Try local decode
        try:
            decoded = decode(Image.open(temp_path))
            if decoded:
                result = decoded[0].data.decode("utf-8")
                embed = discord.Embed(title="✅ QR Code Decoded (Local)", description=f"```{result}```", color=0x00ff66)
                return await interaction.followup.send(embed=embed)
        except Exception:
            pass

        # If local fails -> Ask for third-party
        view = discord.ui.View()
        async def yes_callback(interact):
            await interact.response.defer()
            async with aiohttp.ClientSession() as session:
                form = aiohttp.FormData()
                form.add_field("file", open(temp_path, "rb"), filename="qr.png", content_type="image/png")
                async with session.post("https://api.qrserver.com/v1/read-qr-code/", data=form) as resp:
                    data = await resp.json()
                    text = data[0]["symbol"][0]["data"] if data and data[0]["symbol"][0]["data"] else None
                    if text:
                        embed = discord.Embed(title="✅ QR Code Decoded (via GoQR API)", description=f"```{text}```", color=0x00ffcc)
                        await interaction.followup.send(embed=embed)
                    else:
                        await interaction.followup.send("❌ Could not decode even with external API.")
        async def no_callback(interact):
            await interact.response.send_message("🚫 Decode cancelled.", ephemeral=True)

        yes = discord.ui.Button(label="✅ Yes, use GoQR API", style=discord.ButtonStyle.green)
        no = discord.ui.Button(label="❌ No", style=discord.ButtonStyle.red)
        yes.callback, no.callback = yes_callback, no_callback
        view.add_item(yes)
        view.add_item(no)

        await interaction.followup.send("❌ Local decode failed.\nDo you want to try third-party decoder (GoQR API)?", view=view)

    # --- URL SHORTENER ---
    @app_commands.command(name="shorten", description="Shorten any long URL using QuickLink API.")
    async def shorten(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        payload = {"longUrl": url}

        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, headers=headers, json=payload) as resp:
                data = await resp.json()
                if data.get("status") == "success":
                    short_url = data["shortUrl"]
                    embed = discord.Embed(title="✅ URL Shortened", color=0x00ff99)
                    embed.add_field(name="Original", value=url, inline=False)
                    embed.add_field(name="Shortened", value=short_url, inline=False)
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send(f"❌ Error: {data.get('message', 'Unknown error')}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(QuickLink(bot))
