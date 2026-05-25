"""OrderStatus - Enum value object."""
from enum import Enum


class OrderStatus(str, Enum):
    """Status of an order."""
    
    PENDING = "pending"
    SERVED = "served"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"
