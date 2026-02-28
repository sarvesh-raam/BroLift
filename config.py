import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'brolift-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///brolift.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY') or 'YOUR_GOOGLE_MAPS_API_KEY_HERE'
    COLLEGE_EMAIL_DOMAIN = '.edu'
    COLLEGE_NAME = 'BroLift University'
    COLLEGE_LOCATION = {'lat': 12.9716, 'lng': 77.5946}  # Default: Bangalore coords
    MAX_PASSENGERS = 4
