from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    trades = db.relationship('Trade', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    market = db.Column(db.String(50), nullable=False)
    entry_price = db.Column(db.Float, nullable=False)
    units = db.Column(db.Float, nullable=False)
    remaining_units = db.Column(db.Float, nullable=False)
    position_size = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sales = db.relationship('Sale', backref='trade', lazy=True)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    units_sold = db.Column(db.Float, nullable=False)
    exit_price = db.Column(db.Float, nullable=False)
    partial_pl = db.Column(db.Float, nullable=False)
    partial_pl_percentage = db.Column(db.Float, nullable=False)
    trade_id = db.Column(db.Integer, db.ForeignKey('trade.id'), nullable=False)
