"""
Backend routes and data models for semiconductor supply chain logistics.
Provides manufacturer nodes, US destination hubs, and shipping lane definitions
for shipment planning and tracking.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ManufacturerNode:
    """Represents a semiconductor manufacturing origin node."""

    id: str
    name: str
    company: str
    city: str
    country: str
    node_type: str = "fab"
    nearest_airport: str = ""
    nearest_seaport: str = ""
    typical_parts: List[str] = field(default_factory=list)
    available_modes: List[str] = field(default_factory=list)


@dataclass
class USDestinationHub:
    """Represents a US destination hub for semiconductor imports."""

    id: str
    name: str
    company: str
    city: str
    state: str
    hub_type: str = "warehouse"
    port_of_entry_air: str = ""
    port_of_entry_sea: str = ""
    rail_served: bool = False


@dataclass
class ShippingLane:
    """Represents a shipping lane between origin and destination."""

    lane_id: str
    company: str
    origin_id: str
    destination_id: str
    mode: str
    route_type: str = "standard"
    transit_days_min: float = 0
    transit_days_max: float = 0
    transit_notes: str = ""
    preferred_carriers: List[str] = field(default_factory=list)
    transshipment_hubs: List[str] = field(default_factory=list)
    chokepoint_exposure: bool = False
    cost_usd_per_kg_min: float = 0
    cost_usd_per_kg_max: float = 0
    best_for: List[str] = field(default_factory=list)
    reliability_pct: int = 90


MANUFACTURER_NODES: List[ManufacturerNode] = [
    ManufacturerNode(
        id="TSMC-HS", name="TSMC Hsinchu Science Park", company="Nvidia",
        city="Hsinchu", country="Taiwan", node_type="fab",
        nearest_airport="TPE", nearest_seaport="Port of Keelung",
        typical_parts=["wafer", "photomask"], available_modes=["air", "sea"],
    ),
    ManufacturerNode(
        id="TSMC-TN", name="TSMC Tainan GigaFab", company="Nvidia",
        city="Tainan", country="Taiwan", node_type="fab",
        nearest_airport="TPE", nearest_seaport="Port of Kaohsiung",
        typical_parts=["wafer", "photomask"], available_modes=["air", "sea"],
    ),
    ManufacturerNode(
        id="Intel-PG", name="Intel Penang Assembly & Test", company="Intel",
        city="Penang", country="Malaysia", node_type="OSAT",
        nearest_airport="PEN", nearest_seaport="Penang Port",
        typical_parts=["packaged IC", "spare part"], available_modes=["air", "sea"],
    ),
    ManufacturerNode(
        id="Broadcom-SG", name="Broadcom Singapore Hub", company="Broadcom",
        city="Singapore", country="Singapore", node_type="warehouse",
        nearest_airport="SIN", nearest_seaport="Port of Singapore",
        typical_parts=["packaged IC", "spare part"], available_modes=["air", "sea"],
    ),
    ManufacturerNode(
        id="Samsung-KR", name="Samsung Semiconductor Korea", company="Nvidia",
        city="Pyeongtaek", country="South Korea", node_type="fab",
        nearest_airport="ICN", nearest_seaport="Port of Busan",
        typical_parts=["wafer"], available_modes=["air", "sea"],
    ),
]

US_DESTINATIONS: List[USDestinationHub] = [
    USDestinationHub(id="LAX-LGB", name="LA/Long Beach", company="Nvidia",
        city="Los Angeles", state="CA", hub_type="warehouse",
        port_of_entry_air="LAX", port_of_entry_sea="Long Beach", rail_served=True),
    USDestinationHub(id="SFO", name="San Francisco Bay Area", company="Nvidia",
        city="San Francisco", state="CA", hub_type="warehouse",
        port_of_entry_air="SFO", port_of_entry_sea="Oakland", rail_served=False),
    USDestinationHub(id="PHX", name="Phoenix Semiconductor Hub", company="Intel",
        city="Phoenix", state="AZ", hub_type="fab",
        port_of_entry_air="PHX", port_of_entry_sea="N/A", rail_served=True),
    USDestinationHub(id="DFW", name="Dallas/Fort Worth", company="Nvidia",
        city="Dallas", state="TX", hub_type="assembly",
        port_of_entry_air="DFW", port_of_entry_sea="N/A", rail_served=True),
    USDestinationHub(id="MEM", name="Memphis FedEx Hub", company="Broadcom",
        city="Memphis", state="TN", hub_type="warehouse",
        port_of_entry_air="MEM", port_of_entry_sea="N/A", rail_served=True),
]

SHIPPING_LANES: List[ShippingLane] = [
    ShippingLane(lane_id="TPE-LAX-air", company="Nvidia", origin_id="TSMC-HS",
        destination_id="LAX-LGB", mode="air", route_type="standard",
        transit_days_min=5, transit_days_max=10, transit_notes="TPE to LAX direct.",
        preferred_carriers=["EVA Air Cargo", "China Airlines"], transshipment_hubs=["TPE", "LAX"],
        chokepoint_exposure=False, cost_usd_per_kg_min=4.5, cost_usd_per_kg_max=7,
        best_for=["wafer", "packaged IC"], reliability_pct=90),
    ShippingLane(lane_id="TPE-LAX-ocean", company="Nvidia", origin_id="TSMC-HS",
        destination_id="LAX-LGB", mode="sea", route_type="economy",
        transit_days_min=18, transit_days_max=25, transit_notes="Kaohsiung to Long Beach.",
        preferred_carriers=["Evergreen", "COSCO"], transshipment_hubs=["Long Beach"],
        chokepoint_exposure=True, cost_usd_per_kg_min=0.8, cost_usd_per_kg_max=2.5,
        best_for=["spare part"], reliability_pct=75),
    ShippingLane(lane_id="SIN-SFO-air", company="Broadcom", origin_id="Broadcom-SG",
        destination_id="SFO", mode="air", route_type="standard",
        transit_days_min=5, transit_days_max=10, transit_notes="SIN to SFO.",
        preferred_carriers=["DHL", "FedEx"], transshipment_hubs=["SIN", "SFO"],
        chokepoint_exposure=False, cost_usd_per_kg_min=4.5, cost_usd_per_kg_max=7,
        best_for=["packaged IC", "spare part"], reliability_pct=90),
    ShippingLane(lane_id="Intel-PG-PHX-air", company="Intel", origin_id="Intel-PG",
        destination_id="PHX", mode="air", route_type="standard",
        transit_days_min=7, transit_days_max=12, transit_notes="Penang to Phoenix.",
        preferred_carriers=["DHL", "FedEx"], transshipment_hubs=["KUL", "LAX"],
        chokepoint_exposure=False, cost_usd_per_kg_min=4.5, cost_usd_per_kg_max=7,
        best_for=["packaged IC"], reliability_pct=90),
    ShippingLane(lane_id="TPE-MEM-air", company="Nvidia", origin_id="TSMC-HS",
        destination_id="MEM", mode="air", route_type="express",
        transit_days_min=3, transit_days_max=6, transit_notes="TPE to Memphis via FedEx.",
        preferred_carriers=["FedEx", "EVA Air"], transshipment_hubs=["TPE", "MEM"],
        chokepoint_exposure=False, cost_usd_per_kg_min=4.5, cost_usd_per_kg_max=7,
        best_for=["wafer", "packaged IC"], reliability_pct=90),
]


def get_nodes_by_company(company: str) -> List[ManufacturerNode]:
    return [n for n in MANUFACTURER_NODES if n.company == company]


def get_destinations_by_company(company: str) -> List[USDestinationHub]:
    return [d for d in US_DESTINATIONS if d.company == company]


def get_lanes_by_company(company: str) -> List[ShippingLane]:
    return [l for l in SHIPPING_LANES if l.company == company]


def get_lanes_for_origin(origin_id: str) -> List[ShippingLane]:
    return [l for l in SHIPPING_LANES if l.origin_id == origin_id]


def get_lanes_for_destination(destination_id: str) -> List[ShippingLane]:
    return [l for l in SHIPPING_LANES if l.destination_id == destination_id]


def get_lane(lane_id: str) -> Optional[ShippingLane]:
    for l in SHIPPING_LANES:
        if l.lane_id == lane_id:
            return l
    return None
