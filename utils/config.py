import json
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Config file paths
CONFIG_PATH = os.getenv("CONFIG_PATH", "config.json")
ADOPTION_PATH = os.getenv("ADOPTION_PATH", "adoption_data.json")

# Default configurations
DEFAULT_CONFIG = {
    "daily_channel_id": None,
    "daily_time": os.getenv("DEFAULT_DAILY_TIME", "12:00"),
    "timezone": os.getenv("DEFAULT_TIMEZONE", "UTC"),
    "enabled": False
}

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

def load_config() -> Dict[str, Any]:
    """Load configuration from file"""
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

def save_config(data: Dict[str, Any]) -> None:
    """Save configuration to file"""
    try:
        tmp_path = f"{CONFIG_PATH}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, CONFIG_PATH)
    except Exception as e:
        logger.error(f"Failed to save config.json: {e}")

def load_adoption_data() -> Dict[str, Any]:
    """Load adoption data from file"""
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

def save_adoption_data(data: Dict[str, Any]) -> None:
    """Save adoption data to file"""
    try:
        tmp_path = f"{ADOPTION_PATH}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, ADOPTION_PATH)
    except Exception as e:
        logger.error(f"Failed to save adoption_data.json: {e}")

# Initialize data at module load
config_data = load_config()
adoption_data = load_adoption_data()