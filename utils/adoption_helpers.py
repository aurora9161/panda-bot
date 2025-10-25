from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from .config import adoption_data, save_adoption_data

logger = logging.getLogger(__name__)

def get_user_currency(user_id: str) -> int:
    """Get user's bamboo coin balance"""
    return adoption_data["user_currency"].get(user_id, 100)  # Default starting currency

def add_user_currency(user_id: str, amount: int) -> None:
    """Add bamboo coins to user's balance"""
    current = get_user_currency(user_id)
    adoption_data["user_currency"][user_id] = current + amount
    save_adoption_data(adoption_data)

def subtract_user_currency(user_id: str, amount: int) -> bool:
    """Subtract bamboo coins from user's balance. Returns True if successful."""
    current = get_user_currency(user_id)
    if current >= amount:
        adoption_data["user_currency"][user_id] = current - amount
        save_adoption_data(adoption_data)
        return True
    return False

def get_available_pandas() -> List[Dict[str, Any]]:
    """Get list of pandas available for adoption"""
    return [p for p in adoption_data["available_pandas"] if p["available"]]

def get_panda_by_id(panda_id: str) -> Optional[Dict[str, Any]]:
    """Get panda data by ID"""
    for panda in adoption_data["available_pandas"]:
        if panda["id"] == panda_id:
            return panda
    return None

def adopt_panda(user_id: str, panda_id: str) -> bool:
    """Adopt a panda. Returns True if successful."""
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

def get_user_pandas(user_id: str) -> List[Dict[str, Any]]:
    """Get user's adopted pandas"""
    return adoption_data["adoptions"].get(user_id, [])

def update_panda_stats(user_id: str, panda_id: str, stat: str, value: Any) -> bool:
    """Update panda statistics. Returns True if successful."""
    user_pandas = get_user_pandas(user_id)
    for adopted_panda in user_pandas:
        if adopted_panda["panda_id"] == panda_id:
            adopted_panda[stat] = value
            save_adoption_data(adoption_data)
            return True
    return False