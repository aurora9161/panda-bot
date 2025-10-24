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

# =================== Original adoption helpers (unchanged) ===================

def get_user_currency(user_id: str) -> int:
    return adoption_data["user_currency"].get(user_id, 100)

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
    panda["available"] = False
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

# =================== Additive Enhanced Adoption (Option B) ===================

ENHANCED = {
    'rarity_weights': {
        'common': 60, 'uncommon': 25, 'rare': 10, 'epic': 4, 'legendary': 1
    },
    'rarity_meta': {
        'common':    { 'emoji': '🐼',  'color': 0x95a5a6, 'base_happy': 80,  'decay_per_h': 2.0 },
        'uncommon':  { 'emoji': '🐼✨','color': 0x2ecc71, 'base_happy': 85,  'decay_per_h': 1.5 },
        'rare':      { 'emoji': '🐼💎','color': 0x3498db, 'base_happy': 90,  'decay_per_h': 1.0 },
        'epic':      { 'emoji': '🐼👑','color': 0x9b59b6, 'base_happy': 95,  'decay_per_h': 0.5 },
        'legendary': { 'emoji': '🐼🌟','color': 0xf1c40f, 'base_happy': 100, 'decay_per_h': 0.0 },
    },
    'personalities': ['playful','calm','curious','gentle','energetic'],
    'max_list': 5
}

def _pick_rarity():
    keys = list(ENHANCED['rarity_weights'].keys())
    weights = [ENHANCED['rarity_weights'][k] for k in keys]
    return random.choices(keys, weights=weights)[0]

def _gen_card():
    rarity = _pick_rarity()
    meta = ENHANCED['rarity_meta'][rarity]
    name = random.choice(["Bamboo","Mochi","Bao","Ping","Luna","Gizmo","Noodle","Pebble","Snowball","Oreo","Pudding","Button"]) 
    personality = random.choice(ENHANCED['personalities'])
    base_cost_map = {'common':100,'uncommon':250,'rare':500,'epic':1000,'legendary':2500}
    cost = max(50, base_cost_map[rarity] + random.randint(-50,100))
    return {
        'id': f"gen_{int(datetime.utcnow().timestamp())}_{random.randint(1000,9999)}",
        'name': name,
        'rarity': rarity,
        'personality': personality,
        'adoption_fee': cost,
        'base_happiness': meta['base_happy'],
        'color': meta['color'],
        'emoji': meta['emoji'],
        'image_url': "https://images.unsplash.com/photo-1564349683136-77e08dba1ef7?w=400",
        'available': True,
    }

def _ensure_meta(p: dict):
    # Non-destructive backfill for stored pandas
    if 'rarity' not in p:
        p['rarity'] = 'common'
    meta = ENHANCED['rarity_meta'].get(p['rarity'], ENHANCED['rarity_meta']['common'])
    p.setdefault('base_happiness', meta['base_happy'])
    return p

def _happy_now(adopted: dict, pmeta: dict) -> int:
    try:
        last = max(datetime.fromisoformat(adopted['last_fed']), datetime.fromisoformat(adopted['last_played']))
        hours = max(0.0, (datetime.utcnow() - last).total_seconds()/3600)
        rarity = pmeta.get('rarity','common')
        decay = ENHANCED['rarity_meta'][rarity]['decay_per_h']
        start = adopted.get('happiness', pmeta.get('base_happiness', 100))
        return max(0, int(start - hours*decay))
    except Exception:
        return adopted.get('happiness', pmeta.get('base_happiness', 100))

# Enhanced adoptlist that generates enriched pandas compatible with /adopt <id>
@tree.command(name="adoptlist", description="View enhanced pandas and adopt by ID with /adopt")
async def adoptlist_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        # Present original available pandas first
        orig = get_available_pandas()
        embed = discord.Embed(title="🐼 Panda Adoption Center (Enhanced)", description="Enhanced pandas include rarity/personality but still adopt with /adopt <id>", color=0x3498db)
        shown = 0
        for p in orig[:ENHANCED['max_list']]:
            p = _ensure_meta(p)
            embed.add_field(name=f"{p.get('name','Panda')} (ID: {p['id']})",
                            value=f"Rarity: {p['rarity'].title()} {ENHANCED['rarity_meta'][p['rarity']]['emoji']}\nPersonality: {p.get('personality','Playful').title()}\nFee: {p.get('adoption_fee',150)} 🎋",
                            inline=True)
            shown += 1
        # If fewer than max_list available, generate temporary enhanced entries and append them to available_pandas so /adopt works
        gen_needed = max(0, ENHANCED['max_list'] - shown)
        added_ids = []
        for _ in range(gen_needed):
            card = _gen_card()
            # Materialize into available_pandas (non-destructive append)
            adoption_data["available_pandas"].append({
                "id": card['id'],
                "name": card['name'],
                "age": "Young",
                "personality": card['personality'],
                "favorite_food": "Premium bamboo",
                "special_trait": f"{card['rarity'].title()} companion",
                "image_url": card['image_url'],
                "adoption_fee": card['adoption_fee'],
                "available": True,
                "rarity": card['rarity'],
                "base_happiness": card['base_happiness']
            })
            added_ids.append(card['id'])
            embed.add_field(name=f"{card['name']} (ID: {card['id']})",
                            value=f"Rarity: {card['rarity'].title()} {card['emoji']}\nPersonality: {card['personality'].title()}\nFee: {card['adoption_fee']} 🎋",
                            inline=True)
        if added_ids:
            save_adoption_data(adoption_data)
        if shown == 0 and not added_ids:
            await interaction.followup.send("😢 No pandas are currently available for adoption. Check back later!")
            return
        embed.set_footer(text="Use /adopt <panda_id> to adopt any listed panda.")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"/adoptlist enhanced error: {e}")
        await interaction.followup.send("Unexpected error occurred.")

# Keep your original /adopt; no signature change. Only minor runtime benefits from metadata.
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
            await interaction.followup.send(f"❌ {panda.get('name','Panda')} has already been adopted!")
            return
        user_currency = get_user_currency(user_id)
        fee = panda.get('adoption_fee', 150)
        if user_currency < fee:
            await interaction.followup.send(f"❌ You need {fee} bamboo coins to adopt {panda.get('name','Panda')}. You have {user_currency}. Use `/work` to earn more!")
            return
        # Limit remains 3
        if len(get_user_pandas(user_id)) >= 3:
            await interaction.followup.send("❌ You can only adopt up to 3 pandas at a time!")
            return
        # Process
        if subtract_user_currency(user_id, fee) and adopt_panda(user_id, panda_id):
            p = _ensure_meta(panda)
            embed = discord.Embed(title="🎉 Adoption Successful!", description=f"Congratulations! You've adopted **{p.get('name','Panda')}**!", color=ENHANCED['rarity_meta'][p['rarity']]['color'])
            embed.add_field(name="Rarity", value=f"{p['rarity'].title()} {ENHANCED['rarity_meta'][p['rarity']]['emoji']}", inline=True)
            embed.add_field(name="Personality", value=p.get('personality','Playful').title(), inline=True)
            embed.add_field(name="Adoption Fee", value=f"{fee} 🎋", inline=True)
            embed.add_field(name="Remaining Currency", value=f"{get_user_currency(user_id)} 🎋", inline=True)
            embed.set_thumbnail(url=p.get("image_url"))
            embed.set_footer(text="Use /mypandas to see all your adopted pandas!")
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("❌ Adoption failed. Please try again.")
    except Exception as e:
        logger.error(f"/adopt error: {e}")
        await interaction.followup.send("Unexpected error occurred.")

@tree.command(name="mypandas", description="View your adopted pandas (enhanced view)")
async def mypandas_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        user_id = str(interaction.user.id)
        user_pandas = get_user_pandas(user_id)
        if not user_pandas:
            embed = discord.Embed(title="😢 No Pandas Adopted", description="You haven't adopted any pandas yet! Use `/adoptlist` to see available pandas.", color=0xe74c3c)
            await interaction.followup.send(embed=embed)
            return
        embed = discord.Embed(title="🐼 Your Adopted Pandas", description=f"You have adopted {len(user_pandas)} panda(s)!", color=0x2ecc71)
        for adopted in user_pandas:
            panda = get_panda_by_id(adopted["panda_id"]) or {}
            panda = _ensure_meta(panda)
            adopted_date = datetime.fromisoformat(adopted["adopted_date"]).strftime("%Y-%m-%d")
            happy_now = _happy_now(adopted, panda)
            embed.add_field(name=f"{panda.get('name','Panda')} {ENHANCED['rarity_meta'][panda['rarity']]['emoji']}",
                            value=f"Rarity: {panda['rarity'].title()}\nHappiness: {happy_now}%\nAdopted: {adopted_date}\nPersonality: {panda.get('personality','Playful').title()}",
                            inline=True)
        embed.add_field(name="💰 Your Balance", value=f"{get_user_currency(user_id)} 🎋", inline=False)
        embed.set_footer(text="Use /feed or /play to interact with your pandas!")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"/mypandas error: {e}")
        await interaction.followup.send("Unexpected error occurred.")

# Keep original /feed and /play signatures; just show enhanced info in embeds via _ensure_meta
@tree.command(name="feed", description="Feed one of your pandas")
@discord.app_commands.describe(panda_id="ID of the panda to feed")
async def feed_cmd(interaction: discord.Interaction, panda_id: str):
    await interaction.response.defer()
    try:
        user_id = str(interaction.user.id)
        user_pandas = get_user_pandas(user_id)
        owned = next((a for a in user_pandas if a["panda_id"] == panda_id), None)
        if not owned:
            await interaction.followup.send("❌ You don't own a panda with that ID! Use `/mypandas` to see your pandas.")
            return
        pinfo = get_panda_by_id(panda_id) or {}
        pinfo = _ensure_meta(pinfo)
        last_fed = datetime.fromisoformat(owned["last_fed"]) if "last_fed" in owned else datetime.utcnow()
        if (datetime.utcnow() - last_fed).total_seconds() < 3600:
            minutes_left = int((3600 - (datetime.utcnow() - last_fed).total_seconds())/60)
            await interaction.followup.send(f"🍽️ {pinfo.get('name','Panda')} is not hungry yet! Wait {minutes_left} more minutes.")
            return
        gain = random.randint(5, 15)
        new_h = min(100, owned.get("happiness", pinfo.get('base_happiness', 100)) + gain)
        update_panda_stats(user_id, panda_id, "happiness", new_h)
        update_panda_stats(user_id, panda_id, "last_fed", datetime.utcnow().isoformat())
        coins = random.randint(5, 10)
        add_user_currency(user_id, coins)
        embed = discord.Embed(title="🍃 Feeding Time!", description=f"You fed **{pinfo.get('name','Panda')}** some delicious {pinfo.get('favorite_food','bamboo')}!", color=ENHANCED['rarity_meta'][pinfo['rarity']]['color'])
        embed.add_field(name="Happiness", value=f"{new_h}% (+{gain}%)", inline=True)
        embed.add_field(name="Coins Earned", value=f"+{coins} 🎋", inline=True)
        embed.add_field(name="Your Balance", value=f"{get_user_currency(user_id)} 🎋", inline=True)
        embed.set_thumbnail(url=pinfo.get("image_url"))
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
        owned = next((a for a in user_pandas if a["panda_id"] == panda_id), None)
        if not owned:
            await interaction.followup.send("❌ You don't own a panda with that ID! Use `/mypandas` to see your pandas.")
            return
        pinfo = get_panda_by_id(panda_id) or {}
        pinfo = _ensure_meta(pinfo)
        last_played = datetime.fromisoformat(owned["last_played"]) if "last_played" in owned else datetime.utcnow()
        if (datetime.utcnow() - last_played).total_seconds() < 2700:
            minutes_left = int((2700 - (datetime.utcnow() - last_played).total_seconds())/60)
            await interaction.followup.send(f"🎮 {pinfo.get('name','Panda')} is tired from playing! Wait {minutes_left} more minutes.")
            return
        gain = random.randint(10, 20)
        new_h = min(100, owned.get("happiness", pinfo.get('base_happiness', 100)) + gain)
        update_panda_stats(user_id, panda_id, "happiness", new_h)
        update_panda_stats(user_id, panda_id, "last_played", datetime.utcnow().isoformat())
        coins = random.randint(8, 15)
        add_user_currency(user_id, coins)
        activities = [
            f"rolled around with {pinfo.get('name','Panda')}!",
            f"played hide and seek with {pinfo.get('name','Panda')}!",
            f"had a bamboo stick tug-of-war with {pinfo.get('name','Panda')}!",
            f"watched {pinfo.get('name','Panda')} do adorable tumbles!",
            f"gave {pinfo.get('name','Panda')} belly rubs!"
        ]
        embed = discord.Embed(title="🎮 Playtime!", description=f"You {random.choice(activities)}", color=ENHANCED['rarity_meta'][pinfo['rarity']]['color'])
        embed.add_field(name="Happiness", value=f"{new_h}% (+{gain}%)", inline=True)
        embed.add_field(name="Coins Earned", value=f"+{coins} 🎋", inline=True)
        embed.add_field(name="Your Balance", value=f"{get_user_currency(user_id)} 🎋", inline=True)
        embed.set_thumbnail(url=pinfo.get("image_url"))
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"/play error: {e}")
        await interaction.followup.send("Unexpected error occurred.")

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

# =================== Fun/Utility/Owner/Admin (original sections preserved) ===================

# ... keeping all original commands below unchanged ...

@tree.command(name="balance", description="Check your bamboo coin balance")
async def balance_cmd(interaction: discord.Interaction):
    try:
        user_id = str(interaction.user.id)
        balance = get_user_currency(user_id)
        user_pandas = get_user_pandas(user_id)
        embed = discord.Embed(title="💰 Your Wallet", description=f"**{balance} bamboo coins**", color=0xf1c40f)
        embed.add_field(name="Adopted Pandas", value=f"{len(user_pandas)}/3", inline=True)
        embed.set_footer(text="Use /work or /daily to earn more coins!")
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        logger.error(f"/balance error: {e}")
        await interaction.response.send_message("Unexpected error occurred.")

# =================== Panda content helpers and other commands ===================

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

# ... keep rest of original fun/utility/admin commands as in your previous file ...

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
