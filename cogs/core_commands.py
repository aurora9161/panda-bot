import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
from utils.panda_api import PandaAPI

logger = logging.getLogger(__name__)

class CoreCommands(commands.Cog):
    """Core panda commands - images, facts, etc. (Festive Edition 🎄)"""
    
    def __init__(self, bot):
        self.bot = bot
        self.panda_api = PandaAPI()
    
    async def cog_unload(self):
        """Cleanup when cog is unloaded"""
        await self.panda_api.close()
    
    @app_commands.command(name="panda", description="Get a random panda image (Festive 🎄)")
    async def panda_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            img = await self.panda_api.fetch_panda_image()
            if not img:
                await interaction.followup.send("Couldn't fetch a panda image right now. Please try again later.")
                return
            embed = discord.Embed(title="🎄🐼 Festive Panda", description="Wishing you cozy bamboo vibes!", color=0x2ecc71)
            embed.set_image(url=img)
            embed.set_footer(text="Spread cheer with /christmasgift 🎁")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"/panda error: {e}")
            await interaction.followup.send("Unexpected error occurred.")
    
    @app_commands.command(name="pandafact", description="Get a random panda fact (Festive 🎄)")
    async def pandafact_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            fact = await self.panda_api.fetch_panda_fact()
            embed = discord.Embed(title="❄️ Panda Winter Fact", description=fact, color=0x1abc9c)
            embed.set_footer(text="Warm wishes and bamboo dishes 🎁")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"/pandafact error: {e}")
            await interaction.followup.send("Unexpected error occurred.")
    
    @app_commands.command(name="pandagif", description="Get a random panda GIF (if available) (Festive 🎄)")
    async def pandagif_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            gif = await self.panda_api.fetch_panda_gif()
            if gif:
                embed = discord.Embed(title="🎁 Panda GIF", description="Holiday tumbles incoming!", color=0x95a5a6)
                embed.set_image(url=gif)
                await interaction.followup.send(embed=embed)
            else:
                img = await self.panda_api.fetch_panda_image()
                if img:
                    embed = discord.Embed(title="🎁 Panda Image (GIF not available)", color=0x95a5a6)
                    embed.set_image(url=img)
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send("Couldn't fetch a panda GIF or image right now.")
        except Exception as e:
            logger.error(f"/pandagif error: {e}")
            await interaction.followup.send("Unexpected error occurred.")
    
    @app_commands.command(name="pandaall", description="Get image + fact together (Festive 🎄)")
    async def pandaall_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            img, fact = await asyncio.gather(
                self.panda_api.fetch_panda_image(), 
                self.panda_api.fetch_panda_fact()
            )
            embed = discord.Embed(title="🕯️ Panda Holiday Bundle", description=fact or "", color=0x2c3e50)
            if img:
                embed.set_image(url=img)
            embed.set_footer(text="Season of Giving: try /christmasgift 🎄")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"/pandaall error: {e}")
            await interaction.followup.send("Unexpected error occurred.")
    
    @app_commands.command(name="pandaquote", description="Get an inspirational quote (Festive 🎄)")
    async def pandaquote_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            got = await self.panda_api.fetch_quote()
            if not got:
                await interaction.followup.send("Couldn't fetch a quote right now. Please try again later.")
                return
            content, author = got
            embed = discord.Embed(title="🧣 Cozy Wisdom", description=f"{content}\n\n— {author}", color=0x8e44ad)
            embed.set_footer(text="Give joy with /christmasgift 🎁")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"/pandaquote error: {e}")
            await interaction.followup.send("Unexpected error occurred.")
    
    @app_commands.command(name="pandajoke", description="Get a random joke (Festive 🎄)")
    async def pandajoke_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            joke = await self.panda_api.fetch_joke()
            embed = discord.Embed(title="🎄 Panda Joke", description=joke, color=0xf1c40f)
            embed.set_footer(text="Laughter is a gift 🎁")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"/pandajoke error: {e}")
            await interaction.followup.send("Unexpected error occurred.")
    
    @app_commands.command(name="pandacombo", description="Image + fact + joke (Festive 🎄)")
    async def pandacombo_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            img, fact, joke = await asyncio.gather(
                self.panda_api.fetch_panda_image(), 
                self.panda_api.fetch_panda_fact(), 
                self.panda_api.fetch_joke()
            )
            embed = discord.Embed(title="🎄 Panda Holiday Combo", description=fact or "", color=0x16a085)
            if img:
                embed.set_image(url=img)
            embed.add_field(name="🎁 Joke", value=joke, inline=False)
            embed.set_footer(text="Share cheer with /christmasgift")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"/pandacombo error: {e}")
            await interaction.followup.send("Unexpected error occurred.")

    @app_commands.command(name="pandachristmas", description="Festive panda greeting with image 🎄")
    async def pandachristmas_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            img = await self.panda_api.fetch_panda_image()
            embed = discord.Embed(title="🎄 Panda Christmas", description="Wishing you bamboo-ful holidays!", color=0x2ecc71)
            if img:
                embed.set_image(url=img)
            embed.add_field(name="Warm Wish", value="May your day be cozy, kind, and full of pandas! 🧦❄️", inline=False)
            embed.set_footer(text="Season of Giving • Try /christmasgift to make someone smile 🎁")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"/pandachristmas error: {e}")
            await interaction.followup.send("Unexpected error occurred.")

async def setup(bot):
    await bot.add_cog(CoreCommands(bot))