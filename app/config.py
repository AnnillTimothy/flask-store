import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///store.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload

    # PayFast settings
    PAYFAST_MERCHANT_ID = os.environ.get('PAYFAST_MERCHANT_ID', '10000100')
    PAYFAST_MERCHANT_KEY = os.environ.get('PAYFAST_MERCHANT_KEY', '46f0cd694581a')
    PAYFAST_PASSPHRASE = os.environ.get('PAYFAST_PASSPHRASE', '')
    PAYFAST_SANDBOX = os.environ.get('PAYFAST_SANDBOX', 'True') == 'True'

    SHIPPING_COST = 150.0
