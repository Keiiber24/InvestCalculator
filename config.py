# config.py
import os

class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'dev_key_only_for_development'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "investment.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'