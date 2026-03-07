"""Weather data via Open-Meteo (free, no API key)."""

import requests
from typing import Optional

# Major semiconductor hub coordinates
HUB_COORDS = {
    "Taiwan": (25.0330, 121.5654),
    "Singapore": (1.3521, 103.8198),
    "Malaysia": (3.1390, 101.6869),
    "South Korea": (37.5665, 126.9780),
    "USA_CA": (37.7749, -122.4194),
    "USA_TX": (32.7767, -97.7970),
}


def get_weather_forecast(lat: float, lon: float) -> dict:
    """Fetch 7-day forecast from Open-Meteo."""
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum",
                "timezone": "auto",
                "forecast_days": 7,
            },
            timeout=10,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def get_most_severe_upcoming(region: str = "Taiwan") -> dict:
    """Get most severe upcoming weather event for a region."""
    coords = HUB_COORDS.get(region, HUB_COORDS["Taiwan"])
    data = get_weather_forecast(coords[0], coords[1])
    if "error" in data:
        return {"region": region, "event": "Unable to fetch", "severity": "unknown"}

    daily = data.get("daily", {})
    codes = daily.get("weather_code", [])
    precip = daily.get("precipitation_sum", [0] * 7)
    dates = daily.get("time", [])

    # WMO codes: 61-67 rain, 71-77 snow, 95+ thunderstorm
    severe_codes = {61, 62, 63, 64, 65, 66, 67, 71, 73, 75, 77, 95, 96, 99}
    for i, (code, p) in enumerate(zip(codes, precip)):
        c = int(code) if code else 0
        if c in severe_codes or (isinstance(p, (int, float)) and p > 10):
            return {
                "region": region,
                "date": dates[i] if i < len(dates) else "N/A",
                "event": _code_to_event(c),
                "severity": "high" if c >= 95 or (isinstance(p, (int, float)) and p > 20) else "medium",
            }
    return {
        "region": region,
        "date": dates[0] if dates else "N/A",
        "event": "No severe weather expected",
        "severity": "low",
    }


def _code_to_event(code: int) -> str:
    if 61 <= code <= 67:
        return "Heavy rain"
    if 71 <= code <= 77:
        return "Snow"
    if code >= 95:
        return "Thunderstorm"
    return "Precipitation"


def get_weather_forecast_risk(region: str) -> float:
    """
    Risk of bad weather delaying shipment (0–1) based on 7-day forecast.
    Returns severity as numeric: low=0.1, medium=0.5, high=0.9.
    """
    data = get_most_severe_upcoming(region)
    severity = (data.get("severity") or "low").lower()
    if severity == "high":
        return 0.9
    if severity == "medium":
        return 0.5
    return 0.1  # low or unknown
