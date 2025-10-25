import discord
from discord.ext import commands
import asyncio
import os
import logging
from typing import Optional

# ==========================================
# BOT TOKEN CONFIGURATION
# ==========================================
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # <-- put your token here

# If not set above, will try environment variable as fallback (safe for hosting)
if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    BOT_TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Optional: set your Discord user ID as bot owner for owner-only commands
BOT_OWNER_ID: int = 1310134550566797352

# ==========================================
# BOT SETUP
# ==========================================
intents = discord.Intents.default()
intents.message_content = True

class PandaBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",  # Prefix for fallback (not used for slash commands)
            intents=intents,
            help_command=None,  # Disable default help
            case_insensitive=True
        )
        
        # Store bot owner ID
        self.owner_id = BOT_OWNER_ID
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        # Load all cogs
        cogs_to_load = [
            "cogs.core_commands",
            "cogs.adoption_system", 
            "cogs.economy_commands",
            "cogs.fun_commands",
            "cogs.utility_commands",
            "cogs.admin_commands",
            "cogs.owner_commands",
            "cogs.daily_tasks"
        ]
        
        for cog in cogs_to_load:
            try:
                await self.load_extension(cog)
                logging.info(f"Loaded cog: {cog}")
            except Exception as e:
                logging.error(f"Failed to load cog {cog}: {e}")
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logging.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            logging.error(f"Failed to sync slash commands: {e}")
    
    async def on_ready(self):
        """Called when bot is ready"""
        logging.info(f"Logged in as {self.user} | Guilds: {len(self.guilds)}")
        logging.info("Panda Bot is ready! 🐼")
    
    async def close(self):
        """Cleanup when bot shuts down"""
        # Close any HTTP sessions in cogs
        for cog in self.cogs.values():
            if hasattr(cog, 'http') and hasattr(cog.http, 'close'):
                await cog.http.close()
        await super().close()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("panda-bot")

# Create and run bot
def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("Please set your bot token in BOT_TOKEN at the top of main.py")
        raise SystemExit(1)
    
    bot = PandaBot()
    
    try:
        bot.run(BOT_TOKEN)
    except discord.LoginFailure:
        logger.error("Invalid bot token.")
    except Exception as e:
        logger.error(f"Runtime error: {e}")

if __name__ == "__main__":
    main()