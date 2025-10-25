import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class UtilityCommands(commands.Cog):
    """Utility commands - say, QR, help (Festive Edition 🎄)"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="say", description="Make the bot say a message in a channel")
    @app_commands.describe(message="Text to send", channel="Target channel (defaults to current)")
    async def say_cmd(self, interaction: discord.Interaction, message: str, channel: Optional[discord.TextChannel] = None):
        safe = message.replace("@everyone", "everyone").replace("@here", "here")
        allowed = discord.AllowedMentions(everyone=False, users=False, roles=False)
        target = channel or interaction.channel
        try:
            await target.send(safe, allowed_mentions=allowed)
            await interaction.response.send_message(f"Sent in {target.mention}", ephemeral=True)
        except Exception as e:
            logger.error(f"/say error: {e}")
            await interaction.response.send_message("Failed to send message.", ephemeral=True)
    
    @app_commands.command(name="qr", description="Generate a QR code from text")
    @app_commands.describe(text="Text or URL to encode")
    async def qr_cmd(self, interaction: discord.Interaction, text: str):
        await interaction.response.defer()
        try:
            import io
            import qrcode
            from PIL import Image

            qr = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=2,
            )
            qr.add_data(text)
            qr.make(fit=True)
            img: Image.Image = qr.make_image(fill_color="black", back_color="white").convert("RGB")

            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)

            file = discord.File(buf, filename="qr.png")
            embed = discord.Embed(title="🧦 Your Festive QR Code", color=0x2d3436)
            embed.set_image(url="attachment://qr.png")
            embed.set_footer(text="Season of Giving 🎁")
            await interaction.followup.send(embed=embed, file=file)
        except ModuleNotFoundError:
            await interaction.followup.send("QR dependencies missing. Please add qrcode[pil] and pillow to requirements.txt and reinstall.")
        except Exception as e:
            logger.error(f"/qr error: {e}")
            await interaction.followup.send("Failed to generate QR code.")
    
    @app_commands.command(name="pandahelp", description="Show all panda commands (Festive 🎄)")
    async def pandahelp_cmd(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(title="🎄 Panda Bot Help", description="Slash-only commands • Always-on Festive Mode", color=0x00a86b)
            embed.add_field(name="📦 Core", value=(
                "`/panda` image\n"
                "`/pandafact` fact\n"
                "`/pandagif` gif (if available)\n"
                "`/pandaall` image+fact\n"
                "`/pandaquote` quote\n"
                "`/pandajoke` joke\n"
                "`/pandachristmas` festive greeting\n"
            ), inline=False)
            embed.add_field(name="🎉 Fun", value=(
                "`/pandatrivia` trivia question\n"
                "`/pandaname` random name\n"
                "`/pandamash` name mash\n"
                "`/pandapoll` bamboo poll\n"
                "`/pandaping` latency\n"
            ), inline=False)
            embed.add_field(name="🏠 Adoption", value=(
                "`/adoptlist` see available pandas\n"
                "`/adopt` adopt a panda\n"
                "`/mypandas` view your pandas\n"
                "`/feed` feed your panda\n"
                "`/play` play with panda\n"
                "`/pandastats` detailed stats\n"
                "`/rename` give custom name\n"
                "`/wish` daily panda wish (EXP) 🎄\n"
                "`/christmasgift` gift coins/happiness 🎁\n"
            ), inline=False)
            embed.add_field(name="💰 Economy", value=(
                "`/balance` check coins\n"
                "`/work` earn coins (chance of Santa's Helper Bonus)\n"
                "`/daily` daily bonus (+25 Holiday Cheer)\n"
            ), inline=False)
            embed.add_field(name="🧰 Utility", value=(
                "`/qr` generate QR code\n"
                "`/say` make bot say\n"
            ), inline=False)
            embed.add_field(name="🔧 Admin", value=(
                "`/pandaconfig` set channel/time/enable\n"
                "`/pandastatus` status\n"
                "`/pandatest` test send\n"
            ), inline=False)
            embed.add_field(name="👑 Owner", value=(
                "`/pandaownerreload` reload slash\n"
                "`/pandaownerset` owner set channel/time/enable\n"
                "`/pandaownerstatus` owner diagnostic status\n"
            ), inline=False)
            embed.set_footer(text="Made with 🎄 by aurora • Spread cheer with /christmasgift")
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"/pandahelp error: {e}")
            await interaction.response.send_message("Unexpected error occurred.")

async def setup(bot):
    await bot.add_cog(UtilityCommands(bot))