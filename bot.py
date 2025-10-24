import discord
from discord.ext import tasks
import aiohttp
import asyncio
import os
import json
import random
from datetime import datetime, time, timedelta
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

# =================== Enhanced Adoption System (Replacements) ===================

ENHANCED_ADOPTION_CONFIG = {
    'happiness_decay': True,
    'decay_interval_hours': 1,
    'max_pandas': 3,
}

PANDA_RARITIES = {
    'common':  { 'name': 'Common',    'color': 0x95a5a6, 'emoji': '🐼',   'base_happy': 80,  'decay_per_h': 2,   'weight': 60 },
    'uncommon':{ 'name': 'Uncommon',  'color': 0x2ecc71, 'emoji': '🐼✨','base_happy': 85,  'decay_per_h': 1.5, 'weight': 25 },
    'rare':    { 'name': 'Rare',      'color': 0x3498db, 'emoji': '🐼💎','base_happy': 90,  'decay_per_h': 1,   'weight': 10 },
    'epic':    { 'name': 'Epic',      'color': 0x9b59b6, 'emoji': '🐼👑','base_happy': 95,  'decay_per_h': 0.5, 'weight': 4 },
    'legendary':{'name': 'Legendary', 'color': 0xf1c40f, 'emoji': '🐼🌟','base_happy': 100, 'decay_per_h': 0,   'weight': 1 },
}

PERSONALITIES = ['playful','calm','curious','gentle','energetic']

def _pick_rarity():
    keys = list(PANDA_RARITIES.keys())
    weights = [PANDA_RARITIES[k]['weight'] for k in keys]
    return random.choices(keys, weights=weights)[0]

def _generate_panda_card():
    rarity = _pick_rarity()
    info = PANDA_RARITIES[rarity]
    name = random.choice(["Bamboo","Mochi","Bao","Ping","Luna","Gizmo","Noodle","Pebble","Snowball","Oreo","Pudding","Button"])    
    personality = random.choice(PERSONALITIES)
    cost = max(50, 100 + [0,50,200,400,800][['common','uncommon','rare','epic','legendary'].index(rarity)] + random.randint(-25,75))
    return {
        'id': f"gen_{int(datetime.utcnow().timestamp())}_{random.randint(1000,9999)}",
        'name': name,
        'rarity': rarity,
        'personality': personality,
        'adoption_fee': cost,
        'base_happiness': info['base_happy'],
        'color': info['color'],
        'emoji': info['emoji'],
        'image_url': "https://images.unsplash.com/photo-1564349683136-77e08dba1ef7?w=400",
        'available': True,
    }

def _current_happiness(adopted_entry, panda_meta):
    if not ENHANCED_ADOPTION_CONFIG['happiness_decay']:
        return adopted_entry.get('happiness', panda_meta['base_happiness'])
    last = max(datetime.fromisoformat(adopted_entry['last_fed']), datetime.fromisoformat(adopted_entry['last_played']))
    hours = (datetime.utcnow() - last).total_seconds()/3600
    decay = PANDA_RARITIES[panda_meta.get('rarity','common')]['decay_per_h']
    return max(0, int(adopted_entry.get('happiness', panda_meta['base_happiness']) - hours*decay))

# ---------------- Replaced Commands ----------------

@tree.command(name="adopt", description="Adopt a new enhanced panda")
async def adopt_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        user_id = str(interaction.user.id)
        if len(get_user_pandas(user_id)) >= ENHANCED_ADOPTION_CONFIG['max_pandas']:
            await interaction.followup.send("❌ You can only adopt up to 3 pandas at a time!")
            return
        card = _generate_panda_card()
        balance = get_user_currency(user_id)
        embed = discord.Embed(title=f"{card['emoji']} {card['name']} needs a home!", color=card['color'])
        embed.add_field(name="Rarity", value=card['rarity'].title(), inline=True)
        embed.add_field(name="Personality", value=card['personality'].title(), inline=True)
        embed.add_field(name="Cost", value=f"{card['adoption_fee']} 🎋", inline=True)
        embed.add_field(name="Base Happiness", value=f"{card['base_happiness']}%", inline=True)
        embed.add_field(name="Your Balance", value=f"{balance} 🎋", inline=True)
        embed.set_thumbnail(url=card['image_url'])
        view = EnhancedAdoptionView(interaction.user.id, card)
        await interaction.followup.send(embed=embed, view=view)
    except Exception as e:
        logger.error(f"/adopt replace error: {e}")
        await interaction.followup.send("Unexpected error occurred.")

@tree.command(name="adoptlist", description="Browse enhanced pandas available right now")
async def adoptlist_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        cards = [_generate_panda_card() for _ in range(3)]
        embed = discord.Embed(title="🐼 Enhanced Adoption Center", description="Choose your companion!", color=0x3498db)
        for i, c in enumerate(cards, 1):
            embed.add_field(name=f"{i}. {c['emoji']} {c['name']}", value=f"Rarity: {c['rarity'].title()}\nPersonality: {c['personality'].title()}\nCost: {c['adoption_fee']} 🎋", inline=True)
        view = MarketplaceView(interaction.user.id, cards)
        await interaction.followup.send(embed=embed, view=view)
    except Exception as e:
        logger.error(f"/adoptlist replace error: {e}")
        await interaction.followup.send("Unexpected error occurred.")

@tree.command(name="mypandas", description="View your pandas with detailed stats")
async def mypandas_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        user_id = str(interaction.user.id)
        owned = get_user_pandas(user_id)
        if not owned:
            await interaction.followup.send(embed=discord.Embed(title="😢 No Pandas Adopted", description="Use `/adopt` to adopt a panda!", color=0xe74c3c))
            return
        embed = discord.Embed(title="🐼 Your Pandas (Enhanced)", description=f"Total: {len(owned)}", color=0x2ecc71)
        for ad in owned:
            p = get_panda_by_id(ad['panda_id']) or {}
            rarity = p.get('rarity','common')
            color = PANDA_RARITIES[rarity]['color'] if rarity in PANDA_RARITIES else 0x2ecc71
            happy = _current_happiness(ad, { 'base_happiness': p.get('base_happiness', 100), 'rarity': rarity })
            embed.add_field(name=f"{p.get('name','Panda')} ({rarity.title()})", value=f"Happiness: {happy}%\nAdopted: {datetime.fromisoformat(ad['adopted_date']).strftime('%Y-%m-%d')}\nLast fed: {datetime.fromisoformat(ad['last_fed']).strftime('%H:%M UTC')}", inline=True)
        embed.add_field(name="💰 Balance", value=f"{get_user_currency(user_id)} 🎋", inline=False)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"/mypandas replace error: {e}")
        await interaction.followup.send("Unexpected error occurred.")

@tree.command(name="feed", description="Feed your panda with enhanced effects")
@discord.app_commands.describe(panda_id="Your panda ID")
async def feed_cmd(interaction: discord.Interaction, panda_id: str):
    await interaction.response.defer()
    try:
        user_id = str(interaction.user.id)
        owned = get_user_pandas(user_id)
        target = next((x for x in owned if x['panda_id'] == panda_id), None)
        if not target:
            await interaction.followup.send("❌ You don't own that panda!")
            return
        pmeta = get_panda_by_id(panda_id) or {}
        rarity = pmeta.get('rarity','common')
        gain = random.randint(8, 18)
        new_h = min(100, target.get('happiness', pmeta.get('base_happiness', 100)) + gain)
        update_panda_stats(user_id, panda_id, 'happiness', new_h)
        update_panda_stats(user_id, panda_id, 'last_fed', datetime.utcnow().isoformat())
        coins = random.randint(6, 12)
        add_user_currency(user_id, coins)
        embed = discord.Embed(title="🍃 Feeding Time (Enhanced)", description=f"Happiness +{gain}%", color=PANDA_RARITIES.get(rarity, {'color':0x27ae60})['color'])
        embed.add_field(name="New Happiness", value=f"{new_h}%", inline=True)
        embed.add_field(name="Coins Earned", value=f"+{coins} 🎋", inline=True)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"/feed replace error: {e}")
        await interaction.followup.send("Unexpected error occurred.")

@tree.command(name="play", description="Play with your panda with enhanced effects")
@discord.app_commands.describe(panda_id="Your panda ID")
async def play_cmd(interaction: discord.Interaction, panda_id: str):
    await interaction.response.defer()
    try:
        user_id = str(interaction.user.id)
        owned = get_user_pandas(user_id)
        target = next((x for x in owned if x['panda_id'] == panda_id), None)
        if not target:
            await interaction.followup.send("❌ You don't own that panda!")
            return
        pmeta = get_panda_by_id(panda_id) or {}
        rarity = pmeta.get('rarity','common')
        gain = random.randint(10, 20)
        new_h = min(100, target.get('happiness', pmeta.get('base_happiness', 100)) + gain)
        update_panda_stats(user_id, panda_id, 'happiness', new_h)
        update_panda_stats(user_id, panda_id, 'last_played', datetime.utcnow().isoformat())
        coins = random.randint(8, 15)
        add_user_currency(user_id, coins)
        embed = discord.Embed(title="🎮 Playtime (Enhanced)", description=f"Happiness +{gain}%", color=PANDA_RARITIES.get(rarity, {'color':0xf39c12})['color'])
        embed.add_field(name="New Happiness", value=f"{new_h}%", inline=True)
        embed.add_field(name="Coins Earned", value=f"+{coins} 🎋", inline=True)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"/play replace error: {e}")
        await interaction.followup.send("Unexpected error occurred.")

# -------- Views used by adoption replacements --------
class EnhancedAdoptionView(discord.ui.View):
    def __init__(self, user_id, card):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.card = card
    @discord.ui.button(label="Adopt", style=discord.ButtonStyle.green, emoji="💖")
    async def adopt_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your adoption!", ephemeral=True)
            return
        uid = str(self.user_id)
        if get_user_currency(uid) < self.card['adoption_fee']:
            await interaction.response.send_message("❌ Not enough bamboo coins!", ephemeral=True)
            return
        subtract_user_currency(uid, self.card['adoption_fee'])
        # materialize panda into available_pandas and user's list
        panda_id = f"enh_{int(datetime.utcnow().timestamp())}_{random.randint(1000,9999)}"
        concrete = {
            'id': panda_id,
            'name': self.card['name'],
            'age': 'Young',
            'personality': self.card['personality'],
            'favorite_food': 'Premium bamboo',
            'special_trait': f"{self.card['rarity'].title()} companion",
            'image_url': self.card['image_url'],
            'adoption_fee': self.card['adoption_fee'],
            'available': False,
            'rarity': self.card['rarity'],
            'base_happiness': self.card['base_happiness'],
        }
        adoption_data['available_pandas'].append(concrete)
        if uid not in adoption_data['adoptions']:
            adoption_data['adoptions'][uid] = []
        adoption_data['adoptions'][uid].append({
            'panda_id': panda_id,
            'adopted_date': datetime.utcnow().isoformat(),
            'happiness': self.card['base_happiness'],
            'last_fed': datetime.utcnow().isoformat(),
            'last_played': datetime.utcnow().isoformat()
        })
        save_adoption_data(adoption_data)
        embed = discord.Embed(title="🎉 Adoption Successful!", description=f"Welcome **{self.card['name']}**!", color=self.card['color'])
        embed.add_field(name="Rarity", value=self.card['rarity'].title(), inline=True)
        embed.add_field(name="Personality", value=self.card['personality'].title(), inline=True)
        embed.add_field(name="Your Balance", value=f"{get_user_currency(uid)} 🎋", inline=True)
        await interaction.response.edit_message(embed=embed, view=None)
    @discord.ui.button(label="Pass", style=discord.ButtonStyle.red, emoji="❌")
    async def pass_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your adoption!", ephemeral=True)
            return
        await interaction.response.edit_message(embed=discord.Embed(title="🚶 Adoption Passed", description="Maybe next time!", color=0x95a5a6), view=None)

class MarketplaceView(discord.ui.View):
    def __init__(self, user_id, cards):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.cards = cards
        for idx, c in enumerate(cards):
            btn = discord.ui.Button(label=f"Adopt {c['name']}", style=discord.ButtonStyle.primary, emoji=c['emoji'], custom_id=f"mk_{idx}")
            btn.callback = self._mk_cb(idx)
            self.add_item(btn)
    def _mk_cb(self, idx):
        async def cb(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("This isn't your marketplace!", ephemeral=True)
                return
            view = EnhancedAdoptionView(self.user_id, self.cards[idx])
            c = self.cards[idx]
            embed = discord.Embed(title=f"Adopt {c['emoji']} {c['name']}?", description=f"Cost: {c['adoption_fee']} 🎋\nRarity: {c['rarity'].title()}\nPersonality: {c['personality'].title()}", color=c['color'])
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        return cb

# =================== Original Slash Commands (non-adoption) remain below ===================

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

@tree.command(name="balance", description="Check your bamboo coin balance")
async def balance_cmd(interaction: discord.Interaction):
    try:
        user_id = str(interaction.user.id)
        balance = get_user_currency(user_id)
        user_pandas = get_user_pandas(user_id)
        embed = discord.Embed(title="💰 Your Wallet", description=f"**{balance} bamboo coins**", color=0xf1c40f)
        embed.add_field(name="Adopted Pandas", value=f"{len(user_pandas)}/{ENHANCED_ADOPTION_CONFIG['max_pandas']}", inline=True)
        embed.set_footer(text="Use /work or /daily to earn more coins!")
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        logger.error(f"/balance error: {e}")
        await interaction.response.send_message("Unexpected error occurred.")

@tree.command(name="work", description="Work to earn bamboo coins")
async def work_cmd(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        user_id = str(interaction.user.id)
        last_work_key = f"last_work_{user_id}"
        current_time = datetime.utcnow()
        if last_work_key in adoption_data["user_currency"]:
            last_work_time = datetime.fromisoformat(adoption_data["user_currency"][last_work_key])
            time_since_work = current_time - last_work_time
            if time_since_work.total_seconds() < 1800:
                minutes_left = int((1800 - time_since_work.total_seconds()) / 60)
                await interaction.followup.send(f"💼 You're tired from working! Rest for {minutes_left} more minutes.")
                return
        coins_earned = random.randint(20, 50)
        add_user_currency(user_id, coins_earned)
        adoption_data["user_currency"][last_work_key] = current_time.isoformat()
        save_adoption_data(adoption_data)
        jobs = ["helped at the bamboo farm","cleaned the panda sanctuary","guided tourists at the zoo","delivered bamboo supplies","assisted panda researchers","organized adoption paperwork"]
        embed = discord.Embed(title="💼 Work Complete!", description=f"You {random.choice(jobs)} and earned **{coins_earned} bamboo coins**!", color=0x3498db)
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
        last_daily_key = f"last_daily_{user_id}"
        current_time = datetime.utcnow()
        if last_daily_key in adoption_data["user_currency"]:
            last_daily_time = datetime.fromisoformat(adoption_data["user_currency"][last_daily_key])
            time_since_daily = current_time - last_daily_time
            if time_since_daily.total_seconds() < 86400:
                hours_left = int((86400 - time_since_daily.total_seconds()) / 3600)
                await interaction.followup.send(f"🎁 Daily bonus already claimed! Come back in {hours_left} hours.")
                return
        daily_bonus = 100
        add_user_currency(user_id, daily_bonus)
        adoption_data["user_currency"][last_daily_key] = current_time.isoformat()
        save_adoption_data(adoption_data)
        embed = discord.Embed(title="🎁 Daily Bonus!", description=f"You claimed your daily bonus of **{daily_bonus} bamboo coins**!", color=0xe74c3c)
        embed.add_field(name="Your Balance", value=f"{get_user_currency(user_id)} bamboo coins", inline=True)
        embed.set_footer(text="Come back tomorrow for another bonus!")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        logger.error(f"/daily error: {e}")
        await interaction.followup.send("Unexpected error occurred.")

# keep other fun/utility/admin commands as they were previously ...

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
