import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'brolift-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///brolift.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY') or 'YOUR_GOOGLE_MAPS_API_KEY_HERE'

    # SRM IST Kattankulathur
    COLLEGE_EMAIL_DOMAIN = '@srmist.edu.in'
    COLLEGE_NAME = 'SRM Institute of Science and Technology'
    COLLEGE_LOCATION = {'lat': 12.8231, 'lng': 80.0444}
    MAX_PASSENGERS = 6  # Up to 7‑seater minus driver

    # Real-time fuel prices in Rs (Chennai, updated Feb 2026)
    # Source: Indian Oil Corporation / PPAC
    FUEL_PRICES = {
        'petrol':   102.63,   # Rs per litre
        'diesel':    88.74,   # Rs per litre
        'cng':       72.00,   # Rs per kg (~1 kg ≈ 1 litre equivalent)
        'electric':   0.00,   # Handled separately (Rs per km)
    }
    ELECTRIC_COST_PER_KM = 1.50   # Rs per km for electric vehicles
