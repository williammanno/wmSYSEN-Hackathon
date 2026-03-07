"""
Unified shipment data service. Uses Supabase when configured, otherwise falls back to CSV.
Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_ANON_KEY) in .env to use Supabase.
"""

import os

_use_supabase = None


def _backend():
    """Return 'supabase' or 'csv' based on env config."""
    global _use_supabase
    if _use_supabase is not None:
        return _use_supabase
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    _use_supabase = bool(url and key)
    return "supabase" if _use_supabase else "csv"


def load_shipments():
    if _backend() == "supabase":
        from services.supabase_service import load_shipments as _load
        return _load()
    from services.csv_service import load_shipments as _load
    return _load()


def get_aggregate_stats():
    if _backend() == "supabase":
        from services.supabase_service import get_aggregate_stats as _fn
        return _fn()
    from services.csv_service import get_aggregate_stats as _fn
    return _fn()


def get_risk_context_for_route(origin_country: str, destination: str):
    if _backend() == "supabase":
        from services.supabase_service import get_risk_context_for_route as _fn
        return _fn(origin_country, destination)
    from services.csv_service import get_risk_context_for_route as _fn
    return _fn(origin_country, destination)


def get_delay_probability(origin_country: str, destination: str, transport_mode: str = ""):
    if _backend() == "supabase":
        from services.supabase_service import get_delay_probability as _fn
        return _fn(origin_country, destination, transport_mode)
    from services.csv_service import get_delay_probability as _fn
    return _fn(origin_country, destination, transport_mode)


def get_unprecedented_event_probability(origin_country: str, active_events: list):
    if _backend() == "supabase":
        from services.supabase_service import get_unprecedented_event_probability as _fn
        return _fn(origin_country, active_events)
    from services.csv_service import get_unprecedented_event_probability as _fn
    return _fn(origin_country, active_events)
