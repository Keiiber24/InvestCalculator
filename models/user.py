from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from .database import db

class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)

    # Define relationship with trades only
    trades = db.relationship('Trade', 
                         back_populates='user',
                         lazy='dynamic',
                         cascade='all, delete-orphan')

    def __init__(self, email, username, password=None):
        self.email = email.lower()
        self.username = username
        if password:
            self.set_password(password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def active_trades(self):
        """Get trades with remaining units"""
        return self.trades.filter(db.text('remaining_units > 0')).all()

    @property
    def closed_trades(self):
        """Get trades with no remaining units"""
        return self.trades.filter(db.text('remaining_units = 0')).all()

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'active': self.active,
            'trades_count': self.trades.count()
        }

    @staticmethod
    def get_by_email(email):
        return User.query.filter_by(email=email.lower()).first()

    @staticmethod
    def get_by_username(username):
        return User.query.filter_by(username=username).first()

    def __repr__(self):
        return f'<User {self.username}>'
