import aiohttp
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class HTTPClient:
    """Async HTTP client for API requests"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def ensure_session(self):
        """Ensure HTTP session is created"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=12)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def get_json(self, url: str) -> Optional[Dict[str, Any]]:
        """Make GET request and return JSON response"""
        await self.ensure_session()
        try:
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.warning(f"HTTP {resp.status} for {url}")
        except Exception as e:
            logger.error(f"HTTP error for {url}: {e}")
        return None