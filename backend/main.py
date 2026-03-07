"""
Supply Chain Portal API – semiconductor import/export, planning, tracking.
Uses OpenAI GPT-4o for LLM, Open-Meteo for weather, routes + Supabase for shipment data and decisions.
"""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from routes import MANUFACTURER_NODES, US_DESTINATIONS, SHIPPING_LANES, get_lane
from route_suggester import ShipmentRequest, suggest_routes, RouteRecommendation
from services.openai_service import generate
from services.weather_service import get_most_severe_upcoming, get_weather_forecast, get_weather_forecast_risk
from services.news_service import get_geopolitical_headlines
from services.shipment_service import (
    get_aggregate_stats,
    get_risk_context_for_route,
    get_delay_probability,
    get_unprecedented_event_probability,
    load_shipments,
    load_shipment_events,
    get_event_log_stats,
)

app = FastAPI(title="Supply Chain Portal API")

default_cors_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
cors_origins_env = os.getenv("CORS_ORIGINS", "")
cors_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()] or default_cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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
    """Load weather, news, Supabase shipment data; use GPT-4o to generate summary; return cards data."""
    region = req.region or "Taiwan"
    weather = get_most_severe_upcoming(region)
    headlines = get_geopolitical_headlines(5)
    stats = get_aggregate_stats()
    event_stats = get_event_log_stats()
    risk_scores = _build_plan_risk_scores(get_risk_context_for_route(region, ""))

    context = (
        f"Weather: {weather.get('event', 'N/A')} in {region} (severity: {weather.get('severity', 'N/A')}). "
        f"News: {'; '.join(headlines[:3])}. "
        f"Shipment stats: {stats.get('total', 0)} total, statuses {stats.get('by_status', {})}, "
        f"avg delay {stats.get('avg_delay_hours', 0):.1f}h. Risk events: {stats.get('risk_events', [])[:5]}. "
        f"Event log: {event_stats.get('total_events', 0)} events, {event_stats.get('exception_count', 0)} exceptions."
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
        "event_log_stats": event_stats,
        "risk_scores": risk_scores,
    }


# ─── 2. Plan shipment ────────────────────────────────────────────────────────


def _build_fallback_plan(
    req: PlanShipmentRequest,
    origin_name: str,
    origin_country: str,
    dest_name: str,
    best: RouteRecommendation,
    recs: List[RouteRecommendation],
    risk_factors: List[str],
) -> str:
    """Build a deterministic shipment plan when LLM is unavailable."""
    lines = [
        f"Recommended route: {best.lane.mode} ({best.lane.route_type})",
        "",
        f"For {req.company} shipping {req.part_type} from {origin_name} ({origin_country}) to {dest_name}, "
        f"we recommend Option #{best.rank}: {best.lane.mode} {best.lane.route_type}. "
        f"This route has the highest score ({best.score}) and offers {best.adjusted_days_min}–{best.adjusted_days_max} day transit "
        f"at {best.estimated_cost_tier} cost.",
        "",
        f"Why this route: {best.rationale}",
        "",
        f"Given your {req.priority} priority and {req.part_type} shipment, this option balances "
        "reliability, transit time, and cost.",
    ]
    if (req.notes or "").strip() or (req.concerns or "").strip():
        lines.append("")
        if req.notes:
            lines.append(f"Your notes: {req.notes}")
        if req.concerns:
            lines.append(f"Your concerns: {req.concerns}")
    lines.append("")
    lines.append("Risk factors to monitor:")
    for rf in risk_factors:
        lines.append(f"• {rf}")
    return "\n".join(lines)


def _derive_risk_factors(
    risk_context: Dict[str, Any],
    origin_country: str,
    dest_name: str,
    recs: List[RouteRecommendation],
) -> List[str]:
    """Derive risk factors when route suggester returns none."""
    factors = []
    wr = risk_context.get("weather_risk", 0) or 0
    gr = risk_context.get("geopolitical_risk", 0) or 0
    pc = risk_context.get("port_congestion", 0) or 0
    lr = risk_context.get("labor_risk", 0) or 0

    if wr >= 0.2:
        factors.append("Weather-related delays possible in the region.")
    if gr >= 0.2:
        factors.append("Geopolitical uncertainty may affect transit.")
    if pc >= 0.2:
        factors.append("Port congestion could extend lead times.")
    if lr >= 0.2:
        factors.append("Labor availability may impact carrier capacity.")

    for r in recs:
        if r.lane.chokepoint_exposure and r.lane.mode == "sea":
            factors.append("Route passes through South China Sea chokepoint.")
            break

    factors.append("Transit time variability depending on carrier and conditions.")
    factors.append("Carrier capacity may be limited during peak periods.")

    return list(dict.fromkeys(factors))


def _build_plan_risk_scores(risk_context: Dict[str, Any]) -> Dict[str, float]:
    """Normalize plan risk scores and add a composite score (0-1)."""
    weather = float(risk_context.get("weather_risk", 0) or 0)
    geopolitical = float(risk_context.get("geopolitical_risk", 0) or 0)
    port_congestion = float(risk_context.get("port_congestion", 0) or 0)
    labor = float(risk_context.get("labor_risk", 0) or 0)
    composite = min(1.0, round(0.35 * weather + 0.30 * geopolitical + 0.20 * port_congestion + 0.15 * labor, 3))

    return {
        "weather_risk": weather,
        "geopolitical_risk": geopolitical,
        "port_congestion": port_congestion,
        "labor_risk": labor,
        "composite_risk": composite,
    }


@app.post("/api/plan-shipment")
async def plan_shipment(req: PlanShipmentRequest):
    """Use route suggester + GPT-4o to generate shipment plan with best route and rationale."""
    origin_node = next((n for n in MANUFACTURER_NODES if n.id == req.origin_id), None)
    dest_hub = next((d for d in US_DESTINATIONS if d.id == req.destination_id), None)
    origin_country = origin_node.country if origin_node else ""
    origin_name = origin_node.name if origin_node else req.origin_id
    dest_name = dest_hub.name if dest_hub else req.destination_id

    risk_context = get_risk_context_for_route(origin_country, dest_name, req.part_type)
    request = ShipmentRequest(
        company=req.company,
        origin_id=req.origin_id,
        destination_id=req.destination_id,
        part_type=req.part_type,
        priority=req.priority,
        risk_context=risk_context,
    )
    recs = suggest_routes(request, top_n=3)

    # Build risk factors for LLM context (before generating plan)
    risk_factors = []
    for r in recs:
        risk_factors.extend(r.risk_warnings)
    risk_factors = list(dict.fromkeys(risk_factors))
    if not risk_factors:
        risk_factors = _derive_risk_factors(risk_context, origin_country, dest_name, recs)

    # Generate plan in the same lightweight style as track-shipment for reliability.
    if not recs:
        plan = "No eligible routes found for this shipment."
    else:
        best = recs[0]
        route_lines = "; ".join(
            f"#{r.rank} {r.lane.mode} {r.lane.route_type} ({r.adjusted_days_min}-{r.adjusted_days_max} days, score {r.score}, {r.estimated_cost_tier})"
            for r in recs
        )
        prompt = (
            f"Shipment: {req.company} shipping {req.part_type} from {origin_name} ({origin_country}) to {dest_name}. "
            f"Priority: {req.priority}. "
            f"Recommended route: #{best.rank} {best.lane.mode} {best.lane.route_type}, "
            f"{best.adjusted_days_min}-{best.adjusted_days_max} days, {best.estimated_cost_tier}. "
            f"Route options: {route_lines}. "
            f"Possible risk factors: {risk_factors}. "
            f"User notes: {req.notes or '(none)'}. Concerns: {req.concerns or '(none)'}. "
            "Write a brief 2-paragraph shipment plan that recommends the best route, explains why, "
            "and mentions key risks to monitor."
        )
        plan = generate(prompt)

        # Fallback: if LLM failed (API error or empty), build deterministic plan
        if not plan or plan.strip().startswith("["):
            plan = _build_fallback_plan(req, origin_name, origin_country, dest_name, best, recs, risk_factors)

    return {
        "plan": plan,
        "risk_factors": risk_factors,
        "risk_scores": _build_plan_risk_scores(risk_context),
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
    - Delay probability (from Supabase shipments)
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
    """Estimate arrival, show plan and delay factors from routes + Supabase shipment data."""
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

    # Include event log when shipment_id provided (from shipment_event_log)
    events = []
    if req.shipment_id:
        events = load_shipment_events(shipment_id=req.shipment_id, limit=20)

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
        "events": events,
        "lane": {
            "lane_id": lane.lane_id,
            "mode": lane.mode,
            "route_type": lane.route_type,
        },
    }


# ─── Debug (verify env loading) ───────────────────────────────────────────────

@app.get("/api/debug/env")
async def debug_env():
    """Check if OPENAI_API_KEY is loaded (does not expose the key)."""
    key = os.getenv("OPENAI_API_KEY", "")
    stripped = key.strip() if key else ""
    return {
        "openai_configured": bool(stripped),
        "key_length": len(stripped),
    }


@app.get("/api/debug/data")
async def debug_data():
    """Check if Supabase returns data from shipments and shipment_event_log datasets."""
    from services.shipment_service import load_shipments, get_event_log_stats
    rows = load_shipments()
    event_stats = get_event_log_stats()
    return {
        "backend": "supabase",
        "shipments_count": len(rows),
        "shipment_event_log_count": event_stats.get("total_events", 0),
        "event_exceptions": event_stats.get("exception_count", 0),
        "supabase_configured": bool(os.getenv("SUPABASE_URL") and (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY"))),
    }


@app.get("/api/shipments/{shipment_id}/events")
async def get_shipment_events(shipment_id: str, limit: int = 50):
    """Get event log for a specific shipment (from shipment_event_log)."""
    events = load_shipment_events(shipment_id=shipment_id, limit=limit)
    return {"shipment_id": shipment_id, "events": events}


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


# ─── Frontend static serving (production) ────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_BUILD_DIR = Path(os.getenv("FRONTEND_BUILD_DIR", BASE_DIR / "static")).resolve()
FRONTEND_INDEX = FRONTEND_BUILD_DIR / "index.html"

if FRONTEND_BUILD_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_BUILD_DIR)), name="frontend-static")


@app.get("/")
async def serve_frontend_root():
    """Serve built frontend homepage when available."""
    if FRONTEND_INDEX.exists():
        return FileResponse(str(FRONTEND_INDEX))
    return {"message": "Supply Chain Portal API is running."}


@app.get("/{full_path:path}")
async def serve_frontend_routes(full_path: str):
    """Serve SPA routes/files in production while preserving API routes."""
    if full_path.startswith("api"):
        raise HTTPException(status_code=404, detail="Not Found")

    requested = (FRONTEND_BUILD_DIR / full_path).resolve()
    if FRONTEND_BUILD_DIR.exists() and str(requested).startswith(str(FRONTEND_BUILD_DIR)) and requested.is_file():
        return FileResponse(str(requested))

    if FRONTEND_INDEX.exists():
        return FileResponse(str(FRONTEND_INDEX))

    raise HTTPException(status_code=404, detail="Not Found")
