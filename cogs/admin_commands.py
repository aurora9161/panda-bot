import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional
from utils.config import config_data, save_config
from utils.panda_api import PandaAPI

logger = logging.getLogger(__name__)

class AdminCommands(commands.Cog):
    """Admin-only commands for server configuration"""
    
    def __init__(self, bot):
        self.bot = bot
        self.panda_api = PandaAPI()
    
    async def cog_unload(self):
        """Cleanup when cog is unloaded"""
        await self.panda_api.close()
    
    @app_commands.command(name="pandaconfig", description="Configure daily panda settings (Admin only)")
    @app_commands.describe(
        channel="The channel to send daily pandas to",
        time_str="Time to send daily panda (24-hour UTC, e.g., 14:30)",
        enabled="Enable or disable daily pandas"
    )
    async def pandaconfig_cmd(self, interaction: discord.Interaction, 
                             channel: Optional[discord.TextChannel] = None, 
                             time_str: Optional[str] = None, 
                             enabled: Optional[bool] = None):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You need Administrator permission to use this.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        changes = []
        
        try:
            if channel:
                config_data["daily_channel_id"] = channel.id
                changes.append(f"Channel → {channel.mention}")
            
            if time_str:
                hour, minute = map(int, time_str.split(":"))
                assert 0 <= hour <= 23 and 0 <= minute <= 59
                config_data["daily_time"] = time_str
                changes.append(f"Time → {time_str}")
                
                # Restart daily task if it exists
                daily_cog = self.bot.get_cog("DailyTasks")
                if daily_cog and hasattr(daily_cog, 'daily_panda_task') and daily_cog.daily_panda_task.is_running():
                    daily_cog.daily_panda_task.restart()
            
            if enabled is not None:
                config_data["enabled"] = enabled
                changes.append("Enabled" if enabled else "Disabled")
                
                daily_cog = self.bot.get_cog("DailyTasks")
                if daily_cog and hasattr(daily_cog, 'daily_panda_task'):
                    if enabled:
                        if config_data["daily_channel_id"] and not daily_cog.daily_panda_task.is_running():
                            daily_cog.daily_panda_task.start()
                    else:
                        if daily_cog.daily_panda_task.is_running():
                            daily_cog.daily_panda_task.cancel()
            
            save_config(config_data)
            
            if not changes:
                changes.append("No changes provided.")
            
            embed = discord.Embed(title="🐼 Panda Configuration", color=0x3498db)
            ch = f"<#{config_data['daily_channel_id']}>" if config_data["daily_channel_id"] else "Not set"
            embed.add_field(name="Daily Channel", value=ch, inline=True)
            embed.add_field(name="Daily Time (UTC)", value=config_data["daily_time"], inline=True)
            embed.add_field(name="Enabled", value="Yes" if config_data["enabled"] else "No", inline=True)
            embed.add_field(name="Changes", value=" | ".join(changes), inline=False)
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"/pandaconfig error: {e}")
            await interaction.followup.send("Failed to update settings.", ephemeral=True)
    
    @app_commands.command(name="pandastatus", description="Check current configuration and status")
    async def pandastatus_cmd(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(title="🐼 Panda Bot Status", color=0x9b59b6)
            ch = f"<#{config_data['daily_channel_id']}>" if config_data["daily_channel_id"] else "Not set"
            embed.add_field(name="Daily Channel", value=ch, inline=True)
            embed.add_field(name="Daily Time (UTC)", value=config_data["daily_time"], inline=True)
            embed.add_field(name="Enabled", value="Yes" if config_data["enabled"] else "No", inline=True)
            embed.add_field(name="Guilds", value=str(len(self.bot.guilds)), inline=True)
            embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)} ms", inline=True)
            
            daily_cog = self.bot.get_cog("DailyTasks")
            if daily_cog and hasattr(daily_cog, 'daily_panda_task'):
                if daily_cog.daily_panda_task.is_running() and config_data["enabled"]:
                    nxt = daily_cog.daily_panda_task.next_iteration
                    if nxt:
                        embed.add_field(name="Next Delivery", value=f"<t:{int(nxt.timestamp())}:R>", inline=False)
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"/pandastatus error: {e}")
            await interaction.response.send_message("Unexpected error occurred.")
    
    @app_commands.command(name="pandatest", description="Send a test daily panda (Admin only)")
    async def pandatest_cmd(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You need Administrator permission to use this.", ephemeral=True)
            return
        
        if not config_data["daily_channel_id"]:
            await interaction.response.send_message("Daily channel not configured. Use /pandaconfig first.", ephemeral=True)
            return
        
        await interaction.response.send_message("Sending test panda...", ephemeral=True)
        
        try:
            channel = self.bot.get_channel(config_data["daily_channel_id"])
            img = await self.panda_api.fetch_panda_image()
            fact = await self.panda_api.fetch_panda_fact()
            
            embed = discord.Embed(title="🧪 Test Panda", description=fact or "", color=0x2ecc71)
            if img:
                embed.set_image(url=img)
            
            await channel.send(embed=embed)
            await interaction.followup.send("Test panda sent.", ephemeral=True)
        except Exception as e:
            logger.error(f"/pandatest error: {e}")
            await interaction.followup.send("Failed to send test.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))