"""Load and analyze semiconductor shipments from Supabase for decision making."""

import os
from typing import Any, Dict, List

_supabase_client = None


def _get_client():
    """Lazy-init Supabase client. Returns None if not configured."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    url = (os.getenv("SUPABASE_URL") or "").strip()
    key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY") or "").strip()
    if not url or not key:
        return None
    try:
        from supabase import create_client
        _supabase_client = create_client(url, key)
    except Exception:
        pass
    return _supabase_client


def _row_to_dict(row: Any) -> Dict[str, Any]:
    """Convert Supabase row to plain dict for compatibility with CSV-based logic."""
    d = dict(row) if isinstance(row, dict) else (getattr(row, "_asdict", lambda: {})() or dict(row))
    out = {}
    for k, v in d.items():
        if v is None:
            out[k] = None
        elif hasattr(v, "isoformat"):  # datetime
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out


def load_shipments() -> List[Dict[str, Any]]:
    """Load shipments from Supabase into list of dicts."""
    client = _get_client()
    if not client:
        return []
    try:
        resp = client.table("shipments").select("*").execute()
        return [_row_to_dict(r) for r in (resp.data or [])]
    except Exception:
        return []


def get_aggregate_stats() -> Dict[str, Any]:
    """Compute aggregate stats from Supabase for decision context."""
    rows = load_shipments()
    if not rows:
        return {"total": 0, "by_status": {}, "avg_delay_hours": 0, "risk_events": []}

    by_status = {}
    delays = []
    risk_events = set()
    for r in rows:
        s = str(r.get("current_status") or "unknown")
        by_status[s] = by_status.get(s, 0) + 1
        dh = r.get("delay_hours")
        try:
            delays.append(float(dh) if dh is not None else 0)
        except (ValueError, TypeError):
            pass
        we = r.get("weather_event") or ""
        ge = r.get("geopolitical_event") or ""
        if we and str(we) != "None":
            risk_events.add(str(we))
        if ge and str(ge) != "None":
            risk_events.add(str(ge))

    return {
        "total": len(rows),
        "by_status": by_status,
        "avg_delay_hours": sum(delays) / len(delays) if delays else 0,
        "risk_events": list(risk_events)[:10],
    }


def get_risk_context_for_route(origin_country: str, destination: str) -> Dict[str, float]:
    """Derive risk scores from Supabase for a given route."""
    rows = load_shipments()
    if not rows:
        return {"weather_risk": 0, "geopolitical_risk": 0, "port_congestion": 0, "labor_risk": 0}

    wr, gr, pc, lr = [], [], [], []
    dest_lower = (destination or "").lower()
    for r in rows:
        oc = r.get("origin_country") or ""
        dc = (r.get("destination_city") or "").lower()
        if oc != origin_country and (not dest_lower or dest_lower not in dc):
            continue
        try:
            wr.append(float(r.get("weather_risk_score") or 0))
            gr.append(float(r.get("geopolitical_risk_score") or 0))
            pc.append(float(r.get("port_congestion_score") or 0))
            lr.append(float(r.get("labor_risk_score") or 0))
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
    """Probability of package being delayed (0–1) from Supabase data."""
    rows = load_shipments()
    if not rows:
        return 0.0

    matching = []
    dest_lower = (destination or "").lower()
    mode_lower = (transport_mode or "").lower()
    for r in rows:
        if (r.get("origin_country") or "") != origin_country:
            continue
        dc = ((r.get("destination_city") or "").lower())
        if destination and dest_lower not in dc:
            continue
        tm = (r.get("transport_mode") or "").lower()
        if transport_mode and tm != mode_lower:
            continue
        matching.append(r)

    if not matching:
        matching = [r for r in rows if (r.get("origin_country") or "") == origin_country]
    if not matching:
        matching = rows

    delayed = 0
    for r in matching:
        status = (str(r.get("current_status") or "")).lower()
        dh = r.get("delay_hours")
        mw = r.get("missed_delivery_window")
        try:
            dhi = int(dh) if dh is not None else 0
            mwi = int(mw) if mw is not None else 0
            if status == "delayed" or dhi > 0 or mwi > 0:
                delayed += 1
        except (ValueError, TypeError):
            pass
    return delayed / len(matching) if matching else 0.0


def load_shipment_events(shipment_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Load events from shipment_event_log. Optionally filter by shipment_id."""
    client = _get_client()
    if not client:
        return []
    try:
        q = client.table("shipment_event_log").select("*")
        if shipment_id:
            q = q.eq("shipment_id", shipment_id)
        resp = q.order("event_timestamp", desc=True).limit(limit).execute()
        return [_row_to_dict(r) for r in (resp.data or [])]
    except Exception:
        return []


def get_event_log_stats() -> Dict[str, Any]:
    """Aggregate stats from shipment_event_log for dashboard context."""
    client = _get_client()
    if not client:
        return {"total_events": 0, "exception_count": 0, "by_event_type": {}}
    try:
        resp = client.table("shipment_event_log").select("event_type, exception_flag").execute()
        rows = resp.data or []
        by_type = {}
        exceptions = 0
        for r in rows:
            et = str(r.get("event_type") or "unknown")
            by_type[et] = by_type.get(et, 0) + 1
            if r.get("exception_flag"):
                exceptions += 1
        return {
            "total_events": len(rows),
            "exception_count": exceptions,
            "by_event_type": by_type,
        }
    except Exception:
        return {"total_events": 0, "exception_count": 0, "by_event_type": {}}


def get_unprecedented_event_probability(origin_country: str, active_events: list) -> float:
    """Probability of an unprecedented / rare disruptive event (0–1)."""
    rows = load_shipments()
    with_event = 0
    for r in rows:
        we = r.get("weather_event") or ""
        ge = r.get("geopolitical_event") or ""
        if (we and str(we) != "None") or (ge and str(ge) != "None"):
            with_event += 1
    base_rate = with_event / len(rows) if rows else 0.1

    high_impact = {
        "panama canal", "taiwan strait", "south china sea", "red sea",
        "hurricane", "typhoon", "earthquake", "export ban", "military",
    }
    bonus = 0.0
    for ev in (active_events or []):
        ev_lower = (str(ev or "")).lower()
        if any(h in ev_lower for h in high_impact):
            bonus += 0.15
    return min(1.0, base_rate * 2 + bonus)
