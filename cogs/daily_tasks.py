import discord
from discord.ext import commands, tasks
import asyncio
import logging
from datetime import datetime, time
from utils.config import config_data, save_config
from utils.panda_api import PandaAPI

logger = logging.getLogger(__name__)

class DailyTasks(commands.Cog):
    """Daily automated tasks"""
    
    def __init__(self, bot):
        self.bot = bot
        self.panda_api = PandaAPI()
    
    async def cog_load(self):
        """Called when cog is loaded"""
        # Start daily task if configured
        if config_data["enabled"] and config_data["daily_channel_id"] and not self.daily_panda_task.is_running():
            self.daily_panda_task.start()
            logger.info("Daily panda task started")
    
    async def cog_unload(self):
        """Cleanup when cog is unloaded"""
        if self.daily_panda_task.is_running():
            self.daily_panda_task.cancel()
        await self.panda_api.close()
    
    @tasks.loop(hours=24)
    async def daily_panda_task(self):
        """Daily panda posting task"""
        if not (config_data["enabled"] and config_data["daily_channel_id"]):
            return
        
        channel = self.bot.get_channel(config_data["daily_channel_id"])
        if not isinstance(channel, discord.TextChannel):
            logger.error("Configured daily channel not found or not a text channel")
            return
        
        try:
            img = await self.panda_api.fetch_panda_image()
            fact = await self.panda_api.fetch_panda_fact()
            
            embed = discord.Embed(title="🐼 Daily Panda!", description=fact or "", color=0x2ecc71)
            if img:
                embed.set_image(url=img)
            else:
                embed.add_field(name="Image", value="Image source unavailable right now.")
            
            embed.set_footer(text=f"Delivered at {datetime.utcnow().strftime('%H:%M UTC')}")
            await channel.send(embed=embed)
            logger.info(f"Daily panda sent to {channel.name}")
        except Exception as e:
            logger.error(f"Daily task error: {e}")
    
    @daily_panda_task.before_loop
    async def before_daily(self):
        """Wait for bot to be ready and schedule first run"""
        await self.bot.wait_until_ready()
        
        try:
            hour, minute = map(int, config_data["daily_time"].split(":"))
            target = time(hour=hour, minute=minute)
            now = datetime.utcnow().time()
            
            now_sec = now.hour * 3600 + now.minute * 60 + now.second
            tgt_sec = target.hour * 3600 + target.minute * 60
            
            if tgt_sec > now_sec:
                wait = tgt_sec - now_sec
            else:
                wait = 86400 - (now_sec - tgt_sec)  # Wait until tomorrow
            
            logger.info(f"Daily panda task will start in {wait} seconds")
            await asyncio.sleep(wait)
        except Exception as e:
            logger.error(f"before_loop scheduling error: {e}")
    
    @daily_panda_task.error
    async def daily_task_error(self, error):
        """Error handler for daily task"""
        logger.error(f"Daily panda task error: {error}")

async def setup(bot):
    await bot.add_cog(DailyTasks(bot))