import os
from dotenv import load_dotenv, find_dotenv


class Config:
    load_dotenv(find_dotenv(".env"))

    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    LANGUAGES = ['en', 'es']
    DEBUG = os.getenv("DEBUG")
    LABEL_DEFAULT_LOCALE = 'en'
    LABEL_DEFAULT_TIMEZONE = 'UTC'
    

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///flask-test.db'
    WTF_CSRF_ENABLED = False
