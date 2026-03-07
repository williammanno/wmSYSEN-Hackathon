# Supply Chain Portal Backend

FastAPI backend with OpenAI GPT-4o, weather, news, and CSV-based decision support.

## Setup

```bash
cd backend
pip install -r requirements.txt
```

## Configure environment (required for AI summaries)

Add this to your root `.env`:

```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o
```

Optional:

```bash
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
FRONTEND_BUILD_DIR=backend/static
```

## Start the API

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Serve built frontend from backend (production-style)

```bash
cd ../dashboard
npm run build
cd ../backend
python scripts/prepare_frontend.py
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Endpoints

- `POST /api/import-export/summary` – AI summary + weather + news
- `POST /api/plan-shipment` – Route suggestions + AI plan
- `POST /api/track-shipment` – Arrival estimate + delay factors
- `GET /api/nodes` – Manufacturer nodes
- `GET /api/destinations` – US destinations
- `GET /api/lanes` – Shipping lanes
