"""
Supply Chain Portal API – semiconductor import/export, planning, tracking.
Uses Ollama (gemma3:4b) for LLM, Open-Meteo for weather, routes + CSV for decisions.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from routes import MANUFACTURER_NODES, US_DESTINATIONS, SHIPPING_LANES, get_lane
from route_suggester import ShipmentRequest, suggest_routes, RouteRecommendation
from services.ollama_service import generate
from services.weather_service import get_most_severe_upcoming, get_weather_forecast, get_weather_forecast_risk
from services.news_service import get_geopolitical_headlines
from services.csv_service import (
    get_aggregate_stats,
    get_risk_context_for_route,
    get_delay_probability,
    get_unprecedented_event_probability,
    load_shipments,
)

app = FastAPI(title="Supply Chain Portal API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Schemas ─────────────────────────────────────────────────────────────────

class ImportExportRequest(BaseModel):
    region: Optional[str] = "Taiwan"


class PlanShipmentRequest(BaseModel):
    company: str
    origin_id: str
    destination_id: str
    part_type: str
    priority: str
    notes: str = ""
    concerns: str = ""


class TrackShipmentRequest(BaseModel):
    shipment_id: Optional[str] = None
    origin_id: str
    destination_id: str
    route_id: Optional[str] = None
    date_shipped: Optional[str] = None


# ─── 1. State of semiconductor importing/exporting ───────────────────────────

@app.post("/api/import-export/summary")
async def get_import_export_summary(req: ImportExportRequest):
    """Load weather, news, CSV; use Ollama to generate summary; return cards data."""
    region = req.region or "Taiwan"
    weather = get_most_severe_upcoming(region)
    headlines = get_geopolitical_headlines(5)
    stats = get_aggregate_stats()

    context = (
        f"Weather: {weather.get('event', 'N/A')} in {region} (severity: {weather.get('severity', 'N/A')}). "
        f"News: {'; '.join(headlines[:3])}. "
        f"Shipment stats: {stats.get('total', 0)} total, statuses {stats.get('by_status', {})}, "
        f"avg delay {stats.get('avg_delay_hours', 0):.1f}h. Risk events: {stats.get('risk_events', [])[:5]}."
    )
    prompt = (
        "In 3–4 short paragraphs, summarize the current state of semiconductor "
        "importing and exporting to/from the US, given this context. Be concise and actionable."
    )
    summary = generate(prompt, system=f"Context: {context}")

    return {
        "summary": summary,
        "weather_event": weather,
        "headlines": headlines,
        "stats": stats,
    }


# ─── 2. Plan shipment ────────────────────────────────────────────────────────

@app.post("/api/plan-shipment")
async def plan_shipment(req: PlanShipmentRequest):
    """Use route suggester + Ollama to generate shipment plan and risk factors."""
    risk_context = get_risk_context_for_route(
        next((n.country for n in MANUFACTURER_NODES if n.id == req.origin_id), ""),
        next((d.name for d in US_DESTINATIONS if d.id == req.destination_id), ""),
    )
    request = ShipmentRequest(
        company=req.company,
        origin_id=req.origin_id,
        destination_id=req.destination_id,
        part_type=req.part_type,
        priority=req.priority,
        risk_context=risk_context,
    )
    recs = suggest_routes(request, top_n=3)

    notes_stripped = (req.notes or "").strip()
    concerns_stripped = (req.concerns or "").strip()

    if not notes_stripped and not concerns_stripped:
        # No notes or concerns: pick the fastest route
        fastest = min(recs, key=lambda r: r.adjusted_days_min) if recs else None
        if fastest:
            plan = (
                f"Recommended: {fastest.lane.mode} ({fastest.lane.route_type}) – "
                f"{fastest.adjusted_days_min}–{fastest.adjusted_days_max} days. "
                f"This is the fastest option. {fastest.rationale}"
            )
        else:
            plan = "No eligible routes found for this shipment."
    else:
        routes_text = "\n".join(
            f"#{r.rank}: {r.lane.mode} {r.lane.route_type}, {r.adjusted_days_min}-{r.adjusted_days_max} days, "
            f"score {r.score}, {r.estimated_cost_tier}. {r.rationale}"
            for r in recs
        )
        prompt = (
            f"User notes: {req.notes}. Concerns: {req.concerns}. "
            f"Route options:\n{routes_text}\n\n"
            "Generate a concise shipment plan (2–3 paragraphs) recommending the best option "
            "and addressing the user's concerns. List key risk factors in bullet points."
        )
        plan = generate(prompt)

    risk_factors = []
    for r in recs:
        risk_factors.extend(r.risk_warnings)
    risk_factors = list(dict.fromkeys(risk_factors))  # dedupe

    return {
        "plan": plan,
        "risk_factors": risk_factors,
        "recommendations": [
            {
                "rank": r.rank,
                "mode": r.lane.mode,
                "route_type": r.lane.route_type,
                "days_min": r.adjusted_days_min,
                "days_max": r.adjusted_days_max,
                "score": r.score,
                "cost_tier": r.estimated_cost_tier,
                "rationale": r.rationale,
            }
            for r in recs
        ],
    }


# ─── 3. Track shipment ───────────────────────────────────────────────────────

def _country_to_weather_region(country: str) -> str:
    """Map origin country to weather API region."""
    m = {
        "Taiwan": "Taiwan",
        "Malaysia": "Malaysia",
        "Singapore": "Singapore",
        "South Korea": "South Korea",
        "China": "Taiwan",  # East Asia fallback
        "Vietnam": "Malaysia",  # SE Asia fallback
    }
    return m.get(country, "Taiwan")


def _compute_risk_factor(
    origin_country: str,
    dest_name: str,
    transport_mode: str,
    chokepoint_exposure: bool,
    delay_factors: list,
) -> dict:
    """
    Compute risk factor 1–10 from:
    - Delay probability (from CSV)
    - Weather forecast risk
    - Geopolitics (from CSV)
    - Unprecedented event probability
    Returns {"risk_factor": int, "breakdown": dict} for transparency.
    """
    risk_context = get_risk_context_for_route(origin_country, dest_name)
    delay_prob = get_delay_probability(origin_country, dest_name, transport_mode)
    weather_risk = get_weather_forecast_risk(_country_to_weather_region(origin_country))
    geopolitics = risk_context.get("geopolitical_risk", 0) or 0
    unprecedented = get_unprecedented_event_probability(origin_country, delay_factors)

    # Weighted combination (0–1)
    composite = (
        0.30 * delay_prob
        + 0.30 * weather_risk
        + 0.30 * geopolitics
        + 0.10 * unprecedented
    )
    composite = min(1.0, composite)
    base = round(composite * 10)
    if chokepoint_exposure:
        base = min(10, base + 1)
    risk_factor = max(1, min(10, base))

    return {
        "risk_factor": risk_factor,
        "breakdown": {
            "delay_probability": round(delay_prob, 2),
            "weather_forecast_risk": round(weather_risk, 2),
            "geopolitics_risk": round(geopolitics, 2),
            "unprecedented_event_risk": round(unprecedented, 2),
        },
    }


@app.post("/api/track-shipment")
async def track_shipment(req: TrackShipmentRequest):
    """Estimate arrival, show plan and delay factors from routes + CSV."""
    from datetime import datetime, timedelta

    lanes = [l for l in SHIPPING_LANES if l.origin_id == req.origin_id and l.destination_id == req.destination_id]
    if not lanes and req.route_id:
        lane = get_lane(req.route_id)
        lanes = [lane] if lane else []
    if not lanes:
        lanes = SHIPPING_LANES[:2]  # fallback

    lane = lanes[0]
    est_min, est_max = lane.transit_days_min, lane.transit_days_max

    shipments = load_shipments()
    delay_factors = []
    for s in shipments[:50]:
        we = s.get("weather_event", "")
        ge = s.get("geopolitical_event", "")
        if we and we != "None":
            delay_factors.append(we)
        if ge and ge != "None":
            delay_factors.append(ge)
    delay_factors = list(dict.fromkeys(delay_factors))[:5]

    origin_country = next((n.country for n in MANUFACTURER_NODES if n.id == req.origin_id), "")
    dest_name = next((d.name for d in US_DESTINATIONS if d.id == req.destination_id), "")
    risk_result = _compute_risk_factor(
        origin_country,
        dest_name,
        lane.mode,
        lane.chokepoint_exposure,
        delay_factors,
    )
    risk_factor = risk_result["risk_factor"]
    risk_breakdown = risk_result["breakdown"]

    days_ago_shipped = None
    estimated_arrival_date = None
    if req.date_shipped:
        try:
            shipped = datetime.strptime(req.date_shipped[:10], "%Y-%m-%d")
            now = datetime.utcnow()
            days_ago_shipped = max(0, (now - shipped).days)
            avg_transit = (est_min + est_max) / 2
            arrival = shipped + timedelta(days=avg_transit)
            estimated_arrival_date = arrival.strftime("%Y-%m-%d")
        except (ValueError, TypeError, IndexError):
            pass

    prompt = (
        f"Route: {lane.origin_id} → {lane.destination_id}, {lane.mode} {lane.route_type}. "
        f"Typical transit: {est_min}-{est_max} days. "
        f"Possible delay factors: {delay_factors}. "
        "Write a brief 2-paragraph tracking summary with estimated arrival and delay risks."
    )
    tracking_summary = generate(prompt)

    return {
        "plan": tracking_summary,
        "estimated_arrival_days_min": est_min,
        "estimated_arrival_days_max": est_max,
        "estimated_arrival_date": estimated_arrival_date,
        "days_ago_shipped": days_ago_shipped,
        "risk_factor": risk_factor,
        "risk_breakdown": risk_breakdown,
        "delay_factors": delay_factors,
        "lane": {
            "lane_id": lane.lane_id,
            "mode": lane.mode,
            "route_type": lane.route_type,
        },
    }


# ─── Reference data for frontend dropdowns ───────────────────────────────────

@app.get("/api/nodes")
async def get_nodes():
    return [{"id": n.id, "name": n.name, "company": n.company, "city": n.city, "country": n.country} for n in MANUFACTURER_NODES]


@app.get("/api/destinations")
async def get_destinations():
    return [{"id": d.id, "name": d.name, "company": d.company, "city": d.city, "state": d.state} for d in US_DESTINATIONS]


@app.get("/api/lanes")
async def get_lanes():
    return [
        {
            "lane_id": l.lane_id,
            "company": l.company,
            "origin_id": l.origin_id,
            "destination_id": l.destination_id,
            "mode": l.mode,
            "transit_days_min": l.transit_days_min,
            "transit_days_max": l.transit_days_max,
        }
        for l in SHIPPING_LANES
    ]
