"""Deterministic trend-signal data sources used by TrendScout."""

from __future__ import annotations

import datetime as _dt
import os
from typing import Any, Dict, List, Optional


CATALOGUE: List[Dict[str, Any]] = [
    {
        "name": "Wireless Earbuds (TWS)",
        "category": "Consumer Electronics",
        "trend": "rising",
        "search_volume_idx": 1.34,
        "marketplaces": ["amazon_us", "amazon_de", "amazon_uk"],
        "price_band_usd": "$19.99 - $29.99",
        "demand_signal": "Q3 back-to-school + creator-driven TikTok Shop push",
        "sourcing_hint": "Shenzhen Huaqiangbei OEM cluster, MOQ 500",
    },
    {
        "name": "Smart LED Strip Lights",
        "category": "Home Lighting",
        "trend": "rising",
        "search_volume_idx": 1.21,
        "marketplaces": ["amazon_de", "amazon_us"],
        "price_band_usd": "$12.99 - $24.99",
        "demand_signal": "RGBIC + Matter support sustained over 8 weeks",
        "sourcing_hint": "AliExpress dedicated supplier, MOQ 200",
    },
    {
        "name": "Portable USB-C Blender",
        "category": "Kitchen",
        "trend": "rising",
        "search_volume_idx": 1.18,
        "marketplaces": ["amazon_us", "amazon_uk"],
        "price_band_usd": "$24.99 - $39.99",
        "demand_signal": "Q3 seasonal lift + gym & travel creators",
        "sourcing_hint": "Ningbo OEM cluster, MOQ 300",
    },
    {
        "name": "Magnetic Phone Mount",
        "category": "Mobile Accessories",
        "trend": "stable",
        "search_volume_idx": 1.02,
        "marketplaces": ["amazon_us"],
        "price_band_usd": "$8.99 - $14.99",
        "demand_signal": "Evergreen accessory category, low differentiation",
        "sourcing_hint": "MagSafe-compatible OEM, MOQ 1000",
    },
    {
        "name": "Foldable Laptop Stand",
        "category": "Office",
        "trend": "rising",
        "search_volume_idx": 1.15,
        "marketplaces": ["amazon_uk", "amazon_de", "amazon_us"],
        "price_band_usd": "$18.99 - $29.99",
        "demand_signal": "Remote-work tailwind + 'standing desk' co-keywords",
        "sourcing_hint": "Aluminium CNC, MOQ 150",
    },
    {
        "name": "Cat Water Fountain",
        "category": "Pet",
        "trend": "rising",
        "search_volume_idx": 1.27,
        "marketplaces": ["amazon_us", "amazon_de"],
        "price_band_usd": "$22.99 - $36.99",
        "demand_signal": "Pet humanisation tailwind, replacement cycle ~12 months",
        "sourcing_hint": "Stainless-steel variants winning, MOQ 250",
    },
]


def _filter_for_query(query: str) -> List[Dict[str, Any]]:
    q = (query or "").lower().strip()
    if not q:
        return CATALOGUE
    scored: List[Dict[str, Any]] = []
    for row in CATALOGUE:
        haystack = " ".join(
            str(row.get(k, "")) for k in ("name", "category", "demand_signal", "sourcing_hint")
        ).lower()
        overlap = sum(1 for token in q.split() if token and token in haystack)
        if overlap:
            scored.append({**row, "_score": overlap})
    if not scored:
        return sorted(CATALOGUE, key=lambda r: -r["search_volume_idx"])[:3]
    return sorted(scored, key=lambda r: -r.get("_score", 0))[:5]


def fetch_trends(query: str, *, marketplaces: Optional[List[str]] = None) -> Dict[str, Any]:
    """Return a trend snapshot for the given seed query."""
    rows = _filter_for_query(query)
    if marketplaces:
        mp_set = {m.lower() for m in marketplaces}
        rows = [
            {**r, "marketplaces": [m for m in r.get("marketplaces", []) if m.lower() in mp_set]}
            for r in rows
        ]
        rows = [r for r in rows if r.get("marketplaces")]
    return {
        "generated_at": _dt.datetime.utcnow().isoformat() + "Z",
        "query": query,
        "source": (
            "border_pilot.catalogue"
            if not os.environ.get("BORDER_PILOT_LIVE_SEARCH")
            else "live+fallback"
        ),
        "trends": rows,
    }
