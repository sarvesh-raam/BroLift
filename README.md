# 🚗 BroLift: Smart College Carpooling Network

A high-performance system for academic commute coordination. It cross-references student verification with real-time routing to optimize campus transport and reduce structural inefficiencies in college transit.

[![CI Pipeline](https://github.com/sarvesh-raam/BroLift/actions/workflows/python-app.yml/badge.svg)](https://github.com/sarvesh-raam/BroLift/actions)
[![Render Deployment](https://img.shields.io/badge/Render-Deployed-black?logo=render)](https://brolift.onrender.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

---

## Executive Summary
BroLift (Autonomous Ride Intelligence) provides high-fidelity carpooling coordination. The system automates the matching of student drivers and passengers within a verified network by integrating Google Maps routing and deterministic fuel-cost inference models.

👉 **Optimized for low-latency responses, generating route calculations within milliseconds.**
👉 **Designed as a scalable full-stack system capable of handling real-time ride tracking with optimized passenger matching.**

## Interface Preview

| Home Dashboard | Real-time Search | Ride Management |
| :---: | :---: | :---: |
| ![Home](assets/home.png) | ![Search](assets/search.png) | ![Management](assets/management.png) |

## Deployment
- **Frontend & API**: Deployed on Render [View Live Dashboard](https://brolift.onrender.com)
- **Database Layer**: Managed PostgreSQL instance on Render

## Architecture Diagram

```mermaid
graph TD
    A[Client Browser] -->|HTTP/HTTPS| B(Flask Web Server)
    B -->|SQLAlchemy ORM| C[(PostgreSQL Database)]
    B -.->|Directions & Places| D[Google Maps API]
    A -.->|JavaScript Init| D
    B -->|Authentication| E(Flask-Login)
```

<details>
<summary>View detailed dependency graph</summary>

```mermaid
graph LR
    A[Jinja2 / JS Frontend] -->|REST API Requests| B[Flask Backend]
    B -->|Schema Validation| C[(PostgreSQL / SQLite)]
    B -->|Route Generation| D[Google Directions API]
    C -->|User & Ride Data| B
    D -->|Polyline Data| B
    B -->|JSON Response| A
```
</details>

## System Design
- Handles verified academic ingestion pipeline (@srmist.edu.in)
- Uses spatial indexing for efficient pickup retrieval
- Optimized API responses for low latency route calculation

## System Architecture & Components
- **Frontend Dashboard**: Responsive Material Design interface providing real-time ride discovery.
- **Backend API**: Python Flask layer handling ride lifecycle, orchestration, and integrations.
- **Network Infrastructure**: Strict SRM IST email verification combined with regex-based credential auditing.
- **Routing Intelligence Mesh**: High-performance inference via Google Maps API for institutional transit reasoning.
- **Strategic Cost Gateway**: Real-time integration with fuel price metrics for fair-split financials.

## API Flow
1. **Ride Creation (`/rides/host`)**: Hosts define route and capacity; data is serialized into PostgreSQL.
2. **Ride Query (`/rides/find`)**: Passengers perform spatial searches against the ride database.
3. **Request Logic**: Passengers request joins; backend validates capacity and overlaps.
4. **Financial Evaluation**: Cost-per-head is computed using real-time fuel data and vehicle mileage.
5. **Route Visualization**: Polylines are generated and streamed to the frontend via Google Maps JS SDK.

## Example Output Payload
```json
{
  "status": "success",
  "data": {
    "ride_id": 104,
    "classification": "Standard Car",
    "route": "SRM Main Gate -> Chennai Central",
    "cost_per_head": 142.50,
    "confidence_level": 0.98
  }
}
```

## Environment & Deployment

### Hardware & Engine Requirements
- Python 3.10+ Runtime
- PostgreSQL 15+ 
- External API Gateways: Google Maps (Directions, Places, Maps)

### Infrastructure Initialization
**A. Application Service (Flask)**
```bash
# Initialize environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run server
python run.py
```

## Technical Roadmap
- Multi-Agent Orchestration: Implementation of automated pickup scheduling loops to increase detection accuracy.
- SRM/KTR Integration: Direct ingestion of campus event schedules for high-demand ride prediction.

## License
Distributed under the MIT License. Professional use only.
