# Supply Chain Portal Backend

FastAPI backend with OpenAI GPT-4o, weather, news, and CSV-based decision support.

## Setup

```bash
cd backend
pip install -r requirements.txt
```

## Configure API keys

Add these to your `.env` file at the project root:

```bash
# Required for AI summaries
OPENAI_API_KEY=your_api_key_here

# For Supabase (shipment data). If omitted, falls back to CSV.
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

## Start the API

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints

- `POST /api/import-export/summary` – AI summary + weather + news
- `POST /api/plan-shipment` – Route suggestions + AI plan
- `POST /api/track-shipment` – Arrival estimate + delay factors
- `GET /api/nodes` – Manufacturer nodes
- `GET /api/destinations` – US destinations
- `GET /api/lanes` – Shipping lanes
