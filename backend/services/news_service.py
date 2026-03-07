"""Geopolitical news headlines (mock + optional GNews)."""

# Mock headlines when no API key
MOCK_HEADLINES = [
    "Taiwan Strait tensions affect semiconductor supply chain",
    "CHIPS Act compliance audits expand to Arizona suppliers",
    "South China Sea vessel routing disruptions continue",
    "Nvidia H20 export ban expansion under review",
    "Panama Canal drought impacts transpacific shipping",
    "US West Coast dockworker slowdown negotiations",
    "Malaysia customs semiconductor audit underway",
]


def get_geopolitical_headlines(limit: int = 5) -> list:
    """Return top geopolitical news headlines. Uses mock data."""
    return MOCK_HEADLINES[:limit]
