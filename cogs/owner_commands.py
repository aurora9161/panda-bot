import discord
from discord.ext import commands
from discord import app_commands
import logging
import json
import os
from typing import Optional, List, Dict, Any
from utils.config import config_data, save_config

logger = logging.getLogger(__name__)

# Blacklist data file path
BLACKLIST_PATH = os.getenv("BLACKLIST_PATH", "blacklist_data.json")

# Default blacklist structure
DEFAULT_BLACKLIST = {
    "users": {},  # {user_id: {"reason": str, "timestamp": str, "by": str}}
    "guilds": {},  # {guild_id: {"reason": str, "timestamp": str, "by": str}}
    "global_settings": {
        "block_dm": True,  # Block DMs from blacklisted users
        "auto_leave": True,  # Auto-leave blacklisted guilds
        "log_attempts": True  # Log blocked interactions
    }
}

class OwnerCommands(commands.Cog):
    """Enhanced Owner-only commands with blacklist and status management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.blacklist_data = self.load_blacklist_data()
        
        # Activity type mapping for status command
        self.activity_types = {
            "playing": discord.ActivityType.playing,
            "listening": discord.ActivityType.listening,
            "watching": discord.ActivityType.watching,
            "streaming": discord.ActivityType.streaming,
            "competing": discord.ActivityType.competing
        }
        
        # Status mapping
        self.status_types = {
            "online": discord.Status.online,
            "idle": discord.Status.idle,
            "dnd": discord.Status.dnd,
            "do_not_disturb": discord.Status.dnd,
            "invisible": discord.Status.invisible,
            "offline": discord.Status.offline
        }
    
    def load_blacklist_data(self) -> Dict[str, Any]:
        """Load blacklist data from file"""
        if not os.path.exists(BLACKLIST_PATH):
            self.save_blacklist_data(DEFAULT_BLACKLIST)
            return DEFAULT_BLACKLIST.copy()
        
        try:
            with open(BLACKLIST_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Merge with defaults to ensure all keys exist
                merged = DEFAULT_BLACKLIST.copy()
                if data:
                    merged["users"] = data.get("users", {})
                    merged["guilds"] = data.get("guilds", {})
                    merged["global_settings"] = {**merged["global_settings"], **data.get("global_settings", {})}
                return merged
        except Exception as e:
            logger.error(f"Failed to load blacklist data: {e}. Using defaults.")
            return DEFAULT_BLACKLIST.copy()
    
    def save_blacklist_data(self, data: Dict[str, Any]) -> bool:
        """Save blacklist data to file"""
        try:
            tmp_path = f"{BLACKLIST_PATH}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, BLACKLIST_PATH)
            self.blacklist_data = data  # Update cached data
            return True
        except Exception as e:
            logger.error(f"Failed to save blacklist data: {e}")
            return False
    
    async def is_owner_user(self, interaction: discord.Interaction) -> bool:
        """Enhanced owner check with multiple fallbacks"""
        user_id = interaction.user.id
        
        try:
            # Check application owner
            app = await self.bot.application_info()
            if app.owner and user_id == app.owner.id:
                return True
            
            # Check team owner if bot is owned by team
            if hasattr(app, 'team') and app.team:
                if user_id == app.team.owner.id:
                    return True
                # Check team members with owner-level permissions
                for member in app.team.members:
                    if member.user.id == user_id and member.role in ['admin', 'developer']:
                        return True
        except Exception as e:
            logger.warning(f"Could not fetch application info: {e}")
        
        # Check bot owner ID from main.py
        if hasattr(self.bot, 'owner_id') and self.bot.owner_id and user_id == self.bot.owner_id:
            return True
        
        # Fallback: check if user is in bot's owner_ids (discord.py feature)
        if hasattr(self.bot, 'owner_ids') and self.bot.owner_ids and user_id in self.bot.owner_ids:
            return True
        
        return False
    
    async def is_blacklisted_user(self, user_id: int) -> bool:
        """Check if user is blacklisted"""
        return str(user_id) in self.blacklist_data["users"]
    
    async def is_blacklisted_guild(self, guild_id: int) -> bool:
        """Check if guild is blacklisted"""
        return str(guild_id) in self.blacklist_data["guilds"]
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Handle blacklist for prefix commands"""
        if isinstance(error, commands.CommandError):
            if await self.is_blacklisted_user(ctx.author.id):
                logger.info(f"Blocked command from blacklisted user {ctx.author.id} in guild {ctx.guild.id if ctx.guild else 'DM'}")
                return  # Silently ignore
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Handle blacklist for slash commands"""
        if interaction.type == discord.InteractionType.application_command:
            # Skip owner commands to prevent lockout
            if interaction.command and interaction.command.name.startswith('pandaowner'):
                return
            
            user_id = interaction.user.id
            guild_id = interaction.guild.id if interaction.guild else None
            
            # Check user blacklist
            if await self.is_blacklisted_user(user_id):
                if self.blacklist_data["global_settings"]["log_attempts"]:
                    logger.info(f"Blocked interaction from blacklisted user {user_id} in guild {guild_id or 'DM'}")
                try:
                    embed = discord.Embed(
                        title="🚫 Access Denied",
                        description="You are currently restricted from using this bot.",
                        color=0xe74c3c
                    )
                    embed.set_footer(text="If you believe this is an error, contact the bot owner.")
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                except Exception:
                    pass  # Fail silently
                return
            
            # Check guild blacklist (only for guild interactions)
            if guild_id and await self.is_blacklisted_guild(guild_id):
                if self.blacklist_data["global_settings"]["log_attempts"]:
                    logger.info(f"Blocked interaction in blacklisted guild {guild_id}")
                try:
                    embed = discord.Embed(
                        title="🚫 Server Restricted",
                        description="This server is restricted from using this bot.",
                        color=0xe74c3c
                    )
                    embed.set_footer(text="Server administrators should contact the bot owner.")
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                except Exception:
                    pass
                return
    
    # ==========================================
    # 🚫 BLACKLIST MANAGEMENT COMMANDS
    # ==========================================
    
    @app_commands.command(name="blacklist-user", description="[Owner] Add user to blacklist")
    @app_commands.describe(
        user="User to blacklist",
        reason="Reason for blacklisting (optional)"
    )
    async def blacklist_user(self, interaction: discord.Interaction, user: discord.User, reason: Optional[str] = "No reason provided"):
        """Add a user to the blacklist"""
        if not await self.is_owner_user(interaction):
            embed = discord.Embed(
                title="🚫 Access Denied",
                description="Only the bot owner can use this command.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        user_id_str = str(user.id)
        
        # Prevent owner from blacklisting themselves
        if await self.is_owner_user(type('MockInteraction', (), {'user': user})()):
            embed = discord.Embed(
                title="❌ Cannot Blacklist Owner",
                description="You cannot blacklist the bot owner or team members.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check if already blacklisted
        if user_id_str in self.blacklist_data["users"]:
            embed = discord.Embed(
                title="⚠️ Already Blacklisted",
                description=f"{user.mention} is already blacklisted.",
                color=0xf39c12
            )
            existing_reason = self.blacklist_data["users"][user_id_str].get("reason", "No reason")
            embed.add_field(name="Current Reason", value=existing_reason, inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Add to blacklist
        import datetime
        self.blacklist_data["users"][user_id_str] = {
            "reason": reason,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "by": str(interaction.user),
            "by_id": interaction.user.id
        }
        
        if self.save_blacklist_data(self.blacklist_data):
            embed = discord.Embed(
                title="🚫 User Blacklisted",
                description=f"Successfully blacklisted {user.mention}",
                color=0xe74c3c
            )
            embed.add_field(name="User ID", value=str(user.id), inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text=f"Blacklisted by {interaction.user} • {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logger.info(f"User {user.id} ({user}) blacklisted by {interaction.user.id} - Reason: {reason}")
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to save blacklist data. Please try again.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="blacklist-guild", description="[Owner] Add server to blacklist")
    @app_commands.describe(
        guild_id="Guild/Server ID to blacklist",
        reason="Reason for blacklisting (optional)"
    )
    async def blacklist_guild(self, interaction: discord.Interaction, guild_id: str, reason: Optional[str] = "No reason provided"):
        """Add a guild to the blacklist"""
        if not await self.is_owner_user(interaction):
            embed = discord.Embed(
                title="🚫 Access Denied",
                description="Only the bot owner can use this command.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Validate guild ID
        try:
            guild_id_int = int(guild_id)
        except ValueError:
            embed = discord.Embed(
                title="❌ Invalid Guild ID",
                description="Please provide a valid numeric guild/server ID.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check if already blacklisted
        if guild_id in self.blacklist_data["guilds"]:
            embed = discord.Embed(
                title="⚠️ Already Blacklisted",
                description=f"Guild ID `{guild_id}` is already blacklisted.",
                color=0xf39c12
            )
            existing_reason = self.blacklist_data["guilds"][guild_id].get("reason", "No reason")
            embed.add_field(name="Current Reason", value=existing_reason, inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Get guild info if bot is in it
        guild_name = "Unknown Server"
        try:
            guild = self.bot.get_guild(guild_id_int)
            if guild:
                guild_name = guild.name
        except Exception:
            pass
        
        # Add to blacklist
        import datetime
        self.blacklist_data["guilds"][guild_id] = {
            "reason": reason,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "by": str(interaction.user),
            "by_id": interaction.user.id,
            "guild_name": guild_name
        }
        
        if self.save_blacklist_data(self.blacklist_data):
            embed = discord.Embed(
                title="🚫 Guild Blacklisted",
                description=f"Successfully blacklisted guild: **{guild_name}**",
                color=0xe74c3c
            )
            embed.add_field(name="Guild ID", value=guild_id, inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.set_footer(text=f"Blacklisted by {interaction.user} • {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Auto-leave if enabled and bot is in guild
            if self.blacklist_data["global_settings"]["auto_leave"]:
                try:
                    guild = self.bot.get_guild(guild_id_int)
                    if guild:
                        await guild.leave()
                        embed.add_field(name="Auto-Leave", value="✅ Left the guild automatically", inline=False)
                        await interaction.edit_original_response(embed=embed)
                except Exception as e:
                    logger.error(f"Failed to auto-leave blacklisted guild {guild_id}: {e}")
            
            logger.info(f"Guild {guild_id} ({guild_name}) blacklisted by {interaction.user.id} - Reason: {reason}")
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to save blacklist data. Please try again.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="unblacklist-user", description="[Owner] Remove user from blacklist")
    @app_commands.describe(user="User to remove from blacklist")
    async def unblacklist_user(self, interaction: discord.Interaction, user: discord.User):
        """Remove a user from the blacklist"""
        if not await self.is_owner_user(interaction):
            embed = discord.Embed(
                title="🚫 Access Denied",
                description="Only the bot owner can use this command.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        user_id_str = str(user.id)
        
        if user_id_str not in self.blacklist_data["users"]:
            embed = discord.Embed(
                title="ℹ️ Not Blacklisted",
                description=f"{user.mention} is not currently blacklisted.",
                color=0x3498db
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Remove from blacklist
        removed_data = self.blacklist_data["users"].pop(user_id_str)
        
        if self.save_blacklist_data(self.blacklist_data):
            embed = discord.Embed(
                title="✅ User Unblacklisted",
                description=f"Successfully removed {user.mention} from blacklist",
                color=0x2ecc71
            )
            embed.add_field(name="Previous Reason", value=removed_data.get("reason", "No reason"), inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logger.info(f"User {user.id} ({user}) removed from blacklist by {interaction.user.id}")
        else:
            # Restore data if save failed
            self.blacklist_data["users"][user_id_str] = removed_data
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to save blacklist data. Please try again.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="unblacklist-guild", description="[Owner] Remove server from blacklist")
    @app_commands.describe(guild_id="Guild/Server ID to remove from blacklist")
    async def unblacklist_guild(self, interaction: discord.Interaction, guild_id: str):
        """Remove a guild from the blacklist"""
        if not await self.is_owner_user(interaction):
            embed = discord.Embed(
                title="🚫 Access Denied",
                description="Only the bot owner can use this command.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Validate guild ID
        try:
            int(guild_id)
        except ValueError:
            embed = discord.Embed(
                title="❌ Invalid Guild ID",
                description="Please provide a valid numeric guild/server ID.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if guild_id not in self.blacklist_data["guilds"]:
            embed = discord.Embed(
                title="ℹ️ Not Blacklisted",
                description=f"Guild ID `{guild_id}` is not currently blacklisted.",
                color=0x3498db
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Remove from blacklist
        removed_data = self.blacklist_data["guilds"].pop(guild_id)
        
        if self.save_blacklist_data(self.blacklist_data):
            guild_name = removed_data.get("guild_name", "Unknown Server")
            embed = discord.Embed(
                title="✅ Guild Unblacklisted",
                description=f"Successfully removed **{guild_name}** from blacklist",
                color=0x2ecc71
            )
            embed.add_field(name="Guild ID", value=guild_id, inline=True)
            embed.add_field(name="Previous Reason", value=removed_data.get("reason", "No reason"), inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logger.info(f"Guild {guild_id} ({guild_name}) removed from blacklist by {interaction.user.id}")
        else:
            # Restore data if save failed
            self.blacklist_data["guilds"][guild_id] = removed_data
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to save blacklist data. Please try again.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="blacklist-list", description="[Owner] View blacklist status")
    @app_commands.describe(list_type="Type of blacklist to view")
    @app_commands.choices(list_type=[
        app_commands.Choice(name="Users", value="users"),
        app_commands.Choice(name="Guilds/Servers", value="guilds"),
        app_commands.Choice(name="Settings", value="settings")
    ])
    async def blacklist_list(self, interaction: discord.Interaction, list_type: str = "users"):
        """View blacklist information"""
        if not await self.is_owner_user(interaction):
            embed = discord.Embed(
                title="🚫 Access Denied",
                description="Only the bot owner can use this command.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if list_type == "users":
            embed = discord.Embed(
                title="🚫 Blacklisted Users",
                description=f"Total: {len(self.blacklist_data['users'])} users",
                color=0xe74c3c
            )
            
            if not self.blacklist_data["users"]:
                embed.add_field(name="No Users", value="No users are currently blacklisted.", inline=False)
            else:
                for user_id, data in list(self.blacklist_data["users"].items())[:10]:  # Limit to 10
                    try:
                        user = self.bot.get_user(int(user_id)) or f"Unknown User ({user_id})"
                        reason = data.get("reason", "No reason")[:100]  # Truncate long reasons
                        timestamp = data.get("timestamp", "Unknown time")[:10]  # Date only
                        embed.add_field(
                            name=f"👤 {user}",
                            value=f"**Reason:** {reason}\n**Date:** {timestamp}",
                            inline=False
                        )
                    except Exception:
                        continue
                
                if len(self.blacklist_data["users"]) > 10:
                    embed.set_footer(text=f"Showing first 10 of {len(self.blacklist_data['users'])} users")
        
        elif list_type == "guilds":
            embed = discord.Embed(
                title="🚫 Blacklisted Guilds",
                description=f"Total: {len(self.blacklist_data['guilds'])} guilds",
                color=0xe74c3c
            )
            
            if not self.blacklist_data["guilds"]:
                embed.add_field(name="No Guilds", value="No guilds are currently blacklisted.", inline=False)
            else:
                for guild_id, data in list(self.blacklist_data["guilds"].items())[:10]:  # Limit to 10
                    guild_name = data.get("guild_name", "Unknown Server")
                    reason = data.get("reason", "No reason")[:100]
                    timestamp = data.get("timestamp", "Unknown time")[:10]
                    embed.add_field(
                        name=f"🏰 {guild_name}",
                        value=f"**ID:** {guild_id}\n**Reason:** {reason}\n**Date:** {timestamp}",
                        inline=False
                    )
                
                if len(self.blacklist_data["guilds"]) > 10:
                    embed.set_footer(text=f"Showing first 10 of {len(self.blacklist_data['guilds'])} guilds")
        
        elif list_type == "settings":
            settings = self.blacklist_data["global_settings"]
            embed = discord.Embed(
                title="⚙️ Blacklist Settings",
                color=0x3498db
            )
            embed.add_field(
                name="🚫 Block DMs",
                value="✅ Enabled" if settings["block_dm"] else "❌ Disabled",
                inline=True
            )
            embed.add_field(
                name="🚪 Auto-Leave Guilds",
                value="✅ Enabled" if settings["auto_leave"] else "❌ Disabled",
                inline=True
            )
            embed.add_field(
                name="📝 Log Attempts",
                value="✅ Enabled" if settings["log_attempts"] else "❌ Disabled",
                inline=True
            )
            embed.add_field(
                name="📊 Statistics",
                value=f"Users: {len(self.blacklist_data['users'])}\nGuilds: {len(self.blacklist_data['guilds'])}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # ==========================================
    # 🎭 CUSTOM STATUS MANAGEMENT COMMANDS
    # ==========================================
    
    @app_commands.command(name="set-status", description="[Owner] Change bot's status and activity")
    @app_commands.describe(
        activity_type="Type of activity (playing, watching, listening, streaming, competing)",
        activity_text="Text to display in the activity",
        status="Bot's online status (online, idle, dnd, invisible)",
        streaming_url="Twitch/YouTube URL (only for streaming activity)"
    )
    @app_commands.choices(activity_type=[
        app_commands.Choice(name="🎮 Playing", value="playing"),
        app_commands.Choice(name="👀 Watching", value="watching"),
        app_commands.Choice(name="🎵 Listening", value="listening"),
        app_commands.Choice(name="📺 Streaming", value="streaming"),
        app_commands.Choice(name="🏆 Competing", value="competing")
    ])
    @app_commands.choices(status=[
        app_commands.Choice(name="🟢 Online", value="online"),
        app_commands.Choice(name="🟡 Idle", value="idle"),
        app_commands.Choice(name="🔴 Do Not Disturb", value="dnd"),
        app_commands.Choice(name="⚫ Invisible", value="invisible")
    ])
    async def set_status(self, 
                        interaction: discord.Interaction, 
                        activity_type: str, 
                        activity_text: str, 
                        status: str = "online",
                        streaming_url: Optional[str] = None):
        """Set bot's custom status and activity"""
        if not await self.is_owner_user(interaction):
            embed = discord.Embed(
                title="🚫 Access Denied",
                description="Only the bot owner can use this command.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            # Validate activity type
            if activity_type not in self.activity_types:
                raise ValueError(f"Invalid activity type: {activity_type}")
            
            # Validate status
            if status not in self.status_types:
                raise ValueError(f"Invalid status: {status}")
            
            # Create activity object
            activity_obj = None
            if activity_text:  # Only create activity if text is provided
                if activity_type == "streaming":
                    if not streaming_url:
                        embed = discord.Embed(
                            title="❌ Missing Streaming URL",
                            description="Streaming activity requires a Twitch or YouTube URL.",
                            color=0xe74c3c
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
                    
                    # Validate streaming URL
                    if not (streaming_url.startswith("https://twitch.tv/") or 
                           streaming_url.startswith("https://www.twitch.tv/") or
                           streaming_url.startswith("https://youtube.com/") or
                           streaming_url.startswith("https://www.youtube.com/")):
                        embed = discord.Embed(
                            title="❌ Invalid Streaming URL",
                            description="Please provide a valid Twitch or YouTube URL.",
                            color=0xe74c3c
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
                    
                    activity_obj = discord.Streaming(
                        name=activity_text,
                        url=streaming_url
                    )
                else:
                    activity_obj = discord.Activity(
                        type=self.activity_types[activity_type],
                        name=activity_text
                    )
            
            # Get status object
            status_obj = self.status_types[status]
            
            # Apply the status change
            await self.bot.change_presence(activity=activity_obj, status=status_obj)
            
            # Create success embed
            embed = discord.Embed(
                title="✅ Status Updated Successfully",
                color=0x2ecc71
            )
            
            # Add activity info
            if activity_obj:
                activity_display = f"{activity_type.title()}: {activity_text}"
                if activity_type == "streaming" and streaming_url:
                    activity_display += f"\n🔗 [Stream Link]({streaming_url})"
                embed.add_field(name="🎭 Activity", value=activity_display, inline=False)
            else:
                embed.add_field(name="🎭 Activity", value="No activity set", inline=False)
            
            # Add status info
            status_emojis = {
                "online": "🟢",
                "idle": "🟡", 
                "dnd": "🔴",
                "invisible": "⚫"
            }
            embed.add_field(
                name="📶 Status", 
                value=f"{status_emojis.get(status, '❓')} {status.replace('_', ' ').title()}", 
                inline=True
            )
            
            embed.set_footer(text=f"Status changed by {interaction.user}")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logger.info(f"Bot status changed by {interaction.user.id}: {activity_type} '{activity_text}' - {status}")
        
        except Exception as e:
            logger.error(f"Error setting bot status: {e}")
            embed = discord.Embed(
                title="❌ Status Update Failed",
                description=f"Failed to update bot status: {str(e)[:100]}",
                color=0xe74c3c
            )
            embed.add_field(
                name="💡 Tip", 
                value="Make sure all parameters are valid and try again.",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="clear-status", description="[Owner] Clear bot's activity (keep status)")
    @app_commands.describe(status="Optional: Change status while clearing activity")
    @app_commands.choices(status=[
        app_commands.Choice(name="🟢 Online", value="online"),
        app_commands.Choice(name="🟡 Idle", value="idle"),
        app_commands.Choice(name="🔴 Do Not Disturb", value="dnd"),
        app_commands.Choice(name="⚫ Invisible", value="invisible")
    ])
    async def clear_status(self, interaction: discord.Interaction, status: Optional[str] = None):
        """Clear bot's activity and optionally change status"""
        if not await self.is_owner_user(interaction):
            embed = discord.Embed(
                title="🚫 Access Denied",
                description="Only the bot owner can use this command.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            # Determine status to use
            if status:
                if status not in self.status_types:
                    raise ValueError(f"Invalid status: {status}")
                status_obj = self.status_types[status]
            else:
                status_obj = discord.Status.online  # Default to online
                status = "online"
            
            # Clear activity (set to None)
            await self.bot.change_presence(activity=None, status=status_obj)
            
            embed = discord.Embed(
                title="✅ Activity Cleared",
                description="Bot activity has been cleared successfully.",
                color=0x2ecc71
            )
            
            status_emojis = {
                "online": "🟢",
                "idle": "🟡", 
                "dnd": "🔴",
                "invisible": "⚫"
            }
            
            embed.add_field(
                name="📶 Status",
                value=f"{status_emojis.get(status, '🟢')} {status.replace('_', ' ').title()}",
                inline=True
            )
            embed.set_footer(text=f"Activity cleared by {interaction.user}")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logger.info(f"Bot activity cleared by {interaction.user.id}, status set to {status}")
        
        except Exception as e:
            logger.error(f"Error clearing bot status: {e}")
            embed = discord.Embed(
                title="❌ Clear Status Failed",
                description=f"Failed to clear bot activity: {str(e)[:100]}",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # ==========================================
    # 📊 EXISTING OWNER COMMANDS (Enhanced)
    # ==========================================
    
    @app_commands.command(name="pandaownerreload", description="[Owner] Reload slash commands")
    async def owner_reload(self, interaction: discord.Interaction):
        """Reload slash commands with enhanced feedback"""
        if not await self.is_owner_user(interaction):
            embed = discord.Embed(
                title="🚫 Access Denied",
                description="Only the bot owner can use this command.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Sync commands
            synced = await self.bot.tree.sync()
            
            embed = discord.Embed(
                title="🔄 Commands Reloaded",
                description=f"Successfully synchronized {len(synced)} slash commands.",
                color=0x2ecc71
            )
            embed.add_field(
                name="📊 Details",
                value=f"• Global Commands: {len(synced)}\n• Reload Time: <t:{int(discord.utils.utcnow().timestamp())}:R>",
                inline=False
            )
            embed.set_footer(text=f"Reloaded by {interaction.user}")
            
            await interaction.followup.send(embed=embed)
            logger.info(f"Commands reloaded by {interaction.user.id}: {len(synced)} commands synced")
        
        except Exception as e:
            logger.error(f"/pandaownerreload error: {e}")
            embed = discord.Embed(
                title="❌ Reload Failed",
                description=f"Failed to reload commands: {str(e)[:100]}",
                color=0xe74c3c
            )
            try:
                await interaction.followup.send(embed=embed)
            except:
                await interaction.response.send_message(embed=embed, ephemeral=True)
    
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
        """Enhanced daily settings configuration"""
        if not await self.is_owner_user(interaction):
            embed = discord.Embed(
                title="🚫 Access Denied",
                description="Only the bot owner can use this command.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        changes = []
        try:
            if channel:
                # Check bot permissions in channel
                perms = channel.permissions_for(channel.guild.me)
                if not (perms.send_messages and perms.embed_links):
                    embed = discord.Embed(
                        title="⚠️ Insufficient Permissions",
                        description=f"I need Send Messages and Embed Links permissions in {channel.mention}.",
                        color=0xf39c12
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                
                config_data["daily_channel_id"] = channel.id
                changes.append(f"📍 Channel → {channel.mention}")
            
            if time_str:
                # Validate time format
                try:
                    hour, minute = map(int, time_str.split(":"))
                    if not (0 <= hour <= 23 and 0 <= minute <= 59):
                        raise ValueError("Invalid time range")
                except (ValueError, IndexError):
                    embed = discord.Embed(
                        title="❌ Invalid Time Format",
                        description="Please use HH:MM format (e.g., 14:30 for 2:30 PM UTC).",
                        color=0xe74c3c
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                
                config_data["daily_time"] = time_str
                changes.append(f"⏰ Time → {time_str} UTC")
                
                # Restart daily task if running
                daily_cog = self.bot.get_cog("DailyTasks")
                if daily_cog and hasattr(daily_cog, 'daily_panda_task') and daily_cog.daily_panda_task.is_running():
                    daily_cog.daily_panda_task.restart()
                    changes.append("🔄 Task restarted")
            
            if enabled is not None:
                config_data["enabled"] = enabled
                status_text = "✅ Enabled" if enabled else "❌ Disabled"
                changes.append(f"🎛️ Daily Posts → {status_text}")
                
                # Start/stop daily task
                daily_cog = self.bot.get_cog("DailyTasks")
                if daily_cog and hasattr(daily_cog, 'daily_panda_task'):
                    if enabled:
                        if config_data.get("daily_channel_id") and not daily_cog.daily_panda_task.is_running():
                            daily_cog.daily_panda_task.start()
                            changes.append("▶️ Task started")
                    else:
                        if daily_cog.daily_panda_task.is_running():
                            daily_cog.daily_panda_task.cancel()
                            changes.append("⏹️ Task stopped")
            
            # Save configuration
            save_config(config_data)
            
            if not changes:
                embed = discord.Embed(
                    title="ℹ️ No Changes",
                    description="No configuration changes were provided.",
                    color=0x3498db
                )
            else:
                embed = discord.Embed(
                    title="✅ Configuration Updated",
                    description="Daily panda settings have been updated successfully.",
                    color=0x2ecc71
                )
                embed.add_field(
                    name="📝 Changes Made",
                    value="\n".join(changes),
                    inline=False
                )
            
            embed.set_footer(text=f"Updated by {interaction.user}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"/pandaownerset error: {e}")
            embed = discord.Embed(
                title="❌ Configuration Error",
                description=f"Failed to update settings: {str(e)[:100]}",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="pandaownerstatus", description="[Owner] Comprehensive bot status")
    async def owner_status(self, interaction: discord.Interaction):
        """Enhanced detailed bot status for owners"""
        if not await self.is_owner_user(interaction):
            embed = discord.Embed(
                title="🚫 Access Denied",
                description="Only the bot owner can use this command.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            embed = discord.Embed(
                title="👑 Comprehensive Owner Status", 
                description="Complete bot status and statistics",
                color=0x2e86c1
            )
            
            # Bot Information
            embed.add_field(
                name="🤖 Bot Information",
                value=f"**Name:** {self.bot.user}\n**ID:** {self.bot.user.id}\n**Latency:** {round(self.bot.latency * 1000)}ms",
                inline=True
            )
            
            # Server Statistics
            total_members = sum(guild.member_count for guild in self.bot.guilds)
            embed.add_field(
                name="📊 Server Stats",
                value=f"**Guilds:** {len(self.bot.guilds)}\n**Total Members:** {total_members:,}\n**Shards:** {self.bot.shard_count or 1}",
                inline=True
            )
            
            # Daily Task Status
            ch = f"<#{config_data['daily_channel_id']}>" if config_data.get("daily_channel_id") else "❌ Not set"
            daily_time = config_data.get("daily_time", "12:00")
            daily_enabled = "✅ Yes" if config_data.get("enabled") else "❌ No"
            
            embed.add_field(
                name="🐼 Daily Panda Settings",
                value=f"**Channel:** {ch}\n**Time (UTC):** {daily_time}\n**Enabled:** {daily_enabled}",
                inline=False
            )
            
            # Daily Task Runtime Status
            daily_cog = self.bot.get_cog("DailyTasks")
            if daily_cog and hasattr(daily_cog, 'daily_panda_task'):
                task_running = "✅ Running" if daily_cog.daily_panda_task.is_running() else "❌ Stopped"
                embed.add_field(
                    name="⚙️ Task Runtime Status",
                    value=f"**Daily Task:** {task_running}",
                    inline=True
                )
                
                # Next execution time
                if daily_cog.daily_panda_task.is_running() and config_data.get("enabled"):
                    nxt = daily_cog.daily_panda_task.next_iteration
                    if nxt:
                        embed.add_field(
                            name="⏰ Next Delivery",
                            value=f"<t:{int(nxt.timestamp())}:R>\n<t:{int(nxt.timestamp())}:F>",
                            inline=True
                        )
            
            # Blacklist Statistics
            blacklisted_users = len(self.blacklist_data["users"])
            blacklisted_guilds = len(self.blacklist_data["guilds"])
            embed.add_field(
                name="🚫 Blacklist Stats",
                value=f"**Users:** {blacklisted_users}\n**Guilds:** {blacklisted_guilds}",
                inline=True
            )
            
            # System Information
            if hasattr(self.bot, 'startup_time') and self.bot.startup_time:
                uptime_seconds = (discord.utils.utcnow() - self.bot.startup_time).total_seconds()
                uptime_str = f"<t:{int(self.bot.startup_time.timestamp())}:R>"
            else:
                uptime_str = "Unknown"
            
            embed.add_field(
                name="🚀 System Status",
                value=f"**Uptime:** {uptime_str}\n**Commands:** {len(self.bot.tree.get_commands())} slash",
                inline=True
            )
            
            # Current Status
            activity = self.bot.activity
            if activity:
                activity_text = f"{activity.type.name.title()}: {activity.name}"
                if hasattr(activity, 'url') and activity.url:
                    activity_text += f" ([Link]({activity.url}))"
            else:
                activity_text = "No activity set"
            
            status_emojis = {
                discord.Status.online: "🟢 Online",
                discord.Status.idle: "🟡 Idle",
                discord.Status.dnd: "🔴 Do Not Disturb",
                discord.Status.invisible: "⚫ Invisible",
                discord.Status.offline: "⚫ Offline"
            }
            status_text = status_emojis.get(self.bot.status, "❓ Unknown")
            
            embed.add_field(
                name="🎭 Current Presence",
                value=f"**Status:** {status_text}\n**Activity:** {activity_text}",
                inline=False
            )
            
            embed.set_footer(text="Owner-only comprehensive diagnostic view")
            embed.timestamp = discord.utils.utcnow()
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"/pandaownerstatus error: {e}")
            embed = discord.Embed(
                title="❌ Status Error",
                description=f"Failed to generate owner status: {str(e)[:100]}",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(OwnerCommands(bot))