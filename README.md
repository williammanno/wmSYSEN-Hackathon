# Supply Chain Portal

Semiconductor supply chain intelligence platform built for the SYSEN Hackathon.

This project now uses **OpenAI only** for LLM features (no Ollama/local model runtime).

The app helps users:
- understand current import/export conditions,
- generate route-aware shipment plans, and
- track expected shipment risk and arrival windows.

---

## What the App Does

The product has three primary workflows:

1. **Import/Export State**
   - Pulls weather risk by region.
   - Pulls geopolitical headlines.
   - Pulls aggregate shipment metrics from CSV history.
   - Uses GPT-4o to generate a concise executive summary.

2. **Plan Shipment**
   - Takes shipment inputs (company, origin, destination, part type, priority, notes).
   - Uses deterministic route scoring from `route_suggester.py`.
   - Produces top route recommendations with score, duration, and cost tier.
   - Uses GPT-4o to generate a short operational plan and risk narrative.
   - Falls back to a deterministic text plan if LLM output is unavailable.

3. **Track Shipment**
   - Looks up lane transit ranges.
   - Computes delay/risk factors using weather + geopolitical + historical context.
   - Estimates expected arrival window/date.
   - Uses GPT-4o to generate a short tracking summary.

---

## How It Works (Architecture)

### Frontend (`dashboard/`)

- React + Vite SPA using route-based pages:
  - `/` landing
  - `/import-export`
  - `/plan-shipment`
  - `/track-shipment`
  - `/explore-data`
- All API calls live in `dashboard/src/api/client.js`.
- API base URL comes from `VITE_API_BASE_URL`.
  - If omitted, requests default to relative paths (good for same-origin deploys).

### Backend (`backend/`)

- FastAPI application in `backend/main.py`.
- Core endpoint groups:
  - `POST /api/import-export/summary`
  - `POST /api/plan-shipment`
  - `POST /api/track-shipment`
  - Reference endpoints: `/api/nodes`, `/api/destinations`, `/api/lanes`
- Service layer:
  - `backend/services/openai_service.py` (GPT-4o text generation)
  - `backend/services/weather_service.py` (Open-Meteo)
  - `backend/services/news_service.py` (headlines)
  - `backend/services/csv_service.py` (historical shipment analytics)

### Data + Decisioning

- `backend/routes.py` defines canonical nodes, destinations, and shipping lanes.
- `backend/route_suggester.py` scores route options with business/risk heuristics.
- `data/semiconductor_shipments_500(1).csv` powers historical delay/risk context.

### Runtime Behavior

- In **local dev**, frontend runs on Vite and backend runs on Uvicorn.
- In **production**, backend can also serve the built frontend (`backend/static`) as a single deployable app.

---

## Project Structure

```text
SYSEN-hackathon/
├── dashboard/                       # React frontend (Vite)
│   ├── src/
│   │   ├── api/client.js            # API client wrapper
│   │   └── components/              # UI screens/components
│   └── package.json
├── backend/                         # FastAPI backend
│   ├── main.py                      # API + production static serving
│   ├── route_suggester.py           # Route scoring logic
│   ├── routes.py                    # Nodes/destinations/lanes
│   ├── services/
│   │   ├── openai_service.py
│   │   ├── weather_service.py
│   │   ├── news_service.py
│   │   └── csv_service.py
│   ├── scripts/prepare_frontend.py  # Copies dashboard/dist -> backend/static
│   └── requirements.txt
├── data/                            # Historical shipment data
└── README.md
```

---

## Environment Variables

Create a root `.env` file:

```bash
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o
```

Optional:

```bash
# Comma-separated list of allowed browser origins for CORS.
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Path to built frontend directory for production serving.
FRONTEND_BUILD_DIR=backend/static

# Frontend API base URL at build/runtime (Vite).
VITE_API_BASE_URL=
```

> `OPENAI_API_KEY` is required for AI-generated summaries/plans/tracking text.
> Ollama is deprecated/removed from this project.

---

## Run Locally (Development)

### 1) Install dependencies

Frontend:

```bash
cd dashboard
npm install
```

Backend:

```bash
cd ../backend
pip install -r requirements.txt
```

### 2) Start backend API

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3) Start frontend app

```bash
cd dashboard
npm run dev
```

Open:
- Frontend: `http://localhost:5173`
- Backend docs: `http://localhost:8000/docs`

### Dev networking notes

- Vite proxies `/api/*` to `http://localhost:8000` (configured in `dashboard/vite.config.js`).
- You can keep `VITE_API_BASE_URL` empty for local dev.

---

## Run Locally (Production-like Single Process)

This mode builds the SPA and serves it directly from FastAPI.

```bash
# Build frontend
cd dashboard
npm run build

# Copy build output into backend/static
cd ../backend
python scripts/prepare_frontend.py

# Start API + static app
uvicorn main:app --host 0.0.0.0 --port 8000
```

Then open `http://localhost:8000`.

---

## API Reference

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/import-export/summary` | Weather/news/data synthesis + GPT summary |
| POST | `/api/plan-shipment` | Route recommendations + GPT shipment plan |
| POST | `/api/track-shipment` | Transit estimate + risk score + GPT tracking summary |
| GET | `/api/nodes` | Manufacturer origins |
| GET | `/api/destinations` | US destination hubs |
| GET | `/api/lanes` | Shipping lane definitions |

---

## Deploy to Posit Connect

This project is prepared for Posit Connect as a FastAPI deployment with optional bundled frontend.

### Deployment model

- Deploy the `backend/` directory as a FastAPI content item.
- Bundle frontend assets into `backend/static` before deployment if you want one URL serving both API + UI.

### 1) Build and bundle frontend assets

From repo root:

```bash
cd dashboard
npm ci
npm run build

cd ../backend
python scripts/prepare_frontend.py
```

### 2) Install deployment CLI

```bash
pip install rsconnect-python
```

### 3) Register your Posit Connect server

```bash
rsconnect add \
  --name my-connect \
  --server https://your-connect-server.example.com \
  --api-key YOUR_CONNECT_API_KEY
```

### 4) Deploy FastAPI app

From repo root:

```bash
rsconnect deploy fastapi \
  -n my-connect \
  --entrypoint main:app \
  backend/
```

### 5) Configure secrets on Posit Connect

Set these as environment variables in the Connect content settings:

- `OPENAI_API_KEY` (required)
- `OPENAI_MODEL` (optional, default `gpt-4o`)
- `CORS_ORIGINS` (only needed if frontend is hosted on a different origin)
- `FRONTEND_BUILD_DIR` (optional, default `backend/static` in deployed bundle)

### 6) Validate deployment

- Open deployed URL.
- Confirm SPA loads (if bundled).
- Test API docs endpoint `/docs`.
- Test all three workflows end-to-end with live OpenAI key.

---

## Troubleshooting

- **401 Unauthorized from OpenAI**
  - Validate `OPENAI_API_KEY`.
  - Ensure key is from the OpenAI Platform API keys page.
  - Ensure billing is enabled for API usage.
- **Looking for Ollama setup?**
  - Ollama is no longer supported in this codebase.
  - Configure `OPENAI_API_KEY` instead.

- **Frontend shows network/CORS errors**
  - In dev, ensure backend is running on `:8000`.
  - In production cross-origin setups, set `CORS_ORIGINS`.

- **Frontend not loading in production**
  - Re-run `npm run build` in `dashboard/`.
  - Re-run `python backend/scripts/prepare_frontend.py`.
  - Confirm `backend/static/index.html` exists before deployment.
