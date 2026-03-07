# Supply Chain Portal

A semiconductor supply chain intelligence platform for Intel, Broadcom, and Nvidia. View import/export conditions, plan shipments with AI-powered route recommendations, and track shipments with arrival estimates and delay risk factors.

Built for the SYSEN Hackathon.

---

## Features

### 1. Semiconductor Import/Export State
- **AI summary** of current semiconductor importing and exporting conditions
- **Weather forecast** – most severe upcoming weather event in key manufacturing regions (Taiwan, Singapore, Malaysia, South Korea)
- **Geopolitical headlines** – top news affecting supply chain logistics
- Uses Open-Meteo (weather) and Ollama (local LLM) for analysis

### 2. Plan Shipment
- **Route recommendations** – scored by reliability, speed, priority fit, and risk
- **AI-generated plan** – tailored to your notes and concerns
- **Risk factors** – Taiwan Strait alerts, chokepoint exposure, port congestion
- Integrates `routes.py` and `route_suggester.py` with CSV-based risk context

### 3. Track Shipment
- **Estimated arrival** – transit days from origin to destination
- **Delay factors** – weather, geopolitical events, port congestion from historical data
- **Tracking summary** – AI-generated status based on route and risk context

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React, Vite, React Router |
| **Backend** | FastAPI, Python 3.10+ |
| **LLM** | Ollama (gemma3:4b) – runs locally |
| **Weather** | Open-Meteo (free, no API key) |
| **Data** | Static routes + `semiconductor_shipments_500(1).csv` |

---

## Project Structure

```
SYSEN-hackathon/
├── dashboard/                 # React frontend
│   ├── src/
│   │   ├── components/       # Landing, Dashboard, ImportExport, PlanShipment, TrackShipment
│   │   ├── api/               # API client
│   │   └── ...
│   └── package.json
├── backend/                   # FastAPI backend
│   ├── main.py                # API routes
│   ├── routes.py              # Manufacturer nodes, US destinations, shipping lanes
│   ├── route_suggester.py     # Route scoring and recommendations
│   ├── services/
│   │   ├── ollama_service.py  # Ollama (gemma3:4b) integration
│   │   ├── weather_service.py # Open-Meteo
│   │   ├── news_service.py    # Geopolitical headlines
│   │   └── csv_service.py     # CSV loading and risk context
│   └── requirements.txt
├── data/
│   └── semiconductor_shipments_500(1).csv
├── semiconductor_research/    # Research docs (Gemini, travel times, dataset)
└── Workflow                   # User flow specification
```

---

## Prerequisites

- **Node.js** 18+ (for the React app)
- **Python** 3.10+ (for the backend)
- **Ollama** – [install](https://ollama.ai) and pull the model:
  ```bash
  ollama pull gemma3:4b
  ```

---

## Installation

### 1. Clone and enter the project

```bash
cd SYSEN-hackathon
```

### 2. Frontend

```bash
cd dashboard
npm install
```

### 3. Backend

```bash
cd backend
pip install -r requirements.txt
# or: python -m pip install -r requirements.txt
```

---

## Running the App

### 1. Start Ollama (for AI features)

```bash
ollama run gemma3:4b
```

Keep this running. The backend calls `http://localhost:11434`.

### 2. Start the backend

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Start the frontend

```bash
cd dashboard
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## User Flow

1. **Landing page** – Choose one of three options:
   - See state of semiconductor importing and exporting
   - Plan a shipment
   - Track a shipment

2. **Import/Export** – Automatically loads weather, news, and CSV stats, then generates an AI summary. Results shown in cards.

3. **Plan Shipment** – Enter company, origin, destination, part type, priority, notes, and concerns. Receive ranked route recommendations, an AI plan, and risk factors.

4. **Track Shipment** – Select origin and destination. Receive estimated arrival time and possible delay factors.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/import-export/summary` | AI summary + weather + news |
| POST | `/api/plan-shipment` | Route suggestions + AI plan + risk factors |
| POST | `/api/track-shipment` | Arrival estimate + delay factors |
| GET | `/api/nodes` | Manufacturer nodes |
| GET | `/api/destinations` | US destination hubs |
| GET | `/api/lanes` | Shipping lanes |

---

## Data Sources

- **Routes** – Static definitions from `gemini_travel_times_research.md`, `gemini_research.md`, `gemini_dataset_research.md`
- **Shipments** – `data/semiconductor_shipments_500(1).csv` for risk scores, delay patterns, and aggregate stats
- **Weather** – Open-Meteo for semiconductor hub regions

---

## Notes

- If Ollama is not running, the API returns placeholder text instead of AI-generated content.
- CORS is configured for `http://localhost:5173` and `http://127.0.0.1:5173`.
- The frontend uses a dark theme with Outfit font and neumorphic card styling.
