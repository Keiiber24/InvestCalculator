# First import the database instance
from .database import db, login_manager

# Import models in correct dependency order
from .user import User
from .trade import Trade
from .sale import Sale

# Make them available at package level
__all__ = ['db', 'login_manager', 'User', 'Trade', 'Sale']
