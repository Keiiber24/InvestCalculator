from .database import db
from .user import User
from .trade import Trade

# No need to access the relationship here anymore
__all__ = ['db', 'User', 'Trade']
