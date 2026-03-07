# Supply Chain Portal Backend

FastAPI backend with Ollama (gemma3:4b), weather, news, and CSV-based decision support.

## Setup

```bash
cd backend
pip install -r requirements.txt
```

## Run Ollama (required for AI summaries)

```bash
ollama run gemma3:4b
```

Keep Ollama running. The API calls `http://localhost:11434`.

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
