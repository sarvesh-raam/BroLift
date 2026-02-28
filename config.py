import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'brolift-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///brolift.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY') or 'YOUR_GOOGLE_MAPS_API_KEY_HERE'
    # SRM IST Kattankulathur — fixed college destination
    COLLEGE_EMAIL_DOMAIN = '@srmist.edu.in'
    COLLEGE_NAME = 'SRM Institute of Science and Technology'
    COLLEGE_LOCATION = {'lat': 12.8231, 'lng': 80.0444}
    MAX_PASSENGERS = 4
