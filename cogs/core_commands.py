import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
from utils.panda_api import PandaAPI

logger = logging.getLogger(__name__)

class CoreCommands(commands.Cog):
    """Core panda commands - images, facts, etc."""
    
    def __init__(self, bot):
        self.bot = bot
        self.panda_api = PandaAPI()
    
    async def cog_unload(self):
        """Cleanup when cog is unloaded"""
        await self.panda_api.close()
    
    @app_commands.command(name="panda", description="Get a random panda image")
    async def panda_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            img = await self.panda_api.fetch_panda_image()
            if not img:
                await interaction.followup.send("Couldn't fetch a panda image right now. Please try again later.")
                return
            embed = discord.Embed(title="🐼 Adorable Panda", color=0x000000)
            embed.set_image(url=img)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"/panda error: {e}")
            await interaction.followup.send("Unexpected error occurred.")
    
    @app_commands.command(name="pandafact", description="Get a random panda fact")
    async def pandafact_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            fact = await self.panda_api.fetch_panda_fact()
            embed = discord.Embed(title="🎋 Panda Fact", description=fact, color=0x1abc9c)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"/pandafact error: {e}")
            await interaction.followup.send("Unexpected error occurred.")
    
    @app_commands.command(name="pandagif", description="Get a random panda GIF (if available)")
    async def pandagif_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            gif = await self.panda_api.fetch_panda_gif()
            if gif:
                embed = discord.Embed(title="🐼 Panda GIF", color=0x95a5a6)
                embed.set_image(url=gif)
                await interaction.followup.send(embed=embed)
            else:
                img = await self.panda_api.fetch_panda_image()
                if img:
                    embed = discord.Embed(title="🐼 Panda Image (GIF not available)", color=0x95a5a6)
                    embed.set_image(url=img)
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send("Couldn't fetch a panda GIF or image right now.")
        except Exception as e:
            logger.error(f"/pandagif error: {e}")
            await interaction.followup.send("Unexpected error occurred.")
    
    @app_commands.command(name="pandaall", description="Get image + fact together")
    async def pandaall_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            img, fact = await asyncio.gather(
                self.panda_api.fetch_panda_image(), 
                self.panda_api.fetch_panda_fact()
            )
            embed = discord.Embed(title="🐼 Complete Panda Package", description=fact or "", color=0x2c3e50)
            if img:
                embed.set_image(url=img)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"/pandaall error: {e}")
            await interaction.followup.send("Unexpected error occurred.")
    
    @app_commands.command(name="pandaquote", description="Get an inspirational quote (API)")
    async def pandaquote_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            got = await self.panda_api.fetch_quote()
            if not got:
                await interaction.followup.send("Couldn't fetch a quote right now. Please try again later.")
                return
            content, author = got
            embed = discord.Embed(title="💭 Panda Wisdom", description=f"{content}\n\n— {author}", color=0x8e44ad)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"/pandaquote error: {e}")
            await interaction.followup.send("Unexpected error occurred.")
    
    @app_commands.command(name="pandajoke", description="Get a random joke (API)")
    async def pandajoke_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            joke = await self.panda_api.fetch_joke()
            embed = discord.Embed(title="😂 Panda Joke", description=joke, color=0xf1c40f)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"/pandajoke error: {e}")
            await interaction.followup.send("Unexpected error occurred.")
    
    @app_commands.command(name="pandacombo", description="Get a combo of image + fact + joke in one embed")
    async def pandacombo_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            img, fact, joke = await asyncio.gather(
                self.panda_api.fetch_panda_image(), 
                self.panda_api.fetch_panda_fact(), 
                self.panda_api.fetch_joke()
            )
            embed = discord.Embed(title="🐼 Panda Combo", description=fact or "", color=0x16a085)
            if img:
                embed.set_image(url=img)
            embed.add_field(name="Joke", value=joke, inline=False)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            logger.error(f"/pandacombo error: {e}")
            await interaction.followup.send("Unexpected error occurred.")

async def setup(bot):
    await bot.add_cog(CoreCommands(bot))