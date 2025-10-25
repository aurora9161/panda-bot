import discord
from discord.ext import tasks
import aiohttp
import asyncio
import os
import json
import random
from datetime import datetime, time
import logging
from typing import Optional

# ==========================================
# BOT TOKEN CONFIGURATION (Owner asked for direct token in main file)
# ==========================================
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # <-- put your token here

# If not set above, will try environment variable as fallback (safe for hosting)
if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    BOT_TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_BOT_TOKEN_HERE")

# ==========================================
# BOT SETUP (slash-only; no prefix commands)
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)

# Optional: set your Discord user ID as bot owner for owner-only commands
BOT_OWNER_ID: 1310134550566797352

# Config persistence path
CONFIG_PATH = os.getenv("CONFIG_PATH", "config.json")
ADOPTION_PATH = os.getenv("ADOPTION_PATH", "adoption_data.json")

# Default configuration
DEFAULT_CONFIG = {
    "daily_channel_id": None,
    "daily_time": os.getenv("DEFAULT_DAILY_TIME", "12:00"),
    "timezone": os.getenv("DEFAULT_TIMEZONE", "UTC"),
    "enabled": False
}

# Default adoption data
DEFAULT_ADOPTION_DATA = {
    "adoptions": {},
    "available_pandas": [
        {
            "id": "panda_001",
            "name": "Bamboo",
            "age": "3 months",
            "personality": "Playful and energetic",
            "favorite_food": "Fresh bamboo shoots",
            "special_trait": "Loves to tumble around",
            "image_url": "https://images.unsplash.com/photo-1564349683136-77e08dba1ef7?w=400",
            "adoption_fee": 150,
            "available": True
        },
        {
            "id": "panda_002",
            "name": "Snuggles",
            "age": "6 months",
            "personality": "Calm and cuddly",
            "favorite_food": "Bamboo leaves",
            "special_trait": "Expert hugger",
            "image_url": "https://images.unsplash.com/photo-1548247416-ec66f4900b2e?w=400",
            "adoption_fee": 200,
            "available": True
        },
        {
            "id": "panda_003",
            "name": "Mochi",
            "age": "2 months",
            "personality": "Shy but sweet",
            "favorite_food": "Young bamboo tips",
            "special_trait": "Squeaks when happy",
            "image_url": "https://images.unsplash.com/photo-1539979138647-0d8e368d09fb?w=400",
            "adoption_fee": 120,
            "available": True
        },
        {
            "id": "panda_004",
            "name": "Thunder",
            "age": "1 year",
            "personality": "Brave and adventurous",
            "favorite_food": "Thick bamboo stems",
            "special_trait": "Amazing climber",
            "image_url": "https://images.unsplash.com/photo-1515036551567-6ea0ac3b7bd5?w=400",
            "adoption_fee": 300,
            "available": True
        },
        {
            "id": "panda_005",
            "name": "Marshmallow",
            "age": "4 months",
            "personality": "Gentle and loving",
            "favorite_food": "Soft bamboo shoots",
            "special_trait": "Purrs like a cat",
            "image_url": "https://images.unsplash.com/photo-1582792141062-cdc80a803cc8?w=400",
            "adoption_fee": 175,
            "available": True
        }
    ],
    "user_currency": {}
}

# In-memory configuration
config_data: dict = {}
adoption_data: dict = {}

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("panda-bot")

# APIs
SRA_PANDA = "https://api.some-random-api.com/animal/panda"
SRA_RED_PANDA = "https://api.some-random-api.com/animal/red_panda"
QUOTES_API = "https://api.quotable.io/quotes/random?limit=1"
JOKE_API = "https://v2.jokeapi.dev/joke/Any?safe-mode&type=single"

PANDA_FACTS = [
    "Giant pandas spend 14-16 hours a day eating bamboo!",
    "A newborn panda is about the size of a stick of butter!",
    "Pandas have a pseudo thumb to help them grip bamboo!",
    "Giant pandas are excellent swimmers and climbers!",
    "Pandas are carnivores by classification but eat mostly bamboo.",
]
PANDA_JOKES = [
    "Why don't pandas ever get angry? They're always bamboozled!",
    "What do you call a panda with no teeth? A gummy bear!",
    "What's a panda's favorite dance? The bamboo-cha!",
]
PANDA_NAMES = [
    "Bao Bao", "Xiao Liwu", "Mei Xiang", "Tian Tian", "Lun Lun", "Yang Yang", "Bei Bei", "Yuan Zi",
    "Hua Mei", "Tai Shan", "Gu Gu", "Pan Pan", "Ling Ling", "Shuang Shuang", "Qin Qin", "Xiong Xiong"
]

# =================== Config and Adoption Data persistence ===================

def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged = DEFAULT_CONFIG.copy()
            merged.update(data or {})
            return merged
    except Exception as e:
        logger.error(f"Failed to load config.json: {e}. Using defaults.")
        return DEFAULT_CONFIG.copy()

def save_config(data: dict) -> None:
    try:
        tmp_path = f"{CONFIG_PATH}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, CONFIG_PATH)
    except Exception as e:
        logger.error(f"Failed to save config.json: {e}")

def load_adoption_data() -> dict:
    if not os.path.exists(ADOPTION_PATH):
        save_adoption_data(DEFAULT_ADOPTION_DATA)
        return DEFAULT_ADOPTION_DATA.copy()
    try:
        with open(ADOPTION_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Merge with defaults to ensure all keys exist
            merged = DEFAULT_ADOPTION_DATA.copy()
            if data:
                merged["adoptions"] = data.get("adoptions", {})
                merged["available_pandas"] = data.get("available_pandas", DEFAULT_ADOPTION_DATA["available_pandas"])
                merged["user_currency"] = data.get("user_currency", {})
            return merged
    except Exception as e:
        logger.error(f"Failed to load adoption_data.json: {e}. Using defaults.")
        return DEFAULT_ADOPTION_DATA.copy()

def save_adoption_data(data: dict) -> None:
    try:
        tmp_path = f"{ADOPTION_PATH}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, ADOPTION_PATH)
    except Exception as e:
        logger.error(f"Failed to save adoption_data.json: {e}")

# Initialize data at import time
config_data = load_config()
adoption_data = load_adoption_data()

# =================== Adoption System Helper Functions ===================

def get_user_currency(user_id: str) -> int:
    return adoption_data["user_currency"].get(user_id, 100)  # Default starting currency

def add_user_currency(user_id: str, amount: int) -> None:
    current = get_user_currency(user_id)
    adoption_data["user_currency"][user_id] = current + amount
    save_adoption_data(adoption_data)

def subtract_user_currency(user_id: str, amount: int) -> bool:
    current = get_user_currency(user_id)
    if current >= amount:
        adoption_data["user_currency"][user_id] = current - amount
        save_adoption_data(adoption_data)
        return True
    return False

def get_available_pandas():
    return [p for p in adoption_data["available_pandas"] if p["available"]]

def get_panda_by_id(panda_id: str):
    for panda in adoption_data["available_pandas"]:
        if panda["id"] == panda_id:
            return panda
    return None

def adopt_panda(user_id: str, panda_id: str) -> bool:
    panda = get_panda_by_id(panda_id)
    if not panda or not panda["available"]:
        return False
    
    # Mark panda as adopted
    panda["available"] = False
    
    # Add to user's adoptions
    if user_id not in adoption_data["adoptions"]:
        adoption_data["adoptions"][user_id] = []
    
    adoption_data["adoptions"][user_id].append({
        "panda_id": panda_id,
        "adopted_date": datetime.utcnow().isoformat(),
        "happiness": 100,
        "last_fed": datetime.utcnow().isoformat(),
        "last_played": datetime.utcnow().isoformat()
    })
    
    save_adoption_data(adoption_data)
    return True

def get_user_pandas(user_id: str):
    return adoption_data["adoptions"].get(user_id, [])

def update_panda_stats(user_id: str, panda_id: str, stat: str, value) -> bool:
    user_pandas = get_user_pandas(user_id)
    for adopted_panda in user_pandas:
        if adopted_panda["panda_id"] == panda_id:
            adopted_panda[stat] = value
            save_adoption_data(adoption_data)
            return True
    return False

class HTTP:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def ensure(self):
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=12)
            self.session = aiohttp.ClientSession(timeout=timeout)

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def get_json(self, url: str):
        await self.ensure()
        try:
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.warning(f"HTTP {resp.status} for {url}")
        except Exception as e:
            logger.error(f"HTTP error for {url}: {e}")
        return None

http = HTTP()

# ============== Panda content helpers =================
async def _fetch_sra_animal(primary: str, fallback: str) -> tuple[Optional[str], Optional[str]]:
    for url in (primary, fallback):
        data = await http.get_json(url)
        if isinstance(data, dict):
            img = data.get("image")
            fact = data.get("fact")
            if img or fact:
                return img, fact
    return None, None

async def fetch_panda_image() -> Optional[str]:
    img, _ = await _fetch_sra_animal(SRA_PANDA, SRA_RED_PANDA)
    return img

async def fetch_panda_gif() -> Optional[str]:
    img, _ = await _fetch_sra_animal(SRA_PANDA, SRA_RED_PANDA)
    if img and img.lower().endswith(".gif"):
        return img
    return None

async def fetch_panda_fact() -> str:
    _, fact = await _fetch_sra_animal(SRA_PANDA, SRA_RED_PANDA)
    if fact:
        return fact
    return random.choice(PANDA_FACTS)

async def fetch_quote() -> Optional[tuple[str, str]]:
    data = await http.get_json(QUOTES_API)
    try:
        if isinstance(data, list) and data:
            q = data[0]
            return q.get("content"), q.get("author", "Unknown")
    except Exception as e:
        logger.error(f"Quote parse error: {e}")
    return None

async def fetch_joke() -> Optional[str]:
    data = await http.get_json(JOKE_API)
    if isinstance(data, dict):
        j = data.get("joke")
        if j:
            return j
    return random.choice(PANDA_JOKES)

# ===================== Events =========================
@bot.event
async def on_ready():
    try:
        await tree.sync()
        logger.info("Synced slash commands")
    except Exception as e:
        logger.error(f"Failed to sync slash commands: {e}")

    save_config(config_data)

    if config_data["enabled"] and config_data["daily_channel_id"] and not daily_panda_task.is_running():
        daily_panda_task.start()

    logger.info(f"Logged in as {bot.user} | Guilds: {len(bot.guilds)}")

@bot.event
async def on_disconnect():
    await http.close()

# =================== Daily Task =======================
@tasks.loop(hours=24)
async def daily_panda_task():
    if not (config_data["enabled"] and config_data["daily_channel_id"]):
        return
    channel = bot.get_channel(config_data["daily_channel_id"])
    if not isinstance(channel, discord.TextChannel):
        logger.error("Configured daily channel not found or not a text channel")
        return
    try:
        img = await fetch_panda_image()
        fact = await fetch_panda_fact()
        embed = discord.Embed(title="🐼 Daily Panda!", description=fact or "", color=0x2ecc71)
        if img:
            embed.set_image(url=img)
        else:
            embed.add_field(name="Image", value="Image source unavailable right now.")
        embed.set_footer(text=f"Delivered at {datetime.utcnow().strftime('%H:%M UTC')}")
        await channel.send(embed=embed)
    except Exception as e:
        logger.error(f"Daily task error: {e}")

@daily_panda_task.before_loop
async def before_daily():
    await bot.wait_until_ready()
    try:
        hour, minute = map(int, config_data["daily_time"].split(":"))
        target = time(hour=hour, minute=minute)
        now = datetime.utcnow().time()
        now_sec = now.hour * 3600 + now.minute * 60 + now.second
        tgt_sec = target.hour * 3600 + target.minute * 60
        wait = (tgt_sec - now_sec) if tgt_sec > now_sec else (86400 - (now_sec - tgt_sec))
        await asyncio.sleep(wait)
    except Exception as e:
        logger.error(f"before_loop scheduling error: {e}")

# =================== Owner-only helper =================
async def is_owner_user(interaction: discord.Interaction) -> bool:
    try:
        app = await bot.application_info()
        if interaction.user.id == app.owner.id:
            return True
    except Exception:
        pass
    if BOT_OWNER_ID and interaction.user.id == BOT_OWNER_ID:
        return True
    return False

# =================== Adoption System Slash Commands ====================

@tree.command(name="adopt", description="Adopt a panda from the adoption center")
@discord.app_commands.describe(panda_id="ID of the panda to adopt (use /adoptlist to see available pandas)")
async def adopt_cmd(interaction: discord.Interaction, panda_id: str):
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

@tree.command(name="adoptlist", description="View all available pandas for adoption")
async def adoptlist_cmd(interaction: discord.Interaction):
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

@tree.command(name="mypandas", description="View your adopted pandas")
async def mypandas_cmd(interaction: discord.Interaction):
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

@tree.command(name="feed", description="Feed one of your pandas")
@discord.app_commands.describe(panda_id="ID of the panda to feed")
async def feed_cmd(interaction: discord.Interaction, panda_id: str):
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

@tree.command(name="play", description="Play with one of your pandas")
@discord.app_commands.describe(panda_id="ID of the panda to play with")
async def play_cmd(interaction: discord.Interaction, panda_id: str):
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

@tree.command(name="work", description="Work to earn bamboo coins")
async def work_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        user_id = str(interaction.user.id)
        
        # Simple work system - can work every 30 minutes
        last_work_key = f"last_work_{user_id}"
        current_time = datetime.utcnow()
        
        # For simplicity, we'll store this in user_currency data with a special key
        if last_work_key in adoption_data["user_currency"]:
            last_work_time = datetime.fromisoformat(adoption_data["user_currency"][last_work_key])
            time_since_work = current_time - last_work_time
            if time_since_work.total_seconds() < 1800:  # 30 minute cooldown
                minutes_left = int((1800 - time_since_work.total_seconds()) / 60)
                await interaction.followup.send(f"💼 You're tired from working! Rest for {minutes_left} more minutes.")
                return
                
        # Work and earn coins
        coins_earned = random.randint(20, 50)
        add_user_currency(user_id, coins_earned)
        adoption_data["user_currency"][last_work_key] = current_time.isoformat()
        save_adoption_data(adoption_data)
        
        work_jobs = [
            "helped at the bamboo farm",
            "cleaned the panda sanctuary",
            "guided tourists at the zoo",
            "delivered bamboo supplies",
            "assisted panda researchers",
            "organized adoption paperwork"
        ]
        
        embed = discord.Embed(
            title="💼 Work Complete!",
            description=f"You {random.choice(work_jobs)} and earned **{coins_earned} bamboo coins**!",
            color=0x3498db
        )
        embed.add_field(name="Your Balance", value=f"{get_user_currency(user_id)} bamboo coins", inline=True)
        embed.set_footer(text="You can work again in 30 minutes!")
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"/work error: {e}")
        await interaction.followup.send("Unexpected error occurred.")

@tree.command(name="daily", description="Claim your daily bamboo coin bonus")
async def daily_cmd(interaction: discord.Interaction):
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
                
        # Give daily bonus
        daily_bonus = 100
        add_user_currency(user_id, daily_bonus)
        adoption_data["user_currency"][last_daily_key] = current_time.isoformat()
        save_adoption_data(adoption_data)
        
        embed = discord.Embed(
            title="🎁 Daily Bonus!",
            description=f"You claimed your daily bonus of **{daily_bonus} bamboo coins**!",
            color=0xe74c3c
        )
        embed.add_field(name="Your Balance", value=f"{get_user_currency(user_id)} bamboo coins", inline=True)
        embed.set_footer(text="Come back tomorrow for another bonus!")
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"/daily error: {e}")
        await interaction.followup.send("Unexpected error occurred.")

@tree.command(name="balance", description="Check your bamboo coin balance")
async def balance_cmd(interaction: discord.Interaction):
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
        embed.set_footer(text="Use /work or /daily to earn more coins!")
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        logger.error(f"/balance error: {e}")
        await interaction.response.send_message("Unexpected error occurred.")

# =================== Original Slash Commands (app_commands) ====================
@tree.command(name="panda", description="Get a random panda image")
async def panda_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        img = await fetch_panda_image()
        if not img:
            await interaction.followup.send("Couldn't fetch a panda image right now. Please try again later.")
            return
        embed = discord.Embed(title="🐼 Adorable Panda", color=0x000000)
        embed.set_image(url=img)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"/panda error: {e}")
        await interaction.followup.send("Unexpected error occurred.")

@tree.command(name="pandafact", description="Get a random panda fact")
async def pandafact_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        fact = await fetch_panda_fact()
        embed = discord.Embed(title="🎋 Panda Fact", description=fact, color=0x1abc9c)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"/pandafact error: {e}")
        await interaction.followup.send("Unexpected error occurred.")

@tree.command(name="pandagif", description="Get a random panda GIF (if available)")
async def pandagif_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        gif = await fetch_panda_gif()
        if gif:
            embed = discord.Embed(title="🐼 Panda GIF", color=0x95a5a6)
            embed.set_image(url=gif)
            await interaction.followup.send(embed=embed)
        else:
            img = await fetch_panda_image()
            if img:
                embed = discord.Embed(title="🐼 Panda Image (GIF not available)", color=0x95a5a6)
                embed.set_image(url=img)
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send("Couldn't fetch a panda GIF or image right now.")
    except Exception as e:
        logger.error(f"/pandagif error: {e}")
        await interaction.followup.send("Unexpected error occurred.")

@tree.command(name="pandaall", description="Get image + fact together")
async def pandaall_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        img, fact = await asyncio.gather(fetch_panda_image(), fetch_panda_fact())
        embed = discord.Embed(title="🐼 Complete Panda Package", description=fact or "", color=0x2c3e50)
        if img:
            embed.set_image(url=img)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"/pandaall error: {e}")
        await interaction.followup.send("Unexpected error occurred.")

@tree.command(name="pandaquote", description="Get an inspirational quote (API)")
async def pandaquote_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        got = await fetch_quote()
        if not got:
            await interaction.followup.send("Couldn't fetch a quote right now. Please try again later.")
            return
        content, author = got
        embed = discord.Embed(title="💭 Panda Wisdom", description=f"{content}\n\n— {author}", color=0x8e44ad)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"/pandaquote error: {e}")
        await interaction.followup.send("Unexpected error occurred.")

@tree.command(name="pandajoke", description="Get a random joke (API)")
async def pandajoke_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        joke = await fetch_joke()
        embed = discord.Embed(title="😂 Panda Joke", description=joke, color=0xf1c40f)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"/pandajoke error: {e}")
        await interaction.followup.send("Unexpected error occurred.")

TRIVIA_BANK = [
    {
        "q": "What percentage of a panda's diet is bamboo?",
        "options": ["85%", "95%", "99%", "100%"],
        "answer": 2,
        "explain": "Pandas are classified as carnivores but eat bamboo about 99% of the time."
    },
    {
        "q": "How many hours do pandas typically eat per day?",
        "options": ["8-10", "12-14", "14-16", "18-20"],
        "answer": 2,
        "explain": "They spend most waking hours munching bamboo."
    },
    {
        "q": "What is a group of pandas called?",
        "options": ["A cuddle", "An embarrassment", "A bamboo", "A fluff"],
        "answer": 1,
        "explain": "Yes, it's really called an embarrassment of pandas."
    },
]

@tree.command(name="pandatrivia", description="Answer a panda trivia question")
async def pandatrivia_cmd(interaction: discord.Interaction):
    try:
        q = random.choice(TRIVIA_BANK)
        options_txt = "\n".join([f"{idx+1}. {opt}" for idx, opt in enumerate(q["options"])])
        embed = discord.Embed(title="🧠 Panda Trivia", description=q["q"], color=0xe74c3c)
        embed.add_field(name="Options", value=options_txt, inline=False)
        embed.set_footer(text="React 1/2/3/4 below to answer! You have 20 seconds.")
        await interaction.response.send_message(embed=embed)
        sent = await interaction.original_response()
        emoji_map = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        for i in range(len(q["options"])):
            try:
                await sent.add_reaction(emoji_map[i])
            except Exception:
                pass

        def check(reaction: discord.Reaction, user: discord.User | discord.Member):
            return (
                reaction.message.id == sent.id
                and str(reaction.emoji) in emoji_map[:len(q["options"])]
                and user.id != bot.user.id
            )

        correct_index = q["answer"]
        try:
            while True:
                reaction, user = await bot.wait_for("reaction_add", timeout=20.0, check=check)
                chosen_index = emoji_map.index(str(reaction.emoji))
                if chosen_index == correct_index:
                    await sent.reply(f"✅ {user.mention} got it right! Answer: **{q['options'][correct_index]}**\n*{q['explain']}*")
                    break
                else:
                    continue
        except asyncio.TimeoutError:
            await sent.reply(f"⏰ Time's up! Correct answer was **{q['options'][correct_index]}**\n*{q['explain']}*")
    except Exception as e:
        logger.error(f"/pandatrivia error: {e}")
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("Unexpected error occurred.")
            else:
                await interaction.followup.send("Unexpected error occurred.")
        except Exception:
            pass

@tree.command(name="say", description="Make the bot say a message in a channel")
@discord.app_commands.describe(message="Text to send", channel="Target channel (defaults to current)")
async def say_cmd(interaction: discord.Interaction, message: str, channel: Optional[discord.TextChannel] = None):
    safe = message.replace("@everyone", "everyone").replace("@here", "here")
    allowed = discord.AllowedMentions(everyone=False, users=False, roles=False)
    target = channel or interaction.channel
    try:
        await target.send(safe, allowed_mentions=allowed)
        await interaction.response.send_message(f"Sent in {target.mention}", ephemeral=True)
    except Exception as e:
        logger.error(f"/say error: {e}")
        await interaction.response.send_message("Failed to send message.", ephemeral=True)

@tree.command(name="qr", description="Generate a QR code from text")
@discord.app_commands.describe(text="Text or URL to encode")
async def qr_cmd(interaction: discord.Interaction, text: str):
    await interaction.response.defer()
    try:
        import io
        import qrcode
        from PIL import Image

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(text)
        qr.make(fit=True)
        img: Image.Image = qr.make_image(fill_color="black", back_color="white").convert("RGB")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        file = discord.File(buf, filename="qr.png")
        embed = discord.Embed(title="🔳 Your QR Code", color=0x2d3436)
        embed.set_image(url="attachment://qr.png")
        await interaction.followup.send(embed=embed, file=file)
    except ModuleNotFoundError:
        await interaction.followup.send("QR dependencies missing. Please add qrcode[pil] and pillow to requirements.txt and reinstall.")
    except Exception as e:
        logger.error(f"/qr error: {e}")
        await interaction.followup.send("Failed to generate QR code.")

@tree.command(name="pandaname", description="Get a random cute panda name")
async def pandaname_cmd(interaction: discord.Interaction):
    try:
        name = random.choice(PANDA_NAMES)
        await interaction.response.send_message(f"🍼 Your panda name is: **{name}**")
    except Exception as e:
        logger.error(f"/pandaname error: {e}")
        await interaction.response.send_message("Unexpected error occurred.")

@tree.command(name="pandamash", description="Mash up two panda names into one fun name")
async def pandamash_cmd(interaction: discord.Interaction):
    try:
        a, b = random.sample(PANDA_NAMES, 2)
        mash = a[: len(a)//2] + b[len(b)//2 :]
        await interaction.response.send_message(f"🧪 Panda mash: **{mash}** (from {a} + {b})")
    except Exception as e:
        logger.error(f"/pandamash error: {e}")
        await interaction.response.send_message("Unexpected error occurred.")

@tree.command(name="pandacombo", description="Get a combo of image + fact + joke in one embed")
async def pandacombo_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        img, fact, joke = await asyncio.gather(fetch_panda_image(), fetch_panda_fact(), fetch_joke())
        embed = discord.Embed(title="🐼 Panda Combo", description=fact or "", color=0x16a085)
        if img:
            embed.set_image(url=img)
        embed.add_field(name="Joke", value=joke, inline=False)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"/pandacombo error: {e}")
        await interaction.followup.send("Unexpected error occurred.")

@tree.command(name="pandapoll", description="Create a quick bamboo poll with thumbs reactions")
@discord.app_commands.describe(question="Poll question")
async def pandapoll_cmd(interaction: discord.Interaction, question: str):
    try:
        embed = discord.Embed(title="🎋 Bamboo Poll", description=question, color=0x27ae60)
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        for emoji in ("👍", "👎"):
            try:
                await msg.add_reaction(emoji)
            except Exception:
                pass
    except Exception as e:
        logger.error(f"/pandapoll error: {e}")
        await interaction.response.send_message("Unexpected error occurred.")

@tree.command(name="pandaping", description="Check bot latency the panda way")
async def pandaping_cmd(interaction: discord.Interaction):
    try:
        ms = round(bot.latency * 1000)
        await interaction.response.send_message(f"🐾 Bamboo speed: **{ms} ms**")
    except Exception as e:
        logger.error(f"/pandaping error: {e}")
        await interaction.response.send_message("Unexpected error occurred.")

@tree.command(name="pandaownerreload", description="[Owner] Reload slash commands")
async def owner_reload(interaction: discord.Interaction):
    if not await is_owner_user(interaction):
        await interaction.response.send_message("You are not the bot owner.", ephemeral=True)
        return
    try:
        synced = await tree.sync()
        await interaction.response.send_message(f"Reloaded {len(synced)} commands.", ephemeral=True)
    except Exception as e:
        logger.error(f"/pandaownerreload error: {e}")
        await interaction.response.send_message("Failed to reload commands.", ephemeral=True)

@tree.command(name="pandaownerset", description="[Owner] Set daily channel/time/enable")
@discord.app_commands.describe(channel="Channel to post daily panda", time_str="Daily time HH:MM (UTC)", enabled="Enable daily posts")
async def owner_set(interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None, time_str: Optional[str] = None, enabled: Optional[bool] = None):
    if not await is_owner_user(interaction):
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
            if daily_panda_task.is_running():
                daily_panda_task.restart()
        if enabled is not None:
            config_data["enabled"] = enabled
            changes.append("Enabled" if enabled else "Disabled")
            if enabled:
                if config_data["daily_channel_id"] and not daily_panda_task.is_running():
                    daily_panda_task.start()
            else:
                if daily_panda_task.is_running():
                    daily_panda_task.cancel()
        save_config(config_data)
        if not changes:
            changes.append("No changes provided.")
        await interaction.response.send_message(" | ".join(changes), ephemeral=True)
    except Exception as e:
        logger.error(f"/pandaownerset error: {e}")
        await interaction.response.send_message("Failed to update settings.", ephemeral=True)

@tree.command(name="pandaownerstatus", description="[Owner] Detailed bot status (owner-only)")
async def owner_status(interaction: discord.Interaction):
    if not await is_owner_user(interaction):
        await interaction.response.send_message("You are not the bot owner.", ephemeral=True)
        return
    try:
        embed = discord.Embed(title="👑 Owner Status", color=0x2e86c1)
        embed.add_field(name="Bot User", value=str(bot.user), inline=True)
        embed.add_field(name="Guilds", value=str(len(bot.guilds)), inline=True)
        embed.add_field(name="Latency", value=f"{round(bot.latency * 1000)} ms", inline=True)
        ch = f"<#{config_data['daily_channel_id']}>" if config_data.get("daily_channel_id") else "Not set"
        embed.add_field(name="Daily Channel", value=ch, inline=True)
        embed.add_field(name="Daily Time (UTC)", value=config_data.get("daily_time", "12:00"), inline=True)
        embed.add_field(name="Enabled", value="Yes" if config_data.get("enabled") else "No", inline=True)
        running = daily_panda_task.is_running()
        embed.add_field(name="Daily Task", value="Running" if running else "Stopped", inline=True)
        if running and config_data.get("enabled"):
            nxt = daily_panda_task.next_iteration
            if nxt:
                embed.add_field(name="Next Delivery", value=f"<t:{int(nxt.timestamp())}:R>", inline=False)
        embed.set_footer(text="Owner-only diagnostic view")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        logger.error(f"/pandaownerstatus error: {e}")
        await interaction.response.send_message("Failed to get owner status.", ephemeral=True)

@tree.command(name="pandaconfig", description="Configure daily panda settings (Admin only)")
@discord.app_commands.describe(channel="The channel to send daily pandas to", time_str="Time to send daily panda (24-hour UTC, e.g., 14:30)", enabled="Enable or disable daily pandas")
async def pandaconfig_cmd(interaction: discord.Interaction, channel: Optional[discord.TextChannel] = None, time_str: Optional[str] = None, enabled: Optional[bool] = None):
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
            if daily_panda_task.is_running():
                daily_panda_task.restart()
        if enabled is not None:
            config_data["enabled"] = enabled
            changes.append("Enabled" if enabled else "Disabled")
            if enabled:
                if config_data["daily_channel_id"] and not daily_panda_task.is_running():
                    daily_panda_task.start()
            else:
                if daily_panda_task.is_running():
                    daily_panda_task.cancel()
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

@tree.command(name="pandastatus", description="Check current configuration and status")
async def pandastatus_cmd(interaction: discord.Interaction):
    try:
        embed = discord.Embed(title="🐼 Panda Bot Status", color=0x9b59b6)
        ch = f"<#{config_data['daily_channel_id']}>" if config_data["daily_channel_id"] else "Not set"
        embed.add_field(name="Daily Channel", value=ch, inline=True)
        embed.add_field(name="Daily Time (UTC)", value=config_data["daily_time"], inline=True)
        embed.add_field(name="Enabled", value="Yes" if config_data["enabled"] else "No", inline=True)
        embed.add_field(name="Guilds", value=str(len(bot.guilds)), inline=True)
        embed.add_field(name="Latency", value=f"{round(bot.latency * 1000)} ms", inline=True)
        if daily_panda_task.is_running() and config_data["enabled"]:
            nxt = daily_panda_task.next_iteration
            if nxt:
                embed.add_field(name="Next Delivery", value=f"<t:{int(nxt.timestamp())}:R>", inline=False)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        logger.error(f"/pandastatus error: {e}")
        await interaction.response.send_message("Unexpected error occurred.")

@tree.command(name="pandatest", description="Send a test daily panda (Admin only)")
async def pandatest_cmd(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You need Administrator permission to use this.", ephemeral=True)
        return
    if not config_data["daily_channel_id"]:
        await interaction.response.send_message("Daily channel not configured. Use /pandaconfig first.", ephemeral=True)
        return
    await interaction.response.send_message("Sending test panda...", ephemeral=True)
    try:
        channel = bot.get_channel(config_data["daily_channel_id"])
        img = await fetch_panda_image()
        fact = await fetch_panda_fact()
        embed = discord.Embed(title="🧪 Test Panda", description=fact or "", color=0x2ecc71)
        if img:
            embed.set_image(url=img)
        await channel.send(embed=embed)
        await interaction.followup.send("Test panda sent.", ephemeral=True)
    except Exception as e:
        logger.error(f"/pandatest error: {e}")
        await interaction.followup.send("Failed to send test.", ephemeral=True)

@tree.command(name="pandahelp", description="Show all panda commands")
async def pandahelp_cmd(interaction: discord.Interaction):
    try:
        embed = discord.Embed(title="🐼 Panda Bot Help", description="Slash-only commands", color=0x00a86b)
        embed.add_field(name="📦 Core", value=("`/panda` image\n" "`/pandafact` fact\n" "`/pandagif` gif (if available)\n" "`/pandaall` image+fact\n"), inline=False)
        embed.add_field(name="🎉 Fun", value=("`/pandajoke` joke (API)\n" "`/pandaquote` quote (API)\n" "`/pandatrivia` trivia question\n" "`/pandaname` random name\n" "`/pandamash` name mash\n"), inline=False)
        embed.add_field(name="🏠 Adoption", value=("`/adoptlist` see available pandas\n" "`/adopt` adopt a panda\n" "`/mypandas` view your pandas\n" "`/feed` feed your panda\n" "`/play` play with panda\n"), inline=False)
        embed.add_field(name="💰 Economy", value=("`/balance` check coins\n" "`/work` earn coins\n" "`/daily` daily bonus\n"), inline=False)
        embed.add_field(name="🧰 Utility", value=("`/qr` generate QR code\n" "`/say` make bot say\n" "`/pandapoll` bamboo poll\n" "`/pandaping` latency\n"), inline=False)
        embed.add_field(name="🛠 Admin", value=("`/pandaconfig` set channel/time/enable\n" "`/pandastatus` status\n" "`/pandatest` test send\n"), inline=False)
        embed.add_field(name="👑 Owner", value=("`/pandaownerreload` reload slash\n" "`/pandaownerset` owner set channel/time/enable\n" "`/pandaownerstatus` owner diagnostic status\n"), inline=False)
        embed.set_footer(text="Made by auora.")
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        logger.error(f"/pandahelp error: {e}")
        await interaction.response.send_message("Unexpected error occurred.")

@bot.event
async def on_error(event_method, /, *args, **kwargs):
    try:
        logger.error(f"Unhandled error in {event_method}")
    except Exception:
        pass

if __name__ == "__main__":
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("Please set your bot token in BOT_TOKEN at the top of bot.py")
        raise SystemExit(1)
    try:
        bot.run(BOT_TOKEN)
    except discord.LoginFailure:
        logger.error("Invalid bot token.")
    except Exception as e:
        logger.error(f"Runtime error: {e}")
