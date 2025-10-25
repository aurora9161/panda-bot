import discord
from discord.ext import commands
import asyncio
import os
import logging
from typing import Optional

# ==========================================
# 🐼 PANDA BOT TOKEN CONFIGURATION
# ==========================================
# Put your Discord bot token here (recommended for easy setup)
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # <-- PUT YOUR ACTUAL TOKEN HERE

# Alternative: Use environment variable for production hosting
# Set DISCORD_TOKEN environment variable instead of editing this file
if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    BOT_TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Optional: Set your Discord user ID as bot owner for owner-only commands
BOT_OWNER_ID: int = 1310134550566797352  # <-- PUT YOUR DISCORD USER ID HERE

# ==========================================
# 🚀 ENHANCED BOT SETUP
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.guild_messages = True

class PandaBot(commands.Bot):
    """Enhanced Panda Bot with improved error handling and features"""
    
    def __init__(self):
        super().__init__(
            command_prefix="!",  # Fallback prefix (slash commands are primary)
            intents=intents,
            help_command=None,  # We have custom /pandahelp
            case_insensitive=True,
            description="🐼 The ultimate panda adoption and care bot!",
            owner_id=BOT_OWNER_ID
        )
        
        # Store bot owner ID for easy access
        self.owner_id = BOT_OWNER_ID
        self.startup_time = None
        
    async def setup_hook(self):
        """Enhanced startup process with better error handling"""
        self.startup_time = discord.utils.utcnow()
        
        # Load all cogs with enhanced error handling
        cogs_to_load = [
            "cogs.core_commands",      # Basic panda commands
            "cogs.adoption_system",    # Enhanced adoption system
            "cogs.economy_commands",   # Work, daily, balance
            "cogs.fun_commands",       # Games and entertainment
            "cogs.utility_commands",   # Utility functions
            "cogs.admin_commands",     # Server admin commands
            "cogs.owner_commands",     # Bot owner commands
            "cogs.daily_tasks"         # Automated tasks
        ]
        
        loaded_cogs = 0
        failed_cogs = []
        
        for cog in cogs_to_load:
            try:
                await self.load_extension(cog)
                logging.info(f"✅ Loaded cog: {cog}")
                loaded_cogs += 1
            except Exception as e:
                logging.error(f"❌ Failed to load cog {cog}: {e}")
                failed_cogs.append(f"{cog}: {str(e)}")
        
        # Sync slash commands with enhanced error handling
        try:
            synced = await self.tree.sync()
            logging.info(f"🔄 Synced {len(synced)} slash commands globally")
        except Exception as e:
            logging.error(f"❌ Failed to sync slash commands: {e}")
        
        # Startup summary
        logging.info(f"🐼 Panda Bot Setup Complete:")
        logging.info(f"   └ Loaded: {loaded_cogs}/{len(cogs_to_load)} cogs")
        if failed_cogs:
            logging.warning(f"   └ Failed cogs: {len(failed_cogs)}")
            for failed in failed_cogs:
                logging.warning(f"     • {failed}")
    
    async def on_ready(self):
        """Enhanced ready event with detailed status"""
        print("\n" + "="*50)
        print("🐼 PANDA BOT IS READY!")
        print("="*50)
        print(f"Bot Name: {self.user}")
        print(f"Bot ID: {self.user.id}")
        print(f"Guilds: {len(self.guilds)}")
        print(f"Users: {sum(guild.member_count for guild in self.guilds)}")
        print(f"Latency: {round(self.latency * 1000)}ms")
        print(f"Started: {self.startup_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("Commands: All slash commands (/) ready!")
        print("="*50 + "\n")
        
        # Set bot status
        try:
            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name="pandas play! | /pandahelp"
            )
            await self.change_presence(activity=activity, status=discord.Status.online)
        except Exception as e:
            logging.error(f"Failed to set bot status: {e}")
    
    async def on_application_command_error(self, interaction: discord.Interaction, error: Exception):
        """Enhanced global error handler for slash commands"""
        logging.error(f"Slash command error in {interaction.command.name if interaction.command else 'unknown'}: {error}")
        
        # Create error embed
        embed = discord.Embed(
            title="❌ Command Error",
            description="Something went wrong while processing your command.",
            color=0xe74c3c
        )
        embed.add_field(
            name="💡 What you can do:",
            value="• Try the command again\n• Check `/pandahelp` for correct usage\n• Contact support if the issue persists",
            inline=False
        )
        embed.set_footer(text="If this keeps happening, let the bot owner know!")
        
        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception:
            # Last resort - try to send a simple message
            try:
                await interaction.followup.send("❌ An error occurred. Please try again.", ephemeral=True)
            except Exception:
                pass  # Give up gracefully
    
    async def on_guild_join(self, guild: discord.Guild):
        """Welcome message when bot joins a new server"""
        logging.info(f"🎉 Joined new guild: {guild.name} (ID: {guild.id})")
        
        # Try to send welcome message
        welcome_embed = discord.Embed(
            title="🐼 Hello! Panda Bot is here!",
            description="Thanks for adding me to your server! I'm here to bring adorable pandas and fun adoption gameplay!",
            color=0x2ecc71
        )
        welcome_embed.add_field(
            name="🚀 Get Started",
            value="• Use `/pandahelp` to see all commands\n• Try `/panda` for a cute panda image\n• Check out `/adoptlist` to adopt virtual pandas!",
            inline=False
        )
        welcome_embed.add_field(
            name="⚙️ Setup (Optional)",
            value="Admins can use `/pandaconfig` to set up daily panda posts!",
            inline=False
        )
        welcome_embed.set_footer(text="All commands are slash commands (/) - no prefix needed!")
        
        # Try to send to system channel or first available channel
        channel = guild.system_channel
        if not channel:
            for ch in guild.text_channels:
                if ch.permissions_for(guild.me).send_messages:
                    channel = ch
                    break
        
        if channel:
            try:
                await channel.send(embed=welcome_embed)
            except Exception as e:
                logging.warning(f"Could not send welcome message to {guild.name}: {e}")
    
    async def close(self):
        """Enhanced cleanup when bot shuts down"""
        logging.info("🔄 Shutting down Panda Bot...")
        
        # Close any HTTP sessions in cogs
        for cog_name, cog in self.cogs.items():
            try:
                if hasattr(cog, 'panda_api') and hasattr(cog.panda_api, 'close'):
                    await cog.panda_api.close()
                if hasattr(cog, 'http') and hasattr(cog.http, 'close'):
                    await cog.http.close()
            except Exception as e:
                logging.error(f"Error closing resources for {cog_name}: {e}")
        
        await super().close()
        logging.info("👋 Panda Bot shut down complete")

# ==========================================
# 📝 ENHANCED LOGGING SETUP
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Reduce discord.py logging noise
logging.getLogger('discord').setLevel(logging.WARNING)
logging.getLogger('discord.http').setLevel(logging.WARNING)

logger = logging.getLogger("panda-bot")

# ==========================================
# 🚀 MAIN FUNCTION WITH ENHANCED ERROR HANDLING
# ==========================================
def main():
    """Main function to start the bot with comprehensive error handling"""
    
    # Validate token
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("\n" + "="*60)
        print("❌ BOT TOKEN NOT SET!")
        print("="*60)
        print("Please set your bot token in one of these ways:")
        print("")
        print("1. Edit main.py and replace 'YOUR_BOT_TOKEN_HERE' with your actual token")
        print("2. Set the DISCORD_TOKEN environment variable")
        print("")
        print("Get your token from: https://discord.com/developers/applications")
        print("="*60)
        raise SystemExit(1)
    
    # Validate owner ID
    if not BOT_OWNER_ID or BOT_OWNER_ID == 1310134550566797352:
        print("\n⚠️  Warning: BOT_OWNER_ID not set or using default value")
        print("   Owner-only commands might not work for you.")
        print("   Set your Discord user ID in BOT_OWNER_ID variable.\n")
    
    print("\n🐼 Starting Panda Bot...")
    print(f"Token: {'*' * (len(BOT_TOKEN) - 10) + BOT_TOKEN[-10:]}")
    print(f"Owner ID: {BOT_OWNER_ID}\n")
    
    # Create and run bot
    bot = PandaBot()
    
    try:
        bot.run(BOT_TOKEN)
    except discord.LoginFailure:
        logger.error("\n❌ INVALID BOT TOKEN!")
        logger.error("Please check your token and try again.")
        logger.error("Get your token from: https://discord.com/developers/applications")
    except KeyboardInterrupt:
        logger.info("\n🛑 Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"\n💥 Unexpected error: {e}")
        logger.error("If this keeps happening, check your bot setup and permissions.")
    finally:
        logger.info("👋 Goodbye!")

if __name__ == "__main__":
    main()