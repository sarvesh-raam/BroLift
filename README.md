# Smart College Carpooling System

A dedicated carpooling platform designed exclusively for college networks, enabling students to share rides, split costs, and commute sustainably.

[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat&logo=python)](#)
[![Flask](https://img.shields.io/badge/Flask-3.x-black?style=flat&logo=flask)](#)

---

## Executive Summary
This application provides a secure, verified environment for college students to coordinate daily commutes. By restricting access to verified academic email addresses, the platform ensures user safety while reducing campus traffic and carbon emissions.

## Architecture and System Design
The application implements a robust monolithic architecture with clean separation of concerns.

- **Frontend Interface**: HTML5, Vanilla CSS, and Vanilla JavaScript for responsive interactions.
- **Backend Logic**: Python and Flask.
- **Database Layer**: SQLite (development) / PostgreSQL (production) with SQLAlchemy ORM.
- **External Integrations**: Google Maps JavaScript API, Places API, and Directions API for route calculation and address resolution.

## Core Features
- **Academic Verification**: Strict registration flow allowing only verified `.edu` email addresses.
- **Ride Hosting**: Users can schedule departures, set available capacity (up to 4 passengers), and define route parameters.
- **Intelligent Discovery**: Search functionality based on proximity to pickup zones and departure windows.
- **Automated Financials**: Fair cost division calculated automatically among the host and all confirmed passengers.
- **Real-time Routing**: Integration with Google Maps for precise route visualization and tracking.

## Technical Structure
```text
app/
├── __init__.py          # App factory initialization
├── models.py            # Relational models (User, Ride, Request)
├── routes/
│   ├── auth.py          # Authentication and session logic
│   ├── rides.py         # Ride lifecycle management
│   └── dashboard.py     # Main views
└── templates/           # Jinja2 views
```

## Quickstart Guide

### Prerequisites
- Python 3.8+
- Google Maps API Key

### Installation
```bash
git clone https://github.com/sarvesh-raam/BroLift.git
cd BroLift
pip install -r requirements.txt
```

### Configuration
Configure your Google Maps API Key in `config.py` or `.env`:
```bash
GOOGLE_MAPS_API_KEY=your_production_key_here
```

### Execution
```bash
python run.py
```
Navigate to `http://127.0.0.1:5000` to access the local development server.

## Future Development
- Progressive Web App (PWA) implementation for native mobile experience.
- Real-time WebSocket notifications.
- Integrated communication channels between hosts and passengers.
- Reputation and review system.
