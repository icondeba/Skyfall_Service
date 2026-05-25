"""PaymentStatus - Enum value object."""
from enum import Enum


class PaymentStatus(str, Enum):
    """Status of a payment."""
    
    UNPAID = "unpaid"
    PARTIAL = "partial"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    
    @classmethod
    def from_amounts(cls, paid: float, total: float) -> "PaymentStatus":
        """Determine payment status from amounts.
        
        Args:
            paid: Amount paid so far
            total: Total amount due
            
        Returns:
            PaymentStatus enum value
        """
        if paid <= 0:
            return cls.UNPAID
        if paid + 0.01 < total:  # Small tolerance for float precision
            return cls.PARTIAL
        return cls.PAID
