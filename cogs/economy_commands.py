import discord
from discord.ext import commands
from discord import app_commands
import random
import logging
from datetime import datetime
from utils.adoption_helpers import get_user_currency, add_user_currency, get_user_pandas
from utils.config import adoption_data, save_adoption_data

logger = logging.getLogger(__name__)

class EconomyCommands(commands.Cog):
    """Economy system commands - work, daily, balance (Festive Edition 🎄)"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="work", description="Work to earn bamboo coins (Festive 🎄)")
    async def work_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            user_id = str(interaction.user.id)
            
            # Simple work system - can work every 30 minutes
            last_work_key = f"last_work_{user_id}"
            current_time = datetime.utcnow()
            
            if last_work_key in adoption_data["user_currency"]:
                last_work_time = datetime.fromisoformat(adoption_data["user_currency"][last_work_key])
                time_since_work = current_time - last_work_time
                if time_since_work.total_seconds() < 1800:  # 30 minute cooldown
                    minutes_left = int((1800 - time_since_work.total_seconds()) / 60)
                    await interaction.followup.send(f"💼 You're tired from working! Rest for {minutes_left} more minutes.")
                    return
                    
            # Work and earn coins
            coins_earned = random.randint(20, 50)
            # Festive random bonus
            if random.random() < 0.15:
                coins_earned += 15
                bonus_note = " (+15 Santa's Helper Bonus 🎅)"
            else:
                bonus_note = ""
            
            add_user_currency(user_id, coins_earned)
            adoption_data["user_currency"][last_work_key] = current_time.isoformat()
            save_adoption_data(adoption_data)
            
            work_jobs = [
                "helped at the bamboo farm",
                "cleaned the panda sanctuary",
                "guided tourists at the zoo",
                "delivered bamboo supplies",
                "assisted panda researchers",
                "organized adoption paperwork",
                "wrapped bamboo bundles for gifting 🎁",
                "decorated the panda habitat with garlands 🎄"
            ]
            
            embed = discord.Embed(
                title="💼 Work Complete!",
                description=f"You {random.choice(work_jobs)} and earned **{coins_earned}** bamboo coins{bonus_note}!",
                color=0x3498db
            )
            embed.add_field(name="Your Balance", value=f"{get_user_currency(user_id)} bamboo coins", inline=True)
            embed.set_footer(text="You can work again in 30 minutes! ❄️")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"/work error: {e}")
            await interaction.followup.send("Unexpected error occurred.")
    
    @app_commands.command(name="daily", description="Claim your daily bamboo coin bonus (Festive 🎄)")
    async def daily_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            user_id = str(interaction.user.id)
            
            # Check last daily claim
            last_daily_key = f"last_daily_{user_id}"
            current_time = datetime.utcnow()
            
            if last_daily_key in adoption_data["user_currency"]:
                last_daily_time = datetime.fromisoformat(adoption_data["user_currency"][last_daily_key])
                time_since_daily = current_time - last_daily_time
                if time_since_daily.total_seconds() < 86400:  # 24 hour cooldown
                    hours_left = int((86400 - time_since_daily.total_seconds()) / 3600)
                    await interaction.followup.send(f"🎁 Daily bonus already claimed! Come back in {hours_left} hours.")
                    return
                    
            # Give daily bonus with festive boost
            daily_bonus = 100 + 25  # +25 Holiday Cheer Bonus
            add_user_currency(user_id, daily_bonus)
            adoption_data["user_currency"][last_daily_key] = current_time.isoformat()
            save_adoption_data(adoption_data)
            
            embed = discord.Embed(
                title="🎁 Daily Bonus! (Festive)",
                description=f"You claimed **{daily_bonus}** bamboo coins! (+25 Holiday Cheer Bonus 🎄)",
                color=0xe74c3c
            )
            embed.add_field(name="Your Balance", value=f"{get_user_currency(user_id)} bamboo coins", inline=True)
            embed.set_footer(text="Season of Giving • Try /christmasgift to share joy 🎁")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"/daily error: {e}")
            await interaction.followup.send("Unexpected error occurred.")
    
    @app_commands.command(name="balance", description="Check your bamboo coin balance (Festive 🎄)")
    async def balance_cmd(self, interaction: discord.Interaction):
        try:
            user_id = str(interaction.user.id)
            balance = get_user_currency(user_id)
            user_pandas = get_user_pandas(user_id)
            
            embed = discord.Embed(
                title="💰 Your Wallet",
                description=f"**{balance} bamboo coins**",
                color=0xf1c40f
            )
            embed.add_field(name="Adopted Pandas", value=f"{len(user_pandas)}/3", inline=True)
            embed.set_footer(text="Warm wishes and bamboo dishes ❄️")
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"/balance error: {e}")
            await interaction.response.send_message("Unexpected error occurred.")

async def setup(bot):
    await bot.add_cog(EconomyCommands(bot))