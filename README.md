# Breathe ESG — Emissions Ingestion Platform

Live demo: https://breathe-esg-1-h9p6.onrender.com
Backend API: https://breathe-esg-backend-uixk.onrender.com


## What This Does

Ingests emissions data from three enterprise sources, normalizes to kg CO₂e, and surfaces an analyst review dashboard for approval before audit lock.

**Three data sources:**
- **SAP flat file** (Scope 1) — fuel & procurement exports with German header support
- **Utility CSV** (Scope 2) — electricity billing data with non-calendar period handling
- **Concur/Navan CSV** (Scope 3) — flight, hotel, ground transport with IATA code distance lookup

## Stack

- **Backend:** Django 5.2 + Django REST Framework — Python
- **Frontend:** React (Create React App)
- **Database:** SQLite (dev) / PostgreSQL (prod)

## Run Locally (5 minutes)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python seed_data.py             # loads sample data
python manage.py runserver      # runs on :8000
```

### Frontend

```bash
cd frontend
npm install
npm start                       # runs on :3000
```

Open http://localhost:3000

## Key Documents

- `MODEL.md` — Data model design and rationale
- `DECISIONS.md` — Every ambiguity resolved and why  
- `TRADEOFFS.md` — Three things deliberately not built
- `SOURCES.md` — Research on each data source format

## Sample CSV Files

Download from the **Ingest Data** tab in the app. Three pre-built sample files:
- `sample_sap.csv` — SAP fuel export with German-style data
- `sample_utility.csv` — Utility meter data with non-calendar billing periods
- `sample_travel.csv` — Concur-style travel with flights, hotels, taxis
