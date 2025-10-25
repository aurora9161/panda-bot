import discord
from discord.ext import commands
from discord import app_commands
import random
import logging
from datetime import datetime
from utils.adoption_helpers import (
    get_user_currency, add_user_currency, subtract_user_currency,
    get_available_pandas, get_panda_by_id, adopt_panda,
    get_user_pandas, update_panda_stats
)

logger = logging.getLogger(__name__)

class AdoptionSystem(commands.Cog):
    """Panda adoption system commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="adopt", description="Adopt a panda from the adoption center")
    @app_commands.describe(panda_id="ID of the panda to adopt (use /adoptlist to see available pandas)")
    async def adopt_cmd(self, interaction: discord.Interaction, panda_id: str):
        await interaction.response.defer()
        try:
            user_id = str(interaction.user.id)
            panda = get_panda_by_id(panda_id)
            
            if not panda:
                await interaction.followup.send("❌ Panda not found! Use `/adoptlist` to see available pandas.")
                return
                
            if not panda["available"]:
                await interaction.followup.send(f"❌ {panda['name']} has already been adopted!")
                return
                
            user_currency = get_user_currency(user_id)
            if user_currency < panda["adoption_fee"]:
                await interaction.followup.send(f"❌ You need {panda['adoption_fee']} bamboo coins to adopt {panda['name']}. You have {user_currency}. Use `/work` to earn more!")
                return
                
            # Check if user already has 3 pandas (limit)
            user_pandas = get_user_pandas(user_id)
            if len(user_pandas) >= 3:
                await interaction.followup.send("❌ You can only adopt up to 3 pandas at a time!")
                return
                
            # Process adoption
            if subtract_user_currency(user_id, panda["adoption_fee"]) and adopt_panda(user_id, panda_id):
                embed = discord.Embed(
                    title="🎉 Adoption Successful!",
                    description=f"Congratulations! You've adopted **{panda['name']}**!",
                    color=0x2ecc71
                )
                embed.add_field(name="Name", value=panda["name"], inline=True)
                embed.add_field(name="Age", value=panda["age"], inline=True)
                embed.add_field(name="Personality", value=panda["personality"], inline=True)
                embed.add_field(name="Favorite Food", value=panda["favorite_food"], inline=True)
                embed.add_field(name="Special Trait", value=panda["special_trait"], inline=True)
                embed.add_field(name="Adoption Fee", value=f"{panda['adoption_fee']} bamboo coins", inline=True)
                embed.add_field(name="Remaining Currency", value=f"{get_user_currency(user_id)} bamboo coins", inline=False)
                embed.set_thumbnail(url=panda["image_url"])
                embed.set_footer(text="Use /mypandas to see all your adopted pandas!")
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send("❌ Adoption failed. Please try again.")
                
        except Exception as e:
            logger.error(f"/adopt error: {e}")
            await interaction.followup.send("Unexpected error occurred.")
    
    @app_commands.command(name="adoptlist", description="View all available pandas for adoption")
    async def adoptlist_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            available_pandas = get_available_pandas()
            
            if not available_pandas:
                await interaction.followup.send("😢 No pandas are currently available for adoption. Check back later!")
                return
                
            embed = discord.Embed(
                title="🐼 Panda Adoption Center",
                description="Available pandas looking for loving homes!",
                color=0x3498db
            )
            
            for panda in available_pandas[:5]:  # Show first 5
                embed.add_field(
                    name=f"{panda['name']} (ID: {panda['id']})",
                    value=f"**Age:** {panda['age']}\n**Personality:** {panda['personality']}\n**Fee:** {panda['adoption_fee']} bamboo coins",
                    inline=True
                )
                
            embed.set_footer(text="Use /adopt <panda_id> to adopt a panda!")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"/adoptlist error: {e}")
            await interaction.followup.send("Unexpected error occurred.")
    
    @app_commands.command(name="mypandas", description="View your adopted pandas")
    async def mypandas_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            user_id = str(interaction.user.id)
            user_pandas = get_user_pandas(user_id)
            
            if not user_pandas:
                embed = discord.Embed(
                    title="😢 No Pandas Adopted",
                    description="You haven't adopted any pandas yet! Use `/adoptlist` to see available pandas.",
                    color=0xe74c3c
                )
                await interaction.followup.send(embed=embed)
                return
                
            embed = discord.Embed(
                title="🐼 Your Adopted Pandas",
                description=f"You have adopted {len(user_pandas)} panda(s)!",
                color=0x2ecc71
            )
            
            for adopted in user_pandas:
                panda = get_panda_by_id(adopted["panda_id"])
                if panda:
                    adopted_date = datetime.fromisoformat(adopted["adopted_date"]).strftime("%Y-%m-%d")
                    embed.add_field(
                        name=f"{panda['name']} 🐼",
                        value=f"**Happiness:** {adopted.get('happiness', 100)}%\n**Adopted:** {adopted_date}\n**Age:** {panda['age']}",
                        inline=True
                    )
                    
            embed.add_field(
                name="💰 Your Balance",
                value=f"{get_user_currency(user_id)} bamboo coins",
                inline=False
            )
            embed.set_footer(text="Use /feed or /play to interact with your pandas!")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"/mypandas error: {e}")
            await interaction.followup.send("Unexpected error occurred.")
    
    @app_commands.command(name="feed", description="Feed one of your pandas")
    @app_commands.describe(panda_id="ID of the panda to feed")
    async def feed_cmd(self, interaction: discord.Interaction, panda_id: str):
        await interaction.response.defer()
        try:
            user_id = str(interaction.user.id)
            user_pandas = get_user_pandas(user_id)
            
            # Check if user owns this panda
            owned_panda = None
            for adopted in user_pandas:
                if adopted["panda_id"] == panda_id:
                    owned_panda = adopted
                    break
                    
            if not owned_panda:
                await interaction.followup.send("❌ You don't own a panda with that ID! Use `/mypandas` to see your pandas.")
                return
                
            panda_info = get_panda_by_id(panda_id)
            if not panda_info:
                await interaction.followup.send("❌ Panda data not found!")
                return
                
            # Check if recently fed (cooldown)
            last_fed = datetime.fromisoformat(owned_panda["last_fed"])
            time_since_fed = datetime.utcnow() - last_fed
            if time_since_fed.total_seconds() < 3600:  # 1 hour cooldown
                minutes_left = int((3600 - time_since_fed.total_seconds()) / 60)
                await interaction.followup.send(f"🍽️ {panda_info['name']} is not hungry yet! Wait {minutes_left} more minutes.")
                return
                
            # Feed the panda
            happiness_gain = random.randint(5, 15)
            new_happiness = min(100, owned_panda.get("happiness", 100) + happiness_gain)
            
            update_panda_stats(user_id, panda_id, "happiness", new_happiness)
            update_panda_stats(user_id, panda_id, "last_fed", datetime.utcnow().isoformat())
            
            # Give user some coins as reward
            coins_earned = random.randint(5, 10)
            add_user_currency(user_id, coins_earned)
            
            embed = discord.Embed(
                title="🍃 Feeding Time!",
                description=f"You fed **{panda_info['name']}** some delicious {panda_info['favorite_food']}!",
                color=0x27ae60
            )
            embed.add_field(name="Happiness", value=f"{new_happiness}% (+{happiness_gain}%)", inline=True)
            embed.add_field(name="Coins Earned", value=f"+{coins_earned} bamboo coins", inline=True)
            embed.add_field(name="Your Balance", value=f"{get_user_currency(user_id)} bamboo coins", inline=True)
            embed.set_thumbnail(url=panda_info["image_url"])
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"/feed error: {e}")
            await interaction.followup.send("Unexpected error occurred.")
    
    @app_commands.command(name="play", description="Play with one of your pandas")
    @app_commands.describe(panda_id="ID of the panda to play with")
    async def play_cmd(self, interaction: discord.Interaction, panda_id: str):
        await interaction.response.defer()
        try:
            user_id = str(interaction.user.id)
            user_pandas = get_user_pandas(user_id)
            
            # Check if user owns this panda
            owned_panda = None
            for adopted in user_pandas:
                if adopted["panda_id"] == panda_id:
                    owned_panda = adopted
                    break
                    
            if not owned_panda:
                await interaction.followup.send("❌ You don't own a panda with that ID! Use `/mypandas` to see your pandas.")
                return
                
            panda_info = get_panda_by_id(panda_id)
            if not panda_info:
                await interaction.followup.send("❌ Panda data not found!")
                return
                
            # Check if recently played (cooldown)
            last_played = datetime.fromisoformat(owned_panda["last_played"])
            time_since_played = datetime.utcnow() - last_played
            if time_since_played.total_seconds() < 2700:  # 45 minute cooldown
                minutes_left = int((2700 - time_since_played.total_seconds()) / 60)
                await interaction.followup.send(f"🎮 {panda_info['name']} is tired from playing! Wait {minutes_left} more minutes.")
                return
                
            # Play with the panda
            happiness_gain = random.randint(10, 20)
            new_happiness = min(100, owned_panda.get("happiness", 100) + happiness_gain)
            
            update_panda_stats(user_id, panda_id, "happiness", new_happiness)
            update_panda_stats(user_id, panda_id, "last_played", datetime.utcnow().isoformat())
            
            # Give user some coins as reward
            coins_earned = random.randint(8, 15)
            add_user_currency(user_id, coins_earned)
            
            play_activities = [
                f"rolled around with {panda_info['name']}!",
                f"played hide and seek with {panda_info['name']}!",
                f"had a bamboo stick tug-of-war with {panda_info['name']}!",
                f"watched {panda_info['name']} do adorable tumbles!",
                f"gave {panda_info['name']} belly rubs!"
            ]
            
            embed = discord.Embed(
                title="🎮 Playtime!",
                description=f"You {random.choice(play_activities)}",
                color=0xf39c12
            )
            embed.add_field(name="Happiness", value=f"{new_happiness}% (+{happiness_gain}%)", inline=True)
            embed.add_field(name="Coins Earned", value=f"+{coins_earned} bamboo coins", inline=True)
            embed.add_field(name="Your Balance", value=f"{get_user_currency(user_id)} bamboo coins", inline=True)
            embed.set_thumbnail(url=panda_info["image_url"])
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"/play error: {e}")
            await interaction.followup.send("Unexpected error occurred.")

async def setup(bot):
    await bot.add_cog(AdoptionSystem(bot))