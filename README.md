# 🚗 BroLift — College Carpooling Web App

> **Smart carpooling for college students.** Share rides, split fuel costs, and commute sustainably.

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-black?style=flat&logo=flask)
![SQLite](https://img.shields.io/badge/Database-SQLite-blue?style=flat&logo=sqlite)
![Google Maps](https://img.shields.io/badge/Maps-Google%20Maps%20API-green?style=flat&logo=googlemaps)

---

## 📌 About

**BroLift** is a college-only carpooling web application that allows students to:
- 🚗 **Host rides** to college by sharing their starting location, departure time, and available seats
- 🔍 **Find rides** near their pickup location
- 💰 **Split fuel costs** automatically among all passengers
- 📍 **View routes** on Google Maps with real-time directions

> Only students with verified `.edu` college emails can register.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔐 College Email Auth | Only `.edu` emails allowed — verified student community |
| 🚗 Host a Ride | Set start location, time, seats (max 4), fuel cost |
| 🔍 Find a Ride | Search by pickup area and preferred departure time |
| 💰 Auto Fuel Split | Cost divided equally among host + passengers |
| 📍 Google Maps | Route visualization + address autocomplete |
| ✅ Ride Status | Pending → Confirmed → Completed tracking |
| 👥 Max 4 Passengers | Safe, comfortable rides |
| 🌱 Eco-Friendly | Fewer cars = less traffic = greener campus |

---

## 🛠️ Tech Stack

- **Backend**: Python, Flask, Flask-Login, SQLAlchemy
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Frontend**: HTML5, Vanilla CSS, Vanilla JS
- **Maps**: Google Maps JavaScript API, Places API, Directions API
- **Auth**: Werkzeug password hashing + Flask-Login sessions

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Google Maps API Key ([Get one free](https://console.cloud.google.com))

### 1. Clone the repo
```bash
git clone https://github.com/sarvesh-raam/BroLift.git
cd BroLift
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set your Google Maps API Key
Open `config.py` and replace the API key:
```python
GOOGLE_MAPS_API_KEY = 'YOUR_GOOGLE_MAPS_API_KEY_HERE'
```

> **Or** use a `.env` file (recommended):
```bash
GOOGLE_MAPS_API_KEY=your_key_here
```

### 4. Run the app
```bash
python run.py
```

Visit: **http://127.0.0.1:5000**

---

## 📂 Project Structure

```
BroLift/
├── app/
│   ├── __init__.py          # App factory
│   ├── models.py            # User, Ride, RideRequest models
│   ├── routes/
│   │   ├── auth.py          # Register, Login, Profile
│   │   ├── rides.py         # Host, Find, Request rides
│   │   └── dashboard.py     # Dashboard + Landing
│   └── templates/
│       ├── base.html
│       ├── landing.html
│       ├── auth/            # Login, Register, Profile
│       ├── rides/           # Host, Find, Detail
│       └── dashboard/
├── static/
│   ├── css/style.css        # Dark premium UI
│   └── js/main.js
├── config.py
├── run.py
└── requirements.txt
```

---

## 🗺️ Required Google Maps APIs

Enable these in [Google Cloud Console](https://console.cloud.google.com/apis/library):
- ✅ Maps JavaScript API
- ✅ Places API
- ✅ Directions API
- ✅ Geocoding API

---

## 🔮 Future Roadmap

- [ ] PWA support (installable as mobile app)
- [ ] Real-time notifications
- [ ] In-app chat between host & passengers
- [ ] Ratings & reviews
- [ ] React Native mobile app

---

## 👤 Author

**Sarvesh Raam** — [@sarvesh-raam](https://github.com/sarvesh-raam)

---

## 📄 License

MIT License — free to use for academic projects.
