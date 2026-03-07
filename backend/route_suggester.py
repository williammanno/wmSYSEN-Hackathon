"""
Route suggester for semiconductor shipments.
Scores eligible lanes and returns ranked recommendations.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict
from routes import (
    SHIPPING_LANES, MANUFACTURER_NODES, US_DESTINATIONS,
    ShippingLane, ManufacturerNode, USDestinationHub,
    get_lanes_by_company, get_nodes_by_company, get_destinations_by_company,
)


@dataclass
class ShipmentRequest:
    company: str
    origin_id: str
    destination_id: str
    part_type: str
    priority: str  # critical | high | standard
    risk_context: Dict[str, float] = None

    def __post_init__(self):
        if self.risk_context is None:
            self.risk_context = {}


@dataclass
class RouteRecommendation:
    rank: int
    lane: ShippingLane
    score: float
    estimated_days_min: float
    estimated_days_max: float
    adjusted_days_min: float
    adjusted_days_max: float
    estimated_cost_tier: str
    risk_flag: bool
    risk_warnings: List[str]
    rationale: str


WEIGHTS = {"reliability": 0.30, "speed": 0.25, "priority_fit": 0.20, "part_fit": 0.15, "risk_penalty": 0.10}
MAX_TRANSIT_DAYS = 45.0

PRIORITY_PREFERENCES = {
    "critical": {"modes": ["air", "truck"], "route_types": ["express"], "avoid_sea": True},
    "high": {"modes": ["air", "sea_air_hybrid", "truck"], "route_types": ["express", "standard"], "avoid_sea": False},
    "standard": {"modes": ["air", "sea", "sea_air_hybrid", "truck"], "route_types": ["standard", "economy"], "avoid_sea": False},
}

PART_HARD_RULES = {
    "wafer": {"avoid_modes": ["sea"], "note": "Wafers must ship air or truck."},
    "photomask": {"avoid_modes": ["sea"], "note": "Photomasks require air."},
    "packaged IC": {"avoid_modes": [], "note": None},
    "spare part": {"avoid_modes": [], "note": None},
}


def _composite_risk(risk_context: Dict[str, float]) -> float:
    w = risk_context.get("weather_risk", 0.0)
    g = risk_context.get("geopolitical_risk", 0.0)
    c = risk_context.get("port_congestion", 0.0)
    lr = risk_context.get("labor_risk", 0.0)
    return min(1.0, round(0.35 * w + 0.30 * g + 0.20 * c + 0.15 * lr, 3))


def _risk_delay_days(lane: ShippingLane, risk_context: Dict[str, float]) -> float:
    extra = 0.0
    composite = _composite_risk(risk_context)
    if composite >= 0.60:
        extra += 2.5
    elif composite >= 0.35:
        extra += 1.0
    if risk_context.get("taiwan_strait_alert", False):
        origin_node = next((n for n in MANUFACTURER_NODES if n.id == lane.origin_id), None)
        if origin_node and origin_node.country == "Taiwan":
            extra += 3.0
    return extra


def _build_warnings(lane: ShippingLane, risk_context: Dict[str, float]) -> List[str]:
    warnings = []
    composite = _composite_risk(risk_context)
    if composite >= 0.60:
        warnings.append(f"High composite risk ({composite:.2f}) – expect delays.")
    if risk_context.get("taiwan_strait_alert", False):
        origin_node = next((n for n in MANUFACTURER_NODES if n.id == lane.origin_id), None)
        if origin_node and origin_node.country == "Taiwan":
            warnings.append("Taiwan Strait alert – book early.")
    if lane.chokepoint_exposure and lane.mode == "sea":
        warnings.append("Route passes through South China Sea chokepoint.")
    return warnings


def _score_lane(lane: ShippingLane, request: ShipmentRequest) -> Optional[RouteRecommendation]:
    pref = PRIORITY_PREFERENCES.get(request.priority, PRIORITY_PREFERENCES["standard"])
    hard_rule = PART_HARD_RULES.get(request.part_type, {"avoid_modes": [], "note": None})

    if lane.mode in hard_rule["avoid_modes"]:
        return None
    if pref.get("avoid_sea") and lane.mode == "sea":
        return None
    if lane.origin_id != request.origin_id or lane.destination_id != request.destination_id:
        return None

    reliability_score = lane.reliability_pct / 100.0
    speed_score = max(0.0, 1.0 - (lane.transit_days_max / MAX_TRANSIT_DAYS))
    mode_match = 1.0 if lane.mode in pref["modes"] else 0.4
    type_match = 1.0 if lane.route_type in pref["route_types"] else 0.5
    priority_fit_score = (mode_match + type_match) / 2.0
    part_fit_score = 1.0 if request.part_type in lane.best_for else 0.6

    composite = _composite_risk(request.risk_context)
    chokepoint_pen = 0.15 if lane.chokepoint_exposure else 0.0
    taiwan_pen = 0.10 if (
        request.risk_context.get("taiwan_strait_alert", False)
        and any(n.id == lane.origin_id and n.country == "Taiwan" for n in MANUFACTURER_NODES)
    ) else 0.0
    risk_penalty_score = max(0.0, 1.0 - composite - chokepoint_pen - taiwan_pen)

    score = round((
        WEIGHTS["reliability"] * reliability_score +
        WEIGHTS["speed"] * speed_score +
        WEIGHTS["priority_fit"] * priority_fit_score +
        WEIGHTS["part_fit"] * part_fit_score +
        WEIGHTS["risk_penalty"] * risk_penalty_score
    ) * 100, 1)

    delay = _risk_delay_days(lane, request.risk_context)
    adj_min = round(lane.transit_days_min + delay, 1)
    adj_max = round(lane.transit_days_max + delay, 1)

    avg_cost = (lane.cost_usd_per_kg_min + lane.cost_usd_per_kg_max) / 2
    cost_tier = "premium" if avg_cost >= 12.0 else ("standard" if avg_cost >= 4.0 else "economy")

    warnings = _build_warnings(lane, request.risk_context)
    rationale = (
        f"{lane.mode} ({lane.route_type}) via {' → '.join(lane.transshipment_hubs) or 'direct'}. "
        f"Preferred: {', '.join(lane.preferred_carriers[:2])}. "
        f"Baseline {lane.transit_days_min}–{lane.transit_days_max} days"
        + (f", adjusted to {adj_min}–{adj_max} days." if delay > 0 else ".")
    )

    return RouteRecommendation(
        rank=0, lane=lane, score=score,
        estimated_days_min=lane.transit_days_min, estimated_days_max=lane.transit_days_max,
        adjusted_days_min=adj_min, adjusted_days_max=adj_max,
        estimated_cost_tier=cost_tier, risk_flag=bool(warnings), risk_warnings=warnings,
        rationale=rationale,
    )


def suggest_routes(request: ShipmentRequest, top_n: int = 3) -> List[RouteRecommendation]:
    candidates = []
    company_lanes = get_lanes_by_company(request.company)
    for lane in company_lanes:
        rec = _score_lane(lane, request)
        if rec:
            candidates.append(rec)
    candidates.sort(key=lambda r: r.score, reverse=True)
    for i, rec in enumerate(candidates[:top_n]):
        rec.rank = i + 1
    return candidates[:top_n]
