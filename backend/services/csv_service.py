"""Load and analyze semiconductor shipments CSV for decision making."""

import csv
from pathlib import Path
from typing import List, Dict, Any

CSV_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "semiconductor_shipments_500(1).csv"


def load_shipments() -> List[Dict[str, Any]]:
    """Load CSV into list of dicts."""
    rows = []
    if not CSV_PATH.exists():
        return rows
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def get_aggregate_stats() -> Dict[str, Any]:
    """Compute aggregate stats from CSV for decision context."""
    rows = load_shipments()
    if not rows:
        return {"total": 0, "by_status": {}, "avg_delay": 0, "risk_events": []}

    by_status = {}
    delays = []
    risk_events = set()
    for r in rows:
        s = r.get("current_status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1
        dh = r.get("delay_hours", "0")
        try:
            delays.append(int(dh))
        except (ValueError, TypeError):
            pass
        we = r.get("weather_event", "")
        ge = r.get("geopolitical_event", "")
        if we and we != "None":
            risk_events.add(we)
        if ge and ge != "None":
            risk_events.add(ge)

    return {
        "total": len(rows),
        "by_status": by_status,
        "avg_delay_hours": sum(delays) / len(delays) if delays else 0,
        "risk_events": list(risk_events)[:10],
    }


def get_risk_context_for_route(origin_country: str, destination: str) -> Dict[str, float]:
    """Derive risk scores from CSV for a given route."""
    rows = load_shipments()
    if not rows:
        return {"weather_risk": 0, "geopolitical_risk": 0, "port_congestion": 0, "labor_risk": 0}

    wr, gr, pc, lr = [], [], [], []
    for r in rows:
        if r.get("origin_country") == origin_country or r.get("destination_city", "").lower() in destination.lower():
            try:
                wr.append(float(r.get("weather_risk_score", 0) or 0))
                gr.append(float(r.get("geopolitical_risk_score", 0) or 0))
                pc.append(float(r.get("port_congestion_score", 0) or 0))
                lr.append(float(r.get("labor_risk_score", 0) or 0))
            except (ValueError, TypeError):
                pass
    n = max(len(wr), 1)
    return {
        "weather_risk": sum(wr) / n if wr else 0,
        "geopolitical_risk": sum(gr) / n if gr else 0,
        "port_congestion": sum(pc) / n if pc else 0,
        "labor_risk": sum(lr) / n if lr else 0,
    }


def get_delay_probability(origin_country: str, destination: str, transport_mode: str = "") -> float:
    """
    Probability of package being delayed (0–1) from CSV data.
    Based on historical shipments on similar routes.
    """
    rows = load_shipments()
    if not rows:
        return 0.0

    matching = []
    for r in rows:
        if r.get("origin_country") != origin_country:
            continue
        dest_city = (r.get("destination_city") or "").lower()
        if destination and dest_city not in destination.lower():
            continue
        if transport_mode and (r.get("transport_mode") or "").lower() != transport_mode.lower():
            continue
        matching.append(r)

    if not matching:
        # Fallback: use all shipments for origin country
        matching = [r for r in rows if r.get("origin_country") == origin_country]
    if not matching:
        matching = rows  # Ultimate fallback: global rate

    delayed = 0
    for r in matching:
        status = (r.get("current_status") or "").lower()
        dh = r.get("delay_hours", "0")
        mw = r.get("missed_delivery_window", "0")
        try:
            if status == "delayed" or int(dh or 0) > 0 or int(mw or 0) > 0:
                delayed += 1
        except (ValueError, TypeError):
            pass
    return delayed / len(matching) if matching else 0.0


def get_unprecedented_event_probability(origin_country: str, active_events: list) -> float:
    """
    Probability of an unprecedented / rare disruptive event (0–1).
    Based on: historical rate of unusual events + current high-impact events.
    """
    rows = load_shipments()
    # Base rate: what % of shipments historically had a weather or geo event?
    with_event = 0
    for r in rows:
        we = r.get("weather_event", "") or ""
        ge = r.get("geopolitical_event", "") or ""
        if (we and we != "None") or (ge and ge != "None"):
            with_event += 1
    base_rate = with_event / len(rows) if rows else 0.1

    # High-impact events that are relatively unprecedented
    high_impact = {
        "panama canal", "taiwan strait", "south china sea", "red sea",
        "hurricane", "typhoon", "earthquake", "export ban", "military",
    }
    bonus = 0.0
    for ev in (active_events or []):
        ev_lower = (ev or "").lower()
        if any(h in ev_lower for h in high_impact):
            bonus += 0.15
    return min(1.0, base_rate * 2 + bonus)  # Scale base, add bonus
