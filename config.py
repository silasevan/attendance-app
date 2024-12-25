import os
from dotenv import load_dotenv

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_secure_random_key'
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or 'sqlite:///attendance.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail Configuration
    


    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')  # Default to example.com if not set
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))  # Default to port 587 if not set
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true') == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = [os.environ.get('MAIL_USERNAME')]