import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional
from utils.config import config_data, save_config

logger = logging.getLogger(__name__)

class OwnerCommands(commands.Cog):
    """Owner-only commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def is_owner_user(self, interaction: discord.Interaction) -> bool:
        """Check if user is bot owner"""
        try:
            app = await self.bot.application_info()
            if interaction.user.id == app.owner.id:
                return True
        except Exception:
            pass
        
        # Check bot owner ID from main.py
        if hasattr(self.bot, 'owner_id') and self.bot.owner_id and interaction.user.id == self.bot.owner_id:
            return True
        
        return False
    
    @app_commands.command(name="pandaownerreload", description="[Owner] Reload slash commands")
    async def owner_reload(self, interaction: discord.Interaction):
        if not await self.is_owner_user(interaction):
            await interaction.response.send_message("You are not the bot owner.", ephemeral=True)
            return
        
        try:
            synced = await self.bot.tree.sync()
            await interaction.response.send_message(f"Reloaded {len(synced)} commands.", ephemeral=True)
        except Exception as e:
            logger.error(f"/pandaownerreload error: {e}")
            await interaction.response.send_message("Failed to reload commands.", ephemeral=True)
    
    @app_commands.command(name="pandaownerset", description="[Owner] Set daily channel/time/enable")
    @app_commands.describe(
        channel="Channel to post daily panda",
        time_str="Daily time HH:MM (UTC)",
        enabled="Enable daily posts"
    )
    async def owner_set(self, interaction: discord.Interaction, 
                       channel: Optional[discord.TextChannel] = None, 
                       time_str: Optional[str] = None, 
                       enabled: Optional[bool] = None):
        if not await self.is_owner_user(interaction):
            await interaction.response.send_message("You are not the bot owner.", ephemeral=True)
            return
        
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
            
            await interaction.response.send_message(" | ".join(changes), ephemeral=True)
        except Exception as e:
            logger.error(f"/pandaownerset error: {e}")
            await interaction.response.send_message("Failed to update settings.", ephemeral=True)
    
    @app_commands.command(name="pandaownerstatus", description="[Owner] Detailed bot status (owner-only)")
    async def owner_status(self, interaction: discord.Interaction):
        if not await self.is_owner_user(interaction):
            await interaction.response.send_message("You are not the bot owner.", ephemeral=True)
            return
        
        try:
            embed = discord.Embed(title="👑 Owner Status", color=0x2e86c1)
            embed.add_field(name="Bot User", value=str(self.bot.user), inline=True)
            embed.add_field(name="Guilds", value=str(len(self.bot.guilds)), inline=True)
            embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)} ms", inline=True)
            
            ch = f"<#{config_data['daily_channel_id']}>" if config_data.get("daily_channel_id") else "Not set"
            embed.add_field(name="Daily Channel", value=ch, inline=True)
            embed.add_field(name="Daily Time (UTC)", value=config_data.get("daily_time", "12:00"), inline=True)
            embed.add_field(name="Enabled", value="Yes" if config_data.get("enabled") else "No", inline=True)
            
            daily_cog = self.bot.get_cog("DailyTasks")
            if daily_cog and hasattr(daily_cog, 'daily_panda_task'):
                running = daily_cog.daily_panda_task.is_running()
                embed.add_field(name="Daily Task", value="Running" if running else "Stopped", inline=True)
                
                if running and config_data.get("enabled"):
                    nxt = daily_cog.daily_panda_task.next_iteration
                    if nxt:
                        embed.add_field(name="Next Delivery", value=f"<t:{int(nxt.timestamp())}:R>", inline=False)
            
            embed.set_footer(text="Owner-only diagnostic view")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"/pandaownerstatus error: {e}")
            await interaction.response.send_message("Failed to get owner status.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(OwnerCommands(bot))