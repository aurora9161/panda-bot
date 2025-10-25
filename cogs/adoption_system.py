import discord
from discord.ext import commands
from discord import app_commands
import random
import logging
from datetime import datetime, timedelta
from utils.adoption_helpers import (
    get_user_currency, add_user_currency, subtract_user_currency,
    get_available_pandas, get_panda_by_id, adopt_panda,
    get_user_pandas, update_panda_stats
)

logger = logging.getLogger(__name__)

class AdoptionSystem(commands.Cog):
    """🐼 Enhanced Panda Adoption System with Advanced Features"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Enhanced interaction messages for better UX
        self.feed_activities = [
            "munched happily on fresh {}",
            "devoured the delicious {} with joy",
            "carefully savored every bite of {}",
            "rolled around while eating {}",
            "shared {} with their favorite toy",
            "ate {} while purring contentedly",
            "enjoyed {} in the sunshine",
            "had a feast of {} by the bamboo grove"
        ]
        
        self.play_activities = [
            "tumbled around playfully in the grass",
            "played an exciting game of hide and seek",
            "had an epic bamboo stick tug-of-war",
            "practiced adorable somersaults and flips",
            "enjoyed a relaxing belly rub session",
            "climbed trees with amazing agility",
            "splashed around happily in a mini pool",
            "chased colorful butterflies in the garden",
            "built a cozy fort out of bamboo leaves",
            "had a dance party with their favorite music"
        ]
        
        # Happiness level messages with emojis
        self.happiness_events = {
            95: ("🌟", "absolutely glowing with pure happiness!"),
            85: ("✨", "incredibly content and joyful!"),
            75: ("😊", "very happy and full of energy!"),
            65: ("🙂", "content and peacefully relaxed!"),
            50: ("😐", "okay but could use some extra attention!"),
            35: ("😕", "a bit sad and needs more care!"),
            20: ("😢", "quite unhappy and needs immediate love!"),
            0: ("💔", "extremely sad and desperately needs care!")
        }
        
        # Level titles for pandas
        self.level_titles = {
            1: "🍼 Newborn", 2: "🐾 Crawler", 3: "🚶 Walker", 4: "🏃 Runner", 5: "🧗 Climber",
            6: "🎪 Acrobat", 7: "🎭 Performer", 8: "🏆 Champion", 9: "👑 Master", 10: "🌟 Legend",
            11: "⭐ Superstar", 12: "🚀 Cosmic", 13: "🌌 Galactic", 14: "💎 Diamond", 15: "🔥 Mythical"
        }
    
    def get_happiness_message(self, happiness: int) -> tuple[str, str]:
        """Get appropriate happiness emoji and message based on level"""
        for threshold, (emoji, message) in sorted(self.happiness_events.items(), reverse=True):
            if happiness >= threshold:
                return emoji, f"Your panda is {message}"
        return "💔", "Your panda is in critical condition!"
    
    def get_level_title(self, level: int) -> str:
        """Get title for panda level"""
        return self.level_titles.get(min(level, 15), f"🌟 Level {level}")
    
    def calculate_streak_bonus(self, user_id: str, action_type: str) -> tuple[int, str]:
        """Calculate bonus coins and experience based on daily streaks"""
        from utils.config import adoption_data, save_adoption_data
        
        today = datetime.utcnow().date().isoformat()
        streak_key = f"{action_type}_streak_{user_id}"
        last_date_key = f"last_{action_type}_date_{user_id}"
        
        current_streak = adoption_data["user_currency"].get(streak_key, 0)
        last_date = adoption_data["user_currency"].get(last_date_key, "")
        
        if last_date == today:
            return 0, ""  # Already got bonus today
        
        yesterday = (datetime.utcnow().date() - timedelta(days=1)).isoformat()
        
        if last_date == yesterday:
            # Continue streak
            current_streak += 1
        else:
            # Reset streak or start new one
            current_streak = 1
        
        # Update streak data
        adoption_data["user_currency"][streak_key] = current_streak
        adoption_data["user_currency"][last_date_key] = today
        save_adoption_data(adoption_data)
        
        # Calculate bonus based on streak
        if current_streak >= 30:
            bonus = 100
            emoji = "🔥💎"
            message = f"{emoji} LEGENDARY {current_streak} DAY STREAK! Bonus: +{bonus} coins!"
        elif current_streak >= 14:
            bonus = 50
            emoji = "🔥⭐"
            message = f"{emoji} MEGA {current_streak} day streak! Bonus: +{bonus} coins!"
        elif current_streak >= 7:
            bonus = 25
            emoji = "🔥"
            message = f"{emoji} WEEKLY {current_streak} day streak! Bonus: +{bonus} coins!"
        elif current_streak >= 3:
            bonus = 15
            emoji = "⚡"
            message = f"{emoji} {current_streak} day streak! Bonus: +{bonus} coins!"
        elif current_streak == 2:
            bonus = 5
            emoji = "📈"
            message = f"{emoji} {current_streak} day streak! Bonus: +{bonus} coins!"
        else:
            bonus = 0
            message = ""
        
        return bonus, message
    
    def get_adoption_requirements(self, user_id: str) -> tuple[bool, str]:
        """Enhanced adoption requirements checking"""
        user_pandas = get_user_pandas(user_id)
        max_pandas = 3
        
        if len(user_pandas) >= max_pandas:
            return False, f"❌ You've reached the maximum limit of {max_pandas} pandas! Take great care of your current pandas first."
        
        # Calculate care quality requirements
        if user_pandas:
            total_happiness = sum(panda.get('happiness', 100) for panda in user_pandas)
            avg_happiness = total_happiness / len(user_pandas)
            
            if len(user_pandas) >= 2 and avg_happiness < 70:
                return False, f"❌ Your pandas need better care before adopting more!\n**Average happiness:** {avg_happiness:.0f}% (need 70%+)\n💡 Use `/feed` and `/play` to make them happier!"
        
        return True, ""
    
    def format_time_remaining(self, seconds: int) -> str:
        """Format remaining cooldown time in human-readable format"""
        if seconds <= 0:
            return "Ready now! 🟢"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m 🕐"
        else:
            return f"{minutes}m 🕐"
    
    def calculate_level_up(self, current_exp: int, level: int) -> tuple[bool, int]:
        """Calculate if panda should level up and new level"""
        exp_needed = level * 100  # Increased XP requirement
        if current_exp >= exp_needed:
            new_level = level + 1
            return True, new_level
        return False, level
    
    @app_commands.command(name="adopt", description="🐼 Adopt a panda from the adoption center")
    @app_commands.describe(panda_id="ID of the panda to adopt (use /adoptlist to see available pandas)")
    async def adopt_cmd(self, interaction: discord.Interaction, panda_id: str):
        await interaction.response.defer()
        
        try:
            user_id = str(interaction.user.id)
            
            # Enhanced validation with detailed error messages
            panda = get_panda_by_id(panda_id)
            if not panda:
                embed = discord.Embed(
                    title="❌ Panda Not Found",
                    description=f"No panda found with ID: `{panda_id}`",
                    color=0xe74c3c
                )
                embed.add_field(
                    name="💡 What to do:",
                    value="• Use `/adoptlist` to see available pandas\n• Check the panda ID spelling\n• Make sure the panda hasn't been adopted yet",
                    inline=False
                )
                await interaction.followup.send(embed=embed)
                return
            
            if not panda["available"]:
                embed = discord.Embed(
                    title="💕 Already Adopted",
                    description=f"**{panda['name']}** has already found a loving home!",
                    color=0xf39c12
                )
                embed.add_field(
                    name="🐼 Other Options:",
                    value="• Check `/adoptlist` for other available pandas\n• Each panda is unique and special!",
                    inline=False
                )
                embed.set_thumbnail(url=panda["image_url"])
                await interaction.followup.send(embed=embed)
                return
            
            # Check adoption requirements
            can_adopt, requirement_msg = self.get_adoption_requirements(user_id)
            if not can_adopt:
                embed = discord.Embed(
                    title="🚫 Adoption Requirements",
                    description=requirement_msg,
                    color=0xe67e22
                )
                await interaction.followup.send(embed=embed)
                return
            
            user_currency = get_user_currency(user_id)
            if user_currency < panda["adoption_fee"]:
                needed = panda["adoption_fee"] - user_currency
                embed = discord.Embed(
                    title="💰 Insufficient Funds",
                    description=f"**{panda['name']}** needs a loving home!",
                    color=0xf39c12
                )
                embed.add_field(
                    name="💳 Cost Breakdown:",
                    value=f"**Adoption Fee:** {panda['adoption_fee']} 🪙\n**Your Balance:** {user_currency} 🪙\n**Still Need:** {needed} 🪙",
                    inline=True
                )
                embed.add_field(
                    name="💡 Earn More Coins:",
                    value="• `/work` - Earn 20-50 coins\n• `/daily` - Get 100 bonus coins\n• Care for current pandas for rewards!",
                    inline=True
                )
                embed.set_thumbnail(url=panda["image_url"])
                await interaction.followup.send(embed=embed)
                return
            
            # Process adoption with enhanced data
            if subtract_user_currency(user_id, panda["adoption_fee"]) and adopt_panda(user_id, panda_id):
                # Add enhanced adoption data
                user_pandas = get_user_pandas(user_id)
                for adopted in user_pandas:
                    if adopted["panda_id"] == panda_id:
                        # Initialize enhanced stats
                        update_panda_stats(user_id, panda_id, "experience", 0)
                        update_panda_stats(user_id, panda_id, "level", 1)
                        update_panda_stats(user_id, panda_id, "adoption_date", datetime.utcnow().isoformat())
                        update_panda_stats(user_id, panda_id, "favorite_activity", random.choice(["playing", "eating", "sleeping", "climbing", "swimming"]))
                        update_panda_stats(user_id, panda_id, "mood", "excited")
                        update_panda_stats(user_id, panda_id, "total_feeds", 0)
                        update_panda_stats(user_id, panda_id, "total_plays", 0)
                        break
                
                embed = discord.Embed(
                    title="🎉 ADOPTION SUCCESS!",
                    description=f"**Congratulations!** 🎊\n\n🐼 **{panda['name']}** is so excited to have found their forever home with you! They're already settling in and can't wait to start this amazing journey together! 💕",
                    color=0x2ecc71
                )
                
                # Enhanced panda profile display
                embed.add_field(
                    name="📋 Panda Profile",
                    value=f"**Name:** {panda['name']} 🐼\n**Age:** {panda['age']} 🎂\n**Level:** {self.get_level_title(1)}",
                    inline=True
                )
                embed.add_field(
                    name="✨ Personality",
                    value=f"**Trait:** {panda['personality']} 😊\n**Special:** {panda['special_trait']} 🌟\n**Loves:** {panda['favorite_food']} 🎋",
                    inline=True
                )
                embed.add_field(
                    name="💰 Transaction",
                    value=f"**Paid:** {panda['adoption_fee']} 🪙\n**Balance:** {get_user_currency(user_id)} 🪙\n**Status:** Complete ✅",
                    inline=True
                )
                
                embed.set_thumbnail(url=panda["image_url"])
                embed.set_footer(text="💡 Use /feed and /play to bond with your new panda! Check /mypandas to see your panda family.")
                
                await interaction.followup.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="❌ Adoption Failed",
                    description="Something went wrong during the adoption process. This is usually temporary - please try again!",
                    color=0xe74c3c
                )
                embed.add_field(
                    name="🔧 Troubleshooting:",
                    value="• Wait a moment and try again\n• Check your internet connection\n• Contact support if this persists",
                    inline=False
                )
                await interaction.followup.send(embed=embed)
        
        except Exception as e:
            logger.error(f"Adoption error for user {interaction.user.id}: {e}")
            embed = discord.Embed(
                title="🚨 System Error",
                description="An unexpected error occurred during adoption. Our pandas are safe, don't worry!",
                color=0xe74c3c
            )
            embed.add_field(
                name="🔧 Next Steps:",
                value="• Try again in a moment\n• Contact bot support if this continues\n• Your currency is safe!",
                inline=False
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="adoptlist", description="🏠 View all available pandas for adoption")
    async def adoptlist_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            available_pandas = get_available_pandas()
            
            if not available_pandas:
                embed = discord.Embed(
                    title="🏠 Panda Adoption Center",
                    description="🎉 **All our pandas have found loving homes!**\n\nThis is wonderful news! Every panda in our sanctuary is now living happily with their families. 🥰\n\nNew pandas arrive regularly, so check back soon! 🌸",
                    color=0x9b59b6
                )
                embed.add_field(
                    name="💡 While You Wait:",
                    value="• Take excellent care of your current pandas!\n• Use `/mypandas` to check on them\n• Build up your coin balance with `/work` and `/daily`",
                    inline=False
                )
                embed.set_footer(text="🐼 Happy pandas make happy families!")
                await interaction.followup.send(embed=embed)
                return
            
            embed = discord.Embed(
                title="🏠 Panda Adoption Center",
                description=f"🐼 **{len(available_pandas)} adorable pandas** are looking for loving families!\n\nEach panda has their own unique personality, traits, and needs. Choose the one that speaks to your heart! 💕",
                color=0x3498db
            )
            
            # Show detailed info for available pandas
            for i, panda in enumerate(available_pandas[:6]):  # Show up to 6 pandas for readability
                # Personality emoji mapping
                personality_emojis = {
                    "playful": "🎮", "energetic": "⚡", "calm": "😌", "cuddly": "🤗",
                    "shy": "😊", "sweet": "🍯", "brave": "🦸", "adventurous": "🗺️",
                    "gentle": "🕊️", "loving": "💖"
                }
                
                personality_key = next((key for key in personality_emojis.keys() if key in panda['personality'].lower()), "✨")
                personality_emoji = personality_emojis.get(personality_key, "✨")
                
                # Fee indicator
                fee_indicator = "💎" if panda['adoption_fee'] >= 250 else "🪙" if panda['adoption_fee'] >= 150 else "💰"
                
                field_value = (
                    f"**Age:** {panda['age']} 🎂\n"
                    f"**Personality:** {personality_emoji} {panda['personality']}\n"
                    f"**Special Trait:** {panda['special_trait']}\n"
                    f"**Adoption Fee:** {fee_indicator} {panda['adoption_fee']} coins"
                )
                
                embed.add_field(
                    name=f"🐼 {panda['name']} (ID: `{panda['id']}`)",
                    value=field_value,
                    inline=True
                )
            
            if len(available_pandas) > 6:
                embed.add_field(
                    name="📜 More Pandas Available",
                    value=f"Plus **{len(available_pandas) - 6} more pandas** are waiting for homes! 🏡",
                    inline=False
                )
            
            embed.set_footer(text="💡 Use /adopt <panda_id> to adopt! Example: /adopt panda_001")
            await interaction.followup.send(embed=embed)
        
        except Exception as e:
            logger.error(f"Adoptlist error: {e}")
            embed = discord.Embed(
                title="🚨 Loading Error",
                description="Could not load the adoption center right now. Our pandas are safe!",
                color=0xe74c3c
            )
            embed.add_field(
                name="🔧 Try Again:",
                value="• Wait a moment and retry\n• The adoption center will be back soon!",
                inline=False
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="mypandas", description="👨‍👩‍👧‍👦 View your adopted panda family and their stats")
    async def mypandas_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            user_id = str(interaction.user.id)
            user_pandas = get_user_pandas(user_id)
            
            if not user_pandas:
                embed = discord.Embed(
                    title="🏠 Your Panda Family",
                    description="🤗 **Ready to start your panda family?**\n\nYou haven't adopted any pandas yet, but there are so many adorable ones waiting for loving homes! Each panda brings joy, companionship, and lots of fun activities! 🎉",
                    color=0x3498db
                )
                embed.add_field(
                    name="🚀 Get Started:",
                    value="• Use `/adoptlist` to see available pandas\n• Each panda has unique traits and personality\n• Earn coins with `/work` and `/daily` for adoption fees",
                    inline=False
                )
                embed.add_field(
                    name="💡 Panda Care Tips:",
                    value="• Feed your pandas with `/feed` to keep them happy\n• Play with them using `/play` for bonding\n• Higher happiness = better rewards!",
                    inline=False
                )
                embed.set_footer(text="🐼 Every panda deserves a loving family!")
                await interaction.followup.send(embed=embed)
                return
            
            embed = discord.Embed(
                title="👨‍👩‍👧‍👦 Your Panda Family",
                description=f"🐼 You have **{len(user_pandas)}/3** pandas in your loving care!\n\nYour pandas adore you and depend on your care to stay happy and healthy! 💕",
                color=0x2ecc71
            )
            
            total_happiness = 0
            total_level = 0
            
            for adopted in user_pandas:
                panda = get_panda_by_id(adopted["panda_id"])
                if not panda:
                    continue
                
                happiness = adopted.get('happiness', 100)
                level = adopted.get('level', 1)
                experience = adopted.get('experience', 0)
                total_feeds = adopted.get('total_feeds', 0)
                total_plays = adopted.get('total_plays', 0)
                
                total_happiness += happiness
                total_level += level
                
                # Calculate time since adoption
                adoption_date = datetime.fromisoformat(adopted.get("adoption_date", adopted["adopted_date"]))
                days_together = (datetime.utcnow() - adoption_date).days
                
                # Time since last interactions
                last_fed = datetime.fromisoformat(adopted["last_fed"])
                last_played = datetime.fromisoformat(adopted["last_played"])
                
                fed_cooldown = (datetime.utcnow() - last_fed).total_seconds()
                play_cooldown = (datetime.utcnow() - last_played).total_seconds()
                
                # Enhanced status indicators
                if fed_cooldown >= 3600:  # Can feed
                    feed_status = "🍽️ Hungry & ready!"
                else:
                    remaining = int(3600 - fed_cooldown)
                    feed_status = f"😋 Full ({self.format_time_remaining(remaining)})"
                
                if play_cooldown >= 2700:  # Can play
                    play_status = "🎮 Ready to play!"
                else:
                    remaining = int(2700 - play_cooldown)
                    play_status = f"😴 Resting ({self.format_time_remaining(remaining)})"
                
                # Happiness indicator
                happiness_emoji, happiness_msg = self.get_happiness_message(happiness)
                
                # Experience progress
                exp_needed = level * 100
                exp_progress = min(experience, exp_needed)
                progress_bar = "▰" * int(exp_progress / exp_needed * 10) + "▱" * (10 - int(exp_progress / exp_needed * 10))
                
                field_value = (
                    f"**Happiness:** {happiness_emoji} {happiness}%\n"
                    f"**Level:** {self.get_level_title(level)}\n"
                    f"**EXP:** {progress_bar} {experience}/{exp_needed}\n"
                    f"**Days Together:** {days_together} days 📅\n"
                    f"**Feed Status:** {feed_status}\n"
                    f"**Play Status:** {play_status}"
                )
                
                embed.add_field(
                    name=f"🐼 {panda['name']} ({panda['age']})",
                    value=field_value,
                    inline=True
                )
            
            # Enhanced family statistics
            avg_happiness = total_happiness / len(user_pandas)
            avg_level = total_level / len(user_pandas)
            balance = get_user_currency(user_id)
            
            # Family performance rating
            if avg_happiness >= 90:
                family_rating = "🏆 Excellent Family!"
            elif avg_happiness >= 75:
                family_rating = "⭐ Great Family!"
            elif avg_happiness >= 60:
                family_rating = "😊 Good Family!"
            else:
                family_rating = "📈 Growing Family!"
            
            embed.add_field(
                name="📊 Family Overview",
                value=f"**Rating:** {family_rating}\n"
                      f"**Avg Happiness:** {avg_happiness:.1f}%\n"
                      f"**Avg Level:** {avg_level:.1f}\n"
                      f"**Family Size:** {len(user_pandas)}/3 pandas\n"
                      f"**Your Balance:** 💰 {balance} coins",
                inline=False
            )
            
            embed.set_footer(text="💡 Use /feed <panda_id> and /play <panda_id> to interact! Happy pandas give better rewards!")
            await interaction.followup.send(embed=embed)
        
        except Exception as e:
            logger.error(f"MyPandas error for user {interaction.user.id}: {e}")
            embed = discord.Embed(
                title="🚨 Loading Error",
                description="Could not load your panda family right now. Don't worry, your pandas are safe!",
                color=0xe74c3c
            )
            embed.add_field(
                name="🔧 Try Again:",
                value="• Wait a moment and retry\n• Your panda data is securely stored!",
                inline=False
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="feed", description="🍽️ Feed one of your pandas with their favorite food")
    @app_commands.describe(panda_id="ID of the panda to feed")
    async def feed_cmd(self, interaction: discord.Interaction, panda_id: str):
        await interaction.response.defer()
        
        try:
            user_id = str(interaction.user.id)
            user_pandas = get_user_pandas(user_id)
            
            # Find owned panda with better error handling
            owned_panda = None
            for adopted in user_pandas:
                if adopted["panda_id"] == panda_id:
                    owned_panda = adopted
                    break
            
            if not owned_panda:
                embed = discord.Embed(
                    title="❌ Panda Not Found",
                    description=f"You don't own a panda with ID: `{panda_id}`",
                    color=0xe74c3c
                )
                
                if user_pandas:
                    panda_list = "\n".join([f"• {get_panda_by_id(p['panda_id'])['name'] if get_panda_by_id(p['panda_id']) else 'Unknown'} (ID: `{p['panda_id']}`)" for p in user_pandas[:3]])
                    embed.add_field(
                        name="🐼 Your Pandas:",
                        value=panda_list,
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="💡 Get Started:",
                        value="• Use `/adoptlist` to see available pandas\n• Adopt a panda first with `/adopt <panda_id>`",
                        inline=False
                    )
                
                await interaction.followup.send(embed=embed)
                return
            
            panda_info = get_panda_by_id(panda_id)
            if not panda_info:
                embed = discord.Embed(
                    title="🚨 Data Error",
                    description="Panda data temporarily unavailable. Please try again!",
                    color=0xe74c3c
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Enhanced cooldown checking
            last_fed = datetime.fromisoformat(owned_panda["last_fed"])
            time_since_fed = datetime.utcnow() - last_fed
            cooldown_seconds = 3600  # 1 hour
            
            if time_since_fed.total_seconds() < cooldown_seconds:
                remaining_seconds = int(cooldown_seconds - time_since_fed.total_seconds())
                time_remaining = self.format_time_remaining(remaining_seconds)
                
                embed = discord.Embed(
                    title="😋 Panda is Full!",
                    description=f"**{panda_info['name']}** is still happily digesting their last delicious meal! 🥰",
                    color=0xf39c12
                )
                embed.add_field(
                    name="⏰ Next Feeding Time:",
                    value=f"Ready in: **{time_remaining}**\n\nPandas need time to properly digest their bamboo!",
                    inline=True
                )
                embed.add_field(
                    name="💡 What to do now:",
                    value=f"• Try `/play {panda_id}` for fun activities!\n• Check on your other pandas\n• Come back when they're hungry again!",
                    inline=True
                )
                embed.set_thumbnail(url=panda_info["image_url"])
                embed.set_footer(text="Well-fed pandas are happy pandas! 🐼💕")
                await interaction.followup.send(embed=embed)
                return
            
            # Enhanced feeding mechanics with more variety
            base_happiness = random.randint(12, 25)
            level = owned_panda.get('level', 1)
            current_happiness = owned_panda.get("happiness", 100)
            
            # Streak bonus calculation
            streak_bonus_coins, streak_msg = self.calculate_streak_bonus(user_id, "feed")
            
            # Level-based bonuses
            level_bonus = min(level * 2, 15)
            happiness_bonus = 5 if current_happiness < 50 else 0  # Extra bonus for sad pandas
            
            total_happiness_gain = base_happiness + level_bonus + happiness_bonus
            new_happiness = min(100, current_happiness + total_happiness_gain)
            
            # Experience system
            base_exp = random.randint(8, 18)
            bonus_exp = 5 if new_happiness == 100 else 0
            total_exp_gain = base_exp + bonus_exp
            
            current_exp = owned_panda.get('experience', 0)
            new_exp = current_exp + total_exp_gain
            
            # Level up checking
            level_up, new_level = self.calculate_level_up(new_exp, level)
            
            # Update statistics
            total_feeds = owned_panda.get('total_feeds', 0) + 1
            
            # Update panda stats
            update_panda_stats(user_id, panda_id, "happiness", new_happiness)
            update_panda_stats(user_id, panda_id, "last_fed", datetime.utcnow().isoformat())
            update_panda_stats(user_id, panda_id, "experience", new_exp)
            update_panda_stats(user_id, panda_id, "total_feeds", total_feeds)
            if level_up:
                update_panda_stats(user_id, panda_id, "level", new_level)
            
            # Enhanced coin rewards
            base_coins = random.randint(10, 20)
            level_coin_bonus = level * 2
            happiness_coin_bonus = 5 if new_happiness >= 90 else 0
            milestone_bonus = 10 if total_feeds % 10 == 0 else 0  # Every 10 feeds
            level_up_bonus = 25 if level_up else 0
            
            total_coins = base_coins + level_coin_bonus + happiness_coin_bonus + streak_bonus_coins + milestone_bonus + level_up_bonus
            add_user_currency(user_id, total_coins)
            
            # Create rich, engaging response
            activity = random.choice(self.feed_activities).format(panda_info['favorite_food'])
            happiness_emoji, happiness_msg = self.get_happiness_message(new_happiness)
            
            embed = discord.Embed(
                title="🍽️ Feeding Time Success!",
                description=f"**{panda_info['name']}** {activity}! 😋\n\n{happiness_emoji} {happiness_msg}",
                color=0x27ae60
            )
            
            # Stats update section
            level_display = f"{self.get_level_title(level)}" + (f" → {self.get_level_title(new_level)} 🎉" if level_up else "")
            
            embed.add_field(
                name="📈 Panda Growth",
                value=f"**Happiness:** {current_happiness}% → {new_happiness}% (+{total_happiness_gain})\n"
                      f"**Experience:** {current_exp} → {new_exp} (+{total_exp_gain} EXP)\n"
                      f"**Level:** {level_display}\n"
                      f"**Total Feeds:** {total_feeds} 🍽️",
                inline=True
            )
            
            # Rewards breakdown
            reward_breakdown = f"**Base:** +{base_coins} 🪙\n"
            if level_coin_bonus > 0:
                reward_breakdown += f"**Level Bonus:** +{level_coin_bonus} 🪙\n"
            if happiness_coin_bonus > 0:
                reward_breakdown += f"**Happiness Bonus:** +{happiness_coin_bonus} 🪙\n"
            if milestone_bonus > 0:
                reward_breakdown += f"**🎉 Milestone Bonus:** +{milestone_bonus} 🪙\n"
            if level_up_bonus > 0:
                reward_breakdown += f"**🆙 Level Up Bonus:** +{level_up_bonus} 🪙\n"
            if streak_bonus_coins > 0:
                reward_breakdown += f"**🔥 Streak Bonus:** +{streak_bonus_coins} 🪙\n"
            
            reward_breakdown += f"**Total Earned:** +{total_coins} 🪙\n**Your Balance:** {get_user_currency(user_id)} 🪙"
            
            embed.add_field(
                name="💰 Rewards Earned",
                value=reward_breakdown,
                inline=True
            )
            
            # Special messages
            special_messages = []
            if level_up:
                special_messages.append(f"🎊 **LEVEL UP!** {panda_info['name']} is now {self.get_level_title(new_level)}!")
            if streak_msg:
                special_messages.append(streak_msg)
            if total_feeds % 10 == 0:
                special_messages.append(f"🏆 **Feeding Milestone!** You've fed {panda_info['name']} {total_feeds} times!")
            if new_happiness == 100:
                special_messages.append(f"✨ **Perfect Happiness!** {panda_info['name']} couldn't be happier!")
            
            if special_messages:
                embed.add_field(
                    name="🎉 Special Events",
                    value="\n".join(special_messages),
                    inline=False
                )
            
            embed.set_thumbnail(url=panda_info["image_url"])
            embed.set_footer(text=f"💡 Next feeding in 1 hour • Try /play {panda_id} for more fun! • Keep your panda happy for better rewards!")
            
            await interaction.followup.send(embed=embed)
        
        except Exception as e:
            logger.error(f"Feed error for user {interaction.user.id}, panda {panda_id}: {e}")
            embed = discord.Embed(
                title="🚨 Feeding Error",
                description="Something went wrong while feeding your panda. Don't worry, they're still safe and happy!",
                color=0xe74c3c
            )
            embed.add_field(
                name="🔧 Try Again:",
                value="• Wait a moment and retry\n• Check your internet connection\n• Contact support if this continues",
                inline=False
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="play", description="🎮 Play with one of your pandas for fun and bonding")
    @app_commands.describe(panda_id="ID of the panda to play with")
    async def play_cmd(self, interaction: discord.Interaction, panda_id: str):
        await interaction.response.defer()
        
        try:
            user_id = str(interaction.user.id)
            user_pandas = get_user_pandas(user_id)
            
            # Find owned panda
            owned_panda = None
            for adopted in user_pandas:
                if adopted["panda_id"] == panda_id:
                    owned_panda = adopted
                    break
            
            if not owned_panda:
                embed = discord.Embed(
                    title="❌ Panda Not Found",
                    description=f"You don't own a panda with ID: `{panda_id}`",
                    color=0xe74c3c
                )
                
                if user_pandas:
                    panda_list = "\n".join([f"• {get_panda_by_id(p['panda_id'])['name'] if get_panda_by_id(p['panda_id']) else 'Unknown'} (ID: `{p['panda_id']}`)" for p in user_pandas[:3]])
                    embed.add_field(
                        name="🐼 Your Pandas:",
                        value=panda_list,
                        inline=False
                    )
                else:
                    embed.add_field(
                        name="💡 Get Started:",
                        value="• Use `/adoptlist` to see available pandas\n• Adopt a panda first with `/adopt <panda_id>`",
                        inline=False
                    )
                
                await interaction.followup.send(embed=embed)
                return
            
            panda_info = get_panda_by_id(panda_id)
            if not panda_info:
                embed = discord.Embed(
                    title="🚨 Data Error",
                    description="Panda data temporarily unavailable. Please try again!",
                    color=0xe74c3c
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Enhanced cooldown checking
            last_played = datetime.fromisoformat(owned_panda["last_played"])
            time_since_played = datetime.utcnow() - last_played
            cooldown_seconds = 2700  # 45 minutes
            
            if time_since_played.total_seconds() < cooldown_seconds:
                remaining_seconds = int(cooldown_seconds - time_since_played.total_seconds())
                time_remaining = self.format_time_remaining(remaining_seconds)
                
                embed = discord.Embed(
                    title="😴 Panda Needs Rest",
                    description=f"**{panda_info['name']}** is taking a well-deserved nap after all that fun! 💤",
                    color=0xf39c12
                )
                embed.add_field(
                    name="⏰ Next Playtime:",
                    value=f"Ready in: **{time_remaining}**\n\nPandas need rest between play sessions to stay energetic!",
                    inline=True
                )
                embed.add_field(
                    name="💡 What to do now:",
                    value=f"• Try `/feed {panda_id}` if they're hungry!\n• Check on your other pandas\n• Come back when they're rested!",
                    inline=True
                )
                embed.set_thumbnail(url=panda_info["image_url"])
                embed.set_footer(text="Rested pandas play better! 🐼💤")
                await interaction.followup.send(embed=embed)
                return
            
            # Enhanced playing mechanics
            base_happiness = random.randint(15, 30)
            level = owned_panda.get('level', 1)
            current_happiness = owned_panda.get("happiness", 100)
            
            # Streak bonus calculation
            streak_bonus_coins, streak_msg = self.calculate_streak_bonus(user_id, "play")
            
            # Enhanced bonuses
            level_bonus = min(level * 3, 20)
            happiness_bonus = 8 if current_happiness < 60 else 0
            energy_bonus = random.randint(0, 10)  # Random energy burst
            
            total_happiness_gain = base_happiness + level_bonus + happiness_bonus + energy_bonus
            new_happiness = min(100, current_happiness + total_happiness_gain)
            
            # Enhanced experience system (more from playing)
            base_exp = random.randint(15, 25)
            bonus_exp = 10 if new_happiness >= 95 else 5 if new_happiness >= 80 else 0
            perfect_play_bonus = 15 if energy_bonus >= 8 else 0
            
            total_exp_gain = base_exp + bonus_exp + perfect_play_bonus
            current_exp = owned_panda.get('experience', 0)
            new_exp = current_exp + total_exp_gain
            
            # Level up checking
            level_up, new_level = self.calculate_level_up(new_exp, level)
            
            # Update play statistics
            total_plays = owned_panda.get('total_plays', 0) + 1
            
            # Update panda stats
            update_panda_stats(user_id, panda_id, "happiness", new_happiness)
            update_panda_stats(user_id, panda_id, "last_played", datetime.utcnow().isoformat())
            update_panda_stats(user_id, panda_id, "experience", new_exp)
            update_panda_stats(user_id, panda_id, "total_plays", total_plays)
            if level_up:
                update_panda_stats(user_id, panda_id, "level", new_level)
            
            # Enhanced coin rewards (playing gives more coins)
            base_coins = random.randint(15, 25)
            level_coin_bonus = level * 3
            happiness_coin_bonus = 8 if new_happiness >= 90 else 0
            energy_coin_bonus = energy_bonus  # Bonus coins for energy burst
            milestone_bonus = 15 if total_plays % 10 == 0 else 0
            level_up_bonus = 35 if level_up else 0
            perfect_play_coins = 20 if perfect_play_bonus > 0 else 0
            
            total_coins = base_coins + level_coin_bonus + happiness_coin_bonus + energy_coin_bonus + streak_bonus_coins + milestone_bonus + level_up_bonus + perfect_play_coins
            add_user_currency(user_id, total_coins)
            
            # Create engaging response with variety
            activity = random.choice(self.play_activities)
            happiness_emoji, happiness_msg = self.get_happiness_message(new_happiness)
            
            # Special play event messages
            play_events = []
            if energy_bonus >= 8:
                play_events.append("⚡ Your panda had an amazing burst of energy!")
            if perfect_play_bonus > 0:
                play_events.append("🌟 Perfect play session - amazing bonding!")
            if new_happiness >= 95:
                play_events.append("✨ Your panda is absolutely glowing with joy!")
            
            description = f"You and **{panda_info['name']}** {activity}! 🎉\n\n{happiness_emoji} {happiness_msg}"
            if play_events:
                description += f"\n\n{' '.join(play_events)}"
            
            embed = discord.Embed(
                title="🎮 Playtime Adventure!",
                description=description,
                color=0xf39c12
            )
            
            # Enhanced stats display
            level_display = f"{self.get_level_title(level)}" + (f" → {self.get_level_title(new_level)} 🎊" if level_up else "")
            
            embed.add_field(
                name="📈 Panda Development",
                value=f"**Happiness:** {current_happiness}% → {new_happiness}% (+{total_happiness_gain})\n"
                      f"**Experience:** {current_exp} → {new_exp} (+{total_exp_gain} EXP)\n"
                      f"**Level:** {level_display}\n"
                      f"**Total Plays:** {total_plays} 🎮",
                inline=True
            )
            
            # Enhanced rewards breakdown
            reward_breakdown = f"**Base:** +{base_coins} 🪙\n"
            if level_coin_bonus > 0:
                reward_breakdown += f"**Level Bonus:** +{level_coin_bonus} 🪙\n"
            if happiness_coin_bonus > 0:
                reward_breakdown += f"**Happiness Bonus:** +{happiness_coin_bonus} 🪙\n"
            if energy_coin_bonus > 0:
                reward_breakdown += f"**⚡ Energy Bonus:** +{energy_coin_bonus} 🪙\n"
            if perfect_play_coins > 0:
                reward_breakdown += f"**🌟 Perfect Play:** +{perfect_play_coins} 🪙\n"
            if milestone_bonus > 0:
                reward_breakdown += f"**🎉 Milestone:** +{milestone_bonus} 🪙\n"
            if level_up_bonus > 0:
                reward_breakdown += f"**🆙 Level Up:** +{level_up_bonus} 🪙\n"
            if streak_bonus_coins > 0:
                reward_breakdown += f"**🔥 Streak:** +{streak_bonus_coins} 🪙\n"
            
            reward_breakdown += f"**Total Earned:** +{total_coins} 🪙\n**Your Balance:** {get_user_currency(user_id)} 🪙"
            
            embed.add_field(
                name="💰 Adventure Rewards",
                value=reward_breakdown,
                inline=True
            )
            
            # Special achievement messages
            achievements = []
            if level_up:
                achievements.append(f"🎊 **LEVEL UP!** {panda_info['name']} achieved {self.get_level_title(new_level)}!")
            if streak_msg:
                achievements.append(streak_msg)
            if total_plays % 25 == 0:
                achievements.append(f"🏆 **Play Master!** You've played with {panda_info['name']} {total_plays} times!")
            if new_happiness == 100 and current_happiness < 100:
                achievements.append(f"💖 **Maximum Joy!** {panda_info['name']} reached peak happiness!")
            
            if achievements:
                embed.add_field(
                    name="🏆 Achievements Unlocked",
                    value="\n".join(achievements),
                    inline=False
                )
            
            embed.set_thumbnail(url=panda_info["image_url"])
            embed.set_footer(text=f"💡 Next playtime in 45 minutes • Try /feed {panda_id} to keep them healthy! • Happy pandas = better rewards!")
            
            await interaction.followup.send(embed=embed)
        
        except Exception as e:
            logger.error(f"Play error for user {interaction.user.id}, panda {panda_id}: {e}")
            embed = discord.Embed(
                title="🚨 Playtime Error",
                description="Something went wrong during playtime. Don't worry, your panda is safe and still loves you!",
                color=0xe74c3c
            )
            embed.add_field(
                name="🔧 Try Again:",
                value="• Wait a moment and retry\n• Check your connection\n• Contact support if this persists",
                inline=False
            )
            await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AdoptionSystem(bot))