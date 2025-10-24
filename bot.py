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
                merged["available_pandas"] = data.get("available_pandas", DEFAULT_ADOPTION_ADA