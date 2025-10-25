import random
import logging
from typing import Optional, Tuple
from .http_client import HTTPClient
from .constants import SRA_PANDA, SRA_RED_PANDA, QUOTES_API, JOKE_API, PANDA_FACTS, PANDA_JOKES

logger = logging.getLogger(__name__)

class PandaAPI:
    """Helper class for panda-related API calls"""
    
    def __init__(self):
        self.http = HTTPClient()
    
    async def close(self):
        """Close HTTP client"""
        await self.http.close()
    
    async def _fetch_sra_animal(self, primary: str, fallback: str) -> Tuple[Optional[str], Optional[str]]:
        """Fetch data from Some Random API with fallback"""
        for url in (primary, fallback):
            data = await self.http.get_json(url)
            if isinstance(data, dict):
                img = data.get("image")
                fact = data.get("fact")
                if img or fact:
                    return img, fact
        return None, None
    
    async def fetch_panda_image(self) -> Optional[str]:
        """Fetch a panda image URL"""
        img, _ = await self._fetch_sra_animal(SRA_PANDA, SRA_RED_PANDA)
        return img
    
    async def fetch_panda_gif(self) -> Optional[str]:
        """Fetch a panda GIF URL (if available)"""
        img, _ = await self._fetch_sra_animal(SRA_PANDA, SRA_RED_PANDA)
        if img and img.lower().endswith(".gif"):
            return img
        return None
    
    async def fetch_panda_fact(self) -> str:
        """Fetch a panda fact (API or fallback)"""
        _, fact = await self._fetch_sra_animal(SRA_PANDA, SRA_RED_PANDA)
        if fact:
            return fact
        return random.choice(PANDA_FACTS)
    
    async def fetch_quote(self) -> Optional[Tuple[str, str]]:
        """Fetch an inspirational quote"""
        data = await self.http.get_json(QUOTES_API)
        try:
            if isinstance(data, list) and data:
                q = data[0]
                return q.get("content"), q.get("author", "Unknown")
        except Exception as e:
            logger.error(f"Quote parse error: {e}")
        return None
    
    async def fetch_joke(self) -> Optional[str]:
        """Fetch a random joke (API or fallback)"""
        data = await self.http.get_json(JOKE_API)
        if isinstance(data, dict):
            j = data.get("joke")
            if j:
                return j
        return random.choice(PANDA_JOKES)