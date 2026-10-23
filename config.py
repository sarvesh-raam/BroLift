import os
import secrets
from dotenv import load_dotenv

load_dotenv()


def _database_url():
    url = os.environ.get('DATABASE_URL')
    # Render / Heroku hand out "postgres://" URLs, which SQLAlchemy 2.x rejects
    if url and url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    return url or 'sqlite:///brolift.db'


class Config:
    # Accept both names; .env.example historically used FLASK_SECRET_KEY.
    # Without a fixed key every restart / worker gets a random one and logs everyone out.
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)

    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    if SQLALCHEMY_DATABASE_URI.startswith('postgresql'):
        # Fail fast instead of hanging the worker if the database is unreachable
        SQLALCHEMY_ENGINE_OPTIONS['connect_args'] = {'connect_timeout': 10}

    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY') or ''

    # Secure session cookies when served over HTTPS (Render sets RENDER=true)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = bool(os.environ.get('RENDER'))
    REMEMBER_COOKIE_SECURE = bool(os.environ.get('RENDER'))
    WTF_CSRF_TIME_LIMIT = None

    # SRM IST Kattankulathur
    COLLEGE_EMAIL_DOMAIN = '@srmist.edu.in'
    COLLEGE_NAME = 'SRM Institute of Science and Technology'
    COLLEGE_LOCATION = {'lat': 12.8231, 'lng': 80.0444}
    TIMEZONE = 'Asia/Kolkata'
    MAX_PASSENGERS = 6  # Up to 7-seater minus driver

    ELECTRIC_COST_PER_KM = 1.50   # Rs per km for electric vehicles
