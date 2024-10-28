# First import the database
from .database import db, login_manager

# Then import models in dependency order
from .user import User
from .trade import Trade
from .sale import Sale

# Make sure database is initialized before models are used
__all__ = ['db', 'login_manager', 'User', 'Trade', 'Sale']
